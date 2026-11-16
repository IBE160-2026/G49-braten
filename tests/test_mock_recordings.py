"""FR-20, CAP-12 (story 5): the Sample document and the Mock recordings (AD-4).

The quotes are checked against pypdf's extracted page text with the same kind of normalisation
the Reference check (AD-6, story 6) uses: NFKC, quotes and dashes folded, hyphenation and
whitespace collapsed, case-insensitive.
"""

import json
import re
import unicodedata

import pytest
from django.core.files import File

from ai import mock
from ai.schemas import StudyMaterial, SummaryResponse
from courses import services
from courses.models import DetailLevel
from ingestion import extract
from ingestion.models import SourceText
from ingestion.services import ingest

MIN_QUOTE_WORDS = 5

_FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "«": '"', "»": '"',
                       "–": "-", "—": "-", "−": "-"})  # fmt: skip


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_FOLD)
    text = re.sub(r"-\s*\n\s*", "", text)  # hyphenation across a line break
    return re.sub(r"\s+", " ", text).strip().casefold()


@pytest.fixture(scope="module")
def pages() -> list[str]:
    return extract.pdf_pages(mock.SAMPLE_PATH.read_bytes())


@pytest.fixture(scope="module")
def material() -> StudyMaterial:
    return mock.study_material(DetailLevel.MEDIUM)


def items(material: StudyMaterial):
    return [*material.key_concepts, *material.flashcards, *material.questions]


# ---- The Sample document ---------------------------------------------------------------


def test_fr20_sample_pdf_has_one_page_per_slide_and_norwegian_letters(pages):
    assert len(pages) == mock.SAMPLE_PAGES
    assert all(page.strip() for page in pages)
    text = "\n".join(pages)
    assert {"æ", "ø", "å"} <= set(text)
    assert pages[0].startswith("Databaser: normalisering")


def test_fr20_sample_licence_is_cc0():
    readme = (mock.SAMPLE_PATH.parent / "README.md").read_text(encoding="utf-8")
    assert "CC0" in readme


@pytest.mark.django_db
def test_fr20_ingested_sample_has_the_sample_sha_and_the_recordings_page_range(student, material):
    ida = student("ida@example.no")
    topic = services.create_topic(services.create_course(ida, "Databaser"), "Normalisering")
    with open(mock.SAMPLE_PATH, "rb") as handle:
        source = ingest(topic, upload=File(handle, name=mock.SAMPLE_NAME), detail_level="medium")
    assert source.content_sha256 == mock.SAMPLE_SHA256
    assert mock.is_sample(source.content_sha256)
    page_count = SourceText.objects.filter(source=source).count()
    assert page_count == mock.SAMPLE_PAGES
    indexes = {item.reference.location_index for item in items(material)}
    assert indexes == set(range(1, page_count + 1))


# ---- The recordings --------------------------------------------------------------------


def test_fr20_recordings_validate_against_the_schemas():
    StudyMaterial.model_validate_json(mock.STUDY_MATERIAL_FILE.read_bytes())
    summaries = json.loads(mock.SUMMARIES_FILE.read_text(encoding="utf-8"))
    assert set(summaries) == set(DetailLevel.values)
    for body in summaries.values():
        SummaryResponse.model_validate(body)


def test_fr20_summaries_differ_by_detail_level():
    short, medium, detailed = (mock.summary(level).summary for level in ("short", "medium", "detailed"))
    assert len(short) < len(medium) < len(detailed)


def test_fr20_recordings_have_enough_items_of_each_kind(material):
    assert material.language == "nb"
    assert len(material.key_concepts) >= 5
    assert len(material.flashcards) >= 10
    assert len(material.questions) >= 10
    assert {q.kind for q in material.questions} == {"multiple_choice", "free_text"}


def test_fr20_questions_have_the_ad9_shape(material):
    for question in material.questions:
        assert question.prompt and question.hint
        if question.kind == "multiple_choice":
            assert len(question.options) == 4
            assert question.correct_index in range(4)
            assert all(option.text and option.explanation for option in question.options)
        else:
            assert question.options == []
            assert question.correct_index is None
            assert question.model_answer


def test_fr20_exactly_one_item_points_to_the_wrong_page_and_every_other_quote_is_on_its_page(pages, material):
    normalised = [normalise(page) for page in pages]
    wrong = []
    for item in items(material):
        ref = item.reference
        quote = normalise(ref.quote)
        assert len(quote.split()) >= MIN_QUOTE_WORDS, ref.quote
        on_own_page = 1 <= ref.location_index <= len(pages) and quote in normalised[ref.location_index - 1]
        if not on_own_page:
            elsewhere = [i for i, page in enumerate(normalised, start=1) if quote in page]
            assert elsewhere, f"quote is on no page: {ref.quote!r}"
            wrong.append((ref.location_index, elsewhere))
    assert len(wrong) == 1, wrong


def test_fr20_no_quote_repeats_on_most_pages(pages, material):
    normalised = [normalise(page) for page in pages]
    for item in items(material):
        quote = normalise(item.reference.quote)
        assert sum(quote in page for page in normalised) <= len(pages) // 2
