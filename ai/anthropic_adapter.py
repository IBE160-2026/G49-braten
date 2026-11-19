"""The Anthropic adapter (FR-21, AD-2): Claude Haiku 5.5 with structured output.

Only `ai` imports `anthropic` (AD-1). The client is built lazily from `settings.ANTHROPIC_API_KEY`,
and the Key goes nowhere else: never into a log line, an exception message or a page.

Request (AD-2): structured output with the `ai.schemas` response model's JSON schema as
`output_config.format` (exactly what `messages.parse(output_format=...)` sends), plus
`output_config.effort` per operation; no sampling parameters, no Citations or PDF blocks, no
prefill, not streamed.

Response (AD-2): the stop reason is read before anything is parsed, and only `end_turn` is
validated against the model. `messages.parse` cannot be used for this: it validates every text
block inside the SDK call, so a refused or truncated reply (which need not match the schema) would
surface as a pydantic error with no stop reason, and `Refused`/`Truncated` could never be told apart
from `InvalidFormat`. Provider errors become the typed `ai.errors` the callers store as a
`FailureReason`.
"""

import logging
import time
from functools import cache

import anthropic
import pydantic
from django.conf import settings

from ai import prompts
from ai.errors import (
    AIError,
    InvalidFormat,
    KeyRejected,
    ProviderUnavailable,
    RateLimited,
    Refused,
    Truncated,
)
from ai.schemas import (
    GenerateRequest,
    GradeRequest,
    GradeResponse,
    StudyMaterial,
    SummaryRequest,
    SummaryResponse,
)

MODEL = "claude-haiku-5-5"
# Leaves room for thinking before the structured answer (AD-2 `MAX_OUTPUT_TOKENS`).
MAX_OUTPUT_TOKENS = 16000

# Grading stays under NFR-3's 15 s: one try, 12 s (AD-2). Generation and Summary get one retry,
# so a transient 429/5xx does not cost the Student a Generation call on «Prøv igjen».
# The retry is ours, not the SDK's: the SDK also retries a timeout, and a timed-out request may
# already have run (and been billed), so a timeout is never retried (Author's decision 2026-11-19).
GRADE_TIMEOUT = 12.0
GRADE_RETRIES = 0
GENERATE_TIMEOUT = 110.0
GENERATE_RETRIES = 1
RETRY_DELAY = 2.0

# The SDK and its HTTP client log request details at DEBUG/INFO (with `ANTHROPIC_LOG=debug`, whole
# request bodies, i.e. Source text). They are held at WARNING whatever the environment says (NFR-4).
SDK_LOGGERS = ("anthropic", "httpx", "httpx2", "httpcore")
for _name in SDK_LOGGERS:
    logging.getLogger(_name).setLevel(logging.WARNING)

EFFORT_GRADE = "low"
EFFORT_GENERATE = "medium"

TRUNCATED_STOPS = {"max_tokens", "model_context_window_exceeded"}


def _client() -> anthropic.Anthropic:
    """A client for the configured Key; built per call, so no Key outlives a settings change."""
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def generate(request: GenerateRequest) -> StudyMaterial:
    return _parse(
        StudyMaterial,
        system=prompts.GENERATE_SYSTEM,
        user=prompts.generate_user(request),
        effort=EFFORT_GENERATE,
        timeout=GENERATE_TIMEOUT,
        max_retries=GENERATE_RETRIES,
    )


def summary(request: SummaryRequest) -> SummaryResponse:
    return _parse(
        SummaryResponse,
        system=prompts.SUMMARY_SYSTEM,
        user=prompts.summary_user(request),
        effort=EFFORT_GENERATE,
        timeout=GENERATE_TIMEOUT,
        max_retries=GENERATE_RETRIES,
    )


def grade(request: GradeRequest) -> GradeResponse:
    return _parse(
        GradeResponse,
        system=prompts.GRADE_SYSTEM,
        user=prompts.grade_user(request),
        effort=EFFORT_GRADE,
        timeout=GRADE_TIMEOUT,
        max_retries=GRADE_RETRIES,
    )


@cache
def output_format(model: type[pydantic.BaseModel]) -> dict:
    """The `output_config.format` for a response model, as the SDK's `messages.parse` builds it."""
    return {"type": "json_schema", "schema": anthropic.transform_schema(model.model_json_schema())}


def _parse(model, *, system: str, user: str, effort: str, timeout: float, max_retries: int):
    for attempt in range(max_retries + 1):
        try:
            client = _client().with_options(timeout=timeout, max_retries=0)
            message = client.messages.create(
                model=MODEL,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"format": output_format(model), "effort": effort},
            )
        except anthropic.APIError as error:
            if attempt < max_retries and _retryable(error):
                time.sleep(RETRY_DELAY)
                continue
            raise _mapped(error) from None
        except anthropic.AnthropicError as error:
            # Any other SDK error (client or header setup): the app keeps running.
            raise ProviderUnavailable(type(error).__name__) from None
        return _read(message, model)
    raise AssertionError("unreachable")  # pragma: no cover


def _retryable(error: anthropic.APIError) -> bool:
    """Errors where nothing ran, so a retry cannot be billed twice: 429, 5xx/529, no connection.

    A timeout is not retried: the request may have run to the end on the provider's side.
    """
    if isinstance(error, anthropic.APITimeoutError):
        return False
    if isinstance(error, anthropic.APIConnectionError):
        return True
    return isinstance(error, (anthropic.RateLimitError, anthropic.InternalServerError))


def _mapped(error: anthropic.APIError) -> AIError:
    """The typed gateway error for a provider error. The detail is the class name only (no Key)."""
    detail = type(error).__name__
    if isinstance(error, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)):
        return KeyRejected(detail)
    if isinstance(error, anthropic.RateLimitError):
        return RateLimited(detail)
    # APITimeoutError, APIConnectionError, 5xx/529 and every other APIError.
    return ProviderUnavailable(detail)


def _read(message, model):
    """The validated model when the reply ended normally (AD-2), else the typed error."""
    stop = message.stop_reason
    if stop == "refusal":
        raise Refused()
    if stop in TRUNCATED_STOPS:
        raise Truncated()
    if stop != "end_turn":
        raise InvalidFormat(f"stop_reason={stop}")
    text = next((block.text for block in message.content if block.type == "text"), None)
    if text is None:
        raise InvalidFormat("no text block")
    try:
        return model.model_validate_json(text)
    except pydantic.ValidationError:
        # The detail names the model only; the reply text may quote the Source.
        raise InvalidFormat(f"{model.__name__} did not validate") from None
