

"""
Shared time utilities for NY-day alignment and timestamp/block interactions.

These functions unify the day-boundary conventions used in both liquidation
and TVL pipelines. All day definitions are based on the same rules used in:

    liqs_to_daily_usd.py

Specifically:
- Days are based on the America/New_York calendar.
- Liquidity/tvl snapshots can align to NY midnight boundaries.
- Liquidations group by NY date via to_date_ny(timestamp).

This module provides:
    * to_dt(ts): convert unix ts → aware UTC datetime
    * to_date_ny(ts): convert ts → YYYY-MM-DD in NY calendar
    * ny_date_to_utc_window(date_str): NY midnight → UTC timestamps
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
import pytz

NY_TZ = pytz.timezone("America/New_York")


def to_dt(ts: int) -> datetime:
    """
    Convert a unix timestamp to an aware UTC datetime.
    Behavior mirrors liquidation utilities.
    """
    return datetime.fromtimestamp(int(ts), tz=timezone.utc)


def to_date_ny(ts: int) -> str:
    """
    Convert a unix timestamp to a NY-calendar date (YYYY-MM-DD).
    This is exactly the day-bucketing definition used in liquidations.
    """
    return to_dt(ts).astimezone(NY_TZ).date().isoformat()


def ny_date_to_utc_window(date_str: str) -> tuple[int, int]:
    """
    Given a NY date string 'YYYY-MM-DD', return a pair of UTC timestamps:

        (ts_start_utc, ts_end_utc)

    where:
      ts_start_utc = NY midnight at start of that date
      ts_end_utc   = NY midnight at start of next date

    This will be used to anchor daily TVL sampling blocks:
    - daily snapshot target will be near ts_end_utc
    - block_for_ts(ts_end_utc) will produce a block whose timestamp >= ts_end_utc
    """
    d = datetime.fromisoformat(date_str).date()

    # NY midnight start of day
    start_ny = NY_TZ.localize(datetime(d.year, d.month, d.day, 0, 0, 0))
    end_ny = start_ny + timedelta(days=1)

    ts_start_utc = int(start_ny.astimezone(timezone.utc).timestamp())
    ts_end_utc = int(end_ny.astimezone(timezone.utc).timestamp())
    return ts_start_utc, ts_end_utc