"""Request and response schemas for the AI gateway (AD-2).

Callers build the request objects, so `ai` never touches a model above `accounts`. Responses,
real or recorded (AD-4), validate against the same models.

AD-2 rules: no length or numeric constraints, no recursion, no confidence field and no field named
`reasoning`. Enum values are exactly the stored values (Conventions), lower-cased before validation.
Length rules (FR-7, FR-19) are checked by the caller after validation, never here.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator


def _lower(value):
    return value.strip().lower() if isinstance(value, str) else value


# The stored values of courses.DetailLevel and the Question kinds (AD-9). `ai` may not import
# `courses` (AD-1), so the values are repeated here; tests check they match.
DetailLevel = Annotated[Literal["short", "medium", "detailed"], BeforeValidator(_lower)]
QuestionKind = Annotated[Literal["multiple_choice", "free_text"], BeforeValidator(_lower)]
# The graded values of quiz.rules.Grade (`not_graded` is set by the caller on an AIError, never here).
Grade = Annotated[Literal["correct", "partial", "incorrect"], BeforeValidator(_lower)]


# ---- Requests ----------------------------------------------------------------------------


class Location(BaseModel):
    """The text of one Location the model sees (AD-6); `index` counts from 1."""

    index: int
    text: str


class GenerateRequest(BaseModel):
    """`generate_study_material`: one Source, as its Locations."""

    source_id: int
    content_sha256: str
    language: str = ""
    detail_level: DetailLevel
    locations: list[Location]


class SummaryRequest(BaseModel):
    """`regenerate_summary`: a new Summary of one Source at another Detail level (FR-7)."""

    source_id: int
    content_sha256: str
    language: str = ""
    detail_level: DetailLevel
    locations: list[Location]


class GradeRequest(BaseModel):
    """`grade_free_text`: one Free-text Answer, with the Source text at the Question's Reference (FR-12)."""

    prompt: str
    model_answer: str
    answer: str
    source_text: str
    language: str = ""


# ---- Responses ---------------------------------------------------------------------------


class Reference(BaseModel):
    """Where an item comes from (AD-6): a Location index and a verbatim quote."""

    location_index: int
    quote: str


class KeyConcept(BaseModel):
    term: str
    definition: str
    reference: Reference


class Flashcard(BaseModel):
    front: str
    back: str
    reference: Reference


class Option(BaseModel):
    """One of a Multiple-choice Question's four options, with why it is right or wrong."""

    text: str
    explanation: str


class Question(BaseModel):
    """AD-9: `options` holds four options for `multiple_choice` and none for `free_text`."""

    kind: QuestionKind
    prompt: str
    hint: str
    options: list[Option]
    correct_index: int | None
    model_answer: str
    reference: Reference


class StudyMaterial(BaseModel):
    """What one Generation call returns for a Source (FR-7)."""

    language: str
    summary: str
    key_concepts: list[KeyConcept]
    flashcards: list[Flashcard]
    questions: list[Question]


class SummaryResponse(BaseModel):
    """What `regenerate_summary` returns."""

    summary: str


class GradeResponse(BaseModel):
    """What `grade_free_text` returns: the Grade and why."""

    grade: Grade
    explanation: str
