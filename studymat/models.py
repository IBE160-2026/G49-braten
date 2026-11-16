"""Study material for one Source (FR-7, AD-9): written only by studymat.services.

Every item is owned (`student`, AD-7), goes with its Source by cascade (AD-8) and carries its
Reference (`location_index` + `quote`, AD-6).
"""

from django.conf import settings
from django.db import models

from core.ownership import OwnedQuerySet
from courses.models import DetailLevel, Source


class QuestionKind(models.TextChoices):
    MULTIPLE_CHOICE = "multiple_choice"
    FREE_TEXT = "free_text"


class Item(models.Model):
    """Owner, Source and Reference, shared by every generated item."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    location_index = models.PositiveIntegerField()
    quote = models.TextField()

    objects = OwnedQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ["source", "id"]


class Summary(models.Model):
    """The one Summary of a Source, at its current Detail level (FR-7)."""

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="summaries")
    source = models.OneToOneField(Source, on_delete=models.CASCADE, related_name="summary")
    text = models.TextField()
    detail_level = models.CharField(max_length=10, choices=DetailLevel.choices)

    objects = OwnedQuerySet.as_manager()

    def __str__(self) -> str:
        return f"Summary of {self.source_id}"


class KeyConcept(Item):
    term = models.CharField(max_length=200)
    definition = models.TextField()

    class Meta(Item.Meta):
        default_related_name = "key_concepts"

    def __str__(self) -> str:
        return self.term


class Flashcard(Item):
    front = models.TextField()
    back = models.TextField()

    class Meta(Item.Meta):
        default_related_name = "flashcards"

    def __str__(self) -> str:
        return self.front[:60]


class Question(Item):
    """AD-9: `options` is four `{text, explanation}` for multiple_choice and `[]` for free_text."""

    kind = models.CharField(max_length=16, choices=QuestionKind.choices)
    prompt = models.TextField()
    hint = models.TextField()
    options = models.JSONField(default=list, blank=True)
    correct_index = models.PositiveSmallIntegerField(null=True, blank=True)
    model_answer = models.TextField(blank=True)

    class Meta(Item.Meta):
        default_related_name = "questions"

    def __str__(self) -> str:
        return self.prompt[:60]
