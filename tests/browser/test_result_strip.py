"""P07 result strip in app.js (deferred from story 9): a strip slot or a `#q-N` hash opens and
focuses its result row, also when the same slot is clicked twice."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from quiz.rules import Grade
from tests.test_quiz import ida, make_quiz, now, sample, topic  # noqa: F401  (fixtures)
from tests.test_result import grade_all

C, I = Grade.CORRECT, Grade.INCORRECT


@pytest.fixture
def result(ida, topic, sample, logged_in_page, url):  # noqa: F811
    quiz = make_quiz(ida, topic, n=3)
    grade_all(ida, quiz, [C, I, C])
    page = logged_in_page(ida)
    return page, url(reverse("quiz:result", args=[quiz.id]))


def test_p07_strip_slot_opens_and_focuses_its_row_twice(result):
    page, result_url = result
    page.goto(result_url)
    row = page.locator("details#q-3")
    slot = page.locator('a.result-slot[href="#q-3"]')
    expect(row).not_to_have_attribute("open", "")

    slot.click()
    expect(row).to_have_attribute("open", "")
    expect(row.locator(":scope > summary")).to_be_focused()

    row.locator(":scope > summary").click()  # close the row; the hash stays #q-3
    expect(row).not_to_have_attribute("open", "")
    slot.click()  # same hash: no hashchange, the click handler opens it
    expect(row).to_have_attribute("open", "")
    expect(row.locator(":scope > summary")).to_be_focused()


def test_p07_hash_on_load_opens_its_row(result):
    page, result_url = result
    page.goto(result_url + "#q-2")
    expect(page.locator("details#q-2")).to_have_attribute("open", "")
    expect(page.locator("details#q-1")).not_to_have_attribute("open", "")
