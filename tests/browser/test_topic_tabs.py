"""P05 tema-tabs in app.js (deferred from story 7): ← → Home End follow the neighbouring tab's link,
wrap at the ends, and the newly selected tab has focus on the new page."""

import pytest
from playwright.sync_api import expect

from courses import services
from tests.test_topic_page import ready_source, topic_url


@pytest.fixture
def topic_page(student, logged_in_page, url):
    ida = student("ida@example.no")
    topic = services.create_topic(services.create_course(ida, "Databaser"), "Normalisering")
    ready_source(topic)
    page = logged_in_page(ida)

    def go_by_key(key, to):
        page.keyboard.press(key)
        page.wait_for_url(url(topic_url(topic, to)))
        expect(page.locator(f"#tab-{to}")).to_have_attribute("aria-selected", "true")
        expect(page.locator(f"#tab-{to}")).to_be_focused()

    page.goto(url(topic_url(topic, "summary")))
    page.locator("#tab-summary").focus()
    return go_by_key


def test_p05_arrow_home_end_follow_the_neighbouring_tab_and_focus_it(topic_page):
    topic_page("ArrowRight", "quiz")
    topic_page("ArrowLeft", "summary")
    topic_page("End", "sources")
    topic_page("Home", "summary")


def test_p05_arrows_wrap_at_the_ends(topic_page):
    topic_page("ArrowLeft", "sources")
    topic_page("ArrowRight", "summary")
