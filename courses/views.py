"""Dialogs for fag, tema and kilde (FR-2): D02 «Nytt fag», D03 «Nytt tema», D08 «Gi nytt navn»
and D09 «Slette …?».

Each dialog is a GET URL (AD-18): a full page normally, and the `dialog` partial in the
one #dialog slot under HTMX. A valid submit answers with HX-Location (302 without
HTMX); an invalid one renders the dialog again with its errors.
"""

from django.shortcuts import resolve_url
from django.views.decorators.http import require_http_methods

from core.http import redirect_after_submit, render_page, safe_next, vary_on_htmx
from core.ownership import get_owned_or_404
from courses import rules, services
from courses.forms import CourseForm, RenameCourseForm, RenameSourceForm, TopicForm
from courses.models import Course, Source, Topic

# P03, P04 and P05 live in `web`; courses names them by URL name only (AD-1 governs imports).
HOME = "web:home"
COURSE_PAGE = "web:course"
TOPIC_PAGE = "web:topic"


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
def create_topic(request, course_id):
    course = get_owned_or_404(Course, request.user, pk=course_id)
    next_url = safe_next(request)
    form = TopicForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        topic = services.create_topic(course, form.cleaned_data["name"])
        return redirect_after_submit(request, resolve_url(TOPIC_PAGE, topic.id))
    return render_page(
        request,
        "courses/create_topic.html",
        {
            "form": form,
            "course": course,
            "current_course": course,
            "action": resolve_url("courses:create_topic", course.id),
            "next": next_url,
            "cancel_url": next_url or resolve_url(COURSE_PAGE, course.id),
        },
    )


def _rename(request, item, form_class, rename, action, current_course, item_url):
    """D08 for any named item: prefilled name; back to a safe `next`, else the item's page."""
    next_url = safe_next(request)
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            rename(item, form.cleaned_data["name"])
            return redirect_after_submit(request, next_url or item_url)
    else:
        form = form_class(initial={"name": item.name})
    return render_page(
        request,
        "courses/rename.html",
        {
            "form": form,
            "item": item,
            "action": action,
            "current_course": current_course,
            "next": next_url,
            "cancel_url": next_url or item_url,
        },
    )


def _delete(request, item, delete, *, title, lead, submit_label, action, current_course, after_url, cancel_url):
    """D09 for any item: GET confirms, POST deletes and lands on `after_url`."""
    next_url = safe_next(request)
    if request.method == "POST":
        delete(item)
        return redirect_after_submit(request, after_url)
    return render_page(
        request,
        "courses/delete.html",
        {
            "item": item,
            "title": title,
            "lead": lead,
            "submit_label": submit_label,
            "action": action,
            "current_course": current_course,
            "next": next_url,
            "cancel_url": next_url or cancel_url,
        },
    )


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def rename(request, course_id):
    course = get_owned_or_404(Course, request.user, pk=course_id)
    return _rename(
        request,
        course,
        RenameCourseForm,
        services.rename_course,
        action=resolve_url("courses:rename", course.id),
        current_course=course,
        item_url=resolve_url(COURSE_PAGE, course.id),
    )


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def delete(request, course_id):
    course = get_owned_or_404(Course, request.user, pk=course_id)
    return _delete(
        request,
        course,
        services.delete_course,
        title=f"Slette faget {course.name}?",
        lead=rules.course_delete_lead(*services.course_delete_counts(course)),
        submit_label="Slett faget",
        action=resolve_url("courses:delete", course.id),
        current_course=course,
        after_url=resolve_url(HOME),
        cancel_url=resolve_url(COURSE_PAGE, course.id),
    )


def _owned_topic(request, topic_id) -> Topic:
    return get_owned_or_404(Topic.objects.select_related("course"), request.user, pk=topic_id)


def _owned_source(request, source_id) -> Source:
    return get_owned_or_404(Source.objects.select_related("topic__course"), request.user, pk=source_id)


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def rename_topic(request, topic_id):
    topic = _owned_topic(request, topic_id)
    return _rename(
        request,
        topic,
        TopicForm,
        services.rename_topic,
        action=resolve_url("courses:rename_topic", topic.id),
        current_course=topic.course,
        item_url=resolve_url(TOPIC_PAGE, topic.id),
    )


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def delete_topic(request, topic_id):
    topic = _owned_topic(request, topic_id)
    return _delete(
        request,
        topic,
        services.delete_topic,
        title=f"Slette temaet {topic.name}?",
        lead=rules.topic_delete_lead(services.topic_delete_count(topic)),
        submit_label="Slett temaet",
        action=resolve_url("courses:delete_topic", topic.id),
        current_course=topic.course,
        after_url=resolve_url(COURSE_PAGE, topic.course_id),
        cancel_url=resolve_url(TOPIC_PAGE, topic.id),
    )


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def rename_source(request, source_id):
    source = _owned_source(request, source_id)
    return _rename(
        request,
        source,
        RenameSourceForm,
        services.rename_source,
        action=resolve_url("courses:rename_source", source.id),
        current_course=source.topic.course,
        item_url=resolve_url(TOPIC_PAGE, source.topic_id),
    )


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def delete_source(request, source_id):
    source = _owned_source(request, source_id)
    # The page the kilde was on survives its delete: back to a safe `next`, else «Kilder».
    back_url = safe_next(request) or f"{resolve_url(TOPIC_PAGE, source.topic_id)}?tab=sources"
    return _delete(
        request,
        source,
        services.delete_source,
        title=f"Slette kilden {source.name}?",
        lead=rules.source_delete_lead(),
        submit_label="Slett kilden",
        action=resolve_url("courses:delete_source", source.id),
        current_course=source.topic.course,
        after_url=back_url,
        cancel_url=back_url,
    )
