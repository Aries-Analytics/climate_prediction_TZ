"""
Shadow Run Configuration — Single Source of Truth

All shadow run parameters live here. Every module that needs start dates,
targets, or run-day counts imports from this file. Zero duplication.

To restart a shadow run with new parameters, change ONLY this file.

Date semantics:
- SHADOW_RUN_START / SHADOW_RUN_END     → TARGET dates (calendar math,
                                            assumes zero gaps).
- projected_end_date(valid_run_days)    → live-computed date that accounts
                                            for any accumulated gaps
                                            (server downtime, etc.).
- The shadow run completes when valid_run_days reaches
  SHADOW_RUN_TARGET_DAYS, NOT when the calendar hits SHADOW_RUN_END.
  Gaps push the actual completion date later — sample size (2,160
  forecasts) is always preserved.
"""
from datetime import date, timedelta

# ── Shadow Run v2: Two-Zone Kilombero Split (restarted Apr 16) ──
# Apr 14-15 runs invalidated — stale ingestion modules stored climate data
# at wrong coordinates. Wiped and restarting from Apr 16.
SHADOW_RUN_START = date(2026, 4, 16)
SHADOW_RUN_TARGET_DAYS = 90
SHADOW_RUN_END = SHADOW_RUN_START + timedelta(days=SHADOW_RUN_TARGET_DAYS - 1)

# Forecast volume: 3 trigger types × 4 horizons × 2 zones = 24/day
FORECASTS_PER_DAY = 24
SHADOW_RUN_TARGET_FORECASTS = SHADOW_RUN_TARGET_DAYS * FORECASTS_PER_DAY


def projected_end_date(valid_run_days: int, today: date | None = None) -> date:
    """
    Live projection of shadow run completion date.

    Formula:
        projected_end = SHADOW_RUN_END + gaps_accumulated_so_far
        gaps = calendar_days_elapsed - valid_run_days

    Where calendar_days_elapsed is inclusive of today and clamped to >= 0
    (before-start returns SHADOW_RUN_END as-is).

    Examples:
        Day 5, zero gaps → valid_run_days=5, gaps=0, projected = SHADOW_RUN_END
        Day 5, skipped Day 3 → valid_run_days=4, gaps=1, projected = SHADOW_RUN_END + 1 day
        Before start → projected = SHADOW_RUN_END

    Args:
        valid_run_days: Count of distinct calendar dates with forecast logs
                        (from DB). Must be >= 0.
        today:          Optional override for the reference date (used in tests).

    Returns:
        Projected completion date (tz-naive).
    """
    if today is None:
        today = date.today()
    if today < SHADOW_RUN_START:
        return SHADOW_RUN_END
    calendar_days_elapsed = (today - SHADOW_RUN_START).days + 1  # inclusive
    gaps = max(0, calendar_days_elapsed - valid_run_days)
    return SHADOW_RUN_END + timedelta(days=gaps)


def projected_brier_eval_date(valid_run_days: int, today: date | None = None) -> date:
    """
    Brier Score evaluation happens ~3 days before the run completes
    (first 3-month-horizon forecasts mature just before the final day).
    Derived from projected_end_date so it adapts to gaps automatically.
    """
    return projected_end_date(valid_run_days, today) - timedelta(days=3)
