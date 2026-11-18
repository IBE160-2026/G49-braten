"""Due cards and the only writers of review state (FR-15, AD-11).

`introduce_today` and `rate` are the only writers of ReviewState; `start` and `finish` the only
writers of Review. `due_cards` is the one definition of Due cards: every count of them is taken
from it.
"""

import datetime
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.db.models import Count

from core import time
from courses.models import Status
from courses.scope import Scope
from review import rules
from review.models import Rating, Review, ReviewState
from studymat.models import Flashcard

# The lookup from a ReviewState to its Topic, for Scope.filter.
STATE_TOPIC = "flashcard__source__topic"


def _new_cards(student):
    """Cards from ready Sources with no ReviewState, in generation order (Source id, card id)."""
    return Flashcard.objects.filter(
        student=student, source__status=Status.READY, review_state__isnull=True
    ).order_by("source_id", "id")


def introduce_today(student) -> int:
    """Give up to `DAILY_NEW_CARDS − introduced today` new cards a state (box 1, due today).

    Idempotent per Oslo day, across all Courses; returns how many were introduced now.
    """
    today = time.today()
    room = rules.DAILY_NEW_CARDS - ReviewState.objects.filter(student=student, introduced_on=today).count()
    if room <= 0 or not _new_cards(student).exists():
        # Most page views end here, without taking SQLite's write lock.
        return 0
    with transaction.atomic():
        room = rules.DAILY_NEW_CARDS - ReviewState.objects.filter(student=student, introduced_on=today).count()
        if room <= 0:
            return 0
        cards = list(_new_cards(student).values_list("id", flat=True)[:room])
        ReviewState.objects.bulk_create(
            [
                ReviewState(student=student, flashcard_id=card_id, box=rules.FIRST_BOX, due_date=today, introduced_on=today)
                for card_id in cards
            ],
            ignore_conflicts=True,
        )
    return len(cards)


def due_cards(student, scope: Scope):
    """The Student's Due cards in `scope`: states due today or earlier, from ready Sources.

    Introduces today's new cards first; the scope never changes which cards are introduced.
    Ordered by due date, then generation order.
    """
    introduce_today(student)
    states = ReviewState.objects.filter(
        student=student, due_date__lte=time.today(), flashcard__source__status=Status.READY
    )
    return scope.filter(states, STATE_TOPIC).order_by("due_date", "flashcard__source_id", "flashcard_id")


def due_count_by_course(student) -> dict[int, int]:
    """{course id: Due cards} across all fag, from `due_cards`; fag with none are left out."""
    rows = (
        due_cards(student, Scope.all())
        .order_by()
        .values("flashcard__source__topic__course_id")
        .annotate(n=Count("id"))
    )
    return {row["flashcard__source__topic__course_id"]: row["n"] for row in rows}


def next_due_date(student, scope: Scope) -> datetime.date | None:
    """The first date after today on which a card in `scope` is due, or None. New cards still
    waiting for the daily limit count as due tomorrow."""
    states = ReviewState.objects.filter(
        student=student, due_date__gt=time.today(), flashcard__source__status=Status.READY
    )
    first = scope.filter(states, STATE_TOPIC).order_by("due_date").values_list("due_date", flat=True).first()
    if scope.filter(_new_cards(student), "source__topic").exists():
        # Cards held back by DAILY_NEW_CARDS are introduced from tomorrow at the latest.
        tomorrow = time.today() + datetime.timedelta(days=1)
        return min(first, tomorrow) if first else tomorrow
    return first


def _start_of_today() -> datetime.datetime:
    return datetime.datetime.combine(time.today(), datetime.time.min, tzinfo=time.OSLO)


def start(student, scope: Scope, return_url: str) -> Review:
    """The Student's open Review of `scope` started today (with `return_url` updated), else a new one."""
    review = (
        Review.objects.filter(
            student=student,
            course_id=scope.course_id,
            topic_id=scope.topic_id,
            ended_at__isnull=True,
            started_at__gte=_start_of_today(),
        )
        .order_by("-started_at", "-id")
        .first()
    )
    if review is not None:
        if review.return_url != return_url:
            review.return_url = return_url
            review.save(update_fields=["return_url"])
        return review
    return Review.objects.create(
        student=student, course_id=scope.course_id, topic_id=scope.topic_id, return_url=return_url
    )


def finish(review: Review) -> None:
    """Mark the Review ended (once)."""
    if review.ended_at is None:
        review.ended_at = time.now()
        review.save(update_fields=["ended_at"])


def rate(review: Review, flashcard: Flashcard, rating: str, step: int) -> bool:
    """Write the Rating at `step` and the card's new state from `rules.next_due`.

    A no-op (returns False) when `step` is already rated in this Review, so a double submit moves
    the card once.
    """
    if rating not in rules.RatingValue.values:
        raise ValueError(f"Unknown rating: {rating!r}")
    assert flashcard.student_id == review.student_id
    try:
        with transaction.atomic():
            if Rating.objects.filter(review=review, step=step).exists():
                return False
            state = ReviewState.objects.filter(student_id=review.student_id, flashcard=flashcard).first()
            if state is None:
                # The card (and so its state) was deleted after the view's due check.
                return False
            state.box, state.due_date = rules.next_due(state.box, rating, time.today())
            Rating.objects.create(
                student_id=review.student_id, review=review, flashcard=flashcard, rating=rating, step=step
            )
            state.save(update_fields=["box", "due_date"])
    except IntegrityError:
        # A concurrent request rated this step first.
        return False
    return True


# ---- Reading a Review ------------------------------------------------------------------------


@dataclass
class Progress:
    """Where a Review stands: the cards left in order, «N av M», and the next step number."""

    queue: list  # ReviewStates, the current card first
    done: int  # cards whose last rating here was not «Igjen»
    total: int  # distinct cards in this Review, rated or still due
    rated: int  # distinct cards rated in this Review
    next_step: int

    @property
    def current(self):
        return self.queue[0] if self.queue else None

    @property
    def number(self) -> int:
        return min(self.done + 1, self.total)


def progress(review: Review) -> Progress:
    """The order in a Review: cards not yet rated here first (due date, then generation order),
    then cards whose last rating here was «Igjen», oldest rating first."""
    due = list(
        due_cards(review.student, review.scope).select_related("flashcard__source__topic__course")
    )
    last: dict[int, Rating] = {}
    steps = 0
    for rating in Rating.objects.filter(review=review).order_by("step"):
        last[rating.flashcard_id] = rating
        steps = max(steps, rating.step)
    unrated = [state for state in due if state.flashcard_id not in last]
    again = sorted(
        # Only «Igjen» leaves a card due today; a card rated otherwise is here only when the Review
        # outlived its day, and it then waits behind the unrated ones too.
        (state for state in due if state.flashcard_id in last),
        key=lambda state: (last[state.flashcard_id].rated_at, last[state.flashcard_id].step),
    )
    done = sum(1 for rating in last.values() if rating.rating != rules.RatingValue.AGAIN)
    total = len(set(last) | {state.flashcard_id for state in due})
    return Progress(queue=unrated + again, done=done, total=total, rated=len(last), next_step=steps + 1)
