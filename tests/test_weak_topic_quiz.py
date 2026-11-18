"""CAP-10, FR-17 (story 12): D10 «Øv på svake temaer» — the topic-picker and its Practice-mode Quiz."""

import re

import pytest
from django.test import Client
from django.urls import reverse

from courses import services as courses_services
from courses.models import Source, Status
from quiz import services as quiz_services
from quiz.models import Quiz, QuizKind, QuizQuestion
from studymat.models import Question
from tests.test_progress import pct, seed, text_of
from tests.test_topic_page import ready_source

pytestmark = pytest.mark.django_db

DIALOG = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "dialog"}


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
def abc(ida, databaser):
    """A (created first, 80 %), B (40 %), C (55 %), with 5, 5 and 10 ready Questions."""
    a = courses_services.create_topic(databaser, "A")
    b = courses_services.create_topic(databaser, "B")
    c = courses_services.create_topic(databaser, "C")
    seed(ida, a, pct(4, 5))
    seed(ida, b, pct(2, 5))
    seed(ida, c, ["correct"] * 5 + ["partial"] + ["incorrect"] * 4)
    return a, b, c


def url(course):
    return reverse("web:weak_quiz", args=[course.id])


def checkboxes(body: str) -> list[tuple[str, bool]]:
    """(topic id, checked) per topic-picker row, in order."""
    return [
        (m.group(1), "checked" in m.group(0))
        for m in re.finditer(r'<input type="checkbox" name="topics" value="(\d+)"[^>]*>', body)
    ]


def ready_ids(topic) -> set[int]:
    return set(Question.objects.filter(source__topic=topic, source__status=Status.READY).values_list("id", flat=True))


def test_fr17_d10_lists_weak_first_preselected_then_the_rest(client_ida, databaser, abc):
    a, b, c = abc
    body = client_ida.get(url(databaser), **DIALOG).content.decode()
    assert "<dialog" in body
    assert checkboxes(body) == [(str(b.id), True), (str(c.id), True), (str(a.id), False)]
    text = text_of(body)
    assert "Øv på svake temaer" in text
    assert "Temaene som trenger øving er valgt. Svakeste først." in text
    assert "2 temaer valgt · 15 spørsmål" in text
    assert "5 spørsmål" in text and "Mestring 40 %" in text and "Trenger øving" in text
    assert "Start quiz" in text and "Avbryt" in text
    assert 'data-one="{t} tema valgt · {q} spørsmål"' in body
    assert 'data-other="{t} temaer valgt · {q} spørsmål"' in body


def test_fr17_d10_is_a_full_page_without_htmx(client_ida, databaser, abc):
    body = client_ida.get(url(databaser)).content.decode()
    assert "<dialog" not in body and 'class="dialog dialog--page"' in body
    assert "<title>Øv på svake temaer – Databaser – AI Study Buddy</title>" in body


def test_fr17_d10_leaves_out_topics_without_ready_questions(client_ida, ida, databaser, abc):
    empty = courses_services.create_topic(databaser, "Ingen kilder")
    failed = courses_services.create_topic(databaser, "Feilet")
    source = ready_source(failed, "f.pdf")
    Source.objects.filter(pk=source.pk).update(status=Status.FAILED)
    ids = [topic_id for topic_id, _ in checkboxes(client_ida.get(url(databaser)).content.decode())]
    assert str(empty.id) not in ids and str(failed.id) not in ids


def test_fr17_d10_choosing_a_and_b_holds_only_their_ready_questions(client_ida, ida, databaser, abc):
    a, b, c = abc
    response = client_ida.post(url(databaser), {"topics": [a.id, b.id], "start_token": "tok"})
    quiz = Quiz.objects.get(student=ida, start_token="tok")
    assert response.status_code == 302 and response.url == reverse("quiz:resume", args=[quiz.id])
    held = set(QuizQuestion.objects.filter(quiz=quiz).values_list("question_id", flat=True))
    assert held == ready_ids(a) | ready_ids(b)
    assert sorted(QuizQuestion.objects.filter(quiz=quiz).values_list("position", flat=True)) == list(range(1, 11))
    assert quiz.kind == QuizKind.PRACTICE and quiz.course_id == databaser.id
    assert quiz.return_url == reverse("web:course", args=[databaser.id])


def test_fr17_d10_is_idempotent_on_the_start_token(client_ida, ida, databaser, abc):
    a, b, _ = abc
    client_ida.post(url(databaser), {"topics": [a.id], "start_token": "same"})
    client_ida.post(url(databaser), {"topics": [b.id], "start_token": "same"})
    assert Quiz.objects.filter(student=ida).exclude(start_token__startswith="seed-").count() == 1


def test_fr17_d10_under_htmx_answers_with_hx_location(client_ida, ida, databaser, abc):
    a, _, _ = abc
    response = client_ida.post(url(databaser), {"topics": [a.id], "start_token": "hx"}, **DIALOG)
    quiz = Quiz.objects.get(student=ida, start_token="hx")
    assert reverse("quiz:resume", args=[quiz.id]) in response["HX-Location"]


def test_fr17_d10_nothing_chosen_is_a_form_error_and_no_quiz(client_ida, ida, databaser, abc):
    before = Quiz.objects.count()
    body = client_ida.post(url(databaser), {"start_token": "none"}, **DIALOG).content.decode()
    assert "Velg minst ett tema." in text_of(body)
    assert "<dialog" in body
    assert "0 temaer valgt · 0 spørsmål" in text_of(body)
    assert Quiz.objects.count() == before


def test_fr17_d10_foreign_topic_ids_are_ignored(client_ida, ida, databaser, abc, student):
    a, _, _ = abc
    other_course = courses_services.create_course(ida, "Statistikk")
    other = courses_services.create_topic(other_course, "Annet")
    ready_source(other, "o.pdf", questions=("Annet?",))
    jonas = student("jonas@example.no")
    jonas_topic = courses_services.create_topic(courses_services.create_course(jonas, "Hemmelig"), "J")
    ready_source(jonas_topic, "j.pdf", questions=("Jonas?",))
    client_ida.post(url(databaser), {"topics": [a.id, other.id, jonas_topic.id], "start_token": "mix"})
    quiz = Quiz.objects.get(student=ida, start_token="mix")
    held = set(QuizQuestion.objects.filter(quiz=quiz).values_list("question_id", flat=True))
    assert held == ready_ids(a)


def test_fr17_d10_only_foreign_topic_ids_is_the_form_error(client_ida, ida, databaser, abc, student):
    jonas = student("jonas@example.no")
    jonas_topic = courses_services.create_topic(courses_services.create_course(jonas, "Hemmelig"), "J")
    ready_source(jonas_topic, "j.pdf", questions=("Jonas?",))
    before = Quiz.objects.count()
    body = client_ida.post(url(databaser), {"topics": [jonas_topic.id, "x"], "start_token": "f"}).content.decode()
    assert "Velg minst ett tema." in text_of(body)
    assert Quiz.objects.count() == before


def test_fr17_d10_another_students_course_is_404(client_ida, student):
    jonas = student("jonas@example.no")
    course = courses_services.create_course(jonas, "Hemmelig")
    ready_source(courses_services.create_topic(course, "J"), "j.pdf")
    assert client_ida.get(url(course)).status_code == 404
    assert client_ida.post(url(course), {"topics": [], "start_token": "x"}).status_code == 404


def test_fr17_d10_without_ready_questions_goes_back_to_p04(client_ida, databaser):
    courses_services.create_topic(databaser, "Tomt")
    response = client_ida.get(url(databaser))
    assert response.status_code == 302 and response.url == reverse("web:course", args=[databaser.id])


def test_fr17_start_quiz_from_topics_service_ignores_other_courses(ida, databaser, abc):
    a, _, _ = abc
    other = courses_services.create_topic(courses_services.create_course(ida, "Statistikk"), "Annet")
    ready_source(other, "o.pdf")
    assert quiz_services.start_quiz_from_topics(ida, databaser, [other.id], "s1", "/") is None
    quiz = quiz_services.start_quiz_from_topics(ida, databaser, [a.id, other.id], "s2", "/")
    assert set(QuizQuestion.objects.filter(quiz=quiz).values_list("question_id", flat=True)) == ready_ids(a)


def test_fr10_start_quiz_keeps_its_behaviour(ida, databaser, abc):
    a, _, _ = abc
    quiz = quiz_services.start_quiz(ida, a, 3, "d06", "/x")
    assert QuizQuestion.objects.filter(quiz=quiz).count() == 3
    assert quiz_services.start_quiz(ida, a, 3, "d06", "/x") == quiz


def test_fr17_d10_none_left_at_start_is_the_form_error(client_ida, ida, databaser, abc, monkeypatch):
    a, _, _ = abc
    # The chosen Topics lose their ready Questions between the form check and the start.
    monkeypatch.setattr("web.views.quiz_services.start_quiz_from_topics", lambda *args, **kwargs: None)
    before = Quiz.objects.count()
    response = client_ida.post(url(databaser), {"topics": [a.id], "start_token": "gone"}, **DIALOG)
    assert response.status_code == 200
    body = response.content.decode()
    assert "<dialog" in body and "Velg minst ett tema." in text_of(body)
    assert Quiz.objects.count() == before


def test_fr17_d10_footer_is_singular_for_one_preselected_topic(client_ida, ida, databaser):
    weak = courses_services.create_topic(databaser, "Svak")
    strong = courses_services.create_topic(databaser, "Sterk")
    seed(ida, weak, pct(2, 5))
    seed(ida, strong, pct(4, 5))
    body = client_ida.get(url(databaser), **DIALOG).content.decode()
    assert checkboxes(body) == [(str(weak.id), True), (str(strong.id), False)]
    assert "1 tema valgt · 5 spørsmål" in text_of(body)
