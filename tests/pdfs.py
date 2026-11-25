"""PDFs built in the test with pypdf's writer, so no binary fixtures live in git (story 4)."""

import io

from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject

IMAGE_ONLY = None  # a page entry that draws one image and no text


def _escape(line: str) -> bytes:
    return line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("cp1252")


def make_pdf(pages, *, password: str | None = None, owner_password: str | None = None) -> bytes:
    """One page per entry: a string is drawn as text lines (Helvetica, WinAnsi), IMAGE_ONLY as an image.

    `password` is the user password (needed to open); `owner_password` alone leaves it openable.
    """
    writer = PdfWriter()
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
            NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
        }
    )
    font_ref = writer._add_object(font)
    for text in pages:
        page = writer.add_blank_page(612, 792)
        resources = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})})
        if text is IMAGE_ONLY:
            image = DecodedStreamObject()
            image.update(
                {
                    NameObject("/Type"): NameObject("/XObject"),
                    NameObject("/Subtype"): NameObject("/Image"),
                    NameObject("/Width"): NumberObject(1),
                    NameObject("/Height"): NumberObject(1),
                    NameObject("/ColorSpace"): NameObject("/DeviceGray"),
                    NameObject("/BitsPerComponent"): NumberObject(8),
                }
            )
            image.set_data(b"\x80")
            resources[NameObject("/XObject")] = DictionaryObject({NameObject("/Im1"): writer._add_object(image)})
            ops = b"q 100 0 0 100 72 600 cm /Im1 Do Q"
        else:
            ops = b""
            for n, line in enumerate(text.split("\n")):
                ops += b"BT /F1 11 Tf 40 %d Td (" % (760 - 14 * n) + _escape(line) + b") Tj ET\n"
        page[NameObject("/Resources")] = resources
        contents = DecodedStreamObject()
        contents.set_data(ops)
        page[NameObject("/Contents")] = writer._add_object(contents)
    if password is not None or owner_password is not None:
        writer.encrypt(user_password=password or "", owner_password=owner_password)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def make_unmapped_font_pdf(line: str, pages: int = 2) -> bytes:
    """Pages whose font maps A–F to glyph names pypdf has no Unicode for, as a LaTeX Type 3 deck does.

    pypdf then extracts «/BW/CT/D2…» instead of letters (OQ-1, 05-Fordelinger_post.pdf).
    """
    writer = PdfWriter()
    encoding = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Encoding"),
            NameObject("/Differences"): ArrayObject(
                [NumberObject(65)] + [NameObject("/" + name) for name in ("BW", "CT", "D2", "CZ", "D9", "D1")]
            ),
        }
    )
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
            NameObject("/Encoding"): encoding,
        }
    )
    font_ref = writer._add_object(font)
    for _ in range(pages):
        page = writer.add_blank_page(612, 792)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
        )
        contents = DecodedStreamObject()
        contents.set_data(b"BT /F1 11 Tf 40 760 Td (" + _escape(line) + b") Tj ET\n")
        page[NameObject("/Contents")] = writer._add_object(contents)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


# About 150 non-whitespace characters per line set, so two text pages pass MIN_TEXT_CHARS.
LECTURE_TEXT = (
    "Normalisering fjerner redundans i en relasjonsdatabase.\n"
    "Tredje normalform krever at ingen ikke-nøkkelattributter\n"
    "avhenger transitivt av primærnøkkelen i tabellen."
)
