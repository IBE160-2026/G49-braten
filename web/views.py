"""Composite pages (AD-1): Hjem P03, Fagoversikt P04, Tema P05, «Fant ikke siden» P12, and the theme."""

from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import redirect, render, resolve_url
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from ai import gateway
from core import time
from core.http import redirect_after_submit, render_page, safe_next, vary_on_htmx
from core.ownership import get_owned_or_404
from core.messages import MESSAGES
from courses.models import Course, Source, Status, Topic
from courses.scope import Scope
from progress import services as progress_services
from quiz import services as quiz_services
from quiz.rules import Grade
from review import services as review_services
from studymat.models import Flashcard, KeyConcept, Question
from web.context_processors import THEME_COOKIE, THEMES
from web.forms import WeakQuizForm

THEME_MAX_AGE = 60 * 60 * 24 * 365


@require_safe
@vary_on_htmx
def home(request):
    # The fag list is `shell_courses` from web.context_processors.shell, shared with the rail.
    context = {"nav_current": "home", "next_step": progress_services.next_step(request.user, Scope.all())}
    return render_page(request, "web/home.html", context, partials=())


@require_safe
@vary_on_htmx
def course(request, course_id):
    """P04: the Course score under the title, the Topics Weak first (FR-16, FR-17), and
    «Øv på svake temaer (N)» when a Weak topic has ready Questions."""
    course = get_owned_or_404(Course, request.user, pk=course_id)
    mastery = progress_services.course_score(request.user, course.id)
    weak = mastery.weak
    ready = progress_services.ready_question_counts(request.user, Scope(course_id=course.id))
    return render_page(
        request,
        "web/course.html",
        {
            "course": course,
            "next_step": progress_services.next_step(request.user, Scope(course_id=course.id)),
            "current_course": course,
            "mastery": mastery,
            "topic_scores": progress_services.weak_first(mastery.topics),
            "weak_count": len(weak),
            "weak_quiz_url": resolve_url("web:weak_quiz", course.id) if any(ready.get(t.topic.id) for t in weak) else "",
            "breadcrumb": [{"label": "Hjem", "url": resolve_url("web:home")}],
        },
        partials=(),
    )


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def weak_quiz(request, course_id):
    """D10 «Øv på svake temaer» (FR-17): the topic-picker, Weak topics preselected; «Start quiz»
    starts a Practice-mode Quiz of every ready Question of the chosen Topics (once per start token)."""
    course = get_owned_or_404(Course, request.user, pk=course_id)
    return_url = resolve_url("web:course", course.id)
    ready = progress_services.ready_question_counts(request.user, Scope(course_id=course.id))
    mastery = progress_services.course_score(request.user, course.id)
    listed = [t for t in progress_services.weak_first(mastery.topics) if ready.get(t.topic.id)]
    if not listed:
        # Nothing has ready Questions: there is nothing to start.
        return redirect_after_submit(request, return_url)
    preselected = [t.topic.id for t in listed if t.is_weak]
    form = WeakQuizForm(
        request.POST if request.method == "POST" else None,
        topic_ids=[t.topic.id for t in listed],
        preselected=preselected,
    )
    if request.method == "POST" and form.is_valid():
        quiz = quiz_services.start_quiz_from_topics(
            request.user, course, form.cleaned_data["topics"], form.cleaned_data["start_token"], return_url
        )
        if quiz is not None:
            return redirect_after_submit(request, resolve_url("quiz:resume", quiz.id))
        # The chosen Topics lost their ready Questions since the dialog opened: the same form error.
        form.add_error("topics", MESSAGES["weak_quiz_topics_required"])
    listed_ids = {t.topic.id for t in listed}
    chosen = {int(v) for v in (form["topics"].value() or []) if str(v).isdigit()} & listed_ids
    rows = [
        {
            "score": t,
            "questions": ready[t.topic.id],
            "checked": t.topic.id in chosen,
            "input_id": f"weak-topic-{t.topic.id}",
        }
        for t in listed
    ]
    return render_page(
        request,
        "web/weak_quiz.html",
        {
            "form": form,
            "course": course,
            "current_course": course,
            "rows": rows,
            "count_text": _picker_count(len(chosen), sum(r["questions"] for r in rows if r["checked"])),
            "title": MESSAGES["weak_quiz_title"],
            "lead": MESSAGES["weak_quiz_lead"],
            "action": resolve_url("web:weak_quiz", course.id),
            "cancel_url": return_url,
        },
    )


def _picker_count(topics: int, questions: int) -> str:
    """The topic-picker footer: «2 temaer valgt · 43 spørsmål»."""
    key = "weak_quiz_count_one" if topics == 1 else "weak_quiz_count_other"
    return MESSAGES[key].format(t=topics, q=questions)


# P05's tema-tabs in their fixed order (EXPERIENCE.md, Tema-tabs); `?tab=` selects one.
TABS = ("summary", "quiz", "selftest", "sources")
DEFAULT_TAB = "summary"


def _removed_note(count: int) -> str:
    """FR-8: the note under a summary-block, or "" when the Reference check removed nothing."""
    if count <= 0:
        return ""
    if count == 1:
        return MESSAGES["removed_note_one"]
    return MESSAGES["removed_note_other"].format(n=count)


def _summary_blocks(sources) -> list[dict]:
    """«Sammendrag», newest first: a ready kilde's block, or a generating kilde's dashed line.

    `sources` is newest first with `summary` and `key_concepts` loaded; failed kilder are left out
    (their status and «Prøv igjen» live on «Kilder»).
    """
    blocks = []
    for source in sources:
        status = source.effective_status
        if status == Status.READY:
            blocks.append(
                {
                    "source": source,
                    "ready": True,
                    "summary": getattr(source, "summary", None),
                    "key_concepts": source.key_concepts.all(),
                    "removed_note": _removed_note(source.removed_count),
                }
            )
        elif status == Status.GENERATING:
            blocks.append({"source": source, "ready": False})
    return blocks


@require_safe
@vary_on_htmx
def topic(request, topic_id):
    """P05: breadcrumb, title, actions, the quiz band (Next step) and the four tema-tabs (FR-23).

    Each tab is a full-page GET link (`?tab=`, AD-13); only the selected tab's panel is rendered.
    """
    topic = get_owned_or_404(Topic.objects.select_related("course"), request.user, pk=topic_id)
    course = topic.course
    tab = request.GET.get("tab")
    if tab not in TABS:
        tab = DEFAULT_TAB
    sources = Source.objects.for_student(request.user).filter(topic=topic)
    # Questions and Flashcards count only from ready kilder (FR-9: not used until ready).
    ready_items = {"student": request.user, "source__topic": topic, "source__status": Status.READY}
    counts = {
        "questions": Question.objects.filter(**ready_items).count(),
        "cards": Flashcard.objects.filter(**ready_items).count(),
        "sources": sources.count(),
    }
    context = {
        "topic": topic,
        "course": course,
        # The fag-rail keeps marking the fag while on one of its tema.
        "current_course": course,
        "tab": tab,
        "counts": counts,
        # Label and count chip per tab; the chip hides below 600 px (visually only).
        "tabs": [
            {"key": "summary", "label": "Sammendrag", "count": ""},
            {"key": "quiz", "label": "Quiz", "count": str(counts["questions"])},
            {"key": "selftest", "label": "Test deg selv", "count": f"{counts['cards']} kort"},
            {"key": "sources", "label": "Kilder", "count": str(counts["sources"])},
        ],
        "breadcrumb": [
            {"label": "Hjem", "url": resolve_url("web:home")},
            {"label": course.name, "url": resolve_url("web:course", course.id)},
        ],
        # The band above the tabs, whichever tab is open (EXPERIENCE.md, tema-tabs).
        "next_step": progress_services.next_step(request.user, Scope(topic_id=topic.id)),
        # The Topic score under the title, on every tab (FR-16).
        "mastery": progress_services.topic_scores(request.user, Scope(topic_id=topic.id))[topic.id],
    }
    if tab == "summary":
        listed = sources.select_related("summary").prefetch_related(
            Prefetch("key_concepts", queryset=KeyConcept.objects.for_student(request.user))
        )
        context["blocks"] = _summary_blocks(listed)
        context["has_ready"] = any(block["ready"] for block in context["blocks"])
    elif tab == "quiz":
        context["history"] = _history_rows(request.user, topic)
    elif tab == "selftest":
        # «Repeter dagens kort (N)»: this tema's Due cards, from the one definition (AD-11).
        context["due_today"] = review_services.due_cards(request.user, Scope(topic_id=topic.id)).count()
        back_here = f"{resolve_url('web:topic', topic.id)}?tab=selftest"
        context["review_start_url"] = f"{resolve_url('review:start')}?{urlencode({'topic': topic.id, 'next': back_here})}"
        # Newest kilde first (Source ordering), then each kilde's cards in the order they were made.
        context["flashcards"] = (
            Flashcard.objects.filter(**ready_items)
            .select_related("source")
            .order_by("-source__created_at", "-source__id", "id")
        )
    elif tab == "sources":
        context["sources"] = sources
        # NFR-7: a failed source-row's «Prøv igjen» is inactive at the daily limit.
        context["generation_blocked"] = gateway.remaining_today(request.user) == 0
    return render_page(request, "web/topic.html", context, partials=())


def _history_rows(student, topic) -> list[dict]:
    """«Tidligere quizer» (FR-27): one row per Quiz with a Question from this Topic, newest first.
    Only the newest row may offer «Øv på feilene (N)»; every other row links to its result."""
    rows = []
    for index, item in enumerate(quiz_services.topic_history(student, topic)):
        outcome = item.result
        misses = len(outcome.missed_numbers)
        slots = []
        for row in outcome.rows:
            answer = row.answer
            overridden = answer is not None and bool(answer.override_grade) and answer.override_grade != answer.grade
            label = Grade(row.grade).label if row.grade else MESSAGES["result_unanswered"]
            if overridden:
                label = f"{label}, endret av deg"
            slots.append(
                {"number": row.number, "grade": row.grade or "unanswered", "label": label, "overridden": overridden}
            )
        rows.append(
            {
                "quiz": item.quiz,
                "date": time.short_date(item.quiz.started_at),
                "is_retry": item.is_retry,
                "score": MESSAGES["history_score"].format(k=outcome.correct, n=outcome.total),
                "partial": MESSAGES["history_partial"].format(p=outcome.partial) if outcome.partial else "",
                "slots": slots,
                "retry_label": MESSAGES["retry_band_button"].format(n=misses) if index == 0 and misses else "",
                "retry_url": resolve_url("quiz:retry", item.quiz.id),
                "result_url": resolve_url("quiz:result", item.quiz.id),
            }
        )
    return rows


def not_found(request, exception=None):
    """P12 (handler404): the same page for an unknown URL and for another Student's data."""
    signed_in = getattr(request, "user", None) is not None and request.user.is_authenticated
    layout = "layouts/shell.html" if signed_in else "layouts/auth.html"
    return render(request, "web/404.html", {"layout": layout}, status=404)


@require_POST
def theme(request):
    """D01 «Utseende»: Lys or Mørk sets the cookie, System clears it, anything else is ignored.

    A plain form POST answered with a full page, because the theme lives on <html>,
    which an HTMX swap of <body> cannot change.
    """
    response = redirect(safe_next(request) or resolve_url("web:home"))
    value = request.POST.get("theme", "")
    if value in THEMES:
        response.set_cookie(
            THEME_COOKIE,
            value,
            max_age=THEME_MAX_AGE,
            samesite="Lax",
            secure=settings.SESSION_COOKIE_SECURE,
            httponly=True,
        )
    elif value == "system":
        response.delete_cookie(THEME_COOKIE, samesite="Lax")
    return response
