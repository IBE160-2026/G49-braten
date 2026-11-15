"""FR-2 / CAP-2: create (D02), rename (D08) and delete (D09) a fag, owned per Student (AD-7)."""

import datetime
import json

import pytest
from django.test import Client
from django.urls import reverse

from core.messages import MESSAGES
from courses import services
from courses.models import Course

pytestmark = pytest.mark.django_db

CREATE = reverse("courses:create")
HTMX_DIALOG = {"HTTP_HX_REQUEST": "true", "HTTP_HX_TARGET": "dialog"}
NOT_FOUND = "Fant ikke siden"


def rename_url(course):
    return reverse("courses:rename", args=[course.id])


def delete_url(course):
    return reverse("courses:delete", args=[course.id])


def course_url(course):
    return reverse("web:course", args=[course.id])


@pytest.fixture
def ida(student):
    return student("ida@example.no")


@pytest.fixture
def client_ida(ida):
    client = Client()
    client.force_login(ida)
    return client


def hx_location(response) -> str:
    return json.loads(response["HX-Location"])["path"]


def vary(response) -> set[str]:
    return {v.strip().lower() for v in response.get("Vary", "").split(",")}


# ---- Create (D02) ----------------------------------------------------------------------


def test_fr2_create_saves_course_for_this_student_and_lands_on_its_p04(client_ida, ida):
    response = client_ida.post(CREATE, {"name": "Databaser", "code": "DAT102"})
    course = Course.objects.get()
    assert course.student == ida
    assert (course.name, course.code) == ("Databaser", "DAT102")
    assert response.status_code == 302
    assert response["Location"] == course_url(course)


def test_fr2_create_strips_name_and_code_and_code_is_optional(client_ida):
    client_ida.post(CREATE, {"name": "  Statistikk  ", "code": "   "})
    course = Course.objects.get()
    assert (course.name, course.code) == ("Statistikk", "")


def test_fr2_create_under_htmx_answers_with_hx_location(client_ida):
    response = client_ida.post(CREATE, {"name": "Databaser", "code": ""}, **HTMX_DIALOG)
    assert response.status_code == 200
    assert Course.objects.count() == 1
    assert hx_location(response) == course_url(Course.objects.get())


def test_fr2_new_course_appears_last_in_rail_and_hjem(client_ida, ida):
    services.create_course(ida, "Databaser", "DAT102")
    client_ida.post(CREATE, {"name": "Statistikk", "code": "STA100"})
    content = client_ida.get("/").content.decode()
    rail = content.split('class="fag-rail"')[1].split("</nav>")[0]
    assert rail.index("Databaser") < rail.index("Statistikk")
    main = content.split('<main id="main"')[1]
    assert main.index("Databaser") < main.index("Statistikk")


def test_fr2_courses_are_listed_in_creation_order(ida, freeze_now):
    freeze_now(datetime.datetime(2026, 11, 16, 9, tzinfo=datetime.UTC))
    first = services.create_course(ida, "Zeta")
    freeze_now(datetime.datetime(2026, 11, 16, 10, tzinfo=datetime.UTC))
    second = services.create_course(ida, "Alfa")
    assert first.created_at < second.created_at
    assert list(Course.objects.for_student(ida)) == [first, second]


@pytest.mark.parametrize("headers", [{}, HTMX_DIALOG], ids=["page", "htmx"])
def test_fr2_blank_name_rerenders_d02_with_a_field_error_and_saves_nothing(client_ida, headers):
    response = client_ida.post(CREATE, {"name": "   ", "code": "DAT102"}, **headers)
    assert response.status_code == 200
    assert Course.objects.count() == 0
    content = response.content.decode()
    assert MESSAGES["course_name_required"] in content
    assert 'aria-invalid="true"' in content
    assert 'id="id_name-error"' in content
    if headers:
        assert content.lstrip().startswith("<dialog")
        assert "<html" not in content


@pytest.mark.parametrize(
    ("data", "code"),
    [
        ({"name": "x" * 81, "code": ""}, "course_name_too_long"),
        ({"name": "Databaser", "code": "x" * 21}, "course_code_too_long"),
    ],
)
def test_fr2_too_long_name_or_code_is_refused(client_ida, data, code):
    response = client_ida.post(CREATE, data)
    assert response.status_code == 200
    assert MESSAGES[code] in response.content.decode()
    assert Course.objects.count() == 0


def test_fr2_name_of_80_and_code_of_20_characters_are_accepted(client_ida):
    client_ida.post(CREATE, {"name": "x" * 80, "code": "y" * 20})
    assert Course.objects.count() == 1


# ---- Rename (D08) ----------------------------------------------------------------------


def test_fr2_rename_from_hjem_changes_name_and_returns_to_hjem(client_ida, ida):
    course = services.create_course(ida, "Databaser", "DAT102")
    response = client_ida.post(rename_url(course), {"name": "Databaser 2", "next": "/"})
    assert response.status_code == 302
    assert response["Location"] == "/"
    course.refresh_from_db()
    assert course.name == "Databaser 2"
    assert course.code == "DAT102"


def test_fr2_rename_without_next_lands_on_p04(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    response = client_ida.post(rename_url(course), {"name": "Databaser 2"})
    assert response["Location"] == course_url(course)


@pytest.mark.parametrize("unsafe", ["https://evil.example/", "//evil.example/", "javascript:alert(1)"])
def test_fr2_rename_with_unsafe_next_lands_on_p04(client_ida, ida, unsafe):
    course = services.create_course(ida, "Databaser")
    response = client_ida.post(rename_url(course), {"name": "Databaser 2", "next": unsafe})
    assert response["Location"] == course_url(course)


def test_fr2_rename_under_htmx_answers_with_hx_location_to_next(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    response = client_ida.post(rename_url(course), {"name": "Nytt", "next": "/"}, **HTMX_DIALOG)
    assert hx_location(response) == "/"


def test_fr2_d08_is_prefilled_and_blank_name_is_refused(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    content = client_ida.get(rename_url(course)).content.decode()
    assert 'value="Databaser"' in content
    response = client_ida.post(rename_url(course), {"name": " "})
    assert response.status_code == 200
    assert MESSAGES["course_name_required"] in response.content.decode()
    course.refresh_from_db()
    assert course.name == "Databaser"


# ---- Delete (D09) ----------------------------------------------------------------------


def test_fr2_get_delete_shows_the_confirmation_and_deletes_nothing(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    response = client_ida.get(delete_url(course))
    assert response.status_code == 200
    content = response.content.decode()
    assert "Slette faget Databaser?" in content
    assert "Alt i faget slettes. Dette kan ikke angres." in content
    assert "Slett faget" in content
    assert Course.objects.filter(pk=course.pk).exists()


def test_fr2_d09_under_htmx_is_an_alertdialog_partial(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    content = client_ida.get(delete_url(course), **HTMX_DIALOG).content.decode()
    assert content.lstrip().startswith('<dialog class="dialog" role="alertdialog"')
    assert 'aria-describedby="dialog-lead"' in content
    assert "button-destructive" in content


def test_fr2_confirm_delete_removes_course_and_lands_on_hjem(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    response = client_ida.post(delete_url(course), {"next": course_url(course)})
    assert response.status_code == 302
    assert response["Location"] == "/"
    assert not Course.objects.exists()


def test_fr2_confirm_delete_under_htmx_answers_with_hx_location_to_hjem(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    response = client_ida.post(delete_url(course), **HTMX_DIALOG)
    assert hx_location(response) == "/"


def test_fr2_deleting_a_student_deletes_their_courses(ida):
    services.create_course(ida, "Databaser")
    ida.delete()
    assert not Course.objects.exists()


# ---- Ownership (AD-7) ------------------------------------------------------------------


@pytest.fixture
def jonas_course(student):
    return services.create_course(student("jonas@example.no"), "Jonas sitt fag", "SECRET1")


@pytest.mark.parametrize(
    ("method", "url_of", "data"),
    [
        ("get", course_url, None),
        ("get", rename_url, None),
        ("post", rename_url, {"name": "Kapret"}),
        ("get", delete_url, None),
        ("post", delete_url, {}),
    ],
    ids=["p04", "d08-get", "d08-post", "d09-get", "d09-post"],
)
def test_fr2_another_students_course_gives_p12_and_changes_nothing(client_ida, jonas_course, method, url_of, data):
    unknown = getattr(client_ida, method)(url_of(jonas_course).replace(str(jonas_course.id), "999999"), data or {})
    response = getattr(client_ida, method)(url_of(jonas_course), data or {})
    assert response.status_code == 404
    content = response.content.decode()
    assert NOT_FOUND in content
    assert "Jonas sitt fag" not in content
    assert "SECRET1" not in content
    jonas_course.refresh_from_db()
    assert jonas_course.name == "Jonas sitt fag"
    # Exactly the same page as an id that does not exist.
    assert unknown.status_code == 404
    strip = lambda html: html.split("<main", 1)[1].split("</main>", 1)[0]  # noqa: E731
    assert strip(content) == strip(unknown.content.decode())


def test_fr2_course_of_another_student_is_never_listed(client_ida, ida, jonas_course):
    services.create_course(ida, "Databaser")
    content = client_ida.get("/").content.decode()
    assert "Databaser" in content
    assert "Jonas sitt fag" not in content
    content = client_ida.get(CREATE).content.decode()
    assert "Jonas sitt fag" not in content


# ---- AD-13 / AD-18 mechanics ------------------------------------------------------------


def test_ad13_htmx_dialog_get_returns_only_the_partial_with_vary(client_ida):
    response = client_ida.get(CREATE, **HTMX_DIALOG)
    content = response.content.decode()
    assert content.lstrip().startswith("<dialog")
    assert "<html" not in content and "<title>" not in content
    assert {"hx-request", "hx-target", "hx-history-restore-request"} <= vary(response)


def test_ad13_dialog_without_htmx_is_a_full_page_with_vary(client_ida):
    response = client_ida.get(CREATE)
    content = response.content.decode()
    assert content.startswith("<!doctype html>")
    assert "<title>Nytt fag – AI Study Buddy</title>" in content
    assert "<dialog" not in content
    assert 'class="dialog dialog--page"' in content
    assert "hx-post" not in content.split('class="dialog dialog--page"')[1]
    assert {"hx-request", "hx-target", "hx-history-restore-request"} <= vary(response)


def test_ad13_history_restore_gets_the_full_page(client_ida):
    response = client_ida.get(CREATE, HTTP_HX_HISTORY_RESTORE_REQUEST="true", **HTMX_DIALOG)
    assert response.content.decode().startswith("<!doctype html>")


def test_ad13_htmx_request_for_another_target_gets_the_full_page(client_ida):
    response = client_ida.get(CREATE, HTTP_HX_REQUEST="true", HTTP_HX_TARGET="main")
    assert response.content.decode().startswith("<!doctype html>")


def test_ad18_dialog_form_guards_against_repeat_presses(client_ida):
    content = client_ida.get(CREATE, **HTMX_DIALOG).content.decode()
    assert 'hx-post="/courses/new/"' in content
    assert 'hx-target="#dialog"' in content
    assert "hx-disabled-elt=" in content
    assert 'hx-sync="this:drop"' in content
    assert "hx-confirm" not in content
    assert "data-dialog-close" in content
    assert "Avbryt" in content


def test_ad18_dialog_starts_on_its_title_and_an_error_moves_focus_to_the_field(client_ida):
    content = client_ida.get(CREATE, **HTMX_DIALOG).content.decode()
    assert 'id="dialog-title" tabindex="-1" autofocus' in content
    invalid = client_ida.post(CREATE, {"name": ""}, **HTMX_DIALOG).content.decode()
    assert 'id="dialog-title" tabindex="-1" autofocus' not in invalid
    assert 'name="name"' in invalid and "autofocus" in invalid.split('name="name"')[1].split(">")[0]


@pytest.mark.parametrize("path", ["/courses/new/", "/courses/{id}/rename/", "/courses/{id}/delete/"])
def test_ad18_every_course_post_requires_csrf(ida, path):
    course = services.create_course(ida, "Databaser")
    client = Client(enforce_csrf_checks=True)
    client.force_login(ida)
    response = client.post(path.format(id=course.id), {"name": "Ny"})
    assert response.status_code == 403
    course.refresh_from_db()
    assert course.name == "Databaser"
    assert Course.objects.count() == 1


def test_fr2_no_javascript_flow_create_rename_delete_as_full_pages(client_ida):
    """With JavaScript off every dialog is a page, and each step ends on a full page."""
    page = client_ida.get(CREATE + "?next=/")
    assert page.content.decode().startswith("<!doctype html>")
    created = client_ida.post(CREATE, {"name": "Databaser", "code": "DAT102", "next": "/"}, follow=True)
    course = Course.objects.get()
    assert created.redirect_chain[-1][0] == course_url(course)
    assert "<h1 class=\"page-title\">Databaser</h1>" in created.content.decode()
    renamed = client_ida.post(rename_url(course), {"name": "Databaser 2", "next": course_url(course)}, follow=True)
    assert "<h1 class=\"page-title\">Databaser 2</h1>" in renamed.content.decode()
    deleted = client_ida.post(delete_url(course), follow=True)
    assert deleted.redirect_chain[-1][0] == "/"
    assert "Ingen fag ennå" in deleted.content.decode()


def test_fr2_d08_under_htmx_returns_only_the_dialog_partial(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    get = client_ida.get(rename_url(course), **HTMX_DIALOG).content.decode()
    assert get.lstrip().startswith("<dialog")
    assert "<html" not in get
    assert 'value="Databaser"' in get
    post = client_ida.post(rename_url(course), {"name": "  "}, **HTMX_DIALOG)
    assert post.status_code == 200
    content = post.content.decode()
    assert content.lstrip().startswith("<dialog")
    assert "<html" not in content
    assert MESSAGES["course_name_required"] in content
    course.refresh_from_db()
    assert course.name == "Databaser"


def test_fr2_too_long_rename_is_refused_and_changes_nothing(client_ida, ida):
    course = services.create_course(ida, "Databaser")
    response = client_ida.post(rename_url(course), {"name": "x" * 81})
    assert response.status_code == 200
    assert MESSAGES["course_name_too_long"] in response.content.decode()
    course.refresh_from_db()
    assert course.name == "Databaser"


@pytest.mark.parametrize("method", ["get", "post"])
@pytest.mark.parametrize("url_of", [lambda c: CREATE, rename_url, delete_url], ids=["create", "rename", "delete"])
def test_fr1_signed_out_course_dialogs_redirect_to_sign_in_and_change_nothing(client, ida, method, url_of):
    course = services.create_course(ida, "Databaser")
    response = getattr(client, method)(url_of(course), {"name": "Kapret"} if method == "post" else {})
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:sign_in"))
    assert list(Course.objects.values_list("name", flat=True)) == ["Databaser"]
