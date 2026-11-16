"""Typed gateway errors (AD-2). Each `code` is a `courses.FailureReason` value.

`ai` may not import `courses` (AD-1), so the codes are repeated here; a test checks that they and
`timed_out` (set by AD-5, not by an error) are exactly `FailureReason.values`.
"""

from core.messages import MESSAGES


class AIError(Exception):
    """Base of every gateway error. `message` is the Norwegian text, when there is one yet."""

    code: str = ""

    def __init__(self, detail: str = ""):
        super().__init__(detail or self.code)

    @property
    def message(self) -> str:
        return MESSAGES.get(self.code, "")


class NeedsKey(AIError):
    """Mock mode was asked for something other than the Sample document (FR-20, AD-3 step 1)."""

    code = "needs_key"


class PrivacyNotAccepted(AIError):
    code = "privacy_not_accepted"


class DailyLimitReached(AIError):
    """The Student has used all of today's Generation calls (NFR-7, AD-3)."""

    code = "daily_limit"


class RateLimited(AIError):
    code = "rate_limited"


class Refused(AIError):
    code = "refused"


class Truncated(AIError):
    code = "truncated"


class InvalidFormat(AIError):
    code = "invalid_format"


class KeyRejected(AIError):
    code = "key_rejected"


class ProviderUnavailable(AIError):
    code = "provider_unavailable"


ERRORS: tuple[type[AIError], ...] = (
    NeedsKey,
    PrivacyNotAccepted,
    DailyLimitReached,
    RateLimited,
    Refused,
    Truncated,
    InvalidFormat,
    KeyRejected,
    ProviderUnavailable,
)
