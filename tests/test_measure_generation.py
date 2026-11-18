"""OQ-2 tool `scripts/measure_generation.py`: runs on a fake client, so no socket and no cost."""

from types import SimpleNamespace

import pytest

from ai import anthropic_adapter, mock
from scripts import measure_generation as tool

KEY = "sk-ant-test-measure-0000"


class FakeRaw:
    def __init__(self, text, stop_reason="end_turn"):
        self.headers = {"anthropic-ratelimit-input-tokens-limit": "50000"}
        self._message = SimpleNamespace(
            stop_reason=stop_reason,
            content=[SimpleNamespace(type="text", text=text)],
            usage=SimpleNamespace(input_tokens=12345, output_tokens=6789),
        )

    def parse(self):
        return self._message


class FakeClient:
    def __init__(self, raw):
        self.raw = raw
        self.calls = []
        self.options = None
        self.messages = SimpleNamespace(with_raw_response=SimpleNamespace(create=self._create))

    def with_options(self, **options):
        self.options = options
        return self

    def _create(self, **body):
        self.calls.append(body)
        return self.raw


@pytest.fixture
def fake(monkeypatch, settings):
    settings.ANTHROPIC_API_KEY = KEY
    monkeypatch.setattr(tool, "setup_django", lambda: None)
    client = FakeClient(FakeRaw(mock.STUDY_MATERIAL_FILE.read_text(encoding="utf-8")))
    monkeypatch.setattr(anthropic_adapter, "_client", lambda: client)
    return client


def test_oq2_sends_the_apps_generation_request_once_without_retry(fake, capsys):
    assert tool.main([str(mock.SAMPLE_PATH), "--yes"]) == 0
    assert len(fake.calls) == 1
    body = fake.calls[0]
    assert body["model"] == anthropic_adapter.MODEL
    assert body["output_config"]["effort"] == anthropic_adapter.EFFORT_GENERATE
    assert "[[L1]]" in body["messages"][0]["content"]
    assert fake.options == {"timeout": tool.MEASURE_TIMEOUT, "max_retries": 0}
    out = capsys.readouterr().out
    assert "normalisering.pdf" in out and "12345" in out and "| ok |" in out
    assert "anthropic-ratelimit-input-tokens-limit`: 50000" in out
    assert KEY not in out


def test_oq2_the_reference_check_runs_on_the_reply(fake, capsys):
    tool.main([str(mock.SAMPLE_PATH), "--yes"])
    row = next(line for line in capsys.readouterr().out.splitlines() if line.startswith("| normalisering.pdf"))
    # The recording plants exactly one wrong Reference (AD-4), so the real check removes one item.
    assert row.rstrip(" |").endswith("| 1")


def test_oq2_a_truncated_reply_is_named(fake, capsys):
    fake.raw = FakeRaw("{", stop_reason="max_tokens")
    tool.main([str(mock.SAMPLE_PATH), "--yes"])
    assert "truncated (stop_reason=max_tokens)" in capsys.readouterr().out


def test_oq2_without_a_key_nothing_is_sent(fake, settings):
    settings.ANTHROPIC_API_KEY = ""
    assert tool.main([str(mock.SAMPLE_PATH), "--yes"]) == 2
    assert fake.calls == []


def test_oq2_declining_the_cost_prompt_sends_nothing(fake, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert tool.main([str(mock.SAMPLE_PATH)]) == 1
    assert fake.calls == []


def test_oq2_report_is_appended(fake, monkeypatch, tmp_path):
    report = tmp_path / "oq2.md"
    monkeypatch.setattr(tool, "REPORT", report)
    monkeypatch.setattr(tool, "ROOT", tmp_path)
    tool.main([str(mock.SAMPLE_PATH), "--yes", "--report"])
    tool.main([str(mock.SAMPLE_PATH), "--yes", "--report"])
    text = report.read_text(encoding="utf-8")
    assert text.count("# OQ-2: Real-mode generation time") == 1
    assert text.count("### ") == 2


def test_oq2_verdict_compares_with_the_app_limits():
    assert tool.verdict(50, 110) == "ok"
    assert tool.verdict(95, 110) == "near timeout"
    assert tool.verdict(120, 110) == "over 110 s timeout"
    assert tool.verdict(160, 110) == "over 150 s floor"
