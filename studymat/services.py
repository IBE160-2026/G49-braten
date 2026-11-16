"""Writes to Study material, and the generation orchestrator (AD-5 step 2, AD-19).

`generate()`: claim (committed on its own) -> build the request from non-empty SourceText rows ->
gateway (outside any transaction) -> FR-7 checks -> Reference check -> one atomic, token-guarded
save. Any AIError marks the Source failed with its code; nothing from a failed attempt is saved.
"""

import logging

from django.db import transaction

from ai import gateway
from ai.errors import AIError, InvalidFormat
from ai.schemas import GenerateRequest, Location
from courses import services as courses_services
from courses.models import Source, SourceKind
from ingestion.models import SourceText
from studymat import checks
from studymat.models import Flashcard, KeyConcept, Question, Summary

logger = logging.getLogger(__name__)


def locations(source: Source) -> list[Location]:
    """The Source's non-empty Locations, in order (AD-6: only these get a marker)."""
    rows = SourceText.objects.filter(source=source).order_by("index", "kind").values_list("index", "text")
    return [Location(index=index, text=text) for index, text in rows if text.strip()]


def location_label(source: Source, location_index: int) -> str:
    """A Reference's label (EXPERIENCE.md, Voice and Tone): «Side 14 · {kilde}» for a PDF and
    «Avsnitt 3 · {kilde}» for plain or pasted text."""
    unit = "Side" if source.kind == SourceKind.PDF else "Avsnitt"
    return f"{unit} {location_index} · {source.name}"


def delete_item(student, item) -> None:
    """FR-24, AD-8: a hard delete of one owned Key concept, Flashcard or Question.

    The row is gone, so everything built on it later (Quizzes, Retry rounds, Due today) drops it by
    FK cascade. The caller has already checked ownership (404); this refuses anything else anyway.
    """
    assert item.student_id == student.pk, "delete_item: not the Student's item"
    item.delete()


def generate(student, source: Source) -> bool:
    """Run one generation for `source`. False when it could not be claimed (nothing sent)."""
    token = courses_services.claim(source)
    if token is None:
        return False
    locs = locations(source)
    request = GenerateRequest(
        source_id=source.pk,
        content_sha256=source.content_sha256,
        language=source.language,
        detail_level=source.detail_level,
        locations=locs,
    )
    try:
        material = gateway.generate_study_material(student, request)
        if not material.summary.strip():
            raise InvalidFormat("empty summary")
    except AIError as error:
        courses_services.mark_failed(source, token, error.code)
        return True

    checked = checks.check(material, {loc.index: loc.text for loc in locs})
    _save(source, token, material, checked)
    return True


def _save(source: Source, token, material, checked: checks.Checked) -> bool:
    """All or nothing (AD-5): `ready` first, then the items, only if this run still owns the Source."""
    owner = source.student_id
    with transaction.atomic():
        if not courses_services.mark_ready(source, token, material.language, checked.removed, checked.dropped):
            logger.info("studymat generate source=%s outcome=superseded", source.pk)
            return False
        Summary.objects.update_or_create(
            source=source,
            defaults={"student_id": owner, "text": material.summary, "detail_level": source.detail_level},
        )
        KeyConcept.objects.bulk_create(
            KeyConcept(student_id=owner, source=source, term=k.term, definition=k.definition, **_ref(k))
            for k in checked.key_concepts
        )
        Flashcard.objects.bulk_create(
            Flashcard(student_id=owner, source=source, front=f.front, back=f.back, **_ref(f))
            for f in checked.flashcards
        )
        Question.objects.bulk_create(
            Question(
                student_id=owner,
                source=source,
                kind=q.kind,
                prompt=q.prompt,
                hint=q.hint,
                options=[option.model_dump() for option in q.options],
                correct_index=q.correct_index,
                model_answer=q.model_answer,
                **_ref(q),
            )
            for q in checked.questions
        )
    return True


def _ref(item) -> dict:
    return {"location_index": item.reference.location_index, "quote": item.reference.quote}
