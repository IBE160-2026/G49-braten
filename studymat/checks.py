"""The item checks after validation: FR-7 length/structure (drop) and the AD-6 Reference check (remove).

Pure functions over `ai.schemas` items and a {location_index: text} map; no database.
"""

import re
import unicodedata
from dataclasses import dataclass, field

from ai.markers import strip_markers
from ai.schemas import Flashcard, KeyConcept, Question, StudyMaterial

# AD-6 / FR-8: a quote shorter than this proves nothing.
MIN_QUOTE_WORDS = 5
# FR-7.
MAX_DEFINITION_SENTENCES = 2
HINT_SENTENCES = 1
MULTIPLE_CHOICE_OPTIONS = 4

_FOLD = str.maketrans(
    {
        "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'",
        "“": '"', "”": '"', "„": '"', "‟": '"', "«": '"', "»": '"',
        "″": '"', "‹": "'", "›": "'",
        "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-", "−": "-",
    }
)  # fmt: skip
_HYPHEN_BREAK = re.compile(r"[-‐­][^\S\n]*\n\s*")
_SOFT_HYPHEN = "­"
_WHITESPACE = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Both sides of the Reference check go through this (AD-6)."""
    text = strip_markers(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HYPHEN_BREAK.sub("", text)  # «normali-\nsering» -> «normalisering»
    text = text.replace(_SOFT_HYPHEN, "")
    text = text.translate(_FOLD)
    return _WHITESPACE.sub(" ", text).strip().casefold()


# ---- FR-7 -------------------------------------------------------------------------------

# Abbreviations whose full stop does not end a sentence.
_ABBREVIATIONS = (
    "f.eks.", "bl.a.", "dvs.", "osv.", "mv.", "ca.", "nr.", "jf.", "evt.", "inkl.", "pga.", "mht.",
    "e.l.", "o.l.", "m.m.", "e.g.", "i.e.", "etc.", "vs.", "dr.", "prof.",
)  # fmt: skip
_ABBREVIATION = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(a) for a in _ABBREVIATIONS) + ")")
# A full stop right after a digit («1. normalform») is an ordinal, not a sentence end.
_SENTENCE_END = re.compile(r"(?:[!?…]|(?<!\d)\.)[.!?…]*[\"')\]»]*(?=\s|$)")


def sentence_count(text: str) -> int:
    text = _WHITESPACE.sub(" ", text).strip()
    if not text:
        return 0
    lowered = text.casefold()
    lowered = _ABBREVIATION.sub(lambda match: match.group().replace(".", "_"), lowered)
    parts = [part for part in _SENTENCE_END.split(lowered) if part.strip(" \"'()[]»«")]
    return len(parts)


def key_concept_ok(item: KeyConcept) -> bool:
    return bool(item.term.strip()) and 0 < sentence_count(item.definition) <= MAX_DEFINITION_SENTENCES


def flashcard_ok(item: Flashcard) -> bool:
    return bool(item.front.strip() and item.back.strip())


def _option_core(text: str) -> str:
    return normalise(text).rstrip(" .!?;:")


def question_ok(item: Question) -> bool:
    if not item.prompt.strip() or sentence_count(item.hint) != HINT_SENTENCES:
        return False
    if item.kind == "multiple_choice":
        if len(item.options) != MULTIPLE_CHOICE_OPTIONS:
            return False
        if not all(option.text.strip() and option.explanation.strip() for option in item.options):
            return False
        if item.correct_index is None or not 0 <= item.correct_index < MULTIPLE_CHOICE_OPTIONS:
            return False
        correct = _option_core(item.options[item.correct_index].text)
        return not (correct and re.search(rf"(?<!\w){re.escape(correct)}(?!\w)", normalise(item.hint)))
    if item.options or item.correct_index is not None:
        return False  # AD-9: a Free-text Question has no options
    return bool(item.model_answer.strip())


# ---- AD-6 Reference check ---------------------------------------------------------------


def normalise_locations(locations: dict[int, str]) -> dict[int, str]:
    """{index: normalised text} for the non-empty Locations, normalised once per Source."""
    return {index: normalise(body) for index, body in locations.items() if body.strip()}


def reference_ok(item, locations: dict[int, str]) -> bool:
    """`locations` maps each non-empty Location's index to its text."""
    return _reference_ok(item, normalise_locations(locations))


def _reference_ok(item, normalised: dict[int, str]) -> bool:
    ref = item.reference
    quote = normalise(ref.quote)
    if len(quote.split()) < MIN_QUOTE_WORDS:
        return False
    if ref.location_index not in normalised:
        return False
    if quote not in normalised[ref.location_index]:
        return False
    found_in = sum(quote in body for body in normalised.values())
    repeated = found_in > len(normalised) / 2 and found_in >= 2
    return not repeated


# ---- Both, over one StudyMaterial -------------------------------------------------------


@dataclass
class Checked:
    key_concepts: list[KeyConcept] = field(default_factory=list)
    flashcards: list[Flashcard] = field(default_factory=list)
    questions: list[Question] = field(default_factory=list)
    dropped: int = 0  # FR-7 failures -> Source.dropped_count
    removed: int = 0  # Reference failures -> Source.removed_count


def check(material: StudyMaterial, locations: dict[int, str]) -> Checked:
    """FR-7 checks first (drop), then the Reference check on what is left (remove)."""
    result = Checked()
    normalised = normalise_locations(locations)
    groups = (
        (material.key_concepts, key_concept_ok, result.key_concepts),
        (material.flashcards, flashcard_ok, result.flashcards),
        (material.questions, question_ok, result.questions),
    )
    for items, rule, kept in groups:
        for item in items:
            if not rule(item):
                result.dropped += 1
            elif not _reference_ok(item, normalised):
                result.removed += 1
            else:
                kept.append(item)
    return result
