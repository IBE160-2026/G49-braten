"""CAP-10, FR-16, FR-17 (story 12): Topic score, Course score and Weak topics, computed on read (AD-10),
and where they show: the fag-rail, the fag-switcher, Hjem, Fagoversikt (P04) and the Tema page (P05)."""

import datetime
import itertools
import re
from fractions import Fraction

import pytest
from django.test import Client
from django.urls import reverse

from core import time
from courses import services as courses_services
from courses.models import Source, Status
from courses.scope import Scope
from progress import rules
from progress import services as progress
from quiz.models import Answer, Quiz, QuizKind, QuizQuestion
from quiz.rules import Grade
from studymat.models import Question
from tests.test_topic_page import ready_source

pytestmark = pytest.mark.django_db

C, P, I, N = Grade.CORRECT, Grade.PARTIAL, Grade.INCORRECT, Grade.NOT_GRADED
BASE = datetime.datetime(2026, 11, 17, 12, 0, tzinfo=time.OSLO)
_tick = itertools.count()
_token = itertools.count()


def seed(student, topic, grades, *, kind=QuizKind.PRACTICE, parent=None, start=None) -> Quiz:
    """One Quiz in `topic` with one Answer per Grade (None: pending), answered in list order, each
    later than every Answer seeded before it."""
    source = ready_source(topic, f"k{next(_token)}.pdf", questions=[f"Q{i}" for i in range(len(grades))])
    questions = list(Question.objects.filter(source=source).order_by("id"))
    quiz = Quiz.objects.create(
        student=student, course=topic.course, kind=kind, parent_quiz=parent, return_url="/",
        start_token=f"seed-{next(_token)}", started_at=start or BASE + datetime.timedelta(minutes=next(_tick)),
    )  # fmt: skip
    for position, (question, grade) in enumerate(zip(questions, grades), start=1):
        QuizQuestion.objects.create(student=student, quiz=quiz, question=question, position=position)
        Answer.objects.create(
            student=student, quiz=quiz, question=question, grade=grade, text="svar",
            answered_at=BASE + datetime.timedelta(minutes=next(_tick)),
        )  # fmt: skip
    return quiz


def pct(correct: int, total: int) -> list[str]:
    return [C] * correct + [I] * (total - correct)


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def client_ida(ida):
    client = Client()
    client.force_login(ida)
    return client


@pytest.fixture
def databaser(ida):
    return courses_services.create_course(ida, "Databaser", "DAT102")


@pytest.fixture
def three(databaser):
    """Normalisering 40 %, Transaksjoner 55 %, SQL 80 % — created SQL, Transaksjoner, Normalisering."""
    ida = databaser.student
    sql = courses_services.create_topic(databaser, "SQL")
    transaksjoner = courses_services.create_topic(databaser, "Transaksjoner")
    normalisering = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, normalisering, pct(2, 5))
    seed(ida, transaksjoner, [C] * 5 + [P] + [I] * 4)
    seed(ida, sql, pct(4, 5))
    return normalisering, transaksjoner, sql


def score_of(student, topic) -> int | None:
    return progress.topic_scores(student, Scope(topic_id=topic.id))[topic.id].score


# ---- Rules --------------------------------------------------------------------------------


def test_fr16_constants():
    assert (rules.WINDOW, rules.MIN_ANSWERS, rules.WEAK_BELOW) == (20, 5, 60)


@pytest.mark.parametrize(
    ("mean", "expected"),
    [(Fraction(575, 1000), 58), (Fraction(23, 40), 58), (Fraction(5745, 10000), 57), (Fraction(1, 2), 50),
     (Fraction(0), 0), (Fraction(1), 100), (Fraction(2, 3), 67), (Fraction(1, 200), 1)],
)  # fmt: skip
def test_fr16_percent_rounds_half_up(mean, expected):
    assert rules.percent(mean) == expected


def test_fr17_weak_compares_the_shown_percent():
    # A 59.6 % mean shows «60 %» and is not Weak, so a tag never sits beside «60 %».
    assert rules.percent(Fraction(596, 1000)) == 60
    assert not rules.is_weak(rules.percent(Fraction(596, 1000)))
    assert rules.is_weak(59)
    assert not rules.is_weak(None)


def test_fr16_topic_mean_needs_five_and_keeps_the_first_twenty():
    assert rules.topic_mean([C, C, C, C]) is None
    assert rules.topic_mean([C, P, I, I, I]) == Fraction(3, 10)
    assert rules.topic_mean([C] * 20 + [I] * 5) == 1


def test_fr16_course_mean_skips_topics_without_a_score():
    assert rules.course_mean([None, None]) is None
    assert rules.course_mean([Fraction(2, 5), Fraction(4, 5), None]) == Fraction(3, 5)


# ---- Topic score (I/O matrix) -------------------------------------------------------------


def test_fr17_seeded_weak_topics_lowest_first(ida, databaser, three):
    normalisering, transaksjoner, sql = three
    scores = progress.topic_scores(ida, Scope(course_id=databaser.id))
    assert [scores[t.id].score for t in (normalisering, transaksjoner, sql)] == [40, 55, 80]
    weak = progress.weak_topics(ida, Scope(course_id=databaser.id))
    assert [w.topic for w in weak] == [normalisering, transaksjoner]
    assert not scores[sql.id].is_weak


def test_fr17_weak_ties_keep_creation_order(ida, databaser):
    a = courses_services.create_topic(databaser, "A")
    b = courses_services.create_topic(databaser, "B")
    seed(ida, b, pct(2, 5))
    seed(ida, a, pct(2, 5))
    assert [w.topic for w in progress.weak_topics(ida, Scope.all())] == [a, b]


def test_fr16_too_few_answers_is_no_score_and_not_weak(ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, topic, [I, I, I, I])
    score = progress.topic_scores(ida, Scope(topic_id=topic.id))[topic.id]
    assert score.score is None and score.answers == 4 and not score.is_weak
    assert progress.weak_topics(ida, Scope.all()) == []


def test_fr16_only_the_twenty_newest_count(ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, topic, [I] * 5)
    seed(ida, topic, [C] * 20)
    score = progress.topic_scores(ida, Scope(topic_id=topic.id))[topic.id]
    assert score.answers == 20 and score.score == 100


def test_fr16_newest_ties_on_answered_at_break_on_id(ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, topic, [C] * 20)
    newest = seed(ida, topic, [I])
    Answer.objects.filter(quiz=newest).update(answered_at=Answer.objects.exclude(quiz=newest).latest("answered_at").answered_at)
    # The Incorrect Answer has the higher id, so it is inside the window and one Correct falls out.
    assert score_of(ida, topic) == 95


def test_fr16_retry_round_answers_never_count(ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    parent = seed(ida, topic, pct(2, 5))
    seed(ida, topic, [C] * 10, kind=QuizKind.RETRY, parent=parent)
    assert score_of(ida, topic) == 40


def test_fr16_not_graded_and_pending_answers_are_ignored(ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, topic, pct(2, 5) + [N, N, None, None])
    score = progress.topic_scores(ida, Scope(topic_id=topic.id))[topic.id]
    assert score.answers == 5 and score.score == 40


def test_fr16_an_override_counts_at_once(ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    quiz = seed(ida, topic, [P, P, P, P, P])
    assert score_of(ida, topic) == 50
    Answer.objects.filter(quiz=quiz).update(override_grade=C)
    assert score_of(ida, topic) == 100


def test_fr16_override_from_incorrect_counts_as_correct(ida, databaser):
    # The effective Grade is the override: an Incorrect AI Grade overridden to Correct counts as Correct.
    topic = courses_services.create_topic(databaser, "Normalisering")
    quiz = seed(ida, topic, [I] * 5)
    Answer.objects.filter(quiz=quiz).update(override_grade=C)
    assert score_of(ida, topic) == 100


def test_fr16_deleted_questions_take_their_answers_with_them(ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    quiz = seed(ida, topic, [I] * 5 + [C] * 5)
    assert score_of(ida, topic) == 50
    Question.objects.filter(answers__quiz=quiz, answers__grade=I).delete()
    assert score_of(ida, topic) == 100


def test_fr16_another_students_answers_never_count(ida, databaser, student):
    jonas = student("jonas@example.no")
    jonas_topic = courses_services.create_topic(courses_services.create_course(jonas, "Hemmelig"), "X")
    seed(jonas, jonas_topic, [C] * 5)
    scores = progress.topic_scores(ida, Scope.all())
    assert jonas_topic.id not in scores
    assert progress.course_scores(ida) == {}


# ---- Course score -------------------------------------------------------------------------


def test_fr16_course_score_is_the_mean_of_topics_with_a_score(ida, databaser):
    a = courses_services.create_topic(databaser, "A")
    b = courses_services.create_topic(databaser, "B")
    courses_services.create_topic(databaser, "Uten data")
    seed(ida, a, pct(2, 5))
    seed(ida, b, pct(4, 5))
    assert progress.course_score(ida, databaser.id).score == 60


def test_fr16_course_score_rounds_the_unrounded_mean(ida, databaser):
    # 57.5 % and 62.5 % (unrounded) average to 60 %; rounding each first (58, 63) would give 61 %.
    a = courses_services.create_topic(databaser, "A")
    b = courses_services.create_topic(databaser, "B")
    seed(ida, a, [C] * 11 + [P] + [I] * 8)  # 11.5 / 20
    seed(ida, b, [C] * 11 + [P, P, P] + [I] * 6)  # 12.5 / 20 = 62.5 %
    assert score_of(ida, a) == 58 and score_of(ida, b) == 63
    assert progress.course_score(ida, databaser.id).score == 60


def test_fr16_course_without_scored_topics_has_no_score(ida, databaser):
    courses_services.create_topic(databaser, "A")
    assert progress.course_score(ida, databaser.id).score is None
    empty = courses_services.create_course(ida, "Tomt")
    assert progress.course_score(ida, empty.id).score is None


# ---- Fag-rail and fag-switcher ------------------------------------------------------------


def rail_of(content: str) -> str:
    return content.split('<nav class="fag-rail"', 1)[1].split("</nav>", 1)[0]


def switcher_of(content: str) -> str:
    return content.split('<nav class="fag-switcher"', 1)[1].split("</nav>", 1)[0]


def text_of(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def test_fr16_rail_shows_the_course_score_and_names_it(client_ida, databaser, three):
    content = client_ida.get("/").content.decode()
    rail = rail_of(content)
    # 40, 55 and 80 average to 58.33 → 58 %.
    assert '<span class="fag-rail-pct">58 %</span>' in rail
    assert '<span class="rail-meter-fill" style="width: 58%"></span>' in rail
    assert "rail-meter--none" not in rail
    assert ", DAT102, mestring 58 % i snitt" in rail
    switcher = switcher_of(content)
    assert re.search(r'fag-switcher-option-meta" aria-hidden="true">\d+ i dag · 58 %<', switcher)
    assert "mestring 58 % i snitt" in switcher


def test_fr16_rail_without_a_score_is_dotted_and_says_so(client_ida, databaser):
    rail = rail_of(client_ida.get("/").content.decode())
    assert '<span class="fag-rail-pct">–</span>' in rail
    assert "rail-meter--none" in rail
    assert "mestring: ikke nok data ennå" in rail


# ---- Hjem ---------------------------------------------------------------------------------


def main_of(content: str) -> str:
    return content.split('<main id="main"', 1)[1].split("</main>", 1)[0]


def test_fr17_hjem_row_shows_mastery_practice_tag_and_weakest(client_ida, databaser, three):
    main = main_of(client_ida.get("/").content.decode())
    text = text_of(main)
    assert "Mestring 58 %" in text
    assert 'class="mastery-meter-fill" style="width: 58%"' in main
    assert "2 temaer trenger øving" in text
    assert "Svakest: Normalisering 40 %" in text
    assert "Mestring for et fag er snittet av temaene som har nok svar." in text


def test_fr17_hjem_row_with_one_weak_topic_says_one_tema(client_ida, ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, topic, pct(2, 5))
    text = text_of(main_of(client_ida.get("/").content.decode()))
    assert "1 tema trenger øving" in text


def test_fr16_hjem_row_without_data_says_not_enough_data(client_ida, databaser):
    text = text_of(main_of(client_ida.get("/").content.decode()))
    assert "Ikke nok data ennå" in text
    assert "trenger øving" not in text and "Svakest" not in text


def test_fr17_hjem_names_the_weakest_even_without_weak_topics(client_ida, ida, databaser):
    topic = courses_services.create_topic(databaser, "SQL")
    seed(ida, topic, pct(4, 5))
    text = text_of(main_of(client_ida.get("/").content.decode()))
    assert "Svakest: SQL 80 %" in text
    assert "trenger øving" not in text


# ---- Fagoversikt (P04) --------------------------------------------------------------------


def topic_names_in_order(main: str) -> list[str]:
    return re.findall(r'<span class="item-row-name">([^<]+)', main)


def test_fr17_p04_lists_weak_topics_first_with_tags_and_the_weak_quiz_button(client_ida, databaser, three):
    main = main_of(client_ida.get(reverse("web:course", args=[databaser.id])).content.decode())
    assert [n.strip() for n in topic_names_in_order(main)] == ["Normalisering", "Transaksjoner", "SQL"]
    rows = main.split('class="item-row topic-row"')[1:]
    assert "Trenger øving" in rows[0] and "Trenger øving" in rows[1] and "Trenger øving" not in rows[2]
    assert "Mestring <b>40 %</b>" in rows[0] and "Mestring <b>80 %</b>" in rows[2]
    text = text_of(main)
    assert "Mestring 58 % i snitt" in text
    assert "Mestring for et fag er snittet av temaene som har nok svar." in text
    assert "Øv på svake temaer (2)" in text
    assert f'href="{reverse("web:weak_quiz", args=[databaser.id])}"' in main


def test_fr17_p04_without_weak_topics_has_no_weak_quiz_button(client_ida, ida, databaser):
    topic = courses_services.create_topic(databaser, "SQL")
    seed(ida, topic, pct(4, 5))
    text = text_of(main_of(client_ida.get(reverse("web:course", args=[databaser.id])).content.decode()))
    assert "Øv på svake temaer" not in text and "Trenger øving" not in text
    assert "Mestring 80 % i snitt" in text


def test_fr17_p04_hides_the_weak_quiz_button_when_weak_topics_have_no_ready_questions(client_ida, ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, topic, pct(2, 5))
    Source.objects.filter(topic=topic).update(status=Status.GENERATING)
    text = text_of(main_of(client_ida.get(reverse("web:course", args=[databaser.id])).content.decode()))
    assert "Trenger øving" in text
    assert "Øv på svake temaer" not in text


def test_fr16_p04_without_data_says_not_enough_data_under_the_title(client_ida, databaser):
    main = main_of(client_ida.get(reverse("web:course", args=[databaser.id])).content.decode())
    head = main.split('class="page-mastery"', 1)[1].split("</div>", 1)[0]
    assert "Ikke nok data ennå" in head and "mastery-meter--none" in head


# ---- Tema (P05) ---------------------------------------------------------------------------


@pytest.mark.parametrize("tab", ["summary", "quiz", "selftest", "sources"])
def test_fr17_p05_shows_mastery_and_tag_under_the_title_on_every_tab(client_ida, databaser, three, tab):
    normalisering = three[0]
    main = main_of(client_ida.get(f"{reverse('web:topic', args=[normalisering.id])}?tab={tab}").content.decode())
    head = text_of(main.split('class="page-head-text"', 1)[1].split('role="tablist"', 1)[0])
    assert "Mestring 40 %" in head
    assert "Trenger øving" in head
    assert "Basert på de 20 siste svarene dine." in head


def test_fr16_p05_without_data_says_not_enough_data(client_ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    main = main_of(client_ida.get(reverse("web:topic", args=[topic.id])).content.decode())
    head = text_of(main.split('class="page-head-text"', 1)[1].split('role="tablist"', 1)[0])
    assert "Ikke nok data ennå" in head and "Trenger øving" not in head


# ---- Acceptance: an override shows everywhere at once ---------------------------------------


def test_fr16_override_updates_every_figure_on_reload(client_ida, ida, databaser):
    topic = courses_services.create_topic(databaser, "Normalisering")
    quiz = seed(ida, topic, [P] * 5 + [I] * 5)  # 25 %
    course_url = reverse("web:course", args=[databaser.id])
    content = client_ida.get(course_url).content.decode()
    assert '<span class="fag-rail-pct">25 %</span>' in rail_of(content)
    assert "Trenger øving" in main_of(content)
    Answer.objects.filter(quiz=quiz).update(override_grade=C)
    for url in ("/", course_url, reverse("web:topic", args=[topic.id])):
        content = client_ida.get(url).content.decode()
        rail = rail_of(content)
        assert '<span class="fag-rail-pct">100 %</span>' in rail
        assert "mestring 100 % i snitt" in rail
        assert "Trenger øving" not in main_of(content)
    main = main_of(client_ida.get(course_url).content.decode())
    head = text_of(main.split('class="page-mastery"', 1)[1].split("</div>", 1)[0])
    assert "Mestring 100 % i snitt" in head
    (row,) = main.split('class="item-row topic-row"')[1:]
    assert "Mestring <b>100 %</b>" in row
    assert "Mestring 100 %" in text_of(main_of(client_ida.get("/").content.decode()))
    topic_head = main_of(client_ida.get(reverse("web:topic", args=[topic.id])).content.decode())
    topic_head = text_of(topic_head.split('class="page-head-text"', 1)[1].split('role="tablist"', 1)[0])
    assert "Mestring 100 %" in topic_head
