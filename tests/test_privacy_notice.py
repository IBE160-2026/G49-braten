"""FR-22, AD-17, AD-18 (story 10): D04 «Før du laster opp», `accept_privacy` and Real mode end to end.

Gateway calls assert they are not inside a transaction, so these tests use `transaction=True`.
"""

import datetime
from urllib.parse import quote

import pytest
from django.core.files import File
from django.test import Client
from django.urls import reverse

from accounts.models import Student
from accounts.services import accept_privacy
from ai import anthropic_adapter, mock
from ai.models import GenerationCallCount
from core import time
from core.messages import MESSAGES
from courses import services
from courses.models import FailureReason, Source, Status
from ingestion.services import ingest
from studymat import services as studymat_services
from studymat.models import Question
from tests.test_anthropic_adapter import KEY, FakeAPI, error_response, reply

pytestmark = pytest.mark.django_db(transaction=True)

HTMX_DIALOG = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "dialog"}
TITLE = "Før du laster opp"
LEAD = (
    "Når du laster opp en kilde, sendes teksten i den til KI-tjenesten som lager studiemateriellet. "
    "Noen gratisnivåer kan bruke innsendt innhold til å forbedre leverandørens produkter. "
    "Du må godta dette før du kan laste opp."
)
ACCEPT = "Jeg forstår, fortsett"
NOON = datetime.datetime(2026, 11, 18, 12, 0, tzinfo=time.OSLO)


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
def real(settings):
    settings.AI_PROVIDER = "anthropic"
    settings.ANTHROPIC_API_KEY = KEY


def add_url(topic) -> str:
    return reverse("studymat:add_source", args=[topic.id])


def privacy_url(next_url: str = "", cancel: str = "") -> str:
    url = reverse("studymat:privacy")
    query = []
    if next_url:
        query.append(f"next={quote(next_url, safe='')}")
    if cancel:
        query.append(f"cancel={quote(cancel, safe='')}")
    return f"{url}?{'&'.join(query)}" if query else url


def accepted_at(student) -> datetime.datetime | None:
    return Student.objects.get(pk=student.pk).privacy_accepted_at


def sources() -> int:
    return Source.objects.count()


# ---- accept_privacy (the only writer) ------------------------------------------------------


def test_fr22_accept_privacy_on_a_stale_copy_keeps_the_first_time(ida, freeze_now):
    stale = Student.objects.get(pk=ida.pk)
    freeze_now(NOON)
    accept_privacy(ida)
    assert stale.privacy_accepted_at is None
    freeze_now(NOON + datetime.timedelta(hours=2))
    accept_privacy(stale)
    assert accepted_at(ida) == NOON
    assert stale.privacy_accepted_at == NOON


def test_fr22_accept_privacy_sets_the_time_once(ida, freeze_now):
    freeze_now(NOON)
    accept_privacy(ida)
    assert accepted_at(ida) == NOON and ida.privacy_accepted_at == NOON
    freeze_now(NOON + datetime.timedelta(days=1))
    accept_privacy(Student.objects.get(pk=ida.pk))
    assert accepted_at(ida) == NOON


# ---- D04 as its own dialog URL (AD-18) -----------------------------------------------------


def test_fr22_d04_renders_as_a_page_and_as_a_dialog_partial(real, client_ida, topic):
    page = client_ida.get(privacy_url(add_url(topic)))
    assert page.status_code == 200
    body = page.content.decode()
    assert TITLE in body and LEAD in body and ACCEPT in body and "Avbryt" in body
    assert "Ingenting sendes før du velger «Jeg forstår, fortsett»." in body
    assert '<div class="dialog-page">' in body
    assert f'name="next" value="{add_url(topic)}"' in body
    assert f'action="{reverse("studymat:privacy")}"' in body

    partial = client_ida.get(privacy_url(add_url(topic)), **HTMX_DIALOG)
    fragment = partial.content.decode()
    assert fragment.lstrip().startswith("<dialog")
    assert TITLE in fragment and LEAD in fragment
    assert 'aria-describedby="dialog-lead"' in fragment
    assert "HX-Request" in partial["Vary"]


def test_fr22_showing_d04_stores_nothing(real, client_ida, ida, topic):
    client_ida.get(privacy_url(add_url(topic)))
    client_ida.get(privacy_url(add_url(topic)), **HTMX_DIALOG)
    assert accepted_at(ida) is None


def test_fr22_avbryt_goes_to_cancel_else_next_else_home(real, client_ida, topic):
    topic_url = reverse("web:topic", args=[topic.id])
    body = client_ida.get(privacy_url(add_url(topic), cancel=topic_url)).content.decode()
    assert f'href="{topic_url}" data-dialog-close>Avbryt' in body
    body = client_ida.get(privacy_url(topic_url)).content.decode()
    assert f'href="{topic_url}" data-dialog-close>Avbryt' in body
    body = client_ida.get(privacy_url()).content.decode()
    assert f'href="{reverse("web:home")}" data-dialog-close>Avbryt' in body


def test_fr22_accept_stores_the_time_and_lands_on_next(real, client_ida, ida, topic):
    topic_url = reverse("web:topic", args=[topic.id])
    response = client_ida.post(reverse("studymat:privacy"), {"next": topic_url})
    assert response.status_code == 302 and response["Location"] == topic_url
    assert accepted_at(ida) is not None


def test_fr22_accept_under_htmx_answers_with_hx_location(real, client_ida, topic):
    topic_url = reverse("web:topic", args=[topic.id])
    response = client_ida.post(reverse("studymat:privacy"), {"next": topic_url}, **HTMX_DIALOG)
    assert topic_url in response["HX-Location"]


@pytest.mark.parametrize("bad", ["https://evil.example", "//evil.example/x", "javascript:alert(1)", ""])
def test_fr22_bad_next_falls_back_to_hjem(real, client_ida, ida, bad):
    response = client_ida.post(reverse("studymat:privacy"), {"next": bad})
    assert response["Location"] == reverse("web:home")
    assert accepted_at(ida) is not None
    body = client_ida.get(privacy_url(bad) if bad else privacy_url()).content.decode()
    assert "evil.example" not in body


def test_fr22_d04_needs_a_signed_in_student(real, topic):
    response = Client().get(privacy_url(add_url(topic)))
    assert response.status_code == 302 and reverse("accounts:sign_in") in response["Location"]


def test_fr22_an_accepted_student_is_not_shown_d04_again(real, client_ida, ida, topic):
    accept_privacy(ida)
    topic_url = reverse("web:topic", args=[topic.id])
    response = client_ida.get(privacy_url(topic_url))
    assert response.status_code == 302 and response["Location"] == topic_url


# ---- Mock mode: no D04 ---------------------------------------------------------------------


def test_fr20_mock_mode_d04_redirects_to_next_and_shows_nothing(client_ida, ida, topic):
    response = client_ida.get(privacy_url(add_url(topic)))
    assert response.status_code == 302 and response["Location"] == add_url(topic)
    response = client_ida.post(reverse("studymat:privacy"), {"next": add_url(topic)})
    assert response["Location"] == add_url(topic)
    assert accepted_at(ida) is None


def test_fr20_no_key_means_mock_mode_and_d05_without_d04(settings, client_ida, topic):
    settings.ANTHROPIC_API_KEY = ""
    for response in (client_ida.get(add_url(topic)), client_ida.get(add_url(topic), **HTMX_DIALOG)):
        body = response.content.decode()
        assert TITLE not in body and "Legg til kilde" in body


# ---- Where D04 appears: before D05 ---------------------------------------------------------


def test_fr22_first_upload_in_real_mode_shows_d04_instead_of_d05(real, client_ida, topic):
    topic_url = reverse("web:topic", args=[topic.id])
    for response in (client_ida.get(add_url(topic)), client_ida.get(add_url(topic), **HTMX_DIALOG)):
        body = response.content.decode()
        assert TITLE in body and LEAD in body
        assert "Last opp" not in body
        assert f'name="next" value="{add_url(topic)}"' in body
        # «Avbryt» goes back to the Topic, not to D05.
        assert f'href="{topic_url}" data-dialog-close>Avbryt' in body


def test_fr22_a_d05_post_before_acceptance_saves_nothing_and_shows_d04(real, client_ida, ida, topic):
    response = client_ida.post(
        add_url(topic), {"text": "Normalisering fjerner redundans. " * 5, "detail_level": "medium"}, **HTMX_DIALOG
    )
    assert response.status_code == 200 and "HX-Location" not in response
    assert TITLE in response.content.decode()
    assert sources() == 0
    assert accepted_at(ida) is None


def test_fr22_accept_from_the_d05_gate_opens_d05(real, client_ida, ida, topic):
    response = client_ida.post(reverse("studymat:privacy"), {"next": add_url(topic)})
    assert response["Location"] == add_url(topic)
    body = client_ida.get(add_url(topic)).content.decode()
    assert TITLE not in body and "Last opp" in body


def test_fr22_accept_from_the_d05_gate_under_htmx_swaps_d05_into_the_dialog(real, client_ida, ida, topic):
    response = client_ida.post(reverse("studymat:privacy"), {"next": add_url(topic)}, **HTMX_DIALOG)
    assert "HX-Location" not in response
    fragment = response.content.decode()
    assert fragment.lstrip().startswith("<dialog")
    assert "Legg til kilde" in fragment and "Last opp" in fragment and TITLE not in fragment
    assert accepted_at(ida) is not None


def test_nfr7_accept_from_the_d05_gate_at_the_daily_limit_shows_d05_with_the_limit(real, client_ida, ida, topic):
    GenerationCallCount.objects.create(student=ida, day=time.today(), count=20)
    response = client_ida.post(reverse("studymat:privacy"), {"next": add_url(topic)}, **HTMX_DIALOG)
    fragment = response.content.decode()
    assert "Last opp" in fragment and TITLE not in fragment
    assert MESSAGES["daily_limit"] in fragment
    upload = fragment.split('<button class="button-primary" type="submit"', 1)[1].split(">", 1)[0]
    assert "disabled" in upload
    hidden = fragment.split('<button class="visually-hidden" type="submit"', 1)
    if len(hidden) > 1:
        assert "disabled" in hidden[1].split(">", 1)[0]


def test_fr22_another_students_topic_in_next_is_404_not_shown(real, client_ida, student):
    other = services.create_topic(services.create_course(student("jonas@example.no"), "Fag"), "Tema")
    response = client_ida.post(reverse("studymat:privacy"), {"next": add_url(other)}, **HTMX_DIALOG)
    assert response.status_code == 404


def test_fr22_after_acceptance_d05_uploads(real, client_ida, ida, topic):
    accept_privacy(ida)
    response = client_ida.post(
        add_url(topic), {"text": "Normalisering fjerner redundans. " * 5, "detail_level": "medium"}, **HTMX_DIALOG
    )
    assert "HX-Location" in response
    assert sources() == 1


# ---- Accept elsewhere: the source-row --------------------------------------------------------


@pytest.fixture
def pasted(topic, freeze_now):
    freeze_now(NOON)
    return ingest(topic, text="Normalisering fjerner redundans i tabeller. " * 5, name="Notat", detail_level="medium")


def used(student) -> int:
    row = GenerationCallCount.objects.filter(student=student, day=time.today()).first()
    return row.count if row else 0


def test_fr22_generation_before_acceptance_fails_with_the_message_and_a_d04_link(
    real, client_ida, ida, topic, pasted, monkeypatch
):
    fake = FakeAPI(reply({"summary": "x"}))
    monkeypatch.setattr(anthropic_adapter, "_client", fake.client)
    response = client_ida.post(
        reverse("studymat:generate", args=[pasted.id]), HTTP_HX_REQUEST="true", HTTP_HX_TARGET=f"source-{pasted.id}"
    )
    pasted.refresh_from_db()
    assert pasted.status == Status.FAILED and pasted.failure_reason == FailureReason.PRIVACY_NOT_ACCEPTED
    assert used(ida) == 0 and fake.requests == []
    body = response.content.decode()
    assert MESSAGES["privacy_not_accepted"] in body
    sources_tab = f"{reverse('web:topic', args=[topic.id])}?tab=sources"
    link = privacy_url(sources_tab)
    assert MESSAGES["privacy_notice_link"] in body
    # The link's next is the page (menu_next), not the POST URL.
    assert f'hx-get="{reverse("studymat:privacy")}?next=' in body
    assert "generate" not in body.split("?next=", 1)[1].split('"', 1)[0]

    page = client_ida.get(sources_tab).content.decode()
    assert MESSAGES["privacy_not_accepted"] in page
    assert link.split("?")[0] in page
    # Retrying can only fail again, so «Les og godta varselet» is the only action.
    assert "Prøv igjen" not in page and "Prøv igjen" not in body


def test_fr22_accept_elsewhere_then_prov_igjen_sends(real, client_ida, ida, topic, monkeypatch, freeze_now):
    freeze_now(NOON)
    with open(mock.SAMPLE_PATH, "rb") as handle:
        source = ingest(topic, upload=File(handle, name=mock.SAMPLE_NAME), detail_level="medium")
    studymat_services.generate(ida, source)
    source.refresh_from_db()
    assert source.failure_reason == FailureReason.PRIVACY_NOT_ACCEPTED

    sources_tab = f"{reverse('web:topic', args=[topic.id])}?tab=sources"
    response = client_ida.post(reverse("studymat:privacy"), {"next": sources_tab}, **HTMX_DIALOG)
    assert sources_tab in response["HX-Location"]
    page = client_ida.get(sources_tab).content.decode()
    assert MESSAGES["privacy_notice_link"] not in page  # accepted: no link any more
    assert "Prøv igjen" in page

    fake = FakeAPI(reply(mock.study_material("medium").model_dump()))
    monkeypatch.setattr(anthropic_adapter, "_client", fake.client)
    client_ida.post(reverse("studymat:generate", args=[source.id]))
    source.refresh_from_db()
    assert source.status == Status.READY
    assert len(fake.requests) == 1 and used(ida) == 1


# ---- Acceptance: Real mode end to end ------------------------------------------------------


def test_fr21_real_mode_valid_reply_runs_the_reference_check_and_the_source_is_ready(real, ida, topic, monkeypatch, freeze_now):
    freeze_now(NOON)
    accept_privacy(ida)
    with open(mock.SAMPLE_PATH, "rb") as handle:
        source = ingest(topic, upload=File(handle, name=mock.SAMPLE_NAME), detail_level="medium")
    fake = FakeAPI(reply(mock.study_material("medium").model_dump()))
    monkeypatch.setattr(anthropic_adapter, "_client", fake.client)
    studymat_services.generate(Student.objects.get(pk=ida.pk), source)
    source.refresh_from_db()
    assert source.status == Status.READY
    # The recording's one planted wrong Reference is removed by the real check (AD-4).
    assert source.removed_count == 1
    assert Question.objects.filter(source=source).exists()
    assert used(ida) == 1
    sent = fake.body["messages"][0]["content"]
    assert "[[L1]]" in sent


@pytest.mark.parametrize(
    ("answer", "code"),
    [
        (error_response(401, "authentication_error"), FailureReason.KEY_REJECTED),
        (error_response(429, "rate_limit_error"), FailureReason.RATE_LIMITED),
        (reply(None, stop_reason="refusal", text="Nei."), FailureReason.REFUSED),
        (reply(None, stop_reason="max_tokens", text='{"summ'), FailureReason.TRUNCATED),
        (reply(None, text="ikke json"), FailureReason.INVALID_FORMAT),
    ],
)
def test_fr21_real_mode_failures_are_stored_counted_and_named(real, client_ida, ida, pasted, monkeypatch, answer, code):
    accept_privacy(ida)
    monkeypatch.setattr(anthropic_adapter, "_client", FakeAPI(answer).client)
    response = client_ida.post(
        reverse("studymat:generate", args=[pasted.id]), HTTP_HX_REQUEST="true", HTTP_HX_TARGET=f"source-{pasted.id}"
    )
    pasted.refresh_from_db()
    assert pasted.status == Status.FAILED and pasted.failure_reason == code
    assert used(ida) == 1
    body = response.content.decode()
    assert MESSAGES[code] in body and "Prøv igjen" in body
    assert KEY not in body


def test_nfr4_the_key_is_never_rendered(real, client_ida, ida, topic, pasted):
    pages = [
        client_ida.get(privacy_url(add_url(topic))),
        client_ida.get(privacy_url(add_url(topic)), **HTMX_DIALOG),
        client_ida.get(add_url(topic)),
        client_ida.get(f"{reverse('web:topic', args=[topic.id])}?tab=sources"),
    ]
    for response in pages:
        assert KEY not in response.content.decode()
        assert KEY not in str(response.headers)
