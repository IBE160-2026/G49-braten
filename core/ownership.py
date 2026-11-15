"""Ownership (AD-7): every owned row has a `student`, and anything not the Student's is a 404.

`core` imports no app (AD-1), so this works on any model with a `student` field.
"""

from django.db import models
from django.http import Http404


class OwnedQuerySet(models.QuerySet):
    """Use as `objects = OwnedQuerySet.as_manager()` on every Student-owned model."""

    def for_student(self, student):
        return self.filter(student=student)


def get_owned_or_404(model_or_queryset, student, **lookup):
    """The row matching `lookup` that belongs to `student`, or `Http404`.

    Missing and not-owned answer the same way, so a request reveals nothing about
    other Students' data.
    """
    if student is None or not getattr(student, "is_authenticated", False):
        raise Http404
    if isinstance(model_or_queryset, models.QuerySet):
        queryset = model_or_queryset
    else:
        queryset = model_or_queryset._default_manager.all()
    try:
        return queryset.filter(student=student).get(**lookup)
    except queryset.model.DoesNotExist:
        raise Http404 from None
