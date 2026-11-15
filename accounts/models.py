from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.db.models.functions import Lower

from accounts.managers import StudentManager, normalize
from core import time


def joined_now():
    """Looked up at call time, so tests that freeze core.time.now also freeze this."""
    return time.now()


class Student(AbstractBaseUser):
    """The app's only role and its AUTH_USER_MODEL from the first migration (AD-7).

    No PermissionsMixin and no staff flag: the admin is off and every Student has the same rights.
    """

    # unique=True satisfies Django's USERNAME_FIELD check; the Lower() constraint below
    # also blocks case duplicates written without save().
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=joined_now)
    # Written only by accounts.services.accept_privacy() (FR-22, AD-17).
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)

    objects = StudentManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="student_email_ci_unique"),
        ]

    def save(self, *args, **kwargs):
        self.email = normalize(self.email)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.email
