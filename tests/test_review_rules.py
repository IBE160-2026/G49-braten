"""FR-15 / AD-11 (story 11): the Leitner rules, pure."""

import datetime

import pytest

from review.rules import INTERVALS, RatingValue, next_due, return_label

TODAY = datetime.date(2026, 11, 18)


def days(n: int) -> datetime.date:
    return TODAY + datetime.timedelta(days=n)


def test_fr15_intervals_are_the_eight_boxes():
    assert INTERVALS == (1, 3, 7, 14, 30, 60, 120, 180)


def test_fr15_good_interval_grows():
    box, due = next_due(1, RatingValue.GOOD, TODAY)
    assert (box, due) == (2, days(3))
    box, due = next_due(box, RatingValue.GOOD, TODAY)
    assert (box, due) == (3, days(7))
    box, due = next_due(box, RatingValue.GOOD, TODAY)
    assert (box, due) == (4, days(14))


@pytest.mark.parametrize(
    ("box", "rating", "expected"),
    [
        (1, RatingValue.AGAIN, (1, 0)),
        (5, RatingValue.AGAIN, (1, 0)),
        (1, RatingValue.HARD, (1, 1)),
        (4, RatingValue.HARD, (4, 14)),
        (1, RatingValue.GOOD, (2, 3)),
        (1, RatingValue.EASY, (3, 7)),
        (7, RatingValue.EASY, (8, 180)),
        (8, RatingValue.GOOD, (8, 180)),
        (8, RatingValue.EASY, (8, 180)),
        (8, RatingValue.HARD, (8, 180)),
    ],
)
def test_fr15_next_due_moves_boxes_and_caps_at_eight(box, rating, expected):
    new_box, due = next_due(box, rating, TODAY)
    assert (new_box, (due - TODAY).days) == expected


def test_fr15_next_due_refuses_an_unknown_rating():
    with pytest.raises(ValueError):
        next_due(1, "great", TODAY)


@pytest.mark.parametrize(
    ("n", "label"),
    [
        (0, "i dag"), (1, "i morgen"), (2, "om 2 dager"), (6, "om 6 dager"),
        (7, "om 1 uke"), (13, "om 1 uke"), (14, "om 2 uker"), (29, "om 4 uker"),
        (30, "om 1 mnd."), (59, "om 1 mnd."), (60, "om 2 mnd."), (119, "om 3 mnd."),
        (120, "om 4 mnd."), (180, "om 6 mnd."),
    ],
)  # fmt: skip
def test_fr15_return_label_boundaries(n, label):
    assert return_label(n) == label
