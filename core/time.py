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


# Short month names in bokmål, for «18. nov.» (EXPERIENCE.md, Voice and Tone: the short form in tables).
SHORT_MONTHS = ("jan.", "feb.", "mar.", "apr.", "mai", "jun.", "jul.", "aug.", "sep.", "okt.", "nov.", "des.")


def short_date(moment: datetime.datetime | datetime.date) -> str:
    """«18. nov.»: the Oslo date of `moment` (an aware datetime, or a date)."""
    if isinstance(moment, datetime.datetime):
        moment = moment.astimezone(OSLO).date()
    return f"{moment.day}. {SHORT_MONTHS[moment.month - 1]}"
