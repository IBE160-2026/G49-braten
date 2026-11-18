"""FR-21, AD-2 (story 10): the Anthropic adapter, through the real SDK on a fake HTTP transport.

No socket is opened (`--disable-socket`): the client gets an `httpx2.MockTransport` that answers
like the Messages API, so the request body the SDK builds is checked as sent.
"""

import json
import logging

import anthropic
import httpx2
import pytest

from ai import anthropic_adapter, errors, gateway, markers, mock, prompts
from ai.schemas import GenerateRequest, GradeRequest, GradeResponse, Location, StudyMaterial, SummaryRequest

KEY = "sk-ant-api03-story10-secret-never-shown"
SAMPLING = {"temperature", "top_p", "top_k"}

LOCATIONS = [
    Location(index=1, text="Normalisering fjerner redundans i tabeller."),
    Location(index=2, text="   "),
    Location(index=3, text="Tredje normalform krever at ingen ikke-nøkkelattributter er transitivt avhengige."),
]


def generate_request(detail_level="medium") -> GenerateRequest:
    return GenerateRequest(
        source_id=1, content_sha256="0" * 64, language="", detail_level=detail_level, locations=LOCATIONS
    )


def summary_request() -> SummaryRequest:
    return SummaryRequest(source_id=1, content_sha256="0" * 64, language="nb", detail_level="short", locations=LOCATIONS)


def grade_request() -> GradeRequest:
    return GradeRequest(
        prompt="Hva gjør normalisering?",
        model_answer="Den fjerner redundans.",
        answer="Den fjerner dobbeltlagring.",
        source_text="Normalisering fjerner redundans i tabeller.",
        language="nb",
    )


def reply(payload, *, stop_reason="end_turn", text=None, thinking=True) -> dict:
    """A Messages API reply body: an optional thinking block, then the text block."""
    content = []
    if thinking:
        content.append({"type": "thinking", "thinking": "…", "signature": "sig"})
    content.append({"type": "text", "text": text if text is not None else json.dumps(payload)})
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": anthropic_adapter.MODEL,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }


def material_payload() -> dict:
    return mock.study_material("medium").model_dump()


class FakeAPI:
    """Answers every request with the next item: a reply dict, an `httpx2.Response`, or an exception."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.requests: list[httpx2.Request] = []
        self.clients: list[anthropic.Anthropic] = []

    def handler(self, request: httpx2.Request):
        self.requests.append(request)
        answer = self.answers.pop(0) if len(self.answers) > 1 else self.answers[0]
        if isinstance(answer, Exception):
            raise answer
        if isinstance(answer, httpx2.Response):
            return answer
        return httpx2.Response(200, json=answer)

    def client(self) -> anthropic.Anthropic:
        client = anthropic.Anthropic(
            api_key=KEY, http_client=httpx2.Client(transport=httpx2.MockTransport(self.handler))
        )
        self.clients.append(client)
        return client

    @property
    def body(self) -> dict:
        return json.loads(self.requests[-1].content)


@pytest.fixture
def api(monkeypatch):
    def install(*answers) -> FakeAPI:
        fake = FakeAPI(*answers)
        monkeypatch.setattr(anthropic_adapter, "_client", fake.client)
        return fake

    return install


def error_response(status: int, error_type: str) -> httpx2.Response:
    # retry-after-ms keeps the one generation retry from sleeping.
    return httpx2.Response(
        status,
        json={"type": "error", "error": {"type": error_type, "message": "nope"}},
        headers={"retry-after-ms": "1"},
    )


# ---- Request shape -----------------------------------------------------------------------


def test_fr21_generate_request_shape(api):
    fake = api(reply(material_payload()))
    material = anthropic_adapter.generate(generate_request())
    assert isinstance(material, StudyMaterial)
    body = fake.body
    assert fake.requests[-1].url.path == "/v1/messages"
    assert body["model"] == "claude-haiku-5-5"
    assert body["max_tokens"] == 16000
    assert body["output_config"]["effort"] == "medium"
    assert body["output_config"]["format"] == anthropic_adapter.output_format(StudyMaterial)
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert set(body["output_config"]["format"]["schema"]["properties"]) == set(StudyMaterial.model_fields)
    assert not SAMPLING & set(body)
    assert "stream" not in body or body["stream"] is False
    assert "thinking" not in body and "tools" not in body
    # One user turn, no assistant prefill, plain text only (no PDF or document blocks, no Citations).
    assert [m["role"] for m in body["messages"]] == ["user"]
    user = body["messages"][0]["content"]
    assert isinstance(user, str)
    assert markers.marked_text(LOCATIONS) in user
    assert "[[L1]]" in user and "[[L3]]" in user and "[[L2]]" not in user
    assert "citations" not in json.dumps(body)
    assert body["system"] == prompts.GENERATE_SYSTEM


def test_fr7_generation_prompt_asks_for_the_counts_and_rules():
    system = prompts.GENERATE_SYSTEM
    for phrase in (
        "at least 5 Key concepts",
        "at least 10 Flashcards",
        "at least 10 Questions, with both kinds",
        "exactly 4 `options`",
        "at most two sentences",
        "one sentence",
        "never contains the correct option",
        "verbatim",
        "main language of the Source",
    ):
        assert phrase in system, phrase
    assert "medium" in prompts.generate_user(generate_request())
    assert prompts.DETAIL_LEVELS["detailed"] in prompts.generate_user(generate_request("detailed"))


@pytest.mark.parametrize("build", [generate_request, summary_request, grade_request])
def test_fr6_a_stored_language_is_named_and_an_empty_one_is_detected(build):
    render = {
        GenerateRequest: prompts.generate_user,
        SummaryRequest: prompts.summary_user,
        GradeRequest: prompts.grade_user,
    }
    request = build()
    user = render[type(request)]
    named = user(request.model_copy(update={"language": "nb"}))
    assert "Write in the language with ISO 639-1 code `nb`." in named
    assert "ISO 639-1" not in user(request.model_copy(update={"language": ""}))


def test_fr7_summary_request_shape(api):
    fake = api(reply({"summary": "Kort."}))
    assert anthropic_adapter.summary(summary_request()).summary == "Kort."
    body = fake.body
    assert body["output_config"]["effort"] == "medium"
    assert set(body["output_config"]["format"]["schema"]["properties"]) == {"summary"}
    assert prompts.DETAIL_LEVELS["short"] in body["messages"][0]["content"]
    assert markers.marked_text(LOCATIONS) in body["messages"][0]["content"]
    assert not SAMPLING & set(body)


def test_fr12_grade_request_shape(api):
    fake = api(reply({"grade": "Partial", "explanation": "Delvis."}))
    response = anthropic_adapter.grade(grade_request())
    assert response == GradeResponse(grade="partial", explanation="Delvis.")
    body = fake.body
    assert body["output_config"]["effort"] == "low"
    assert set(body["output_config"]["format"]["schema"]["properties"]) == {"grade", "explanation"}
    user = body["messages"][0]["content"]
    for part in ("Hva gjør normalisering?", "Den fjerner redundans.", "Den fjerner dobbeltlagring.", "i tabeller."):
        assert part in user
    assert "main language of the Source" in body["system"]
    assert not SAMPLING & set(body)


def test_nfr3_timeouts_and_retries_per_operation(api, monkeypatch):
    fake = api(reply({"grade": "correct", "explanation": "Ja."}))
    seen = []
    original = anthropic.Anthropic.with_options

    def spy(self, **kwargs):
        seen.append(kwargs)
        return original(self, **kwargs)

    monkeypatch.setattr(anthropic.Anthropic, "with_options", spy)
    anthropic_adapter.grade(grade_request())
    fake.answers = [reply(material_payload())]
    anthropic_adapter.generate(generate_request())
    fake.answers = [reply({"summary": "Kort."})]
    anthropic_adapter.summary(summary_request())
    assert seen == [
        {"timeout": 12.0, "max_retries": 0},
        {"timeout": 110.0, "max_retries": 1},
        {"timeout": 110.0, "max_retries": 1},
    ]


def test_fr21_the_key_is_sent_only_in_the_auth_header(api):
    fake = api(reply({"summary": "Kort."}))
    anthropic_adapter.summary(summary_request())
    request = fake.requests[-1]
    carrying = [name for name, value in request.headers.items() if KEY in value]
    assert carrying in (["authorization"], ["x-api-key"])
    assert KEY not in request.content.decode()
    assert KEY not in str(request.url)


def test_fr21_the_client_is_built_from_settings(settings, monkeypatch):
    monkeypatch.undo()  # the conftest guard; nothing is sent here
    settings.ANTHROPIC_API_KEY = KEY
    client = anthropic_adapter._client()
    assert isinstance(client, anthropic.Anthropic)
    assert client.api_key == KEY


# ---- Response (AD-2) -----------------------------------------------------------------------


def test_fr21_reply_without_thinking_block_parses(api):
    api(reply({"summary": "Kort."}, thinking=False))
    assert anthropic_adapter.summary(summary_request()).summary == "Kort."


@pytest.mark.parametrize(
    ("stop_reason", "error"),
    [
        ("refusal", errors.Refused),
        ("max_tokens", errors.Truncated),
        ("model_context_window_exceeded", errors.Truncated),
        ("pause_turn", errors.InvalidFormat),
        ("tool_use", errors.InvalidFormat),
        ("stop_sequence", errors.InvalidFormat),
    ],
)
def test_ad2_every_stop_reason_other_than_end_turn_is_an_error(api, stop_reason, error):
    # Even a reply that would validate is not parsed unless it ended normally.
    api(reply({"summary": "Kort."}, stop_reason=stop_reason))
    with pytest.raises(error):
        anthropic_adapter.summary(summary_request())


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_ad2_a_refused_or_truncated_reply_that_is_not_json_keeps_its_stop_reason(api, stop_reason):
    api(reply(None, stop_reason=stop_reason, text='{"summary": "Avbr'))
    with pytest.raises(errors.Refused if stop_reason == "refusal" else errors.Truncated):
        anthropic_adapter.summary(summary_request())


@pytest.mark.parametrize(
    "text",
    ["not json", '{"summary": 3}', '{"grade": "maybe", "explanation": "x"}', '{"language": "nb"}'],
)
def test_ad2_bad_json_or_schema_failure_is_invalid_format(api, text):
    api(reply(None, text=text))
    with pytest.raises(errors.InvalidFormat):
        anthropic_adapter.generate(generate_request())


def test_ad2_a_reply_without_a_text_block_is_invalid_format(api):
    body = reply({"summary": "x"})
    body["content"] = [{"type": "thinking", "thinking": "…", "signature": "sig"}]
    api(body)
    with pytest.raises(errors.InvalidFormat):
        anthropic_adapter.summary(summary_request())


# ---- Errors --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "error_type", "error"),
    [
        (401, "authentication_error", errors.KeyRejected),
        (403, "permission_error", errors.KeyRejected),
        (429, "rate_limit_error", errors.RateLimited),
        (500, "api_error", errors.ProviderUnavailable),
        (503, "api_error", errors.ProviderUnavailable),
        (529, "overloaded_error", errors.ProviderUnavailable),
        (400, "invalid_request_error", errors.ProviderUnavailable),
        (404, "not_found_error", errors.ProviderUnavailable),
    ],
)
def test_fr21_provider_errors_are_mapped(api, status, error_type, error):
    api(error_response(status, error_type))
    with pytest.raises(error) as caught:
        anthropic_adapter.grade(grade_request())
    assert KEY not in str(caught.value)
    assert caught.value.__cause__ is None


def test_fr21_any_other_sdk_error_is_provider_unavailable(monkeypatch):
    class Broken:
        def with_options(self, **kwargs):
            raise anthropic.AnthropicError(f"bad header {KEY}")

    monkeypatch.setattr(anthropic_adapter, "_client", Broken)
    with pytest.raises(errors.ProviderUnavailable) as caught:
        anthropic_adapter.generate(generate_request())
    assert KEY not in str(caught.value) and caught.value.__cause__ is None


@pytest.mark.parametrize(
    "exception",
    [httpx2.ReadTimeout("slow"), httpx2.ConnectError("down")],
    ids=["timeout", "connection"],
)
def test_nfr3_timeouts_and_connection_errors_are_provider_unavailable(api, exception):
    fake = api(exception)
    with pytest.raises(errors.ProviderUnavailable):
        anthropic_adapter.grade(grade_request())
    # Grading never retries (NFR-3: the whole call stays under 15 s).
    assert len(fake.requests) == 1


def test_fr21_generation_retries_once_after_a_transient_error(api):
    fake = api(error_response(529, "overloaded_error"), reply(material_payload()))
    assert isinstance(anthropic_adapter.generate(generate_request()), StudyMaterial)
    assert len(fake.requests) == 2


def test_fr21_generation_gives_up_after_one_retry(api):
    fake = api(error_response(429, "rate_limit_error"))
    with pytest.raises(errors.RateLimited):
        anthropic_adapter.generate(generate_request())
    assert len(fake.requests) == 2


# ---- The Key never shows (AD-2, NFR-4) ------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_nfr4_the_key_never_appears_in_logs(api, student, settings, caplog):
    settings.AI_PROVIDER = "anthropic"
    settings.ANTHROPIC_API_KEY = KEY
    from accounts.services import accept_privacy

    ida = student("ida@example.no")
    accept_privacy(ida)
    answers = [
        reply(material_payload()),
        error_response(401, "authentication_error"),
        reply(None, text="not json"),
        error_response(500, "api_error"),
    ]
    with caplog.at_level(logging.DEBUG):
        for answer in answers:
            api(answer)
            try:
                gateway.grade_free_text(ida, grade_request())
            except errors.AIError:
                pass
            try:
                gateway.generate_study_material(ida, generate_request())
            except errors.AIError:
                pass
    logged = "\n".join(f"{r.getMessage()} {r.exc_text or ''} {r.args}" for r in caplog.records)
    assert logged  # the gateway and the SDK did log
    assert KEY not in logged
    assert "Normalisering fjerner redundans" not in "\n".join(
        r.getMessage() for r in caplog.records if r.name == "ai.gateway"
    )
