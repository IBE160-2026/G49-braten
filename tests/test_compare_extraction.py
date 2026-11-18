"""OQ-1 tool `scripts/compare_extraction.py`, run on the Sample document (local only, no network)."""

import pytest

from ai import mock
from ingestion import extract
from scripts import compare_extraction as tool


@pytest.fixture(autouse=True)
def no_setup(monkeypatch):
    monkeypatch.setattr(tool, "setup_django", lambda: None)


def test_oq1_compares_plain_and_layout_on_every_deck(capsys):
    assert tool.main([str(mock.SAMPLE_PATH)]) == 0
    out = capsys.readouterr().out
    assert "| normalisering.pdf | pypdf-plain | 20 |" in out
    assert "| normalisering.pdf | pypdf-layout | 20 |" in out


def test_oq1_plain_is_the_apps_own_extraction():
    row, texts = tool.measure(mock.SAMPLE_PATH, "pypdf-plain", tool.pypdf_plain)
    assert texts == extract.pdf_pages(mock.SAMPLE_PATH.read_bytes())
    assert row.limits() == "ok" and row.mojibake == 0 and row.empty_pages == 0


def test_oq1_mojibake_and_padding_are_counted(tmp_path):
    deck = tmp_path / "x.pdf"
    deck.write_bytes(b"")
    row, _ = tool.measure(deck, "fake", lambda data: ["NÃ¸kkel   og   Ã¥r", "Nøkkel og år"])
    assert row.mojibake == 2
    assert row.norwegian == 2
    assert row.padded_lines_pct == 50


def test_oq1_an_unreadable_file_is_a_row_not_a_crash(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    row, texts = tool.measure(bad, "pypdf-plain", tool.pypdf_plain)
    assert texts == [] and row.error == "unsupported_type"
    assert "failed: unsupported_type" in tool.table([row])


def test_oq1_show_page_prints_every_method(capsys):
    tool.main([str(mock.SAMPLE_PATH), "--show-page", "2"])
    out = capsys.readouterr().out
    assert "page 2" in out and "[pypdf-plain]" in out and "[pypdf-layout]" in out


def test_oq1_report_appends_one_measurements_section(monkeypatch, tmp_path):
    report = tmp_path / "oq1.md"
    report.write_text("# OQ-1\n", encoding="utf-8")
    monkeypatch.setattr(tool, "REPORT", report)
    monkeypatch.setattr(tool, "ROOT", tmp_path)
    tool.main([str(mock.SAMPLE_PATH), "--report"])
    tool.main([str(mock.SAMPLE_PATH), "--report"])
    text = report.read_text(encoding="utf-8")
    assert text.count("## Measurements") == 1 and text.count("### ") == 2


def test_oq1_a_missing_file_stops_before_anything_runs(capsys):
    assert tool.main(["/no/such/deck.pdf"]) == 2
