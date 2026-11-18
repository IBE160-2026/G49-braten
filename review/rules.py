"""Leitner scheduling (FR-15, AD-11). Pure rules: no queries, no writes.

`next_due` is the one scheduler: review.services writes with it and P09 previews the four
rating-buttons with it.
"""

import datetime

from django.db import models

from core.messages import MESSAGES

# Days until the next Review for a card in box 1 to 8 (FR-15: never longer than 180 days).
INTERVALS = (1, 3, 7, 14, 30, 60, 120, 180)
FIRST_BOX = 1
LAST_BOX = len(INTERVALS)

# New cards introduced per Oslo day, across all Courses (FR-15, PRD §10).
DAILY_NEW_CARDS = 20


class RatingValue(models.TextChoices):
    """A rating of a card; the labels are the interface words (EXPERIENCE.md, glossary)."""

    AGAIN = "again", "Igjen"
    HARD = "hard", "Vanskelig"
    GOOD = "good", "Bra"
    EASY = "easy", "Lett"


# How many boxes each rating moves a card up («Igjen» is handled apart: back to box 1, due today).
STEPS = {RatingValue.HARD: 0, RatingValue.GOOD: 1, RatingValue.EASY: 2}


def next_due(box: int, rating: str, today: datetime.date) -> tuple[int, datetime.date]:
    """The card's new box and due date after `rating`."""
    if rating == RatingValue.AGAIN:
        return FIRST_BOX, today
    if rating not in STEPS:
        raise ValueError(f"Unknown rating: {rating!r}")
    new_box = min(max(box, FIRST_BOX) + STEPS[rating], LAST_BOX)
    return new_box, today + datetime.timedelta(days=INTERVALS[new_box - 1])


def return_label(days: int) -> str:
    """When a card returns, in bokmål relative to today: «i dag», «i morgen», «om 3 dager» …"""
    if days <= 0:
        return MESSAGES["return_today"]
    if days == 1:
        return MESSAGES["return_tomorrow"]
    if days < 7:
        return MESSAGES["return_days"].format(n=days)
    if days < 14:
        return MESSAGES["return_week"]
    if days < 30:
        return MESSAGES["return_weeks"].format(n=days // 7)
    if days < 60:
        return MESSAGES["return_month"]
    return MESSAGES["return_months"].format(n=days // 30)
