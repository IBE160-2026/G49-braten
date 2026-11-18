"""The only writes to Quizzes and Answers (CAP-7, FR-10 to FR-12).

Grading runs synchronously and outside any transaction (AD-19): the Answer is saved first (its own
committed write), then graded, then the Grade is written. Multiple-choice is graded in code;
Free-text goes through `ai.gateway.grade_free_text`, which never counts toward the daily limit.
"""

import logging
import math
import random
from dataclasses import dataclass

from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef

from ai import gateway
from ai.errors import AIError
from ai.schemas import GradeRequest
from core import time
from courses.models import Status, Topic
from quiz.models import Answer, Quiz, QuizKind, QuizQuestion
from quiz.rules import Grade, grade_choice
from studymat import services as studymat_services
from studymat.models import Question, QuestionKind

logger = logging.getLogger(__name__)


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


# ---- P07 «Resultat» and «Øv på feilene» (FR-13, AD-9) ------------------------------------

# The effective Grades that put a Question in a Retry round. Not graded, pending and unanswered
# Questions are left out (FR-12, FR-13).
MISSED = (Grade.INCORRECT, Grade.PARTIAL)


def missed(quiz: Quiz) -> list[int]:
    """The Question ids whose effective Grade is incorrect or partial, in the Quiz's position order."""
    misses = Answer.objects.filter(quiz=quiz).with_effective_grade().filter(effective_grade__in=MISSED)
    return list(
        QuizQuestion.objects.filter(quiz=quiz, question_id__in=misses.values("question_id"))
        .order_by("position")
        .values_list("question_id", flat=True)
    )


def start_retry(student, quiz: Quiz) -> Quiz | None:
    """«Øv på feilene»: a Retry round of `quiz`'s missed Questions, in its order (no shuffle).

    Reuses the parent's Retry round that has no Answers yet (its Questions brought in line with the
    current misses, which an override may have changed), else creates one. None when nothing is
    missed (nothing is created). The round copies `course` and `return_url`.
    """
    assert quiz.student_id == student.pk, "start_retry: not the Student's Quiz"
    question_ids = missed(quiz)
    if not question_ids:
        return None
    unanswered = (
        Quiz.objects.filter(student=student, parent_quiz=quiz, kind=QuizKind.RETRY)
        .exclude(Exists(Answer.objects.filter(quiz=OuterRef("pk"))))
        .order_by("-id")
        .first()
    )
    if unanswered is not None:
        _set_questions(student, unanswered, question_ids)
        return unanswered
    # One token per round of this parent, so two concurrent POSTs create one round (the loser of the
    # unique constraint takes the winner's).
    rounds = Quiz.objects.filter(student=student, parent_quiz=quiz).count()
    token = f"retry-{quiz.pk}-{rounds + 1}"
    try:
        with transaction.atomic():
            round_ = Quiz.objects.create(
                student=student,
                course_id=quiz.course_id,
                kind=QuizKind.RETRY,
                parent_quiz=quiz,
                return_url=quiz.return_url,
                start_token=token,
            )
            _set_questions(student, round_, question_ids)
    except IntegrityError:
        twin = Quiz.objects.filter(
            student=student, start_token=token, kind=QuizKind.RETRY, parent_quiz=quiz
        ).first()
        if twin is None:
            raise
        return twin
    logger.info("quiz retry student=%s quiz=%s parent=%s n=%s", student.pk, round_.pk, quiz.pk, len(question_ids))
    return round_


def _set_questions(student, quiz: Quiz, question_ids: list[int]) -> None:
    """Positions 1..n for `question_ids`, unless the Quiz already has exactly these in this order."""
    current = list(QuizQuestion.objects.filter(quiz=quiz).order_by("position").values_list("question_id", flat=True))
    if current == question_ids:
        return
    with transaction.atomic():
        QuizQuestion.objects.filter(quiz=quiz).delete()
        QuizQuestion.objects.bulk_create(
            QuizQuestion(student=student, quiz=quiz, question_id=question_id, position=position)
            for position, question_id in enumerate(question_ids, start=1)
        )


@dataclass
class ResultRow:
    """One Question on P07. `number` is its display number (1-based among the remaining Questions)."""

    number: int
    position: int
    question: Question
    answer: Answer | None
    # The effective Grade (pending reads as not graded); "" when unanswered.
    grade: str
    missed: bool


@dataclass
class Result:
    rows: list[ResultRow]
    correct: int
    partial: int
    incorrect: int

    @property
    def total(self) -> int:
        return len(self.rows)

    @property
    def missed_numbers(self) -> list[int]:
        return [row.number for row in self.rows if row.missed]

    @property
    def all_correct(self) -> bool:
        return bool(self.rows) and self.correct == self.total

    @property
    def minutes(self) -> int:
        """«ca. {m} min» for a Retry round of the misses: 0.8 minutes per Question, rounded up."""
        return math.ceil(0.8 * len(self.missed_numbers))


def result(quiz: Quiz) -> Result:
    """Every Question still in the Quiz with its effective Grade, and the counts for P07."""
    quiz_questions = list(
        QuizQuestion.objects.filter(quiz=quiz).select_related("question__source").order_by("position")
    )
    answers = {answer.question_id: answer for answer in Answer.objects.filter(quiz=quiz)}
    misses = set(missed(quiz))
    rows = []
    for number, quiz_question in enumerate(quiz_questions, start=1):
        answer = answers.get(quiz_question.question_id)
        rows.append(
            ResultRow(
                number=number,
                position=quiz_question.position,
                question=quiz_question.question,
                answer=answer,
                grade=answer.shown_grade if answer is not None else "",
                missed=quiz_question.question_id in misses,
            )
        )
    grades = [row.grade for row in rows]
    return Result(
        rows=rows,
        correct=grades.count(Grade.CORRECT),
        partial=grades.count(Grade.PARTIAL),
        incorrect=grades.count(Grade.INCORRECT),
    )
