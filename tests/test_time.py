import datetime

from core import time

UTC = datetime.UTC


def test_today_is_the_oslo_date_after_utc_evening(freeze_now):
    freeze_now(datetime.datetime(2026, 11, 14, 23, 30, tzinfo=UTC))
    assert time.today() == datetime.date(2026, 11, 15)


def test_today_is_the_same_date_before_oslo_midnight(freeze_now):
    freeze_now(datetime.datetime(2026, 11, 14, 22, 59, tzinfo=UTC))
    assert time.today() == datetime.date(2026, 11, 14)


def test_oslo_summer_time_offset(freeze_now):
    # CEST is UTC+2: 22:30 UTC on 30 June is 00:30 on 1 July in Oslo.
    freeze_now(datetime.datetime(2026, 6, 30, 22, 30, tzinfo=UTC))
    assert time.today() == datetime.date(2026, 7, 1)


def test_now_is_aware():
    assert time.now().tzinfo is not None
