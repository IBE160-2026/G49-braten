"""`Scope` (AD-1): the one scope type used by `review`, `progress` and `web`.

All fag, one fag (`course_id`) or one tema (`topic_id`). It never checks ownership: callers load
the Course or Topic through `get_owned_or_404` first, and filter querysets that are already the
Student's.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scope:
    course_id: int | None = None
    topic_id: int | None = None

    def __post_init__(self):
        if self.course_id is not None and self.topic_id is not None:
            raise ValueError("A Scope is all, one course or one topic, never both.")

    @classmethod
    def all(cls) -> "Scope":
        return cls()

    @property
    def is_all(self) -> bool:
        return self.course_id is None and self.topic_id is None

    def filter(self, queryset, topic_path: str):
        """`queryset` narrowed to this scope; `topic_path` is the lookup from its model to Topic,
        e.g. "source__topic" for a Flashcard or "flashcard__source__topic" for a ReviewState."""
        if self.topic_id is not None:
            return queryset.filter(**{f"{topic_path}_id": self.topic_id})
        if self.course_id is not None:
            return queryset.filter(**{f"{topic_path}__course_id": self.course_id})
        return queryset
