"""Composite pages (AD-1): Hjem P03, Fagoversikt P04, Tema P05, «Fant ikke siden» P12, and the theme."""

from django.conf import settings
from django.shortcuts import redirect, render, resolve_url
from django.views.decorators.http import require_POST, require_safe

from core.http import render_page, safe_next, vary_on_htmx
from core.ownership import get_owned_or_404
from courses.models import Course, Source, Topic
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


@require_safe
@vary_on_htmx
def topic(request, topic_id):
    """P05, basic: breadcrumb, title, actions and the «Kilder» list (tabs and band come later)."""
    topic = get_owned_or_404(Topic.objects.select_related("course"), request.user, pk=topic_id)
    course = topic.course
    return render_page(
        request,
        "web/topic.html",
        {
            "topic": topic,
            "course": course,
            # The fag-rail keeps marking the fag while on one of its tema.
            "current_course": course,
            "sources": Source.objects.for_student(request.user).filter(topic=topic),
            "breadcrumb": [
                {"label": "Hjem", "url": resolve_url("web:home")},
                {"label": course.name, "url": resolve_url("web:course", course.id)},
            ],
        },
        partials=(),
    )


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
