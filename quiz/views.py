"""D06 «Start quiz» and P06 Quiz in Practice mode (FR-10 to FR-12, AD-13).

D06 is a GET URL like the other dialogs (AD-18): a full page normally, the `dialog` partial in the
#dialog slot under HTMX. P06 is a full page per position (`quizzes/<id>/<position>/`). The answer
and regrade POSTs answer under HTMX with the `card` partial for #question-card, and otherwise
redirect to the position (POST/redirect/GET). Every lookup is owned, or 404 (AD-7).
"""

from django.http import Http404
from django.shortcuts import redirect, render, resolve_url
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from core.http import htmx_target, redirect_after_submit, render_page, vary_on_htmx
from core.messages import MESSAGES
from core.ownership import get_owned_or_404
from courses.models import Topic
from quiz import services
from quiz.forms import StartQuizForm
from quiz.models import Answer, Quiz, QuizQuestion
from quiz.rules import Grade, option_letter
from studymat.models import QuestionKind

# P05 lives in `web`; quiz names it by URL name only (AD-1 governs imports).
TOPIC_PAGE = "web:topic"

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
    """The first unanswered position; with every Question answered, `return_url` with the note."""
    quiz = get_owned_or_404(Quiz, request.user, pk=quiz_id)
    position = services.first_unanswered(quiz)
    if position is not None:
        return redirect("quiz:question", quiz.id, position)
    if not services.positions(quiz):
        return redirect(quiz.return_url)
    return redirect(services.finished_url(quiz))


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
    is_mc = question.kind == QuestionKind.MULTIPLE_CHOICE
    url_args = (quiz.id, quiz_question.position)
    context = {
        "quiz": quiz,
        "question": question,
        "topic": topic,
        "lang": question.source.language,
        "is_mc": is_mc,
        "index": index,
        "total": len(all_positions),
        "slots": [{"answered": p in answered, "current": p == quiz_question.position} for p in all_positions],
        "exit_url": quiz.return_url,
        "context_label": f"{topic.name} · øving",
        "answer": stored,
        "error": error,
        "typed": typed,
        "answer_url": resolve_url("quiz:answer", *url_args),
        "regrade_url": resolve_url("quiz:regrade", *url_args),
        "next_url": resolve_url("quiz:question", quiz.id, next_position) if next_position else resolve_url("quiz:resume", quiz.id),
        "next_label": "Neste spørsmål" if next_position else "Fullfør quiz",
    }
    if is_mc:
        context["options"] = _options(question, stored, focus_first=bool(error))
    if stored is not None:
        grade = stored.shown_grade
        context.update(
            {
                "grade": grade,
                "grade_label": Grade(grade).label,
                "grade_icon": GRADE_ICONS[grade],
                "failure_message": _failure_message(stored.shown_failure) if grade == Grade.NOT_GRADED else "",
                "correct_letter": option_letter(question.correct_index),
                "wrong_choice": is_mc and grade == Grade.INCORRECT,
            }
        )
    return context


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


def _failure_message(code: str) -> str:
    """«Ikke rettet»: E:303 for a rejected Key, otherwise the grading message."""
    if code == "key_rejected":
        return MESSAGES["key_rejected"]
    return MESSAGES["grading_failed"]
