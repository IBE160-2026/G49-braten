"""Writes to `accounts` models from other apps go through here (AD-1)."""

from accounts.models import Student
from core import time


def accept_privacy(student: Student) -> None:
    """D04 «Jeg forstår, fortsett» (FR-22, AD-17): sets `privacy_accepted_at` once; the only writer."""
    if student.privacy_accepted_at is not None:
        return
    now = time.now()
    # Conditional, so a second tab accepting at the same time keeps the first time.
    Student.objects.filter(pk=student.pk, privacy_accepted_at__isnull=True).update(privacy_accepted_at=now)
    student.refresh_from_db(fields=["privacy_accepted_at"])
