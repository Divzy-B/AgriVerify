import re
from datetime import date

from dateutil import parser


class AmbiguousDateError(ValueError):
    pass


def normalize_confirmed_date(value: str) -> date:
    """Accept an unambiguous confirmed date and reject dates that omit a year."""
    if not re.search(r"\b\d{4}\b", value):
        raise AmbiguousDateError("Please confirm the planting year; dates without a year are ambiguous.")
    try:
        return parser.parse(value, fuzzy=False, dayfirst=False).date()
    except (ValueError, OverflowError) as exc:
        raise AmbiguousDateError("The planting date could not be normalized. Ask for month, day, and year.") from exc

