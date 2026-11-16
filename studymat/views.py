"""D05 «Legg til kilde» (FR-3, FR-20, NFR-7, AD-5 step 1).

A GET URL (AD-18): a full page normally, and the `dialog` partial in the one #dialog slot
under HTMX. A valid upload answers with HX-Location to the Topic's P05 (302 without HTMX);
a rejected one renders the dialog again with the reason in the upload-panel.

In Mock mode, «Bruk eksempeldokumentet» (`use_sample`) ingests the Sample document with the chosen
Detail level. When the Student has no Generation calls left today, the dialog shows the
daily-limit message with both submits disabled, and a POST anyway saves nothing.
"""

from django.core.files import File
from django.shortcuts import resolve_url
from django.views.decorators.http import require_http_methods

from ai import gateway, mock
from core.http import redirect_after_submit, render_page, vary_on_htmx
from core.messages import MESSAGES
from core.ownership import get_owned_or_404
from courses.models import Topic
from ingestion import extract
from ingestion.errors import IngestError, megabytes
from ingestion.services import ingest
from studymat.forms import AddSourceForm

# P05 lives in `web`; studymat names it by URL name only (AD-1 governs imports).
TOPIC_PAGE = "web:topic"

LIMITS = {"pages": extract.MAX_PAGES, "megabytes": megabytes(extract.MAX_FILE_BYTES)}

# The submit button that asks for the Sample document (Mock mode only).
USE_SAMPLE = "use_sample"


def _ingest_sample(topic, detail_level: str):
    with open(mock.SAMPLE_PATH, "rb") as handle:
        return ingest(topic, upload=File(handle, name=mock.SAMPLE_NAME), detail_level=detail_level)


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def add_source(request, topic_id):
    topic = get_owned_or_404(Topic.objects.select_related("course"), request.user, pk=topic_id)
    topic_url = resolve_url(TOPIC_PAGE, topic.id)
    mock_mode = gateway.mode() == gateway.MOCK
    # NFR-7: the message comes before anything is uploaded or sent (EXPERIENCE.md, D05).
    at_limit = gateway.remaining_today(request.user) == 0
    upload_error = None
    rejected_field = None
    if request.method == "POST" and not at_limit:
        use_sample = mock_mode and USE_SAMPLE in request.POST
        if use_sample:
            form = AddSourceForm(request.POST, use_sample=True)
        else:
            form = AddSourceForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                if use_sample:
                    _ingest_sample(topic, form.cleaned_data["detail_level"])
                else:
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
    elif request.method == "POST":
        # At the limit a POST saves nothing and validates nothing; the dialog keeps what was typed.
        form = AddSourceForm(initial={k: request.POST.get(k) for k in ("text", "name", "detail_level") if k in request.POST})
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
            "offer_sample": mock_mode,
            "daily_limit_message": MESSAGES["daily_limit"] if at_limit else None,
        },
    )
