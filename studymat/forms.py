"""D05 «Legg til kilde» (FR-3). Error text comes from core.messages by code."""

from django import forms

from core.messages import MESSAGES
from courses.forms import FocusFirstErrorMixin
from courses.models import NAME_MAX_LENGTH, DetailLevel

# Display text for the Detail level segmented-control (EXPERIENCE.md glossary).
DETAIL_LEVEL_CHOICES = [
    (DetailLevel.SHORT, "Kortfattet"),
    (DetailLevel.MEDIUM, "Middels"),
    (DetailLevel.DETAILED, "Detaljert"),
]


class SegmentedRadioSelect(forms.RadioSelect):
    """Radios for components/segmented_control.html.

    The fieldset carries `aria-describedby`, and only the first radio takes `autofocus`
    (FocusFirstErrorMixin sets it on the widget, which would put it on every option).
    """

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        option["attrs"].pop("aria-describedby", None)
        if index:
            option["attrs"].pop("autofocus", None)
        return option


class AddSourceForm(FocusFirstErrorMixin, forms.Form):
    """A file or pasted text (exactly one), an optional name for pasted text, and the Detail level."""

    file = forms.FileField(
        label="Velg fil",
        required=False,
        error_messages={"empty": MESSAGES["empty_file"], "invalid": MESSAGES["unsupported_type"]},
        widget=forms.FileInput(attrs={"class": "file-input", "accept": ".pdf,.txt,application/pdf,text/plain"}),
    )
    text = forms.CharField(
        label="Lim inn tekst",
        required=False,
        strip=False,
        error_messages={"null_characters_not_allowed": MESSAGES["null_characters"]},
        widget=forms.Textarea(attrs={"class": "text-input text-area", "rows": 6}),
    )
    name = forms.CharField(
        label="Navn på teksten (valgfritt)",
        required=False,
        max_length=NAME_MAX_LENGTH,
        help_text="Gjelder bare innlimt tekst.",
        error_messages={
            "max_length": MESSAGES["pasted_name_too_long"],
            "null_characters_not_allowed": MESSAGES["null_characters"],
        },
        widget=forms.TextInput(
            attrs={
                "class": "text-input",
                "maxlength": NAME_MAX_LENGTH,
                "autocomplete": "off",
                "placeholder": MESSAGES["pasted_default_name"],
            }
        ),
    )
    detail_level = forms.ChoiceField(
        label="Detaljnivå",
        choices=DETAIL_LEVEL_CHOICES,
        initial=DetailLevel.MEDIUM,
        help_text="Gjelder sammendraget. Du kan bytte detaljnivå senere.",
        error_messages={
            "required": MESSAGES["detail_level_required"],
            "invalid_choice": MESSAGES["detail_level_required"],
        },
        widget=SegmentedRadioSelect,
    )

    def clean(self):
        cleaned = super().clean()
        has_file = bool(cleaned.get("file"))
        has_text = bool((cleaned.get("text") or "").strip())
        if has_file and has_text:
            self.add_error("file", forms.ValidationError(MESSAGES["file_or_text"], code="file_or_text"))
        elif not has_file and not has_text and "file" not in self.errors:
            self.add_error("text", forms.ValidationError(MESSAGES["paste_empty"], code="paste_empty"))
        return cleaned

    def reject(self, error) -> str:
        """Mark the input an IngestError is about: the file when one was sent, else the text.

        Returns that field's name.
        """
        field = "file" if self.cleaned_data.get("file") else "text"
        attrs = self.fields[field].widget.attrs
        attrs["aria-invalid"] = "true"
        attrs["aria-describedby"] = "upload-error"
        attrs["autofocus"] = True
        return field
