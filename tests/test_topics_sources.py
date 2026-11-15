"""FR-2 / CAP-2 (story 3b): Topics and Sources under a fag, D03, D08/D09 for both, counted D09s."""

import datetime
import json

import pytest
from django.test import Client
from django.urls import reverse

from core.messages import MESSAGES
from courses import rules, services
from courses.models import Course, Source, SourceKind, Status, Topic

pytestmark = pytest.mark.django_db

HTMX_DIALOG = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "dialog"}
NOT_FOUND = "Fant ikke siden"


def course_url(course):
    return reverse("web:course", args=[course.id])


def topic_url(topic):
    return reverse("web:topic", args=[topic.id])


def create_topic_url(course):
    return reverse("courses:create_topic", args=[course.id])


def rename_topic_url(topic):
    return reverse("courses:rename_topic", args=[topic.id])


def delete_topic_url(topic):
    return reverse("courses:delete_topic", args=[topic.id])


def rename_source_url(source):
    return reverse("courses:rename_source", args=[source.id])


def delete_source_url(source):
    return reverse("courses:delete_source", args=[source.id])


def hx_location(response) -> str:
    return json.loads(response["HX-Location"])["path"]


def vary(response) -> set[str]:
    return {v.strip().lower() for v in response.get("Vary", "").split(",")}


def main_of(content: str) -> str:
    return content.split('<main id="main"', 1)[1].split("</main>", 1)[0]


def rail_of(content: str) -> str:
    return content.split('<nav class="fag-rail"', 1)[1].split("</nav>", 1)[0]


def add_source(topic, name="forelesning-3.pdf", kind=SourceKind.PDF, size_bytes=2_400_000):
    return services.create_source(topic, name, kind, size_bytes=size_bytes, content_sha256="a" * 64)


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
    return services.create_course(ida, "Databaser", "DAT102")


@pytest.fixture
def normalisering(databaser):
    return services.create_topic(databaser, "Normalisering")


# ---- Models and ownership (AD-7, AD-8) --------------------------------------------------


def test_ad7_topic_student_equals_its_courses(databaser, ida):
    topic = services.create_topic(databaser, "Normalisering")
    assert topic.student_id == databaser.student_id == ida.id
    assert topic.course == databaser


def test_ad7_source_student_equals_its_topics(normalisering, ida):
    source = add_source(normalisering)
    assert source.student_id == normalisering.student_id == ida.id
    assert source.topic == normalisering
    assert source.status == Status.PENDING
    assert source.detail_level == "medium"
    assert source.started_at is not None


def test_source_factory_refuses_unknown_kind_or_detail_level(normalisering):
    with pytest.raises(AssertionError):
        services.create_source(normalisering, "x", "docx")
    with pytest.raises(AssertionError):
        services.create_source(normalisering, "x", SourceKind.PDF, detail_level="huge")
    assert not Source.objects.exists()


def test_enums_use_the_spines_lowercase_values():
    from courses.models import DetailLevel, FailureReason

    assert Status.values == ["pending", "generating", "ready", "failed"]
    assert DetailLevel.values == ["short", "medium", "detailed"]
    assert SourceKind.values == ["pdf", "text", "pasted"]
    assert set(FailureReason.values) == {
        "needs_key", "privacy_not_accepted", "daily_limit", "rate_limited", "refused",
        "truncated", "invalid_format", "key_rejected", "provider_unavailable", "timed_out",
    }  # fmt: skip


def test_ad8_deleting_a_course_cascades_to_topics_and_sources(databaser, normalisering):
    add_source(normalisering)
    services.delete_course(databaser)
    assert not Topic.objects.exists()
    assert not Source.objects.exists()


def test_ad8_deleting_a_topic_cascades_to_its_sources_only(databaser, normalisering):
    add_source(normalisering)
    other = services.create_topic(databaser, "SQL")
    kept = add_source(other, "sql.pdf")
    services.delete_topic(normalisering)
    assert list(Source.objects.all()) == [kept]
    assert Course.objects.filter(pk=databaser.pk).exists()


def test_ad8_deleting_a_student_deletes_their_topics_and_sources(ida, normalisering):
    add_source(normalisering)
    ida.delete()
    assert not Topic.objects.exists()
    assert not Source.objects.exists()


def test_fr2_topics_in_creation_order_and_sources_newest_first(databaser, freeze_now):
    freeze_now(datetime.datetime(2026, 11, 16, 9, tzinfo=datetime.UTC))
    zeta = services.create_topic(databaser, "Zeta")
    old = add_source(zeta, "eldst.pdf")
    freeze_now(datetime.datetime(2026, 11, 16, 10, tzinfo=datetime.UTC))
    alfa = services.create_topic(databaser, "Alfa")
    new = add_source(zeta, "nyest.pdf")
    assert list(Topic.objects.filter(course=databaser)) == [zeta, alfa]
    assert list(Source.objects.filter(topic=zeta)) == [new, old]


# ---- D09 texts --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("topics", "sources", "lead"),
    [
        (4, 7, "4 temaer, 7 kilder og alle svar slettes. Dette kan ikke angres."),
        (1, 1, "1 tema, 1 kilde og alle svar slettes. Dette kan ikke angres."),
        (2, 0, "2 temaer og alle svar slettes. Dette kan ikke angres."),
        (0, 0, "Dette kan ikke angres."),
    ],
)
def test_fr2_course_delete_lead_counts_with_plurals_and_leaves_out_zero(topics, sources, lead):
    assert rules.course_delete_lead(topics, sources) == lead


@pytest.mark.parametrize(
    ("sources", "lead"),
    [
        (2, "2 kilder og alle svar slettes. Dette kan ikke angres."),
        (1, "1 kilde og alle svar slettes. Dette kan ikke angres."),
        (0, "Dette kan ikke angres."),
    ],
)
def test_fr2_topic_delete_lead_counts_with_plurals_and_leaves_out_zero(sources, lead):
    assert rules.topic_delete_lead(sources) == lead


# ---- Create tema (D03) ------------------------------------------------------------------


def test_fr2_create_topic_sets_student_and_course_and_lands_on_its_p05(client_ida, ida, databaser):
    response = client_ida.post(create_topic_url(databaser), {"name": "  Normalisering  "})
    topic = Topic.objects.get()
    assert (topic.name, topic.student, topic.course) == ("Normalisering", ida, databaser)
    assert response.status_code == 302
    assert response["Location"] == topic_url(topic)


def test_fr2_create_topic_under_htmx_answers_with_hx_location(client_ida, databaser):
    response = client_ida.post(create_topic_url(databaser), {"name": "Normalisering"}, **HTMX_DIALOG)
    assert hx_location(response) == topic_url(Topic.objects.get())


@pytest.mark.parametrize("headers", [{}, HTMX_DIALOG], ids=["page", "htmx"])
def test_fr2_blank_topic_rerenders_d03_with_a_field_error_and_saves_nothing(client_ida, databaser, headers):
    response = client_ida.post(create_topic_url(databaser), {"name": "  "}, **headers)
    assert response.status_code == 200
    assert not Topic.objects.exists()
    content = response.content.decode()
    assert MESSAGES["topic_name_required"] in content
    assert 'aria-invalid="true"' in content
    if headers:
        assert content.lstrip().startswith("<dialog")
        assert "<html" not in content


def test_fr2_too_long_topic_name_is_refused(client_ida, databaser):
    response = client_ida.post(create_topic_url(databaser), {"name": "x" * 81})
    assert MESSAGES["course_name_too_long"] in response.content.decode()
    assert not Topic.objects.exists()


def test_fr2_d03_is_a_page_without_htmx_and_a_dialog_partial_with_it(client_ida, databaser):
    page = client_ida.get(create_topic_url(databaser))
    content = page.content.decode()
    assert content.startswith("<!doctype html>")
    assert "<title>Nytt tema – Databaser – AI Study Buddy</title>" in content
    assert f'action="{create_topic_url(databaser)}"' in content
    assert "Lag tema" in content
    partial = client_ida.get(create_topic_url(databaser), **HTMX_DIALOG)
    body = partial.content.decode()
    assert body.lstrip().startswith("<dialog")
    assert f'hx-post="{create_topic_url(databaser)}"' in body
    assert "<html" not in body
    for response in (page, partial):
        assert {"hx-request", "hx-target", "hx-history-restore-request"} <= vary(response)


# ---- Rename tema (D08) ------------------------------------------------------------------


def test_fr2_rename_topic_from_p04_returns_to_p04(client_ida, databaser, normalisering):
    response = client_ida.post(
        rename_topic_url(normalisering), {"name": "Normalformer", "next": course_url(databaser)}
    )
    assert response["Location"] == course_url(databaser)
    normalisering.refresh_from_db()
    assert normalisering.name == "Normalformer"


@pytest.mark.parametrize("unsafe", ["", "https://evil.example/", "//evil.example/"])
def test_fr2_rename_topic_without_safe_next_lands_on_its_p05(client_ida, normalisering, unsafe):
    response = client_ida.post(rename_topic_url(normalisering), {"name": "Normalformer", "next": unsafe})
    assert response["Location"] == topic_url(normalisering)


def test_fr2_rename_topic_d08_is_prefilled_and_refuses_blank(client_ida, normalisering):
    get = client_ida.get(rename_topic_url(normalisering), **HTMX_DIALOG).content.decode()
    assert get.lstrip().startswith("<dialog")
    assert 'value="Normalisering"' in get
    post = client_ida.post(rename_topic_url(normalisering), {"name": " "}, **HTMX_DIALOG)
    content = post.content.decode()
    assert post.status_code == 200
    assert content.lstrip().startswith("<dialog")
    assert MESSAGES["topic_name_required"] in content
    normalisering.refresh_from_db()
    assert normalisering.name == "Normalisering"


# ---- Delete tema (D09) ------------------------------------------------------------------


def test_fr2_delete_topic_counts_its_sources_and_lands_on_p04(client_ida, databaser, normalisering):
    add_source(normalisering, "a.pdf")
    add_source(normalisering, "b.pdf")
    content = client_ida.get(delete_topic_url(normalisering)).content.decode()
    assert "Slette temaet Normalisering?" in content
    assert "2 kilder og alle svar slettes. Dette kan ikke angres." in content
    assert "Slett temaet" in content
    assert Topic.objects.exists()
    response = client_ida.post(delete_topic_url(normalisering), {"next": topic_url(normalisering)})
    assert response["Location"] == course_url(databaser)
    assert not Topic.objects.exists()
    assert not Source.objects.exists()


def test_fr2_delete_topic_d09_partial_is_an_alertdialog_and_htmx_post_goes_to_p04(
    client_ida, databaser, normalisering
):
    response = client_ida.get(delete_topic_url(normalisering), **HTMX_DIALOG)
    content = response.content.decode()
    assert content.lstrip().startswith('<dialog class="dialog" role="alertdialog"')
    assert 'id="dialog-lead">Dette kan ikke angres.</p>' in content
    assert {"hx-request", "hx-target"} <= vary(response)
    post = client_ida.post(delete_topic_url(normalisering), **HTMX_DIALOG)
    assert hx_location(post) == course_url(databaser)


# ---- Delete fag counts ------------------------------------------------------------------


def test_fr2_delete_course_counts_topics_and_sources_and_removes_all(client_ida, databaser, normalisering):
    add_source(normalisering)
    content = client_ida.get(reverse("courses:delete", args=[databaser.id])).content.decode()
    assert "Slette faget Databaser?" in content
    assert "1 tema, 1 kilde og alle svar slettes. Dette kan ikke angres." in content
    client_ida.post(reverse("courses:delete", args=[databaser.id]))
    assert not Course.objects.exists() and not Topic.objects.exists() and not Source.objects.exists()


def test_fr2_delete_course_counts_the_example_from_experience(client_ida, databaser):
    topics = [services.create_topic(databaser, f"Tema {i}") for i in range(4)]
    for i in range(7):
        add_source(topics[i % 4], f"k{i}.pdf")
    content = client_ida.get(reverse("courses:delete", args=[databaser.id])).content.decode()
    assert "4 temaer, 7 kilder og alle svar slettes. Dette kan ikke angres." in content


def test_fr2_delete_empty_course_says_only_that_it_cannot_be_undone(client_ida, databaser):
    content = client_ida.get(reverse("courses:delete", args=[databaser.id])).content.decode()
    assert "Slette faget Databaser?" in content
    assert 'id="dialog-lead">Dette kan ikke angres.</p>' in content
    assert "og alle svar" not in content


# ---- Rename and delete kilde ------------------------------------------------------------


def test_fr2_rename_source_lands_on_its_p05(client_ida, normalisering):
    source = add_source(normalisering)
    get = client_ida.get(rename_source_url(source), **HTMX_DIALOG).content.decode()
    assert get.lstrip().startswith("<dialog")
    assert 'value="forelesning-3.pdf"' in get
    response = client_ida.post(rename_source_url(source), {"name": "  Forelesning 3  "})
    assert response["Location"] == topic_url(normalisering)
    source.refresh_from_db()
    assert source.name == "Forelesning 3"


def test_fr2_blank_source_name_is_refused(client_ida, normalisering):
    source = add_source(normalisering)
    response = client_ida.post(rename_source_url(source), {"name": ""}, **HTMX_DIALOG)
    assert MESSAGES["source_name_required"] in response.content.decode()
    source.refresh_from_db()
    assert source.name == "forelesning-3.pdf"


def test_fr2_delete_source_names_what_goes_and_lands_on_its_p05(client_ida, normalisering):
    source = add_source(normalisering)
    content = client_ida.get(delete_source_url(source)).content.decode()
    assert "Slette kilden forelesning-3.pdf?" in content
    assert "Studiemateriellet fra kilden og svarene på det slettes. Dette kan ikke angres." in content
    assert "Slett kilden" in content
    partial = client_ida.get(delete_source_url(source), **HTMX_DIALOG).content.decode()
    assert partial.lstrip().startswith('<dialog class="dialog" role="alertdialog"')
    response = client_ida.post(delete_source_url(source), **HTMX_DIALOG)
    assert hx_location(response) == topic_url(normalisering)
    assert not Source.objects.exists()
    assert Topic.objects.filter(pk=normalisering.pk).exists()


# ---- P04 rows ---------------------------------------------------------------------------


def test_fr2_p04_lists_topics_in_creation_order_with_links_mastery_and_menus(client_ida, databaser):
    first = services.create_topic(databaser, "Normalisering")
    second = services.create_topic(databaser, "SQL")
    main = main_of(client_ida.get(course_url(databaser)).content.decode())
    assert main.index("Normalisering") < main.index("SQL")
    for topic in (first, second):
        assert f'href="{topic_url(topic)}"' in main
        assert f'href="{rename_topic_url(topic)}?next={course_url(databaser)}"' in main
        assert f'href="{delete_topic_url(topic)}?next={course_url(databaser)}"' in main
    assert main.count("Ikke nok data ennå") == 2
    assert "Ingen temaer ennå" not in main
    assert f'href="{create_topic_url(databaser)}?next={course_url(databaser)}"' in main
    assert "Nytt tema" in main


def test_fr2_p04_empty_state_offers_nytt_tema(client_ida, databaser):
    main = main_of(client_ida.get(course_url(databaser)).content.decode())
    assert "Ingen temaer ennå" in main
    assert "Et tema samler kildene, kortene og spørsmålene for én del av faget." in main
    assert f'hx-get="{create_topic_url(databaser)}?next={course_url(databaser)}"' in main


# ---- P05 --------------------------------------------------------------------------------


def test_fr2_p05_has_breadcrumb_back_link_title_actions_and_empty_kilder(client_ida, databaser, normalisering):
    content = client_ida.get(topic_url(normalisering)).content.decode()
    assert "<title>Normalisering – Databaser – AI Study Buddy</title>" in content
    main = main_of(content)
    assert '<li><a href="/">Hjem</a></li>' in main
    assert f'<li><a href="{course_url(databaser)}">Databaser</a></li>' in main
    assert '<span aria-current="page">Normalisering</span>' in main
    assert f'class="back-link" href="{course_url(databaser)}"' in main
    assert '<h1 class="page-title">Normalisering</h1>' in main
    assert f'href="{rename_topic_url(normalisering)}?next={topic_url(normalisering)}"' in main
    assert f'href="{delete_topic_url(normalisering)}?next={topic_url(normalisering)}"' in main
    assert ">Kilder</h2>" in main
    assert "Ingen kilder ennå" in main
    assert (
        "Legg til en PDF, en tekstfil eller tekst du limer inn. "
        "Quiz og kort kommer når studiemateriellet er klart."
    ) in main
    empty = main.split('class="empty-state"', 1)[1].split("</section>", 1)[0]
    assert "<a " not in empty
    assert "Legg til kilde" not in content


def test_fr2_p05_rail_keeps_marking_the_fag(client_ida, databaser, normalisering):
    rail = rail_of(client_ida.get(topic_url(normalisering)).content.decode())
    assert f'href="{course_url(databaser)}" aria-current="page"' in rail


def test_fr2_p05_lists_source_rows_newest_first_with_type_size_detail_and_status(
    client_ida, normalisering, freeze_now
):
    freeze_now(datetime.datetime(2026, 11, 16, 9, tzinfo=datetime.UTC))
    old = add_source(normalisering, "eldst.pdf", size_bytes=2_516_582)
    freeze_now(datetime.datetime(2026, 11, 16, 10, tzinfo=datetime.UTC))
    new = services.create_source(normalisering, "notater.txt", SourceKind.TEXT, size_bytes=4096)
    main = main_of(client_ida.get(topic_url(normalisering)).content.decode())
    assert main.index("notater.txt") < main.index("eldst.pdf")
    assert "Ingen kilder ennå" not in main
    assert "PDF ·" in main and "Tekstfil ·" in main
    assert "2,4" in main and "MB" in main
    assert "Detaljnivå: middels" in main
    assert main.count("Lager studiemateriell …") == 2
    for source in (old, new):
        assert f'href="{rename_source_url(source)}?next={topic_url(normalisering)}"' in main
        assert f'href="{delete_source_url(source)}?next={topic_url(normalisering)}"' in main


@pytest.mark.parametrize(
    ("status", "text"),
    [
        (Status.PENDING, "Lager studiemateriell …"),
        (Status.GENERATING, "Lager studiemateriell …"),
        (Status.READY, "Klar"),
        (Status.FAILED, "Feilet"),
    ],
)
def test_fr9_status_label_text_per_status(client_ida, normalisering, status, text):
    source = add_source(normalisering)
    Source.objects.filter(pk=source.pk).update(status=status)
    main = main_of(client_ida.get(topic_url(normalisering)).content.decode())
    label = main.split('class="status-label', 1)[1].split("</span>", 1)[0]
    assert label.endswith(text)


# ---- Ownership: P12 for anything not the Student's --------------------------------------


@pytest.fixture
def jonas_items(student):
    jonas = student("jonas@example.no")
    course = services.create_course(jonas, "Jonas sitt fag")
    topic = services.create_topic(course, "Jonas sitt tema")
    source = services.create_source(topic, "jonas-hemmelig.pdf", SourceKind.PDF)
    return course, topic, source


@pytest.mark.parametrize(
    ("method", "which", "url_of", "data"),
    [
        ("get", 0, create_topic_url, None),
        ("post", 0, create_topic_url, {"name": "Kapret"}),
        ("get", 1, topic_url, None),
        ("get", 1, rename_topic_url, None),
        ("post", 1, rename_topic_url, {"name": "Kapret"}),
        ("get", 1, delete_topic_url, None),
        ("post", 1, delete_topic_url, {}),
        ("get", 2, rename_source_url, None),
        ("post", 2, rename_source_url, {"name": "Kapret"}),
        ("get", 2, delete_source_url, None),
        ("post", 2, delete_source_url, {}),
    ],
    ids=[
        "d03-get", "d03-post", "p05", "topic-d08-get", "topic-d08-post", "topic-d09-get",
        "topic-d09-post", "source-d08-get", "source-d08-post", "source-d09-get", "source-d09-post",
    ],  # fmt: skip
)
def test_fr2_another_students_tema_or_kilde_gives_p12_and_changes_nothing(
    client_ida, jonas_items, method, which, url_of, data
):
    response = getattr(client_ida, method)(url_of(jonas_items[which]), data or {})
    assert response.status_code == 404
    content = response.content.decode()
    assert NOT_FOUND in content
    assert "Jonas sitt" not in content and "jonas-hemmelig" not in content
    assert list(Topic.objects.values_list("name", flat=True)) == ["Jonas sitt tema"]
    assert list(Source.objects.values_list("name", flat=True)) == ["jonas-hemmelig.pdf"]


def test_fr2_another_students_topics_and_sources_are_never_listed(client_ida, databaser, normalisering, jonas_items):
    content = client_ida.get(course_url(databaser)).content.decode()
    content += client_ida.get(topic_url(normalisering)).content.decode()
    assert "Jonas sitt" not in content and "jonas-hemmelig" not in content


# ---- AD-18 mechanics --------------------------------------------------------------------


@pytest.mark.parametrize(
    "url_of",
    [
        lambda c, t, s: create_topic_url(c),
        lambda c, t, s: rename_topic_url(t),
        lambda c, t, s: delete_topic_url(t),
        lambda c, t, s: rename_source_url(s),
        lambda c, t, s: delete_source_url(s),
    ],
    ids=["d03", "topic-d08", "topic-d09", "source-d08", "source-d09"],
)
def test_ad18_every_new_post_requires_csrf(ida, databaser, normalisering, url_of):
    source = add_source(normalisering)
    client = Client(enforce_csrf_checks=True)
    client.force_login(ida)
    response = client.post(url_of(databaser, normalisering, source), {"name": "Ny"})
    assert response.status_code == 403
    assert list(Topic.objects.values_list("name", flat=True)) == ["Normalisering"]
    assert list(Source.objects.values_list("name", flat=True)) == ["forelesning-3.pdf"]


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize(
    "url_of",
    [
        lambda c, t, s: create_topic_url(c),
        lambda c, t, s: topic_url(t),
        lambda c, t, s: rename_topic_url(t),
        lambda c, t, s: delete_topic_url(t),
        lambda c, t, s: rename_source_url(s),
        lambda c, t, s: delete_source_url(s),
    ],
    ids=["d03", "p05", "topic-d08", "topic-d09", "source-d08", "source-d09"],
)
def test_fr1_signed_out_topic_and_source_urls_redirect_to_sign_in(client, databaser, normalisering, method, url_of):
    source = add_source(normalisering)
    url = url_of(databaser, normalisering, source)
    response = getattr(client, method)(url, {"name": "Kapret"} if method == "post" else {})
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:sign_in"))
    assert list(Topic.objects.values_list("name", flat=True)) == ["Normalisering"]
    assert list(Source.objects.values_list("name", flat=True)) == ["forelesning-3.pdf"]


def test_fr2_no_javascript_flow_create_rename_delete_tema_as_full_pages(client_ida, databaser):
    """With JavaScript off every dialog is a page, and each step ends on a full page."""
    p04 = course_url(databaser)
    assert client_ida.get(create_topic_url(databaser) + f"?next={p04}").content.decode().startswith("<!doctype html>")
    created = client_ida.post(create_topic_url(databaser), {"name": "Normalisering", "next": p04}, follow=True)
    topic = Topic.objects.get()
    assert created.redirect_chain[-1][0] == topic_url(topic)
    assert '<h1 class="page-title">Normalisering</h1>' in created.content.decode()
    assert client_ida.get(rename_topic_url(topic) + f"?next={p04}").content.decode().startswith("<!doctype html>")
    renamed = client_ida.post(rename_topic_url(topic), {"name": "Normalformer", "next": p04}, follow=True)
    assert renamed.redirect_chain[-1][0] == p04
    assert "Normalformer" in main_of(renamed.content.decode())
    assert client_ida.get(delete_topic_url(topic)).content.decode().startswith("<!doctype html>")
    deleted = client_ida.post(delete_topic_url(topic), follow=True)
    assert deleted.redirect_chain[-1][0] == p04
    assert "Ingen temaer ennå" in deleted.content.decode()


# ---- Review follow-ups ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("which", "url_of", "fallback_of"),
    [
        ("course", lambda c, t, s: reverse("courses:rename", args=[c.id]), lambda c, t, s: course_url(c)),
        ("course", lambda c, t, s: reverse("courses:delete", args=[c.id]), lambda c, t, s: course_url(c)),
        ("topic", lambda c, t, s: rename_topic_url(t), lambda c, t, s: topic_url(t)),
        ("topic", lambda c, t, s: delete_topic_url(t), lambda c, t, s: topic_url(t)),
        ("source", lambda c, t, s: rename_source_url(s), lambda c, t, s: topic_url(t)),
        ("source", lambda c, t, s: delete_source_url(s), lambda c, t, s: topic_url(t)),
    ],
    ids=["fag-d08", "fag-d09", "tema-d08", "tema-d09", "kilde-d08", "kilde-d09"],
)
@pytest.mark.parametrize("next_url", ["", "/"], ids=["no-next", "safe-next"])
def test_ad18_rename_and_delete_dialogs_post_to_their_own_url_and_cancel_correctly(
    client_ida, databaser, normalisering, which, url_of, fallback_of, next_url
):
    source = add_source(normalisering)
    url = url_of(databaser, normalisering, source)
    cancel = next_url or fallback_of(databaser, normalisering, source)
    query = f"?next={next_url}" if next_url else ""
    page = client_ida.get(url + query).content.decode()
    assert page.startswith("<!doctype html>")
    assert f'action="{url}"' in page
    assert f'<a class="button-secondary" href="{cancel}" data-dialog-close>Avbryt</a>' in page
    partial = client_ida.get(url + query, **HTMX_DIALOG).content.decode()
    assert partial.lstrip().startswith("<dialog")
    assert f'hx-post="{url}"' in partial
    assert f'<a class="button-secondary" href="{cancel}" data-dialog-close>Avbryt</a>' in partial


def test_fr2_too_long_source_rename_is_refused_and_changes_nothing(client_ida, normalisering):
    source = add_source(normalisering)
    response = client_ida.post(rename_source_url(source), {"name": "x" * 81})
    assert response.status_code == 200
    assert MESSAGES["course_name_too_long"] in response.content.decode()
    source.refresh_from_db()
    assert source.name == "forelesning-3.pdf"


def test_p05_post_answers_405(client_ida, normalisering):
    assert client_ida.post(topic_url(normalisering)).status_code == 405


def test_fr2_pasted_source_with_size_zero_shows_no_size(client_ida, normalisering):
    services.create_source(normalisering, "Notater", SourceKind.PASTED, size_bytes=0)
    main = main_of(client_ida.get(topic_url(normalisering)).content.decode())
    meta = main.split('class="item-row-meta">', 1)[1].split("</span>", 1)[0]
    assert meta == "Innlimt tekst · Detaljnivå: middels"
    assert "byte" not in main
