"""D05 «Legg til kilde» (FR-3, FR-20, NFR-7, AD-5 step 1) and D09 for one item (FR-24).

A GET URL (AD-18): a full page normally, and the `dialog` partial in the one #dialog slot
under HTMX. A valid upload answers with HX-Location to the Topic's P05 «Kilder» tab (302
without HTMX), where its status lives; a rejected one renders the dialog again with the reason
in the upload-panel.

In Mock mode, «Bruk eksempeldokumentet» (`use_sample`) ingests the Sample document with the chosen
Detail level. When the Student has no Generation calls left today, the dialog shows the
daily-limit message with both submits disabled, and a POST anyway saves nothing.

D04 «Før du laster opp» (FR-22, AD-17) is its own dialog URL, `studymat:privacy?next=…`. In Real
mode, until the Student accepts, D05 shows D04 instead (with `next` = D05) and a D05 POST saves
nothing. The gateway is the guard; D04 only asks.
"""

from urllib.parse import urlsplit

from django.core.files import File
from django.http import Http404
from django.shortcuts import redirect, render, resolve_url
from django.urls import Resolver404, resolve, reverse
from django.views.decorators.http import require_http_methods, require_POST

from accounts import services as accounts_services
from ai import gateway, mock
from core.http import DIALOG_TARGET, htmx_target, redirect_after_submit, render_page, safe_next, vary_on_htmx
from core.messages import MESSAGES
from core.ownership import get_owned_or_404
from courses.models import Source, Status, Topic
from ingestion import extract
from ingestion.errors import IngestError, megabytes
from ingestion.services import ingest
from studymat import services
from studymat.forms import AddSourceForm
from studymat.models import Flashcard, KeyConcept, Question

# P05 and Hjem live in `web`; studymat names them by URL name only (AD-1 governs imports).
TOPIC_PAGE = "web:topic"
HOME_PAGE = "web:home"

# D09 for one item (FR-24): the URL kind -> (model, the P05 tab it is shown on).
ITEM_KINDS = {
    "concept": (KeyConcept, "summary"),
    "card": (Flashcard, "selftest"),
    "question": (Question, "quiz"),
}


def topic_tab_url(topic_id, tab: str) -> str:
    """P05 with one tab selected (`web:topic?tab=…`)."""
    return f"{resolve_url(TOPIC_PAGE, topic_id)}?tab={tab}"

LIMITS = {"pages": extract.MAX_PAGES, "megabytes": megabytes(extract.MAX_FILE_BYTES)}

# The submit button that asks for the Sample document (Mock mode only).
USE_SAMPLE = "use_sample"


def _ingest_sample(topic, detail_level: str):
    with open(mock.SAMPLE_PATH, "rb") as handle:
        return ingest(topic, upload=File(handle, name=mock.SAMPLE_NAME), detail_level=detail_level)


def needs_privacy_notice(student) -> bool:
    """D04 comes first: Real mode and the Student has not accepted the notice (FR-22)."""
    return gateway.mode() == gateway.REAL and student.privacy_accepted_at is None


def _render_privacy(request, next_url: str, cancel_url: str):
    return render_page(
        request,
        "studymat/privacy_notice.html",
        {
            "action": reverse("studymat:privacy"),
            "next": next_url,
            "cancel_url": cancel_url,
        },
    )


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def privacy(request):
    """D04 «Før du laster opp» (FR-22, AD-18 dialog). POST accepts and lands on a safe `next`, else Hjem.

    «Avbryt» goes to a safe `cancel`, else to `next`, else Hjem; nothing is stored. In Mock mode the URL
    goes straight to `next` and shows nothing.
    """
    next_url = safe_next(request)
    landing = next_url or resolve_url(HOME_PAGE)
    if gateway.mode() == gateway.MOCK or (request.method == "GET" and request.user.privacy_accepted_at):
        # Nothing to ask: Mock mode never shows D04, and an accepted notice is not shown again.
        return redirect_after_submit(request, landing)
    if request.method == "POST":
        accounts_services.accept_privacy(request.user)
        # Accepted from D05's gate inside #dialog: open D05 in the same slot, without leaving the page.
        topic_id = _add_source_topic(next_url)
        if topic_id is not None and htmx_target(request) == DIALOG_TARGET:
            topic = get_owned_or_404(Topic.objects.select_related("course"), request.user, pk=topic_id)
            return _render_add_source(request, topic, AddSourceForm())
        return redirect_after_submit(request, landing)
    return _render_privacy(request, next_url, safe_next(request, "cancel") or landing)


def _add_source_topic(url: str) -> int | None:
    """The Topic id when `url` is D05 (`studymat:add_source`), else None."""
    if not url:
        return None
    try:
        match = resolve(urlsplit(url).path)
    except Resolver404:
        return None
    if match.view_name != "studymat:add_source":
        return None
    return match.kwargs["topic_id"]


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def add_source(request, topic_id):
    topic = get_owned_or_404(Topic.objects.select_related("course"), request.user, pk=topic_id)
    if needs_privacy_notice(request.user):
        # FR-22: D04 before D05; a D05 POST saves nothing. «Avbryt» goes back to the Topic.
        return _render_privacy(request, resolve_url("studymat:add_source", topic.id), resolve_url(TOPIC_PAGE, topic.id))
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
                # The new kilde's status and «Prøv igjen» live on «Kilder» (story 7, Landing).
                return redirect_after_submit(request, topic_tab_url(topic.id, "sources"))
    elif request.method == "POST":
        # At the limit a POST saves nothing and validates nothing; the dialog keeps what was typed.
        form = AddSourceForm(initial={k: request.POST.get(k) for k in ("text", "name", "detail_level") if k in request.POST})
    else:
        form = AddSourceForm()
    return _render_add_source(
        request, topic, form, upload_error=upload_error, rejected_field=rejected_field, at_limit=at_limit
    )


def _render_add_source(request, topic, form, *, upload_error=None, rejected_field=None, at_limit=None):
    """D05 as a page or as the #dialog partial."""
    if at_limit is None:
        at_limit = gateway.remaining_today(request.user) == 0
    mock_mode = gateway.mode() == gateway.MOCK
    topic_url = resolve_url(TOPIC_PAGE, topic.id)
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


@require_POST
@vary_on_htmx
def generate(request, source_id):
    """AD-5 step 2 for one owned Source (404 otherwise); idempotent through the claim.

    Under HTMX it answers with the source-row plus the #live-polite status text; otherwise 302 to
    P05's «Kilder» tab. At the daily limit a failed or stale row is not claimed and nothing is sent; a pending row
    still runs, so the gateway marks it failed with `daily_limit` (or `needs_key` first, AD-3).
    """
    source = get_owned_or_404(Source, request.user, pk=source_id)
    blocked = gateway.remaining_today(request.user) == 0
    if not blocked or source.status == Status.PENDING:
        services.generate(request.user, source)
        source.refresh_from_db()
    sources_tab = topic_tab_url(source.topic_id, "sources")
    if not getattr(request, "htmx", None):
        return redirect(sources_tab)
    return render(
        request,
        "studymat/source_row.html",
        {
            "source": source,
            "generation_blocked": gateway.remaining_today(request.user) == 0,
            # The row's «⋯» menu returns to the page, not to this POST URL.
            "menu_next": sources_tab,
        },
    )


def _delete_copy(kind: str, item) -> tuple[str, str]:
    """D09's title and destructive button for one item (EXPERIENCE.md, dialog)."""
    if kind == "concept":
        return f"Slette nøkkelbegrepet {item.term}?", "Slett nøkkelbegrepet"
    if kind == "card":
        return "Slette kortet?", "Slett kortet"
    return "Slette spørsmålet?", "Slett spørsmålet"


@require_http_methods(["GET", "POST"])
@vary_on_htmx
def delete_item(request, kind, item_id):
    """D09 for one Key concept, Flashcard or Question (FR-24): owned or 404, a hard delete (AD-8).

    GET confirms (the `courses/delete.html` alertdialog); POST deletes and lands on a safe `next`,
    else on the P05 tab that shows the item. «Avbryt» goes to a safe `cancel`, else to the same
    place. No toast, no undo.
    """
    if kind not in ITEM_KINDS:
        raise Http404
    model, tab = ITEM_KINDS[kind]
    item = get_owned_or_404(model.objects.select_related("source__topic__course"), request.user, pk=item_id)
    topic = item.source.topic
    next_url = safe_next(request)
    back_url = next_url or topic_tab_url(topic.id, tab)
    # «Avbryt» may go elsewhere than the delete lands, e.g. back to the P06 position (story 8b).
    cancel_url = safe_next(request, "cancel") or back_url
    if request.method == "POST":
        services.delete_item(request.user, item)
        return redirect_after_submit(request, back_url)
    title, submit_label = _delete_copy(kind, item)
    return render_page(
        request,
        "courses/delete.html",
        {
            "item": item,
            "title": title,
            "lead": MESSAGES["delete_cannot_undo"],
            "submit_label": submit_label,
            "action": resolve_url("studymat:delete_item", kind, item.id),
            "current_course": topic.course,
            "next": next_url,
            "cancel_url": cancel_url,
        },
    )
