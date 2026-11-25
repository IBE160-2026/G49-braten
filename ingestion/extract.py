"""Text extraction as pure functions (FR-3, FR-4, AD-6). No database, no Django request objects.

The limits are the PRD §10 numbers (FR-3); MIN_TEXT_CHARS and the plain extraction mode are
the confirmed OQ-1 decision (docs/quality/oq1-pdf-extraction.md).
"""

import codecs
import io
import logging
import os
import re

from pypdf import PdfReader

from courses.models import NAME_MAX_LENGTH
from ingestion.errors import MEGABYTE, IngestError

logger = logging.getLogger(__name__)

# PRD §10 / FR-3.
MAX_FILE_BYTES = 10 * MEGABYTE
MAX_PAGES = 50
MAX_CHARS = 150_000  # extracted characters, every kind
# OQ-1 (confirmed 2026-11-25): fewer non-whitespace characters than this in a whole PDF means scanned.
MIN_TEXT_CHARS = 200
# OQ-1 (measured 2026-11-23): a font with no Unicode map (LaTeX Type 3 / bitmap fonts) makes pypdf
# print glyph names such as «/BW/CT/D2» instead of letters. Such a deck passes MIN_TEXT_CHARS but is
# unreadable. Measured: 89 % glyph names on such a deck, at most 0.9 % on seven ordinary ones.
GLYPH_NAME_SHARE_MAX = 0.5

PDF_EXTENSION = ".pdf"
TEXT_EXTENSION = ".txt"
PDF_MAGIC = b"%PDF-"

BOM = "\ufeff"

_BLANK_LINE = re.compile(r"\n[^\S\n]*\n\s*")
_WHITESPACE = re.compile(r"\s+")
# Two or more glyph names back to back, so a lone «/studier» or «og/eller» does not count. No «.» in a
# name, so «/www.uit.no/studier» is not a run; a longer URL path can still count, but stays a tiny share.
_GLYPH_NAME = re.compile(r"(?:/[A-Za-z][A-Za-z0-9_]*){2,}")


def extension(file_name: str) -> str:
    """The lower-cased extension, «.pdf» or «.txt» for the types we take, else whatever it is."""
    return os.path.splitext(file_name)[1].lower()


def normalise_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def decode_text(data: bytes) -> str:
    """UTF-16 when it starts with a UTF-16 BOM; else UTF-8 with any BOM stripped, falling back to
    cp1252. Otherwise NUL bytes mean it is not text."""
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        try:
            text = data.decode("utf-16")  # uses and strips the BOM
        except UnicodeDecodeError:
            raise IngestError("unsupported_type") from None
        if "\x00" in text:
            raise IngestError("unsupported_type")
        return text
    if b"\x00" in data:
        raise IngestError("unsupported_type")
    if data.startswith(codecs.BOM_UTF8):
        data = data[len(codecs.BOM_UTF8) :]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp1252")
    except UnicodeDecodeError:
        raise IngestError("unsupported_type") from None


def paragraphs(text: str) -> list[str]:
    """One block per run of lines separated by blank lines; line endings normalised, blocks stripped."""
    text = normalise_newlines(text).lstrip(BOM)
    return [block.strip() for block in _BLANK_LINE.split(text) if block.strip()]


def pdf_pages(data: bytes) -> list[str]:
    """The text of every page, empty pages included, in plain `extract_text()` mode.

    Refuses a file that does not start with %PDF-, an encrypted or unreadable PDF, and more
    than MAX_PAGES pages (counted before any text is extracted).
    """
    if not data.startswith(PDF_MAGIC):
        raise IngestError("unsupported_type")
    try:
        reader = PdfReader(io.BytesIO(data))
        # An owner password alone (empty user password) only restricts editing; the text is readable.
        if reader.is_encrypted and not reader.decrypt(""):
            raise IngestError("unreadable_pdf")
        pages = reader.pages
        count = len(pages)
    except IngestError:
        raise
    except Exception:  # pypdf raises many kinds on a broken file; none may become a 500.
        logger.warning("PDF refused: could not be read", exc_info=True)
        raise IngestError("unreadable_pdf") from None
    if count > MAX_PAGES:
        raise IngestError("too_many_pages", pages=count, limit=MAX_PAGES)
    texts = []
    for page in pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            logger.warning("PDF refused: a page could not be extracted", exc_info=True)
            raise IngestError("unreadable_pdf") from None
        texts.append(valid_utf8(normalise_newlines(text).replace("\x00", "")))
    return texts


def valid_utf8(text: str) -> str:
    """Lone surrogates (from broken ToUnicode maps) become U+FFFD, so the database write cannot fail."""
    if text.isascii():
        return text
    return text.encode("utf-8", "surrogatepass").decode("utf-8", "replace")


def non_whitespace_count(texts: list[str]) -> int:
    return sum(len(_WHITESPACE.sub("", text)) for text in texts)


def glyph_name_share(texts: list[str]) -> float:
    """The share of non-whitespace characters in runs of pypdf glyph names (`/BW/CT`), 0.0 for no text."""
    total = non_whitespace_count(texts)
    if not total:
        return 0.0
    return sum(len(name) for text in texts for name in _GLYPH_NAME.findall(text)) / total


def check_char_limit(texts: list[str]) -> None:
    total = sum(len(text) for text in texts)
    if total > MAX_CHARS:
        raise IngestError("too_many_chars", chars=total, limit=MAX_CHARS)


def shorten_name(name: str, limit: int = NAME_MAX_LENGTH) -> str:
    """At most `limit` characters, keeping the extension; the middle of the stem becomes «…»."""
    name = name.strip()
    if len(name) <= limit:
        return name
    stem, ext = os.path.splitext(name)
    if len(ext) >= limit // 2:  # not a real extension; shorten the whole name
        stem, ext = name, ""
    room = limit - len(ext) - 1
    head = (room + 1) // 2
    tail = room - head
    return stem[:head] + "…" + (stem[-tail:] if tail else "") + ext
