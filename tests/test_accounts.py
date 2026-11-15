"""FR-1 / CAP-1: sign up, sign in, sign out; sign-in required everywhere (AD-7)."""

from urllib.parse import urlencode

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import Student
from core.messages import MESSAGES
from tests.conftest import PASSWORD

pytestmark = pytest.mark.django_db

SIGN_IN = reverse("accounts:sign_in")
SIGN_UP = reverse("accounts:sign_up")
SIGN_OUT = reverse("accounts:sign_out")


def signed_in_email(client: Client) -> str | None:
    response = client.get("/")
    return response.context["user"].email if response.status_code == 200 else None


# ---- Sign up -------------------------------------------------------------------------


def test_fr1_sign_up_creates_normalised_student_signs_in_and_lands_home(client):
    response = client.post(SIGN_UP, {"email": "Ida@Example.no", "password": PASSWORD})
    assert response.status_code == 302
    assert response["Location"] == "/"
    assert Student.objects.get().email == "ida@example.no"
    assert signed_in_email(client) == "ida@example.no"


def assert_email_in_use_shown(response, sign_in_link=SIGN_IN):
    assert response.status_code == 200
    content = response.content.decode()
    assert MESSAGES["email_in_use"] in content
    assert f'{MESSAGES["email_in_use"]} <a href="{sign_in_link}">Logg inn</a>' in content
    assert 'aria-invalid="true"' in content
    assert 'aria-describedby="id_email-error"' in content
    assert 'id="id_email-error"' in content


def test_fr1_sign_up_with_taken_email_shows_in_use_message(client, student):
    student("ida@example.no")
    response = client.post(SIGN_UP, {"email": " IDA@example.no ", "password": PASSWORD})
    assert_email_in_use_shown(response)
    assert Student.objects.count() == 1


def test_fr1_email_in_use_sign_in_link_keeps_next(client, student):
    student("ida@example.no")
    response = client.post(
        f"{SIGN_UP}?next=/topics/12/",
        {"email": "ida@example.no", "password": PASSWORD, "next": "/topics/12/"},
    )
    assert_email_in_use_shown(response, sign_in_link=f"{SIGN_IN}?next=%2Ftopics%2F12%2F")


def test_fr1_sign_up_with_weak_password_shows_validator_text_in_bokmal(client):
    response = client.post(SIGN_UP, {"email": "ida@example.no", "password": "12345678"})
    assert response.status_code == 200
    assert Student.objects.count() == 0
    errors = response.context["form"].errors["password"]
    assert errors == ["Dette passordet er for vanlig."]
    content = response.content.decode()
    assert 'aria-invalid="true"' in content
    assert 'aria-describedby="id_password-help id_password-error"' in content


def test_fr1_password_rules_are_shown_on_p02(client):
    content = client.get(SIGN_UP).content.decode()
    assert '<p class="help-text" id="id_password-help">Minst 8 tegn, og ikke et vanlig passord.</p>' in content
    assert 'aria-describedby="id_password-help"' in content


@pytest.mark.parametrize(
    ("data", "invalid_fields"),
    [
        ({"email": "ikke-en-adresse", "password": PASSWORD}, ["email"]),
        ({"email": "ida@@example.no", "password": PASSWORD}, ["email"]),
        ({"email": "", "password": ""}, ["email", "password"]),
    ],
)
def test_fr1_sign_up_with_bad_input_rerenders_with_errors(client, data, invalid_fields):
    response = client.post(SIGN_UP, data)
    assert response.status_code == 200
    assert Student.objects.count() == 0
    assert sorted(response.context["form"].errors) == invalid_fields
    content = response.content.decode()
    for name in invalid_fields:
        assert f'id="id_{name}-error"' in content


def test_fr1_sign_up_race_on_email_gives_same_field_error(client, monkeypatch):
    """Another request takes the email between the check and the insert."""
    from accounts import forms

    real_clean_email = forms.SignUpForm.clean_email

    def clean_then_steal(self):
        email = real_clean_email(self)
        Student.objects.create_user(email, PASSWORD)
        return email

    monkeypatch.setattr(forms.SignUpForm, "clean_email", clean_then_steal)
    response = client.post(SIGN_UP, {"email": "ida@example.no", "password": PASSWORD})
    assert_email_in_use_shown(response)
    assert Student.objects.count() == 1


def test_fr1_sign_up_accepts_norwegian_letters(client):
    response = client.post(SIGN_UP, {"email": "Øyvind@Eksempel.no", "password": PASSWORD})
    assert response.status_code == 302
    assert Student.objects.get().email == "øyvind@eksempel.no"


def test_fr1_sign_up_with_decomposed_letter_is_stored_composed(client):
    decomposed = "A\u030asa@eksempel.no"  # «Å» as A + combining ring above
    response = client.post(SIGN_UP, {"email": decomposed, "password": PASSWORD})
    assert response.status_code == 302
    assert Student.objects.get().email == "\u00e5sa@eksempel.no"


def test_fr1_password_is_stored_with_slow_salted_hash(client):
    client.post(SIGN_UP, {"email": "ida@example.no", "password": PASSWORD})
    stored = Student.objects.get().password
    assert PASSWORD not in stored
    assert stored.startswith("pbkdf2_sha256$")


# ---- Sign in -------------------------------------------------------------------------


def test_fr1_sign_in_ignores_case_and_spaces_with_norwegian_letters(client, student):
    student("øyvind@eksempel.no")
    response = client.post(SIGN_IN, {"username": " ØYVIND@eksempel.no ", "password": PASSWORD})
    assert response.status_code == 302
    assert response["Location"] == "/"
    assert signed_in_email(client) == "øyvind@eksempel.no"


def test_fr1_wrong_password_shows_wrong_credentials(client, student):
    student("ida@example.no")
    response = client.post(SIGN_IN, {"username": "ida@example.no", "password": "feil-passord-1"})
    assert response.status_code == 200
    content = response.content.decode()
    assert MESSAGES["wrong_credentials"] in content
    assert 'id="form-error"' in content
    assert 'aria-invalid="true"' in content
    assert 'aria-describedby="form-error"' in content
    assert signed_in_email(client) is None


def test_fr1_unknown_email_shows_the_same_message(client):
    response = client.post(SIGN_IN, {"username": "ingen@example.no", "password": PASSWORD})
    assert response.status_code == 200
    assert MESSAGES["wrong_credentials"] in response.content.decode()


def post_with_next(client, view, next_url):
    """Sign in (existing Student) or sign up (new Student) with `next` in query and form."""
    if view == "sign_in":
        Student.objects.create_user("ida@example.no", PASSWORD)
        data = {"username": "ida@example.no", "password": PASSWORD}
    else:
        data = {"email": "ida@example.no", "password": PASSWORD}
    url = reverse(f"accounts:{view}")
    return client.post(f"{url}?{urlencode({'next': next_url})}", {**data, "next": next_url})


@pytest.mark.parametrize("view", ["sign_in", "sign_up"])
def test_fr1_safe_next_is_followed(client, view):
    response = post_with_next(client, view, "/topics/12/?tab=quiz")
    assert response.status_code == 302
    assert response["Location"] == "/topics/12/?tab=quiz"


def test_fr1_p01_carries_next_to_form_and_sign_up_link(client):
    content = client.get(f"{SIGN_IN}?next=/topics/12/").content.decode()
    assert '<input type="hidden" name="next" value="/topics/12/">' in content
    assert f'href="{SIGN_UP}?next=/topics/12/"' in content


@pytest.mark.parametrize(
    "unsafe",
    ["https://evil.example/", "//evil.example/", "http://testserver/", "/\\evil.example", "javascript:alert(1)"],
)
@pytest.mark.parametrize("view", ["sign_in", "sign_up"])
def test_fr1_unsafe_next_lands_home(client, view, unsafe):
    response = post_with_next(client, view, unsafe)
    assert response.status_code == 302
    assert response["Location"] == "/"


@pytest.mark.parametrize("url", [SIGN_IN, SIGN_UP])
def test_fr1_signed_in_visit_to_auth_pages_redirects_home(client, student, url):
    client.force_login(student("ida@example.no"))
    response = client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/"


# ---- Sign-in required ----------------------------------------------------------------


def test_fr1_signed_out_page_redirects_to_sign_in_with_next(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response["Location"] == f"{SIGN_IN}?next=/"


def test_fr1_fresh_visit_shows_p01_with_link_to_p02(client):
    response = client.get("/", follow=True)
    content = response.content.decode()
    assert response.status_code == 200
    assert '<html lang="nb">' in content
    assert "<h1 class=\"auth-title\">Logg inn</h1>" in content
    assert f'href="{SIGN_UP}' in content


def test_fr1_signed_out_htmx_gets_hx_redirect(client):
    response = client.get("/", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert response["HX-Redirect"] == f"{SIGN_IN}?next=/"
    assert response.content == b""


def test_fr1_signed_out_htmx_returns_to_the_page_the_browser_shows(client):
    response = client.get(
        "/",
        headers={"HX-Request": "true", "HX-Current-URL": "http://testserver/topics/3/?tab=quiz"},
    )
    assert response["HX-Redirect"] == f"{SIGN_IN}?next=/topics/3/%3Ftab%3Dquiz"


def test_fr1_signed_out_htmx_ignores_unsafe_current_url(client):
    response = client.get(
        "/", headers={"HX-Request": "true", "HX-Current-URL": "http://testserver//evil.example/"}
    )
    assert response["HX-Redirect"] == f"{SIGN_IN}?next=/"


def test_fr1_auth_pages_are_open_when_signed_out(client):
    assert client.get(SIGN_IN).status_code == 200
    assert client.get(SIGN_UP).status_code == 200


# ---- Sign out ------------------------------------------------------------------------


def test_fr1_sign_out_ends_session_and_lands_on_p01(client, student):
    client.force_login(student("ida@example.no"))
    response = client.post(SIGN_OUT)
    assert response.status_code == 302
    assert response["Location"] == SIGN_IN
    assert client.get("/").status_code == 302


def test_fr1_sign_out_when_already_signed_out_lands_on_p01(client):
    response = client.post(SIGN_OUT)
    assert response.status_code == 302
    assert response["Location"] == SIGN_IN


def test_fr1_sign_out_by_get_is_refused(client, student):
    client.force_login(student("ida@example.no"))
    assert client.get(SIGN_OUT).status_code == 405
    assert signed_in_email(client) == "ida@example.no"


def test_fr1_sign_out_requires_csrf(student):
    client = Client(enforce_csrf_checks=True)
    client.force_login(student("ida@example.no"))
    assert client.post(SIGN_OUT).status_code == 403
    assert signed_in_email(client) == "ida@example.no"

    token = client.get("/").context["csrf_token"]
    response = client.post(SIGN_OUT, {"csrfmiddlewaretoken": str(token)})
    assert response.status_code == 302
    assert signed_in_email(client) is None


def test_fr1_home_shows_signed_in_email_and_sign_out_button(client, student):
    # The email and «Logg ut» live in the account menu D01 (story 3).
    client.force_login(student("ida@example.no"))
    content = client.get("/").content.decode()
    assert 'aria-label="Kontomeny for ida@example.no"' in content
    assert f'action="{SIGN_OUT}"' in content
    assert "Logg ut" in content


# ---- Session -------------------------------------------------------------------------


def test_fr1_session_survives_a_new_client_with_the_same_cookie(client, student):
    student("ida@example.no")
    client.post(SIGN_IN, {"username": "ida@example.no", "password": PASSWORD})
    cookie = client.cookies["sessionid"].value

    other = Client()
    other.cookies["sessionid"] = cookie
    assert signed_in_email(other) == "ida@example.no"
