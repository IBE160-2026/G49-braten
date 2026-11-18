"""The only writes to Quizzes and Answers (CAP-7, FR-10 to FR-12).

Grading runs synchronously and outside any transaction (AD-19): the Answer is saved first (its own
committed write), then graded, then the Grade is written. Multiple-choice is graded in code;
Free-text goes through `ai.gateway.grade_free_text`, which never counts toward the daily limit.
"""

import logging
import random

from django.db import IntegrityError, transaction
from django.utils.http import urlencode

from ai import gateway
from ai.errors import AIError
from ai.schemas import GradeRequest
from core import time
from core.messages import MESSAGES
from courses.models import Status, Topic
from quiz.models import Answer, Quiz, QuizKind, QuizQuestion
from quiz.rules import Grade, grade_choice
from studymat import services as studymat_services
from studymat.models import Question, QuestionKind

logger = logging.getLogger(__name__)

# The query parameter on `return_url` that names a finished Quiz for the Quiz tab's note.
FINISHED_PARAM = "quiz"


def available_questions(student, topic: Topic):
    """The Topic's Questions from ready Sources only (FR-9: not used until ready)."""
    return Question.objects.filter(student=student, source__topic=topic, source__status=Status.READY)


def start_quiz(student, topic: Topic, n: int, start_token: str, return_url: str) -> Quiz | None:
    """A Practice-mode Quiz of `n` random ready Questions, `n` clamped to 1..available.

    Idempotent on `start_token`: the same token returns the same Quiz. None when the Topic has no
    ready Questions (nothing is created).
    """
    existing = Quiz.objects.filter(student=student, start_token=start_token).first()
    if existing is not None:
        return existing
    ids = list(available_questions(student, topic).values_list("id", flat=True))
    if not ids:
        return None
    random.shuffle(ids)
    chosen = ids[: max(1, min(n, len(ids)))]
    try:
        with transaction.atomic():
            quiz = Quiz.objects.create(
                student=student,
                course_id=topic.course_id,
                kind=QuizKind.PRACTICE,
                return_url=return_url,
                start_token=start_token,
            )
            QuizQuestion.objects.bulk_create(
                QuizQuestion(student=student, quiz=quiz, question_id=question_id, position=position)
                for position, question_id in enumerate(chosen, start=1)
            )
    except IntegrityError:
        # A concurrent start with the same token won; use its Quiz.
        return Quiz.objects.get(student=student, start_token=start_token)
    logger.info("quiz start student=%s quiz=%s n=%s", student.pk, quiz.pk, len(chosen))
    return quiz


def save_answer(student, quiz: Quiz, question: Question, *, chosen_index: int | None = None, text: str = "") -> Answer:
    """Save and grade the Student's Answer. The first write is kept: a second call returns it as is."""
    assert quiz.student_id == student.pk and question.student_id == student.pk, "save_answer: not the Student's"
    answer, created = Answer.objects.get_or_create(
        quiz=quiz,
        question=question,
        defaults={
            "student": student,
            "chosen_index": chosen_index if question.kind == QuestionKind.MULTIPLE_CHOICE else None,
            "text": text if question.kind == QuestionKind.FREE_TEXT else "",
            "answered_at": time.now(),
        },
    )
    if not created:
        return answer
    _grade(student, answer, question)
    answer.refresh_from_db()
    return answer


def regrade(student, answer: Answer) -> Answer:
    """Grade a not-graded (or pending) Free-text Answer again, with the same text."""
    assert answer.student_id == student.pk, "regrade: not the Student's Answer"
    if answer.grade not in (None, Grade.NOT_GRADED):
        return answer
    _grade(student, answer, answer.question)
    answer.refresh_from_db()
    return answer


# The Grades a Student may set as an override (FR-12); also the AI Grades that may be overridden.
OVERRIDABLE = (Grade.CORRECT, Grade.PARTIAL, Grade.INCORRECT)


def can_override(answer: Answer | None) -> bool:
    """A graded Free-text Answer: never Multiple-choice, «Ikke rettet» or pending (FR-12)."""
    return (
        answer is not None
        and answer.question.kind == QuestionKind.FREE_TEXT
        and answer.grade in OVERRIDABLE
    )


def override_grade(student, answer: Answer, grade: str | None) -> Answer:
    """The only writer of `Answer.override_grade` (FR-12).

    `None`, or the AI Grade itself, clears the override. Only `override_grade` is written: the AI
    Grade, its Explanation and `answered_at` stay. Any other case (Multiple-choice, not graded,
    pending, an unknown value) leaves the row as it is.
    """
    assert answer.student_id == student.pk, "override_grade: not the Student's Answer"
    if not can_override(answer):
        return answer
    if grade is not None and grade not in OVERRIDABLE:
        return answer
    value = None if grade is None or grade == answer.grade else grade
    Answer.objects.filter(pk=answer.pk).update(override_grade=value)
    answer.refresh_from_db()
    logger.info("quiz override student=%s answer=%s overridden=%s", student.pk, answer.pk, value is not None)
    return answer


def _grade(student, answer: Answer, question: Question) -> None:
    if question.kind == QuestionKind.MULTIPLE_CHOICE:
        options = question.options or []
        chosen = answer.chosen_index
        explanation = options[chosen].get("explanation", "") if chosen is not None and chosen < len(options) else ""
        fields = {
            "grade": grade_choice(chosen, question.correct_index),
            "explanation": explanation,
            "is_mock": False,
            "failure": "",
        }
    else:
        fields = _grade_free_text(student, answer, question)
    Answer.objects.filter(pk=answer.pk).update(**fields)


def _grade_free_text(student, answer: Answer, question: Question) -> dict:
    try:
        request = GradeRequest(
            prompt=question.prompt,
            model_answer=question.model_answer,
            answer=answer.text,
            source_text=_source_text(question),
            language=question.source.language,
        )
        result = gateway.grade_free_text(student, request)
    except AIError as error:
        return {"grade": Grade.NOT_GRADED, "explanation": "", "is_mock": False, "failure": error.code}
    except Exception:
        # Never leave a pending Answer behind: an unexpected failure reads as «Ikke rettet».
        logger.exception("quiz grade student=%s answer=%s outcome=error", student.pk, answer.pk)
        return {"grade": Grade.NOT_GRADED, "explanation": "", "is_mock": False, "failure": "provider_unavailable"}
    return {
        "grade": result.grade,
        "explanation": result.explanation,
        "is_mock": gateway.mode() == gateway.MOCK,
        "failure": "",
    }


def _source_text(question: Question) -> str:
    """The Source text at the Question's Reference, or its quote when that Location is gone."""
    for location in studymat_services.locations(question.source):
        if location.index == question.location_index:
            return location.text
    return question.quote


# ---- Reading a Quiz -----------------------------------------------------------------------


def positions(quiz: Quiz) -> list[int]:
    """The positions still in the Quiz, in order (a deleted Question leaves a gap)."""
    return list(QuizQuestion.objects.filter(quiz=quiz).order_by("position").values_list("position", flat=True))


def next_position(quiz: Quiz, after: int) -> int | None:
    """The next existing position after `after`, or None at the end."""
    return (
        QuizQuestion.objects.filter(quiz=quiz, position__gt=after)
        .order_by("position")
        .values_list("position", flat=True)
        .first()
    )


def first_unanswered(quiz: Quiz) -> int | None:
    """Where resuming lands: the first position without an Answer, or None when all are answered."""
    answered = Answer.objects.filter(quiz=quiz).values("question_id")
    return (
        QuizQuestion.objects.filter(quiz=quiz)
        .exclude(question_id__in=answered)
        .order_by("position")
        .values_list("position", flat=True)
        .first()
    )


def finished_url(quiz: Quiz) -> str:
    """`return_url` naming this Quiz, so the Quiz tab shows its note."""
    separator = "&" if "?" in quiz.return_url else "?"
    return f"{quiz.return_url}{separator}{urlencode({FINISHED_PARAM: quiz.pk})}"


def finish_note(student, quiz_id) -> str:
    """«Quizen er lagret. k av N riktige.» for the Student's Quiz `quiz_id`; "" for anything else.

    k counts effective Grades that are `correct`; N counts the Questions still in the Quiz.
    """
    try:
        pk = int(quiz_id)
    except (TypeError, ValueError):
        return ""
    quiz = Quiz.objects.for_student(student).filter(pk=pk).first()
    if quiz is None:
        return ""
    total = QuizQuestion.objects.filter(quiz=quiz).count()
    correct = Answer.objects.filter(quiz=quiz).with_effective_grade().filter(effective_grade=Grade.CORRECT).count()
    return MESSAGES["quiz_saved"].format(k=correct, n=total)
