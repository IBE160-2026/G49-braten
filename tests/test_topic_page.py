"""FR-23 / CAP-6 (story 7): P05 with four tema-tabs, the Sammendrag tab and the card list."""

import datetime
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.core.files import File
from django.test import Client
from django.urls import reverse

from ai import mock
from core.messages import MESSAGES
from courses import services
from courses.models import STALE_AFTER, Source, SourceKind, Status
from ingestion.services import ingest
from studymat import services as studymat_services
from studymat.models import Flashcard, KeyConcept, Question, Summary

pytestmark = pytest.mark.django_db

STATIC = Path(settings.BASE_DIR) / "static"


def topic_url(topic, tab=None):
    url = reverse("web:topic", args=[topic.id])
    return f"{url}?tab={tab}" if tab else url


def main_of(content: str) -> str:
    return content.split('<main id="main"', 1)[1].split("</main>", 1)[0]


def text_of(html: str) -> str:
    """Visible-ish text: tags dropped, whitespace collapsed."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def tablist_of(main: str) -> str:
    return main.split('role="tablist"', 1)[1].split("</div>", 1)[0]


def tab_of(main: str, key: str) -> str:
    return tablist_of(main).split(f'id="tab-{key}"', 1)[1].split("</a>", 1)[0]


def panel_of(main: str) -> str:
    return main.split('role="tabpanel"', 1)[1]


def ready_source(
    topic, name="forelesning-5.pdf", *, kind=SourceKind.PDF, summary="Normalisering fjerner redundans.",
    concepts=(("3NF", "Tredje normalform."),), cards=(("Hva er 1NF?", "Atomiske verdier."),),
    questions=("Hva er en kandidatnøkkel?",), removed=0, language="nb",
):  # fmt: skip
    """A `ready` Source with a Summary and items, as story 6's save leaves it."""
    source = services.create_source(topic, name, kind, size_bytes=1000, content_sha256="a" * 64)
    Source.objects.filter(pk=source.pk).update(status=Status.READY, removed_count=removed, language=language)
    source.refresh_from_db()
    owner = source.student_id
    Summary.objects.create(student_id=owner, source=source, text=summary, detail_level="medium")
    for i, (term, definition) in enumerate(concepts, start=1):
        KeyConcept.objects.create(
            student_id=owner, source=source, term=term, definition=definition, location_index=i, quote=f"sitat {term}"
        )
    for i, (front, back) in enumerate(cards, start=1):
        Flashcard.objects.create(
            student_id=owner, source=source, front=front, back=back, location_index=i, quote=f"sitat {front}"
        )
    for i, prompt in enumerate(questions, start=1):
        Question.objects.create(
            student_id=owner, source=source, kind="free_text", prompt=prompt, hint="Et hint.",
            model_answer="Et svar.", location_index=i, quote="sitat",
        )  # fmt: skip
    return source


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
    return services.create_topic(services.create_course(ida, "Databaser", "DAT102"), "Normalisering")


# ---- Tabs ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "selected"),
    [(None, "summary"), ("summary", "summary"), ("quiz", "quiz"), ("selftest", "selftest"),
     ("sources", "sources"), ("x", "summary"), ("", "summary"), ("SOURCES", "summary")],
)  # fmt: skip
def test_fr23_tab_param_selects_one_tab_and_unknown_gives_summary(client_ida, normalisering, query, selected):
    url = reverse("web:topic", args=[normalisering.id]) + (f"?tab={query}" if query is not None else "")
    response = client_ida.get(url)
    assert response.status_code == 200
    main = main_of(response.content.decode())
    tablist = tablist_of(main)
    assert tablist.count('role="tab"') == 4
    assert tablist.count('aria-selected="true"') == 1
    assert tablist.count('tabindex="0"') == 1
    tab = tab_of(main, selected)
    assert 'aria-selected="true"' in tab and f'aria-controls="panel-{selected}"' in tab and 'tabindex="0"' in tab
    assert f'id="panel-{selected}" aria-labelledby="tab-{selected}"' in main
    assert main.count('role="tabpanel"') == 1


def test_fr23_tabs_are_full_page_links_in_fixed_order_with_counts(client_ida, normalisering):
    ready_source(normalisering, cards=(("a", "b"), ("c", "d")), questions=("q1", "q2", "q3"))
    services.create_source(normalisering, "venter.pdf", SourceKind.PDF, size_bytes=10)
    main = main_of(client_ida.get(topic_url(normalisering)).content.decode())
    tablist = tablist_of(main)
    base = topic_url(normalisering)
    hrefs = re.findall(r'href="([^"]+)"', tablist)
    assert hrefs == [f"{base}?tab={key}" for key in ("summary", "quiz", "selftest", "sources")]
    labels = [text_of(a) for a in re.findall(r'role="tab"[^>]*>(.*?)</a>', tablist)]
    assert labels == ["Sammendrag", "Quiz · 3", "Test deg selv · 2 kort", "Kilder · 2"]
    assert tablist.count('class="tab-count"') == 3
    # Full-page links: no HTMX partial swaps on the tabs.
    assert "hx-" not in tablist


def test_fr23_counts_exclude_items_of_sources_that_are_not_ready(client_ida, normalisering):
    source = ready_source(normalisering)
    Source.objects.filter(pk=source.pk).update(status=Status.FAILED)
    main = main_of(client_ida.get(topic_url(normalisering)).content.decode())
    assert text_of(tab_of(main, "quiz")).endswith("Quiz · 0")
    assert text_of(tab_of(main, "selftest")).endswith("Test deg selv · 0 kort")


def test_fr23_tab_css_hides_counts_visually_below_600_and_selected_is_ink_not_copper():
    css = (STATIC / "css" / "components.css").read_text(encoding="utf-8")
    small = css.split("@media (max-width: 599.98px)", 1)[1].split("}\n}", 1)[0]
    assert ".tab-count" in small and "clip: rect(0 0 0 0)" in small and "display: none" not in small
    selected = css.split('.tema-tab[aria-selected="true"]::after', 1)[1].split("}", 1)[0]
    assert "height: 3px" in selected and "var(--ink)" in selected
    assert "primary" not in css.split(".tema-tabs {", 1)[1].split("/* summary-block", 1)[0]


def test_fr23_app_js_moves_between_tabs_with_arrows_home_end_and_restores_focus():
    script = (STATIC / "js" / "app.js").read_text(encoding="utf-8")
    tabs = script.split("tema-tabs (P05)", 1)[1]
    for key in ('"ArrowRight"', '"ArrowLeft"', '"Home"', '"End"'):
        assert key in tabs
    assert "evt.shiftKey" in tabs
    assert "window.location.href = next.href" in tabs
    assert "sessionStorage" in tabs and "try {" in tabs


# ---- Sammendrag ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_fr23_ready_sample_shows_summary_concepts_with_page_references_and_removed_note(
    client_ida, ida, normalisering
):
    with open(mock.SAMPLE_PATH, "rb") as handle:
        sample = ingest(normalisering, upload=File(handle, name=mock.SAMPLE_NAME), detail_level="medium")
    assert studymat_services.generate(ida, sample)
    main = main_of(client_ida.get(topic_url(normalisering)).content.decode())
    assert 'id="tab-summary"' in main and 'aria-selected="true" aria-controls="panel-summary"' in main
    panel = panel_of(main)
    summary = Summary.objects.get(source=sample)
    assert summary.text.split("\n")[0][:60] in panel
    assert panel.count('class="key-concept-item"') == KeyConcept.objects.filter(source=sample).count() >= 5
    assert len(re.findall(rf"Side \d+ · {re.escape(mock.SAMPLE_NAME)}", panel)) >= 5
    assert MESSAGES["removed_note_one"] in panel
    # Questions are counted, never listed.
    for prompt in Question.objects.filter(source=sample).values_list("prompt", flat=True):
        assert prompt not in main


def test_fr23_two_ready_sources_newest_first_and_no_question_text(client_ida, normalisering, freeze_now):
    freeze_now(datetime.datetime(2026, 11, 16, 9, tzinfo=datetime.UTC))
    ready_source(normalisering, "eldst.pdf", summary="Eldste sammendrag.", questions=("Hemmelig spørsmål A?",))
    freeze_now(datetime.datetime(2026, 11, 16, 10, tzinfo=datetime.UTC))
    ready_source(normalisering, "nyest.txt", kind=SourceKind.TEXT, summary="Nyeste sammendrag.",
                 questions=("Hemmelig spørsmål B?",))  # fmt: skip
    content = client_ida.get(topic_url(normalisering)).content.decode()
    panel = panel_of(main_of(content))
    assert panel.count('class="summary-block"') == 2
    assert panel.index("Nyeste sammendrag.") < panel.index("Eldste sammendrag.")
    assert "Side 1 · eldst.pdf" in panel and "Avsnitt 1 · nyest.txt" in panel
    assert "Hemmelig spørsmål" not in content


def test_fr23_summary_block_holds_name_summary_concepts_and_quoted_reference(client_ida, normalisering):
    source = ready_source(normalisering, summary="Første avsnitt.\n\nAndre avsnitt.", language="en")
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering)).content.decode()))
    block = panel.split(f'id="summary-{source.id}"', 1)[1].split("</article>", 1)[0]
    assert ">forelesning-5.pdf</h2>" in block
    assert '<div class="summary-text" lang="en"><p>Første avsnitt.</p>\n\n<p>Andre avsnitt.</p></div>' in block
    assert "3NF" in block and "Tredje normalform." in block
    assert "Side 1 · forelesning-5.pdf" in block
    assert "«sitat 3NF»" in block
    reference = block.split('class="reference"', 1)[1].split("</div>", 1)[0]
    assert "<a " not in reference
    # No removed note when the Reference check removed nothing.
    assert "ble fjernet" not in block


@pytest.mark.parametrize(
    ("removed", "note"),
    [(1, "1 element ble fjernet fordi kildehenvisningen ikke stemte."),
     (3, "3 elementer ble fjernet fordi kildehenvisningen ikke stemte.")],
)  # fmt: skip
def test_fr8_removed_note_under_the_summary(client_ida, normalisering, removed, note):
    ready_source(normalisering, removed=removed)
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering)).content.decode()))
    assert note in panel


@pytest.mark.parametrize("status", [Status.PENDING, Status.GENERATING])
def test_fr23_generating_source_shows_a_dashed_line_and_no_block(client_ida, normalisering, status):
    source = services.create_source(normalisering, "venter.pdf", SourceKind.PDF, size_bytes=10)
    if status == Status.GENERATING:
        services.claim(source)
    main = main_of(client_ida.get(topic_url(normalisering)).content.decode())
    panel = panel_of(main)
    assert "venter.pdf: sammendraget lages. Vanligvis under 2 minutter." in panel
    assert 'class="summary-pending"' in panel
    assert 'class="summary-block"' not in panel
    # Display only: generation starts from the «Kilder» source-row, never from here.
    assert "hx-post" not in panel and 'hx-trigger="load"' not in main
    assert "Ingen sammendrag ennå" in panel


def test_fr23_stale_generating_source_has_no_pending_line(client_ida, normalisering, freeze_now):
    start = datetime.datetime(2026, 11, 16, 12, tzinfo=datetime.UTC)
    freeze_now(start)
    source = services.create_source(normalisering, "gammel.pdf", SourceKind.PDF, size_bytes=10)
    assert services.claim(source) is not None
    freeze_now(start + STALE_AFTER + datetime.timedelta(minutes=1))
    source.refresh_from_db()
    assert source.status == Status.GENERATING and source.effective_status == Status.FAILED
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering, "summary")).content.decode()))
    assert "summary-pending" not in panel
    assert "gammel.pdf" not in panel
    assert "Ingen sammendrag ennå" in panel


def test_fr23_failed_source_is_left_out_of_sammendrag_with_a_pointer_to_kilder(client_ida, normalisering):
    source = services.create_source(normalisering, "feilet.pdf", SourceKind.PDF, size_bytes=10)
    Source.objects.filter(pk=source.pk).update(status=Status.FAILED, failure_reason="truncated")
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering)).content.decode()))
    assert "feilet.pdf" not in panel
    assert "Ingen sammendrag ennå" in panel
    assert f'href="{topic_url(normalisering, "sources")}"' in panel


def test_fr23_no_sources_shows_the_ingen_kilder_empty_state_on_sammendrag(client_ida, normalisering):
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering)).content.decode()))
    assert "Ingen kilder ennå" in panel
    assert f'hx-get="{reverse("studymat:add_source", args=[normalisering.id])}"' in panel


def test_fr23_location_label_per_source_kind(normalisering):
    pdf = services.create_source(normalisering, "a.pdf", SourceKind.PDF)
    txt = services.create_source(normalisering, "b.txt", SourceKind.TEXT)
    pasted = services.create_source(normalisering, "Notater", SourceKind.PASTED)
    assert studymat_services.location_label(pdf, 14) == "Side 14 · a.pdf"
    assert studymat_services.location_label(txt, 3) == "Avsnitt 3 · b.txt"
    assert studymat_services.location_label(pasted, 2) == "Avsnitt 2 · Notater"


def test_fr23_another_students_items_never_show(client_ida, normalisering, student):
    jonas = student("jonas@example.no")
    jonas_topic = services.create_topic(services.create_course(jonas, "Hemmelig"), "Jonas tema")
    ready_source(jonas_topic, "jonas.pdf", concepts=(("JonasBegrep", "x"),), cards=(("JonasKort", "y"),))
    ready_source(normalisering)
    for tab in ("summary", "quiz", "selftest", "sources"):
        content = client_ida.get(topic_url(normalisering, tab)).content.decode()
        assert "JonasBegrep" not in content and "JonasKort" not in content and "jonas.pdf" not in content
    assert client_ida.get(topic_url(jonas_topic)).status_code == 404


# ---- Quiz ---------------------------------------------------------------------------------


def test_fr23_quiz_tab_counts_ready_questions_and_has_an_empty_history(client_ida, normalisering):
    ready_source(normalisering, questions=("Hva er A?", "Hva er B?"))
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering, "quiz")).content.decode()))
    assert "Quiz i Normalisering" in panel
    assert "2 spørsmål er klare." in panel
    assert "Tidligere quizer" in panel
    assert "Du har ikke tatt en quiz i dette temaet ennå." in panel
    assert "Hva er A?" not in panel and "Hva er B?" not in panel
    # Actions for later stories are left out.
    for later in ("Velg antall og start", "Repeter dagens kort", "Bla i alle kort", "Sett opp prøveeksamen"):
        assert later not in panel


def test_fr23_quiz_tab_without_questions_shows_an_empty_state(client_ida, normalisering):
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering, "quiz")).content.decode()))
    assert "Ingen spørsmål ennå" in panel
    assert "spørsmål er klare" not in panel
    assert "Du har ikke tatt en quiz i dette temaet ennå." in panel


# ---- Test deg selv ------------------------------------------------------------------------


def test_fr23_selftest_lists_cards_newest_source_first_with_front_back_reference_and_menu(
    client_ida, normalisering, freeze_now
):
    freeze_now(datetime.datetime(2026, 11, 16, 9, tzinfo=datetime.UTC))
    ready_source(normalisering, "eldst.pdf", cards=(("Gammel forside", "Gammel bakside"),))
    freeze_now(datetime.datetime(2026, 11, 16, 10, tzinfo=datetime.UTC))
    new = ready_source(normalisering, "nyest.pdf", cards=(("Ny forside 1", "Ny bakside 1"), ("Ny forside 2", "b")))
    main = main_of(client_ida.get(topic_url(normalisering, "selftest")).content.decode())
    panel = panel_of(main)
    assert panel.count('class="flashcard-item"') == 3
    assert panel.index("Ny forside 1") < panel.index("Ny forside 2") < panel.index("Gammel forside")
    assert "Ny bakside 1" in panel and "Side 1 · nyest.pdf" in panel and "«sitat Ny forside 1»" in panel
    card = Flashcard.objects.get(source=new, front="Ny forside 1")
    delete_url = reverse("studymat:delete_item", args=["card", card.id])
    next_param = f"{topic_url(normalisering)}%3Ftab%3Dselftest"
    assert f'hx-get="{delete_url}?next={next_param}" hx-target="#dialog"' in panel
    assert "Slett kortet</a>" in panel
    for later in ("Repeter dagens kort", "Bla i alle kort", "Sett opp prøveeksamen"):
        assert later not in panel


@pytest.mark.parametrize("status", [Status.FAILED, Status.GENERATING])
def test_fr23_selftest_hides_cards_of_a_source_that_is_not_ready(client_ida, normalisering, status):
    ready_source(normalisering, "ikke-klar.pdf", cards=(("Skjult forside", "Skjult bakside"),))
    Source.objects.filter(topic=normalisering).update(status=status)
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering, "selftest")).content.decode()))
    assert "Skjult forside" not in panel and "Skjult bakside" not in panel
    assert 'class="flashcard-item"' not in panel
    assert "Ingen kort ennå" in panel


def test_fr23_selftest_without_cards_shows_an_empty_state(client_ida, normalisering):
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering, "selftest")).content.decode()))
    assert "Ingen kort ennå" in panel


# ---- Kilder -------------------------------------------------------------------------------


def test_fr23_kilder_tab_keeps_legg_til_kilde_and_source_rows(client_ida, normalisering):
    ready_source(normalisering, "klar.pdf")
    pending = services.create_source(normalisering, "venter.pdf", SourceKind.PDF, size_bytes=10)
    panel = panel_of(main_of(client_ida.get(topic_url(normalisering, "sources")).content.decode()))
    assert ">Kilder</h2>" in panel and "Legg til kilde" in panel
    assert panel.count('class="item-row source-row"') == 2
    # The pending row still starts its run from here (story 6).
    row = panel.split(f'id="source-{pending.id}"', 1)[1].split(">", 1)[0]
    assert 'hx-trigger="load"' in row


def test_fr23_other_tabs_do_not_render_source_rows(client_ida, normalisering):
    services.create_source(normalisering, "venter.pdf", SourceKind.PDF, size_bytes=10)
    for tab in ("summary", "quiz", "selftest"):
        main = main_of(client_ida.get(topic_url(normalisering, tab)).content.decode())
        assert "source-row" not in main
        assert 'hx-trigger="load"' not in main


# ---- Landing ------------------------------------------------------------------------------


def test_fr23_upload_lands_on_kilder(client_ida, normalisering):
    url = reverse("studymat:add_source", args=[normalisering.id])
    response = client_ida.post(url, {"text": "Noe tekst.", "name": "", "detail_level": "medium"}, follow=True)
    assert response.redirect_chain[-1][0] == topic_url(normalisering, "sources")
    assert 'aria-selected="true" aria-controls="panel-sources"' in response.content.decode()


def test_fr23_kilde_delete_lands_on_safe_next_else_kilder(client_ida, normalisering):
    first = services.create_source(normalisering, "a.pdf", SourceKind.PDF)
    second = services.create_source(normalisering, "b.pdf", SourceKind.PDF)
    # «Avbryt» without HTMX goes to the same place as the delete.
    dialog = client_ida.get(reverse("courses:delete_source", args=[first.id])).content.decode()
    assert f'<a class="button-secondary" href="{topic_url(normalisering, "sources")}" data-dialog-close>Avbryt</a>' in dialog
    response = client_ida.post(reverse("courses:delete_source", args=[first.id]))
    assert response["Location"] == topic_url(normalisering, "sources")
    response = client_ida.post(
        reverse("courses:delete_source", args=[second.id]), {"next": topic_url(normalisering, "summary")}
    )
    assert response["Location"] == topic_url(normalisering, "summary")
    assert not Source.objects.exists()


def test_fr23_kilde_rename_from_kilder_returns_to_kilder(client_ida, normalisering):
    source = services.create_source(normalisering, "a.pdf", SourceKind.PDF)
    response = client_ida.post(
        reverse("courses:rename_source", args=[source.id]), {"name": "Ny", "next": topic_url(normalisering, "sources")}
    )
    assert response["Location"] == topic_url(normalisering, "sources")


def test_fr23_topic_menu_keeps_the_tab_in_next(client_ida, normalisering):
    main = main_of(client_ida.get(topic_url(normalisering, "quiz")).content.decode())
    rename = reverse("courses:rename_topic", args=[normalisering.id])
    assert f'href="{rename}?next={topic_url(normalisering)}%3Ftab%3Dquiz"' in main


@pytest.mark.django_db(transaction=True)
def test_fr23_generate_row_menu_returns_to_kilder_not_to_the_post_url(client_ida, normalisering):
    source = services.create_source(normalisering, "a.pdf", SourceKind.PDF)
    response = client_ida.post(
        reverse("studymat:generate", args=[source.id]), HTTP_HX_REQUEST="true", HTTP_HX_TARGET=f"source-{source.id}"
    )
    body = response.content.decode()
    assert f"?next={topic_url(normalisering)}%3Ftab%3Dsources" in body
    assert "generate" not in body.split("Gi nytt navn", 1)[0].rsplit("<a", 1)[1]
