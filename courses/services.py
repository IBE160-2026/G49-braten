"""Writes to Course, Topic and Source (AD-1: only courses.services writes courses' tables).

Every owned row gets its `student` from its parent, set explicitly here (AD-7).
"""

from core import time
from courses.models import Course, DetailLevel, FailureReason, Source, SourceKind, Status, Topic


def create_course(student, name: str, code: str = "") -> Course:
    """A new Course owned by `student`, set explicitly (AD-7)."""
    return Course.objects.create(student=student, name=name, code=code)


def rename_course(course: Course, name: str) -> Course:
    course.name = name
    course.save(update_fields=["name"])
    return course


def delete_course(course: Course) -> None:
    """Hard delete; everything under the Course goes with it by cascade (AD-8)."""
    course.delete()


def create_topic(course: Course, name: str) -> Topic:
    """A new Topic in `course`, owned by the Course's Student (AD-7)."""
    return Topic.objects.create(student_id=course.student_id, course=course, name=name)


def rename_topic(topic: Topic, name: str) -> Topic:
    topic.name = name
    topic.save(update_fields=["name"])
    return topic


def delete_topic(topic: Topic) -> None:
    """Hard delete; its Sources and everything under them go by cascade (AD-8)."""
    topic.delete()


def create_source(
    topic: Topic,
    name: str,
    kind: str,
    size_bytes: int = 0,
    content_sha256: str = "",
    detail_level: str = DetailLevel.MEDIUM,
) -> Source:
    """A new `pending` Source in `topic`, owned by the Topic's Student (AD-7).

    Called by ingestion.services.ingest() inside its transaction (AD-5 step 1).
    """
    assert kind in SourceKind.values, kind
    assert detail_level in DetailLevel.values, detail_level
    return Source.objects.create(
        student_id=topic.student_id,
        topic=topic,
        name=name,
        kind=kind,
        size_bytes=size_bytes,
        content_sha256=content_sha256,
        detail_level=detail_level,
        started_at=time.now(),
    )


# ---- Generation lifecycle (AD-5): only these change Source status -------------------------


def claim(source: Source):
    """Claim `source` for one generation run, or None when it is not claimable (AD-5).

    One conditional UPDATE over `claimable()` that sets `generating`, a fresh `started_at` (the run
    token, returned) and clears `failure_reason`. Run it outside a transaction so it commits at
    once and a second tab or reload sees it (AD-19).
    """
    token = time.now()
    claimed = (
        Source.objects.claimable()
        .filter(pk=source.pk)
        .update(status=Status.GENERATING, started_at=token, failure_reason="")
    )
    if not claimed:
        return None
    source.status, source.started_at, source.failure_reason = Status.GENERATING, token, ""
    return token


def _run(source: Source, token):
    return Source.objects.filter(pk=source.pk, status=Status.GENERATING, started_at=token)


def mark_ready(source: Source, token, language: str, removed: int, dropped: int) -> bool:
    """`ready` with the run's counts, only while the run with `token` still owns the Source."""
    matched = _run(source, token).update(
        status=Status.READY, failure_reason="", language=language, removed_count=removed, dropped_count=dropped
    )
    if matched:
        source.status, source.failure_reason = Status.READY, ""
        source.language, source.removed_count, source.dropped_count = language, removed, dropped
    return bool(matched)


def mark_failed(source: Source, token, reason: str) -> bool:
    """`failed` with `reason` (a FailureReason), only while the run with `token` owns the Source."""
    assert reason in FailureReason.values, reason
    matched = _run(source, token).update(status=Status.FAILED, failure_reason=reason)
    if matched:
        source.status, source.failure_reason = Status.FAILED, reason
    return bool(matched)


def rename_source(source: Source, name: str) -> Source:
    source.name = name
    source.save(update_fields=["name"])
    return source


def delete_source(source: Source) -> None:
    """Hard delete; its Study material and the answers on it go by cascade (AD-8)."""
    source.delete()


def course_delete_counts(course: Course) -> tuple[int, int]:
    """(Topics, Sources) that go with `course`, for D09."""
    topics = Topic.objects.filter(course=course).count()
    sources = Source.objects.filter(topic__course=course).count()
    return topics, sources


def topic_delete_count(topic: Topic) -> int:
    """Sources that go with `topic`, for D09."""
    return Source.objects.filter(topic=topic).count()
