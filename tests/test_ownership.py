"""AD-7: owned rows load only for their Student; anything else is a 404."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import Http404

from core.ownership import get_owned_or_404
from tests.ownership_app.models import Note

pytestmark = pytest.mark.django_db


@pytest.fixture
def two_students(student):
    return student("a@example.no"), student("b@example.no")


def test_fr1_for_student_returns_only_own_rows(two_students):
    a, b = two_students
    mine = Note.objects.create(student=a, title="A")
    Note.objects.create(student=b, title="B")
    assert list(Note.objects.for_student(a)) == [mine]


def test_fr1_get_owned_returns_own_row(two_students):
    a, _ = two_students
    note = Note.objects.create(student=a, title="A")
    assert get_owned_or_404(Note, a, pk=note.pk) == note


def test_fr1_not_owned_is_404_like_missing(two_students):
    a, b = two_students
    other = Note.objects.create(student=b, title="B")
    with pytest.raises(Http404):
        get_owned_or_404(Note, a, pk=other.pk)
    with pytest.raises(Http404):
        get_owned_or_404(Note, a, pk=other.pk + 1000)


def test_fr1_get_owned_accepts_a_queryset(two_students):
    a, b = two_students
    note = Note.objects.create(student=a, title="A")
    other = Note.objects.create(student=b, title="A")
    queryset = Note.objects.filter(title="A")
    assert get_owned_or_404(queryset, a, pk=note.pk) == note
    with pytest.raises(Http404):
        get_owned_or_404(queryset, a, pk=other.pk)


def test_fr1_queryset_cannot_widen_past_the_student(two_students):
    """Even an unscoped queryset passed in is narrowed to the Student."""
    a, b = two_students
    Note.objects.create(student=b, title="B")
    with pytest.raises(Http404):
        get_owned_or_404(Note.objects.all(), a, title="B")


def test_fr1_anonymous_gets_404():
    with pytest.raises(Http404):
        get_owned_or_404(Note, AnonymousUser(), pk=1)
