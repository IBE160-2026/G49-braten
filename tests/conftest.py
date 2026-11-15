import datetime

import pytest


@pytest.fixture
def freeze_now(monkeypatch):
    """Freeze core.time at an aware datetime.

    today() and model defaults follow, since they call core.time.now() at run time.
    """

    def _freeze(moment: datetime.datetime) -> None:
        assert moment.tzinfo is not None, "freeze with an aware datetime"
        monkeypatch.setattr("core.time.now", lambda: moment)

    return _freeze


PASSWORD = "lang-og-trygg-frase-42"


@pytest.fixture
def student(db):
    """Factory: student("ida@example.no") creates a Student with the shared test PASSWORD."""
    from accounts.models import Student

    def _make(email: str = "ida@example.no", password: str = PASSWORD):
        return Student.objects.create_user(email, password)

    return _make
