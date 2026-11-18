"""Student-facing text by error code (Conventions: "Errors to the Student").

A plain dict from `code` to Norwegian bokmål text. Views and forms never write error
text inline; they look it up here. Calm, «du», no exclamation marks.
"""

MESSAGES: dict[str, str] = {
    "wrong_credentials": "Feil e-post eller passord.",
    "email_in_use": "Det finnes allerede en konto med denne e-postadressen.",
    "course_name_required": "Skriv inn et navn på faget.",
    "course_name_too_long": "Navnet kan ha høyst 80 tegn.",
    "topic_name_required": "Skriv inn et navn på temaet.",
    "source_name_required": "Skriv inn et navn på kilden.",
    "course_code_too_long": "Kurskoden kan ha høyst 20 tegn.",
    # D09 «Slette …?» (FR-2): courses.rules counts and joins these; zero counts are left out.
    "delete_count_topic_one": "{n} tema",
    "delete_count_topic_other": "{n} temaer",
    "delete_count_source_one": "{n} kilde",
    "delete_count_source_other": "{n} kilder",
    "delete_lead_counted": "{items} og alle svar slettes.",
    "delete_lead_source": "Studiemateriellet fra kilden og svarene på det slettes.",
    "delete_cannot_undo": "Dette kan ikke angres.",
    # FR-8: under a kilde's summary-block on P05 when the Reference check removed items.
    "removed_note_one": "1 element ble fjernet fordi kildehenvisningen ikke stemte.",
    "removed_note_other": "{n} elementer ble fjernet fordi kildehenvisningen ikke stemte.",
    # D05 «Legg til kilde» (FR-3): ingestion rejections name the limit; params are formatted by
    # ingestion.errors (thousands with a space, megabytes with a decimal comma).
    "too_many_pages": "Filen har {pages} sider. Grensen er {limit} sider, så last opp ett kapittel om gangen.",
    "file_too_large": "Filen er {size} MB. Grensen er {limit} MB.",
    "too_many_chars": "Teksten har {chars} tegn. Grensen er {limit} tegn.",
    "scanned_pdf": "Fant ingen tekst i PDF-en. Skannede dokumenter støttes ikke.",
    "unsupported_type": "Bare PDF og tekstfiler (.txt) støttes.",
    "unreadable_pdf": "Kunne ikke lese PDF-en. Den kan være skadet eller passordbeskyttet.",
    "empty_file": "Fant ingen tekst i filen.",
    "paste_empty": "Lim inn tekst først.",
    "file_or_text": "Velg enten en fil eller tekst.",
    "detail_level_required": "Velg et detaljnivå.",
    "null_characters": "Teksten inneholder et tegn som ikke støttes (nulltegn).",
    "pasted_name_too_long": "Navnet kan ha høyst 80 tegn.",
    # The name a pasted Source gets when the Student leaves the name field blank.
    "pasted_default_name": "Innlimt tekst",
    # AI gateway errors (AD-2), keyed by courses.FailureReason; the rest arrive with stories 6 and 10.
    "needs_key": "I demomodus lages studiemateriell bare for eksempeldokumentet. Legg inn en API-nøkkel for å bruke egne filer.",
    "daily_limit": "Du har brukt alle 20 genereringene for i dag. Grensen nullstilles ved midnatt.",
    # Generation failures on the source-row (FR-9, story 6); `timed_out` is set by AD-5.
    "timed_out": "Genereringen ble ikke ferdig. Prøv igjen.",
    "truncated": "Kunne ikke lage studiemateriell fordi svaret fra KI-tjenesten ble avbrutt. Prøv igjen.",
    "rate_limited": "KI-tjenesten har mange forespørsler akkurat nå. Vent noen minutter og prøv igjen.",
    "refused": "Kunne ikke lage studiemateriell fordi KI-tjenesten avviste forespørselen. Prøv igjen.",
    "invalid_format": "Kunne ikke lage studiemateriell fordi svaret fra KI-tjenesten hadde feil format. Prøv igjen.",
    "provider_unavailable": "Kunne ikke lage studiemateriell fordi KI-tjenesten ikke svarte. Prøv igjen.",
    # FR-21 (EXPERIENCE.md, State Patterns «Key rejected»): on the source-row and in a Quiz.
    "key_rejected": "KI-tjenesten godtok ikke API-nøkkelen. Sjekk nøkkelen i .env og start appen på nytt.",
    # P06 Quiz (FR-10 to FR-12, story 8).
    "answer_choose_first": "Velg et svar først.",
    "answer_write_first": "Skriv et svar først.",
    "grading_failed": "Kunne ikke rette svaret fordi KI-tjenesten ikke svarte. Prøv igjen.",
    "mock_grade_explanation": "Demo-vurdering: {k} av {m} nøkkelord fra fasiten finnes i svaret ditt.",
    "quiz_count_required": "Velg hvor mange spørsmål du vil ha.",
    "quiz_available": "{n} spørsmål tilgjengelig. Flervalg og fritekst blandes.",
    # P07 «Resultat» and the Retry round (FR-13, story 9). {numbers} are display numbers joined with «og».
    "result_lead_correct_one": "{n} riktig",
    "result_lead_correct_other": "{n} riktige",
    "result_lead_partial_one": "{n} delvis riktig",
    "result_lead_partial_other": "{n} delvis riktige",
    "result_lead_incorrect": "{n} feil",
    "result_all_correct": "Alle svarene var riktige.",
    "result_unanswered": "Ikke besvart",
    "result_not_graded_note": "Spørsmålet er ikke med i «Øv på feilene» før det er rettet.",
    "result_open_question": "Åpne spørsmålet",
    "retry_band_unit": "spørsmål",
    "retry_band_heading": "Øv på feilene",
    "retry_band_why_one": "Spørsmål {numbers} var feil eller delvis riktig. Runden teller ikke i mestringen.",
    "retry_band_why_other": "Spørsmål {numbers} var feil eller delvis riktige. Runden teller ikke i mestringen.",
    "retry_band_button": "Øv på feilene ({n})",
    "band_minutes": "ca. {m} min",
    "retry_context": "Øv på feilene",
    "retry_note": "Denne runden teller ikke i mestringen.",
    # Shown by static/js/app.js when htmx gets no answer or an error status (AD-18).
    "network_error": "Fikk ikke kontakt med appen. Sjekk nettforbindelsen og prøv igjen.",
    "response_error": "Det du ba om, kunne ikke vises. Last inn siden på nytt og prøv igjen.",
}
