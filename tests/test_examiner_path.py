"""UJ-5 / NFR-2 / SM-2 checks 1–6 (story 14): the Examiner's path end to end, in Mock mode.

Everything goes through the views with the Django test client, as the README's «Prøv alle
kjernefunksjonene» steps do. The one shortcut is the clock (`freeze_now`). No Key, no socket
(pytest-socket); every request must answer within NFR-3's 5 s Mock budget.

Gateway calls assert they are outside a transaction, so `transaction=True`.
"""

import datetime
import json
import re
import time as wallclock
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from ai import gateway
from core import time
from core.messages import MESSAGES
from courses.models import Course, FailureReason, Source, Status, Topic
from quiz.models import Answer, Quiz, QuizKind, QuizQuestion
from quiz.rules import Grade
from review.models import Rating, ReviewState
from review.rules import RatingValue
from studymat.models import Flashcard, KeyConcept, Question, Summary
from tests.conftest import PASSWORD
from tests.pdfs import LECTURE_TEXT, make_pdf

TOO_MANY_PAGES_PDF = Path(__file__).resolve().parent.parent / "sample" / "for_mange_sider.pdf"

pytestmark = pytest.mark.django_db(transaction=True)

NOON = datetime.datetime(2026, 11, 19, 12, 0, tzinfo=time.OSLO)
MOCK_BUDGET_SECONDS = 5.0  # NFR-3, Mock mode
EMAIL = "sensor@example.no"
BANNER = '<p class="mode-banner"'
BANNER_TEXT = "<b>Demomodus:</b> appen bruker innspilte svar for eksempeldokumentet."


class TimedClient(Client):
    """A test client that fails any request slower than the Mock budget (NFR-3)."""

    def request(self, **request):
        started = wallclock.perf_counter()
        response = super().request(**request)
        elapsed = wallclock.perf_counter() - started
        path = request.get("PATH_INFO", "?")
        assert elapsed < MOCK_BUDGET_SECONDS, f"{request.get('REQUEST_METHOD')} {path} took {elapsed:.2f} s"
        return response


def text_of(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def topic_tab(topic_id: int, tab: str) -> str:
    return f"{reverse('web:topic', args=[topic_id])}?tab={tab}"


def id_from(location: str) -> int:
    """The last integer in a redirect path, e.g. /courses/3/ -> 3."""
    ids = re.findall(r"/(\d+)/", location)
    assert ids, f"no id in the redirect {location!r}"
    return int(ids[-1])


def found(pattern: str, html: str, what: str) -> re.Match:
    """re.search that fails naming what was missing, instead of an AttributeError on None."""
    match = re.search(pattern, html)
    assert match, f"not found on the page: {what}"
    return match


def snapshot(email: str) -> dict:
    """What must survive signing out and in again (FR-1, FR-2, FR-15)."""
    mine = {"student__email": email}
    return {
        "courses": list(Course.objects.filter(**mine).values_list("name", "code").order_by("pk")),
        "topics": list(Topic.objects.filter(**mine).values_list("name", flat=True).order_by("pk")),
        "sources": list(Source.objects.filter(**mine).values_list("name", "status").order_by("pk")),
        "summaries": list(Summary.objects.filter(**mine).values_list("text", flat=True).order_by("pk")),
        "concepts": KeyConcept.objects.filter(**mine).count(),
        "cards": Flashcard.objects.filter(**mine).count(),
        "questions": Question.objects.filter(**mine).count(),
        "answers": list(Answer.objects.filter(**mine).values_list("question_id", "grade").order_by("pk")),
        "review_dates": list(
            ReviewState.objects.filter(**mine).values_list("flashcard_id", "box", "due_date").order_by("flashcard_id")
        ),
    }


@pytest.fixture
def now(freeze_now):
    freeze_now(NOON)


@pytest.fixture
def mock_mode():
    assert gateway.mode() == gateway.MOCK


def sign_up_and_create_topic(client) -> int:
    """UJ-5 steps 1–2 through the views; returns the Topic id."""
    sign_up = client.get(reverse("accounts:sign_up")).content.decode()
    assert BANNER in sign_up and BANNER_TEXT in sign_up
    response = client.post(reverse("accounts:sign_up"), {"email": EMAIL, "password": PASSWORD})
    assert (response.status_code, response["Location"]) == (302, "/")
    home = client.get("/").content.decode()
    assert BANNER in home and BANNER_TEXT in home

    response = client.post(reverse("courses:create"), {"name": "Databaser", "code": "DAT102"})
    assert response.status_code == 302
    course_id = id_from(response["Location"])
    response = client.post(reverse("courses:create_topic", args=[course_id]), {"name": "Normalisering"})
    assert response.status_code == 302
    return id_from(response["Location"])


def test_uj5_examiner_path_end_to_end_in_mock_mode(now, mock_mode):
    client = TimedClient()

    # ---- Steps 1–2 (SM-2 check 3): sign up, the Mock banner, a Course and a Topic -----------------
    topic_id = sign_up_and_create_topic(client)

    # ---- Step 3: «Bruk eksempeldokumentet» on D05 ------------------------------------------------
    add_url = reverse("studymat:add_source", args=[topic_id])
    dialog = client.get(add_url).content.decode()
    assert "Bruk eksempeldokumentet" in dialog
    response = client.post(add_url, {"use_sample": "1", "detail_level": "medium"})
    assert (response.status_code, response["Location"]) == (302, topic_tab(topic_id, "sources"))
    source = Source.objects.get(student__email=EMAIL)
    # The pending source-row starts generation with one POST on load (hx-trigger="load").
    sources_tab = client.get(topic_tab(topic_id, "sources")).content.decode()
    generate_url = reverse("studymat:generate", args=[source.id])
    assert f'hx-post="{generate_url}" hx-trigger="load"' in sources_tab
    response = client.post(generate_url, HTTP_HX_REQUEST="true", HTTP_HX_TARGET=f"source-{source.id}")
    assert response.status_code == 200
    source.refresh_from_db()
    assert source.status == Status.READY

    # ---- Step 4 (SM-2 checks 1–2): Summary, ≥ 5 Key concepts, ≥ 10 Flashcards, one item removed --
    summary_tab = client.get(topic_tab(topic_id, "summary")).content.decode()
    assert '<div class="summary-text"' in summary_tab
    assert summary_tab.count('class="key-concept-item"') >= 5
    assert MESSAGES["removed_note_one"] in summary_tab
    assert source.removed_count == 1
    selftest_tab = client.get(topic_tab(topic_id, "selftest")).content.decode()
    card_count = int(found(r"(\d+) kort</span>", selftest_tab, "the «Test deg selv» card count").group(1))
    assert card_count >= 10
    browse = client.get(reverse("review:browse_start", args=[topic_id]), follow=True).content.decode()
    assert f"Kort 1 av {card_count}" in text_of(browse)

    # ---- Step 5 (SM-2 check 5): a Practice Quiz with every Question answered, one wrong ---------
    quiz_tab = client.get(topic_tab(topic_id, "quiz")).content.decode()
    assert "Velg antall og start" in quiz_tab
    start_dialog = client.get(reverse("quiz:start", args=[topic_id])).content.decode()
    available = int(found(r"(\d+) spørsmål tilgjengelig", start_dialog, "D06's available count").group(1))
    response = client.post(
        reverse("quiz:start", args=[topic_id]), {"count": str(available), "start_token": "uj5"}, follow=True
    )
    quiz = Quiz.objects.get(student__email=EMAIL, kind=QuizKind.PRACTICE)
    assert response.redirect_chain[-1][0] == reverse("quiz:question", args=[quiz.id, 1])
    positions = list(QuizQuestion.objects.filter(quiz=quiz).order_by("position").select_related("question"))
    assert len(positions) == available
    multiple_choice = [qq for qq in positions if qq.question.kind == "multiple_choice"]
    assert multiple_choice, "the Sample's Quiz has no multiple-choice Question to answer wrong"
    wrong_mc = multiple_choice[0]
    for qq in positions:
        question = qq.question
        page = client.get(reverse("quiz:question", args=[quiz.id, qq.position]))
        assert page.status_code == 200
        if question.kind == "multiple_choice":
            assert len(question.options) >= 2, f"Question {question.id} has fewer than two options"
            wrong = (question.correct_index + 1) % len(question.options)
            choice = wrong if qq is wrong_mc else question.correct_index
            data = {"choice": choice}
        else:
            data = {"text": question.model_answer}
        response = client.post(reverse("quiz:answer", args=[quiz.id, qq.position]), data)
        assert response.status_code in (200, 302), f"answer at position {qq.position}: {response.status_code}"
    assert Answer.objects.filter(quiz=quiz).count() == available

    # The result page, P07.
    response = client.get(reverse("quiz:resume", args=[quiz.id]), follow=True)
    assert response.redirect_chain[-1][0] == reverse("quiz:result", args=[quiz.id])
    result = text_of(response.content.decode())
    assert "Resultat" in result
    missed = {
        a.question_id for a in Answer.objects.filter(quiz=quiz) if a.grade in (Grade.INCORRECT, Grade.PARTIAL)
    }
    assert wrong_mc.question_id in missed
    assert f"Øv på feilene ({len(missed)})" in result

    # «Øv på feilene» holds exactly the missed Questions; answer them.
    response = client.post(reverse("quiz:retry", args=[quiz.id]), follow=True)
    retry = Quiz.objects.get(student__email=EMAIL, kind=QuizKind.RETRY)
    assert response.redirect_chain[-1][0] == reverse("quiz:question", args=[retry.id, 1])
    retry_positions = list(QuizQuestion.objects.filter(quiz=retry).order_by("position").select_related("question"))
    assert {qq.question_id for qq in retry_positions} == missed
    for qq in retry_positions:
        question = qq.question
        data = {"choice": question.correct_index} if question.kind == "multiple_choice" else {"text": question.model_answer}
        response = client.post(reverse("quiz:answer", args=[retry.id, qq.position]), data)
        assert response.status_code in (200, 302), f"retry answer at position {qq.position}: {response.status_code}"
    response = client.get(reverse("quiz:resume", args=[retry.id]), follow=True)
    assert response.redirect_chain[-1][0] == reverse("quiz:result", args=[retry.id])
    assert Answer.objects.filter(quiz=retry).count() == len(missed)

    # ---- Step 6: a Review from «I dag», rating every card until «Repetisjonen er ferdig» ---------
    home = client.get("/").content.decode()
    today = int(found(r"I dag · <b>(\d+)</b>", home, "«I dag · N»").group(1))
    assert today == card_count
    # The «I dag · N» link in the fag-rail opens Repetisjon for every fag.
    today_href = found(r'<a class="rail-link" href="([^"]+)">[^\n]*I dag · <b>', home, "the «I dag» link").group(1)
    today_href = today_href.replace("&amp;", "&")
    assert today_href.startswith(reverse("review:start"))
    start = client.get(today_href)
    assert start.status_code == 302
    session_url = start["Location"]
    review_id = id_from(session_url)
    rated = 0
    while True:
        page = client.get(session_url).content.decode()
        if "Repetisjonen er ferdig" in page:
            break
        card_id = int(found(r'name="flashcard" value="(\d+)"', page, "the card being reviewed").group(1))
        step = int(found(r'name="step" value="(\d+)"', page, "the review step").group(1))
        response = client.post(
            reverse("review:rate", args=[review_id]), {"flashcard": card_id, "step": step, "rating": RatingValue.GOOD}
        )
        assert response.status_code == 302
        rated += 1
        assert rated <= card_count, "the Review did not end"
    assert rated == card_count
    assert Rating.objects.filter(student__email=EMAIL).count() == card_count
    assert f"Du repeterte {card_count} kort." in page
    found(r"I dag · <b>0</b>", client.get("/").content.decode(), "«I dag · 0» after the Review")

    # ---- Persistence (SM-2 check 6): sign out and in, data unchanged -------------------------------
    before = snapshot(EMAIL)
    response = client.post(reverse("accounts:sign_out"))
    assert response["Location"] == reverse("accounts:sign_in")
    assert client.get("/").status_code == 302
    response = client.post(reverse("accounts:sign_in"), {"username": EMAIL, "password": PASSWORD})
    assert response.status_code == 302
    assert snapshot(EMAIL) == before
    home = text_of(client.get("/").content.decode())
    assert "Databaser" in home
    summary_tab = client.get(topic_tab(topic_id, "summary")).content.decode()
    assert summary_tab.count('class="key-concept-item"') >= 5
    assert MESSAGES["removed_note_one"] in summary_tab
    history = text_of(client.get(topic_tab(topic_id, "quiz")).content.decode())
    assert f"{available - len(missed)} av {available} riktige" in history


def test_uj5_other_pdf_in_mock_mode_is_stored_with_the_needs_key_message(now, mock_mode):
    client = TimedClient()
    topic_id = sign_up_and_create_topic(client)

    upload = SimpleUploadedFile("egne-notater.pdf", make_pdf([LECTURE_TEXT, LECTURE_TEXT]), content_type="application/pdf")
    response = client.post(
        reverse("studymat:add_source", args=[topic_id]),
        {"file": upload, "detail_level": "medium", "text": "", "name": ""},
        HTTP_HX_REQUEST="true",
        HTTP_HX_TARGET="dialog",
    )
    assert json.loads(response["HX-Location"])["path"] == topic_tab(topic_id, "sources")
    source = Source.objects.get(student__email=EMAIL)
    assert source.name == "egne-notater.pdf"
    assert source.texts.count() == 2

    body = client.post(
        reverse("studymat:generate", args=[source.id]), HTTP_HX_REQUEST="true", HTTP_HX_TARGET=f"source-{source.id}"
    ).content.decode()
    source.refresh_from_db()
    assert (source.status, source.failure_reason) == (Status.FAILED, FailureReason.NEEDS_KEY)
    assert MESSAGES["needs_key"] in body
    sources_tab = client.get(topic_tab(topic_id, "sources")).content.decode()
    assert "egne-notater.pdf" in sources_tab and MESSAGES["needs_key"] in sources_tab
    assert not Summary.objects.filter(source=source).exists()
    for model in (KeyConcept, Flashcard, Question):
        assert not model.objects.filter(source=source).exists()


def test_uj5_committed_51_page_pdf_is_refused_naming_the_page_limit(now, mock_mode):
    """SM-2 check 4 (FR-3): the README's upload of sample/for_mange_sider.pdf is refused."""
    client = TimedClient()
    topic_id = sign_up_and_create_topic(client)
    upload = SimpleUploadedFile(TOO_MANY_PAGES_PDF.name, TOO_MANY_PAGES_PDF.read_bytes(), content_type="application/pdf")
    response = client.post(
        reverse("studymat:add_source", args=[topic_id]),
        {"file": upload, "detail_level": "medium", "text": "", "name": ""},
        HTTP_HX_REQUEST="true",
        HTTP_HX_TARGET="dialog",
    )
    assert response.status_code == 200 and "HX-Location" not in response
    assert MESSAGES["too_many_pages"].format(pages=51, limit=50) in response.content.decode()
    assert not Source.objects.filter(student__email=EMAIL).exists()
