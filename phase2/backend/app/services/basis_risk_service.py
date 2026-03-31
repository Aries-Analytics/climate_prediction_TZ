"""
NDVI Proxy Basis Risk Service

Computes an indicative basis risk percentage from the shadow run data by
correlating primary-tier model triggers with satellite vegetation anomalies.

Definition used here:
  Basis risk (proxy) = uncorroborated primary triggers / total primary triggers

A primary-tier trigger is a ForecastLog row where:
  - forecast_type is drought or crop_failure (NDVI-relevant perils only)
  - forecast_value >= 0.75  (primary tier confidence threshold)
  - lead_time_days <= 120   (≤ 4 months = primary / payout-eligible tier)
  - status = 'evaluated'    (validity window has closed — outcome is known)

A trigger is corroborated when the NDVI anomaly for the same calendar month
(year + month of issued_at) is < NDVI_CORROBORATION_THRESHOLD (default -0.05),
indicating below-normal vegetation stress consistent with drought or crop failure.

Important limitations (surfaced in the report):
  - Flood forecasts are excluded — NDVI does not reliably capture flood events.
  - NDVI is a monthly composite proxy; it reflects area-wide vegetation, not
    individual farm yield. This is an indicative estimate, not ground truth.
  - Months with no NDVI observation are excluded from the denominator so data
    gaps do not artificially inflate the basis risk percentage.
  - A full harvest survey (30-50 farmers, Jun 2026) is needed for a verified number.
"""
import logging
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from app.models.forecast_log import ForecastLog
from app.models.ndvi_observation import NdviObservation

logger = logging.getLogger(__name__)

# Primary tier confidence threshold (must match pitch deck and tier system)
PRIMARY_TIER_THRESHOLD = 0.75

# Maximum lead time for primary (payout-eligible) tier in days (4 months ≈ 120 days)
PRIMARY_TIER_MAX_LEAD_DAYS = 120

# NDVI anomaly below which a month is considered vegetation-stressed (corroborates trigger)
NDVI_CORROBORATION_THRESHOLD = -0.05

# Perils for which NDVI is a valid corroboration signal
NDVI_RELEVANT_TYPES = {"drought", "crop_failure"}

# Perils explicitly excluded with reason surfaced in report
NDVI_EXCLUDED_TYPES = {"flood", "heat_stress"}


def compute_ndvi_proxy_basis_risk(db: Session) -> dict:
    """
    Compute the NDVI proxy basis risk from evaluated primary-tier forecast logs.

    Joins forecast_logs with ndvi_observations on calendar month (year + month
    of issued_at vs observed_date). Only evaluated forecasts with closed validity
    windows are included — pending forecasts are excluded because we don't yet
    know their outcome.

    Returns a dict with:
        proxy_basis_risk_pct  : float | None   — % of uncorroborated triggers
        gate_pass             : bool | None    — True if < 30%, None if insufficient data
        total_primary         : int            — primary-tier triggers in scope
        corroborated          : int            — triggers with NDVI agreement
        uncorroborated        : int            — triggers without NDVI agreement
        no_ndvi_data          : int            — triggers where no NDVI obs exists
        excluded_flood        : int            — flood triggers excluded from scope
        month_breakdown       : list[dict]     — per-month detail
        methodology_note      : str            — plain-language caveat for report
    """
    result_template = {
        "proxy_basis_risk_pct": None,
        "gate_pass": None,
        "total_primary": 0,
        "corroborated": 0,
        "uncorroborated": 0,
        "no_ndvi_data": 0,
        "excluded_flood": 0,
        "month_breakdown": [],
        "methodology_note": (
            "Basis risk estimated from NDVI proxy (MODIS MOD13A2, Kilombero Basin). "
            "A primary-tier trigger (drought/crop_failure, ≥75% confidence, ≤4mo horizon) "
            "is corroborated when the monthly NDVI anomaly is < -0.05 (below-normal "
            "vegetation). Flood forecasts excluded — NDVI does not reliably capture flood "
            "events. Months with no satellite composite excluded from denominator. "
            "This is an indicative proxy estimate; a harvest survey is required for "
            "verified ground truth."
        ),
    }

    try:
        # ── Step 1: fetch all evaluated primary-tier NDVI-relevant triggers ──
        primary_triggers = (
            db.query(ForecastLog)
            .filter(
                ForecastLog.status == "evaluated",
                ForecastLog.forecast_type.in_(NDVI_RELEVANT_TYPES),
                ForecastLog.forecast_value >= PRIMARY_TIER_THRESHOLD,
                ForecastLog.lead_time_days <= PRIMARY_TIER_MAX_LEAD_DAYS,
            )
            .order_by(ForecastLog.issued_at)
            .all()
        )

        # Count excluded flood triggers for transparency
        excluded_flood = (
            db.query(func.count(ForecastLog.id))
            .filter(
                ForecastLog.status == "evaluated",
                ForecastLog.forecast_type == "flood",
                ForecastLog.forecast_value >= PRIMARY_TIER_THRESHOLD,
                ForecastLog.lead_time_days <= PRIMARY_TIER_MAX_LEAD_DAYS,
            )
            .scalar() or 0
        )

        result_template["excluded_flood"] = excluded_flood

        if not primary_triggers:
            logger.info("Basis risk: no evaluated primary-tier triggers found yet")
            result_template["methodology_note"] = (
                "No evaluated primary-tier forecasts available yet. "
                "Basis risk will be computed once forecast validity windows close "
                "(first 3-month forecasts mature ~June 9, 2026)."
            )
            return result_template

        # ── Step 2: load all NDVI observations keyed by (year, month) ──
        ndvi_obs = db.query(NdviObservation).all()
        # Key: (year, month) → NdviObservation with the lowest run_date for that month
        # (all rows for the same month share the same composite value, so any row works)
        ndvi_by_month: dict[tuple, NdviObservation] = {}
        for obs in ndvi_obs:
            key = (obs.observed_date.year, obs.observed_date.month)
            if key not in ndvi_by_month:
                ndvi_by_month[key] = obs

        # ── Step 3: correlate triggers with NDVI by month ──
        # Group triggers by calendar month for the per-month breakdown
        month_groups: dict[tuple, list] = {}
        for log in primary_triggers:
            issued_month = log.issued_at.date() if hasattr(log.issued_at, "date") else log.issued_at
            key = (issued_month.year, issued_month.month)
            month_groups.setdefault(key, []).append(log)

        corroborated   = 0
        uncorroborated = 0
        no_ndvi_data   = 0
        month_breakdown = []

        for (year, month), logs in sorted(month_groups.items()):
            ndvi_obs_for_month = ndvi_by_month.get((year, month))

            month_corroborated   = 0
            month_uncorroborated = 0
            month_no_ndvi        = 0

            for log in logs:
                if ndvi_obs_for_month is None or ndvi_obs_for_month.ndvi_anomaly is None:
                    month_no_ndvi += 1
                elif float(ndvi_obs_for_month.ndvi_anomaly) < NDVI_CORROBORATION_THRESHOLD:
                    month_corroborated += 1
                else:
                    month_uncorroborated += 1

            corroborated   += month_corroborated
            uncorroborated += month_uncorroborated
            no_ndvi_data   += month_no_ndvi

            month_breakdown.append({
                "year": year,
                "month": month,
                "triggers": len(logs),
                "ndvi_anomaly": (
                    float(ndvi_obs_for_month.ndvi_anomaly)
                    if ndvi_obs_for_month and ndvi_obs_for_month.ndvi_anomaly is not None
                    else None
                ),
                "ndvi_corroborates": (
                    (float(ndvi_obs_for_month.ndvi_anomaly) < NDVI_CORROBORATION_THRESHOLD)
                    if ndvi_obs_for_month and ndvi_obs_for_month.ndvi_anomaly is not None
                    else None
                ),
                "corroborated": month_corroborated,
                "uncorroborated": month_uncorroborated,
                "no_ndvi_data": month_no_ndvi,
            })

        total_primary = len(primary_triggers)
        # Denominator excludes months with no NDVI data — gaps must not inflate the %
        denominator = corroborated + uncorroborated

        BASIS_RISK_GATE_PCT = 30.0
        proxy_pct = None
        gate_pass = None
        if denominator > 0:
            proxy_pct = round((uncorroborated / denominator) * 100, 1)
            gate_pass = proxy_pct < BASIS_RISK_GATE_PCT

        logger.info(
            f"Basis risk proxy: {proxy_pct}% | "
            f"corroborated={corroborated} uncorroborated={uncorroborated} "
            f"no_ndvi={no_ndvi_data} excluded_flood={excluded_flood}"
        )

        return {
            "proxy_basis_risk_pct": proxy_pct,
            "gate_pass": gate_pass,
            "total_primary": total_primary,
            "corroborated": corroborated,
            "uncorroborated": uncorroborated,
            "no_ndvi_data": no_ndvi_data,
            "excluded_flood": excluded_flood,
            "month_breakdown": month_breakdown,
            "methodology_note": result_template["methodology_note"],
        }

    except Exception as e:
        logger.error(f"Basis risk computation failed: {e}", exc_info=True)
        result_template["methodology_note"] = (
            f"Basis risk computation failed: {e}. Manual review required."
        )
        return result_template
