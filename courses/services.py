"""Writes to Course (AD-1: only courses.services writes courses' tables)."""

from courses.models import Course


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
