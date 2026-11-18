"""Composite pages (AD-1): Hjem P03, Fagoversikt P04, Tema P05, «Fant ikke siden» P12, and the theme."""

from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import redirect, render, resolve_url
from django.views.decorators.http import require_POST, require_safe

from ai import gateway
from core.http import render_page, safe_next, vary_on_htmx
from core.ownership import get_owned_or_404
from core.messages import MESSAGES
from courses.models import Course, Source, Status, Topic
from quiz import services as quiz_services
from studymat.models import Flashcard, KeyConcept, Question
from web.context_processors import THEME_COOKIE, THEMES

THEME_MAX_AGE = 60 * 60 * 24 * 365


@require_safe
@vary_on_htmx
def home(request):
    # The fag list is `shell_courses` from web.context_processors.shell, shared with the rail.
    return render_page(request, "web/home.html", {"nav_current": "home"}, partials=())


@require_safe
@vary_on_htmx
def course(request, course_id):
    course = get_owned_or_404(Course, request.user, pk=course_id)
    return render_page(
        request,
        "web/course.html",
        {
            "course": course,
            "current_course": course,
            "topics": Topic.objects.for_student(request.user).filter(course=course),
            "breadcrumb": [{"label": "Hjem", "url": resolve_url("web:home")}],
        },
        partials=(),
    )


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
    """P05: breadcrumb, title, actions and the four tema-tabs (FR-23). The band comes later.

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
    }
    if tab == "quiz":
        # «Quizen er lagret. k av N riktige.» after «Fullfør quiz» (story 8; P07 replaces it in story 9).
        context["finish_note"] = quiz_services.finish_note(request.user, request.GET.get(quiz_services.FINISHED_PARAM))
    elif tab == "summary":
        listed = sources.select_related("summary").prefetch_related(
            Prefetch("key_concepts", queryset=KeyConcept.objects.for_student(request.user))
        )
        context["blocks"] = _summary_blocks(listed)
        context["has_ready"] = any(block["ready"] for block in context["blocks"])
    elif tab == "selftest":
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
