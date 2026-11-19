"""CAP-11, FR-28 (story 13): the Next step on Hjem (P03), Fagoversikt (P04) and the quiz band on Tema (P05).

The band takes the first rule that applies within the page's scope: Due cards, Weak topics with
ready Questions, a Topic without Sources, else a calm-message.
"""

import datetime
import re
from urllib.parse import parse_qs, urlsplit

import pytest
from django.test import Client
from django.urls import reverse

from core import time
from courses import services as courses_services
from courses.models import Source, Status
from courses.scope import Scope
from progress import rules
from progress import services as progress
from review import services as review_services
from review.models import Review, ReviewState
from studymat.models import Flashcard
from tests.test_progress import pct, seed
from tests.test_topic_page import main_of, ready_source, text_of

pytestmark = pytest.mark.django_db

NOON = datetime.datetime(2026, 11, 19, 12, 0, tzinfo=time.OSLO)


@pytest.fixture(autouse=True)
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
def databaser(ida):
    return courses_services.create_course(ida, "Databaser", "DAT102")


def cards(n: int, prefix: str = "Kort") -> tuple:
    return tuple((f"{prefix} {i}?", f"Svar {i}.") for i in range(1, n + 1))


def topic_with_cards(course, name: str, n: int):
    topic = courses_services.create_topic(course, name)
    ready_source(topic, f"{name}.pdf", cards=cards(n, name), questions=())
    return topic


def topic_without_cards(course, name: str):
    """A Topic with a ready Source and nothing to review or practise."""
    topic = courses_services.create_topic(course, name)
    ready_source(topic, f"{name}.pdf", cards=(), questions=())
    return topic


def no_cards():
    """Seeded Quizzes bring a Flashcard per Source; drop them so no rule 1 or date applies."""
    Flashcard.objects.all().delete()


def band_of(main: str) -> str:
    match = re.search(r'<section class="next-step-band".*?</section>', main, re.DOTALL)
    return match.group(0) if match else ""


def page(client, url) -> str:
    response = client.get(url)
    assert response.status_code == 200
    return main_of(response.content.decode())


def course_url(course) -> str:
    return reverse("web:course", args=[course.id])


def band_parts(band: str) -> dict:
    href = re.search(r'<a class="band-button" href="([^"]+)"', band)
    return {
        "number": text_of(re.search(r'<p class="band-number">(.*?)</p>', band, re.DOTALL).group(1)),
        "unit": text_of(re.search(r'<p class="band-unit">(.*?)</p>', band, re.DOTALL).group(1)),
        "heading": text_of(re.search(r'<h2 class="band-heading"[^>]*>(.*?)</h2>', band, re.DOTALL).group(1)),
        "why": text_of(re.search(r'<p class="band-why">(.*?)</p>', band, re.DOTALL).group(1)),
        "minutes": text_of(re.search(r'<p class="band-time">(.*?)</p>', band, re.DOTALL).group(1)),
        "button": text_of(re.search(r'<a class="band-button"[^>]*>(.*?)</a>', band, re.DOTALL).group(1)),
        "href": href.group(1).replace("&amp;", "&") if href else "",
    }


def calm_of(main: str) -> str:
    match = re.search(r'<p class="calm-message">(.*?)</p>', main, re.DOTALL)
    return text_of(match.group(1)) if match else ""


def assert_one_primary(main: str):
    """At most one band or calm-message, at most one band-button, and no other primary."""
    assert main.count("next-step-band") + main.count("calm-message") <= 1
    assert main.count("band-button") <= 1
    if "band-button" in main:
        assert "button-primary" not in main


# ---- Rules -------------------------------------------------------------------------------------


def test_fr28_minute_rates_round_up_exactly():
    assert (rules.CARD_MINUTES, rules.QUESTION_MINUTES, rules.SOURCE_MINUTES) == (0.8, 0.8, 2)
    assert rules.band_minutes(14, rules.CARD_MINUTES) == 12
    assert rules.band_minutes(35, rules.QUESTION_MINUTES) == 28
    assert rules.band_minutes(1, rules.SOURCE_MINUTES) == 2


# ---- Matrix: Due and Weak -> rule 1 -------------------------------------------------------------


def test_fr28_hjem_due_cards_come_first_per_fag(client_ida, ida, databaser):
    statistikk = courses_services.create_course(ida, "Statistikk")
    weak = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, weak, pct(9, 20))
    no_cards()
    topic_with_cards(databaser, "Transaksjoner", 9)
    topic_with_cards(statistikk, "Fordelinger", 5)
    main = page(client_ida, "/")
    band = band_parts(band_of(main))
    assert band["number"] == "14" and band["unit"] == "kort"
    assert band["heading"] == "Repeter dagens kort"
    assert band["why"] == "14 kort forfaller i dag: Databaser 9 og Statistikk 5."
    assert "<b>14</b>" in band_of(main) and "<b>9</b>" in band_of(main)
    assert band["minutes"] == "ca. 12 min"
    assert band["button"] == "Start repetisjon"
    assert band["href"] == f"{reverse('review:start')}?next=%2F"
    assert_one_primary(main)


def test_fr28_p04_due_cards_per_tema_most_first_then_name(client_ida, ida, databaser):
    weak = courses_services.create_topic(databaser, "Analyse")
    seed(ida, weak, pct(1, 5))
    no_cards()
    topic_with_cards(databaser, "Normalisering", 5)
    topic_with_cards(databaser, "Grunnleggende SQL", 1)
    topic_with_cards(databaser, "Transaksjoner", 3)
    topic_with_cards(databaser, "Indekser", 3)  # same count, created later: the name decides
    main = page(client_ida, course_url(databaser))
    band = band_parts(band_of(main))
    assert band["number"] == "12"
    assert band["heading"] == "Repeter kortene i Databaser"
    assert band["why"] == "12 kort forfaller i dag: Normalisering 5, Indekser 3, Transaksjoner 3 og Grunnleggende SQL 1."
    assert band["minutes"] == "ca. 10 min"
    query = parse_qs(urlsplit(band["href"]).query)
    assert urlsplit(band["href"]).path == reverse("review:start")
    assert query == {"course": [str(databaser.id)], "next": [course_url(databaser)]}
    assert_one_primary(main)


def test_fr28_hjem_band_starts_a_review_of_every_fag_that_returns_home(client_ida, ida, databaser):
    statistikk = courses_services.create_course(ida, "Statistikk")
    topic_with_cards(databaser, "Normalisering", 2)
    topic_with_cards(statistikk, "Fordelinger", 3)
    href = band_parts(band_of(page(client_ida, "/")))["href"]
    response = client_ida.get(href)
    assert response.status_code == 302
    review = Review.objects.get()
    assert review.course_id is None and review.topic_id is None and review.return_url == "/"
    assert review_services.progress(review).total == 5
    body = client_ida.get(response["Location"]).content.decode()
    assert '<a class="session-exit" href="/">' in body and "Avslutt" in body


# ---- Matrix: Weak only -> rule 2 ----------------------------------------------------------------


def test_fr28_p04_weak_topics_lowest_first(client_ida, ida, databaser):
    transaksjoner = courses_services.create_topic(databaser, "Transaksjoner")
    normalisering = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, transaksjoner, pct(11, 20))
    seed(ida, normalisering, pct(9, 20))
    no_cards()
    main = page(client_ida, course_url(databaser))
    band = band_parts(band_of(main))
    assert band["number"] == "40" and band["unit"] == "spørsmål"
    assert band["heading"] == "Øv på de svake temaene"
    assert band["why"] == "2 temaer trenger øving: Normalisering 45 % og Transaksjoner 55 %."
    assert band["minutes"] == "ca. 32 min"
    assert band["button"] == "Øv på svake temaer"
    assert band["href"] == reverse("web:weak_quiz", args=[databaser.id])
    assert_one_primary(main)
    # Following it opens D10 with both Weak topics preselected.
    d10 = client_ida.get(band["href"]).content.decode()
    checked = re.findall(r'<input type="checkbox" name="topics" value="(\d+)"[^>]*checked', d10)
    assert checked == [str(normalisering.id), str(transaksjoner.id)]


def test_fr28_p04_one_weak_topic_says_one_tema(client_ida, ida, databaser):
    seed(ida, courses_services.create_topic(databaser, "Normalisering"), pct(2, 5))
    no_cards()
    band = band_parts(band_of(page(client_ida, course_url(databaser))))
    assert band["why"] == "1 tema trenger øving: Normalisering 40 %."
    assert band["number"] == "5" and band["minutes"] == "ca. 4 min"


def test_fr28_hjem_weak_across_fag_goes_to_the_weakest_fag(client_ida, ida, databaser):
    statistikk = courses_services.create_course(ida, "Statistikk")
    seed(ida, courses_services.create_topic(databaser, "Normalisering"), pct(11, 20))
    seed(ida, courses_services.create_topic(statistikk, "Fordelinger"), pct(2, 5))
    no_cards()
    main = page(client_ida, "/")
    band = band_parts(band_of(main))
    assert band["heading"] == "Øv på de svake temaene i Statistikk"
    assert band["why"] == "2 temaer trenger øving i alle fag. Svakest: Fordelinger 40 %."
    # {q} counts that fag only.
    assert band["number"] == "5" and band["unit"] == "spørsmål"
    assert band["href"] == reverse("web:weak_quiz", args=[statistikk.id])
    assert_one_primary(main)


def test_fr28_hjem_weak_ties_go_to_the_fag_created_first(client_ida, ida, databaser):
    statistikk = courses_services.create_course(ida, "Statistikk")
    # Statistikk's Topic is created first, but Databaser is the older fag.
    seed(ida, courses_services.create_topic(statistikk, "Fordelinger"), pct(2, 5))
    seed(ida, courses_services.create_topic(databaser, "Normalisering"), pct(2, 5))
    no_cards()
    band = band_parts(band_of(page(client_ida, "/")))
    assert band["href"] == reverse("web:weak_quiz", args=[databaser.id])
    assert band["why"] == "2 temaer trenger øving i alle fag. Svakest: Normalisering 40 %."


def test_fr28_hjem_one_weak_topic_says_one_tema(client_ida, ida, databaser):
    seed(ida, courses_services.create_topic(databaser, "Normalisering"), pct(2, 5))
    no_cards()
    band = band_parts(band_of(page(client_ida, "/")))
    assert band["why"] == "1 tema trenger øving i alle fag. Svakest: Normalisering 40 %."


# ---- Matrix: Weak without Questions -------------------------------------------------------------


def test_fr28_weak_topic_without_ready_questions_is_not_rule_2(client_ida, ida, databaser):
    normalisering = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, normalisering, pct(2, 5))
    no_cards()
    Source.objects.filter(topic=normalisering).update(status=Status.GENERATING)
    assert progress.weak_topics(ida, Scope(course_id=databaser.id))
    for url in ("/", course_url(databaser)):
        main = page(client_ida, url)
        assert band_of(main) == ""
        assert "Ingen flere kort er planlagt." in calm_of(main)


# ---- Matrix: Topic without Sources -> rule 3 -----------------------------------------------------


def test_fr28_topic_without_sources_first_by_fag_then_topic_order(client_ida, ida, databaser):
    statistikk = courses_services.create_course(ida, "Statistikk")
    courses_services.create_topic(statistikk, "Fordelinger")  # created first, in the newer fag
    topic_without_cards(databaser, "Normalisering")
    sql = courses_services.create_topic(databaser, "SQL")
    courses_services.create_topic(databaser, "Indekser")
    main = page(client_ida, "/")
    band = band_parts(band_of(main))
    assert (band["number"], band["unit"]) == ("1", "kilde")
    assert band["heading"] == "Legg til kilde i SQL"
    assert band["why"] == "SQL i Databaser har ingen kilder ennå."
    assert band["minutes"] == "ca. 2 min"
    assert band["button"] == "Legg til kilde"
    assert band["href"] == reverse("studymat:add_source", args=[sql.id])
    assert_one_primary(main)
    band = band_parts(band_of(page(client_ida, course_url(statistikk))))
    assert band["heading"] == "Legg til kilde i Fordelinger"
    assert band["why"] == "Fordelinger har ingen kilder ennå."


def test_fr28_rules_1_and_2_come_before_an_empty_topic(client_ida, ida, databaser):
    courses_services.create_topic(databaser, "Tom")  # rule 3 applies throughout
    weak = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, weak, pct(2, 5))
    topic_with_cards(databaser, "Transaksjoner", 2)
    for url in ("/", course_url(databaser)):
        assert urlsplit(band_parts(band_of(page(client_ida, url)))["href"]).path == reverse("review:start")
    no_cards()
    for url in ("/", course_url(databaser)):
        assert band_parts(band_of(page(client_ida, url)))["href"] == reverse("web:weak_quiz", args=[databaser.id])


def test_fr28_names_are_escaped_in_the_band(client_ida, ida):
    fag = courses_services.create_course(ida, "<b>fag</b>")
    empty = courses_services.create_topic(fag, "<i>tom</i>")
    weak = courses_services.create_topic(fag, "<u>svak</u>")
    seed(ida, weak, pct(2, 5))
    no_cards()
    ready_source(empty, cards=cards(2), questions=())

    def assert_escaped(band: str):
        assert band
        assert "<b>fag</b>" not in band and "<i>tom</i>" not in band and "<u>svak</u>" not in band

    # Rule 1: per fag on Hjem, per tema (and the fag in the heading) on P04.
    assert "&lt;b&gt;fag&lt;/b&gt;" in band_of(page(client_ida, "/"))
    p04 = band_of(page(client_ida, course_url(fag)))
    assert "&lt;i&gt;tom&lt;/i&gt;" in p04 and "&lt;b&gt;fag&lt;/b&gt;" in p04
    assert_escaped(band_of(page(client_ida, "/")))
    assert_escaped(p04)
    # Rule 2: the fag in the heading and the tema in the why.
    no_cards()
    for url in ("/", course_url(fag)):
        band = band_of(page(client_ida, url))
        assert_escaped(band)
        assert "&lt;u&gt;svak&lt;/u&gt;" in band
    assert "&lt;b&gt;fag&lt;/b&gt;" in band_of(page(client_ida, "/"))
    # Rule 3: the tema and the fag.
    Source.objects.filter(topic=weak).update(status=Status.GENERATING)
    later = courses_services.create_topic(fag, "<s>ny</s>")
    for url in ("/", course_url(fag)):
        band = band_of(page(client_ida, url))
        assert "<s>ny</s>" not in band and "&lt;s&gt;ny&lt;/s&gt;" in band
        assert_escaped(band)
    assert "&lt;b&gt;fag&lt;/b&gt;" in band_of(page(client_ida, "/"))
    assert later.name == "<s>ny</s>"


# ---- Matrix: Calm ------------------------------------------------------------------------------


def test_fr28_calm_with_the_next_date(client_ida, ida, databaser):
    topic_with_cards(databaser, "Normalisering", 1)
    review_services.introduce_today(ida)
    ReviewState.objects.update(due_date=NOON.date() + datetime.timedelta(days=3))
    main = page(client_ida, "/")
    assert band_of(main) == "" and "band-button" not in main
    assert calm_of(main) == "Ingen kort i dag. Neste kort kommer 22. november."
    assert_one_primary(main)
    main = page(client_ida, course_url(databaser))
    assert calm_of(main) == "Ingen kort i Databaser i dag. Neste kort kommer 22. november."
    assert_one_primary(main)


def test_fr28_calm_without_a_date(client_ida, ida, databaser):
    topic_without_cards(databaser, "Normalisering")
    assert calm_of(page(client_ida, "/")) == "Ingen kort i dag. Ingen flere kort er planlagt."
    assert calm_of(page(client_ida, course_url(databaser))) == "Ingen kort i Databaser i dag. Ingen flere kort er planlagt."


def test_fr28_hjem_with_fag_but_no_topics_is_calm(client_ida, databaser):
    assert calm_of(page(client_ida, "/")) == "Ingen kort i dag. Ingen flere kort er planlagt."


# ---- Matrix: Scope -----------------------------------------------------------------------------


def test_fr28_due_cards_in_another_fag_are_not_rule_1_on_p04(client_ida, ida, databaser):
    statistikk = courses_services.create_course(ida, "Statistikk")
    topic_without_cards(databaser, "Normalisering")
    topic_with_cards(statistikk, "Fordelinger", 4)
    main = page(client_ida, course_url(databaser))
    assert band_of(main) == ""
    assert calm_of(main) == "Ingen kort i Databaser i dag. Ingen flere kort er planlagt."
    assert band_parts(band_of(page(client_ida, "/")))["why"] == "4 kort forfaller i dag: Statistikk 4."


# ---- Matrix: Empty -----------------------------------------------------------------------------


def test_fr28_no_band_without_fag_or_topics(client_ida, ida, databaser):
    main = page(client_ida, course_url(databaser))
    assert "next-step-band" not in main and "calm-message" not in main
    assert "Ingen temaer ennå" in text_of(main)
    databaser.delete()
    main = page(client_ida, "/")
    assert "next-step-band" not in main and "calm-message" not in main
    assert "Ingen fag ennå" in text_of(main)
    assert progress.next_step(ida, Scope.all()) is None


# ---- Matrix: P05 -------------------------------------------------------------------------------


def test_fr28_p05_quiz_band_for_a_weak_topic(client_ida, ida, databaser):
    normalisering = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, normalisering, pct(9, 20))
    ready_source(normalisering, "ekstra.pdf", questions=[f"Ekstra {i}" for i in range(8)])
    for tab in ("summary", "quiz", "selftest", "sources"):
        main = page(client_ida, f"{reverse('web:topic', args=[normalisering.id])}?tab={tab}")
        band = band_parts(band_of(main))
        assert (band["number"], band["unit"]) == ("10", "spørsmål")
        assert band["heading"] == "Ta en quiz i Normalisering"
        assert band["why"] == "Mestring 45 %, så temaet trenger øving. 28 spørsmål er klare."
        assert band["minutes"] == "ca. 8 min"
        assert band["button"] == "Start quiz"
        assert band["href"] == reverse("quiz:start", args=[normalisering.id])
        assert_one_primary(main)


def test_fr28_p05_quiz_band_scored_and_without_data(client_ida, ida, databaser):
    normalisering = courses_services.create_topic(databaser, "Normalisering")
    seed(ida, normalisering, pct(4, 5))
    url = reverse("web:topic", args=[normalisering.id])
    band = band_parts(band_of(page(client_ida, url)))
    assert band["why"] == "Mestring 80 %. 5 spørsmål er klare."
    assert band["number"] == "5" and band["minutes"] == "ca. 4 min"
    sql = courses_services.create_topic(databaser, "SQL")
    ready_source(sql, questions=("Hva er en join?", "Hva er en indeks?"))
    band = band_parts(band_of(page(client_ida, reverse("web:topic", args=[sql.id]))))
    assert band["why"] == "2 spørsmål er klare."


def test_fr28_p05_one_ready_question_is_singular(client_ida, ida, databaser):
    sql = courses_services.create_topic(databaser, "SQL")
    ready_source(sql, questions=("Hva er en join?",))
    band = band_parts(band_of(page(client_ida, reverse("web:topic", args=[sql.id]))))
    assert band["number"] == "1"
    assert band["why"] == "1 spørsmål er klart."
    seed(ida, sql, pct(1, 5))
    Source.objects.filter(topic=sql).exclude(name="forelesning-5.pdf").update(status=Status.GENERATING)
    band = band_parts(band_of(page(client_ida, reverse("web:topic", args=[sql.id]))))
    assert band["why"] == "Mestring 20 %, så temaet trenger øving. 1 spørsmål er klart."
    seed(ida, sql, pct(5, 5))
    Source.objects.filter(topic=sql).exclude(name="forelesning-5.pdf").update(status=Status.GENERATING)
    band = band_parts(band_of(page(client_ida, reverse("web:topic", args=[sql.id]))))
    assert band["why"] == "Mestring 60 %. 1 spørsmål er klart."


def test_fr28_p05_no_band_without_ready_questions(client_ida, ida, databaser):
    empty = courses_services.create_topic(databaser, "Tom")
    main = page(client_ida, reverse("web:topic", args=[empty.id]))
    assert "next-step-band" not in main and "calm-message" not in main
    generating = courses_services.create_topic(databaser, "Lages")
    source = ready_source(generating)
    Source.objects.filter(pk=source.pk).update(status=Status.GENERATING)
    main = page(client_ida, reverse("web:topic", args=[generating.id]))
    assert "next-step-band" not in main


# ---- One primary, GET only ---------------------------------------------------------------------


def test_fr28_every_band_button_is_a_get_link(client_ida, ida, databaser):
    """Each rule's button is a link (never a form) to a page that answers a GET."""
    hrefs = []
    tom = courses_services.create_topic(databaser, "Tom")  # rule 3
    hrefs.append(band_parts(band_of(page(client_ida, "/")))["href"])
    svak = courses_services.create_topic(databaser, "Svak")
    seed(ida, svak, pct(1, 5))
    no_cards()
    ready_source(tom, cards=(), questions=())  # rule 2 now
    hrefs.append(band_parts(band_of(page(client_ida, "/")))["href"])
    topic_with_cards(databaser, "Kort", 2)  # rule 1
    hrefs.append(band_parts(band_of(page(client_ida, "/")))["href"])
    hrefs.append(band_parts(band_of(page(client_ida, reverse("web:topic", args=[svak.id]))))["href"])
    assert [urlsplit(h).path for h in hrefs] == [
        reverse("studymat:add_source", args=[tom.id]),
        reverse("web:weak_quiz", args=[databaser.id]),
        reverse("review:start"),
        reverse("quiz:start", args=[svak.id]),
    ]
    for href in hrefs:
        assert client_ida.get(href).status_code in (200, 302)
    assert "<form" not in band_of(page(client_ida, "/"))
    assert all(isinstance(step, progress.NextStep) and step.method == "get" for step in (
        progress.next_step(ida, Scope.all()),
        progress.next_step(ida, Scope(course_id=databaser.id)),
        progress.next_step(ida, Scope(topic_id=svak.id)),
    ))  # fmt: skip


# ---- Hjem rows ---------------------------------------------------------------------------------


def test_fr28_hjem_rows_show_todays_cards(client_ida, ida, databaser):
    courses_services.create_course(ida, "Statistikk")
    topic_with_cards(databaser, "Normalisering", 9)
    rows = re.findall(r'<span class="course-row-due">(.*?)</span>', page(client_ida, "/"))
    assert rows == ["9 kort i dag", "Ingen kort i dag"]
