"""D06 «Start quiz» (FR-10): how many Questions, as a segmented-control of presets."""

import uuid

from django import forms

from core.messages import MESSAGES
from courses.forms import FocusFirstErrorMixin
from studymat.forms import SegmentedRadioSelect

PRESETS = (5, 10, 20)
DEFAULT_COUNT = 10


def preset_choices(available: int) -> list[tuple[int, str]]:
    """«5», «10», «20» below what is available, then «Alle {n}» (EXPERIENCE.md, Few Questions)."""
    return [(n, str(n)) for n in PRESETS if n < available] + [(available, f"Alle {available}")]


def default_count(available: int) -> int:
    return min(DEFAULT_COUNT, available)


class StartQuizForm(FocusFirstErrorMixin, forms.Form):
    """Any count of at least 1 is accepted; quiz.services clamps it to what is available."""

    count = forms.IntegerField(
        label="Antall spørsmål",
        min_value=1,
        error_messages={key: MESSAGES["quiz_count_required"] for key in ("required", "invalid", "min_value")},
    )
    start_token = forms.CharField(required=False, max_length=64, widget=forms.HiddenInput)

    def __init__(self, *args, available: int, **kwargs):
        kwargs.setdefault("initial", {"count": default_count(available), "start_token": uuid.uuid4().hex})
        super().__init__(*args, **kwargs)
        self.fields["count"].widget = SegmentedRadioSelect(choices=preset_choices(available))
        self.fields["count"].initial = default_count(available)

    def clean_start_token(self) -> str:
        return self.cleaned_data.get("start_token") or uuid.uuid4().hex
