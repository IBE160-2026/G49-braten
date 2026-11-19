"""SM-2 / CAP-12 (story 14): every acceptance check is tied to named evidence.

Checks 7–10 (T) are proven by the covering tests named here; renaming or removing one fails this
file, naming the check. Checks 1–6 (R) are the README's «Prøv alle kjernefunksjonene» steps; the
`test_uj5_…` tests in tests/test_examiner_path.py walk them through the views, check 4 by uploading
the committed sample/for_mange_sider.pdf. The README's SM-2 table must name exactly the same tests,
so the README cannot drift from the evidence.
"""

import importlib
import re
from pathlib import Path

import pytest

README = Path(__file__).resolve().parent.parent / "README.md"

# check -> the covering tests, as "module::function" under tests/.
COVERING_TESTS: dict[int, tuple[str, ...]] = {
    # 1–6 (R): the README steps, walked by the test_uj5_… tests.
    1: ("test_examiner_path::test_uj5_examiner_path_end_to_end_in_mock_mode",),
    2: ("test_examiner_path::test_uj5_examiner_path_end_to_end_in_mock_mode",),
    3: (
        "test_examiner_path::test_uj5_examiner_path_end_to_end_in_mock_mode",
        "test_examiner_path::test_uj5_other_pdf_in_mock_mode_is_stored_with_the_needs_key_message",
    ),
    4: (
        "test_examiner_path::test_uj5_committed_51_page_pdf_is_refused_naming_the_page_limit",
        "test_ingestion::test_fr3_51_page_pdf_is_refused_naming_the_limit",
    ),
    5: ("test_examiner_path::test_uj5_examiner_path_end_to_end_in_mock_mode",),
    6: ("test_examiner_path::test_uj5_examiner_path_end_to_end_in_mock_mode",),
    # 7–10 (T).
    7: (
        "test_review_rules::test_fr15_next_due_moves_boxes_and_caps_at_eight",
        "test_review::test_fr15_acceptance_three_good_ratings_end_and_today_drops",
    ),
    8: (
        "test_progress::test_fr17_seeded_weak_topics_lowest_first",
        "test_progress::test_fr17_p04_lists_weak_topics_first_with_tags_and_the_weak_quiz_button",
    ),
    9: (
        "test_ai_gateway::test_nfr7_twenty_calls_succeed_and_the_21st_raises_daily_limit",
        "test_generation::test_nfr7_a_pending_source_at_the_limit_fails_with_daily_limit",
    ),
    10: (
        "test_next_step::test_fr28_hjem_due_cards_come_first_per_fag",
        "test_next_step::test_fr28_rules_1_and_2_come_before_an_empty_topic",
    ),
}


def assert_covered(check: int) -> None:
    for name in COVERING_TESTS[check]:
        module_name, function = name.split("::")
        module = importlib.import_module(f"tests.{module_name}")
        assert callable(getattr(module, function, None)), f"SM-2 check {check}: covering test {name} is missing"


def test_sm2_check_7_review_dates_follow_fr15():
    assert_covered(7)


def test_sm2_check_8_weak_topics_show_as_in_fr17():
    assert_covered(8)


def test_sm2_check_9_generation_stops_at_the_nfr7_limit():
    assert_covered(9)


def test_sm2_check_10_next_step_follows_the_fr28_order():
    assert_covered(10)


@pytest.mark.parametrize("check", range(1, 7))
def test_sm2_checks_1_to_6_point_to_the_uj5_test_and_the_readme(check):
    assert_covered(check)


SM2_HEADING = "## Akseptansesjekkliste (SM-2)"


def readme_table_rows() -> dict[int, str]:
    """The table under the README's SM-2 heading: check number -> the whole row.

    Only that section is read (up to the next `## ` heading); a check number twice fails.
    """
    lines = README.read_text(encoding="utf-8").splitlines()
    assert SM2_HEADING in lines, f"the README has no {SM2_HEADING!r} section"
    rows: dict[int, str] = {}
    for line in lines[lines.index(SM2_HEADING) + 1 :]:
        if line.startswith("## "):
            break
        match = re.match(r"\|\s*(\d+)\s*\|", line)
        if match:
            check = int(match.group(1))
            assert check not in rows, f"SM-2 check {check} appears twice in the README's table"
            rows[check] = line
    return rows


def test_sm2_readme_table_names_the_same_tests():
    rows = readme_table_rows()
    assert sorted(rows) == list(range(1, 11)), "the README's SM-2 table must have checks 1–10, once each"
    for check, names in COVERING_TESTS.items():
        cited = set(re.findall(r"`(test_\w+)`", rows[check]))
        expected = {name.split("::")[1] for name in names}
        assert cited == expected, f"SM-2 check {check}: the README cites {sorted(cited)}, expected {sorted(expected)}"
        kind = "T" if check >= 7 else "R"
        assert f"| {kind} |" in rows[check], f"SM-2 check {check} must be marked {kind}"
