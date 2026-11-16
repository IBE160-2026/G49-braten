"""Render sample/source.md to the committed Sample document, sample/normalisering.pdf (CAP-12).

One slide per PDF page: a `# Title` line starts a slide; every other line is drawn as is, with a
leading «- » turned into a bullet; blank lines add space. Helvetica in WinAnsi (cp1252), so æøå,
«», – and • come through pypdf's text extraction unchanged.

Run from the repository root:  uv run python sample/build_sample.py

After a change to source.md, re-check the Mock recordings in ai/mock/ (their quotes are copied from
the extracted page text); `uv run pytest tests/test_mock_recordings.py` tells you which ones broke.
SAMPLE_SHA256 is computed from the PDF at import, so it needs no update.
"""

import sys
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source.md"
OUTPUT = HERE / "normalisering.pdf"

# A4 landscape, in points.
WIDTH, HEIGHT = 842, 595
MARGIN = 48
TITLE_SIZE, BODY_SIZE = 24, 14
TITLE_Y, BODY_TOP, LINE_GAP, BLANK_GAP = 530, 478, 22, 12
# Helvetica at 14 pt averages under 7.5 pt per character, so this keeps a line inside the margins.
MAX_LINE_CHARS = 100
BULLET = "• "


def parse(text: str) -> list[tuple[str, list[str]]]:
    slides: list[tuple[str, list[str]]] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            slides.append((line[2:].strip(), []))
        elif slides:
            slides[-1][1].append(BULLET + line[2:] if line.startswith("- ") else line)
        elif line:
            raise SystemExit(f"Text before the first slide title: {line!r}")
    for title, lines in slides:
        while lines and not lines[-1]:
            lines.pop()
        for line in [title, *lines]:
            if len(line) > MAX_LINE_CHARS:
                raise SystemExit(f"Line longer than {MAX_LINE_CHARS} characters: {line!r}")
            line.encode("cp1252")  # refuses a character Helvetica/WinAnsi cannot draw
    return slides


def _escape(line: str) -> bytes:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("cp1252")


def _font(writer: PdfWriter, base: str):
    return writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject(base),
                NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
            }
        )
    )


def render(slides: list[tuple[str, list[str]]]) -> bytes:
    writer = PdfWriter()
    regular, bold = _font(writer, "/Helvetica"), _font(writer, "/Helvetica-Bold")
    for title, lines in slides:
        page = writer.add_blank_page(WIDTH, HEIGHT)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): regular, NameObject("/F2"): bold})}
        )
        ops = b"BT /F2 %d Tf %d %d Td (" % (TITLE_SIZE, MARGIN, TITLE_Y) + _escape(title) + b") Tj ET\n"
        y = BODY_TOP
        for line in lines:
            if not line:
                y -= BLANK_GAP
                continue
            if y < MARGIN:
                raise SystemExit(f"Slide {title!r} runs off the page.")
            ops += b"BT /F1 %d Tf %d %d Td (" % (BODY_SIZE, MARGIN, y) + _escape(line) + b") Tj ET\n"
            y -= LINE_GAP
        contents = DecodedStreamObject()
        contents.set_data(ops)
        page[NameObject("/Contents")] = writer._add_object(contents)
    writer.add_metadata({"/Title": "Databaser: normalisering", "/Author": "AI Study Buddy (CC0 1.0)"})
    with open(OUTPUT, "wb") as handle:
        writer.write(handle)
    return OUTPUT.read_bytes()


def main() -> None:
    slides = parse(SOURCE.read_text(encoding="utf-8"))
    data = render(slides)
    print(f"Wrote {OUTPUT.relative_to(HERE.parent)}: {len(slides)} pages, {len(data)} bytes", file=sys.stderr)


if __name__ == "__main__":
    main()
