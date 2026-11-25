"""P06 keyboard contract in app.js (deferred from story 8): 1–4 pick an option, Enter answers,
focus goes to the feedback heading, Enter there moves on, and keys type normally in a field."""

import pytest
from playwright.sync_api import expect

from tests.test_quiz import (  # noqa: F401
    ida,
    make_quiz,
    now,
    position_of,
    question_url,
    sample,
    topic,
)


@pytest.fixture
def quiz_page(ida, topic, sample, logged_in_page, url):  # noqa: F811
    quiz = make_quiz(ida, topic, n=11)
    page = logged_in_page(ida)

    def open_kind(kind):
        qq = position_of(quiz, kind)
        page.goto(url(question_url(quiz, qq.position)))
        return page

    return open_kind


def test_p06_key_picks_option_and_enter_answers_with_focus_on_feedback(quiz_page):
    page = quiz_page("multiple_choice")
    expect(page.locator("#question-prompt")).to_be_focused()
    page.keyboard.press("2")
    second = page.locator('.option-group input[type="radio"]').nth(1)
    expect(second).to_be_checked()
    expect(second).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.locator(".feedback-heading")).to_be_focused()
    expect(page.locator(".option-row").nth(1)).to_contain_text("Ditt svar")


def test_p06_enter_on_feedback_heading_follows_next(quiz_page):
    page = quiz_page("multiple_choice")
    page.keyboard.press("1")
    page.keyboard.press("Enter")
    heading = page.locator(".feedback-heading")
    expect(heading).to_be_focused()
    next_href = page.locator("#question-card [data-next]").evaluate("a => a.href")
    page.keyboard.press("Enter")
    page.wait_for_url(next_href)


def test_p06_number_key_types_in_a_free_text_field(quiz_page):
    page = quiz_page("free_text")
    field = page.locator("#answer-text")
    field.focus()
    page.keyboard.press("1")
    expect(field).to_have_value("1")
    expect(page.locator('input[type="radio"]:checked')).to_have_count(0)


def test_p06_number_key_in_a_text_field_never_picks_an_option(quiz_page):
    """The P06 card has a field or radios, never both, so a text input is added to an MC card to
    reach the typing guard itself (without it, «1» would check option 1 and eat the keystroke)."""
    page = quiz_page("multiple_choice")
    page.locator(".question-form").evaluate(
        "form => form.insertAdjacentHTML('beforeend', '<input type=\"text\" id=\"probe\">')"
    )
    probe = page.locator("#probe")
    probe.focus()
    page.keyboard.press("1")
    expect(probe).to_have_value("1")
    expect(page.locator('.option-group input[type="radio"]:checked')).to_have_count(0)
