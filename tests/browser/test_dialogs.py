"""AD-18 dialogs in app.js (deferred from story 3): open on a swap into #dialog, close by Esc or
«Avbryt» with focus back on the trigger, a valid submit's focus, and the two failure messages."""

import pytest
from playwright.sync_api import expect

from core.messages import MESSAGES


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def home(logged_in_page, url, ida):
    page = logged_in_page(ida)
    page.goto(url("/"))
    return page


def open_new_course(page):
    trigger = page.locator("a.rail-add")
    trigger.click()
    dialog = page.locator("#dialog dialog")
    expect(dialog).to_have_attribute("open", "")
    return trigger, dialog


def test_dialog_opens_as_a_modal_on_swap_into_the_slot(home):
    _, dialog = open_new_course(home)
    assert dialog.evaluate("d => d.matches(':modal')")


def test_dialog_closes_on_escape_and_returns_focus_to_the_trigger(home):
    trigger, _ = open_new_course(home)
    home.keyboard.press("Escape")
    expect(home.locator("#dialog")).to_be_empty()
    expect(trigger).to_be_focused()


def test_dialog_closes_on_avbryt_without_navigating(home):
    before = home.url
    trigger, dialog = open_new_course(home)
    dialog.locator(".dialog-foot [data-dialog-close]").click()
    expect(home.locator("#dialog")).to_be_empty()
    expect(trigger).to_be_focused()
    assert home.url == before


def test_dialog_valid_submit_swaps_the_page_and_focuses_autofocus_or_main(home):
    _, dialog = open_new_course(home)
    dialog.locator('input[name="name"]').fill("Databaser")
    dialog.locator('button[type="submit"]').click()
    expect(home.locator("#dialog dialog")).to_have_count(0)
    expect(home.locator("h1").first).to_contain_text("Databaser")
    home.wait_for_function(
        "() => document.activeElement === (document.querySelector('[autofocus]') || document.getElementById('main'))"
    )


def abort_post(route):
    if route.request.method == "POST":
        route.abort()
    else:
        route.fallback()


def answer_500(route):
    if route.request.method == "POST":
        route.fulfill(status=500, body="Server error")
    else:
        route.fallback()


@pytest.mark.parametrize(
    ("handler", "message"),
    [(abort_post, MESSAGES["network_error"]), (answer_500, MESSAGES["response_error"])],
    ids=["network-failure", "server-error"],
)
def test_dialog_failure_shows_the_fixed_message_in_the_dialog(home, handler, message):
    _, dialog = open_new_course(home)
    home.route("**/courses/new/**", handler)
    dialog.locator('input[name="name"]').fill("Databaser")
    dialog.locator('button[type="submit"]').click()
    expect(dialog.locator(".dialog-messages")).to_contain_text(message)
    expect(dialog).to_have_attribute("open", "")
