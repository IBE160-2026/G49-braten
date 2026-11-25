"""P08 ← → and its guards, and the shared Space flip on P08 and P09 with keys 1–4 rating on P09
(deferred from story 11b)."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from courses import services as course_services
from tests.test_browse_cards import browse_url, cards
from tests.test_topic_page import ready_source


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def topic(ida):
    topic = course_services.create_topic(course_services.create_course(ida, "Databaser"), "Normalisering")
    ready_source(topic, cards=cards(3))
    return topic


@pytest.fixture
def page(ida, topic, logged_in_page):
    return logged_in_page(ida)


@pytest.fixture
def navigations(page):
    """Main-frame URLs navigated to, in order, so a key that must not navigate can be checked
    by the next key that must (no sleeps)."""
    seen: list[str] = []
    page.on("framenavigated", lambda frame: seen.append(frame.url) if frame == page.main_frame else None)
    return seen


def test_p08_arrows_follow_neighbours_and_stop_at_the_end(page, topic, url, navigations):
    page.goto(url(browse_url(topic, 2)))
    page.keyboard.press("ArrowRight")
    page.wait_for_url(url(browse_url(topic, 3)))
    page.keyboard.press("ArrowLeft")
    page.wait_for_url(url(browse_url(topic, 2)))

    page.goto(url(browse_url(topic, 3)))
    navigations.clear()
    page.keyboard.press("ArrowRight")  # no «Neste» on the last card
    page.keyboard.press("ArrowLeft")
    page.wait_for_url(url(browse_url(topic, 2)))
    assert navigations == [url(browse_url(topic, 2))]


def test_p08_arrow_inside_an_open_menu_does_not_navigate(page, topic, url, navigations):
    page.goto(url(browse_url(topic, 2)))
    page.locator(".menu-trigger").click()
    menu = page.locator(".browse-foot [popover]")
    expect(menu).to_be_visible()
    menu.locator(".menu-item").first.focus()
    navigations.clear()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Escape")
    expect(menu).to_be_hidden()
    page.locator("#review-front").focus()
    page.keyboard.press("ArrowLeft")
    page.wait_for_url(url(browse_url(topic, 1)))
    assert navigations == [url(browse_url(topic, 1))]


def expect_flipped(page):
    expect(page.locator("#review-back")).to_be_visible()
    expect(page.locator("#review-back")).to_be_focused()
    expect(page.locator('#review-card [data-face="front"]')).to_have_count(2)
    for front in page.locator('#review-card [data-face="front"]').all():
        expect(front).to_be_hidden()


@pytest.mark.parametrize("key", [" ", "Enter"], ids=["space", "enter"])
def test_p08_space_or_enter_flips_the_card(page, topic, url, key):
    page.goto(url(browse_url(topic, 1)))
    expect(page.locator("#review-front")).to_be_focused()
    page.keyboard.press(key)
    expect_flipped(page)


def test_p09_space_flips_and_a_number_key_rates(page, topic, url):
    page.goto(url(f"{reverse('review:start')}?topic={topic.id}"))
    expect(page.locator("#review-front")).to_be_focused()
    expect(page.locator(".rating-button").first).to_be_hidden()
    page.keyboard.press(" ")
    expect_flipped(page)
    expected = page.locator('.rating-button[data-key="3"]').get_attribute("value")
    with page.expect_request(lambda r: r.method == "POST" and "/rate" in r.url) as posted:
        page.keyboard.press("3")
    assert f"rating={expected}" in posted.value.post_data
    expect(page.locator("#review-front")).to_be_focused()
