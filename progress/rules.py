"""Topic score, Course score and Weak topics: the pure rules (AD-10, FR-16, FR-17).

No queries and no writes. Means are exact `Fraction`s, so «half up» never meets a float error
(11.5 / 20 is exactly 57.5 %, shown as 58 %).
"""

import math
from fractions import Fraction

from quiz.rules import WEIGHTS

# The Topic score uses the 20 most recent counted Answers (FR-16).
WINDOW = 20
# Fewer counted Answers than this: no score («Ikke nok data ennå»), and never Weak (FR-16).
MIN_ANSWERS = 5
# A Topic whose score (a whole percent) is below this is a Weak topic (FR-17).
WEAK_BELOW = 60


def percent(mean: Fraction) -> int:
    """A mean in 0..1 as a whole percent, rounded half up."""
    return int(mean * 100 + Fraction(1, 2))


def topic_mean(grades: list[str]) -> Fraction | None:
    """The WEIGHTS mean of the newest WINDOW Grades (newest first), or None below MIN_ANSWERS."""
    window = [grade for grade in grades if grade in WEIGHTS][:WINDOW]
    if len(window) < MIN_ANSWERS:
        return None
    return sum((Fraction(WEIGHTS[grade]) for grade in window), Fraction(0)) / len(window)


def course_mean(topic_means: list[Fraction | None]) -> Fraction | None:
    """The mean of the Topic scores that exist (unrounded), or None when none does (FR-16)."""
    scored = [mean for mean in topic_means if mean is not None]
    if not scored:
        return None
    return sum(scored, Fraction(0)) / len(scored)


def is_weak(score: int | None) -> bool:
    """Weak compares the shown percent, so a tag never sits beside «60 %»."""
    return score is not None and score < WEAK_BELOW


# «ca. {m} min» on the next-step-band (EXPERIENCE.md, Next step): minutes per item, rounded up.
CARD_MINUTES = 0.8
QUESTION_MINUTES = 0.8
SOURCE_MINUTES = 2


def band_minutes(count: int, rate: float) -> int:
    """`ceil(count × rate)`, exact: 35 × 0.8 is 28, never 28.000000000000004 → 29."""
    return math.ceil(count * Fraction(str(rate)))
