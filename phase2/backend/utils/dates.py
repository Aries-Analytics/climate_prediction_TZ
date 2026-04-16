"""
Date / Timezone Contract — Ingestion Layer

====================================================================
  ALL INGESTION CODE WORKS IN TZ-NAIVE `date` OBJECTS. ALWAYS.
====================================================================

Rationale
---------
Data sources publish at monthly granularity. Our database stores
`date` columns (not `datetime`). Pandas filters are tz-naive by default.
Mixing tz-aware and tz-naive values at comparison sites has caused
four production bugs (Apr 6, 7, 9, 16 of 2026) — each a local patch
that didn't eliminate the underlying inconsistency.

Convention
----------
• `start_date` and `end_date` parameters → always `datetime.date`
• Defaults when caller passes None  → `date(2010, 1, 1)` / `date.today()`
• Internal month math               → `date` arithmetic, never datetime
• Pandas filter bounds              → `pd.Timestamp` (tz-naive)
• NO `datetime.now(timezone.utc)` anywhere in ingestion modules
• NO `tz_localize` / `replace(tzinfo=...)` patches — unnecessary once
  the contract is clean

Helpers
-------
`as_date(x)`           → coerce anything (date, datetime, Timestamp,
                         str ISO, None) to tz-naive `date`
`last_complete_month`  → last day of the previous calendar month,
                         as tz-naive `date`
`month_start`          → first day of month containing the input
                         date, as tz-naive `date`

Law #1 (explicit failure): as_date() raises TypeError on unrecognised
input — never silently returns a sentinel.
"""
from datetime import date, datetime, timedelta
from typing import Optional, Union

import pandas as pd


DateInput = Union[date, datetime, pd.Timestamp, str, None]


def as_date(x: DateInput, default: Optional[date] = None) -> date:
    """
    Coerce any date-like input to a tz-naive `datetime.date`.

    Parameters
    ----------
    x : date | datetime | Timestamp | str | None
        Value to coerce.
    default : date, optional
        Returned when `x is None`. If None, raises ValueError.

    Returns
    -------
    datetime.date
        Tz-naive date object.

    Raises
    ------
    TypeError  — unrecognised input type (Law #1: explicit failure)
    ValueError — x is None and no default provided
    """
    if x is None:
        if default is None:
            raise ValueError("as_date(None) requires a default")
        return default
    if isinstance(x, datetime):
        # strip tz first if present, then take .date()
        return x.date()
    if isinstance(x, date):
        return x
    if isinstance(x, pd.Timestamp):
        # pd.Timestamp.tz_convert(None) raises if tz-naive; use tz_localize(None) if aware
        if x.tzinfo is not None:
            x = x.tz_localize(None)
        return x.date()
    if isinstance(x, str):
        return datetime.fromisoformat(x).date()
    raise TypeError(f"as_date: cannot coerce {type(x).__name__} to date")


def last_complete_month(reference: Optional[date] = None) -> date:
    """
    Return the last day of the last COMPLETE calendar month.

    Used by ingestion modules to avoid fetching partial-month data
    (current month has only N days, aggregates produce NaN/bias).

    Parameters
    ----------
    reference : date, optional
        Reference date; defaults to today.

    Returns
    -------
    datetime.date
        Last day of the previous calendar month.
    """
    ref = reference if reference is not None else date.today()
    return date(ref.year, ref.month, 1) - timedelta(days=1)


def month_start(d: date) -> date:
    """Return the first day of the calendar month containing `d`."""
    return date(d.year, d.month, 1)


def subtract_months(d: date, months: int) -> date:
    """
    Return `d` shifted back by `months` calendar months (same day of month,
    clamped to month end if necessary). Used for ERA5 lag-month calculation.
    """
    total = d.year * 12 + (d.month - 1) - months
    year = total // 12
    month = total % 12 + 1
    # Clamp day to last day of target month
    last = (date(year + (month == 12), (month % 12) + 1, 1) - timedelta(days=1)).day
    day = min(d.day, last)
    return date(year, month, day)
