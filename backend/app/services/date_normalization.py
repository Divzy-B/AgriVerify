import re
from datetime import date

from dateutil import parser

_NUMERIC = re.compile(r"^\s*(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})\s*$")


class AmbiguousDateError(ValueError):
    pass


def normalize_confirmed_date(value: str) -> date:
    """Accept an unambiguous confirmed date and reject dates that omit a year or could be read two ways."""
    if not re.search(r"\b\d{4}\b", value):
        raise AmbiguousDateError("Please confirm the planting year; dates without a year are ambiguous.")
    numeric = _NUMERIC.match(value)
    if numeric and int(numeric[1]) <= 12 and int(numeric[2]) <= 12 and numeric[1] != numeric[2]:
        # 05/06/2025 is 6 May in the US and 5 June in India; do not guess
        raise AmbiguousDateError("That date could be day/month or month/day. Please give the month by name, for example 25 May 2025.")
    try:
        return parser.parse(value, fuzzy=False, dayfirst=False).date()
    except (ValueError, OverflowError) as exc:
        raise AmbiguousDateError("The planting date could not be normalized. Ask for month, day, and year.") from exc
