"""FR-14 / CAP-9 (story 11b): P08 «Bla i kort», one Flashcard per page in generation order, GET only."""

import datetime
import re

import pytest
from django.test import Client
from django.urls import reverse

from core import time
from courses import services as course_services
from courses.models import Source, Status
from courses.scope import Scope
from review import services as review_services
from review.models import Rating, Review, ReviewState
from studymat.models import Flashcard
from tests.test_topic_page import main_of, panel_of, ready_source, text_of, topic_url

pytestmark = pytest.mark.django_db

NOON = datetime.datetime(2026, 11, 19, 12, 0, tzinfo=time.OSLO)


def browse_url(topic, position=None) -> str:
    if position is None:
        return reverse("review:browse_start", args=[topic.id])
    return reverse("review:browse", args=[topic.id, position])


def selftest_url(topic) -> str:
    return topic_url(topic, "selftest")


def cards(n: int, prefix: str = "Kort") -> tuple:
    return tuple((f"{prefix} {i}?", f"Svar {prefix} {i}.") for i in range(1, n + 1))


def front_of(main: str) -> str:
    return re.search(r'id="review-front"[^>]*>([^<]*)<', main).group(1)


def page(client, topic, position, query="") -> str:
    response = client.get(browse_url(topic, position) + query)
    assert response.status_code == 200
    return response.content.decode()


@pytest.fixture
def now(freeze_now):
    freeze_now(NOON)


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
    return course_services.create_topic(course_services.create_course(ida, "Databaser", "DAT102"), "Normalisering")


# ---- Entry and the page -------------------------------------------------------------------


def test_fr14_bla_i_alle_kort_opens_card_1_of_m_front_showing(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(3))
    panel = panel_of(main_of(client_ida.get(selftest_url(normalisering)).content.decode()))
    href = re.search(r'<a class="button-quiet" href="([^"]+)">Bla i alle kort</a>', panel).group(1)
    assert href == browse_url(normalisering, 1)
    content = page(client_ida, normalisering, 1)
    main = main_of(content)
    assert front_of(main) == "Kort 1?"
    # The front shows; the back and the Reference wait for the flip.
    assert re.search(r'class="review-card-back" data-face="back" hidden', main)
    assert 'data-face="front">Forside</span>' in main
    assert f'href="{browse_url(normalisering, 1)}?vis=svar" data-flip>' in main
    bar = content.split('<header class="session-bar"', 1)[1].split("</header>", 1)[0]
    assert "1 av 3" in bar and 'class="session-meter" max="3" value="1"' in bar
    assert "Normalisering · bla i kort" in bar
    assert "Kort 1 av 3 · 2 kort igjen i temaet · → neste kort" in text_of(main)
    assert "Databaser › Normalisering" in main
    assert "<title>Kort 1 av 3 – Bla i kort" in content


def test_fr14_bla_i_alle_kort_is_offered_when_nothing_is_due(now, client_ida, ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    ReviewState.objects.filter(pk=review_services.due_cards(ida, Scope(topic_id=normalisering.id)).get().pk).update(
        due_date=NOON.date() + datetime.timedelta(days=2)
    )
    panel = panel_of(main_of(client_ida.get(selftest_url(normalisering)).content.decode()))
    assert "Ingen kort i dag" in panel and "Bla i alle kort" in panel


def test_fr14_cards_path_redirects_to_position_1(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(2))
    response = client_ida.get(browse_url(normalisering))
    assert response.status_code == 302 and response["Location"] == browse_url(normalisering, 1)


def test_fr14_avslutt_goes_to_test_deg_selv(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(2))
    content = page(client_ida, normalisering, 2)
    assert f'<a class="session-exit" href="{selftest_url(normalisering)}">' in content


# ---- Matrix: Order ------------------------------------------------------------------------


def test_fr14_order_is_generation_order_older_source_first(now, client_ida, normalisering):
    ready_source(normalisering, "eldst.pdf", cards=(("Eldst 1", "a"), ("Eldst 2", "b")))
    ready_source(normalisering, "nyest.pdf", cards=(("Nyest 1", "c"),))
    fronts = [front_of(main_of(page(client_ida, normalisering, n))) for n in (1, 2, 3)]
    assert fronts == ["Eldst 1", "Eldst 2", "Nyest 1"]


# ---- Matrix: Flip without JS --------------------------------------------------------------


def test_fr14_vis_svar_shows_back_and_reference_and_keeps_the_front(now, client_ida, normalisering):
    ready_source(normalisering, "forelesning.pdf", cards=(("Hva er 1NF?", "Atomiske verdier."),), language="en")
    main = main_of(page(client_ida, normalisering, 1, "?vis=svar"))
    assert 'class="review-card is-flipped"' in main
    assert re.search(r'<h1 class="review-card-front" id="review-front" tabindex="-1" lang="en">Hva er 1NF\?</h1>', main)
    assert re.search(r'id="review-back" tabindex="-1" lang="en" autofocus>Atomiske verdier\.</p>', main)
    assert "Side 1 · forelesning.pdf" in main and "«sitat Hva er 1NF?»" in main
    assert 'data-face="back">Bakside</span>' in main
    # The flip link and the D09 next never carry the flip: moving always shows the front.
    assert "?vis=svar&" not in main and "%3Fvis%3Dsvar" not in main


# ---- Matrix: Ends -------------------------------------------------------------------------


def test_fr14_ends_have_no_forrige_or_neste_and_the_last_says_so(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(3))
    first = main_of(page(client_ida, normalisering, 1))
    assert "Forrige" not in first and "data-browse-prev" not in first
    assert f'href="{browse_url(normalisering, 2)}" rel="next" data-browse-next>' in first

    middle = main_of(page(client_ida, normalisering, 2))
    assert f'href="{browse_url(normalisering, 1)}" rel="prev" data-browse-prev>' in middle
    assert f'href="{browse_url(normalisering, 3)}" rel="next" data-browse-next>' in middle

    last = main_of(page(client_ida, normalisering, 3))
    assert "data-browse-next" not in last and ">Neste" not in last
    assert f'href="{browse_url(normalisering, 2)}" rel="prev" data-browse-prev>' in last
    assert "Siste kort i temaet" in text_of(last) and "kort igjen i temaet" not in text_of(last)

    # One card: nothing to move to, so no nav and no key hint.
    Flashcard.objects.exclude(front="Kort 1?").delete()
    only = main_of(page(client_ida, normalisering, 1))
    assert "browse-nav" not in only and "blar</p>" not in only


# ---- Matrix: Out of range -----------------------------------------------------------------


@pytest.mark.parametrize(("position", "expected"), [(0, 1), (8, 3)])
def test_fr14_out_of_range_redirects_to_first_or_last(now, client_ida, normalisering, position, expected):
    ready_source(normalisering, cards=cards(3))
    response = client_ida.get(browse_url(normalisering, position))
    assert response.status_code == 302 and response["Location"] == browse_url(normalisering, expected)


# ---- Matrix: No writes --------------------------------------------------------------------


def test_fr14_browsing_every_card_writes_nothing(now, client_ida, ida, normalisering, monkeypatch):
    ready_source(normalisering, cards=cards(4))

    def refuse(*args, **kwargs):
        raise AssertionError("P08 must not call due_cards or introduce_today")

    monkeypatch.setattr(review_services, "due_cards", refuse)
    monkeypatch.setattr(review_services, "introduce_today", refuse)
    for position in range(1, 5):
        page(client_ida, normalisering, position)
        page(client_ida, normalisering, position, "?vis=svar")
    client_ida.get(browse_url(normalisering))
    client_ida.get(browse_url(normalisering, 9))
    assert not ReviewState.objects.exists() and not Review.objects.exists() and not Rating.objects.exists()
    monkeypatch.undo()
    # Due counts are as if P08 was never opened: the 4 new cards are introduced on first count.
    assert review_services.due_cards(ida, Scope(topic_id=normalisering.id)).count() == 4


def test_fr14_browsing_keeps_existing_due_dates(now, client_ida, ida, normalisering):
    ready_source(normalisering, cards=cards(2))
    review_services.introduce_today(ida)
    before = dict(ReviewState.objects.values_list("flashcard_id", "due_date"))
    for position in (1, 2):
        page(client_ida, normalisering, position, "?vis=svar")
    assert dict(ReviewState.objects.values_list("flashcard_id", "due_date")) == before


def test_fr14_post_is_not_allowed(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    assert client_ida.post(browse_url(normalisering, 1)).status_code == 405


# ---- Matrix: Dates ------------------------------------------------------------------------


def test_fr14_next_review_date_or_not_reviewed_yet(now, client_ida, ida, normalisering):
    ready_source(normalisering, cards=cards(2))
    first = Flashcard.objects.get(front="Kort 1?")
    ReviewState.objects.create(
        student=ida, flashcard=first, box=2, due_date=datetime.date(2026, 11, 25), introduced_on=NOON.date()
    )
    assert "Neste repetisjon: 25. november" in text_of(main_of(page(client_ida, normalisering, 1)))
    second = text_of(main_of(page(client_ida, normalisering, 2)))
    assert "Ikke repetert ennå" in second and "Neste repetisjon" not in second


# ---- Matrix: Not ready --------------------------------------------------------------------


@pytest.mark.parametrize("status", [Status.GENERATING, Status.FAILED, Status.PENDING])
def test_fr14_cards_of_a_source_that_is_not_ready_are_not_listed(now, client_ida, normalisering, status):
    ready_source(normalisering, "klar.pdf", cards=(("Klar 1", "a"),))
    other = ready_source(normalisering, "lager.pdf", cards=(("Skjult 1", "b"),))
    Source.objects.filter(pk=other.pk).update(status=status)
    main = main_of(page(client_ida, normalisering, 1))
    assert front_of(main) == "Klar 1"
    assert "Siste kort i temaet" in text_of(main)
    response = client_ida.get(browse_url(normalisering, 2))
    assert response["Location"] == browse_url(normalisering, 1)


# ---- Matrix: Delete -----------------------------------------------------------------------


def test_fr14_delete_card_3_of_5_lands_on_position_3_showing_old_card_4(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(5))
    card = Flashcard.objects.get(front="Kort 3?")
    here = browse_url(normalisering, 3)
    content = page(client_ida, normalisering, 3, "?vis=svar")
    delete = reverse("studymat:delete_item", args=["card", card.id])
    # «⋯» → «Slett kortet», a full-page D09 with next on this position (front, not the flip).
    link = content.split('class="menu-item menu-item--destructive"', 1)[1].split("</a>", 1)[0]
    assert f'href="{delete}?next={here}">' in link and "hx-get" not in link and "Slett kortet" in link
    assert 'aria-label="Flere valg for kortet Kort 3?"' in content
    dialog = client_ida.get(f"{delete}?next={here}").content.decode()
    assert dialog.startswith("<!doctype html>") and f'name="next" value="{here}"' in dialog
    response = client_ida.post(delete, {"next": here})
    assert response.status_code == 302 and response["Location"] == here
    content = page(client_ida, normalisering, 3)
    assert front_of(main_of(content)) == "Kort 4?"
    bar = content.split('<header class="session-bar"', 1)[1].split("</header>", 1)[0]
    assert "3 av 4" in bar


def test_fr14_delete_the_last_card_lands_on_the_new_last(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(2))
    card = Flashcard.objects.get(front="Kort 2?")
    here = browse_url(normalisering, 2)
    response = client_ida.post(reverse("studymat:delete_item", args=["card", card.id]), {"next": here}, follow=True)
    assert response.redirect_chain[-1][0] == browse_url(normalisering, 1)
    assert front_of(main_of(response.content.decode())) == "Kort 1?"


def test_fr14_delete_the_only_card_lands_on_test_deg_selv(now, client_ida, normalisering):
    ready_source(normalisering, cards=cards(1))
    card = Flashcard.objects.get()
    here = browse_url(normalisering, 1)
    content = page(client_ida, normalisering, 1)
    link = content.split('class="menu-item menu-item--destructive"', 1)[1].split("</a>", 1)[0]
    assert "hx-get" not in link
    response = client_ida.post(reverse("studymat:delete_item", args=["card", card.id]), {"next": here}, follow=True)
    assert response.redirect_chain[-1][0] == selftest_url(normalisering)


# ---- Matrix: Empty ------------------------------------------------------------------------


def test_fr14_a_card_gone_between_count_and_fetch_redirects_to_the_last(now, client_ida, normalisering, monkeypatch):
    from django.db.models import QuerySet

    ready_source(normalisering, cards=cards(3))
    real_count = QuerySet.count
    calls = {"n": 0}

    def count_then_delete(self):
        n = real_count(self)
        calls["n"] += 1
        if calls["n"] == 1 and self.model is Flashcard:
            Flashcard.objects.filter(front="Kort 3?").delete()
        return n

    monkeypatch.setattr(QuerySet, "count", count_then_delete)
    response = client_ida.get(browse_url(normalisering, 3))
    assert response.status_code == 302 and response["Location"] == browse_url(normalisering, 2)


def test_fr14_topic_without_ready_cards_redirects_to_test_deg_selv(now, client_ida, normalisering):
    for url in (browse_url(normalisering), browse_url(normalisering, 1)):
        response = client_ida.get(url, follow=True)
        assert response.redirect_chain[-1][0] == selftest_url(normalisering)


# ---- Matrix: Not owned --------------------------------------------------------------------


def test_fr14_another_students_topic_is_404(now, client_ida, student):
    jonas = student("jonas@example.no")
    topic = course_services.create_topic(course_services.create_course(jonas, "Hemmelig"), "Jonas tema")
    ready_source(topic, cards=(("JonasKort", "y"),))
    for url in (browse_url(topic), browse_url(topic, 1)):
        response = client_ida.get(url)
        assert response.status_code == 404 and "JonasKort" not in response.content.decode()


def test_fr14_signed_out_is_sent_to_sign_in(now, client, normalisering):
    response = client.get(browse_url(normalisering, 1))
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:sign_in"))


# ---- Keys (app.js) ------------------------------------------------------------------------


def test_fr14_app_js_follows_the_links_on_arrow_keys(now):
    from django.conf import settings

    js = (settings.BASE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert '"[data-browse-prev]"' in js and '"[data-browse-next]"' in js
    assert 'evt.key !== "ArrowLeft" && evt.key !== "ArrowRight"' in js
