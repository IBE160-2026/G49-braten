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
    # FR-22, AD-17: the gateway refused to send before D04 «Før du laster opp» was accepted.
    "privacy_not_accepted": "Du må godta personvernvarselet før teksten sendes til KI-tjenesten.",
    "privacy_notice_link": "Les og godta varselet",
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
    # P09 Repetisjon (FR-15, story 11): when a card returns, relative to today (review.rules.return_label).
    "return_today": "i dag",
    "return_tomorrow": "i morgen",
    "return_days": "om {n} dager",
    "return_week": "om 1 uke",
    "return_weeks": "om {n} uker",
    "return_month": "om 1 mnd.",
    "return_months": "om {n} mnd.",
    "review_context_all": "I dag · repetisjon",
    "review_context_scoped": "{name} · repetisjon",
    # Mastery (FR-16, FR-17, story 12): progress figures on the shell, Hjem, P04, P05 and D10.
    "mastery_none": "Ikke nok data ennå",
    "mastery_explain_course": "Mestring for et fag er snittet av temaene som har nok svar.",
    "mastery_explain_topic": "Basert på de 20 siste svarene dine.",
    "mastery_rail_label": "mestring {n} % i snitt",
    "mastery_rail_none": "mestring: ikke nok data ennå",
    "practice_tag": "Trenger øving",
    "practice_tag_course_one": "1 tema trenger øving",
    "practice_tag_course_other": "{n} temaer trenger øving",
    # D10 «Øv på svake temaer» (FR-17).
    "weak_quiz_title": "Øv på svake temaer",
    "weak_quiz_button": "Øv på svake temaer ({n})",
    "weak_quiz_lead": "Temaene som trenger øving er valgt. Svakeste først.",
    "weak_quiz_topics_required": "Velg minst ett tema.",
    "weak_quiz_count_one": "{t} tema valgt · {q} spørsmål",
    "weak_quiz_count_other": "{t} temaer valgt · {q} spørsmål",
    # P05 «Tidligere quizer» (FR-27).
    "history_score": "{k} av {n} riktige",
    "history_partial": "· {p} delvis",
    "history_retry_note": "Runder med «Øv på feilene» teller ikke i mestringen.",
    "history_empty": "Du har ikke tatt en quiz i dette temaet ennå.",
    "history_see_result": "Se resultatet",
    # Shown by static/js/app.js when htmx gets no answer or an error status (AD-18).
    "network_error": "Fikk ikke kontakt med appen. Sjekk nettforbindelsen og prøv igjen.",
    "response_error": "Det du ba om, kunne ikke vises. Last inn siden på nytt og prøv igjen.",
}
