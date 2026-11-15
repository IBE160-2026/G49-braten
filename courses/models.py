from django.conf import settings
from django.db import models

from core import time
from core.ownership import OwnedQuerySet

NAME_MAX_LENGTH = 80
CODE_MAX_LENGTH = 20


def created_now():
    """Looked up at call time, so tests that freeze core.time.now also freeze this."""
    return time.now()


class Course(models.Model):
    """A fag (PRD Course, FR-2). Listed in creation order everywhere."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    code = models.CharField(max_length=CODE_MAX_LENGTH, blank=True)
    created_at = models.DateTimeField(default=created_now)

    objects = OwnedQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return self.name
