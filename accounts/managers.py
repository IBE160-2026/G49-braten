import unicodedata

from django.contrib.auth.base_user import BaseUserManager


def normalize(email: str | None) -> str:
    """The one email normalisation, in Python, because SQLite folds case only for A-Z.

    NFKC first, so a decomposed Å (A + combining ring) matches the composed one.
    """
    return unicodedata.normalize("NFKC", email or "").strip().lower()


class StudentManager(BaseUserManager):
    """Emails are stored lower-cased and looked up case-insensitively (AD-7)."""

    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(email=normalize(username))

    def _create_user(self, email, password, **extra_fields):
        email = normalize(email)
        if not email:
            raise ValueError("A Student needs an email address.")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, **extra_fields)
