"""NFR-7, FR-20, FR-21 (story 5): the AI gateway, Mock mode and the daily limit (AD-2, AD-3, AD-19).

Gateway calls assert they are not inside a transaction, so these tests use `transaction=True`.
"""

import datetime
import logging

import pytest
from django.db import connection, transaction

from accounts.services import accept_privacy
from ai import anthropic_adapter, errors, gateway, mock
from ai.models import GenerationCallCount
from ai.schemas import (
    GenerateRequest,
    GradeRequest,
    GradeResponse,
    Location,
    StudyMaterial,
    SummaryRequest,
    SummaryResponse,
)
from core import time
from core.messages import MESSAGES
from courses.models import DetailLevel, FailureReason

pytestmark = pytest.mark.django_db(transaction=True)

OSLO = time.OSLO
OTHER_SHA = "0" * 64


def generate_request(sha=None, detail_level="medium") -> GenerateRequest:
    return GenerateRequest(
        source_id=1,
        content_sha256=sha or mock.SAMPLE_SHA256,
        language="",
        detail_level=detail_level,
        locations=[Location(index=1, text="Normalisering fjerner redundans.")],
    )


def summary_request(sha=None, detail_level="detailed") -> SummaryRequest:
    return SummaryRequest(
        source_id=1,
        content_sha256=sha or mock.SAMPLE_SHA256,
        language="nb",
        detail_level=detail_level,
        locations=[Location(index=1, text="Normalisering fjerner redundans.")],
    )


def used(student, day=None) -> int:
    row = GenerationCallCount.objects.filter(student=student, day=day or time.today()).first()
    return row.count if row else 0


def use_up(student, n=gateway.DAILY_LIMIT, day=None):
    GenerationCallCount.objects.update_or_create(student=student, day=day or time.today(), defaults={"count": n})


@pytest.fixture
def ida(student):
    return student("ida@example.no")


# ---- Mode (FR-20, FR-21) -----------------------------------------------------------------


def test_fr20_mode_is_mock_under_test_settings():
    assert gateway.mode() == "mock"


def test_fr21_mode_is_real_when_the_provider_is_anthropic(settings):
    settings.AI_PROVIDER = "anthropic"
    assert gateway.mode() == "real"


# ---- Matrix: Sample, Mock ----------------------------------------------------------------


def test_fr20_sample_in_mock_mode_returns_validated_study_material_and_counts_one(ida):
    material = gateway.generate_study_material(ida, generate_request())
    assert isinstance(material, StudyMaterial)
    assert material.key_concepts and material.flashcards and material.questions
    assert used(ida) == 1
    assert gateway.remaining_today(ida) == gateway.DAILY_LIMIT - 1


@pytest.mark.parametrize("level", DetailLevel.values)
def test_fr20_generated_summary_follows_the_detail_level(ida, level):
    material = gateway.generate_study_material(ida, generate_request(detail_level=level))
    assert material.summary == mock.summary(level).summary


def test_fr20_summary_in_mock_mode_returns_the_detailed_recording_and_counts_one(ida):
    response = gateway.regenerate_summary(ida, summary_request(detail_level="detailed"))
    assert isinstance(response, SummaryResponse)
    assert response.summary == mock.summary("detailed").summary
    assert response.summary != mock.summary("short").summary
    assert used(ida) == 1


def test_fr20_detail_level_is_lower_cased_before_validation(ida):
    request = summary_request(detail_level="DETAILED")
    assert request.detail_level == "detailed"


# ---- Matrix: Other file, Mock ------------------------------------------------------------


def test_fr20_other_file_in_mock_mode_raises_needs_key_and_counts_nothing(ida):
    with pytest.raises(errors.NeedsKey) as caught:
        gateway.generate_study_material(ida, generate_request(sha=OTHER_SHA))
    assert caught.value.code == "needs_key"
    assert caught.value.message == MESSAGES["needs_key"]
    with pytest.raises(errors.NeedsKey):
        gateway.regenerate_summary(ida, summary_request(sha=OTHER_SHA))
    assert used(ida) == 0
    assert gateway.remaining_today(ida) == gateway.DAILY_LIMIT


def test_fr20_needs_key_is_checked_before_the_limit(ida):
    use_up(ida)
    with pytest.raises(errors.NeedsKey):
        gateway.generate_study_material(ida, generate_request(sha=OTHER_SHA))
    assert used(ida) == gateway.DAILY_LIMIT


# ---- Matrix: 21st call, new Oslo day, two Students ---------------------------------------


def test_nfr7_twenty_calls_succeed_and_the_21st_raises_daily_limit(ida, monkeypatch):
    for _ in range(gateway.DAILY_LIMIT):
        gateway.generate_study_material(ida, generate_request())
    assert used(ida) == 20
    assert gateway.remaining_today(ida) == 0

    sent = []
    monkeypatch.setattr(gateway, "_send_generate", lambda request: sent.append(request))
    with pytest.raises(errors.DailyLimitReached) as caught:
        gateway.generate_study_material(ida, generate_request())
    assert caught.value.code == "daily_limit"
    assert caught.value.message == MESSAGES["daily_limit"]
    assert sent == []
    assert used(ida) == 20


def test_nfr7_summary_regeneration_counts_against_the_same_limit(ida):
    use_up(ida, gateway.DAILY_LIMIT - 1)
    gateway.regenerate_summary(ida, summary_request())
    with pytest.raises(errors.DailyLimitReached):
        gateway.regenerate_summary(ida, summary_request())
    assert used(ida) == 20


def test_nfr7_the_limit_resets_at_oslo_midnight(ida, freeze_now):
    yesterday_evening = datetime.datetime(2026, 11, 16, 23, 30, tzinfo=OSLO)
    freeze_now(yesterday_evening)
    use_up(ida)
    with pytest.raises(errors.DailyLimitReached):
        gateway.generate_study_material(ida, generate_request())

    # 00:05 in Oslo is still 23:05 UTC the day before; the day counts in Oslo (AD-12).
    freeze_now(datetime.datetime(2026, 11, 17, 0, 5, tzinfo=OSLO))
    gateway.generate_study_material(ida, generate_request())
    assert used(ida, datetime.date(2026, 11, 17)) == 1
    assert used(ida, datetime.date(2026, 11, 16)) == 20


def test_nfr7_one_students_limit_does_not_block_another(ida, student):
    jonas = student("jonas@example.no")
    use_up(ida)
    gateway.generate_study_material(jonas, generate_request())
    assert used(jonas) == 1
    assert gateway.remaining_today(ida) == 0


def test_nfr7_a_failed_send_still_counts(ida, monkeypatch):
    def fail(request):
        raise errors.InvalidFormat()

    monkeypatch.setattr(gateway, "_send_generate", fail)
    with pytest.raises(errors.InvalidFormat):
        gateway.generate_study_material(ida, generate_request())
    assert used(ida) == 1


# ---- Matrix: Inside atomic (AD-19) -------------------------------------------------------


def test_nfr7_a_gateway_call_inside_a_transaction_is_refused(ida):
    with transaction.atomic():
        with pytest.raises(AssertionError):
            gateway.generate_study_material(ida, generate_request())
        with pytest.raises(AssertionError):
            gateway.regenerate_summary(ida, summary_request())
    assert used(ida) == 0


def test_nfr7_the_increment_is_committed_before_the_send(ida, monkeypatch):
    seen = []

    def send(request):
        # In autocommit (no open transaction), so the increment read here is committed.
        assert not connection.in_atomic_block
        seen.append(GenerationCallCount.objects.get(student=ida).count)
        return mock.study_material(request.detail_level)

    monkeypatch.setattr(gateway, "_send_generate", send)
    gateway.generate_study_material(ida, generate_request())
    assert seen == [1]


# ---- Matrix: Real mode and privacy (FR-21, FR-22, AD-17, story 10) ----------------------


@pytest.fixture
def real(settings):
    settings.AI_PROVIDER = "anthropic"


@pytest.fixture
def adapter(monkeypatch):
    """Fakes the three adapter operations and records what was sent."""
    sent = []
    monkeypatch.setattr(anthropic_adapter, "generate", lambda r: sent.append("generate") or mock.study_material("medium"))
    monkeypatch.setattr(anthropic_adapter, "summary", lambda r: sent.append("summary") or mock.summary("short"))
    monkeypatch.setattr(
        anthropic_adapter, "grade", lambda r: sent.append("grade") or GradeResponse(grade="correct", explanation="Ja.")
    )
    return sent


def grade_request() -> GradeRequest:
    return GradeRequest(prompt="Hva?", model_answer="Redundans.", answer="Redundans.", source_text="Tekst.")


def test_fr22_real_mode_without_acceptance_sends_nothing_and_counts_nothing(ida, real, adapter, caplog):
    with caplog.at_level(logging.INFO, logger="ai.gateway"):
        for call in (
            lambda: gateway.generate_study_material(ida, generate_request(sha=OTHER_SHA)),
            lambda: gateway.regenerate_summary(ida, summary_request(sha=OTHER_SHA)),
            lambda: gateway.grade_free_text(ida, grade_request()),
        ):
            with pytest.raises(errors.PrivacyNotAccepted) as caught:
                call()
            assert caught.value.code == "privacy_not_accepted"
            assert caught.value.message == MESSAGES["privacy_not_accepted"]
    assert adapter == []
    assert used(ida) == 0
    assert "outcome=privacy_not_accepted" in caplog.text


# Every gateway operation that sends Source text, with a request for it. A new operation must be
# added here, so it cannot skip the privacy check (AD-17).
PRIVATE_OPERATIONS = {
    "generate_study_material": lambda: generate_request(sha=OTHER_SHA),
    "regenerate_summary": lambda: summary_request(sha=OTHER_SHA),
    "grade_free_text": grade_request,
}
# Not built yet (story 16). When it is, it must move to PRIVATE_OPERATIONS.
NOT_BUILT = {"simpler_explanation"}


def test_ad17_every_gateway_operation_that_takes_a_student_checks_privacy(ida, real, adapter):
    import inspect

    operations = {
        name
        for name, function in inspect.getmembers(gateway, inspect.isfunction)
        if function.__module__ == gateway.__name__
        and not name.startswith("_")
        and list(inspect.signature(function).parameters)[:2] == ["student", "request"]
    }
    assert operations == set(PRIVATE_OPERATIONS) | NOT_BUILT, "add the new operation to PRIVATE_OPERATIONS"
    for name, request in PRIVATE_OPERATIONS.items():
        with pytest.raises(errors.PrivacyNotAccepted):
            getattr(gateway, name)(ida, request())
    for name in NOT_BUILT:
        with pytest.raises(NotImplementedError):
            getattr(gateway, name)(ida, None)
    assert adapter == []
    assert used(ida) == 0


def test_fr22_privacy_is_checked_before_the_counter(ida, real, adapter):
    use_up(ida)
    with pytest.raises(errors.PrivacyNotAccepted):
        gateway.generate_study_material(ida, generate_request(sha=OTHER_SHA))
    assert used(ida) == gateway.DAILY_LIMIT and adapter == []


def test_fr21_real_mode_with_acceptance_sends_through_the_adapter(ida, real, adapter):
    accept_privacy(ida)
    ida.refresh_from_db()
    assert isinstance(gateway.generate_study_material(ida, generate_request(sha=OTHER_SHA)), StudyMaterial)
    assert isinstance(gateway.regenerate_summary(ida, summary_request(sha=OTHER_SHA)), SummaryResponse)
    assert gateway.grade_free_text(ida, grade_request()).grade == "correct"
    assert adapter == ["generate", "summary", "grade"]
    # Generation and Summary count; grading never does (AD-3).
    assert used(ida) == 2


def test_fr21_a_failed_real_send_still_counts(ida, real, monkeypatch):
    accept_privacy(ida)

    def reject(request):
        raise errors.KeyRejected()

    monkeypatch.setattr(anthropic_adapter, "generate", reject)
    with pytest.raises(errors.KeyRejected):
        gateway.generate_study_material(ida, generate_request(sha=OTHER_SHA))
    assert used(ida) == 1


def test_fr20_mock_mode_never_checks_privacy(ida, adapter):
    assert ida.privacy_accepted_at is None
    gateway.generate_study_material(ida, generate_request())
    gateway.grade_free_text(ida, grade_request())
    assert adapter == []


def test_fr21_not_yet_built_operations_raise_not_implemented(ida):
    with pytest.raises(NotImplementedError):
        gateway.simpler_explanation(ida, None)


# ---- Errors and logging (AD-2) -----------------------------------------------------------


def test_nfr7_daily_limit_message_names_the_limit():
    assert str(gateway.DAILY_LIMIT) in MESSAGES["daily_limit"]


def test_fr20_error_codes_match_failure_reason():
    codes = {error.code for error in errors.ERRORS}
    assert len(codes) == len(errors.ERRORS)
    assert codes | {"timed_out"} == set(FailureReason.values)


def test_fr20_schema_detail_levels_match_courses():
    assert set(GenerateRequest.model_fields["detail_level"].annotation.__args__) == set(DetailLevel.values)


def test_fr20_gateway_logs_student_operation_and_outcome_but_no_text(ida, caplog, settings):
    settings.ANTHROPIC_API_KEY = "sk-ant-secret-should-never-be-logged"
    with caplog.at_level(logging.INFO, logger="ai.gateway"):
        gateway.generate_study_material(ida, generate_request())
        with pytest.raises(errors.NeedsKey):
            gateway.generate_study_material(ida, generate_request(sha=OTHER_SHA))
    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert f"student={ida.pk}" in logged
    assert "generate_study_material" in logged
    assert "outcome=ok" in logged and "outcome=needs_key" in logged
    assert "Normalisering fjerner redundans" not in logged
    assert "sk-ant-secret" not in logged


def test_nfr7_counter_rows_cascade_with_the_student(ida):
    gateway.generate_study_material(ida, generate_request())
    ida.delete()
    assert GenerationCallCount.objects.count() == 0
