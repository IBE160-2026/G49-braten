"""D10 topic-picker footer in app.js (deferred from story 12), opened from P04: checking boxes
updates «{t} tema valgt · {q} spørsmål», singular for one, summing the boxes' Questions."""

from django.urls import reverse
from playwright.sync_api import expect

from core.messages import MESSAGES
from tests.test_weak_topic_quiz import abc, databaser, ida  # noqa: F401  (fixtures)


def test_d10_footer_counts_one_then_two_topics(ida, databaser, abc, logged_in_page, url):  # noqa: F811
    a, b, c = abc
    page = logged_in_page(ida)
    page.goto(url(reverse("web:course", args=[databaser.id])))
    page.locator(f'a[hx-get="{reverse("web:weak_quiz", args=[databaser.id])}"]').click()
    dialog = page.locator("#dialog dialog")
    expect(dialog).to_have_attribute("open", "")
    foot = dialog.locator("[data-topic-picker-count]")
    box = {t: dialog.locator(f'input[type="checkbox"][value="{t.id}"]') for t in (a, b, c)}

    # B and C are preselected; start from none.
    box[b].uncheck()
    box[c].uncheck()
    expect(foot).to_have_text(MESSAGES["weak_quiz_count_other"].format(t=0, q=0))

    box[b].check()  # 5 Questions
    expect(foot).to_have_text(MESSAGES["weak_quiz_count_one"].format(t=1, q=5))
    box[c].check()  # 10 Questions
    expect(foot).to_have_text(MESSAGES["weak_quiz_count_other"].format(t=2, q=15))
