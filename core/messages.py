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
    # Shown by static/js/app.js when htmx gets no answer or an error status (AD-18).
    "network_error": "Fikk ikke kontakt med appen. Sjekk nettforbindelsen og prøv igjen.",
    "response_error": "Det du ba om, kunne ikke vises. Last inn siden på nytt og prøv igjen.",
}
