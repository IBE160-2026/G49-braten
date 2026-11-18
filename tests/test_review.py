"""FR-15 / CAP-9 (story 11): Due cards, Leitner Reviews (P09) and the «I dag · N» entry points."""

import datetime
import re

import pytest
from django.test import Client
from django.urls import reverse

from core import time
from courses import services as course_services
from courses.models import Course, Source, Status
from courses.scope import Scope
from review import services
from review.models import Rating, Review, ReviewState
from review.rules import RatingValue
from studymat.models import Flashcard
from tests.test_topic_page import main_of, ready_source, text_of, topic_url

pytestmark = pytest.mark.django_db

NOON = datetime.datetime(2026, 11, 18, 12, 0, tzinfo=time.OSLO)
TODAY = NOON.date()
CARD = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "review-card"}


def day(n: int) -> datetime.date:
    return TODAY + datetime.timedelta(days=n)


def cards(n: int, prefix: str = "Kort") -> tuple:
    return tuple((f"{prefix} {i}?", f"Svar {prefix} {i}.") for i in range(1, n + 1))


def rail_of(content: str) -> str:
    return content.split('<nav class="fag-rail"', 1)[1].split("</nav>", 1)[0]


def today_count(client) -> int:
    """N in the fag-rail's «I dag · N»."""
    match = re.search(r"I dag · <b>(\d+)</b>", rail_of(client.get("/").content.decode()))
    return int(match.group(1))


def start_url(**params) -> str:
    query = "&".join(f"{key}={value}" for key, value in params.items())
    return reverse("review:start") + (f"?{query}" if query else "")


def session_url(review) -> str:
    return reverse("review:session", args=[review.id])


def rate_url(review) -> str:
    return reverse("review:rate", args=[review.id])


def current_front(client, review) -> str:
    main = main_of(client.get(session_url(review)).content.decode())
    return re.search(r'id="review-front"[^>]*>([^<]*)<', main).group(1)


def current_step(client, review) -> tuple[int, int]:
    main = main_of(client.get(session_url(review)).content.decode())
    card_id = int(re.search(r'name="flashcard" value="(\d+)"', main).group(1))
    step = int(re.search(r'name="step" value="(\d+)"', main).group(1))
    return card_id, step


def rate_current(client, review, rating, **headers):
    card_id, step = current_step(client, review)
    return client.post(rate_url(review), {"flashcard": card_id, "step": step, "rating": rating}, **headers)


@pytest.fixture
def now(freeze_now):
    freeze_now(NOON)
    return freeze_now


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
    return course_services.create_course(ida, "Databaser", "DAT102")


@pytest.fixture
def normalisering(databaser):
    return course_services.create_topic(databaser, "Normalisering")


@pytest.fixture
def transaksjoner(databaser):
    return course_services.create_topic(databaser, "Transaksjoner")


def start_review(client, **params) -> Review:
    response = client.get(start_url(**params))
    assert response.status_code == 302
    return Review.objects.get(pk=int(response["Location"].rstrip("/").rsplit("/", 1)[1]))


# ---- Matrix: New cards ---------------------------------------------------------------------


def test_fr15_new_cards_twenty_a_day_in_generation_order(now, ida, normalisering, transaksjoner):
    first = ready_source(normalisering, name="a.pdf", cards=cards(15, "A"))
    second = ready_source(transaksjoner, name="b.pdf", cards=cards(10, "B"))
    due = list(services.due_cards(ida, Scope.all()))
    assert len(due) == 20
    expected = list(Flashcard.objects.filter(source=first).order_by("id")) + list(
        Flashcard.objects.filter(source=second).order_by("id")[:5]
    )
    assert [state.flashcard_id for state in due] == [card.id for card in expected]
    assert all(state.box == 1 and state.due_date == TODAY and state.introduced_on == TODAY for state in due)
    # Idempotent per day: asking again introduces nothing more.
    assert services.introduce_today(ida) == 0
    assert ReviewState.objects.count() == 20

    now(NOON + datetime.timedelta(days=1))
    assert services.due_cards(ida, Scope.all()).count() == 25
    assert ReviewState.objects.filter(introduced_on=day(1)).count() == 5


def test_fr15_topic_scope_never_changes_which_cards_are_introduced(now, ida, normalisering, transaksjoner):
    ready_source(normalisering, name="a.pdf", cards=cards(15, "A"))
    ready_source(transaksjoner, name="b.pdf", cards=cards(10, "B"))
    # Asking for Transaksjoner first still introduces in generation order across all fag.
    assert services.due_cards(ida, Scope(topic_id=transaksjoner.id)).count() == 5
    assert services.due_cards(ida, Scope(topic_id=normalisering.id)).count() == 15


def test_fr15_only_ready_sources_count(now, ida, normalisering):
    source = ready_source(normalisering, cards=cards(3))
    Source.objects.filter(pk=source.pk).update(status=Status.FAILED)
    assert services.due_cards(ida, Scope.all()).count() == 0
    assert ReviewState.objects.count() == 0


# ---- Matrix: Topic Review ------------------------------------------------------------------


def test_fr15_topic_review_holds_only_that_topics_cards(now, client_ida, ida, normalisering, transaksjoner):
    ready_source(normalisering, name="a.pdf", cards=cards(2, "A"))
    ready_source(transaksjoner, name="b.pdf", cards=cards(2, "B"))
    review = start_review(client_ida, topic=normalisering.id)
    assert review.topic_id == normalisering.id and review.course_id is None
    main = main_of(client_ida.get(session_url(review)).content.decode())
    assert "1 av 2" in client_ida.get(session_url(review)).content.decode()
    assert "Databaser › Normalisering" in main
    for _ in range(2):
        assert current_front(client_ida, review).startswith("A ")
        rate_current(client_ida, review, RatingValue.GOOD)
    body = client_ida.get(session_url(review)).content.decode()
    assert "Repetisjonen er ferdig" in body and "Du repeterte 2 kort." in body
    assert services.due_cards(ida, Scope(topic_id=transaksjoner.id)).count() == 2


def test_fr15_context_label_names_the_scope(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    all_review = start_review(client_ida)
    assert '<p class="session-context">I dag · repetisjon</p>' in client_ida.get(session_url(all_review)).content.decode()
    topic_review = start_review(client_ida, topic=normalisering.id)
    assert topic_review.id != all_review.id
    body = client_ida.get(session_url(topic_review)).content.decode()
    assert '<p class="session-context">Normalisering · repetisjon</p>' in body
    course_review = start_review(client_ida, course=normalisering.course_id)
    assert course_review.id not in (all_review.id, topic_review.id)
    body = client_ida.get(session_url(course_review)).content.decode()
    assert '<p class="session-context">Databaser · repetisjon</p>' in body


def test_fr15_course_review_holds_only_that_courses_cards(now, client_ida, ida, databaser, normalisering):
    statistikk = course_services.create_course(ida, "Statistikk")
    ready_source(normalisering, name="a.pdf", cards=cards(2, "A"))
    ready_source(course_services.create_topic(statistikk, "Regresjon"), name="s.pdf", cards=cards(3, "S"))
    review = start_review(client_ida, course=databaser.id)
    assert review.course_id == databaser.id and review.topic_id is None
    assert "1 av 2" in client_ida.get(session_url(review)).content.decode()
    for _ in range(2):
        assert current_front(client_ida, review).startswith("A ")
        rate_current(client_ida, review, RatingValue.GOOD)
    assert "Du repeterte 2 kort." in client_ida.get(session_url(review)).content.decode()
    assert services.due_cards(ida, Scope(course_id=statistikk.id)).count() == 3


def test_fr15_overdue_cards_come_first(now, client_ida, ida, normalisering):
    ready_source(normalisering, name="a.pdf", cards=(("Tidlig kilde?", "a"),))
    ready_source(normalisering, name="b.pdf", cards=(("Forfalt fra senere kilde?", "b"),))
    services.introduce_today(ida)
    ReviewState.objects.filter(flashcard__front="Forfalt fra senere kilde?").update(due_date=day(-2))
    review = start_review(client_ida)
    assert current_front(client_ida, review) == "Forfalt fra senere kilde?"


# ---- Matrix: Good streak, Cap --------------------------------------------------------------


def test_fr15_good_streak_through_the_service(now, ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    state = services.due_cards(ida, Scope.all()).get()
    card = state.flashcard
    review = services.start(ida, Scope.all(), "/")
    for step, (box, gap) in enumerate([(2, 3), (3, 7), (4, 14)], start=1):
        assert services.rate(review, card, RatingValue.GOOD, step)
        state.refresh_from_db()
        assert (state.box, state.due_date) == (box, day(gap))


def test_fr15_cap_at_box_eight(now, ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    state = services.due_cards(ida, Scope.all()).get()
    ReviewState.objects.filter(pk=state.pk).update(box=8)
    review = services.start(ida, Scope.all(), "/")
    services.rate(review, state.flashcard, RatingValue.EASY, 1)
    state.refresh_from_db()
    assert (state.box, state.due_date) == (8, day(180))


# ---- Matrix: Igjen, progress -----------------------------------------------------------------


def test_fr15_again_card_comes_after_the_others_and_progress_never_runs_back(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(3))
    review = start_review(client_ida)
    assert current_front(client_ida, review) == "Kort 1?"
    assert "1 av 3" in client_ida.get(session_url(review)).content.decode()
    rate_current(client_ida, review, RatingValue.AGAIN)
    state = ReviewState.objects.get(flashcard__front="Kort 1?")
    assert (state.box, state.due_date) == (1, TODAY)
    assert "1 av 3" in client_ida.get(session_url(review)).content.decode()
    assert current_front(client_ida, review) == "Kort 2?"
    rate_current(client_ida, review, RatingValue.GOOD)
    assert "2 av 3" in client_ida.get(session_url(review)).content.decode()
    assert current_front(client_ida, review) == "Kort 3?"
    rate_current(client_ida, review, RatingValue.GOOD)
    assert current_front(client_ida, review) == "Kort 1?"
    assert "3 av 3" in client_ida.get(session_url(review)).content.decode()
    rate_current(client_ida, review, RatingValue.GOOD)
    body = client_ida.get(session_url(review)).content.decode()
    assert "Du repeterte 3 kort." in body
    review.refresh_from_db()
    assert review.ended_at is not None


# ---- Matrix: Double tap --------------------------------------------------------------------


def test_fr15_double_tap_moves_the_card_once(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(2))
    review = start_review(client_ida)
    card_id, step = current_step(client_ida, review)
    data = {"flashcard": card_id, "step": step, "rating": RatingValue.EASY}
    client_ida.post(rate_url(review), data)
    client_ida.post(rate_url(review), data)
    assert Rating.objects.filter(review=review).count() == 1
    state = ReviewState.objects.get(flashcard_id=card_id)
    assert (state.box, state.due_date) == (3, day(7))


def test_fr15_double_tap_on_again_rates_once(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    review = start_review(client_ida)
    card_id, step = current_step(client_ida, review)
    data = {"flashcard": card_id, "step": step}
    client_ida.post(rate_url(review), {**data, "rating": RatingValue.AGAIN})
    client_ida.post(rate_url(review), {**data, "rating": RatingValue.GOOD})
    assert list(Rating.objects.values_list("rating", flat=True)) == [RatingValue.AGAIN]
    assert ReviewState.objects.get(flashcard_id=card_id).due_date == TODAY


def test_fr15_rating_a_card_no_longer_due_writes_nothing(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(2))
    review = start_review(client_ida)
    card_id, step = current_step(client_ida, review)
    client_ida.post(rate_url(review), {"flashcard": card_id, "step": step, "rating": RatingValue.GOOD})
    # A stale tab rates the same card again with a fresh step: it is no longer due.
    client_ida.post(rate_url(review), {"flashcard": card_id, "step": step + 1, "rating": RatingValue.EASY})
    assert Rating.objects.filter(review=review).count() == 1
    state = ReviewState.objects.get(flashcard_id=card_id)
    assert (state.box, state.due_date) == (2, day(3))


def test_fr15_rating_in_an_ended_review_writes_nothing(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    review = start_review(client_ida)
    card_id, step = current_step(client_ida, review)
    services.finish(review)
    response = client_ida.post(rate_url(review), {"flashcard": card_id, "step": step, "rating": RatingValue.GOOD})
    assert response.status_code == 302
    assert not Rating.objects.exists()
    state = ReviewState.objects.get(flashcard_id=card_id)
    assert (state.box, state.due_date) == (1, TODAY)


def test_fr15_rate_is_a_no_op_when_the_state_is_gone(now, ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    state = services.due_cards(ida, Scope.all()).get()
    card = state.flashcard
    review = services.start(ida, Scope.all(), "/")
    state.delete()
    assert services.rate(review, card, RatingValue.GOOD, 1) is False
    assert not Rating.objects.exists()


# ---- Matrix: Nothing due -------------------------------------------------------------------


def test_fr15_cards_held_back_by_the_daily_limit_come_tomorrow_on_the_nothing_due_screen(now, client_ida, ida, normalisering):
    ready_source(normalisering, cards=cards(21))
    services.introduce_today(ida)
    ReviewState.objects.update(due_date=day(5))
    body = text_of(client_ida.get(start_url()).content.decode())
    assert "Ingen kort i dag. Neste kort kommer 19. november." in body
    assert Review.objects.count() == 0


def test_fr15_cards_held_back_by_the_daily_limit_come_tomorrow_on_the_end_screen(now, client_ida, ida, normalisering):
    ready_source(normalisering, cards=cards(21))
    services.introduce_today(ida)
    keep = ReviewState.objects.order_by("flashcard_id").first()
    ReviewState.objects.exclude(pk=keep.pk).update(due_date=day(5))
    review = start_review(client_ida, topic=normalisering.id)
    rate_current(client_ida, review, RatingValue.GOOD)
    body = text_of(client_ida.get(session_url(review)).content.decode())
    assert "Du repeterte 1 kort. Neste kort kommer i morgen." in body


def test_fr15_nothing_due_creates_no_review(now, client_ida, ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    state = services.due_cards(ida, Scope.all()).get()
    ReviewState.objects.filter(pk=state.pk).update(due_date=day(2))
    response = client_ida.get(start_url(next=topic_url(normalisering, "selftest")))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Ingen kort i dag. Neste kort kommer 20. november." in text_of(body)
    assert f'href="{topic_url(normalisering, "selftest")}">Tilbake</a>' in body
    assert Review.objects.count() == 0


def test_fr15_nothing_at_all_says_nothing_is_planned(now, client_ida):
    body = client_ida.get(start_url()).content.decode()
    assert "Ingen kort i dag. Ingen flere kort er planlagt." in text_of(body)
    assert 'href="/">Tilbake</a>' in body
    assert Review.objects.count() == 0


# ---- Matrix: Not owned ---------------------------------------------------------------------


def test_fr15_another_students_review_or_card_is_404(now, client_ida, student, normalisering):
    ready_source(normalisering, cards=cards(1))
    review = start_review(client_ida)
    card_id, step = current_step(client_ida, review)
    other = Client()
    other.force_login(student("jonas@example.no"))
    assert other.get(session_url(review)).status_code == 404
    assert other.post(rate_url(review), {"flashcard": card_id, "step": step, "rating": "good"}).status_code == 404
    assert other.get(start_url(topic=normalisering.id)).status_code == 404
    assert other.get(start_url(course=normalisering.course_id)).status_code == 404
    assert Rating.objects.count() == 0


def test_fr15_rating_another_students_card_in_your_review_is_404(now, client_ida, ida, student, normalisering):
    ready_source(normalisering, cards=cards(1))
    ida_card = Flashcard.objects.get()
    jonas = student("jonas@example.no")
    jonas_topic = course_services.create_topic(course_services.create_course(jonas, "Statistikk"), "Regresjon")
    ready_source(jonas_topic, cards=cards(1))
    jonas_client = Client()
    jonas_client.force_login(jonas)
    review = start_review(jonas_client)
    response = jonas_client.post(rate_url(review), {"flashcard": ida_card.id, "step": 1, "rating": "good"})
    assert response.status_code == 404
    assert Rating.objects.count() == 0


def test_fr15_bad_start_params_are_404(now, client_ida):
    assert client_ida.get(start_url(topic="x")).status_code == 404
    assert client_ida.get(start_url(course="999")).status_code == 404


# ---- Matrix: Card deleted mid-Review -------------------------------------------------------


def test_fr15_card_deleted_mid_review_takes_state_and_ratings_and_review_continues(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(3))
    review = start_review(client_ida)
    rate_current(client_ida, review, RatingValue.AGAIN)
    card = Flashcard.objects.get(front="Kort 1?")
    assert Rating.objects.filter(flashcard=card).exists()
    response = client_ida.post(
        reverse("studymat:delete_item", args=["card", card.id]), {"next": session_url(review)}, follow=True
    )
    assert response.status_code == 200
    assert not ReviewState.objects.filter(flashcard_id=card.id).exists()
    assert not Rating.objects.filter(flashcard_id=card.id).exists()
    assert "1 av 2" in response.content.decode()
    assert current_front(client_ida, review) == "Kort 2?"


# ---- Matrix: Oslo day ----------------------------------------------------------------------


def test_fr15_rating_at_half_past_midnight_counts_the_oslo_date(now, ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    # 23:30 UTC on 18 November is 00:30 on 19 November in Oslo.
    now(datetime.datetime(2026, 11, 18, 23, 30, tzinfo=datetime.UTC))
    state = services.due_cards(ida, Scope.all()).get()
    assert state.introduced_on == datetime.date(2026, 11, 19)
    review = services.start(ida, Scope.all(), "/")
    services.rate(review, state.flashcard, RatingValue.GOOD, 1)
    state.refresh_from_db()
    assert state.due_date == datetime.date(2026, 11, 22)


# ---- P09: flip, buttons, HTMX and no-JS ----------------------------------------------------


def test_fr15_front_first_then_back_with_reference_and_real_return_times(now, client_ida, normalisering):
    ready_source(normalisering, cards=(("Hva er 1NF?", "Atomiske verdier."),))
    review = start_review(client_ida)
    main = main_of(client_ida.get(session_url(review)).content.decode())
    assert "Forside" in main and "Vis svaret" in main
    assert f'href="{session_url(review)}?vis=svar" data-flip' in main
    assert re.search(r'<div class="review-card-back" data-face="back" hidden>', main)
    assert re.search(r'<form class="review-rate"[^>]* hidden', main)
    assert re.search(r'id="review-front"[^>]*autofocus', main)

    flipped = main_of(client_ida.get(f"{session_url(review)}?vis=svar").content.decode())
    assert '<div class="review-card-back" data-face="back">' in flipped
    assert "Atomiske verdier." in flipped and "Bakside" in flipped
    assert "«sitat Hva er 1NF?»" in flipped
    assert re.search(r'id="review-back"[^>]*autofocus', flipped)
    buttons = re.findall(r'<button class="rating-button".*?</button>', flipped, re.S)
    # The key hint is aria-hidden; the rest is each button's name and when the card returns.
    spoken = [text_of(re.sub(r'<kbd[^>]*aria-hidden="true">.*?</kbd>', "", b)).replace(" ,", ",") for b in buttons]
    assert spoken == [
        "Igjen, kommer tilbake i dag",
        "Vanskelig, kommer tilbake i morgen",
        "Bra, kommer tilbake om 3 dager",
        "Lett, kommer tilbake om 1 uke",
    ]
    assert [re.search(r'data-key="(\d)"', b).group(1) for b in buttons] == ["1", "2", "3", "4"]


def test_fr15_rating_without_js_redirects_to_the_session(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(2))
    review = start_review(client_ida)
    response = rate_current(client_ida, review, RatingValue.GOOD)
    assert response.status_code == 302 and response["Location"] == session_url(review)


def test_fr15_rating_under_htmx_swaps_the_next_card_with_focus_and_the_session_bar(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(2))
    review = start_review(client_ida)
    response = rate_current(client_ida, review, RatingValue.GOOD, **CARD)
    assert response.status_code == 200
    body = response.content.decode()
    assert "<html" not in body and "<main" not in body
    assert '<header class="session-bar" id="session-bar" hx-swap-oob="true">' in body
    assert "2 av 2" in body
    assert re.search(r'id="review-front"[^>]*autofocus[^>]*>Kort 2\?<', body)
    assert '<div id="live-polite" hx-swap-oob="innerHTML">Kort 2 av 2</div>' in body
    assert "HX-Target" in response["Vary"]

    end = rate_current(client_ida, review, RatingValue.GOOD, **CARD).content.decode()
    assert "Repetisjonen er ferdig" in end and "session-bar--result" in end


# ---- Entry points --------------------------------------------------------------------------


def test_fr15_start_reuses_todays_open_review_and_checks_next(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    first = start_review(client_ida, next="/courses/1/")
    again = start_review(client_ida, next="https://evil.example/")
    assert first.id == again.id and Review.objects.count() == 1
    again.refresh_from_db()
    assert again.return_url == "/"
    assert '<a class="session-exit" href="/">' in client_ida.get(session_url(again)).content.decode()

    # A Review left open yesterday is not reused.
    now(NOON + datetime.timedelta(days=1))
    assert start_review(client_ida).id != first.id


def test_fr15_rail_top_bar_and_switcher_show_real_counts_and_link_to_start(now, client_ida, databaser, normalisering):
    statistikk = course_services.create_course(databaser.student, "Statistikk")
    ready_source(normalisering, cards=cards(3))
    ready_source(course_services.create_topic(statistikk, "Regresjon"), name="s.pdf", cards=cards(2, "S"))
    body = client_ida.get("/").content.decode()
    rail = rail_of(body)
    assert re.search(r'<a class="rail-link" href="/reviews/start/\?next=/">.*I dag · <b>5</b>', rail)
    assert ", 3 kort i dag" in rail and ", 2 kort i dag" in rail
    assert re.search(r'<a class="today-chip" href="/reviews/start/\?next=/">.*I dag · <b>5</b>', body)
    assert '<span class="fag-switcher-due"><b>5</b> i dag</span>' in body
    assert "3 i dag · –" in body and "2 i dag · –" in body
    # The switcher shows the count; its «I dag · N» link is the top-bar's, so the fag listbox has none.
    switcher = body.split('<nav class="fag-switcher"', 1)[1].split("</nav>", 1)[0]
    assert "/reviews/start/" not in switcher
    course_page = client_ida.get(reverse("web:course", args=[statistikk.id])).content.decode()
    assert '<span class="fag-switcher-due"><b>2</b> i dag</span>' in course_page


def test_fr15_acceptance_three_good_ratings_end_and_today_drops(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(3))
    assert today_count(client_ida) == 3
    review = start_review(client_ida)
    for _ in range(3):
        rate_current(client_ida, review, RatingValue.GOOD)
    body = text_of(client_ida.get(session_url(review)).content.decode())
    assert "Repetisjonen er ferdig" in body
    assert "Du repeterte 3 kort. Neste kort kommer om 3 dager." in body
    assert today_count(client_ida) == 0


def test_fr15_selftest_tab_counts_due_and_starts_a_topic_review(now, client_ida, ida, normalisering):
    ready_source(normalisering, cards=cards(3))
    main = main_of(client_ida.get(topic_url(normalisering, "selftest")).content.decode())
    assert "3 kort i temaet. 3 forfaller i dag." in text_of(main)
    expected = f"/reviews/start/?topic={normalisering.id}&amp;next=%2Ftopics%2F{normalisering.id}%2F%3Ftab%3Dselftest"
    assert f'<a class="button-secondary" href="{expected}">Repeter dagens kort (3)</a>' in main
    # The existing card list stays.
    assert main.count('class="flashcard-item"') == 3

    review = start_review(client_ida, topic=normalisering.id, next=f"/topics/{normalisering.id}/?tab=selftest")
    before = dict(ReviewState.objects.values_list("flashcard_id", "due_date"))
    card_id, _ = current_step(client_ida, review)
    rate_current(client_ida, review, RatingValue.GOOD)
    after = dict(ReviewState.objects.values_list("flashcard_id", "due_date"))
    assert after.pop(card_id) == day(3)
    before.pop(card_id)
    assert after == before
    main = main_of(client_ida.get(topic_url(normalisering, "selftest")).content.decode())
    assert "3 kort i temaet. 2 forfaller i dag." in text_of(main)
    assert "Repeter dagens kort (2)" in main


def test_fr15_selftest_tab_with_nothing_due_says_so(now, client_ida, ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    ReviewState.objects.filter(pk=services.due_cards(ida, Scope.all()).get().pk).update(due_date=day(1))
    main = main_of(client_ida.get(topic_url(normalisering, "selftest")).content.decode())
    assert "1 kort i temaet. 0 forfaller i dag." in text_of(main)
    assert "Ingen kort i dag" in main and "Repeter dagens kort" not in main


# ---- Ownership and cascade (AD-7, AD-8) ----------------------------------------------------


def test_fr15_every_row_has_the_parents_student(now, client_ida, ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    review = start_review(client_ida)
    rate_current(client_ida, review, RatingValue.GOOD)
    state = ReviewState.objects.get()
    rating = Rating.objects.get()
    assert state.student_id == state.flashcard.student_id == ida.id
    assert rating.student_id == rating.review.student_id == rating.flashcard.student_id
    assert review.student_id == ida.id


def test_fr15_deleting_a_course_removes_states_reviews_and_ratings(now, client_ida, databaser, normalisering):
    ready_source(normalisering, cards=cards(2))
    review = start_review(client_ida, course=databaser.id)
    rate_current(client_ida, review, RatingValue.GOOD)
    Course.objects.filter(pk=databaser.pk).delete()
    assert not ReviewState.objects.exists()
    assert not Rating.objects.exists()
    assert not Review.objects.exists()
