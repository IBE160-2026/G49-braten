"""FR-3 (story 4): D05 «Legg til kilde» on P05 — dialog mechanics, rejections, ownership."""

import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from accounts.services import accept_privacy
from courses import services
from courses.models import Source, SourceKind, Status
from ingestion.errors import MEGABYTE
from ingestion.models import SourceText
from tests.pdfs import IMAGE_ONLY, LECTURE_TEXT, make_pdf

pytestmark = pytest.mark.django_db

HTMX_DIALOG = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "dialog"}
NOT_FOUND = "Fant ikke siden"


def add_url(topic):
    return reverse("studymat:add_source", args=[topic.id])


def sources_tab_url(topic):
    """P05 with «Kilder» selected: where a valid upload lands (story 7, Landing)."""
    return reverse("web:topic", args=[topic.id]) + "?tab=sources"


def vary(response) -> set[str]:
    return {v.strip().lower() for v in response.get("Vary", "").split(",")}


def main_of(content: str) -> str:
    return content.split('<main id="main"', 1)[1].split("</main>", 1)[0]


def pdf_file(name="forelesning-3.pdf", pages=(LECTURE_TEXT, IMAGE_ONLY, LECTURE_TEXT)):
    return SimpleUploadedFile(name, make_pdf(list(pages)), content_type="application/pdf")


def tag_of(body: str, start: str) -> str:
    """The opening tag that begins with `start`."""
    return start + body.split(start, 1)[1].split(">", 1)[0]


def counts():
    return Source.objects.count(), SourceText.objects.count()


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def client_ida(ida):
    client = Client()
    client.force_login(ida)
    return client


@pytest.fixture
def normalisering(ida):
    return services.create_topic(services.create_course(ida, "Databaser", "DAT102"), "Normalisering")


@pytest.fixture
def jonas_topic(student):
    jonas = student("jonas@example.no")
    return services.create_topic(services.create_course(jonas, "Jonas sitt fag"), "Jonas sitt tema")


# ---- D05 as a page and as a dialog (AD-13, AD-18) ---------------------------------------


def test_fr3_d05_is_a_page_without_htmx_and_a_dialog_partial_with_it(client_ida, normalisering):
    page = client_ida.get(add_url(normalisering))
    content = page.content.decode()
    assert content.startswith("<!doctype html>")
    assert "<title>Legg til kilde – Normalisering – AI Study Buddy</title>" in content
    assert 'enctype="multipart/form-data"' in content
    assert f'action="{add_url(normalisering)}"' in content
    partial = client_ida.get(add_url(normalisering), **HTMX_DIALOG)
    body = partial.content.decode()
    assert body.lstrip().startswith("<dialog")
    assert "<html" not in body
    assert f'hx-post="{add_url(normalisering)}"' in body
    assert 'enctype="multipart/form-data"' in body
    for response in (page, partial):
        assert response.status_code == 200
        assert {"hx-request", "hx-target", "hx-history-restore-request"} <= vary(response)


def test_fr3_d05_shows_file_paste_limits_detail_level_and_upload(client_ida, normalisering):
    body = client_ida.get(add_url(normalisering), **HTMX_DIALOG).content.decode()
    assert "Velg fil" in body
    assert 'type="file"' in body and 'name="file"' in body
    assert "Lim inn tekst" in body and "<textarea" in body
    assert "PDF eller tekstfil · maks 50 sider eller 10 MB" in body
    assert "Kortfattet" in body and "Middels" in body and "Detaljert" in body
    assert 'type="radio" name="detail_level" value="medium"' in body
    medium = body.split('value="medium"', 1)[1].split(">", 1)[0]
    assert "checked" in medium
    assert "Gjelder sammendraget. Du kan bytte detaljnivå senere." in body
    assert "Last opp" in body
    assert "Velg en annen fil" not in body


# ---- Valid uploads land on P05 ----------------------------------------------------------


def test_fr3_pdf_upload_without_htmx_lands_on_p05_with_the_source_pending(client_ida, normalisering):
    response = client_ida.post(
        add_url(normalisering), {"file": pdf_file(), "text": "", "detail_level": "detailed"}, follow=True
    )
    assert response.redirect_chain == [(sources_tab_url(normalisering), 302)]
    source = Source.objects.get()
    assert (source.kind, source.status, source.detail_level, source.topic) == (
        SourceKind.PDF, Status.PENDING, "detailed", normalisering,
    )  # fmt: skip
    assert source.texts.count() == 3
    main = main_of(response.content.decode())
    assert "forelesning-3.pdf" in main
    assert "Detaljnivå: detaljert" in main


def test_fr3_pasted_text_without_htmx_lands_on_p05(client_ida, normalisering):
    response = client_ida.post(
        add_url(normalisering), {"text": "Første.\r\n\r\nAndre.", "name": "", "detail_level": "medium"}, follow=True
    )
    assert response.redirect_chain[-1][0] == sources_tab_url(normalisering)
    source = Source.objects.get()
    assert (source.name, source.kind) == ("Innlimt tekst", SourceKind.PASTED)
    assert "Innlimt tekst" in main_of(response.content.decode())


def test_fr3_valid_upload_under_htmx_answers_with_hx_location_to_p05(client_ida, normalisering):
    response = client_ida.post(
        add_url(normalisering), {"text": "Noe tekst.", "name": "Mine notater", "detail_level": "short"}, **HTMX_DIALOG
    )
    assert response.status_code == 200
    assert json.loads(response["HX-Location"])["path"] == sources_tab_url(normalisering)
    assert Source.objects.get().name == "Mine notater"


def test_fr3_p05_with_sources_offers_legg_til_kilde_above_the_list(client_ida, normalisering):
    client_ida.post(add_url(normalisering), {"text": "Noe tekst.", "detail_level": "medium"})
    main = main_of(client_ida.get(sources_tab_url(normalisering)).content.decode())
    head = main.split('class="section-head"', 1)[1].split("</div>", 1)[0]
    assert f'class="button-secondary" href="{add_url(normalisering)}" hx-get="{add_url(normalisering)}"' in head
    assert "Legg til kilde" in head
    assert "empty-state" not in main


# ---- Rejections: 200, the reason in the upload-panel, nothing saved --------------------


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (
            {"file": lambda: pdf_file("kompendium.pdf", [LECTURE_TEXT] * 51)},
            "Filen har 51 sider. Grensen er 50 sider, så last opp ett kapittel om gangen.",
        ),
        (
            {"file": lambda: SimpleUploadedFile("stor.pdf", b"%PDF-" + b"0" * (10 * MEGABYTE - 4))},
            "Filen er 10,1 MB. Grensen er 10 MB.",
        ),
        ({"text": lambda: "a" * 150_001}, "Teksten har 150 001 tegn. Grensen er 150 000 tegn."),
        (
            {"file": lambda: pdf_file("skannet.pdf", [IMAGE_ONLY, IMAGE_ONLY])},
            "Fant ingen tekst i PDF-en. Skannede dokumenter støttes ikke.",
        ),
        ({"file": lambda: SimpleUploadedFile("oppgave.docx", b"PK\x03\x04")}, "Bare PDF og tekstfiler (.txt) støttes."),
        ({"file": lambda: SimpleUploadedFile("falsk.pdf", b"not a pdf")}, "Bare PDF og tekstfiler (.txt) støttes."),
        (
            {"file": lambda: SimpleUploadedFile("ødelagt.pdf", make_pdf([LECTURE_TEXT] * 2)[:300])},
            "Kunne ikke lese PDF-en. Den kan være skadet eller passordbeskyttet.",
        ),
        (
            {"file": lambda: SimpleUploadedFile("låst.pdf", make_pdf([LECTURE_TEXT] * 2, password="x"))},
            "Kunne ikke lese PDF-en. Den kan være skadet eller passordbeskyttet.",
        ),
    ],
    ids=["pages", "size", "chars", "scanned", "docx", "fake-pdf", "truncated", "encrypted"],
)
@pytest.mark.parametrize("headers", [{}, HTMX_DIALOG], ids=["page", "htmx"])
def test_fr3_rejection_shows_reason_with_velg_en_annen_fil_and_saves_nothing(
    client_ida, normalisering, data, message, headers
):
    payload = {key: make() for key, make in data.items()}
    response = client_ida.post(add_url(normalisering), {**payload, "detail_level": "medium"}, **headers)
    assert response.status_code == 200
    assert "HX-Location" not in response
    body = response.content.decode()
    panel = body.split('class="upload-panel"', 1)[1]
    assert message in panel
    assert 'id="upload-error"' in panel
    about_file = "file" in data
    assert ('>Velg en annen fil</label>' in panel) is about_file
    file_input = tag_of(body, '<input type="file"')
    textarea = tag_of(body, "<textarea")
    marked, unmarked = (file_input, textarea) if about_file else (textarea, file_input)
    for attr in ('aria-invalid="true"', 'aria-describedby="upload-error"', "autofocus"):
        assert attr in marked
        assert attr not in unmarked
    assert counts() == (0, 0)
    if headers:
        assert body.lstrip().startswith("<dialog")
        assert 'class="dialog-title" id="dialog-title" tabindex="-1" autofocus' not in body


def test_fr3_neither_file_nor_text_gives_a_field_error(client_ida, normalisering):
    response = client_ida.post(add_url(normalisering), {"text": "   ", "detail_level": "medium"})
    assert response.status_code == 200
    body = response.content.decode()
    assert "Lim inn tekst først." in body
    assert 'id="id_text-error"' in body
    assert counts() == (0, 0)


def test_fr3_file_and_text_together_give_a_field_error(client_ida, normalisering):
    response = client_ida.post(
        add_url(normalisering), {"file": pdf_file(), "text": "Og tekst.", "detail_level": "medium"}
    )
    assert response.status_code == 200
    body = response.content.decode()
    assert "Velg enten en fil eller tekst." in body
    assert 'id="id_file-error"' in body
    assert counts() == (0, 0)


def test_fr3_rejected_paste_keeps_the_text_in_the_form(client_ida, normalisering):
    body = client_ida.post(add_url(normalisering), {"text": "b" * 150_001, "detail_level": "detailed"}).content.decode()
    assert "b" * 1000 in body
    detailed = body.split('value="detailed"', 1)[1].split(">", 1)[0]
    assert "checked" in detailed


def test_fr3_81_char_name_for_pasted_text_is_refused(client_ida, normalisering):
    response = client_ida.post(add_url(normalisering), {"text": "Tekst.", "name": "n" * 81, "detail_level": "medium"})
    assert response.status_code == 200
    body = response.content.decode()
    error = body.split('id="id_name-error"', 1)[1].split("</div>", 1)[0]
    assert "Navnet kan ha høyst 80 tegn." in error
    assert counts() == (0, 0)


def test_fr3_empty_file_says_no_text_under_the_file_field(client_ida, normalisering):
    response = client_ida.post(
        add_url(normalisering), {"file": SimpleUploadedFile("tom.pdf", b""), "detail_level": "medium"}
    )
    assert response.status_code == 200
    body = response.content.decode()
    error = body.split('id="id_file-error"', 1)[1].split("</div>", 1)[0]
    assert "Fant ingen tekst i filen." in error
    assert "Lim inn tekst først." not in body
    assert counts() == (0, 0)


@pytest.mark.parametrize("field", ["text", "name"])
def test_fr3_null_character_gives_a_norwegian_field_error(client_ida, normalisering, field):
    data = {"text": "Tekst.", "detail_level": "medium", field: "før\x00etter"}
    body = client_ida.post(add_url(normalisering), data).content.decode()
    error = body.split(f'id="id_{field}-error"', 1)[1].split("</div>", 1)[0]
    assert "Teksten inneholder et tegn som ikke støttes (nulltegn)." in error
    assert "Null characters" not in body
    assert counts() == (0, 0)


def test_fr3_detail_level_help_and_error_are_linked_and_only_one_radio_takes_focus(client_ida, normalisering):
    body = client_ida.get(add_url(normalisering)).content.decode()
    assert 'class="field segmented-field" aria-describedby="id_detail_level-help"' in body
    body = client_ida.post(add_url(normalisering), {"text": "Tekst.", "detail_level": "huge"}).content.decode()
    assert 'aria-describedby="id_detail_level-help id_detail_level-error"' in body
    radios = [part.split(">", 1)[0] for part in body.split('<input type="radio"')[1:]]
    assert len(radios) == 3
    assert ["autofocus" in r for r in radios] == [True, False, False]
    assert not any("aria-describedby" in r for r in radios)


def test_fr3_unknown_detail_level_is_refused(client_ida, normalisering):
    response = client_ida.post(add_url(normalisering), {"text": "Tekst.", "detail_level": "huge"})
    assert "Velg et detaljnivå." in response.content.decode()
    assert counts() == (0, 0)


def test_fr3_long_file_name_is_shortened(client_ida, normalisering):
    name = "k" * 116 + ".pdf"
    client_ida.post(add_url(normalisering), {"file": pdf_file(name), "detail_level": "medium"})
    source = Source.objects.get()
    assert len(source.name) <= 80 and source.name.endswith(".pdf")


# ---- Ownership, CSRF, sign-in (AD-7, AD-13, FR-1) ---------------------------------------


@pytest.mark.parametrize("method", ["get", "post"])
def test_fr3_another_students_tema_gives_p12_and_saves_nothing(client_ida, jonas_topic, method):
    data = {"text": "Kapret.", "detail_level": "medium"} if method == "post" else {}
    response = getattr(client_ida, method)(add_url(jonas_topic), data)
    assert response.status_code == 404
    content = response.content.decode()
    assert NOT_FOUND in content
    assert "Jonas sitt" not in content
    assert counts() == (0, 0)


def test_fr3_unknown_tema_gives_p12(client_ida):
    assert client_ida.get(reverse("studymat:add_source", args=[999])).status_code == 404


def test_ad18_d05_post_requires_csrf(ida, normalisering):
    client = Client(enforce_csrf_checks=True)
    client.force_login(ida)
    response = client.post(add_url(normalisering), {"text": "Tekst.", "detail_level": "medium"})
    assert response.status_code == 403
    assert counts() == (0, 0)


@pytest.mark.parametrize("method", ["get", "post"])
def test_fr1_signed_out_d05_redirects_to_sign_in(client, normalisering, method):
    data = {"text": "Tekst.", "detail_level": "medium"} if method == "post" else {}
    response = getattr(client, method)(add_url(normalisering), data)
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:sign_in"))
    assert counts() == (0, 0)


def test_fr1_signed_out_htmx_d05_gets_hx_redirect(client, normalisering):
    response = client.get(add_url(normalisering), **HTMX_DIALOG)
    assert reverse("accounts:sign_in") in response["HX-Redirect"]


def test_d05_other_methods_answer_405(client_ida, normalisering):
    assert client_ida.put(add_url(normalisering)).status_code == 405


# ---- Story 5: «Bruk eksempeldokumentet» in Mock mode (FR-20) and the daily limit (NFR-7) ----

SAMPLE_BUTTON = "Bruk eksempeldokumentet"


def use_up_today(student):
    from ai.gateway import DAILY_LIMIT
    from ai.models import GenerationCallCount
    from core import time

    GenerationCallCount.objects.create(student=student, day=time.today(), count=DAILY_LIMIT)


def test_fr20_d05_in_mock_mode_offers_the_sample_as_a_secondary_submit(client_ida, normalisering):
    body = client_ida.get(add_url(normalisering), **HTMX_DIALOG).content.decode()
    button = tag_of(body, '<button class="button-secondary" type="submit" name="use_sample"')
    assert "disabled" not in button
    assert SAMPLE_BUTTON in body
    # Enter in a field submits «Last opp», not the Sample: a hidden copy of it comes first.
    first_submit = tag_of(body, '<button class="visually-hidden" type="submit"')
    assert 'name="use_sample"' not in first_submit
    assert body.index(first_submit) < body.index(button)


def test_fr20_d05_sample_ingests_the_sample_document_and_lands_on_p05(client_ida, normalisering):
    from ai import mock

    response = client_ida.post(
        add_url(normalisering), {"use_sample": "1", "detail_level": "detailed", "text": ""}, **HTMX_DIALOG
    )
    assert response.status_code == 200
    assert json.loads(response["HX-Location"])["path"] == sources_tab_url(normalisering)
    source = Source.objects.get()
    assert (source.kind, source.status, source.detail_level, source.topic) == (
        SourceKind.PDF, Status.PENDING, "detailed", normalisering,
    )  # fmt: skip
    assert source.content_sha256 == mock.SAMPLE_SHA256
    assert source.name == "normalisering.pdf"
    assert source.texts.count() == mock.SAMPLE_PAGES


def test_fr20_d05_sample_without_htmx_redirects_and_ignores_a_sent_file(client_ida, normalisering):
    from ai import mock

    response = client_ida.post(
        add_url(normalisering), {"use_sample": "1", "detail_level": "short", "file": pdf_file()}
    )
    assert response.status_code == 302 and response["Location"] == sources_tab_url(normalisering)
    source = Source.objects.get()
    assert (source.content_sha256, source.detail_level) == (mock.SAMPLE_SHA256, "short")


def test_fr20_d05_sample_still_needs_a_detail_level(client_ida, normalisering):
    response = client_ida.post(add_url(normalisering), {"use_sample": "1"}, **HTMX_DIALOG)
    assert "HX-Location" not in response
    assert "Velg et detaljnivå." in response.content.decode()
    assert counts() == (0, 0)


def test_fr21_d05_in_real_mode_has_no_sample_and_ignores_use_sample(settings, client_ida, ida, normalisering):
    settings.AI_PROVIDER = "anthropic"
    accept_privacy(ida)
    body = client_ida.get(add_url(normalisering), **HTMX_DIALOG).content.decode()
    assert SAMPLE_BUTTON not in body
    assert 'name="use_sample"' not in body
    response = client_ida.post(add_url(normalisering), {"use_sample": "1", "detail_level": "medium"}, **HTMX_DIALOG)
    assert "HX-Location" not in response
    assert counts() == (0, 0)


def test_nfr7_d05_at_the_daily_limit_shows_the_message_and_disables_both_submits(client_ida, ida, normalisering):
    use_up_today(ida)
    for response in (client_ida.get(add_url(normalisering)), client_ida.get(add_url(normalisering), **HTMX_DIALOG)):
        assert response.status_code == 200
        body = response.content.decode()
        assert "Du har brukt alle 20 genereringene for i dag. Grensen nullstilles ved midnatt." in body
        assert 'id="daily-limit"' in body
        upload = tag_of(body, '<button class="button-primary" type="submit"')
        sample = tag_of(body, '<button class="button-secondary" type="submit" name="use_sample"')
        for button in (upload, sample):
            assert "disabled" in button
            assert 'aria-describedby="daily-limit"' in button


@pytest.mark.parametrize(
    "data",
    [
        {"use_sample": "1", "detail_level": "medium"},
        {"text": "Noe tekst.", "detail_level": "medium"},
        {"file": "pdf", "detail_level": "medium"},
    ],
)
def test_nfr7_d05_post_at_the_daily_limit_saves_nothing_and_rerenders(client_ida, ida, normalisering, data):
    use_up_today(ida)
    if data.get("file") == "pdf":
        data = {**data, "file": pdf_file()}
    response = client_ida.post(add_url(normalisering), data, **HTMX_DIALOG)
    assert response.status_code == 200
    assert "HX-Location" not in response
    assert "Du har brukt alle 20 genereringene for i dag." in response.content.decode()
    assert counts() == (0, 0)


def test_nfr7_d05_below_the_limit_has_no_limit_message(client_ida, ida, normalisering):
    from ai.gateway import DAILY_LIMIT
    from ai.models import GenerationCallCount
    from core import time

    GenerationCallCount.objects.create(student=ida, day=time.today(), count=DAILY_LIMIT - 1)
    body = client_ida.get(add_url(normalisering), **HTMX_DIALOG).content.decode()
    assert 'id="daily-limit"' not in body
    assert "disabled" not in tag_of(body, '<button class="button-primary" type="submit"')
