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


class Topic(models.Model):
    """A tema under a fag (PRD Topic, FR-2). Listed in creation order."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topics")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    created_at = models.DateTimeField(default=created_now)

    objects = OwnedQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return self.name


class SourceKind(models.TextChoices):
    """Display text lives in templates (components/source_row.html)."""

    PDF = "pdf"
    TEXT = "text"
    PASTED = "pasted"


class Status(models.TextChoices):
    """Source status (FR-9, AD-5). Only courses.services changes it; text is in status_label.html."""

    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class DetailLevel(models.TextChoices):
    """Display text lives in templates (components/source_row.html)."""

    SHORT = "short"
    MEDIUM = "medium"
    DETAILED = "detailed"


class FailureReason(models.TextChoices):
    """The AD-2 error codes plus `timed_out` (AD-5)."""

    NEEDS_KEY = "needs_key"
    PRIVACY_NOT_ACCEPTED = "privacy_not_accepted"
    DAILY_LIMIT = "daily_limit"
    RATE_LIMITED = "rate_limited"
    REFUSED = "refused"
    TRUNCATED = "truncated"
    INVALID_FORMAT = "invalid_format"
    KEY_REJECTED = "key_rejected"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    TIMED_OUT = "timed_out"


class Source(models.Model):
    """A kilde in a tema (PRD Source, FR-2, FR-9). Listed newest first."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sources")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="sources")
    name = models.CharField(max_length=NAME_MAX_LENGTH)
    kind = models.CharField(max_length=10, choices=SourceKind.choices)
    size_bytes = models.PositiveBigIntegerField(default=0)
    detail_level = models.CharField(max_length=10, choices=DetailLevel.choices, default=DetailLevel.MEDIUM)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    failure_reason = models.CharField(max_length=24, choices=FailureReason.choices, blank=True)
    content_sha256 = models.CharField(max_length=64, blank=True)
    language = models.CharField(max_length=16, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    removed_count = models.PositiveIntegerField(default=0)
    dropped_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=created_now)

    objects = OwnedQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return self.name
