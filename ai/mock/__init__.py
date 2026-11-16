"""The Mock adapter (FR-20, AD-4): recorded answers for the Sample document.

The Sample document is recognised by `content_sha256`, which ingestion sets from the file bytes
(AD-5); SAMPLE_SHA256 is computed from the committed PDF at import, so re-rendering it needs no
code change. Recordings are validated through the same schema models as real responses.

Story 5 writes the recordings by hand against pypdf's extracted page text; `manage.py record_mock`
(story 10) re-records them. Exactly one recorded item has a wrong `location_index` on purpose, so
the real Reference check (story 6) removes it (AD-4).
"""

import hashlib
import json
from functools import cache
from pathlib import Path

from ai.schemas import StudyMaterial, SummaryResponse

RECORDINGS_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = RECORDINGS_DIR.parent.parent / "sample" / "normalisering.pdf"
SAMPLE_NAME = SAMPLE_PATH.name
SAMPLE_SHA256 = hashlib.sha256(SAMPLE_PATH.read_bytes()).hexdigest()
# The Sample document has one slide per page.
SAMPLE_PAGES = 20

STUDY_MATERIAL_FILE = RECORDINGS_DIR / "study_material.json"
SUMMARIES_FILE = RECORDINGS_DIR / "summaries.json"


def is_sample(content_sha256: str) -> bool:
    return content_sha256 == SAMPLE_SHA256


@cache
def _summaries() -> dict[str, SummaryResponse]:
    raw = json.loads(SUMMARIES_FILE.read_text(encoding="utf-8"))
    return {level: SummaryResponse.model_validate(body) for level, body in raw.items()}


@cache
def _study_material() -> StudyMaterial:
    return StudyMaterial.model_validate_json(STUDY_MATERIAL_FILE.read_bytes())


def summary(detail_level: str) -> SummaryResponse:
    """The recorded Summary of the Sample document at `detail_level`."""
    return _summaries()[detail_level].model_copy(deep=True)


def study_material(detail_level: str) -> StudyMaterial:
    """The recorded Study material, with the Summary recorded for `detail_level`."""
    material = _study_material().model_copy(deep=True)
    material.summary = summary(detail_level).summary
    return material
