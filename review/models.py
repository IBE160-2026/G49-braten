"""Leitner state, Reviews and their Ratings (FR-14, FR-15, AD-11).

Written only by review.services. Every row is owned (`student`, AD-7) and goes with its Flashcard,
and so with its Source, Topic and Course, by cascade (AD-8).
"""

from django.conf import settings
from django.db import models

from core import time
from core.ownership import OwnedQuerySet
from courses.models import Course, Topic
from courses.scope import Scope
from review.rules import FIRST_BOX, RatingValue
from studymat.models import Flashcard


def _now():
    """Looked up at call time, so tests that freeze core.time.now also freeze this."""
    return time.now()


class ReviewState(models.Model):
    """An introduced card: its box (1–8) and the Oslo date it is due. A card without one is new."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_states")
    flashcard = models.OneToOneField(Flashcard, on_delete=models.CASCADE, related_name="review_state")
    box = models.PositiveSmallIntegerField(default=FIRST_BOX)
    due_date = models.DateField()
    introduced_on = models.DateField()

    objects = OwnedQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["student", "due_date"], name="reviewstate_student_due"),
            models.Index(fields=["student", "introduced_on"], name="reviewstate_student_intro"),
        ]

    def __str__(self) -> str:
        return f"{self.flashcard_id}: box {self.box}, due {self.due_date}"


class Review(models.Model):
    """One Repetisjon. Its scope is all fag (no course, no topic), one `course` or one `topic`."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.CASCADE, related_name="reviews")
    topic = models.ForeignKey(Topic, null=True, blank=True, on_delete=models.CASCADE, related_name="reviews")
    started_at = models.DateTimeField(default=_now)
    ended_at = models.DateTimeField(null=True, blank=True)
    return_url = models.CharField(max_length=500)

    objects = OwnedQuerySet.as_manager()

    class Meta:
        ordering = ["-started_at", "-id"]

    def __str__(self) -> str:
        return f"Review {self.pk}"

    @property
    def scope(self) -> Scope:
        return Scope(course_id=self.course_id, topic_id=self.topic_id)


class Rating(models.Model):
    """One press of a rating-button. `step` (from 1) makes a double submit a no-op."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="ratings")
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name="ratings")
    rating = models.CharField(max_length=8, choices=RatingValue.choices)
    step = models.PositiveIntegerField()
    rated_at = models.DateTimeField(default=_now)

    objects = OwnedQuerySet.as_manager()

    class Meta:
        ordering = ["review", "step"]
        constraints = [
            models.UniqueConstraint(fields=["review", "step"], name="rating_unique_review_step"),
        ]

    def __str__(self) -> str:
        return f"{self.review_id}:{self.step}:{self.rating}"
