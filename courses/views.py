"""D02 «Nytt fag», D08 «Gi nytt navn» and D09 «Slette faget …?» (FR-2).

Each dialog is a GET URL (AD-18): a full page normally, and the `dialog` partial in the
one #dialog slot under HTMX. A valid submit answers with HX-Location (302 without
HTMX); an invalid one renders the dialog again with its errors.
"""

from django.shortcuts import resolve_url
from django.views.decorators.http import require_http_methods

from core.http import redirect_after_submit, render_page, safe_next, vary_on_htmx
from core.ownership import get_owned_or_404
from courses import services
from courses.forms import CourseForm, RenameCourseForm
from courses.models import Course

# P03 and P04 live in `web`; courses names them by URL name only (AD-1 governs imports).
HOME = "web:home"
COURSE_PAGE = "web:course"


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def create(request):
    next_url = safe_next(request)
    form = CourseForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        course = services.create_course(request.user, form.cleaned_data["name"], form.cleaned_data["code"])
        return redirect_after_submit(request, resolve_url(COURSE_PAGE, course.id))
    return render_page(
        request,
        "courses/create.html",
        {"form": form, "next": next_url, "cancel_url": next_url or resolve_url(HOME)},
    )


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def rename(request, course_id):
    course = get_owned_or_404(Course, request.user, pk=course_id)
    next_url = safe_next(request)
    if request.method == "POST":
        form = RenameCourseForm(request.POST)
        if form.is_valid():
            services.rename_course(course, form.cleaned_data["name"])
            return redirect_after_submit(request, next_url or resolve_url(COURSE_PAGE, course.id))
    else:
        form = RenameCourseForm(initial={"name": course.name})
    return render_page(
        request,
        "courses/rename.html",
        {
            "form": form,
            "course": course,
            "current_course": course,
            "next": next_url,
            "cancel_url": next_url or resolve_url(COURSE_PAGE, course.id),
        },
    )


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def delete(request, course_id):
    course = get_owned_or_404(Course, request.user, pk=course_id)
    next_url = safe_next(request)
    if request.method == "POST":
        services.delete_course(course)
        return redirect_after_submit(request, resolve_url(HOME))
    return render_page(
        request,
        "courses/delete.html",
        {
            "course": course,
            "current_course": course,
            "next": next_url,
            "cancel_url": next_url or resolve_url(COURSE_PAGE, course.id),
        },
    )
