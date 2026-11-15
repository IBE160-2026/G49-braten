"""D02 «Nytt fag» and D08 «Gi nytt navn» (FR-2). Error text comes from core.messages by code."""

from django import forms

from accounts.forms import LinkedErrorsMixin
from core.messages import MESSAGES
from courses.models import CODE_MAX_LENGTH, NAME_MAX_LENGTH


def name_field(**widget_attrs):
    return forms.CharField(
        label="Navn",
        max_length=NAME_MAX_LENGTH,
        error_messages={
            "required": MESSAGES["course_name_required"],
            "max_length": MESSAGES["course_name_too_long"],
        },
        widget=forms.TextInput(
            attrs={"class": "text-input", "maxlength": NAME_MAX_LENGTH, "autocomplete": "off", **widget_attrs}
        ),
    )


class FocusFirstErrorMixin(LinkedErrorsMixin):
    """After a failed submit, the first field with an error gets `autofocus` (AD-18)."""

    def full_clean(self):
        super().full_clean()
        for name in self.fields:
            if name in (self._errors or {}):
                self.fields[name].widget.attrs["autofocus"] = True
                break


class CourseForm(FocusFirstErrorMixin, forms.Form):
    name = name_field()
    code = forms.CharField(
        label="Kurskode (valgfritt)",
        required=False,
        max_length=CODE_MAX_LENGTH,
        help_text="Vises ved siden av navnet.",
        error_messages={"max_length": MESSAGES["course_code_too_long"]},
        widget=forms.TextInput(
            attrs={"class": "text-input", "maxlength": CODE_MAX_LENGTH, "autocomplete": "off"}
        ),
    )


class RenameCourseForm(FocusFirstErrorMixin, forms.Form):
    name = name_field()
