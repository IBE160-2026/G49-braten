"""Browser tests for static/js/app.js (retro action E1-1): Playwright Chromium against live_server.

Opt-in: deselected by the default `-m "not browser"`; run them with

    uv run playwright install chromium
    uv run pytest -m browser

Mock mode (config.settings_test), no Key. Every test here is marked `browser`, uses a transactional
DB (the server thread must see the test's data), and may open sockets to 127.0.0.1 only. Requests
from the browser to any other host are aborted and fail the test.
"""

import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from django.conf import settings
from django.test import Client
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, expect
from pytest_django import live_server_helper

HOST = "127.0.0.1"
HERE = Path(__file__).parent

# htmx swaps are asynchronous; wait on DOM state, never on sleeps (spec Design Notes).
expect.set_options(timeout=5_000)


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.path.is_relative_to(HERE):
            item.add_marker(pytest.mark.browser)
            item.add_marker(pytest.mark.allow_hosts([HOST]))
            item.add_marker(pytest.mark.django_db(transaction=True))


ASYNC_UNSAFE = "DJANGO_ALLOW_ASYNC_UNSAFE"
_saved_async_unsafe = pytest.StashKey[str | None]()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Playwright's sync API keeps an asyncio loop on the main thread, which trips Django's
    async-safety check on plain ORM calls (fixtures, DB flush). Lifted for each browser test, from
    before its fixtures run until after their teardown; restored for every other test."""
    if item.get_closest_marker("browser"):
        item.stash[_saved_async_unsafe] = os.environ.get(ASYNC_UNSAFE)
        os.environ[ASYNC_UNSAFE] = "true"


@pytest.hookimpl(wrapper=True)
def pytest_runtest_teardown(item):
    try:
        return (yield)
    finally:
        if _saved_async_unsafe in item.stash:
            previous = item.stash[_saved_async_unsafe]
            if previous is None:
                os.environ.pop(ASYNC_UNSAFE, None)
            else:
                os.environ[ASYNC_UNSAFE] = previous


@pytest.fixture(scope="session")
def live_server(request):
    """pytest-django's live_server, bound to 127.0.0.1 (its default is `localhost`)."""
    server = live_server_helper.LiveServer(HOST)
    yield server
    server.stop()


@pytest.fixture(scope="session")
def browser(launch_browser):
    """pytest-playwright's browser, with a clear message when Chromium is not installed."""
    try:
        browser = launch_browser()
    except PlaywrightError as error:
        if "Executable doesn't exist" in str(error) or "playwright install" in str(error):
            pytest.fail(
                "Chromium for Playwright is missing. Run `uv run playwright install chromium`, "
                "then `uv run pytest -m browser`.",
                pytrace=False,
            )
        raise
    yield browser
    browser.close()


@pytest.fixture
def offsite_requests(context):
    """Abort and record every browser request that is not for 127.0.0.1; asserted empty after the test."""
    seen: list[str] = []

    def guard(route):
        url = route.request.url
        if urlsplit(url).hostname == HOST or url.startswith(("data:", "blob:", "about:")):
            route.fallback()
        else:
            seen.append(url)
            route.abort()

    context.route("**/*", guard)
    yield seen
    assert seen == [], f"requests left 127.0.0.1: {seen}"


@pytest.fixture
def logged_in_page(live_server, context, offsite_requests):
    """Factory: logged_in_page(student) gives a Page whose context holds that Student's session.

    The session comes from Client.force_login, copied into the browser as a cookie.
    """

    def _login(user) -> Page:
        client = Client()
        client.force_login(user)
        context.add_cookies(
            [{"name": settings.SESSION_COOKIE_NAME, "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
              "url": live_server.url}]
        )  # fmt: skip
        return context.new_page()

    return _login


@pytest.fixture
def url(live_server):
    """url("/path") gives the absolute live_server URL."""
    return lambda path: f"{live_server.url}{path}"
