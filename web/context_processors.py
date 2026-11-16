"""The shell context every page gets: the theme, the AI mode and, when signed in, the Student's fag."""

from ai import gateway
from courses.models import Course

# The theme override lives only in this cookie, rendered as <html data-theme> (Conventions).
THEME_COOKIE = "theme"
THEMES = ("light", "dark")


def theme_from(request) -> str:
    value = request.COOKIES.get(THEME_COOKIE, "")
    return value if value in THEMES else ""


def shell(request):
    # `mock` shows the mode-banner (FR-20); never the Key itself.
    context = {"theme": theme_from(request), "ai_mode": gateway.mode()}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        # Lazy and evaluated once per render: the rail, the fag-switcher and Hjem share it.
        context["shell_courses"] = Course.objects.for_student(user)
    return context
