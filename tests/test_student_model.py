import datetime

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError

from accounts.models import Student

pytestmark = pytest.mark.django_db


def test_student_is_the_user_model():
    assert get_user_model() is Student


def test_email_is_lower_cased_on_save():
    student = Student.objects.create_user("Ida@Example.no", "a-long-password")
    student.refresh_from_db()
    assert student.email == "ida@example.no"


def test_second_account_differing_only_by_case_is_rejected():
    Student.objects.create_user("Ida@Example.no", "a-long-password")
    with pytest.raises(IntegrityError):
        Student.objects.create_user("IDA@example.no", "another-password")


def test_case_insensitive_constraint_holds_without_save():
    Student.objects.create_user("ida@example.no", "a-long-password")
    with pytest.raises(IntegrityError):
        Student.objects.bulk_create([Student(email="IDA@EXAMPLE.NO", password="x")])


def test_sign_in_lookup_ignores_case():
    Student.objects.create_user("ida@example.no", "a-long-password")
    assert authenticate(username="IDA@Example.NO", password="a-long-password") is not None


def test_password_is_stored_as_a_hash():
    student = Student.objects.create_user("ida@example.no", "a-long-password")
    assert student.password != "a-long-password"
    assert student.check_password("a-long-password")


def test_privacy_not_accepted_by_default():
    student = Student.objects.create_user("ida@example.no", "a-long-password")
    assert student.privacy_accepted_at is None


def test_sign_in_with_non_ascii_letters_ignores_case():
    Student.objects.create_user("Øyvind@Example.no", "a-long-password")
    assert authenticate(username="ØYVIND@example.no", password="a-long-password") is not None


def test_sign_in_ignores_surrounding_whitespace():
    Student.objects.create_user("ida@example.no", "a-long-password")
    assert authenticate(username="  ida@example.no ", password="a-long-password") is not None


def test_blank_email_is_refused():
    with pytest.raises(ValueError):
        Student.objects.create_user("   ", "a-long-password")


def test_date_joined_follows_frozen_time(freeze_now):
    moment = datetime.datetime(2026, 11, 14, 12, 0, tzinfo=datetime.UTC)
    freeze_now(moment)
    assert Student.objects.create_user("ida@example.no", "a-long-password").date_joined == moment
