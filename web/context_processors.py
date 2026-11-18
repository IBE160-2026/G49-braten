"""The shell context every page gets: the theme, the AI mode and, when signed in, the Student's fag
with their Due cards («I dag · N», FR-15) and their Course scores (FR-16, FR-17)."""

from functools import cached_property

from django.utils.functional import SimpleLazyObject

from ai import gateway
from courses.models import Course
from progress import services as progress_services
from review import services as review_services

# The theme override lives only in this cookie, rendered as <html data-theme> (Conventions).
THEME_COOKIE = "theme"
THEMES = ("light", "dark")


def theme_from(request) -> str:
    value = request.COOKIES.get(THEME_COOKIE, "")
    return value if value in THEMES else ""


class ShellDue:
    """Due cards for the shell, from review.services.due_cards only (AD-11); evaluated on first use,
    so pages without the shell (sessions) never count."""

    def __init__(self, student):
        self.student = student

    @cached_property
    def by_course(self) -> dict[int, int]:
        return review_services.due_count_by_course(self.student)

    @cached_property
    def total(self) -> int:
        return sum(self.by_course.values())


def _courses_with_due(student, due: ShellDue) -> list:
    """Each fag with `due_today` and `mastery` (a progress.services.CourseScore), computed on read
    (AD-10) the first time the list is used."""
    courses = list(Course.objects.for_student(student))
    scores = progress_services.course_scores(student)
    for course in courses:
        course.due_today = due.by_course.get(course.id, 0)
        course.mastery = scores.get(course.id) or progress_services.CourseScore(course.id, None)
    return courses


def shell(request):
    # `mock` shows the mode-banner (FR-20); never the Key itself.
    context = {"theme": theme_from(request), "ai_mode": gateway.mode()}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        due = ShellDue(user)
        context["shell_due"] = due
        # Lazy and evaluated once per render: the rail, the fag-switcher and Hjem share it.
        context["shell_courses"] = SimpleLazyObject(lambda: _courses_with_due(user, due))
    return context
