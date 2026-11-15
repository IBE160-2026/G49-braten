"""D05 «Legg til kilde» (FR-3, AD-5 step 1).

A GET URL (AD-18): a full page normally, and the `dialog` partial in the one #dialog slot
under HTMX. A valid upload answers with HX-Location to the Topic's P05 (302 without HTMX);
a rejected one renders the dialog again with the reason in the upload-panel.
"""

from django.shortcuts import resolve_url
from django.views.decorators.http import require_http_methods

from core.http import redirect_after_submit, render_page, vary_on_htmx
from core.ownership import get_owned_or_404
from courses.models import Topic
from ingestion import extract
from ingestion.errors import IngestError, megabytes
from ingestion.services import ingest
from studymat.forms import AddSourceForm

# P05 lives in `web`; studymat names it by URL name only (AD-1 governs imports).
TOPIC_PAGE = "web:topic"

LIMITS = {"pages": extract.MAX_PAGES, "megabytes": megabytes(extract.MAX_FILE_BYTES)}


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def add_source(request, topic_id):
    topic = get_owned_or_404(Topic.objects.select_related("course"), request.user, pk=topic_id)
    topic_url = resolve_url(TOPIC_PAGE, topic.id)
    upload_error = None
    rejected_field = None
    if request.method == "POST":
        form = AddSourceForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                ingest(
                    topic,
                    upload=form.cleaned_data["file"] or None,
                    text=form.cleaned_data["text"],
                    name=form.cleaned_data["name"],
                    detail_level=form.cleaned_data["detail_level"],
                )
            except IngestError as error:
                upload_error = error.message
                rejected_field = form.reject(error)
            else:
                return redirect_after_submit(request, topic_url)
    else:
        form = AddSourceForm()
    return render_page(
        request,
        "studymat/add_source.html",
        {
            "form": form,
            "topic": topic,
            "current_course": topic.course,
            "action": resolve_url("studymat:add_source", topic.id),
            "cancel_url": topic_url,
            "upload_error": upload_error,
            # «Velg en annen fil» only when the rejection is about the file.
            "file_rejected": rejected_field == "file",
            "limits": LIMITS,
        },
    )
