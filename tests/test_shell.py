"""FR-2 / CAP-2: the signed-in shell, Hjem P03, Fagoversikt P04, P12, D01 and the theme."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from core.messages import MESSAGES
from courses import services
from web.views import THEME_MAX_AGE

pytestmark = pytest.mark.django_db

STATIC = Path(settings.BASE_DIR) / "static"
THEME = reverse("web:theme")


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def client_ida(ida):
    client = Client()
    client.force_login(ida)
    return client


def rail_of(content: str) -> str:
    return content.split('<nav class="fag-rail"', 1)[1].split("</nav>", 1)[0]


def main_of(content: str) -> str:
    return content.split('<main id="main"', 1)[1].split("</main>", 1)[0]


# ---- New Student -----------------------------------------------------------------------


def test_fr2_new_student_sees_empty_hjem_empty_rail_and_no_fag_switcher(client_ida):
    content = client_ida.get("/").content.decode()
    main = main_of(content)
    assert "Ingen fag ennå" in main
    assert "Lag ett fag for hvert emne du tar, og legg temaer inn under det." in main
    assert "Nytt fag" in main
    assert "Ingen fag ennå. Lag ett fag for hvert emne du tar." in rail_of(content)
    assert "Nytt fag" in rail_of(content)
    assert 'class="fag-switcher"' not in content
    assert "next-step-band" not in content and "forecast" not in content


# ---- Shell -----------------------------------------------------------------------------


def test_fr2_rail_lists_fag_with_zero_due_and_no_mastery_yet(client_ida, ida):
    services.create_course(ida, "Databaser", "DAT102")
    rail = rail_of(client_ida.get("/").content.decode())
    assert '<span class="fag-rail-name">Databaser</span>' in rail
    assert '<span class="fag-rail-code">DAT102</span>' in rail
    assert '<span class="fag-rail-pct">–</span>' in rail
    assert "rail-meter--none" in rail
    assert ", ingen kort i dag" in rail
    # «I dag · 0» is plain text until Repetisjon exists.
    assert re.search(r'<p class="rail-link rail-link--text">.*I dag · <b>0</b>', rail)


def test_fr2_rail_marks_hjem_as_current_on_hjem(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    rail = rail_of(client_ida.get("/").content.decode())
    assert re.search(r'<a class="rail-link" href="/" aria-current="page">', rail)
    assert f'href="/courses/{course.id}/" aria-current' not in rail


def test_fr2_rail_marks_the_fag_as_current_on_its_p04(client_ida, ida):
    first = services.create_course(ida, "Databaser")
    second = services.create_course(ida, "Statistikk")
    rail = rail_of(client_ida.get(reverse("web:course", args=[second.id])).content.decode())
    assert f'<a class="fag-rail-row" href="/courses/{second.id}/" aria-current="page">' in rail
    assert f'<a class="fag-rail-row" href="/courses/{first.id}/">' in rail
    assert rail.count('aria-current="page"') == 1


def test_fr2_fag_switcher_shows_all_fag_on_hjem_and_the_fag_on_p04(client_ida, ida):
    course = services.create_course(ida, "Databaser", "DAT102")
    services.create_course(ida, "Statistikk")
    home = client_ida.get("/").content.decode()
    assert 'aria-label="Bytt fag"' in home
    assert 'aria-haspopup="listbox"' in home
    assert re.search(r"Alle fag<small>2 fag</small>", home)
    assert "Hjem · alle fag" in home
    p04 = client_ida.get(reverse("web:course", args=[course.id])).content.decode()
    assert "Databaser<small>DAT102</small>" in p04
    assert re.search(rf'href="/courses/{course.id}/" aria-selected="true"', p04)


def test_ad13_base_loads_vendored_htmx_and_app_js_deferred_in_head(client_ida):
    content = client_ida.get("/").content.decode()
    head = content.split("</head>")[0]
    assert '<script src="/static/vendor/htmx-2.0.11.min.js" defer></script>' in head
    assert '<script src="/static/js/app.js" defer></script>' in head
    assert '"historyRestoreAsHxRequest": false' in head
    assert 'hx-headers=\'{"X-CSRFToken": ' in content
    for slot in ('id="dialog"', 'id="live-polite"', 'id="live-assertive"'):
        assert slot in content


def test_ad13_vendored_files_are_present():
    htmx = (STATIC / "vendor" / "htmx-2.0.11.min.js").read_text(encoding="utf-8")
    assert 'version:"2.0.11"' in htmx
    fonts = STATIC / "fonts" / "public-sans"
    assert "SIL Open Font License" in (fonts / "OFL.txt").read_text(encoding="utf-8")
    assert list(fonts.glob("*.woff2"))
    assert "font-family: 'Public Sans'" in (STATIC / "css" / "components.css").read_text(encoding="utf-8")


def test_ad13_app_js_binds_only_delegated_listeners_and_never_confirms():
    script = (STATIC / "js" / "app.js").read_text(encoding="utf-8")
    listeners = re.findall(r"(\w+)\.addEventListener\(", script)
    assert set(listeners) <= {"document", "window"}
    assert "confirm(" not in script


def test_ad18_no_template_uses_hx_confirm():
    templates = Path(settings.BASE_DIR) / "templates"
    for path in templates.rglob("*.html"):
        assert "hx-confirm" not in path.read_text(encoding="utf-8"), path


# ---- Hjem (P03) and Fagoversikt (P04) ----------------------------------------------------


def test_fr2_hjem_has_one_row_per_fag_with_actions(client_ida, ida):
    course = services.create_course(ida, "Databaser", "DAT102")
    main = main_of(client_ida.get("/").content.decode())
    assert '<h1 class="page-title">Hjem</h1>' in main
    assert '<span class="course-row-name">Databaser</span>' in main
    assert '<span class="course-row-code">DAT102</span>' in main
    assert "Ikke nok data ennå" in main
    assert 'aria-label="Flere valg for Databaser"' in main
    assert f'popovertarget="course-menu-{course.id}"' in main
    assert f'href="/courses/{course.id}/rename/?next=/"' in main
    assert f'href="/courses/{course.id}/delete/?next=/"' in main
    assert ">Gi nytt navn</a>" in main and ">Slett</a>" in main
    assert "Ingen fag ennå" not in main


def test_fr2_p04_has_breadcrumb_title_code_actions_and_empty_state(client_ida, ida):
    course = services.create_course(ida, "Databaser", "DAT102")
    content = client_ida.get(reverse("web:course", args=[course.id])).content.decode()
    assert "<title>Databaser – AI Study Buddy</title>" in content
    main = main_of(content)
    assert 'aria-label="Brødsmuler"' in main
    assert '<li><a href="/">Hjem</a></li>' in main
    assert '<span aria-current="page">Databaser</span>' in main
    assert 'class="back-link" href="/"' in main
    assert '<h1 class="page-title">Databaser</h1>' in main
    assert '<p class="page-meta">DAT102</p>' in main
    assert f'href="/courses/{course.id}/rename/?next=/courses/{course.id}/"' in main
    assert "Ingen temaer ennå" in main
    assert "Et tema samler kildene, kortene og spørsmålene for én del av faget." in main
    assert "Nytt tema" not in content


# ---- P12 -------------------------------------------------------------------------------


def test_fr1_unknown_url_signed_in_shows_p12_in_the_shell(client_ida, ida):
    services.create_course(ida, "Databaser")
    response = client_ida.get("/nope/")
    assert response.status_code == 404
    content = response.content.decode()
    assert "<title>Fant ikke siden – AI Study Buddy</title>" in content
    main = main_of(content)
    for text in (
        "Feil 404",
        "Fant ikke siden",
        "Sjekk adressen, eller velg et fag i listen. Fagene dine og dagens kort står der som før.",
        "Til Hjem",
    ):
        assert text in main
    assert "Databaser" in rail_of(content)


def test_fr1_unknown_url_signed_out_shows_p12_without_the_shell(client):
    response = client.get("/nope/")
    assert response.status_code == 404
    content = response.content.decode()
    assert "Fant ikke siden" in content
    assert 'class="fag-rail"' not in content


# ---- D01 and the theme -----------------------------------------------------------------


def test_fr1_d01_offers_utseende_and_logg_ut(client_ida):
    content = client_ida.get("/").content.decode()
    menu = content.split('id="account-menu"', 1)[1].split("</div>\n\n", 1)[0]
    assert "popover" in content.split('id="account-menu"', 1)[1][:80]
    assert "Utseende" in menu
    for value, label in (("system", "System"), ("light", "Lys"), ("dark", "Mørk")):
        assert f'value="{value}"' in menu and f">{label}</button>" in menu
    assert f'action="{reverse("accounts:sign_out")}"' in menu
    assert "Logg ut" in menu
    assert content.count('popovertarget="account-menu"') == 2


def test_d01_choosing_mork_sets_the_cookie_and_renders_data_theme(client_ida):
    response = client_ida.post(THEME, {"theme": "dark", "next": "/"})
    assert response.status_code == 302
    assert response["Location"] == "/"
    cookie = response.cookies["theme"]
    assert cookie.value == "dark"
    assert cookie["max-age"] == THEME_MAX_AGE
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"
    content = client_ida.get("/").content.decode()
    assert '<html lang="nb" data-theme="dark">' in content
    assert re.search(r'value="dark" aria-pressed="true"', content)


def test_d01_system_clears_the_cookie(client_ida):
    client_ida.post(THEME, {"theme": "light"})
    response = client_ida.post(THEME, {"theme": "system"})
    assert response.cookies["theme"].value == ""
    assert response.cookies["theme"]["max-age"] == 0
    content = client_ida.get("/").content.decode()
    assert "data-theme" not in content.split(">", 2)[1]
    assert re.search(r'value="system" aria-pressed="true"', content)


def test_d01_invalid_theme_value_is_ignored(client_ida):
    client_ida.post(THEME, {"theme": "dark"})
    response = client_ida.post(THEME, {"theme": "purple"})
    assert "theme" not in response.cookies
    assert 'data-theme="dark"' in client_ida.get("/").content.decode()


def test_d01_invalid_theme_cookie_is_not_rendered(client_ida):
    client_ida.cookies["theme"] = '"><script>'
    content = client_ida.get("/").content.decode()
    assert "data-theme" not in content.split(">", 2)[1]


def test_d01_theme_unsafe_next_lands_on_hjem(client_ida):
    response = client_ida.post(THEME, {"theme": "dark", "next": "https://evil.example/"})
    assert response["Location"] == "/"


def test_d01_theme_is_post_only(client_ida):
    assert client_ida.get(THEME).status_code == 405


@pytest.mark.parametrize("url", [THEME, reverse("accounts:sign_out")])
def test_ad18_theme_and_sign_out_require_csrf(ida, url):
    client = Client(enforce_csrf_checks=True)
    client.force_login(ida)
    assert client.post(url, {"theme": "dark"}).status_code == 403


def test_fr1_shell_requires_sign_in(client):
    response = client.get(reverse("web:course", args=[1]))
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:sign_in"))


def test_ad18_shell_carries_the_fixed_failure_messages(client_ida):
    content = client_ida.get("/").content.decode()
    network = content.split('id="message-network-error"', 1)[1].split("</template>", 1)[0]
    response = content.split('id="message-response-error"', 1)[1].split("</template>", 1)[0]
    assert MESSAGES["network_error"] in network
    assert MESSAGES["response_error"] in response


def test_hjem_and_p04_answer_head(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    assert client_ida.head("/").status_code == 200
    assert client_ida.head(reverse("web:course", args=[course.id])).status_code == 200
