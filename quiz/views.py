"""D06 «Start quiz», P06 Quiz in Practice mode, and P07 «Resultat» (FR-10 to FR-13, AD-13).

D06 is a GET URL like the other dialogs (AD-18): a full page normally, the `dialog` partial in the
#dialog slot under HTMX. P06 is a full page per position (`quizzes/<id>/<position>/`). The answer
and regrade POSTs answer under HTMX with the `card` partial for #question-card, and otherwise
redirect to the position (POST/redirect/GET). P07 is a full page; «Øv på feilene» POSTs to
`retry`, which starts a Retry round (FR-13). Every lookup is owned, or 404 (AD-7).
"""

from django.http import Http404
from django.shortcuts import redirect, render, resolve_url
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from core.http import htmx_target, redirect_after_submit, render_page, vary_on_htmx
from core.messages import MESSAGES
from core.ownership import get_owned_or_404
from courses.models import Topic
from quiz import services
from quiz.forms import StartQuizForm
from quiz.models import Answer, Quiz, QuizKind, QuizQuestion
from quiz.rules import Grade, join_with_og, option_letter
from studymat.models import QuestionKind

# P05 lives in `web`; quiz names it by URL name only (AD-1 governs imports).
TOPIC_PAGE = "web:topic"
# D09 lives in `studymat`; named by URL only, like P05.
DELETE_ITEM = "studymat:delete_item"

CARD_TARGET = "question-card"

GRADE_ICONS = {
    Grade.CORRECT: "ok",
    Grade.PARTIAL: "part",
    Grade.INCORRECT: "bad",
    Grade.NOT_GRADED: "alert",
}


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def start(request, topic_id):
    """D06: how many Questions; «Start quiz» creates the Quiz once per start token."""
    topic = get_owned_or_404(Topic.objects.select_related("course"), request.user, pk=topic_id)
    return_url = f"{resolve_url(TOPIC_PAGE, topic.id)}?tab=quiz"
    available = services.available_questions(request.user, topic).count()
    if not available:
        # With none ready there is nothing to start (EXPERIENCE.md, Few Questions).
        return redirect_after_submit(request, return_url)
    form = StartQuizForm(request.POST if request.method == "POST" else None, available=available)
    if request.method == "POST" and form.is_valid():
        quiz = services.start_quiz(
            request.user,
            topic,
            form.cleaned_data["count"],
            form.cleaned_data["start_token"],
            return_url,
        )
        if quiz is None:
            return redirect_after_submit(request, return_url)
        return redirect_after_submit(request, resolve_url("quiz:resume", quiz.id))
    return render_page(
        request,
        "quiz/start.html",
        {
            "form": form,
            "topic": topic,
            "current_course": topic.course,
            "title": f"Start quiz i {topic.name}",
            "lead": MESSAGES["quiz_available"].format(n=available),
            "action": resolve_url("quiz:start", topic.id),
            "cancel_url": return_url,
        },
    )


@require_safe
def resume(request, quiz_id):
    """The first unanswered position; with every Question answered, P07; with none left, `return_url`."""
    quiz = get_owned_or_404(Quiz, request.user, pk=quiz_id)
    position = services.first_unanswered(quiz)
    if position is not None:
        return redirect("quiz:question", quiz.id, position)
    if not services.positions(quiz):
        return redirect(quiz.return_url)
    return redirect("quiz:result", quiz.id)


@require_safe
def result(request, quiz_id):
    """P07 «Resultat» (FR-13): the score, a strip and one row per Question, and the band for
    «Øv på feilene» when anything is missed. Read-only: acting on rows is story 9b."""
    quiz = get_owned_or_404(Quiz, request.user, pk=quiz_id)
    outcome = services.result(quiz)
    if not outcome.rows:
        # Every Question was deleted: there is nothing to show.
        return redirect(quiz.return_url)
    return render(request, "quiz/result.html", _result_context(quiz, outcome))


@require_POST
def retry(request, quiz_id):
    """«Øv på feilene»: the Retry round's first position; with nothing missed, back to P07."""
    quiz = get_owned_or_404(Quiz, request.user, pk=quiz_id)
    round_ = services.start_retry(request.user, quiz)
    if round_ is None:
        return redirect_after_submit(request, resolve_url("quiz:result", quiz.id))
    first = services.positions(round_)[0]
    return redirect_after_submit(request, resolve_url("quiz:question", round_.id, first))


def _owned_position(request, quiz_id, position) -> tuple[Quiz, QuizQuestion]:
    quiz = get_owned_or_404(Quiz, request.user, pk=quiz_id)
    quiz_question = (
        QuizQuestion.objects.select_related("question__source__topic")
        .filter(quiz=quiz, position=position)
        .first()
    )
    if quiz_question is None:
        raise Http404
    return quiz, quiz_question


def _stored_answer(quiz, question) -> Answer | None:
    return Answer.objects.filter(quiz=quiz, question=question).first()


@require_safe
@vary_on_htmx
def question(request, quiz_id, position):
    """P06: one Question; a stored Answer shows locked, with its feedback."""
    quiz, quiz_question = _owned_position(request, quiz_id, position)
    return _respond(request, quiz, quiz_question, _stored_answer(quiz, quiz_question.question))


@require_POST
@vary_on_htmx
def answer(request, quiz_id, position):
    """Save and grade the Answer. An empty one is refused inline and nothing is saved."""
    quiz, quiz_question = _owned_position(request, quiz_id, position)
    question = quiz_question.question
    stored = _stored_answer(quiz, question)
    if stored is not None:
        # A resubmit: the first Answer is kept and shown.
        return _after_post(request, quiz, quiz_question, stored)
    if question.kind == QuestionKind.MULTIPLE_CHOICE:
        chosen = _chosen_index(request.POST.get("choice"), len(question.options or []))
        if chosen is None:
            return _respond(request, quiz, quiz_question, None, error=MESSAGES["answer_choose_first"])
        saved = services.save_answer(request.user, quiz, question, chosen_index=chosen)
    else:
        text = request.POST.get("text", "").strip()
        if not text:
            return _respond(request, quiz, quiz_question, None, error=MESSAGES["answer_write_first"])
        saved = services.save_answer(request.user, quiz, question, text=text)
    return _after_post(request, quiz, quiz_question, saved)


@require_POST
@vary_on_htmx
def regrade(request, quiz_id, position):
    """«Prøv å rette igjen»: grade a not-graded Answer again with the same text."""
    quiz, quiz_question = _owned_position(request, quiz_id, position)
    stored = _stored_answer(quiz, quiz_question.question)
    if stored is None:
        return _after_post(request, quiz, quiz_question, None)
    return _after_post(request, quiz, quiz_question, services.regrade(request.user, stored))


# The «Endre vurdering» value that clears the override («Bruk KI-vurderingen»).
USE_AI = "ai"


@require_POST
@vary_on_htmx
def override(request, quiz_id, position):
    """«Endre vurdering» (FR-12): set or clear the override on a graded Free-text Answer."""
    quiz, quiz_question = _owned_position(request, quiz_id, position)
    stored = _stored_answer(quiz, quiz_question.question)
    if stored is None:
        return _after_post(request, quiz, quiz_question, None)
    raw = request.POST.get("grade", "")
    if raw == USE_AI:
        stored = services.override_grade(request.user, stored, None)
    elif raw in services.OVERRIDABLE:
        stored = services.override_grade(request.user, stored, raw)
    return _after_post(request, quiz, quiz_question, stored)


def _chosen_index(raw, count: int) -> int | None:
    try:
        index = int(raw)
    except (TypeError, ValueError):
        return None
    return index if 0 <= index < count else None


def _after_post(request, quiz, quiz_question, stored):
    if htmx_target(request) == CARD_TARGET:
        return _respond(request, quiz, quiz_question, stored)
    return redirect("quiz:question", quiz.id, quiz_question.position)


def _respond(request, quiz, quiz_question, stored, *, error: str = ""):
    context = _context(quiz, quiz_question, stored, error=error, typed=request.POST.get("text", ""))
    if htmx_target(request) == CARD_TARGET:
        context["oob"] = True
        return render(request, "quiz/question.html#card", context)
    return render(request, "quiz/question.html", context)


def _context(quiz, quiz_question, stored, *, error: str, typed: str) -> dict:
    question = quiz_question.question
    topic = question.source.topic
    all_positions = services.positions(quiz)
    answered = set(
        QuizQuestion.objects.filter(quiz=quiz, question__answers__quiz=quiz).values_list("position", flat=True)
    )
    index = all_positions.index(quiz_question.position) + 1
    next_position = services.next_position(quiz, quiz_question.position)
    if next_position:
        next_url = resolve_url("quiz:question", quiz.id, next_position)
    elif answered.issuperset(all_positions):
        next_url = resolve_url("quiz:result", quiz.id)
    else:
        next_url = resolve_url("quiz:resume", quiz.id)
    is_retry = quiz.kind == QuizKind.RETRY
    url_args = (quiz.id, quiz_question.position)
    context = {
        "quiz": quiz,
        "question": question,
        "topic": topic,
        "lang": question.source.language,
        "is_mc": question.kind == QuestionKind.MULTIPLE_CHOICE,
        "index": index,
        "total": len(all_positions),
        "slots": [{"answered": p in answered, "current": p == quiz_question.position} for p in all_positions],
        "exit_url": quiz.return_url,
        "context_label": MESSAGES["retry_context"] if is_retry else f"{topic.name} · øving",
        "retry_note": MESSAGES["retry_note"] if is_retry else "",
        "answer": stored,
        "error": error,
        "typed": typed,
        "answer_url": resolve_url("quiz:answer", *url_args),
        "regrade_url": resolve_url("quiz:regrade", *url_args),
        # D04's `next` from the feedback-panel: back to this Question (FR-22).
        "question_url": resolve_url("quiz:question", *url_args),
        "next_url": next_url,
        "next_label": "Neste spørsmål" if next_position else "Fullfør quiz",
    }
    if context["is_mc"]:
        context["options"] = _options(question, stored, focus_first=bool(error))
    if stored is not None:
        context.update(_feedback(question, stored))
        can_override = services.can_override(stored)
        context.update(
            {
                "can_override": can_override,
                "override_url": resolve_url("quiz:override", *url_args),
                "override_items": _override_items(context["grade"], context["overridden"]) if can_override else [],
                "delete_url": _delete_url(question.id, next_url, resolve_url("quiz:question", *url_args)),
            }
        )
    return context


def _feedback(question, stored: Answer) -> dict:
    """What the feedback-panel shows for a stored Answer, on P06 and read-only on P07."""
    grade = stored.shown_grade
    overridden = bool(stored.override_grade) and stored.override_grade != stored.grade
    is_mc = question.kind == QuestionKind.MULTIPLE_CHOICE
    return {
        "overridden": overridden,
        "ai_grade_label": Grade(stored.grade).label if overridden else "",
        "grade": grade,
        "grade_label": Grade(grade).label,
        "grade_icon": GRADE_ICONS[grade],
        "failure_message": _failure_message(stored.shown_failure) if grade == Grade.NOT_GRADED else "",
        "failure_code": stored.shown_failure if grade == Grade.NOT_GRADED else "",
        "correct_letter": option_letter(question.correct_index),
        "wrong_choice": is_mc and grade == Grade.INCORRECT,
    }


def _result_context(quiz, outcome: services.Result) -> dict:
    rows = []
    for row in outcome.rows:
        question = row.question
        item = {
            "number": row.number,
            "heading_id": f"q-{row.number}-heading",
            "question": question,
            "answer": row.answer,
            "grade": row.grade or "unanswered",
            "grade_label": Grade(row.grade).label if row.grade else MESSAGES["result_unanswered"],
            "grade_icon": GRADE_ICONS.get(row.grade, ""),
            "is_mc": question.kind == QuestionKind.MULTIPLE_CHOICE,
            "lang": question.source.language,
            "question_url": resolve_url("quiz:question", quiz.id, row.position),
        }
        if row.answer is not None:
            item.update(_feedback(question, row.answer))
        rows.append(item)
    context = {
        "quiz": quiz,
        "exit_url": quiz.return_url,
        "context_label": "Resultat",
        "score_k": outcome.correct,
        "score_n": outcome.total,
        "lead": _result_lead(outcome),
        "rows": rows,
        "all_correct": outcome.all_correct,
        "all_correct_text": MESSAGES["result_all_correct"],
        "not_graded_note": MESSAGES["result_not_graded_note"],
        "open_label": MESSAGES["result_open_question"],
    }
    numbers = outcome.missed_numbers
    if numbers:
        # Each number is escaped by format_html; the separators are literal, so the join is safe.
        joined = mark_safe(join_with_og([format_html("<b>{}</b>", n) for n in numbers]))
        why = MESSAGES["retry_band_why_one" if len(numbers) == 1 else "retry_band_why_other"]
        context["band"] = {
            "number": len(numbers),
            "unit": MESSAGES["retry_band_unit"],
            "heading": MESSAGES["retry_band_heading"],
            "why": format_html(why, numbers=joined),
            "minutes": MESSAGES["band_minutes"].format(m=outcome.minutes),
            "button_label": MESSAGES["retry_band_button"].format(n=len(numbers)),
            "action_url": resolve_url("quiz:retry", quiz.id),
        }
    return context


def _result_lead(outcome: services.Result) -> str:
    """«7 riktige, 2 delvis riktige og 1 feil.»; zero counts are left out."""
    parts = []
    for count, code in (
        (outcome.correct, "result_lead_correct"),
        (outcome.partial, "result_lead_partial"),
    ):
        if count:
            parts.append(MESSAGES[f"{code}_{'one' if count == 1 else 'other'}"].format(n=count))
    if outcome.incorrect:
        parts.append(MESSAGES["result_lead_incorrect"].format(n=outcome.incorrect))
    return f"{join_with_og(parts)}." if parts else ""


def _override_items(shown: str, overridden: bool) -> list[dict]:
    """The «Endre vurdering» menu: the three Grades, the effective one marked, then the undo."""
    items = [
        {"value": value, "label": Grade(value).label, "icon": GRADE_ICONS[value], "current": value == shown}
        for value in services.OVERRIDABLE
    ]
    if overridden:
        items.append({"value": USE_AI, "label": "Bruk KI-vurderingen", "icon": "refresh", "current": False, "separator": True})
    return items


def _delete_url(question_id: int, next_url: str, cancel_url: str) -> str:
    """D09 for this Question (story 7): after the delete the Quiz goes on at `next_url`."""
    query = urlencode({"next": next_url, "cancel": cancel_url})
    return f"{resolve_url(DELETE_ITEM, 'question', question_id)}?{query}"


def _options(question, stored, *, focus_first: bool) -> list[dict]:
    """Option rows A–D; once answered, «Ditt svar» and «Riktig svar» in words (FR-11)."""
    rows = []
    for index, option in enumerate(question.options or []):
        chosen = stored is not None and stored.chosen_index == index
        correct = stored is not None and question.correct_index == index
        tags = []
        if chosen:
            tags.append("Ditt svar")
        if correct:
            tags.append("Riktig svar")
        state = ""
        if correct:
            state = "correct"
        elif chosen:
            state = "incorrect"
        rows.append(
            {
                "index": index,
                "letter": option_letter(index),
                "text": option.get("text", ""),
                "chosen": chosen,
                "state": state,
                "tag": " · ".join(tags),
                "tag_icon": "ok" if correct else "bad",
                "focus": focus_first and index == 0,
            }
        )
    return rows


# «Ikke rettet» names these failures; any other shows the grading message.
NAMED_GRADING_FAILURES = ("key_rejected", "rate_limited", "privacy_not_accepted")


def _failure_message(code: str) -> str:
    """«Ikke rettet»: the named message for a rejected Key, a rate limit or a missing privacy acceptance."""
    if code in NAMED_GRADING_FAILURES:
        return MESSAGES[code]
    return MESSAGES["grading_failed"]
