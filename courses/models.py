import datetime

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


# AD-5: a run still `generating` this long after its claim is stale: it reads as failed/timed_out
# and may be claimed again.
STALE_AFTER = datetime.timedelta(minutes=5)


def _stale_before() -> datetime.datetime:
    return time.now() - STALE_AFTER


class SourceQuerySet(OwnedQuerySet):
    def claimable(self):
        """Sources a generation run may claim (AD-5): pending, failed, or a stale `generating`."""
        return self.filter(
            models.Q(status__in=[Status.PENDING, Status.FAILED])
            | models.Q(status=Status.GENERATING, started_at__lt=_stale_before())
            | models.Q(status=Status.GENERATING, started_at__isnull=True)
        )


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

    objects = SourceQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return self.name

    @property
    def is_stale(self) -> bool:
        """`generating` past STALE_AFTER: the same predicate as `claimable()` (AD-5)."""
        return self.status == Status.GENERATING and (self.started_at is None or self.started_at < _stale_before())

    @property
    def effective_status(self) -> str:
        """What everyone reads (AD-5): `pending` shows as generating, a stale run as failed."""
        if self.status == Status.PENDING:
            return Status.GENERATING
        if self.is_stale:
            return Status.FAILED
        return self.status

    @property
    def effective_failure_reason(self) -> str:
        if self.is_stale:
            return FailureReason.TIMED_OUT
        return self.failure_reason if self.status == Status.FAILED else ""
