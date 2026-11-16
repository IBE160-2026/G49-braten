"""FR-20, FR-21 (story 5): the mode-banner on every page in Mock mode, and never the Key."""

import pytest
from django.test import Client
from django.urls import reverse

from courses import services

pytestmark = pytest.mark.django_db

BANNER_TEXT = (
    "<b>Demomodus:</b> appen bruker innspilte svar for eksempeldokumentet. "
    "Legg inn en API-nøkkel for å bruke egne filer."
)
SECRET_KEY = "sk-ant-api03-this-key-must-never-be-rendered"


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def client_ida(ida):
    client = Client()
    client.force_login(ida)
    return client


@pytest.fixture
def topic(ida):
    return services.create_topic(services.create_course(ida, "Databaser", "DAT102"), "Normalisering")


def signed_in_urls(topic):
    return [
        reverse("web:home"),
        reverse("web:course", args=[topic.course_id]),
        reverse("web:topic", args=[topic.id]),
        reverse("studymat:add_source", args=[topic.id]),
        "/finnes-ikke/",  # P12 in the shell
    ]


def banner_count(content: str) -> int:
    return content.count('class="mode-banner"')


def test_fr20_mock_mode_shows_the_banner_on_p01_and_p02():
    client = Client()
    for name in ("accounts:sign_in", "accounts:sign_up"):
        content = client.get(reverse(name)).content.decode()
        assert banner_count(content) == 1, name
        assert BANNER_TEXT in content


def test_fr20_mock_mode_shows_the_banner_under_the_top_bar_on_every_shell_page(client_ida, topic):
    for url in signed_in_urls(topic):
        content = client_ida.get(url).content.decode()
        assert banner_count(content) == 1, url
        assert BANNER_TEXT in content
        assert content.index('class="top-bar"') < content.index('class="mode-banner"') < content.index('<main id="main"')


def test_fr20_the_banner_cannot_be_closed(client_ida):
    content = client_ida.get(reverse("web:home")).content.decode()
    banner = content.split('class="mode-banner"', 1)[1].split("</p>", 1)[0]
    assert "<button" not in banner and "Lukk" not in banner


def test_fr20_an_empty_env_means_mock_mode():
    from config.env import effective_ai_provider

    assert effective_ai_provider({}) == "mock"
    assert effective_ai_provider({"ANTHROPIC_API_KEY": SECRET_KEY, "AI_PROVIDER": "mock"}) == "mock"
    assert effective_ai_provider({"ANTHROPIC_API_KEY": SECRET_KEY, "AI_PROVIDER": "anthropic"}) == "anthropic"


def test_fr21_real_mode_shows_no_banner_and_never_renders_the_key(settings, client_ida, topic):
    settings.AI_PROVIDER = "anthropic"
    settings.ANTHROPIC_API_KEY = SECRET_KEY
    responses = [Client().get(reverse("accounts:sign_in")), Client().get(reverse("accounts:sign_up"))]
    responses += [client_ida.get(url) for url in signed_in_urls(topic)]
    responses.append(client_ida.get(reverse("studymat:add_source", args=[topic.id]), HTTP_HX_REQUEST="true", HTTP_HX_TARGET="dialog"))
    for response in responses:
        content = response.content.decode()
        assert banner_count(content) == 0
        assert "Demomodus" not in content
        assert SECRET_KEY not in content
        assert SECRET_KEY not in str(response.headers)
