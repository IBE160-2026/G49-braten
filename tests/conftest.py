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


@pytest.fixture(autouse=True)
def no_real_anthropic_client(monkeypatch):
    """No test reaches the real Anthropic client (story 10); tests that need one install a fake."""

    def refuse():
        raise AssertionError("A test tried to build the real Anthropic client; install a fake instead.")

    monkeypatch.setattr("ai.anthropic_adapter._client", refuse)
