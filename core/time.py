"""The one source of "now" and "today" (AD-12).

Datetimes are stored in UTC; days are counted in Oslo. Tests freeze both by
patching `now`, since `today` is derived from it.
"""

import datetime
from zoneinfo import ZoneInfo

from django.utils import timezone

OSLO = ZoneInfo("Europe/Oslo")


def now() -> datetime.datetime:
    """The current moment as an aware datetime."""
    return timezone.now()


def today() -> datetime.date:
    """Today's date in Oslo."""
    return now().astimezone(OSLO).date()
