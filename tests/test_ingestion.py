"""FR-3 / FR-4 (story 4): ingestion.services.ingest() and the pure extraction functions.

PDFs are built in the test (tests/pdfs.py); nothing binary lives in git.
"""

import codecs
import hashlib
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfReader

from courses import services as course_services
from courses.models import Source, SourceKind, Status
from ingestion import extract
from ingestion.errors import MEGABYTE, IngestError, megabytes, thousands
from ingestion.models import LocationKind, SourceText
from ingestion.services import ingest
from tests.pdfs import IMAGE_ONLY, LECTURE_TEXT, make_pdf

pytestmark = pytest.mark.django_db


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def topic(ida):
    course = course_services.create_course(ida, "Databaser", "DAT102")
    return course_services.create_topic(course, "Normalisering")


def upload(name, data, content_type="application/octet-stream"):
    return SimpleUploadedFile(name, data, content_type=content_type)


def rejected(topic, **kwargs) -> IngestError:
    """Runs ingest, expecting a rejection, and checks that nothing was kept."""
    with pytest.raises(IngestError) as caught:
        ingest(topic, detail_level=kwargs.pop("detail_level", "medium"), **kwargs)
    assert Source.objects.count() == 0
    assert SourceText.objects.count() == 0
    return caught.value


# ---- The matrix: what is stored ---------------------------------------------------------


def test_fr3_pdf_gets_one_page_row_per_page_with_empty_image_page_kept(topic, ida):
    data = make_pdf([LECTURE_TEXT, IMAGE_ONLY, LECTURE_TEXT + "\nSide tre."])
    source = ingest(topic, upload=upload("forelesning-3.pdf", data), detail_level="detailed")
    assert (source.kind, source.status, source.detail_level) == (SourceKind.PDF, Status.PENDING, "detailed")
    assert source.name == "forelesning-3.pdf"
    assert source.size_bytes == len(data)
    assert source.content_sha256 == hashlib.sha256(data).hexdigest()
    assert source.started_at is not None
    rows = list(SourceText.objects.filter(source=source).order_by("index"))
    assert [(r.kind, r.index, r.label) for r in rows] == [("page", 1, "1"), ("page", 2, "2"), ("page", 3, "3")]
    assert rows[0].text.startswith("Normalisering fjerner redundans")
    assert "primærnøkkelen" in rows[0].text
    assert rows[1].text == ""
    assert rows[2].text.endswith("Side tre.")


def test_fr4_text_file_gets_one_paragraph_row_per_block(topic):
    data = "Første avsnitt.\nFortsatt første.\r\n\r\nAndre avsnitt.\n   \n\n\nTredje avsnitt.\n".encode()
    source = ingest(topic, upload=upload("notater.txt", data, "text/plain"), detail_level="medium")
    assert source.kind == SourceKind.TEXT
    assert source.size_bytes == len(data)
    assert source.content_sha256 == hashlib.sha256(data).hexdigest()
    rows = list(SourceText.objects.filter(source=source).order_by("index"))
    assert [(r.kind, r.index) for r in rows] == [("paragraph", 1), ("paragraph", 2), ("paragraph", 3)]
    assert [r.text for r in rows] == ["Første avsnitt.\nFortsatt første.", "Andre avsnitt.", "Tredje avsnitt."]


def test_fr3_pasted_text_without_name_is_named_innlimt_tekst(topic):
    text = "Et avsnitt.\r\n\r\nEt til."
    source = ingest(topic, text=text, detail_level="short")
    assert (source.name, source.kind, source.detail_level, source.size_bytes) == (
        "Innlimt tekst", SourceKind.PASTED, "short", 0,
    )  # fmt: skip
    assert source.content_sha256 == hashlib.sha256(b"Et avsnitt.\n\nEt til.").hexdigest()
    assert list(source.texts.order_by("index").values_list("text", flat=True)) == ["Et avsnitt.", "Et til."]


def test_fr3_pasted_text_keeps_a_given_name(topic):
    assert ingest(topic, text="Tekst", name="  Mine notater  ", detail_level="medium").name == "Mine notater"


def test_fr4_cp1252_text_file_is_decoded(topic):
    source = ingest(topic, upload=upload("gammel.txt", "Æøå er norske bokstaver.".encode("cp1252")), detail_level="medium")
    assert source.texts.get().text == "Æøå er norske bokstaver."


def test_fr4_utf8_bom_is_stripped(topic):
    source = ingest(topic, upload=upload("bom.txt", "﻿Æøå".encode("utf-8")), detail_level="medium")
    assert source.texts.get().text == "Æøå"


def test_fr3_long_file_name_is_shortened_keeping_the_extension(topic):
    name = "a" * 60 + "b" * 56 + ".pdf"
    assert len(name) == 120
    source = ingest(topic, upload=upload(name, make_pdf([LECTURE_TEXT, LECTURE_TEXT])), detail_level="medium")
    assert len(source.name) <= 80
    assert source.name.endswith(".pdf")
    assert "…" in source.name
    assert source.name.startswith("aaaa") and source.name.endswith("bbbb.pdf")


# ---- AD-7, AD-8 ---------------------------------------------------------------------------


def test_ad7_sourcetext_student_equals_its_sources(topic, ida):
    source = ingest(topic, text="Ett.\n\nTo.", detail_level="medium")
    assert set(SourceText.objects.values_list("student_id", flat=True)) == {source.student_id} == {ida.id}
    assert SourceText.objects.for_student(ida).count() == 2


def test_ad8_deleting_a_source_deletes_its_texts(topic):
    kept = ingest(topic, text="Beholdes.", detail_level="medium")
    gone = ingest(topic, text="En.\n\nTo.", detail_level="medium")
    course_services.delete_source(gone)
    assert list(SourceText.objects.values_list("source_id", flat=True)) == [kept.id]


def test_ad6_location_is_unique_per_source_kind_and_index(topic):
    from django.db import IntegrityError, transaction

    source = ingest(topic, text="En.", detail_level="medium")
    with pytest.raises(IntegrityError), transaction.atomic():
        SourceText.objects.create(student_id=source.student_id, source=source, kind="paragraph", index=1, text="x")
    with pytest.raises(IntegrityError), transaction.atomic():
        SourceText.objects.create(student_id=source.student_id, source=source, kind="page", index=0, text="x")


def test_ad6_location_kinds_use_the_spines_values():
    assert LocationKind.values == ["page", "paragraph", "heading"]


# ---- The matrix: rejections keep nothing ------------------------------------------------


def test_fr3_51_page_pdf_is_refused_naming_the_limit(topic):
    error = rejected(topic, upload=upload("kompendium.pdf", make_pdf([LECTURE_TEXT] * 51)))
    assert error.code == "too_many_pages"
    assert error.message == "Filen har 51 sider. Grensen er 50 sider, så last opp ett kapittel om gangen."


def test_fr3_50_page_pdf_is_accepted(topic):
    source = ingest(topic, upload=upload("kapittel.pdf", make_pdf([LECTURE_TEXT] * 50)), detail_level="medium")
    assert source.texts.count() == 50


def test_fr3_file_one_byte_over_10_mb_is_refused(topic):
    data = b"%PDF-" + b"0" * (10 * MEGABYTE + 1 - 5)
    error = rejected(topic, upload=upload("stor.pdf", data))
    assert error.code == "file_too_large"
    assert error.message == "Filen er 10,1 MB. Grensen er 10 MB."


def test_fr3_size_message_matches_the_experience_example():
    assert IngestError("file_too_large", size=int(12.4 * MEGABYTE), limit=10 * MEGABYTE).message == (
        "Filen er 12,4 MB. Grensen er 10 MB."
    )


def test_fr3_150001_characters_are_refused(topic):
    error = rejected(topic, text="a" * 150_001)
    assert error.code == "too_many_chars"
    assert error.message == "Teksten har 150 001 tegn. Grensen er 150 000 tegn."
    assert IngestError("too_many_chars", chars=180_000, limit=150_000).message == (
        "Teksten har 180 000 tegn. Grensen er 150 000 tegn."
    )


def test_fr3_150000_characters_are_accepted(topic):
    assert ingest(topic, text="a" * 150_000, detail_level="medium").texts.get().text == "a" * 150_000


def test_fr3_character_limit_applies_to_text_files(topic):
    assert rejected(topic, upload=upload("lang.txt", b"a" * 150_001)).code == "too_many_chars"


def test_fr3_scanned_pdf_is_refused(topic):
    error = rejected(topic, upload=upload("skannet.pdf", make_pdf([IMAGE_ONLY, IMAGE_ONLY])))
    assert error.message == "Fant ingen tekst i PDF-en. Skannede dokumenter støttes ikke."


def chars_page(n: int) -> str:
    """A page with exactly `n` non-whitespace characters, in lines of 50."""
    return "\n".join("x" * len(chunk) for chunk in [range(n)[i : i + 50] for i in range(0, n, 50)])


def test_fr3_min_text_chars_boundary_199_refused_200_accepted(topic):
    assert extract.MIN_TEXT_CHARS == 200
    assert extract.non_whitespace_count(extract.pdf_pages(make_pdf([chars_page(199)]))) == 199
    assert rejected(topic, upload=upload("tynn.pdf", make_pdf([chars_page(199)]))).code == "scanned_pdf"
    source = ingest(topic, upload=upload("akkurat.pdf", make_pdf([chars_page(200)])), detail_level="medium")
    assert source.texts.get().text.replace("\n", "") == "x" * 200


def test_fr3_pdf_within_page_limit_but_over_150000_characters_is_refused(topic):
    page = "\n".join(["y" * 80] * 40)  # 3,239 characters with newlines
    error = rejected(topic, upload=upload("tett.pdf", make_pdf([page] * 50)))
    assert error.code == "too_many_chars"
    assert error.params["chars"] > 150_000


def test_fr3_pdf_with_only_an_owner_password_is_read(topic):
    data = make_pdf([LECTURE_TEXT, LECTURE_TEXT], owner_password="eier")
    assert PdfReader(io.BytesIO(data)).is_encrypted
    source = ingest(topic, upload=upload("forelesning.pdf", data), detail_level="medium")
    assert "Normalisering" in source.texts.order_by("index").first().text


@pytest.mark.parametrize("encoding", ["utf-16-le", "utf-16-be"])
def test_fr4_utf16_text_file_with_bom_is_decoded(topic, encoding):
    bom = codecs.BOM_UTF16_LE if encoding == "utf-16-le" else codecs.BOM_UTF16_BE
    data = bom + "Æøå i Notepad.\r\n\r\nAndre avsnitt.".encode(encoding)
    source = ingest(topic, upload=upload("notepad.txt", data), detail_level="medium")
    assert list(source.texts.order_by("index").values_list("text", flat=True)) == ["Æøå i Notepad.", "Andre avsnitt."]


def test_valid_utf8_replaces_lone_surrogates():
    cleaned = extract.valid_utf8("a\udc80b\ud800")
    cleaned.encode("utf-8")
    assert cleaned.startswith("a") and "b" in cleaned and "\ufffd" in cleaned
    assert extract.valid_utf8("Æøå") == "Æøå"


@pytest.mark.parametrize(
    ("name", "data"),
    [
        ("oppgave.docx", b"PK\x03\x04 word"),
        ("falsk.pdf", b"Hei, jeg er ikke en PDF" * 20),
        ("bilde.txt", b"\x89PNG\r\n\x1a\n\x00\x00binary"),
        ("uten-endelse", b"tekst"),
    ],
)
def test_fr3_wrong_type_is_refused(topic, name, data):
    error = rejected(topic, upload=upload(name, data))
    assert error.code == "unsupported_type"
    assert error.message == "Bare PDF og tekstfiler (.txt) støttes."


@pytest.mark.parametrize(
    "data",
    [
        make_pdf([LECTURE_TEXT, LECTURE_TEXT])[:300],
        make_pdf([LECTURE_TEXT, LECTURE_TEXT])[:-40],
        make_pdf([LECTURE_TEXT, LECTURE_TEXT], password="hemmelig"),
        b"%PDF-1.7\n garbage \x00\xff",
    ],
    ids=["truncated", "truncated-tail", "encrypted", "garbage"],
)
def test_fr3_broken_or_encrypted_pdf_is_refused_without_a_crash(topic, data):
    error = rejected(topic, upload=upload("ødelagt.pdf", data))
    assert error.code == "unreadable_pdf"
    assert error.message == "Kunne ikke lese PDF-en. Den kan være skadet eller passordbeskyttet."


def test_fr3_empty_paste_and_blank_text_file_are_refused(topic):
    assert rejected(topic, text="  \n\n ").message == "Lim inn tekst først."
    assert rejected(topic).code == "paste_empty"
    assert rejected(topic, upload=upload("tom.txt", b"\r\n  \n")).code == "empty_file"


def test_fr3_file_and_text_together_are_refused(topic):
    error = rejected(topic, upload=upload("a.txt", b"tekst"), text="mer tekst")
    assert error.message == "Velg enten en fil eller tekst."


def test_fr3_a_failure_while_saving_texts_keeps_no_source(topic, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(SourceText.objects, "bulk_create", boom)
    with pytest.raises(RuntimeError):
        ingest(topic, text="Ett avsnitt.", detail_level="medium")
    assert Source.objects.count() == 0


# ---- Pure helpers -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected_len"),
    [("kort.pdf", 8), ("x" * 80 + ".txt", 80), ("y" * 76 + ".pdf", 80)],
)
def test_shorten_name_leaves_short_names_and_caps_long_ones(name, expected_len):
    shortened = extract.shorten_name(name)
    assert len(shortened) == expected_len
    assert shortened.endswith(name[-4:])


def test_number_formats_are_norwegian():
    assert thousands(150_000) == "150 000"
    assert megabytes(10 * MEGABYTE) == "10"
    assert megabytes(10 * MEGABYTE + 1) == "10,1"


def test_limits_are_the_prd_numbers():
    assert (extract.MAX_FILE_BYTES, extract.MAX_PAGES, extract.MAX_CHARS) == (10 * MEGABYTE, 50, 150_000)
