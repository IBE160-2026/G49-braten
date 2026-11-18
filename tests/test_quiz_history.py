"""CAP-8, FR-27 (story 12): «Tidligere quizer» on the Tema page's «Quiz» tab."""

import datetime

import pytest
from django.test import Client
from django.urls import reverse

from core import time
from courses import services as courses_services
from quiz import services as quiz_services
from quiz.models import Answer, QuizKind, QuizQuestion
from quiz.rules import Grade
from tests.test_progress import seed, text_of
from tests.test_topic_page import main_of, panel_of

pytestmark = pytest.mark.django_db

C, P, I = Grade.CORRECT, Grade.PARTIAL, Grade.INCORRECT
NOV_17 = datetime.datetime(2026, 11, 17, 23, 30, tzinfo=datetime.timezone.utc)  # 18 Nov in Oslo


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def client_ida(ida):
    client = Client()
    client.force_login(ida)
    return client


@pytest.fixture
def topic(ida):
    return courses_services.create_topic(courses_services.create_course(ida, "Databaser"), "Normalisering")


def quiz_tab(client, topic) -> str:
    return panel_of(main_of(client.get(f"{reverse('web:topic', args=[topic.id])}?tab=quiz").content.decode()))


def rows_of(panel: str) -> list[str]:
    return panel.split('<li class="quiz-history-row">')[1:]


def test_fr27_no_quiz_yet_says_so_and_has_no_retry_note(client_ida, topic):
    panel = quiz_tab(client_ida, topic)
    assert "Tidligere quizer" in panel
    assert "Du har ikke tatt en quiz i dette temaet ennå." in panel
    assert "teller ikke i mestringen" not in panel


def test_fr27_row_shows_date_counts_and_strip(client_ida, ida, topic):
    quiz = seed(ida, topic, [C, C, C, P, I, I], start=NOV_17)
    panel = quiz_tab(client_ida, topic)
    (row,) = rows_of(panel)
    text = text_of(row)
    assert "18. nov." in text
    assert "3 av 6 riktige · 1 delvis" in text
    assert "Øv på feilene" not in text.split("riktige")[0]
    assert row.count('class="result-slot result-slot--') == 6
    assert 'aria-label="Spørsmål 4: Delvis riktig"' in row
    assert "Runder med «Øv på feilene» teller ikke i mestringen." in text_of(panel)
    assert "Du har ikke tatt en quiz" not in panel
    # Newest with misses: «Øv på feilene (3)» POSTs to quiz:retry.
    assert "Øv på feilene (3)" in text
    assert f'action="{reverse("quiz:retry", args=[quiz.id])}"' in row


def test_fr27_no_partial_count_when_none_partial(client_ida, ida, topic):
    seed(ida, topic, [C, C, I])
    text = text_of(rows_of(quiz_tab(client_ida, topic))[0])
    assert "2 av 3 riktige" in text and "delvis" not in text


def test_fr27_newest_without_misses_links_to_the_result(client_ida, ida, topic):
    quiz = seed(ida, topic, [C, C])
    (row,) = rows_of(quiz_tab(client_ida, topic))
    assert "Se resultatet" in row and f'href="{reverse("quiz:result", args=[quiz.id])}"' in row
    assert "Øv på feilene (" not in row


def test_fr27_practice_then_retry_two_rows_retry_newest_and_only_it_offers_retry(client_ida, ida, topic):
    parent = seed(ida, topic, [C, I, P])
    round_ = quiz_services.start_retry(ida, parent)
    first = QuizQuestion.objects.filter(quiz=round_).order_by("position").first()
    Answer.objects.create(student=ida, quiz=round_, question=first.question, grade=I, answered_at=time.now())
    rows = rows_of(quiz_tab(client_ida, topic))
    assert len(rows) == 2
    newest, older = rows
    assert "Øv på feilene" in text_of(newest).split("av")[0]  # the Retry-round mark before the score
    assert "Øv på feilene (" in newest
    assert f'action="{reverse("quiz:retry", args=[round_.id])}"' in newest
    assert "Øv på feilene (" not in older
    assert f'href="{reverse("quiz:result", args=[parent.id])}"' in older
    assert "quiz-history-kind" not in older


def test_fr27_overridden_grades_are_marked_in_the_strip(client_ida, ida, topic):
    quiz = seed(ida, topic, [P, C, C])
    Answer.objects.filter(quiz=quiz, grade=P).update(override_grade=C)
    (row,) = rows_of(quiz_tab(client_ida, topic))
    assert "result-slot--correct result-slot--overridden" in row
    assert 'aria-label="Spørsmål 1: Riktig, endret av deg"' in row
    assert "3 av 3 riktige" in text_of(row)


def test_fr27_counts_are_over_the_whole_quiz_and_other_topics_quizzes_are_left_out(client_ida, ida, topic):
    other = courses_services.create_topic(topic.course, "SQL")
    seed(ida, other, [C, C])
    mixed = seed(ida, topic, [C, I])
    extra = seed(ida, other, [C, C, C])
    # Move `extra`'s Questions into `mixed`: a D10 Quiz spanning both Topics.
    for offset, qq in enumerate(QuizQuestion.objects.filter(quiz=extra).order_by("position"), start=3):
        QuizQuestion.objects.filter(pk=qq.pk).update(quiz=mixed, position=offset)
        Answer.objects.filter(quiz=extra, question=qq.question).update(quiz=mixed)
    rows = rows_of(quiz_tab(client_ida, topic))
    assert len(rows) == 1
    assert "4 av 5 riktige" in text_of(rows[0])
    assert len(rows_of(quiz_tab(client_ida, other))) == 2


def test_fr27_newest_first_by_started_at_then_id(ida, topic):
    a = seed(ida, topic, [C], start=NOV_17)
    b = seed(ida, topic, [C], start=NOV_17)
    c = seed(ida, topic, [C], start=NOV_17 - datetime.timedelta(days=1))
    assert [item.quiz for item in quiz_services.topic_history(ida, topic)] == [b, a, c]


def test_fr27_a_quiz_with_no_questions_left_is_skipped(ida, topic):
    quiz = seed(ida, topic, [C, I])
    kept = seed(ida, topic, [C])
    QuizQuestion.objects.filter(quiz=quiz).delete()
    assert [item.quiz for item in quiz_services.topic_history(ida, topic)] == [kept]


def test_fr27_another_students_quizzes_never_show(ida, topic, student):
    jonas = student("jonas@example.no")
    jonas_topic = courses_services.create_topic(courses_services.create_course(jonas, "X"), "Y")
    seed(jonas, jonas_topic, [C])
    assert quiz_services.topic_history(ida, topic) == []
    assert quiz_services.topic_history(ida, jonas_topic) == []


def test_fr27_is_retry_flag(ida, topic):
    parent = seed(ida, topic, [I])
    seed(ida, topic, [C], kind=QuizKind.RETRY, parent=parent)
    items = quiz_services.topic_history(ida, topic)
    assert [item.is_retry for item in items] == [True, False]


@pytest.mark.parametrize(
    ("moment", "expected"),
    [(datetime.datetime(2026, 11, 17, 23, 30, tzinfo=datetime.timezone.utc), "18. nov."),
     (datetime.datetime(2026, 5, 3, 10, 0, tzinfo=datetime.timezone.utc), "3. mai"),
     (datetime.date(2026, 12, 1), "1. des.")],
)  # fmt: skip
def test_ad12_short_date_is_the_oslo_date(moment, expected):
    assert time.short_date(moment) == expected
