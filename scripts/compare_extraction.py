"""OQ-1: compare PDF text extraction on the Author's own slide decks (Author's tool, not app code).

Runs each PDF through:
- `pypdf-plain`: the app's own path, `ingestion.extract.pdf_pages` (pypdf `extract_text()`);
- `pypdf-layout`: pypdf `extract_text(extraction_mode="layout")`;
- `pdfplumber`: only when it is installed. It is not a dependency of the app, so run with
  `uv run --with pdfplumber python scripts/compare_extraction.py …` to include it.

For each method it reports what decides the OQ-1 choice: how much text comes out, empty pages
(scanned slides), whether Æ/Ø/Å survive or turn into mojibake, padding that bloats prompts and
breaks verbatim quotes (runs of 3+ spaces), the time taken, and whether the deck passes the app's
`MIN_TEXT_CHARS` and `MAX_CHARS`. `--show-page N` prints page N from every method side by side for
an eyeball check of bullet lists, tables and two-column slides.

Nothing leaves the machine and nothing is stored. Usage:

    uv run --with pdfplumber python scripts/compare_extraction.py deck1.pdf deck2.pdf deck3.pdf --report
    uv run python scripts/compare_extraction.py deck.pdf --show-page 4

`--report` appends the tables to docs/quality/oq1-pdf-extraction.md under «Measurements».
"""

import argparse
import io
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "quality" / "oq1-pdf-extraction.md"
NORWEGIAN = set("æøåÆØÅ")
# What Æ/Ø/Å (and other UTF-8 letters) look like when decoded as Latin-1, plus the replacement char.
MOJIBAKE = re.compile(r"Ã[\x80-\xbf¦¸¥†˜…]|�")
PADDING = re.compile(r" {3,}")
PREVIEW_CHARS = 600


def setup_django() -> None:
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()


def pypdf_plain(data: bytes) -> list[str]:
    from ingestion import extract

    return extract.pdf_pages(data)


def pypdf_layout(data: bytes) -> list[str]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        reader.decrypt("")
    return [(page.extract_text(extraction_mode="layout") or "") for page in reader.pages]


def pdfplumber_text(data: bytes) -> list[str]:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return [(page.extract_text() or "") for page in pdf.pages]


def methods() -> dict:
    found = {"pypdf-plain": pypdf_plain, "pypdf-layout": pypdf_layout}
    try:
        import pdfplumber  # noqa: F401
    except ImportError:
        pass
    else:
        found["pdfplumber"] = pdfplumber_text
    return found


@dataclass
class Row:
    file: str
    method: str
    pages: int = 0
    chars: int = 0
    non_ws: int = 0
    empty_pages: int = 0
    norwegian: int = 0
    mojibake: int = 0
    padded_lines_pct: float = 0.0
    seconds: float = 0.0
    error: str = ""

    def limits(self) -> str:
        from ingestion import extract

        if self.error:
            return "–"
        if self.non_ws < extract.MIN_TEXT_CHARS:
            return f"under MIN_TEXT_CHARS ({extract.MIN_TEXT_CHARS})"
        if self.chars > extract.MAX_CHARS:
            return f"over MAX_CHARS ({extract.MAX_CHARS})"
        return "ok"


def measure(path: Path, name: str, extract_fn) -> tuple[Row, list[str]]:
    row = Row(path.name, name)
    started = time.perf_counter()
    try:
        texts = extract_fn(path.read_bytes())
    except Exception as error:  # a method that cannot read the file is a result, not a crash
        row.seconds = time.perf_counter() - started
        row.error = getattr(error, "code", "") or type(error).__name__
        return row, []
    row.seconds = time.perf_counter() - started
    joined = "\n".join(texts)
    lines = [line for line in joined.splitlines() if line.strip()]
    row.pages = len(texts)
    row.chars = len(joined)
    row.non_ws = sum(not ch.isspace() for ch in joined)
    row.empty_pages = sum(not text.strip() for text in texts)
    row.norwegian = sum(ch in NORWEGIAN for ch in joined)
    row.mojibake = len(MOJIBAKE.findall(joined))
    row.padded_lines_pct = 100 * sum(bool(PADDING.search(line)) for line in lines) / len(lines) if lines else 0.0
    return row, texts


def table(rows: list[Row]) -> str:
    out = [
        "| File | Method | Pages | Empty pages | Chars | Non-space chars | Æ/Ø/Å | Mojibake | Padded lines | Seconds | App limits |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r.error:
            out.append(f"| {r.file} | {r.method} | – | – | – | – | – | – | – | {r.seconds:.2f} | failed: {r.error} |")
            continue
        out.append(
            f"| {r.file} | {r.method} | {r.pages} | {r.empty_pages} | {r.chars} | {r.non_ws} | {r.norwegian} "
            f"| {r.mojibake} | {r.padded_lines_pct:.0f} % | {r.seconds:.2f} | {r.limits()} |"
        )
    return "\n".join(out)


def preview(path: Path, page: int, texts_by_method: dict[str, list[str]]) -> str:
    parts = [f"--- {path.name}, page {page} ---"]
    for method, texts in texts_by_method.items():
        text = texts[page - 1] if 0 < page <= len(texts) else "(no such page)"
        shown = text[:PREVIEW_CHARS] + (" …" if len(text) > PREVIEW_CHARS else "")
        parts.append(f"[{method}]\n{shown or '(empty)'}\n")
    return "\n".join(parts)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="OQ-1: compare PDF text extraction (local only).")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--show-page", type=int, metavar="N")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(argv)

    missing = [str(f) for f in args.files if not f.is_file()]
    if missing:
        print("Not found: " + ", ".join(missing))
        return 2
    setup_django()
    import pypdf

    found = methods()
    rows: list[Row] = []
    previews = []
    for path in args.files:
        texts_by_method = {}
        for name, extract_fn in found.items():
            row, texts = measure(path, name, extract_fn)
            rows.append(row)
            texts_by_method[name] = texts
        if args.show_page:
            previews.append(preview(path, args.show_page, texts_by_method))

    skipped = "" if "pdfplumber" in found else " pdfplumber not installed (run with `uv run --with pdfplumber`), so it is not compared."
    output = (
        f"### {date.today().isoformat()} · pypdf {pypdf.__version__} · {len(args.files)} deck(s)\n\n"
        f"{table(rows)}\n\n"
        "Empty pages: no text (likely scanned or image-only slides). Mojibake: broken Æ/Ø/Å or replacement "
        "characters. Padded lines: lines with 3+ spaces in a row, which bloat the prompt and break verbatim "
        f"quotes in the Reference check.{skipped}\n"
    )
    print(output)
    for block in previews:
        print(block)
    if args.report:
        text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
        with REPORT.open("a", encoding="utf-8") as handle:
            if "## Measurements" not in text:
                handle.write("\n## Measurements\n\nMeasured with `scripts/compare_extraction.py`.\n\n")
            handle.write(output + "\n")
        print(f"Appended to {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
