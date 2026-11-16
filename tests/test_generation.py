"""FR-7, FR-8, FR-9 (story 6): generation, the claim and the source-row (AD-5, AD-19).

Gateway calls assert they are not inside a transaction, so these tests use `transaction=True`.
"""

import datetime

import pytest
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client
from django.urls import reverse

from ai import errors, gateway, mock
from ai.models import GenerationCallCount
from core import time
from core.messages import MESSAGES
from courses import services
from courses.models import STALE_AFTER, FailureReason, Source, Status
from ingestion.models import SourceText
from ingestion.services import ingest
from studymat import services as studymat_services
from studymat.models import Flashcard, KeyConcept, Question, Summary

pytestmark = pytest.mark.django_db(transaction=True)

OSLO = time.OSLO
NOON = datetime.datetime(2026, 11, 16, 12, 0, tzinfo=OSLO)
HTMX = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "source-1"}


def used(student) -> int:
    row = GenerationCallCount.objects.filter(student=student, day=time.today()).first()
    return row.count if row else 0


def use_up(student, n=gateway.DAILY_LIMIT):
    GenerationCallCount.objects.update_or_create(student=student, day=time.today(), defaults={"count": n})


def item_count(source) -> int:
    return sum(
        model.objects.filter(source=source).count() for model in (Summary, KeyConcept, Flashcard, Question)
    )


def retry_button(body: str) -> str:
    """The opening tag of the «Prøv igjen» button."""
    return body.split(">Prøv igjen</button>", 1)[0].rsplit("<button", 1)[1]


def generate_url(source):
    return reverse("studymat:generate", args=[source.id])


@pytest.fixture
def now(freeze_now):
    state = {"at": NOON}

    def advance(**delta):
        state["at"] = state["at"] + datetime.timedelta(**delta)
        freeze_now(state["at"])

    freeze_now(NOON)
    return advance


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def client_ida(ida):
    client = Client()
    client.force_login(ida)
    return client


@pytest.fixture
def topic(ida):
    return services.create_topic(services.create_course(ida, "Databaser"), "Normalisering")


@pytest.fixture
def sample(topic, now):
    with open(mock.SAMPLE_PATH, "rb") as handle:
        return ingest(topic, upload=File(handle, name=mock.SAMPLE_NAME), detail_level="medium")


@pytest.fixture
def other(topic, now):
    upload = SimpleUploadedFile("notater.txt", b"Normalisering fjerner redundans i tabeller.\n\nAndre avsnitt.")
    return ingest(topic, upload=upload, detail_level="short")


def fail_with(monkeypatch, error_class):
    def send(request):
        raise error_class()

    monkeypatch.setattr(gateway, "_send_generate", send)


# ---- Matrix: Sample, Mock ----------------------------------------------------------------


def test_fr7_sample_in_mock_mode_becomes_ready_with_checked_material(ida, sample):
    assert studymat_services.generate(ida, sample)
    sample.refresh_from_db()
    assert sample.status == Status.READY
    assert sample.language == "nb"
    assert (sample.removed_count, sample.dropped_count) == (1, 0)
    assert Summary.objects.get(source=sample).text == mock.summary("medium").summary
    assert Summary.objects.get(source=sample).detail_level == "medium"
    assert KeyConcept.objects.filter(source=sample).count() >= 5
    assert Flashcard.objects.filter(source=sample).count() >= 10
    assert Question.objects.filter(source=sample).count() >= 10
    assert set(Question.objects.filter(source=sample).values_list("kind", flat=True)) == {
        "multiple_choice",
        "free_text",
    }
    assert used(ida) == 1


def test_fr8_the_planted_bcnf_flashcard_is_removed(ida, sample):
    studymat_services.generate(ida, sample)
    assert not Flashcard.objects.filter(source=sample, front__contains="BCNF").exists()
    assert not Flashcard.objects.filter(source=sample, location_index=11).exists()


def test_fr7_every_saved_item_has_the_sources_student_and_a_reference(ida, sample):
    studymat_services.generate(ida, sample)
    for model in (KeyConcept, Flashcard, Question):
        rows = model.objects.filter(source=sample)
        assert rows.exists()
        assert set(rows.values_list("student_id", flat=True)) == {sample.student_id}
        assert all(row.quote and row.location_index >= 1 for row in rows)
    assert Summary.objects.get(source=sample).student_id == sample.student_id
    multiple_choice = Question.objects.filter(source=sample, kind="multiple_choice").first()
    assert len(multiple_choice.options) == 4
    assert set(multiple_choice.options[0]) == {"text", "explanation"}


def test_fr9_sample_row_reads_ready_with_one_item_removed(client_ida, sample):
    response = client_ida.post(generate_url(sample), **HTMX)
    assert response.status_code == 200
    body = response.content.decode()
    assert "Klar · 1 element fjernet" in body
    assert 'id="live-polite" hx-swap-oob="innerHTML"' in body
    assert "hx-trigger" not in body


def test_fr9_items_cascade_with_the_source(ida, sample):
    studymat_services.generate(ida, sample)
    services.delete_source(sample)
    assert sum(m.objects.count() for m in (Summary, KeyConcept, Flashcard, Question)) == 0


# ---- Matrix: Other file, Mock ------------------------------------------------------------


def test_fr9_other_file_in_mock_mode_fails_with_needs_key_and_saves_nothing(client_ida, ida, other):
    response = client_ida.post(generate_url(other), **HTMX)
    assert response.status_code == 200
    other.refresh_from_db()
    assert (other.status, other.failure_reason) == (Status.FAILED, FailureReason.NEEDS_KEY)
    assert item_count(other) == 0
    assert used(ida) == 0
    body = response.content.decode()
    assert MESSAGES["needs_key"] in body
    assert "Bruk eksempeldokumentet" in body
    assert reverse("studymat:add_source", args=[other.topic_id]) in body
    assert "Prøv igjen" not in body


# ---- Matrix: Provider error --------------------------------------------------------------


@pytest.mark.parametrize(
    "error_class",
    [errors.Truncated, errors.RateLimited, errors.Refused, errors.InvalidFormat, errors.ProviderUnavailable],
)
def test_fr9_a_provider_error_fails_with_its_code_saves_nothing_and_counts(client_ida, ida, sample, monkeypatch, error_class):
    fail_with(monkeypatch, error_class)
    response = client_ida.post(generate_url(sample), **HTMX)
    assert response.status_code == 200
    sample.refresh_from_db()
    assert (sample.status, sample.failure_reason) == (Status.FAILED, error_class.code)
    assert item_count(sample) == 0
    assert used(ida) == 1
    body = response.content.decode()
    assert MESSAGES[error_class.code] in body
    assert "disabled" not in retry_button(body)


def test_fr9_an_empty_summary_fails_as_invalid_format(ida, sample, monkeypatch):
    def send(request):
        material = mock.study_material(request.detail_level)
        material.summary = "  "
        return material

    monkeypatch.setattr(gateway, "_send_generate", send)
    studymat_services.generate(ida, sample)
    sample.refresh_from_db()
    assert (sample.status, sample.failure_reason) == (Status.FAILED, FailureReason.INVALID_FORMAT)
    assert item_count(sample) == 0


def test_fr9_six_failure_messages_are_in_core_messages():
    assert MESSAGES["timed_out"] == "Genereringen ble ikke ferdig. Prøv igjen."
    for code in ("truncated", "rate_limited", "refused", "invalid_format", "provider_unavailable"):
        assert MESSAGES[code]


# ---- Matrix: Retry -----------------------------------------------------------------------


def test_fr9_retry_claims_a_failed_source_again_and_reuses_source_text(client_ida, ida, sample, monkeypatch, now):
    fail_with(monkeypatch, errors.Truncated)
    studymat_services.generate(ida, sample)
    texts_before = list(SourceText.objects.filter(source=sample).values_list("id", "text"))
    monkeypatch.undo()
    now(minutes=1)

    response = client_ida.post(generate_url(sample))
    assert response.status_code == 302
    assert response["Location"] == reverse("web:topic", args=[sample.topic_id])
    sample.refresh_from_db()
    assert sample.status == Status.READY
    assert sample.failure_reason == ""
    assert sample.detail_level == "medium"
    assert list(SourceText.objects.filter(source=sample).values_list("id", "text")) == texts_before
    assert used(ida) == 2


# ---- Matrix: Double POST -----------------------------------------------------------------


def test_fr9_a_fresh_generating_source_is_not_sent_twice(client_ida, ida, sample, monkeypatch, now):
    assert services.claim(sample) is not None
    sent = []
    monkeypatch.setattr(gateway, "_send_generate", lambda request: sent.append(request))
    now(minutes=1)
    response = client_ida.post(generate_url(sample), **HTMX)
    assert response.status_code == 200
    assert sent == []
    assert used(ida) == 0
    assert "Lager studiemateriell" in response.content.decode()
    assert "hx-trigger" not in response.content.decode()


def test_fr9_claim_returns_none_for_a_ready_source(ida, sample):
    studymat_services.generate(ida, sample)
    assert services.claim(sample) is None
    assert not studymat_services.generate(ida, sample)
    assert used(ida) == 1


# ---- Matrix: Stale run -------------------------------------------------------------------


def test_fr9_a_stale_run_reads_failed_timed_out_and_retry_claims_it(client_ida, ida, sample, now):
    services.claim(sample)
    now(minutes=6)
    sample.refresh_from_db()
    assert sample.status == Status.GENERATING
    assert sample.effective_status == Status.FAILED
    assert sample.effective_failure_reason == FailureReason.TIMED_OUT

    page = client_ida.get(reverse("web:topic", args=[sample.topic_id])).content.decode()
    assert MESSAGES["timed_out"] in page and "Prøv igjen" in page

    client_ida.post(generate_url(sample), **HTMX)
    sample.refresh_from_db()
    assert sample.status == Status.READY


def test_fr9_effective_status_reads_pending_as_generating_and_fresh_run_as_generating(sample, now):
    assert sample.effective_status == Status.GENERATING
    services.claim(sample)
    now(seconds=STALE_AFTER.total_seconds() - 1)
    assert sample.effective_status == Status.GENERATING
    assert sample.effective_failure_reason == ""
    assert Source.objects.claimable().filter(pk=sample.pk).count() == 0
    now(seconds=2)
    assert Source.objects.claimable().filter(pk=sample.pk).count() == 1


# ---- Matrix: Late finish -----------------------------------------------------------------


def test_fr9_a_late_finish_after_a_newer_claim_saves_nothing(ida, sample, monkeypatch, now):
    def send(request):
        # A retry claims the stale Source while this run waits for the provider.
        now(minutes=6)
        assert services.claim(Source.objects.get(pk=sample.pk)) is not None
        return mock.study_material(request.detail_level)

    monkeypatch.setattr(gateway, "_send_generate", send)
    studymat_services.generate(ida, sample)
    fresh = Source.objects.get(pk=sample.pk)
    assert fresh.status == Status.GENERATING
    assert item_count(sample) == 0


def test_fr9_mark_functions_match_only_the_current_token(sample, now):
    old = services.claim(sample)
    now(minutes=6)
    new = services.claim(Source.objects.get(pk=sample.pk))
    assert old != new
    assert not services.mark_ready(sample, old, "nb", 0, 0)
    assert not services.mark_failed(sample, old, FailureReason.TRUNCATED)
    assert services.mark_failed(sample, new, FailureReason.TRUNCATED)
    assert Source.objects.get(pk=sample.pk).failure_reason == FailureReason.TRUNCATED


# ---- Matrix: Daily limit -----------------------------------------------------------------


def test_nfr7_a_pending_source_at_the_limit_fails_with_daily_limit(client_ida, ida, sample, monkeypatch):
    use_up(ida)
    sent = []
    monkeypatch.setattr(gateway, "_send_generate", lambda request: sent.append(request))
    response = client_ida.post(generate_url(sample), **HTMX)
    assert response.status_code == 200
    sample.refresh_from_db()
    assert (sample.status, sample.failure_reason) == (Status.FAILED, FailureReason.DAILY_LIMIT)
    assert sent == []
    body = response.content.decode()
    button = retry_button(body)
    assert "disabled" in button
    assert f'aria-describedby="source-{sample.id}-reason"' in button
    row = body.split('id="live-polite"', 1)[0]
    assert row.count(MESSAGES["daily_limit"]) == 1
    assert f'id="source-{sample.id}-reason"' in row


def test_nfr7_a_retry_post_at_the_limit_sends_nothing_and_keeps_the_reason(client_ida, ida, sample, monkeypatch):
    fail_with(monkeypatch, errors.Truncated)
    studymat_services.generate(ida, sample)
    use_up(ida)
    response = client_ida.post(generate_url(sample), **HTMX)
    sample.refresh_from_db()
    assert (sample.status, sample.failure_reason) == (Status.FAILED, FailureReason.TRUNCATED)
    assert used(ida) == gateway.DAILY_LIMIT
    body = response.content.decode()
    assert MESSAGES["daily_limit"] in body
    page = client_ida.get(reverse("web:topic", args=[sample.topic_id])).content.decode()
    assert "disabled" in retry_button(page)


def test_nfr7_a_stale_row_at_the_limit_is_not_claimed_and_keeps_timed_out(client_ida, ida, sample, monkeypatch, now):
    services.claim(sample)
    started_at = Source.objects.get(pk=sample.pk).started_at
    now(minutes=6)
    use_up(ida)
    sent = []
    monkeypatch.setattr(gateway, "_send_generate", lambda request: sent.append(request))
    response = client_ida.post(generate_url(sample), **HTMX)
    assert response.status_code == 200
    sample.refresh_from_db()
    assert sample.status == Status.GENERATING
    assert sample.started_at == started_at
    assert sample.effective_failure_reason == FailureReason.TIMED_OUT
    assert used(ida) == gateway.DAILY_LIMIT
    assert sent == []


# ---- Matrix: Not owned -------------------------------------------------------------------


def test_fr9_another_students_source_is_404_and_untouched(student, sample):
    jonas = Client()
    jonas.force_login(student("jonas@example.no"))
    assert jonas.post(generate_url(sample), **HTMX).status_code == 404
    sample.refresh_from_db()
    assert sample.status == Status.PENDING


def test_ad18_generate_requires_csrf(ida, sample):
    client = Client(enforce_csrf_checks=True)
    client.force_login(ida)
    response = client.post(generate_url(sample))
    assert response.status_code == 403
    sample.refresh_from_db()
    assert sample.status == Status.PENDING
    assert used(ida) == 0


def test_fr9_generate_is_post_only(client_ida, sample):
    assert client_ida.get(generate_url(sample)).status_code == 405


# ---- The pending row and P05 -------------------------------------------------------------


def test_fr9_a_pending_row_starts_generation_with_one_post_on_load(client_ida, sample):
    page = client_ida.get(reverse("web:topic", args=[sample.topic_id])).content.decode()
    row = page.split('id="source-%d"' % sample.id, 1)[1].split(">", 1)[0]
    assert f'hx-post="{generate_url(sample)}"' in row
    assert 'hx-trigger="load"' in row
    assert 'hx-swap="outerHTML"' in row
    assert "Lager studiemateriell" in page
    assert page.count('hx-trigger="load"') == 1


# ---- AD-19: claim committed, gateway outside atomic --------------------------------------


def test_fr9_the_claim_is_committed_before_the_gateway_call_outside_any_transaction(ida, sample, monkeypatch):
    seen = []

    def send(request):
        assert not connection.in_atomic_block
        seen.append(Source.objects.get(pk=sample.pk).status)
        return mock.study_material(request.detail_level)

    monkeypatch.setattr(gateway, "_send_generate", send)
    studymat_services.generate(ida, sample)
    assert seen == [Status.GENERATING]


def test_fr9_the_request_carries_only_non_empty_locations(ida, topic, monkeypatch, now):
    from tests.pdfs import IMAGE_ONLY, LECTURE_TEXT, make_pdf

    upload = SimpleUploadedFile("f.pdf", make_pdf([LECTURE_TEXT, IMAGE_ONLY, LECTURE_TEXT]))
    source = ingest(topic, upload=upload, detail_level="detailed")
    seen = []
    monkeypatch.setattr(gateway, "_send_generate", lambda request: seen.append(request) or (_ for _ in ()).throw(errors.Refused()))
    monkeypatch.setattr(mock, "is_sample", lambda sha: True)
    studymat_services.generate(ida, source)
    assert [loc.index for loc in seen[0].locations] == [1, 3]
    assert seen[0].detail_level == "detailed"
