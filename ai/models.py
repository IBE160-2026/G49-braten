from django.conf import settings
from django.db import models

from core.ownership import OwnedQuerySet


class GenerationCallCount(models.Model):
    """How many Generation calls a Student has made on one Oslo day (NFR-7, AD-3, AD-12).

    Written only by `ai.gateway`, one committed conditional UPDATE per call (AD-19).
    """

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="generation_call_counts"
    )
    day = models.DateField()
    count = models.PositiveIntegerField(default=0)

    objects = OwnedQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "day"], name="generationcallcount_unique_student_day"),
        ]

    def __str__(self) -> str:
        return f"{self.student_id}:{self.day}:{self.count}"
