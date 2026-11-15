"""The typed upload error (Conventions: "Errors to the Student").

`IngestError(code, **params)` carries a `code` from core.messages and the raw numbers behind
it; `message` formats them the Norwegian way.
"""

import math

from core.messages import MESSAGES

MEGABYTE = 1024 * 1024


def thousands(n: int) -> str:
    """180000 -> «180 000»."""
    return f"{n:,}".replace(",", " ")


def megabytes(size_bytes: int) -> str:
    """Rounded up to one decimal, with a decimal comma, so a file over the limit never reads as the limit."""
    tenths = math.ceil(size_bytes * 10 / MEGABYTE)
    whole, rest = divmod(tenths, 10)
    return f"{whole},{rest}" if rest else str(whole)


class IngestError(Exception):
    """An upload `ingestion.services.ingest()` refuses. Nothing is saved when it is raised."""

    def __init__(self, code: str, **params):
        assert code in MESSAGES, code
        self.code = code
        self.params = params
        super().__init__(code)

    @property
    def message(self) -> str:
        # Byte counts read as megabytes; every other number as a count.
        fmt = megabytes if self.code == "file_too_large" else thousands
        return MESSAGES[self.code].format(**{k: fmt(v) for k, v in self.params.items()})
