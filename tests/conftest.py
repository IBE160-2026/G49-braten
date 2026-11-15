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
