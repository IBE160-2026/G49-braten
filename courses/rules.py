"""Pure functions for courses: the D09 texts that name what goes (FR-2).

Only the counting, plural choice and zero-omission live here; the words are in core.messages.
"""

from core.messages import MESSAGES


def counted(n: int, noun: str) -> str:
    """`noun` is "topic" or "source"; picks the singular or plural entry for `n`."""
    return MESSAGES[f"delete_count_{noun}_{'one' if n == 1 else 'other'}"].format(n=n)


def _lead(parts: list[str]) -> str:
    """«4 temaer, 7 kilder og alle svar slettes. Dette kan ikke angres.»; zero counts are left out."""
    if not parts:
        return MESSAGES["delete_cannot_undo"]
    return f"{MESSAGES['delete_lead_counted'].format(items=', '.join(parts))} {MESSAGES['delete_cannot_undo']}"


def course_delete_lead(topics: int, sources: int) -> str:
    parts = []
    if topics:
        parts.append(counted(topics, "topic"))
    if sources:
        parts.append(counted(sources, "source"))
    return _lead(parts)


def topic_delete_lead(sources: int) -> str:
    return _lead([counted(sources, "source")] if sources else [])


def source_delete_lead() -> str:
    return f"{MESSAGES['delete_lead_source']} {MESSAGES['delete_cannot_undo']}"
