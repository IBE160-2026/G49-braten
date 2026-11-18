"""CAP-7, FR-10 to FR-12 (story 8): D06 «Start quiz», P06 one Question per page, and grading.

Free-text grading calls the gateway, which asserts it is outside a transaction, so `transaction=True`.
"""

import datetime
import re

import pytest
from django.core.files import File
from django.test import Client
from django.urls import reverse

from ai import errors, gateway, mock
from ai.models import GenerationCallCount
from core import time
from core.messages import MESSAGES
from courses import services as courses_services
from ingestion.services import ingest
from quiz import services
from quiz.models import Answer, Quiz, QuizQuestion
from quiz.rules import Grade
from studymat import services as studymat_services
from studymat.models import Question

pytestmark = pytest.mark.django_db(transaction=True)

NOON = datetime.datetime(2026, 11, 17, 12, 0, tzinfo=time.OSLO)
CARD = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "question-card"}
DIALOG = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "dialog"}


def text_of(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def used(student) -> int:
    row = GenerationCallCount.objects.filter(student=student, day=time.today()).first()
    return row.count if row else 0


@pytest.fixture
def now(freeze_now):
    freeze_now(NOON)


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def jonas(student):
    return student("jonas@example.no")


@pytest.fixture
def client_ida(ida):
    client = Client()
    client.force_login(ida)
    return client


@pytest.fixture
def topic(ida):
    return courses_services.create_topic(courses_services.create_course(ida, "Databaser"), "Normalisering")


@pytest.fixture
def sample(ida, topic, now):
    """The Sample document, generated in Mock mode: 11 ready Questions."""
    with open(mock.SAMPLE_PATH, "rb") as handle:
        source = ingest(topic, upload=File(handle, name=mock.SAMPLE_NAME), detail_level="medium")
    studymat_services.generate(ida, source)
    source.refresh_from_db()
    return source


def start_url(topic):
    return reverse("quiz:start", args=[topic.id])


def question_url(quiz, position):
    return reverse("quiz:question", args=[quiz.id, position])


def answer_url(quiz, position):
    return reverse("quiz:answer", args=[quiz.id, position])


def return_url(topic):
    return f"{reverse('web:topic', args=[topic.id])}?tab=quiz"


def make_quiz(ida, topic, n=11, token="t1"):
    return services.start_quiz(ida, topic, n, token, return_url(topic))


def position_of(quiz, kind):
    return QuizQuestion.objects.filter(quiz=quiz, question__kind=kind).order_by("position").first()


# ---- D06 and Start -------------------------------------------------------------------------


def test_fr10_quiz_tab_opens_d06_with_presets_capped_at_eleven(client_ida, topic, sample):
    tab = client_ida.get(return_url(topic)).content.decode()
    assert "Velg antall og start" in tab
    assert f'hx-get="{start_url(topic)}"' in tab
    body = client_ida.get(start_url(topic), **DIALOG).content.decode()
    text = text_of(body)
    assert "Start quiz i Normalisering" in text
    assert "Antall spørsmål" in text
    assert "11 spørsmål tilgjengelig. Flervalg og fritekst blandes." in text
    labels = re.findall(r'<span>([^<]+)</span></label>', body)
    assert labels == ["5", "10", "Alle 11"]
    assert re.search(r'value="10"[^>]*checked', body)
    assert "Avbryt" in text and "Start quiz" in text
    assert "<dialog" in body


def test_fr10_d06_default_is_all_when_fewer_than_ten(ida, client_ida, topic, sample):
    Question.objects.filter(source=sample).exclude(
        pk__in=list(Question.objects.filter(source=sample).values_list("pk", flat=True)[:7])
    ).delete()
    body = client_ida.get(start_url(topic)).content.decode()
    assert re.findall(r'<span>([^<]+)</span></label>', body) == ["5", "Alle 7"]
    assert re.search(r'value="7"[^>]*checked', body)


def test_fr10_start_creates_ten_distinct_ready_questions_and_opens_position_one(ida, client_ida, topic, sample):
    response = client_ida.post(start_url(topic), {"count": "10", "start_token": "abc"}, follow=True)
    quiz = Quiz.objects.get(student=ida)
    assert response.redirect_chain[-1][0] == question_url(quiz, 1)
    qqs = QuizQuestion.objects.filter(quiz=quiz)
    assert qqs.count() == 10
    assert len(set(qqs.values_list("question_id", flat=True))) == 10
    assert sorted(qqs.values_list("position", flat=True)) == list(range(1, 11))
    assert all(qq.question.source.status == "ready" for qq in qqs)
    assert quiz.return_url == return_url(topic)
    assert quiz.kind == "practice" and quiz.course_id == topic.course_id


def test_fr10_start_under_htmx_answers_with_hx_location(client_ida, topic, sample):
    response = client_ida.post(start_url(topic), {"count": "5", "start_token": "abc"}, **DIALOG)
    quiz = Quiz.objects.get()
    assert reverse("quiz:resume", args=[quiz.id]) in response.headers["HX-Location"]


def test_fr10_double_start_with_the_same_token_makes_one_quiz(ida, client_ida, topic, sample):
    first = client_ida.post(start_url(topic), {"count": "10", "start_token": "same"}, follow=True)
    second = client_ida.post(start_url(topic), {"count": "10", "start_token": "same"}, follow=True)
    assert Quiz.objects.count() == 1
    assert first.redirect_chain[-1][0] == second.redirect_chain[-1][0]


def test_fr10_n_too_large_is_clamped(ida, topic, sample):
    quiz = make_quiz(ida, topic, n=50)
    assert QuizQuestion.objects.filter(quiz=quiz).count() == 11


def test_fr10_only_ready_sources_supply_questions(ida, topic, sample):
    type(sample).objects.filter(pk=sample.pk).update(status="failed")
    assert make_quiz(ida, topic) is None
    assert not Quiz.objects.exists()


def test_ad7_every_model_has_its_student(ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "multiple_choice")
    services.save_answer(ida, quiz, qq.question, chosen_index=0)
    assert quiz.student_id == ida.pk
    assert set(QuizQuestion.objects.values_list("student_id", flat=True)) == {ida.pk}
    assert set(Answer.objects.values_list("student_id", flat=True)) == {ida.pk}


# ---- P06 -------------------------------------------------------------------------------------


def test_fr10_p06_shows_session_bar_chip_prompt_hint_and_options(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "multiple_choice")
    body = client_ida.get(question_url(quiz, qq.position)).content.decode()
    text = text_of(body)
    assert "Avslutt" in text and f"{qq.position} av 11" in text and "Normalisering · øving" in text
    assert f'href="{return_url(topic)}"' in body
    assert "Flervalg" in text and qq.question.prompt in text
    assert "<details" in body and "Vis hint" in text
    assert body.count('type="radio"') == 4
    assert 'class="option-group"' in body
    assert ">Svar</button>" in body
    assert "fag-rail" not in body


def test_fr10_free_text_has_a_ditt_svar_field(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")
    text = text_of(client_ida.get(question_url(quiz, qq.position)).content.decode())
    assert "Fritekst" in text and "Ditt svar" in text


def test_fr11_mc_right_and_wrong_without_a_gateway_call(ida, client_ida, topic, sample, monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("no gateway call for multiple-choice")

    monkeypatch.setattr(gateway, "_send_grade", boom)
    monkeypatch.setattr(gateway, "grade_free_text", boom)
    quiz = make_quiz(ida, topic)
    mcs = QuizQuestion.objects.filter(quiz=quiz, question__kind="multiple_choice").order_by("position")[:2]
    right, wrong = mcs[0], mcs[1]

    body = client_ida.post(answer_url(quiz, right.position), {"choice": right.question.correct_index}, **CARD).content.decode()
    assert "Riktig" in text_of(body) and "Riktig svar er" not in body
    assert 'aria-live="polite"' in body and "data-focus-on-swap" in body
    assert 'hx-swap-oob="true"' in body

    wrong_index = (wrong.question.correct_index + 1) % 4
    body = client_ida.post(answer_url(quiz, wrong.position), {"choice": wrong_index}, **CARD).content.decode()
    text = text_of(body)
    letter = "ABCD"[wrong.question.correct_index]
    assert "Feil" in text
    assert f"Riktig svar er {letter}." in text
    assert wrong.question.options[wrong_index]["explanation"] in text
    assert "Ditt svar" in text and "Riktig svar" in text
    assert Answer.objects.get(question=wrong.question).grade == Grade.INCORRECT
    assert Answer.objects.get(question=right.question).grade == Grade.CORRECT


def test_fr12_free_text_mock_is_graded_by_rule_with_demo_and_fasit(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")
    before = used(ida)
    body = client_ida.post(answer_url(quiz, qq.position), {"text": qq.question.model_answer}, **CARD).content.decode()
    text = text_of(body)
    answer = Answer.objects.get(question=qq.question)
    assert answer.grade == Grade.CORRECT and answer.is_mock
    assert answer.explanation.startswith("Demo-vurdering:")
    assert "Demo" in text and "Vis fasit" in text and "Riktig" in text
    assert used(ida) == before  # AD-3: grading is never counted


def test_fr10_empty_answers_are_refused_inline_and_nothing_is_saved(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    mc = position_of(quiz, "multiple_choice")
    ft = position_of(quiz, "free_text")
    response = client_ida.post(answer_url(quiz, mc.position), {}, **CARD)
    assert response.status_code == 200 and "Velg et svar først." in response.content.decode()
    response = client_ida.post(answer_url(quiz, ft.position), {"text": "   "})
    assert response.status_code == 200 and "Skriv et svar først." in response.content.decode()
    assert not Answer.objects.exists()


def test_fr12_grading_failure_is_not_graded_with_message_and_regrade(ida, client_ida, topic, sample, monkeypatch):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")

    def fail(request):
        raise errors.RateLimited()

    monkeypatch.setattr(gateway, "_send_grade", fail)
    body = client_ida.post(answer_url(quiz, qq.position), {"text": qq.question.model_answer}, **CARD).content.decode()
    answer = Answer.objects.get(question=qq.question)
    assert (answer.grade, answer.failure) == (Grade.NOT_GRADED, "rate_limited")
    assert "Ikke rettet" in body and MESSAGES["grading_failed"] in body and 'role="alert"' in body
    assert "Prøv å rette igjen" in body
    # A reload shows the same.
    assert MESSAGES["grading_failed"] in client_ida.get(question_url(quiz, qq.position)).content.decode()

    monkeypatch.undo()
    regrade = reverse("quiz:regrade", args=[quiz.id, qq.position])
    body = client_ida.post(regrade, **CARD).content.decode()
    answer.refresh_from_db()
    assert answer.grade == Grade.CORRECT and answer.failure == ""
    assert answer.text == qq.question.model_answer
    assert "Ikke rettet" not in body


def test_fr21_key_rejected_shows_the_key_message(ida, topic, sample, monkeypatch):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")

    def fail(request):
        raise errors.KeyRejected()

    monkeypatch.setattr(gateway, "_send_grade", fail)
    services.save_answer(ida, quiz, qq.question, text="svar")
    client = Client()
    client.force_login(ida)
    assert MESSAGES["key_rejected"] in client.get(question_url(quiz, qq.position)).content.decode()


def test_fr21_real_mode_saves_the_text_and_shows_ikke_rettet(ida, client_ida, topic, sample, settings):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")
    settings.AI_PROVIDER = "anthropic"
    body = client_ida.post(answer_url(quiz, qq.position), {"text": "Mitt svar"}, **CARD).content.decode()
    answer = Answer.objects.get(question=qq.question)
    assert answer.text == "Mitt svar" and answer.grade == Grade.NOT_GRADED
    assert answer.failure == "provider_unavailable"
    assert "Ikke rettet" in body and MESSAGES["grading_failed"] in body


def test_fr10_a_pending_grade_reads_as_not_graded(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")
    Answer.objects.create(student=ida, quiz=quiz, question=qq.question, text="x", answered_at=time.now())
    body = client_ida.get(question_url(quiz, qq.position)).content.decode()
    assert "Ikke rettet" in body and MESSAGES["grading_failed"] in body


def test_fr10_resubmit_keeps_the_first_answer(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "multiple_choice")
    first = qq.question.correct_index
    client_ida.post(answer_url(quiz, qq.position), {"choice": first})
    stamp = Answer.objects.get().answered_at
    response = client_ida.post(answer_url(quiz, qq.position), {"choice": (first + 1) % 4})
    assert response.status_code == 302 and response.url == question_url(quiz, qq.position)
    answer = Answer.objects.get()
    assert answer.chosen_index == first and answer.answered_at == stamp
    body = client_ida.get(question_url(quiz, qq.position)).content.decode()
    assert "Riktig" in text_of(body) and "disabled" in body and ">Svar</button>" not in body


def test_fr10_abandon_keeps_the_answers(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=10)
    for qq in QuizQuestion.objects.filter(quiz=quiz).order_by("position")[:3]:
        data = {"choice": 0} if qq.question.kind == "multiple_choice" else {"text": "noe"}
        client_ida.post(answer_url(quiz, qq.position), data)
    assert client_ida.get(return_url(topic)).status_code == 200
    assert Answer.objects.filter(quiz=quiz).count() == 3
    resume = client_ida.get(reverse("quiz:resume", args=[quiz.id]))
    assert resume.url == question_url(quiz, 4)


def test_fr10_finish_goes_to_the_quiz_tab_with_the_note(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    qqs = list(QuizQuestion.objects.filter(quiz=quiz).order_by("position"))
    for qq in qqs:
        q = qq.question
        data = {"choice": q.correct_index} if q.kind == "multiple_choice" else {"text": "feil feil"}
        client_ida.post(answer_url(quiz, qq.position), data)
    last = client_ida.get(question_url(quiz, 3)).content.decode()
    assert "Fullfør quiz" in last and "Neste spørsmål" not in last
    assert "Neste spørsmål" in client_ida.get(question_url(quiz, 1)).content.decode()
    response = client_ida.get(reverse("quiz:resume", args=[quiz.id]), follow=True)
    assert response.redirect_chain[-1][0] == f"{return_url(topic)}&quiz={quiz.id}"
    k = sum(1 for qq in qqs if qq.question.kind == "multiple_choice")
    assert f"Quizen er lagret. {k} av 3 riktige." in response.content.decode()


def test_fr12_with_effective_grade_prefers_the_override(ida, topic, sample):
    quiz = make_quiz(ida, topic, n=2)
    a, b = [qq.question for qq in QuizQuestion.objects.filter(quiz=quiz).order_by("position")]
    Answer.objects.create(student=ida, quiz=quiz, question=a, grade=Grade.PARTIAL, override_grade=Grade.CORRECT)
    Answer.objects.create(student=ida, quiz=quiz, question=b, grade=Grade.INCORRECT)
    grades = dict(Answer.objects.with_effective_grade().values_list("question_id", "effective_grade"))
    assert grades == {a.pk: Grade.CORRECT, b.pk: Grade.INCORRECT}
    assert services.finish_note(ida, quiz.id) == "Quizen er lagret. 1 av 2 riktige."


def test_ad7_other_students_quiz_and_bad_position_are_404(ida, jonas, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    client_jonas = Client()
    client_jonas.force_login(jonas)
    assert client_jonas.get(question_url(quiz, 1)).status_code == 404
    assert client_jonas.post(answer_url(quiz, 1), {"choice": 0}).status_code == 404
    assert client_jonas.get(reverse("quiz:resume", args=[quiz.id])).status_code == 404
    assert client_jonas.get(start_url(topic)).status_code == 404
    assert client_ida.get(question_url(quiz, 99)).status_code == 404
    assert services.finish_note(jonas, quiz.id) == ""
    assert services.finish_note(ida, "nope") == ""
    assert "Quizen er lagret" not in client_jonas.get(return_url(topic)).content.decode()


def test_ad8_deleting_a_question_drops_it_from_the_quiz(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic, n=3)
    qqs = list(QuizQuestion.objects.filter(quiz=quiz).order_by("position"))
    services.save_answer(ida, quiz, qqs[1].question, chosen_index=0, text="noe")
    qqs[1].question.delete()
    assert QuizQuestion.objects.filter(quiz=quiz).count() == 2
    assert not Answer.objects.filter(quiz=quiz).exists()
    assert services.next_position(quiz, 1) == 3
    assert client_ida.get(question_url(quiz, 2)).status_code == 404
    body = text_of(client_ida.get(question_url(quiz, 3)).content.decode())
    assert "2 av 2" in body
    # Nothing left: resume goes to return_url.
    for qq in (qqs[0], qqs[2]):
        qq.question.delete()
    assert client_ida.get(reverse("quiz:resume", args=[quiz.id])).url == return_url(topic)


# ---- Review follow-ups --------------------------------------------------------------------


def test_fr12_an_unexpected_grading_error_is_not_graded_not_a_500(ida, client_ida, topic, sample, monkeypatch):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")

    def crash(request):
        raise RuntimeError("bug")

    monkeypatch.setattr(gateway, "_send_grade", crash)
    response = client_ida.post(answer_url(quiz, qq.position), {"text": "mitt svar"}, **CARD)
    assert response.status_code == 200
    assert "Ikke rettet" in response.content.decode()
    answer = Answer.objects.get(question=qq.question)
    assert (answer.grade, answer.failure) == (Grade.NOT_GRADED, "provider_unavailable")


@pytest.mark.parametrize("choice", ["4", "-1", "abc"])
def test_fr10_an_out_of_range_choice_is_refused(ida, client_ida, topic, sample, choice):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "multiple_choice")
    response = client_ida.post(answer_url(quiz, qq.position), {"choice": choice}, **CARD)
    assert response.status_code == 200
    assert MESSAGES["answer_choose_first"] in response.content.decode()
    assert not Answer.objects.exists()


def test_fr10_a_full_page_error_puts_autofocus_on_the_field(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    mc = position_of(quiz, "multiple_choice")
    ft = position_of(quiz, "free_text")
    body = client_ida.post(answer_url(quiz, mc.position), {}).content.decode()
    assert re.search(r'<input type="radio" name="choice" value="0"[^>]*autofocus', body)
    body = client_ida.post(answer_url(quiz, ft.position), {"text": " "}).content.decode()
    assert re.search(r'<textarea[^>]*autofocus', body)


def test_fr12_regrade_leaves_a_graded_answer_alone(ida, client_ida, topic, sample, monkeypatch):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")
    client_ida.post(answer_url(quiz, qq.position), {"text": qq.question.model_answer})
    before = Answer.objects.get(question=qq.question)
    assert before.grade == Grade.CORRECT

    def fail(request):
        raise errors.RateLimited()

    monkeypatch.setattr(gateway, "_send_grade", fail)
    client_ida.post(reverse("quiz:regrade", args=[quiz.id, qq.position]), **CARD)
    after = Answer.objects.get(pk=before.pk)
    assert (after.grade, after.explanation) == (before.grade, before.explanation)


@pytest.mark.parametrize("count", ["", "0"])
def test_fr10_d06_refuses_an_empty_or_zero_count(client_ida, topic, sample, count):
    response = client_ida.post(start_url(topic), {"count": count, "start_token": "x"}, **DIALOG)
    assert response.status_code == 200
    body = response.content.decode()
    assert "<dialog" in body and MESSAGES["quiz_count_required"] in body
    assert not Quiz.objects.exists()


def test_ad7_another_students_regrade_is_404(ida, jonas, topic, sample):
    quiz = make_quiz(ida, topic)
    qq = position_of(quiz, "free_text")
    services.save_answer(ida, quiz, qq.question, text="svar")
    client_jonas = Client()
    client_jonas.force_login(jonas)
    assert client_jonas.post(reverse("quiz:regrade", args=[quiz.id, qq.position])).status_code == 404


# ---- Story 8b: the feedback panel's new actions --------------------------------------------


def test_fr12_feedback_panel_offers_endre_vurdering_only_on_graded_free_text(ida, client_ida, topic, sample):
    quiz = make_quiz(ida, topic)
    ft = position_of(quiz, "free_text")
    mc = position_of(quiz, "multiple_choice")
    ft_body = client_ida.post(answer_url(quiz, ft.position), {"text": ft.question.model_answer}, **CARD).content.decode()
    mc_body = client_ida.post(answer_url(quiz, mc.position), {"choice": 0}, **CARD).content.decode()
    assert "Endre vurdering" in ft_body and 'aria-current="true"' in ft_body
    assert "Endre vurdering" not in mc_body
    assert "Slett spørsmålet" in ft_body and "Slett spørsmålet" in mc_body
