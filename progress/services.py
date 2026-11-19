"""Topic score, Course score and Weak topics, computed on read (AD-10, FR-16, FR-17).

Nothing is stored. One query fetches the counted Answers of a scope, newest first, and
`progress.rules` does the arithmetic. Every page reads its figures from here.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction

from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from core import time
from core.messages import MESSAGES
from courses.models import Course, Source, Status, Topic
from courses.scope import Scope
from progress import rules
from quiz.forms import default_count
from quiz.models import Answer, QuizKind
from quiz.rules import WEIGHTS, join_with_og
from review import services as review_services
from studymat.models import Question


@dataclass(frozen=True)
class TopicScore:
    topic: Topic
    # Counted Answers inside the window (0..WINDOW).
    answers: int
    # The unrounded mean, or None with fewer than MIN_ANSWERS («Ikke nok data ennå»).
    mean: Fraction | None

    @property
    def score(self) -> int | None:
        return None if self.mean is None else rules.percent(self.mean)

    @property
    def is_weak(self) -> bool:
        return rules.is_weak(self.score)


@dataclass(frozen=True)
class CourseScore:
    course_id: int
    mean: Fraction | None
    # Every Topic of the Course, in creation order.
    topics: list[TopicScore] = field(default_factory=list)

    @property
    def score(self) -> int | None:
        return None if self.mean is None else rules.percent(self.mean)

    @property
    def weak(self) -> list[TopicScore]:
        return weak_of(self.topics)

    @property
    def weakest(self) -> TopicScore | None:
        """The lowest scored Topic (Weak or not), or None when no Topic has a score."""
        scored = [t for t in self.topics if t.score is not None]
        return min(scored, key=lambda t: t.score) if scored else None


def _topics(student, scope: Scope):
    topics = Topic.objects.for_student(student).order_by("created_at", "id")
    if scope.topic_id is not None:
        return topics.filter(id=scope.topic_id)
    if scope.course_id is not None:
        return topics.filter(course_id=scope.course_id)
    return topics


def _counted_grades(student, scope: Scope) -> dict[int, list[str]]:
    """{topic id: effective Grades, newest first} of the counted Answers in scope.

    Counted: an effective Grade with a weight (never `not_graded` or pending) in a Quiz that is not
    a Retry round. Newest means `answered_at` desc, then `id` desc (AD-9).
    """
    answers = (
        Answer.objects.for_student(student)
        .with_effective_grade()
        .filter(effective_grade__in=list(WEIGHTS))
        .exclude(quiz__kind=QuizKind.RETRY)
    )
    answers = scope.filter(answers, "question__source__topic")
    rows = answers.order_by("-answered_at", "-id").values_list("question__source__topic_id", "effective_grade")
    grades: dict[int, list[str]] = defaultdict(list)
    for topic_id, grade in rows:
        if len(grades[topic_id]) < rules.WINDOW:
            grades[topic_id].append(grade)
    return grades


def topic_scores(student, scope: Scope) -> dict[int, TopicScore]:
    """{topic id: TopicScore} for every Topic in scope, in creation order."""
    grades = _counted_grades(student, scope)
    result = {}
    for topic in _topics(student, scope):
        window = grades.get(topic.id, [])
        result[topic.id] = TopicScore(topic=topic, answers=len(window), mean=rules.topic_mean(window))
    return result


def weak_of(scores) -> list[TopicScore]:
    """The Weak topics among `scores` (in creation order): lowest first, ties in creation order."""
    return sorted((s for s in scores if s.is_weak), key=lambda s: s.score)


def weak_topics(student, scope: Scope) -> list[TopicScore]:
    """Weak topics in scope (FR-17): score below WEAK_BELOW, lowest first."""
    return weak_of(topic_scores(student, scope).values())


def weak_first(scores) -> list[TopicScore]:
    """Weak topics first (lowest first), then the rest in creation order (P04, D10)."""
    scores = list(scores)
    weak = weak_of(scores)
    return weak + [s for s in scores if not s.is_weak]


def course_scores(student, scope: Scope | None = None) -> dict[int, CourseScore]:
    """{course id: CourseScore} for every Course with a Topic in scope; a Course without Topics is
    left out (callers read a missing key as «no score»)."""
    scope = scope or Scope.all()
    by_course: dict[int, list[TopicScore]] = defaultdict(list)
    for score in topic_scores(student, scope).values():
        by_course[score.topic.course_id].append(score)
    return {
        course_id: CourseScore(course_id=course_id, mean=rules.course_mean([t.mean for t in topics]), topics=topics)
        for course_id, topics in by_course.items()
    }


def course_score(student, course_id: int) -> CourseScore:
    """One Course's score; an empty one when it has no Topics."""
    return course_scores(student, Scope(course_id=course_id)).get(course_id) or CourseScore(course_id, None)


# ---- Next step (FR-28, AD-10) ----------------------------------------------------------------


@dataclass(frozen=True)
class NextStep:
    """One next-step-band: the attribute names `components/next_step_band.html` reads.

    `why` is safe HTML with the numbers in <b>; `action_url` is always a GET page or dialog."""

    number: int
    unit: str
    heading: str
    why: str
    minutes: str
    button_label: str
    action_url: str
    method: str = "get"
    is_calm = False


@dataclass(frozen=True)
class Calm:
    """The calm-message in place of the band: one line, no button."""

    text: str
    is_calm = True


def ready_question_counts(student, scope: Scope) -> dict[int, int]:
    """{topic id: ready Questions} in scope (FR-9: Questions count only from ready kilder)."""
    questions = Question.objects.filter(student=student, source__status=Status.READY)
    rows = (
        scope.filter(questions, "source__topic").order_by().values("source__topic_id").annotate(n=Count("id"))
    )
    return {row["source__topic_id"]: row["n"] for row in rows}


def _bold(value) -> str:
    return format_html("<b>{}</b>", value)


def _bold_percent(score: int) -> str:
    return format_html("<b>{} %</b>", score)


def _join(parts: list[str]) -> str:
    # Each part is built by format_html; the separators are literal, so the join is safe.
    return mark_safe(join_with_og(parts))


def _minutes(count: int, rate: float) -> str:
    return MESSAGES["band_minutes"].format(m=rules.band_minutes(count, rate))


def next_step(student, scope: Scope, *, here: str = "") -> NextStep | Calm | None:
    """The Next step for a page (FR-28): Hjem (`Scope.all()`), P04 (one fag) or P05 (one tema).

    Hjem and P04 take the first rule that applies within the scope: Due cards, Weak topics with
    ready Questions, a Topic without Sources, else a calm-message. P05 offers a Quiz when the Topic
    has ready Questions. None where the page's empty-state carries the action. `here` is the page's
    own URL, where a Review returns («Avslutt»).
    """
    if scope.topic_id is not None:
        return _quiz_step(student, scope)
    # Hjem with no fag and P04 with no Topics have no band: their empty-states carry the action.
    topics = list(
        _topics(student, scope).select_related("course").order_by("course__created_at", "course_id", "created_at", "id")
    )
    if not topics and (scope.course_id or not Course.objects.for_student(student).exists()):
        return None
    course = topics[0].course if scope.course_id else None
    here = here or (reverse("web:course", args=[course.id]) if course else reverse("web:home"))
    return (
        _due_step(student, scope, course, here)
        or _weak_step(student, scope)
        or _source_step(student, scope, topics)
        or _calm(student, scope, course)
    )


def _due_step(student, scope: Scope, course, here: str) -> NextStep | None:
    """Rule 1: Due cards, per fag on Hjem and per tema on P04, most first, then by name."""
    by = "flashcard__source__topic" if course else "flashcard__source__topic__course"
    rows = (
        review_services.due_cards(student, scope)
        .order_by()
        .values(f"{by}_id", f"{by}__name")
        .annotate(n=Count("id"))
    )
    counts = sorted(((row[f"{by}__name"], row["n"]) for row in rows), key=lambda item: (-item[1], item[0]))
    total = sum(n for _, n in counts)
    if not total:
        return None
    params = {"course": course.id, "next": here} if course else {"next": here}
    if course:
        heading = MESSAGES["next_due_heading_course"].format(fag=course.name)
    else:
        heading = MESSAGES["next_due_heading_all"]
    parts = [format_html("{} {}", name, _bold(n)) for name, n in counts]
    return NextStep(
        number=total,
        unit=MESSAGES["next_unit_cards"],
        heading=heading,
        why=format_html(MESSAGES["next_due_why"], n=_bold(total), parts=_join(parts)),
        minutes=_minutes(total, rules.CARD_MINUTES),
        button_label=MESSAGES["next_due_button"],
        action_url=f"{reverse('review:start')}?{urlencode(params)}",
    )


def _weak_step(student, scope: Scope) -> NextStep | None:
    """Rule 2: Weak topics that have ready Questions (a Weak topic without any does not count)."""
    ready = ready_question_counts(student, scope)
    weak = [s for s in weak_topics(student, scope) if ready.get(s.topic.id)]
    if not weak:
        return None
    if scope.course_id:
        course_id = scope.course_id
        in_course = weak
        count = "next_weak_why_course_one" if len(weak) == 1 else "next_weak_why_course_other"
        parts = [format_html("{} {}", s.topic.name, _bold_percent(s.score)) for s in weak]
        heading = MESSAGES["next_weak_heading_course"]
        why = format_html(MESSAGES[count], t=_bold(len(weak)), parts=_join(parts))
    else:
        order = {course_id: i for i, course_id in enumerate(Course.objects.for_student(student).values_list("id", flat=True))}
        # Lowest first; ties go to the fag created first, then the Topic created first (stable sort).
        weakest = min(weak, key=lambda s: (s.score, order[s.topic.course_id]))
        course_id = weakest.topic.course_id
        in_course = [s for s in weak if s.topic.course_id == course_id]
        count = "next_weak_why_all_one" if len(weak) == 1 else "next_weak_why_all_other"
        heading = MESSAGES["next_weak_heading_all"].format(fag=weakest.topic.course.name)
        why = format_html(
            MESSAGES[count], t=_bold(len(weak)), tema=weakest.topic.name, score=_bold_percent(weakest.score)
        )
    questions = sum(ready[s.topic.id] for s in in_course)
    return NextStep(
        number=questions,
        unit=MESSAGES["next_unit_questions"],
        heading=heading,
        why=why,
        minutes=_minutes(questions, rules.QUESTION_MINUTES),
        button_label=MESSAGES["next_weak_button"],
        action_url=reverse("web:weak_quiz", args=[course_id]),
    )


def _source_step(student, scope: Scope, topics: list[Topic]) -> NextStep | None:
    """Rule 3: the first Topic without Sources (fag creation order, then Topic creation order)."""
    with_sources = set(
        scope.filter(Source.objects.for_student(student), "topic").values_list("topic_id", flat=True).distinct()
    )
    empty = next((t for t in topics if t.id not in with_sources), None)
    if empty is None:
        return None
    if scope.course_id:
        why = format_html(MESSAGES["next_source_why_course"], tema=empty.name)
    else:
        why = format_html(MESSAGES["next_source_why_all"], tema=empty.name, fag=empty.course.name)
    return NextStep(
        number=1,
        unit=MESSAGES["next_unit_source"],
        heading=MESSAGES["next_source_heading"].format(tema=empty.name),
        why=why,
        minutes=_minutes(1, rules.SOURCE_MINUTES),
        button_label=MESSAGES["next_source_button"],
        # D04 «Før du laster opp» comes first when it has not been accepted (FR-22).
        action_url=reverse("studymat:add_source", args=[empty.id]),
    )


def _calm(student, scope: Scope, course) -> Calm:
    """Rule 4: nothing to do, and when the next card in scope is due."""
    due = review_services.next_due_date(student, scope)
    key = "next_calm_course" if course else "next_calm_all"
    if due is None:
        key += "_none"
    return Calm(MESSAGES[key].format(fag=course.name if course else "", dato=time.long_date(due) if due else ""))


def _quiz_step(student, scope: Scope) -> NextStep | None:
    """P05: a Quiz in the Topic when it has ready Questions (D06's default count)."""
    available = ready_question_counts(student, scope).get(scope.topic_id, 0)
    if not available:
        return None
    mastery = topic_scores(student, scope)[scope.topic_id]
    n = _bold(available)
    plural = "_one" if available == 1 else "_other"
    if mastery.score is None:
        why = format_html(MESSAGES["next_quiz_why_none" + plural], n=n)
    else:
        key = "next_quiz_why_weak" if mastery.is_weak else "next_quiz_why_scored"
        why = format_html(MESSAGES[key + plural], score=_bold_percent(mastery.score), n=n)
    count = default_count(available)
    return NextStep(
        number=count,
        unit=MESSAGES["next_unit_questions"],
        heading=MESSAGES["next_quiz_heading"].format(tema=mastery.topic.name),
        why=why,
        minutes=_minutes(count, rules.QUESTION_MINUTES),
        button_label=MESSAGES["next_quiz_button"],
        action_url=reverse("quiz:start", args=[scope.topic_id]),
    )
