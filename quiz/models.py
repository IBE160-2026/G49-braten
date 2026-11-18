"""A Practice-mode Quiz, its Questions in order, and the Student's Answers (CAP-7, FR-10 to FR-12).

Written only by quiz.services. Every row is owned (`student`, AD-7); QuizQuestion and Answer go
with their Question, and so with its Source, by cascade (AD-8).
"""

from django.conf import settings
from django.db import models
from django.db.models.functions import Coalesce

from core import time
from core.ownership import OwnedQuerySet
from courses.models import Course
from quiz.rules import Grade
from studymat.models import Question


def _now():
    """Looked up at call time, so tests that freeze core.time.now also freeze this."""
    return time.now()


class QuizKind(models.TextChoices):
    PRACTICE = "practice"


class Quiz(models.Model):
    """One Quiz. `start_token` makes D06's start idempotent; `return_url` is where it was started."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quizzes")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    kind = models.CharField(max_length=12, choices=QuizKind.choices, default=QuizKind.PRACTICE)
    started_at = models.DateTimeField(default=_now)
    return_url = models.CharField(max_length=500)
    start_token = models.CharField(max_length=64)

    objects = OwnedQuerySet.as_manager()

    class Meta:
        ordering = ["-started_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["student", "start_token"], name="quiz_unique_student_start_token"),
        ]

    def __str__(self) -> str:
        return f"Quiz {self.pk}"


class QuizQuestion(models.Model):
    """A Question at a fixed position (from 1). Deleting the Question leaves a gap."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="quiz_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="quiz_questions")
    position = models.PositiveIntegerField()

    objects = OwnedQuerySet.as_manager()

    class Meta:
        ordering = ["quiz", "position"]
        constraints = [
            models.UniqueConstraint(fields=["quiz", "position"], name="quizquestion_unique_quiz_position"),
            models.UniqueConstraint(fields=["quiz", "question"], name="quizquestion_unique_quiz_question"),
        ]

    def __str__(self) -> str:
        return f"{self.quiz_id}:{self.position}"


class AnswerQuerySet(OwnedQuerySet):
    def with_effective_grade(self):
        """`effective_grade`: the Student's override when there is one, else the Grade (FR-12)."""
        return self.annotate(effective_grade=Coalesce("override_grade", "grade"))


class Answer(models.Model):
    """The Student's one Answer to a Question in a Quiz. A null `grade` means grading is pending."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    chosen_index = models.PositiveSmallIntegerField(null=True, blank=True)
    text = models.TextField(blank=True)
    grade = models.CharField(max_length=12, choices=Grade.choices, null=True, blank=True)
    override_grade = models.CharField(max_length=12, choices=Grade.choices, null=True, blank=True)
    explanation = models.TextField(blank=True)
    is_mock = models.BooleanField(default=False)
    # The AIError code when grading failed (`grade` is then `not_graded`), so a reload says the same.
    failure = models.CharField(max_length=24, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    objects = AnswerQuerySet.as_manager()

    class Meta:
        ordering = ["quiz", "id"]
        constraints = [
            models.UniqueConstraint(fields=["quiz", "question"], name="answer_unique_quiz_question"),
        ]

    def __str__(self) -> str:
        return f"{self.quiz_id}:{self.question_id}:{self.grade}"

    @property
    def shown_grade(self) -> str:
        """The Grade to show: the override, else the Grade; pending (a crash mid-request) reads as
        not graded (story 8, Design Notes)."""
        return self.override_grade or self.grade or Grade.NOT_GRADED

    @property
    def shown_failure(self) -> str:
        if self.grade is None:
            return "provider_unavailable"
        return self.failure
