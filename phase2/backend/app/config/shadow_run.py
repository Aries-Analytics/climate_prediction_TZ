"""
Shadow Run Configuration — Single Source of Truth

All shadow run parameters live here. Every module that needs start dates,
targets, or run-day counts imports from this file. Zero duplication.

To restart a shadow run with new parameters, change ONLY this file.
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
