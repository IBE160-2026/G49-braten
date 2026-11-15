from django.conf import settings
from django.db import models

from core.ownership import OwnedQuerySet
from courses.models import Source


class LocationKind(models.TextChoices):
    """The shape of a Location (AD-6). Display text lives in templates."""

    PAGE = "page"
    PARAGRAPH = "paragraph"
    HEADING = "heading"


class SourceText(models.Model):
    """The extracted text of one Location in a Source (AD-5 step 1, AD-6).

    A PDF has one `page` row per viewer page, empty pages included; plain and pasted text
    have one `paragraph` row per block. `index` counts from 1 within (source, kind).
    `label` is the Location's own label: the page or paragraph number, or the heading text.
    """

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="source_texts")
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="texts")
    kind = models.CharField(max_length=10, choices=LocationKind.choices)
    index = models.PositiveIntegerField()
    label = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True)

    objects = OwnedQuerySet.as_manager()

    class Meta:
        ordering = ["source", "kind", "index"]
        constraints = [
            models.UniqueConstraint(fields=["source", "kind", "index"], name="sourcetext_unique_location"),
            models.CheckConstraint(condition=models.Q(index__gte=1), name="sourcetext_index_from_1"),
        ]

    def __str__(self) -> str:
        return f"{self.source_id}:{self.kind}:{self.index}"
