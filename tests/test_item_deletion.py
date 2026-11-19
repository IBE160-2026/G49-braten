"""FR-24 / CAP-6 (story 7): D09 deletes one Key concept, Flashcard or Question (AD-8 hard delete)."""

import json

import pytest
from django.test import Client
from django.urls import reverse

from core.messages import MESSAGES
from courses import services
from studymat import services as studymat_services
from studymat.models import Flashcard, KeyConcept, Question, Summary
from tests.test_topic_page import main_of, ready_source, tab_of, text_of, topic_url

pytestmark = pytest.mark.django_db

HTMX_DIALOG = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "dialog"}


def delete_url(kind, item_id):
    return reverse("studymat:delete_item", args=[kind, item_id])


def hx_location(response) -> str:
    return json.loads(response["HX-Location"])["path"]


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def client_ida(ida):
    client = Client()
    client.force_login(ida)
    return client


@pytest.fixture
def normalisering(ida):
    return services.create_topic(services.create_course(ida, "Databaser", "DAT102"), "Normalisering")


@pytest.fixture
def source(normalisering):
    return ready_source(
        normalisering,
        concepts=(("3NF", "Tredje normalform."), ("BCNF", "Boyce-Codd.")),
        cards=(("Kort A", "a"), ("Kort B", "b"), ("Kort C", "c")),
        questions=("Spørsmål A?", "Spørsmål B?"),
    )


# ---- Matrix: Delete card ------------------------------------------------------------------


def test_fr24_delete_card_from_bla_i_kort_lands_back_with_one_card_fewer(client_ida, normalisering, source):
    """Story 11b: cards are deleted from P08 «Bla i kort»; D09's `next` is that position."""
    card = Flashcard.objects.get(front="Kort A")
    page = client_ida.get(topic_url(normalisering, "selftest")).content.decode()
    assert text_of(tab_of(main_of(page), "selftest")).endswith("Test deg selv · 3 kort")
    next_url = reverse("review:browse", args=[normalisering.id, 1])
    p08 = client_ida.get(next_url).content.decode()
    # D09 opens as a full page from the session layout (a normal POST/redirect, no HX-Location).
    assert f'href="{delete_url("card", card.id)}?next={next_url}">' in p08
    assert "hx-get" not in p08.split('class="menu-item menu-item--destructive"', 1)[1].split("</a>", 1)[0]
    dialog = client_ida.get(f"{delete_url('card', card.id)}?next={next_url}", **HTMX_DIALOG).content.decode()
    assert dialog.lstrip().startswith('<dialog class="dialog" role="alertdialog"')
    assert "Slette kortet?" in dialog and MESSAGES["delete_cannot_undo"] in dialog
    assert "Slett kortet</button>" in dialog
    assert f'name="next" value="{next_url}"' in dialog

    response = client_ida.post(delete_url("card", card.id), {"next": next_url}, follow=True)
    assert response.redirect_chain[-1][0] == next_url
    main = main_of(response.content.decode())
    assert "Kort A" not in main and "Kort B" in main
    assert not Flashcard.objects.filter(pk=card.pk).exists()
    page = client_ida.get(topic_url(normalisering, "selftest")).content.decode()
    assert text_of(tab_of(main_of(page), "selftest")).endswith("Test deg selv · 2 kort")
    # The rest of that Source is untouched.
    assert KeyConcept.objects.filter(source=source).count() == 2
    assert Question.objects.filter(source=source).count() == 2
    assert Summary.objects.filter(source=source).exists()


def test_fr24_delete_card_without_next_lands_on_selftest(client_ida, normalisering, source):
    card = Flashcard.objects.get(front="Kort B")
    response = client_ida.post(delete_url("card", card.id), **HTMX_DIALOG)
    assert hx_location(response) == topic_url(normalisering, "selftest")


# ---- Matrix: Delete concept ---------------------------------------------------------------


def test_fr24_delete_concept_answers_hx_location_to_sammendrag_and_count_drops(client_ida, normalisering, source):
    concept = KeyConcept.objects.get(term="3NF")
    page = main_of(client_ida.get(topic_url(normalisering)).content.decode())
    assert page.count('class="key-concept-item"') == 2
    url = delete_url("concept", concept.id)
    assert f'hx-get="{url}?next={topic_url(normalisering)}"' in page
    dialog = client_ida.get(url, **HTMX_DIALOG).content.decode()
    assert "Slette nøkkelbegrepet 3NF?" in dialog
    assert "Slett nøkkelbegrepet</button>" in dialog
    assert MESSAGES["delete_cannot_undo"] in dialog

    response = client_ida.post(url, **HTMX_DIALOG)
    assert response.status_code == 200
    assert hx_location(response) == topic_url(normalisering, "summary")
    page = main_of(client_ida.get(topic_url(normalisering)).content.decode())
    assert page.count('class="key-concept-item"') == 1
    assert "BCNF" in page and ">3NF<" not in page
    assert Flashcard.objects.filter(source=source).count() == 3


def test_fr24_delete_concept_dialog_is_a_full_page_without_htmx(client_ida, source):
    concept = KeyConcept.objects.get(term="BCNF")
    page = client_ida.get(delete_url("concept", concept.id)).content.decode()
    assert page.startswith("<!doctype html>")
    assert "Slette nøkkelbegrepet BCNF?" in page
    assert f'action="{delete_url("concept", concept.id)}"' in page


# ---- Question: service and route, no P05 trigger ------------------------------------------


def test_fr24_delete_question_route_deletes_and_lands_on_quiz(client_ida, normalisering, source):
    question = Question.objects.get(prompt="Spørsmål A?")
    dialog = client_ida.get(delete_url("question", question.id), **HTMX_DIALOG).content.decode()
    assert "Slette spørsmålet?" in dialog and "Slett spørsmålet</button>" in dialog
    response = client_ida.post(delete_url("question", question.id))
    assert response["Location"] == topic_url(normalisering, "quiz")
    assert not Question.objects.filter(pk=question.pk).exists()
    main = main_of(client_ida.get(topic_url(normalisering, "quiz")).content.decode())
    assert text_of(tab_of(main, "quiz")).endswith("Quiz · 1")
    assert "1 spørsmål er klart." in main


def test_fr24_p05_has_no_question_delete_trigger(client_ida, normalisering, source):
    for tab in ("summary", "quiz", "selftest", "sources"):
        content = client_ida.get(topic_url(normalisering, tab)).content.decode()
        assert "/items/question/" not in content


def test_fr24_delete_item_service_is_a_hard_delete(ida, source):
    concept = KeyConcept.objects.filter(source=source).first()
    studymat_services.delete_item(ida, concept)
    assert not KeyConcept.objects.filter(pk=concept.pk).exists()


def test_fr24_delete_item_service_refuses_another_students_item(student, source):
    jonas = student("jonas@example.no")
    concept = KeyConcept.objects.filter(source=source).first()
    with pytest.raises(AssertionError):
        studymat_services.delete_item(jonas, concept)
    assert KeyConcept.objects.filter(pk=concept.pk).exists()


# ---- Matrix: Not owned, Bad kind, No CSRF -------------------------------------------------


@pytest.mark.parametrize("kind", ["concept", "card", "question"])
@pytest.mark.parametrize("method", ["get", "post"])
def test_fr24_another_students_item_is_404_and_nothing_is_deleted(student, source, kind, method):
    model = {"concept": KeyConcept, "card": Flashcard, "question": Question}[kind]
    item = model.objects.filter(source=source).first()
    jonas = Client()
    jonas.force_login(student("jonas@example.no"))
    response = getattr(jonas, method)(delete_url(kind, item.id))
    assert response.status_code == 404
    assert model.objects.filter(pk=item.pk).exists()


@pytest.mark.parametrize("method", ["get", "post"])
def test_fr24_bad_kind_is_404(client_ida, source, method):
    concept = KeyConcept.objects.filter(source=source).first()
    response = getattr(client_ida, method)(f"/items/foo/{concept.id}/delete/")
    assert response.status_code == 404
    # A kind that names another model never reaches an item of a different type.
    assert getattr(client_ida, method)(delete_url("summary", concept.id)).status_code == 404
    assert KeyConcept.objects.filter(pk=concept.pk).exists()


def test_fr24_missing_item_is_404(client_ida, source):
    assert client_ida.get(delete_url("card", 999_999)).status_code == 404


@pytest.mark.parametrize("kind", ["concept", "card", "question"])
def test_fr24_post_without_csrf_is_403_and_nothing_is_deleted(ida, source, kind):
    model = {"concept": KeyConcept, "card": Flashcard, "question": Question}[kind]
    item = model.objects.filter(source=source).first()
    client = Client(enforce_csrf_checks=True)
    client.force_login(ida)
    assert client.post(delete_url(kind, item.id)).status_code == 403
    assert model.objects.filter(pk=item.pk).exists()


def test_fr24_signed_out_is_sent_to_sign_in_and_nothing_is_deleted(client, source):
    concept = KeyConcept.objects.filter(source=source).first()
    response = client.post(delete_url("concept", concept.id))
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:sign_in"))
    assert KeyConcept.objects.filter(pk=concept.pk).exists()


def test_fr24_unsafe_next_is_ignored(client_ida, normalisering, source):
    card = Flashcard.objects.filter(source=source).first()
    response = client_ida.post(delete_url("card", card.id), {"next": "https://example.com/"})
    assert response["Location"] == topic_url(normalisering, "selftest")


def test_fr24_dialog_uses_no_native_confirm(client_ida, source):
    card = Flashcard.objects.filter(source=source).first()
    dialog = client_ida.get(delete_url("card", card.id), **HTMX_DIALOG).content.decode()
    assert "hx-confirm" not in dialog and "confirm(" not in dialog
    # A confirm-delete dialog has no close icon (DESIGN.md, dialog).
    assert 'aria-label="Lukk"' not in dialog


def test_fr24_deleting_the_source_cascades_to_its_items(ida, source):
    services.delete_source(source)
    assert not KeyConcept.objects.exists() and not Flashcard.objects.exists() and not Question.objects.exists()


def test_fr24_deleting_a_card_or_its_source_takes_its_review_state_and_ratings(ida, source):
    """AD-8 (story 11): Leitner state and Ratings go with their Flashcard, and so with its Source."""
    from courses.scope import Scope
    from review import services as review_services
    from review.models import Rating, Review, ReviewState
    from review.rules import RatingValue

    states = list(review_services.due_cards(ida, Scope.all()))
    assert len(states) == 3
    review = review_services.start(ida, Scope.all(), "/")
    review_services.rate(review, states[0].flashcard, RatingValue.AGAIN, 1)
    review_services.rate(review, states[1].flashcard, RatingValue.GOOD, 2)

    studymat_services.delete_item(ida, states[0].flashcard)
    assert not ReviewState.objects.filter(pk=states[0].pk).exists()
    assert Rating.objects.filter(review=review).count() == 1
    # The Review itself and the other cards' state stay.
    assert Review.objects.filter(pk=review.pk).exists() and ReviewState.objects.count() == 2

    services.delete_source(source)
    assert not ReviewState.objects.exists() and not Rating.objects.exists()


# ---- Story 8b: an optional `cancel` for «Avbryt» ------------------------------------------


def test_fr24_cancel_sets_avbryt_and_next_still_sets_the_landing(client_ida, normalisering, source):
    card = Flashcard.objects.get(front="Kort A")
    next_url = topic_url(normalisering, "selftest")
    url = f"{delete_url('card', card.id)}?next={next_url}&cancel=/quizzes/1/2/"
    dialog = client_ida.get(url, **HTMX_DIALOG).content.decode()
    assert 'href="/quizzes/1/2/" data-dialog-close>Avbryt' in dialog
    assert f'name="next" value="{next_url}"' in dialog


@pytest.mark.parametrize("cancel", ["https://example.com/", "//example.com/", "javascript:alert(1)", "quizzes/1/"])
def test_fr24_cancel_refuses_anything_but_a_relative_path(client_ida, normalisering, source, cancel):
    card = Flashcard.objects.get(front="Kort A")
    dialog = client_ida.get(delete_url("card", card.id), {"cancel": cancel}, **HTMX_DIALOG).content.decode()
    assert f'href="{topic_url(normalisering, "selftest")}" data-dialog-close>Avbryt' in dialog
    assert "example.com" not in dialog


def test_fr24_without_cancel_avbryt_follows_next_as_in_story_7(client_ida, normalisering, source):
    concept = KeyConcept.objects.get(term="3NF")
    next_url = topic_url(normalisering)
    dialog = client_ida.get(f"{delete_url('concept', concept.id)}?next={next_url}", **HTMX_DIALOG).content.decode()
    assert f'href="{next_url}" data-dialog-close>Avbryt' in dialog
