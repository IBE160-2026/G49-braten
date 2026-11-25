"""AD-5 step 1: validate an upload, extract its text per Location and create the Source as `pending`.

Every check runs before anything is saved, and the Source and its SourceText rows are created
in one transaction, so a rejection keeps nothing. The uploaded file itself is never stored.
Source text is never logged.
"""

import hashlib
import logging
from dataclasses import dataclass

from django.db import transaction

from core.messages import MESSAGES
from courses.models import DetailLevel, Source, SourceKind, Topic
from courses.services import create_source
from ingestion import extract
from ingestion.errors import IngestError
from ingestion.models import LocationKind, SourceText

logger = logging.getLogger(__name__)

__all__ = ["IngestError", "ingest"]


@dataclass(frozen=True)
class Extracted:
    name: str
    kind: str  # SourceKind
    size_bytes: int
    content_sha256: str
    location_kind: str  # LocationKind
    texts: list[str]


def _from_upload(upload) -> Extracted:
    file_name = upload.name or ""
    ext = extract.extension(file_name)
    if ext not in (extract.PDF_EXTENSION, extract.TEXT_EXTENSION):
        raise IngestError("unsupported_type")
    if upload.size > extract.MAX_FILE_BYTES:
        raise IngestError("file_too_large", size=upload.size, limit=extract.MAX_FILE_BYTES)
    data = upload.read()
    if ext == extract.PDF_EXTENSION:
        texts = extract.pdf_pages(data)
        if extract.non_whitespace_count(texts) < extract.MIN_TEXT_CHARS:
            raise IngestError("scanned_pdf")
        if extract.glyph_name_share(texts) > extract.GLYPH_NAME_SHARE_MAX:
            raise IngestError("unmapped_font_pdf")
        kind, location_kind = SourceKind.PDF, LocationKind.PAGE
    else:
        texts = extract.paragraphs(extract.decode_text(data))
        if not texts:
            raise IngestError("empty_file")
        kind, location_kind = SourceKind.TEXT, LocationKind.PARAGRAPH
    extract.check_char_limit(texts)
    return Extracted(
        name=extract.shorten_name(file_name),
        kind=kind,
        size_bytes=len(data),
        content_sha256=hashlib.sha256(data).hexdigest(),
        location_kind=location_kind,
        texts=texts,
    )


def _from_text(text: str, name: str) -> Extracted:
    text = extract.normalise_newlines(text).lstrip(extract.BOM)
    texts = extract.paragraphs(text)
    if not texts:
        raise IngestError("paste_empty")
    extract.check_char_limit(texts)
    return Extracted(
        name=extract.shorten_name(name.strip() or MESSAGES["pasted_default_name"]),
        kind=SourceKind.PASTED,
        size_bytes=0,
        content_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        location_kind=LocationKind.PARAGRAPH,
        texts=texts,
    )


def ingest(topic: Topic, *, upload=None, text: str = "", name: str = "", detail_level: str) -> Source:
    """A new `pending` Source in `topic` with one SourceText row per Location (AD-5, AD-6).

    Takes either an uploaded file (`upload`) or pasted `text`; `name` names pasted text only.
    Raises IngestError when the input breaks a limit or cannot be read; nothing is saved then.
    """
    assert detail_level in DetailLevel.values, detail_level
    has_text = bool(text and text.strip())
    if upload is not None and has_text:
        raise IngestError("file_or_text")
    if upload is not None:
        extracted = _from_upload(upload)
    elif has_text:
        extracted = _from_text(text, name)
    else:
        raise IngestError("paste_empty")

    with transaction.atomic():
        source = create_source(
            topic,
            extracted.name,
            extracted.kind,
            size_bytes=extracted.size_bytes,
            content_sha256=extracted.content_sha256,
            detail_level=detail_level,
        )
        SourceText.objects.bulk_create(
            SourceText(
                student_id=source.student_id,
                source=source,
                kind=extracted.location_kind,
                index=i,
                label=str(i),
                text=body,
            )
            for i, body in enumerate(extracted.texts, start=1)
        )
    logger.info(
        "Source %s ingested for student %s: kind=%s locations=%d",
        source.id, source.student_id, source.kind, len(extracted.texts),
    )  # fmt: skip
    return source
