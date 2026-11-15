"""Student-facing text by error code (Conventions: "Errors to the Student").

A plain dict from `code` to Norwegian bokmål text. Views and forms never write error
text inline; they look it up here. Calm, «du», no exclamation marks.
"""

MESSAGES: dict[str, str] = {
    "wrong_credentials": "Feil e-post eller passord.",
    "email_in_use": "Det finnes allerede en konto med denne e-postadressen.",
    "course_name_required": "Skriv inn et navn på faget.",
    "course_name_too_long": "Navnet kan ha høyst 80 tegn.",
    "course_code_too_long": "Kurskoden kan ha høyst 20 tegn.",
    # Shown by static/js/app.js when htmx gets no answer or an error status (AD-18).
    "network_error": "Fikk ikke kontakt med appen. Sjekk nettforbindelsen og prøv igjen.",
    "response_error": "Det du ba om, kunne ikke vises. Last inn siden på nytt og prøv igjen.",
}
