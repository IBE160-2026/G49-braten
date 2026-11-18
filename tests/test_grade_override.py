"""FR-12 override and FR-24 on P06 (story 8b): «Endre vurdering» and «Slett spørsmålet» in the feedback panel."""

import json
import re
from urllib.parse import parse_qs, urlsplit

import pytest
from django.test import Client
from django.urls import reverse

from ai import gateway
from quiz import services
from quiz.models import Answer, QuizQuestion
from quiz.rules import Grade
from studymat.models import Question
from tests.test_quiz import (  # noqa: F401  (fixtures)
    CARD,
    DIALOG,
    client_ida,
    ida,
    jonas,
    make_quiz,
    now,
    position_of,
    question_url,
    return_url,
    sample,
    text_of,
    topic,
)

pytestmark = pytest.mark.django_db(transaction=True)


def override_url(quiz, position):
    return reverse("quiz:override", args=[quiz.id, position])


def graded(ida, quiz, kind="free_text", grade=Grade.INCORRECT, explanation="KI sier feil."):
    """A stored Answer at the first position of `kind`, with the AI Grade set to `grade`."""
    qq = position_of(quiz, kind)
    if kind == "free_text":
        answer = services.save_answer(ida, quiz, qq.question, text="mitt svar")
    else:
        answer = services.save_answer(ida, quiz, qq.question, chosen_index=0)
    Answer.objects.filter(pk=answer.pk).update(grade=grade, explanation=explanation)
    answer.refresh_from_db()
    return qq, answer


def menu_of(body: str) -> str:
    match = re.search(r'<div id="override-menu".*?</form>', body, re.S)
    return match.group(0) if match else ""


def current_items(body: str) -> list[str]:
    return re.findall(r'value="(\w+)" aria-current="true"', menu_of(body))


# ---- The service ----------------------------------------------------------------------------


def test_fr12_override_sets_only_the_override(ida, topic, sample):
    quiz = make_quiz(ida, topic)
    _, answer = graded(ida, quiz)
    before = (answer.grade, answer.explanation, answer.answered_at)
    services.override_grade(ida, answer, Grade.CORRECT)
    after = Answer.objects.get(pk=answer.pk)
    assert after.override_grade == Grade.CORRECT
    assert (after.grade, after.explanation, after.answered_at) == before
    effective = Answer.objects.with_effective_grade().get(pk=answer.pk).effective_grade
    assert effective == Grade.CORRECT


def test_fr12_none_or_the_ai_grade_clears_the_override(ida, topic, sample):
    quiz = make_quiz(ida, topic)
    _, answer = graded(ida, quiz, grade=Grade.PARTIAL)
    services.override_grade(ida, answer, Grade.PARTIAL)
    assert Answer.objects.get(pk=answer.pk).override_grade is None
    services.override_grade(ida, answer, Grade.CORRECT)
    services.override_grade(ida, answer, None)
    assert Answer.objects.get(pk=answer.pk).override_grade is None
    services.override_grade(ida, answer, Grade.CORRECT)
    services.override_grade(ida, answer, Grade.PARTIAL)
    assert Answer.objects.get(pk=answer.pk).override_grade is None


@pytest.mark.parametrize("value", [Grade.NOT_GRADED, "xyz", ""])
def test_fr12_service_ignores_unknown_values(ida, topic, sample, value):
    quiz = make_quiz(ida, topic)
    _, answer = graded(ida, quiz)
    services.override_grade(ida, answer, value)
    assert Answer.objects.get(pk=answer.pk).override_grade is None


def test_fr12_service_never_calls_the_gateway(ida, topic, sample, monkeypatch):
    quiz = make_quiz(ida, topic)
    _, answer = graded(ida, quiz)

    def boom(*args, **kwargs):
        raise AssertionError("no gateway call on override")

    monkeypatch.setattr(gateway, "grade_free_text", boom)
    monkeypatch.setattr(gateway, "_send_grade", boom)
    services.override_grade(ida, answer, Grade.CORRECT)


# ---- Matrix: Override, Undo, Same as AI ---------------------------------------------------


def test_fr12_override_under_htmx_rerenders_the_panel(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq, answer = graded(ida, quiz, grade=Grade.INCORRECT, explanation="Mangler 2NF.")
    response = client_ida.post(override_url(quiz, qq.position), {"grade": "correct"}, **CARD)
    assert response.status_code == 200
    body = response.content.decode()
    assert Answer.objects.get(pk=answer.pk).override_grade == Grade.CORRECT
    assert "feedback-panel--correct" in body
    assert re.search(r'id="feedback-heading"[^>]*data-focus-on-swap', body)
    text = text_of(body)
    assert "Endret av deg" in text and "KI-vurdering: Feil" in text and "Mangler 2NF." in text
    assert text.index("KI-vurdering: Feil") < text.index("Mangler 2NF.")
    assert current_items(body) == ["correct"]
    assert "Bruk KI-vurderingen" in menu_of(body)
    assert 'hx-swap-oob="true"' in body


def test_fr12_override_without_js_redirects_and_the_reload_shows_it(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq, answer = graded(ida, quiz, grade=Grade.INCORRECT, explanation="Mangler 2NF.")
    response = client_ida.post(override_url(quiz, qq.position), {"grade": "partial"})
    assert response.status_code == 302 and response.url == question_url(quiz, qq.position)
    body = client_ida.get(question_url(quiz, qq.position)).content.decode()
    text = text_of(body)
    assert "feedback-panel--partial" in body
    assert "Delvis riktig" in text and "Endret av deg" in text
    assert "KI-vurdering: Feil" in text and "Mangler 2NF." in text


def test_fr12_undo_clears_the_override_and_the_chip(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq, answer = graded(ida, quiz, grade=Grade.INCORRECT)
    client_ida.post(override_url(quiz, qq.position), {"grade": "correct"})
    body = client_ida.post(override_url(quiz, qq.position), {"grade": "ai"}, **CARD).content.decode()
    assert Answer.objects.get(pk=answer.pk).override_grade is None
    assert "feedback-panel--incorrect" in body
    text = text_of(body)
    assert "Endret av deg" not in text and "KI-vurdering" not in text
    assert "Bruk KI-vurderingen" not in body
    assert current_items(body) == ["incorrect"]


def test_fr12_same_as_ai_stays_null(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq, answer = graded(ida, quiz, grade=Grade.PARTIAL)
    body = client_ida.post(override_url(quiz, qq.position), {"grade": "partial"}, **CARD).content.decode()
    assert Answer.objects.get(pk=answer.pk).override_grade is None
    assert "Endret av deg" not in body


def test_fr12_menu_lists_the_three_grades_without_undo_before_an_override(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq, _ = graded(ida, quiz, grade=Grade.PARTIAL)
    body = client_ida.get(question_url(quiz, qq.position)).content.decode()
    menu = menu_of(body)
    assert "Endre vurdering" in text_of(body)
    assert re.findall(r'name="grade" value="(\w+)"', menu) == ["correct", "partial", "incorrect"]
    assert "Bruk KI-vurderingen" not in menu
    assert current_items(body) == ["partial"]
    assert 'popovertarget="override-menu"' in body and "popover data-anchored role=\"group\"" in menu


# ---- Matrix: Not allowed, Bad value, Not owned --------------------------------------------


def test_fr12_mc_answer_has_no_menu_and_post_saves_nothing(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq, answer = graded(ida, quiz, kind="multiple_choice", grade=Grade.INCORRECT)
    body = client_ida.get(question_url(quiz, qq.position)).content.decode()
    assert "Endre vurdering" not in body
    response = client_ida.post(override_url(quiz, qq.position), {"grade": "correct"}, **CARD)
    assert response.status_code == 200
    assert Answer.objects.get(pk=answer.pk).override_grade is None
    assert "Endre vurdering" not in response.content.decode()


def test_fr12_not_graded_and_pending_have_no_menu_and_post_saves_nothing(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq, answer = graded(ida, quiz, grade=Grade.NOT_GRADED)
    assert "Endre vurdering" not in client_ida.get(question_url(quiz, qq.position)).content.decode()
    client_ida.post(override_url(quiz, qq.position), {"grade": "correct"})
    assert Answer.objects.get(pk=answer.pk).override_grade is None

    Answer.objects.filter(pk=answer.pk).update(grade=None)
    assert "Endre vurdering" not in client_ida.get(question_url(quiz, qq.position)).content.decode()
    client_ida.post(override_url(quiz, qq.position), {"grade": "correct"})
    assert Answer.objects.get(pk=answer.pk).override_grade is None


def test_fr12_no_answer_post_saves_nothing(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")
    response = client_ida.post(override_url(quiz, qq.position), {"grade": "correct"}, **CARD)
    assert response.status_code == 200
    assert not Answer.objects.exists()
    response = client_ida.post(override_url(quiz, qq.position), {"grade": "correct"})
    assert response.status_code == 302


@pytest.mark.parametrize("value", ["not_graded", "xyz", ""])
def test_fr12_bad_value_saves_nothing(ida, client_ida, topic, sample, value):
    quiz = make_quiz(ida, topic)
    qq, answer = graded(ida, quiz)
    client_ida.post(override_url(quiz, qq.position), {"grade": value}, **CARD)
    assert Answer.objects.get(pk=answer.pk).override_grade is None


def test_ad7_other_students_override_and_bad_position_are_404(ida, jonas, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq, answer = graded(ida, quiz)
    client_jonas = Client()
    client_jonas.force_login(jonas)
    assert client_jonas.post(override_url(quiz, qq.position), {"grade": "correct"}).status_code == 404
    assert client_ida.post(override_url(quiz, 99), {"grade": "correct"}).status_code == 404
    assert client_ida.get(override_url(quiz, qq.position)).status_code == 405
    assert Answer.objects.get(pk=answer.pk).override_grade is None


# ---- «Slett spørsmålet» --------------------------------------------------------------------


def delete_link(body: str) -> str:
    match = re.search(r'<a class="button-quiet button-quiet--destructive" href="([^"]+)" hx-get="([^"]+)" '
                      r'hx-target="#dialog" hx-swap="innerHTML">', body)
    assert match, "no «Slett spørsmålet» link"
    assert match.group(1) == match.group(2)
    return match.group(1).replace("&amp;", "&")


def test_fr24_every_answered_question_offers_slett_sporsmalet(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    mc, _ = graded(ida, quiz, kind="multiple_choice")
    ft, _ = graded(ida, quiz, grade=Grade.NOT_GRADED)
    for qq in (mc, ft):
        body = client_ida.get(question_url(quiz, qq.position)).content.decode()
        assert "Slett spørsmålet" in text_of(body)
        url = delete_link(body)
        parts = urlsplit(url)
        assert parts.path == reverse("studymat:delete_item", args=["question", qq.question.id])
        query = parse_qs(parts.query)
        assert query["cancel"] == [question_url(quiz, qq.position)]
    # Not offered before the Answer.
    other = QuizQuestion.objects.filter(quiz=quiz).exclude(pk__in=[mc.pk, ft.pk]).first()
    assert "Slett spørsmålet" not in client_ida.get(question_url(quiz, other.position)).content.decode()
    assert "hx-confirm" not in client_ida.get(question_url(quiz, mc.position)).content.decode()


def test_fr24_delete_mid_quiz_goes_on_at_the_next_position(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=5)
    qqs = list(QuizQuestion.objects.filter(quiz=quiz).order_by("position"))
    second = qqs[1]
    services.save_answer(ida, quiz, second.question, chosen_index=0, text="svar")
    url = delete_link(client_ida.get(question_url(quiz, 2)).content.decode())
    query = parse_qs(urlsplit(url).query)
    assert query["next"] == [question_url(quiz, 3)]

    dialog = client_ida.get(url, **DIALOG).content.decode()
    assert dialog.lstrip().startswith('<dialog class="dialog" role="alertdialog"')
    assert "Slette spørsmålet?" in dialog and "Dette kan ikke angres." in dialog
    assert "Slett spørsmålet</button>" in dialog
    assert f'href="{question_url(quiz, 2)}" data-dialog-close>Avbryt' in dialog

    response = client_ida.post(urlsplit(url).path, {"next": query["next"][0]}, **DIALOG)
    assert json.loads(response["HX-Location"])["path"] == question_url(quiz, 3)
    assert not Question.objects.filter(pk=second.question.pk).exists()
    assert not QuizQuestion.objects.filter(pk=second.pk).exists()
    assert not Answer.objects.filter(question_id=second.question_id).exists()
    assert "2 av 4" in text_of(client_ida.get(question_url(quiz, 3)).content.decode())


def test_fr24_delete_last_question_goes_to_p07_or_return_url(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=2)
    first, last = QuizQuestion.objects.filter(quiz=quiz).order_by("position")
    services.save_answer(ida, quiz, first.question, chosen_index=0, text="svar")
    services.save_answer(ida, quiz, last.question, chosen_index=0, text="svar")
    url = delete_link(client_ida.get(question_url(quiz, last.position)).content.decode())
    next_url = parse_qs(urlsplit(url).query)["next"][0]
    assert next_url == reverse("quiz:result", args=[quiz.id])
    response = client_ida.post(urlsplit(url).path, {"next": next_url}, follow=True)
    assert response.redirect_chain[-1][0] == reverse("quiz:result", args=[quiz.id])
    assert re.search(r'result-score-n">av 1<', response.content.decode())

    # The only Question left goes too: P07 has nothing to show and lands on return_url.
    url = delete_link(client_ida.get(question_url(quiz, first.position)).content.decode())
    next_url = parse_qs(urlsplit(url).query)["next"][0]
    response = client_ida.post(urlsplit(url).path, {"next": next_url}, follow=True)
    assert response.redirect_chain[-1][0] == return_url(topic)


def test_fr24_cancel_without_js_returns_to_the_same_position(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    qq = QuizQuestion.objects.filter(quiz=quiz).order_by("position")[1]
    services.save_answer(ida, quiz, qq.question, chosen_index=0, text="svar")
    url = delete_link(client_ida.get(question_url(quiz, qq.position)).content.decode())
    page = client_ida.get(url).content.decode()
    assert "<dialog" not in page
    assert f'href="{question_url(quiz, qq.position)}" data-dialog-close>Avbryt' in page
    assert client_ida.get(question_url(quiz, qq.position)).status_code == 200
    assert Question.objects.filter(pk=qq.question.pk).exists()
