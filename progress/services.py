"""Topic score, Course score and Weak topics, computed on read (AD-10, FR-16, FR-17).

Nothing is stored. One query fetches the counted Answers of a scope, newest first, and
`progress.rules` does the arithmetic. Every page reads its figures from here.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from fractions import Fraction

from courses.models import Topic
from courses.scope import Scope
from progress import rules
from quiz.models import Answer, QuizKind
from quiz.rules import WEIGHTS


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
