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
    # Shown by static/js/app.js when htmx gets no answer or an error status (AD-18).
    "network_error": "Fikk ikke kontakt med appen. Sjekk nettforbindelsen og prøv igjen.",
    "response_error": "Det du ba om, kunne ikke vises. Last inn siden på nytt og prøv igjen.",
}
