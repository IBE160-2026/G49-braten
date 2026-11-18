"""The single port to any language model (AD-2).

Operations take `student` plus one request object from `ai.schemas`. Every counted operation runs,
in order (AD-3): the mode check (Mock mode answers only for the Sample document, otherwise
`NeedsKey`, counting nothing), the daily counter (one committed conditional UPDATE, AD-19), then the
send. A send that fails still counts; Mock mode counts too (NFR-7).

No gateway call runs inside a transaction (AD-19). Calls are logged with the Student id, the
operation and the outcome, never with Source text or the Key.
"""

import logging

from django.conf import settings
from django.db import connection
from django.db.models import F

from ai import mock
from ai.errors import AIError, DailyLimitReached, NeedsKey, ProviderUnavailable
from ai.models import GenerationCallCount
from ai.schemas import (
    GenerateRequest,
    GradeRequest,
    GradeResponse,
    StudyMaterial,
    SummaryRequest,
    SummaryResponse,
)
from core import time

logger = logging.getLogger(__name__)

# NFR-7 (PRD §10): Generation calls per Student per Oslo day.
DAILY_LIMIT = 20

MOCK = "mock"
REAL = "real"


def mode() -> str:
    """`mock` or `real`, from settings.AI_PROVIDER (FR-20, FR-21)."""
    return MOCK if settings.AI_PROVIDER == "mock" else REAL


def remaining_today(student) -> int:
    """Generation calls the Student has left today (NFR-7)."""
    row = GenerationCallCount.objects.filter(student=student, day=time.today()).only("count").first()
    used = row.count if row else 0
    return max(DAILY_LIMIT - used, 0)


def generate_study_material(student, request: GenerateRequest) -> StudyMaterial:
    """Study material for one Source (FR-7). Counts one Generation call."""
    return _counted(student, "generate_study_material", request.content_sha256, _send_generate, request)


def regenerate_summary(student, request: SummaryRequest) -> SummaryResponse:
    """A new Summary at another Detail level (FR-7). Counts one Generation call."""
    return _counted(student, "regenerate_summary", request.content_sha256, _send_summary, request)


def grade_free_text(student, request: GradeRequest) -> GradeResponse:
    """Grade a Free-text Answer (FR-12). Never counted against the daily limit (AD-3).

    Mock mode grades every Source with the word-overlap rule (no `NeedsKey`, so Questions made in
    Real mode can still be practised); Real mode raises `ProviderUnavailable` until story 10.
    """
    return _uncounted(student, "grade_free_text", _send_grade, request)


def simpler_explanation(student, request):
    """A Simpler explanation of a Key concept or Flashcard (FR-19). Counted. Story 16."""
    raise NotImplementedError("simpler_explanation arrives in story 16.")


# ---- Internals ---------------------------------------------------------------------------


def _counted(student, operation: str, content_sha256: str, send, request):
    assert not connection.in_atomic_block, "No gateway call runs inside a transaction (AD-19)."
    try:
        if mode() == MOCK and not mock.is_sample(content_sha256):
            raise NeedsKey()
        _count_call(student)
        result = send(request)
    except AIError as error:
        logger.info("ai %s student=%s outcome=%s", operation, student.pk, error.code)
        raise
    except Exception:
        logger.exception("ai %s student=%s outcome=error", operation, student.pk)
        raise
    logger.info("ai %s student=%s outcome=ok mode=%s", operation, student.pk, mode())
    return result


def _uncounted(student, operation: str, send, request):
    """Like `_counted`, without the mode gate and the daily counter."""
    assert not connection.in_atomic_block, "No gateway call runs inside a transaction (AD-19)."
    try:
        result = send(request)
    except AIError as error:
        logger.info("ai %s student=%s outcome=%s", operation, student.pk, error.code)
        raise
    except Exception:
        logger.exception("ai %s student=%s outcome=error", operation, student.pk)
        raise
    logger.info("ai %s student=%s outcome=ok mode=%s", operation, student.pk, mode())
    return result


def _count_call(student) -> None:
    """One conditional UPDATE below the limit, committed on its own (AD-3, AD-19)."""
    row, _ = GenerationCallCount.objects.get_or_create(student=student, day=time.today())
    if not GenerationCallCount.objects.filter(pk=row.pk, count__lt=DAILY_LIMIT).update(count=F("count") + 1):
        raise DailyLimitReached()


def _send_generate(request: GenerateRequest) -> StudyMaterial:
    if mode() == MOCK:
        return mock.study_material(request.detail_level)
    # The Anthropic adapter arrives in story 10.
    raise ProviderUnavailable()


def _send_summary(request: SummaryRequest) -> SummaryResponse:
    if mode() == MOCK:
        return mock.summary(request.detail_level)
    raise ProviderUnavailable()


def _send_grade(request: GradeRequest) -> GradeResponse:
    if mode() == MOCK:
        return mock.grade(request)
    raise ProviderUnavailable()
