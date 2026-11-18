"""Grades and their weights (FR-12, FR-16). Pure rules: no queries, no writes."""

from django.db import models


class Grade(models.TextChoices):
    """The stored Grade of an Answer; the labels are the interface words (EXPERIENCE.md, glossary)."""

    CORRECT = "correct", "Riktig"
    PARTIAL = "partial", "Delvis riktig"
    INCORRECT = "incorrect", "Feil"
    NOT_GRADED = "not_graded", "Ikke rettet"


# What each Grade is worth in a score (FR-16). `not_graded` is worth nothing and counts nowhere.
WEIGHTS: dict[str, float] = {
    Grade.CORRECT: 1.0,
    Grade.PARTIAL: 0.5,
    Grade.INCORRECT: 0.0,
}

# The letters of a Multiple-choice Question's options, by index (AD-9: always four).
OPTION_LETTERS = ("A", "B", "C", "D")


def grade_choice(chosen_index: int, correct_index: int | None) -> str:
    """A Multiple-choice Answer is graded in code, never by the AI (FR-11)."""
    return Grade.CORRECT if chosen_index == correct_index else Grade.INCORRECT


def option_letter(index: int | None) -> str:
    if index is None or not 0 <= index < len(OPTION_LETTERS):
        return ""
    return OPTION_LETTERS[index]
