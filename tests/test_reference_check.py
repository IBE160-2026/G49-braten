"""FR-7, FR-8 (story 6): the item checks and the Reference check (AD-6), as pure functions."""

import pytest

from ai import markers
from ai.schemas import Flashcard, KeyConcept, Option, Question, Reference, StudyMaterial
from studymat import checks

QUOTE = "Normalisering er en metode for å strukturere tabeller."


def card(quote=QUOTE, index=1) -> Flashcard:
    return Flashcard(front="Hva?", back="Dette.", reference=Reference(location_index=index, quote=quote))


def concept(definition="En metode. Den fjerner redundans.") -> KeyConcept:
    return KeyConcept(term="Normalisering", definition=definition, reference=Reference(location_index=1, quote=QUOTE))


def multiple_choice(**overrides) -> Question:
    fields = dict(
        kind="multiple_choice",
        prompt="Hva er 2NF?",
        hint="Tenk på delnøkler.",
        options=[Option(text=t, explanation="Fordi.") for t in ("1NF", "3NF", "Ingen partielle avhengigheter.", "4NF")],
        correct_index=2,
        model_answer="",
        reference=Reference(location_index=1, quote=QUOTE),
    )
    fields.update(overrides)
    return Question(**fields)


def free_text(**overrides) -> Question:
    fields = dict(
        kind="free_text",
        prompt="Forklar normalisering.",
        hint="Tenk på redundans.",
        options=[],
        correct_index=None,
        model_answer="Den fjerner redundans.",
        reference=Reference(location_index=1, quote=QUOTE),
    )
    fields.update(overrides)
    return Question(**fields)


# ---- Normalisation (AD-6) ----------------------------------------------------------------


def test_fr8_hyphenation_across_a_line_break_is_joined():
    page = {1: "Normali-\nsering er en metode for å strukturere tabeller."}
    assert checks.reference_ok(card(), page)


def test_fr8_line_breaks_and_extra_whitespace_are_collapsed():
    page = {1: "Normalisering er en\nmetode   for å\n\nstrukturere tabeller."}
    assert checks.reference_ok(card(), page)


def test_fr8_curly_quotes_and_dashes_are_folded():
    page = {1: "Han sa “normalisering er viktig” – for alle tabeller her."}
    quote = 'han sa "Normalisering er viktig" - for alle'
    assert checks.reference_ok(card(quote), page)


def test_fr8_case_and_nfkc_are_normalised():
    page = {1: "ﬁre TABELLER er på første normalform i dag."}  # «ﬁ» ligature
    assert checks.reference_ok(card("Fire tabeller er på første normalform"), page)


def test_fr8_markers_are_stripped_from_both_sides():
    page = {1: markers.marker(1) + "\n" + QUOTE}
    assert checks.reference_ok(card(markers.marker(1) + " " + QUOTE), page)
    assert markers.strip_markers(markers.marker(12)).strip() == ""


def test_fr8_marked_text_marks_only_non_empty_locations():
    from ai.schemas import Location

    text = markers.marked_text([Location(index=1, text="A"), Location(index=2, text="  "), Location(index=3, text="B")])
    assert markers.marker(1) in text and markers.marker(3) in text
    assert markers.marker(2) not in text


# ---- Reference rules ---------------------------------------------------------------------


def test_fr8_a_four_word_quote_is_removed():
    page = {1: QUOTE}
    assert not checks.reference_ok(card("Normalisering er en metode"), page)
    assert checks.reference_ok(card("Normalisering er en metode for"), page)


def test_fr8_a_header_repeated_on_most_pages_is_removed():
    header = "DAT102 Databaser høsten 2026 forelesning"
    pages = {i: f"{header}\nInnhold på side {i} om noe helt eget nr {i}." for i in range(1, 6)}
    assert not checks.reference_ok(card(header, 2), pages)


def test_fr8_a_quote_on_two_of_five_pages_is_kept():
    shared = "denne setningen står på to sider"
    pages = {i: f"Side {i} har sitt eget innhold." for i in range(1, 6)}
    pages[2] += " " + shared
    pages[4] += " " + shared
    assert checks.reference_ok(card(shared, 2), pages)


def test_fr8_a_quote_on_exactly_half_the_pages_is_kept():
    shared = "denne setningen står på to sider"
    pages = {i: f"Side {i} har sitt eget innhold." for i in range(1, 5)}
    pages[1] += " " + shared
    pages[3] += " " + shared
    assert checks.reference_ok(card(shared, 1), pages)


def test_fr8_a_single_location_source_passes():
    assert checks.reference_ok(card(), {1: QUOTE})


def test_fr8_a_missing_location_is_removed():
    assert not checks.reference_ok(card(index=7), {1: QUOTE})
    assert not checks.reference_ok(card(index=2), {1: QUOTE, 2: "   "})


def test_fr8_a_quote_on_another_page_is_removed():
    assert not checks.reference_ok(card(index=2), {1: QUOTE, 2: "Noe helt annet står her på siden."})


# ---- FR-7 --------------------------------------------------------------------------------


def test_fr7_sentence_count_ignores_abbreviations():
    assert checks.sentence_count("Bruk f.eks. en nøkkel. Så er du ferdig.") == 2
    assert checks.sentence_count("Én setning uten punktum") == 1
    assert checks.sentence_count("") == 0


def test_fr7_a_full_stop_after_a_digit_does_not_end_a_sentence():
    assert checks.sentence_count("Tabellen er på 1. normalform.") == 1


def test_fr7_an_abbreviation_inside_a_word_still_ends_a_sentence():
    assert checks.sentence_count("Han bor i Jamaica. Det er varmt.") == 2


def test_fr7_a_definition_of_three_sentences_is_dropped():
    assert checks.key_concept_ok(concept())
    assert not checks.key_concept_ok(concept("En. To. Tre."))


def test_fr7_a_hint_must_be_exactly_one_sentence():
    assert checks.question_ok(multiple_choice())
    assert not checks.question_ok(multiple_choice(hint="Tenk. Og tenk igjen."))
    assert not checks.question_ok(free_text(hint=""))


def test_fr7_a_hint_containing_the_correct_option_is_dropped():
    assert not checks.question_ok(multiple_choice(hint="Svaret er ingen partielle avhengigheter."))
    assert checks.question_ok(multiple_choice(hint="Svaret er ikke 1NF."))  # a wrong option is fine


def test_fr7_a_short_correct_option_matches_only_whole_words_in_the_hint():
    options = [Option(text=t, explanation="Fordi.") for t in ("Nei", "Ja", "Kanskje", "Aldri")]
    assert checks.question_ok(multiple_choice(options=options, correct_index=1, hint="Tenk på jakten etter nøkler."))
    assert not checks.question_ok(multiple_choice(options=options, correct_index=1, hint="Svaret er ja, ikke nei."))
    one_nf = [Option(text=t, explanation="Fordi.") for t in ("1NF", "2NF", "3NF", "4NF")]
    assert checks.question_ok(multiple_choice(options=one_nf, correct_index=0, hint="Se på regel 11NF i notatet."))


def test_fr7_multiple_choice_needs_four_explained_options_and_a_valid_index():
    options = multiple_choice().options
    assert not checks.question_ok(multiple_choice(options=options[:3]))
    assert not checks.question_ok(multiple_choice(options=[*options[:3], Option(text="4NF", explanation="")]))
    assert not checks.question_ok(multiple_choice(correct_index=4))
    assert not checks.question_ok(multiple_choice(correct_index=None))


def test_fr7_free_text_needs_a_model_answer():
    assert checks.question_ok(free_text())
    assert not checks.question_ok(free_text(model_answer=" "))


def test_fr7_free_text_with_options_or_a_correct_index_is_dropped():
    assert not checks.question_ok(free_text(options=[Option(text="A", explanation="B")]))
    assert not checks.question_ok(free_text(correct_index=0))


def test_fr7_check_drops_and_removes_and_counts_separately():
    material = StudyMaterial(
        language="nb",
        summary="Et sammendrag.",
        key_concepts=[concept(), concept("En. To. Tre.")],
        flashcards=[card(), card(index=2)],
        questions=[multiple_choice(), free_text(model_answer="")],
    )
    result = checks.check(material, {1: QUOTE, 2: "Noe annet på denne siden helt for seg."})
    assert (len(result.key_concepts), len(result.flashcards), len(result.questions)) == (1, 1, 1)
    assert (result.dropped, result.removed) == (2, 1)


@pytest.mark.parametrize("words", [5, 8])
def test_fr8_min_quote_words_is_five(words):
    assert checks.MIN_QUOTE_WORDS == 5
    text = " ".join(f"ord{i}" for i in range(words))
    assert checks.reference_ok(card(text), {1: text})
