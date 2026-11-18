"""FR-12 (story 8): `grade_free_text`, the Mock word-overlap rule and the Grade rules (AD-2, AD-3, AD-4).

Gateway calls assert they are not inside a transaction, so these tests use `transaction=True`.
"""

import logging

import pytest
from django.db import transaction

from ai import errors, gateway, mock
from ai.models import GenerationCallCount
from ai.schemas import GradeRequest, GradeResponse
from core import time
from core.messages import MESSAGES
from quiz.rules import WEIGHTS, Grade, grade_choice, option_letter

pytestmark = pytest.mark.django_db(transaction=True)

MODEL = "Normalisering fjerner redundans i tabeller og hindrer anomalier ved oppdatering"


def request_for(answer: str, model: str = MODEL) -> GradeRequest:
    return GradeRequest(prompt="Hva gjør normalisering?", model_answer=model, answer=answer, source_text="Tekst.")


def used(student) -> int:
    row = GenerationCallCount.objects.filter(student=student, day=time.today()).first()
    return row.count if row else 0


@pytest.fixture
def ida(student):
    return student("ida@example.no")


# ---- The Mock rule (AD-4) ------------------------------------------------------------------


def test_fr12_keywords_are_lower_cased_words_of_three_letters_or_more_with_aeoa():
    assert mock.keywords("Øl, ÆRE og på Å-ord: blå 3NF i tabeller") == {"ære", "ord", "blå", "tabeller"}


def test_fr12_mock_rule_thresholds():
    model = "alfa beta gamma delta epsilon zeta eta theta iota kappa"  # 10 keywords
    words = model.split()

    def grade_with(k: int) -> str:
        return mock.grade(request_for(" ".join(words[:k]), model)).grade

    assert grade_with(10) == "correct"
    assert grade_with(6) == "correct"  # 0.6
    assert grade_with(5) == "partial"
    assert grade_with(3) == "partial"  # 0.3
    assert grade_with(2) == "incorrect"
    assert grade_with(0) == "incorrect"


def test_fr12_mock_explanation_counts_keywords():
    response = mock.grade(request_for("Normalisering fjerner redundans"))
    m = len(mock.keywords(MODEL))
    assert response.explanation == MESSAGES["mock_grade_explanation"].format(k=3, m=m)
    assert response.explanation.startswith("Demo-vurdering: 3 av ")


def test_fr12_mock_with_an_empty_model_answer_is_incorrect():
    assert mock.grade(request_for("hva som helst", model="")).grade == "incorrect"


def test_fr12_grade_response_is_lower_cased_and_restricted():
    assert GradeResponse.model_validate({"grade": " Correct ", "explanation": "x"}).grade == "correct"
    with pytest.raises(ValueError):
        GradeResponse.model_validate({"grade": "not_graded", "explanation": "x"})


def test_fr12_schema_grades_match_the_graded_values_of_quiz_rules():
    values = set(GradeResponse.model_fields["grade"].annotation.__args__)
    assert values == set(Grade.values) - {Grade.NOT_GRADED}


def test_fr16_grade_weights():
    assert WEIGHTS == {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}
    assert Grade.NOT_GRADED not in WEIGHTS


def test_fr11_multiple_choice_is_graded_in_code():
    assert grade_choice(2, 2) == Grade.CORRECT
    assert grade_choice(1, 2) == Grade.INCORRECT
    assert [option_letter(i) for i in range(4)] == ["A", "B", "C", "D"]
    assert option_letter(None) == ""


# ---- The gateway (AD-2, AD-3, AD-19) -------------------------------------------------------


def test_nfr7_mock_grading_is_not_counted_and_works_for_any_source(ida):
    response = gateway.grade_free_text(ida, request_for("Normalisering fjerner redundans i tabeller"))
    assert response.grade == "partial"
    assert used(ida) == 0
    assert not GenerationCallCount.objects.exists()


def test_nfr7_grading_at_the_daily_limit_still_works(ida):
    GenerationCallCount.objects.create(student=ida, day=time.today(), count=gateway.DAILY_LIMIT)
    assert gateway.grade_free_text(ida, request_for(MODEL)).grade == "correct"
    assert used(ida) == gateway.DAILY_LIMIT


def test_fr21_real_mode_grading_raises_provider_unavailable_uncounted(ida, settings):
    settings.AI_PROVIDER = "anthropic"
    with pytest.raises(errors.ProviderUnavailable):
        gateway.grade_free_text(ida, request_for(MODEL))
    assert used(ida) == 0


def test_ad19_grading_inside_a_transaction_is_refused(ida):
    with transaction.atomic():
        with pytest.raises(AssertionError):
            gateway.grade_free_text(ida, request_for(MODEL))


def test_fr12_grading_logs_the_outcome_but_no_text(ida, caplog):
    with caplog.at_level(logging.INFO, logger="ai.gateway"):
        gateway.grade_free_text(ida, request_for("hemmelig svartekst"))
    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert f"student={ida.pk}" in logged and "grade_free_text" in logged and "outcome=ok" in logged
    assert "hemmelig" not in logged and "Normalisering" not in logged
