"""D10 «Øv på svake temaer» (FR-17): which Topics of one Course go into the Quiz."""

import uuid

from django import forms

from core.messages import MESSAGES
from courses.forms import FocusFirstErrorMixin


class LenientTopicsField(forms.TypedMultipleChoiceField):
    """Topic ids not among the choices (another Course, another Student, no ready Questions) are
    dropped instead of rejected; with none left it is the «Velg minst ett tema.» error."""

    def clean(self, value):
        allowed = {str(key) for key, _ in self.choices}
        kept = [v for v in (value or []) if str(v) in allowed]
        return super().clean(kept)


class WeakQuizForm(FocusFirstErrorMixin, forms.Form):
    topics = LenientTopicsField(
        label="Temaer",
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        error_messages={"required": MESSAGES["weak_quiz_topics_required"]},
    )
    start_token = forms.CharField(required=False, max_length=64, widget=forms.HiddenInput)

    def __init__(self, *args, topic_ids: list[int], preselected: list[int], **kwargs):
        kwargs.setdefault("initial", {"topics": preselected, "start_token": uuid.uuid4().hex})
        super().__init__(*args, **kwargs)
        self.fields["topics"].choices = [(topic_id, str(topic_id)) for topic_id in topic_ids]

    def clean_start_token(self) -> str:
        return self.cleaned_data.get("start_token") or uuid.uuid4().hex
