"""P01 and P02 forms (FR-1). Text the Student sees comes from core.messages by code."""

import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.validators import EmailValidator
from django.db import IntegrityError, transaction

from accounts.managers import normalize
from accounts.models import Student
from core.messages import MESSAGES

EMAIL_WIDGET_ATTRS = {
    # type="text", not "email": browsers refuse Æ/Ø/Å before the @ in an email input.
    "inputmode": "email",
    "autocomplete": "email",
    "autocapitalize": "none",
    "spellcheck": "false",
    "class": "text-input",
}


class StudentEmailValidator(EmailValidator):
    """Django's email check, but letters such as Æ, Ø and Å are allowed before the @."""

    user_regex = re.compile(
        r"^[-!#$%&'*+/=?^_`{}|~\w]+(\.[-!#$%&'*+/=?^_`{}|~\w]+)*\Z",
        re.IGNORECASE,
    )


class LinkedErrorsMixin:
    """Links each field to its help text and errors with aria-describedby.

    Help text renders with id "<field id>-help", a field's errors with "<field id>-error",
    and errors for the whole form with NON_FIELD_ERROR_ID, linked from every field.
    """

    NON_FIELD_ERROR_ID = "form-error"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._link_errors()

    def full_clean(self):
        super().full_clean()
        self._link_errors()

    def _link_errors(self):
        errors = self._errors or {}
        whole_form = NON_FIELD_ERRORS in errors
        for name, field in self.fields.items():
            ids = []
            if field.help_text:
                ids.append(f"{self[name].auto_id}-help")
            if whole_form:
                ids.append(self.NON_FIELD_ERROR_ID)
            if name in errors:
                ids.append(f"{self[name].auto_id}-error")
            if whole_form or name in errors:
                field.widget.attrs["aria-invalid"] = "true"
            if ids:
                field.widget.attrs["aria-describedby"] = " ".join(ids)


class SignInForm(LinkedErrorsMixin, AuthenticationForm):
    """AuthenticationForm with the email normalised and the wrong-credentials text by code."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": MESSAGES["wrong_credentials"],
        "inactive": MESSAGES["wrong_credentials"],
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        username = self.fields["username"]
        username.label = "E-post"
        username.widget.input_type = "text"
        username.widget.attrs.update(EMAIL_WIDGET_ATTRS)
        password = self.fields["password"]
        password.label = "Passord"
        password.widget.attrs.update({"autocomplete": "current-password", "class": "text-input"})

    def clean_username(self):
        return normalize(self.cleaned_data.get("username"))


class SignUpForm(LinkedErrorsMixin, forms.Form):
    """Email and one password. The duplicate check ignores case, like the database constraint."""

    email = forms.CharField(
        label="E-post",
        max_length=254,
        widget=forms.TextInput(attrs={**EMAIL_WIDGET_ATTRS, "autofocus": True}),
    )
    password = forms.CharField(
        label="Passord",
        strip=False,
        help_text="Minst 8 tegn, og ikke et vanlig passord.",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "text-input"}),
    )

    def clean_email(self):
        email = normalize(self.cleaned_data.get("email"))
        # Validated after normalising, so a decomposed Å (A + combining ring) passes.
        StudentEmailValidator()(email)
        if Student.objects.filter(email=email).exists():
            raise forms.ValidationError(MESSAGES["email_in_use"], code="email_in_use")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        email = normalize(self.data.get(self.add_prefix("email")))
        validate_password(password, user=Student(email=email))
        return password

    @property
    def email_in_use(self) -> bool:
        return self.has_error("email", code="email_in_use")

    def save(self) -> Student | None:
        """The new Student, or None when another request took the email first."""
        try:
            with transaction.atomic():
                return Student.objects.create_user(
                    self.cleaned_data["email"], self.cleaned_data["password"]
                )
        except IntegrityError:
            self.add_error(
                "email", forms.ValidationError(MESSAGES["email_in_use"], code="email_in_use")
            )
            self._link_errors()
            return None
