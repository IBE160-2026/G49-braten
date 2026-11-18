"""CAP-8, FR-13 (story 9): P07 «Resultat» and the Retry round («Øv på feilene»)."""

import re

import pytest
from django.db import IntegrityError
from django.test import Client
from django.urls import reverse

from ai import gateway
from core import time
from quiz import services
from quiz.models import Answer, Quiz, QuizKind, QuizQuestion
from quiz.rules import Grade, join_with_og
from tests.test_quiz import (  # noqa: F401  (fixtures)
    client_ida,
    ida,
    jonas,
    make_quiz,
    now,
    question_url,
    return_url,
    sample,
    text_of,
    topic,
    used,
)

pytestmark = pytest.mark.django_db(transaction=True)

C, P, I, N = Grade.CORRECT, Grade.PARTIAL, Grade.INCORRECT, Grade.NOT_GRADED


def result_url(quiz):
    return reverse("quiz:result", args=[quiz.id])


def retry_url(quiz):
    return reverse("quiz:retry", args=[quiz.id])


def qqs_of(quiz):
    return list(QuizQuestion.objects.filter(quiz=quiz).order_by("position"))


def grade_all(ida, quiz, grades):
    """Answers with these Grades at the first len(grades) positions (None leaves one unanswered)."""
    for qq, grade in zip(qqs_of(quiz), grades):
        if grade is not None:
            Answer.objects.create(
                student=ida, quiz=quiz, question=qq.question, grade=grade, text="svar", answered_at=time.now()
            )


def band_of(body: str) -> str:
    match = re.search(r'<section class="next-step-band".*?</section>', body, re.S)
    return text_of(match.group(0)).replace(" ,", ",") if match else ""


@pytest.fixture
def no_gateway(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("P07 and «Øv på feilene» never call the gateway")

    monkeypatch.setattr(gateway, "grade_free_text", boom)


# ---- Matrix: Finish --------------------------------------------------------------------------


def test_fr13_finish_shows_score_lead_strip_and_band(ida, client_ida, topic, sample, no_gateway):
    quiz = make_quiz(ida, topic, n=10)
    grade_all(ida, quiz, [C, C, I, P, I, C, C, C, C, C])
    before = used(ida)
    response = client_ida.get(reverse("quiz:resume", args=[quiz.id]), follow=True)
    assert response.redirect_chain[-1][0] == result_url(quiz)
    body = response.content.decode()
    text = text_of(body)
    assert "Resultat" in text and "7 av 10" in text
    assert "7 riktige, 1 delvis riktig og 2 feil." in text
    assert band_of(body) == (
        "3 spørsmål Øv på feilene Spørsmål 3, 4 og 5 var feil eller delvis riktige. "
        "Runden teller ikke i mestringen. Øv på feilene (3) ca. 3 min"
    )
    assert f'<form method="post" action="{retry_url(quiz)}">' in body
    assert body.count('class="next-step-band"') == 1
    slots = re.findall(r'class="result-slot result-slot--(\w+)" href="#q-(\d+)"', body)
    assert slots[2:5] == [("incorrect", "3"), ("partial", "4"), ("incorrect", "5")]
    assert body.count("<details class=\"result-row") == 10
    assert 'id="q-10"' in body
    # The session-bar: «Avslutt» to return_url, the context «Resultat», no progress strip.
    assert f'<a class="session-exit" href="{return_url(topic)}"' in body
    assert '<p class="session-context">Resultat</p>' in body
    assert "session-strip" not in body
    assert f'href="{return_url(topic)}">Tilbake</a>' in body
    client_ida.post(retry_url(quiz))
    assert used(ida) == before


def test_fr13_lead_leaves_out_zero_counts_and_minutes_round_up(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [I, I, C])
    text = text_of(client_ida.get(result_url(quiz)).content.decode())
    assert "1 riktig og 2 feil." in text
    assert "riktige," not in text and "delvis riktig og" not in text
    assert "ca. 2 min" in text  # ceil(0.8 · 2)
    assert "Spørsmål 1 og 2 var feil eller delvis riktige." in text


def test_fr13_one_miss_reads_in_the_singular(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=2)
    grade_all(ida, quiz, [C, P])
    body = client_ida.get(result_url(quiz)).content.decode()
    assert "Spørsmål 2 var feil eller delvis riktig." in text_of(body)
    assert "<b>2</b>" in body
    assert "Øv på feilene (1)" in body and "ca. 1 min" in text_of(body)


# ---- Matrix: Start retry, Double click, reuse ----------------------------------------------


def test_fr13_start_retry_takes_the_misses_in_parent_order(ida, topic, sample, no_gateway):
    quiz = make_quiz(ida, topic, n=6)
    grade_all(ida, quiz, [I, C, N, P, C, I])
    before = used(ida)
    parent = qqs_of(quiz)
    round_ = services.start_retry(ida, quiz)
    assert round_.kind == QuizKind.RETRY and round_.parent_quiz_id == quiz.id
    assert round_.course_id == quiz.course_id and round_.return_url == quiz.return_url
    members = [qq.question_id for qq in qqs_of(round_)]
    assert members == [parent[0].question_id, parent[3].question_id, parent[5].question_id]
    assert [qq.position for qq in qqs_of(round_)] == [1, 2, 3]
    assert list(quiz.retry_rounds.all()) == [round_]
    assert used(ida) == before


def test_fr13_retry_post_goes_to_the_first_position_and_double_click_is_one_round(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=4)
    grade_all(ida, quiz, [C, I, C, P])
    first = client_ida.post(retry_url(quiz))
    second = client_ida.post(retry_url(quiz))
    round_ = Quiz.objects.get(parent_quiz=quiz)
    assert first.status_code == 302 and first.url == question_url(round_, 1)
    assert second.url == first.url
    assert Quiz.objects.filter(parent_quiz=quiz).count() == 1


def test_fr13_a_token_collision_returns_the_twin_round(ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [I, I, C])
    # Two answered rounds exist (so the reuse branch skips both), and one of them holds the token
    # the next round would take, retry-<pk>-3, as a concurrent POST's round would.
    Quiz.objects.create(
        student=ida, course_id=quiz.course_id, kind=QuizKind.RETRY, parent_quiz=quiz,
        return_url=quiz.return_url, start_token="other",
    )
    grade_all(ida, Quiz.objects.get(start_token="other"), [C])
    twin = Quiz.objects.create(
        student=ida, course_id=quiz.course_id, kind=QuizKind.RETRY, parent_quiz=quiz,
        return_url=quiz.return_url, start_token=f"retry-{quiz.pk}-3",
    )
    grade_all(ida, twin, [C])
    assert services.start_retry(ida, quiz).pk == twin.pk
    assert Quiz.objects.filter(parent_quiz=quiz).count() == 2


def test_fr13_a_practice_quiz_holding_the_retry_token_is_not_returned(ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [I, I, C])
    squatter = make_quiz(ida, topic, n=1, token=f"retry-{quiz.pk}-1")
    assert squatter.kind == QuizKind.PRACTICE
    with pytest.raises(IntegrityError):
        services.start_retry(ida, quiz)
    assert not Quiz.objects.filter(parent_quiz=quiz).exists()


def test_fr13_a_partly_answered_round_is_not_reused(ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [I, I, C])
    round_ = services.start_retry(ida, quiz)
    grade_all(ida, round_, [C])
    fresh = services.start_retry(ida, quiz)
    assert fresh.pk != round_.pk and fresh.parent_quiz_id == quiz.id
    assert len(qqs_of(fresh)) == 2
    assert services.start_retry(ida, quiz).pk == fresh.pk


def test_fr13_a_reused_round_follows_an_override_made_after_it_was_started(ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [I, I, C])
    round_ = services.start_retry(ida, quiz)
    first = qqs_of(quiz)[0]
    Answer.objects.filter(quiz=quiz, question=first.question).update(override_grade=C)
    again = services.start_retry(ida, quiz)
    assert again.pk == round_.pk
    assert [qq.question_id for qq in qqs_of(again)] == [qqs_of(quiz)[1].question_id]


# ---- Matrix: Retry of retry ----------------------------------------------------------------


def test_fr13_retry_of_a_retry_round(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [I, P, C])
    round_ = services.start_retry(ida, quiz)
    grade_all(ida, round_, [C, I])
    response = client_ida.get(reverse("quiz:resume", args=[round_.id]), follow=True)
    assert response.redirect_chain[-1][0] == result_url(round_)
    body = response.content.decode()
    assert "1 av 2" in text_of(body) and "Øv på feilene (1)" in body
    assert "Spørsmål 2 var feil eller delvis riktig." in text_of(body)
    client_ida.post(retry_url(round_))
    nested = Quiz.objects.get(parent_quiz=round_)
    assert nested.kind == QuizKind.RETRY and nested.return_url == quiz.return_url
    assert [qq.question_id for qq in qqs_of(nested)] == [qqs_of(round_)[1].question_id]


# ---- Matrix: All correct, Override counts, Abandoned, Nothing missed --------------------------


def test_fr13_all_correct_has_no_band(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [C, C, C])
    body = client_ida.get(result_url(quiz)).content.decode()
    assert "next-step-band" not in body
    assert "Alle svarene var riktige." in text_of(body) and "3 av 3" in text_of(body)


def test_fr13_not_all_answered_is_not_all_correct(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [C, C, None])
    body = client_ida.get(result_url(quiz)).content.decode()
    assert "next-step-band" not in body and "Alle svarene var riktige." not in body


def test_fr12_an_override_to_correct_leaves_the_band_and_the_round(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [I, I, C])
    first = qqs_of(quiz)[0]
    Answer.objects.filter(quiz=quiz, question=first.question).update(override_grade=C)
    body = client_ida.get(result_url(quiz)).content.decode()
    assert "Øv på feilene (1)" in body and "2 av 3" in text_of(body)
    assert "Spørsmål 2 var" in text_of(body)
    round_ = services.start_retry(ida, quiz)
    assert [qq.question_id for qq in qqs_of(round_)] == [qqs_of(quiz)[1].question_id]


def test_fr13_abandoned_quiz(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=10)
    grade_all(ida, quiz, [I, C, C])
    # «Avslutt» on P06 goes to return_url, and resume goes on at the first unanswered Question.
    p06 = client_ida.get(question_url(quiz, 1)).content.decode()
    assert f'<a class="session-exit" href="{return_url(topic)}"' in p06
    assert client_ida.get(reverse("quiz:resume", args=[quiz.id])).url == question_url(quiz, 4)
    body = client_ida.get(result_url(quiz)).content.decode()
    assert body.count("result-slot--unanswered") == 7
    assert text_of(body).count("Ikke besvart") >= 7
    assert "2 av 10" in text_of(body) and "Øv på feilene (1)" in body
    round_ = services.start_retry(ida, quiz)
    assert [qq.question_id for qq in qqs_of(round_)] == [qqs_of(quiz)[0].question_id]


def test_fr13_nothing_missed_post_creates_nothing(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [C, N, None])
    response = client_ida.post(retry_url(quiz))
    assert response.status_code == 302 and response.url == result_url(quiz)
    assert Quiz.objects.count() == 1
    assert services.start_retry(ida, quiz) is None


def test_ad7_result_and_retry_are_owned(ida, jonas, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [I, C, C])
    other = Client()
    other.force_login(jonas)
    assert other.get(result_url(quiz)).status_code == 404
    assert other.post(retry_url(quiz)).status_code == 404
    assert not Quiz.objects.filter(parent_quiz=quiz).exists()
    assert client_ida.get(retry_url(quiz)).status_code == 405
    assert client_ida.post(result_url(quiz)).status_code == 405


# ---- Display numbers, rows, the Retry round on P06 ----------------------------------------


def test_fr13_display_numbers_close_the_gap_after_a_delete(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=4)
    grade_all(ida, quiz, [C, C, I, P])
    qqs_of(quiz)[1].question.delete()
    body = client_ida.get(result_url(quiz)).content.decode()
    assert "Spørsmål 2 og 3 var feil eller delvis riktige." in text_of(body)
    assert "2 av 3" not in text_of(body) and "1 av 3" in text_of(body)
    assert 'id="q-3"' in body and 'id="q-4"' not in body
    # «Åpne spørsmålet» still names the real position.
    assert f'href="{question_url(quiz, 4)}"' in body


def test_fr13_rows_are_read_only_and_open_their_p06_position(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=11)
    free = [qq for qq in qqs_of(quiz) if qq.question.kind == "free_text"]
    first, second = free[0], free[1]
    Answer.objects.create(
        student=ida, quiz=quiz, question=first.question, text="svar", grade=I, override_grade=P,
        explanation="KI sier feil.", answered_at=time.now(),
    )
    Answer.objects.create(
        student=ida, quiz=quiz, question=second.question, text="svar", grade=N,
        failure="provider_unavailable", answered_at=time.now(),
    )
    body = client_ida.get(result_url(quiz)).content.decode()
    assert "Endre vurdering" not in body
    assert "Prøv å rette igjen" not in body
    assert "Slett spørsmålet" not in body
    assert "data-next" not in body and "Neste spørsmål" not in body
    assert "Endret av deg" in body and "KI-vurdering: Feil" in body and "KI sier feil." in body
    assert "Vis fasit" in body
    assert "Spørsmålet er ikke med i «Øv på feilene» før det er rettet." in body
    assert 'aria-live="polite"' not in body.split('id="live-polite"')[0]
    ids = re.findall(r'id="(q-\d+-heading)"', body)
    assert len(ids) == len(set(ids)) == 2
    assert f'<a class="result-row-open" href="{question_url(quiz, first.position)}">Åpne spørsmålet' in body
    assert client_ida.get(question_url(quiz, first.position)).status_code == 200


def test_fr16_retry_round_on_p06_reads_ov_pa_feilene_with_the_note(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [I, P, C])
    p06 = client_ida.get(question_url(quiz, 1)).content.decode()
    assert "Denne runden teller ikke i mestringen." not in p06
    round_ = services.start_retry(ida, quiz)
    body = client_ida.get(question_url(round_, 1)).content.decode()
    assert '<p class="session-context">Øv på feilene</p>' in body
    assert "Denne runden teller ikke i mestringen." in body
    assert "1 av 2" in text_of(body)


def test_fr13_quiz_tab_has_no_finish_note(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=2)
    grade_all(ida, quiz, [C, C])
    body = client_ida.get(f"{return_url(topic)}&quiz={quiz.id}").content.decode()
    assert "Quizen er lagret" not in body and "quiz-finish-note" not in body


def test_join_with_og():
    assert join_with_og([]) == ""
    assert join_with_og(["3"]) == "3"
    assert join_with_og(["3", "4"]) == "3 og 4"
    assert join_with_og(["3", "4", "5"]) == "3, 4 og 5"
