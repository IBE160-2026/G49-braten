"""Write sample/for_mange_sider.pdf: 51 pages with one line of text each (SM-2 check 4, FR-3).

The Examiner uploads it under «Legg til kilde» to see an upload over the 50-page limit refused.
Reuses the Sample document's fonts and page size.

Run from the repository root:  uv run python sample/build_too_many_pages.py
"""

import sys

from build_sample import (
    BODY_SIZE,
    BODY_TOP,
    HEIGHT,
    HERE,
    MARGIN,
    WIDTH,
    _escape,
    _font,
)
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

OUTPUT = HERE / "for_mange_sider.pdf"
PAGES = 51  # one over FR-3's limit of 50


def main() -> None:
    writer = PdfWriter()
    regular = _font(writer, "/Helvetica")
    for number in range(1, PAGES + 1):
        page = writer.add_blank_page(WIDTH, HEIGHT)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): regular})}
        )
        line = f"Side {number} av {PAGES}: denne filen har én side for mye."
        contents = DecodedStreamObject()
        contents.set_data(b"BT /F1 %d Tf %d %d Td (" % (BODY_SIZE, MARGIN, BODY_TOP) + _escape(line) + b") Tj ET\n")
        page[NameObject("/Contents")] = writer._add_object(contents)
    writer.add_metadata({"/Title": "For mange sider", "/Author": "AI Study Buddy (CC0 1.0)"})
    with open(OUTPUT, "wb") as handle:
        writer.write(handle)
    print(f"Wrote {OUTPUT.relative_to(HERE.parent)}: {PAGES} pages, {OUTPUT.stat().st_size} bytes", file=sys.stderr)


if __name__ == "__main__":
    main()
