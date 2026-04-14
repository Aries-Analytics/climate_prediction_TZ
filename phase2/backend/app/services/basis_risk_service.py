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


from app.models.location import Location
from app.services.evaluation_service import PILOT_ZONE_IDS

BASIS_RISK_GATE_PCT = 30.0

_METHODOLOGY_NOTE = (
    "Basis risk estimated from NDVI proxy (MODIS MOD13A2, Kilombero Basin). "
    "A primary-tier trigger (drought/crop_failure, ≥75% confidence, ≤4mo horizon) "
    "is corroborated when the monthly NDVI anomaly is < -0.05 (below-normal "
    "vegetation). Flood forecasts excluded — NDVI does not reliably capture flood "
    "events. Months with no satellite composite excluded from denominator. "
    "This is an indicative proxy estimate; a harvest survey is required for "
    "verified ground truth."
)

_NO_DATA_NOTE = (
    "No evaluated primary-tier forecasts available yet. "
    "Basis risk will be computed once forecast validity windows close "
    "(first 3-month forecasts mature ~June 9, 2026)."
)


def _empty_result() -> dict:
    """Template for a single-zone (or aggregate) basis risk result."""
    return {
        "proxy_basis_risk_pct": None,
        "gate_pass": None,
        "total_primary": 0,
        "corroborated": 0,
        "uncorroborated": 0,
        "no_ndvi_data": 0,
        "excluded_flood": 0,
        "month_breakdown": [],
        "methodology_note": _METHODOLOGY_NOTE,
    }


def _compute_basis_risk_for_triggers(
    primary_triggers: list,
    ndvi_by_month: dict,
    excluded_flood: int,
) -> dict:
    """
    Pure computation: correlate a list of primary-tier ForecastLog rows with
    an NDVI lookup dict keyed by (year, month).  Returns a single result dict.
    """
    result = _empty_result()
    result["excluded_flood"] = excluded_flood

    if not primary_triggers:
        result["methodology_note"] = _NO_DATA_NOTE
        return result

    # Group triggers by calendar month
    month_groups: dict[tuple, list] = {}
    for log in primary_triggers:
        issued = log.issued_at.date() if hasattr(log.issued_at, "date") else log.issued_at
        key = (issued.year, issued.month)
        month_groups.setdefault(key, []).append(log)

    corroborated = 0
    uncorroborated = 0
    no_ndvi_data = 0
    month_breakdown = []

    for (year, month), logs in sorted(month_groups.items()):
        ndvi_obs_for_month = ndvi_by_month.get((year, month))

        m_corr = m_uncorr = m_no = 0
        for _log in logs:
            if ndvi_obs_for_month is None or ndvi_obs_for_month.ndvi_anomaly is None:
                m_no += 1
            elif float(ndvi_obs_for_month.ndvi_anomaly) < NDVI_CORROBORATION_THRESHOLD:
                m_corr += 1
            else:
                m_uncorr += 1

        corroborated += m_corr
        uncorroborated += m_uncorr
        no_ndvi_data += m_no

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
            "corroborated": m_corr,
            "uncorroborated": m_uncorr,
            "no_ndvi_data": m_no,
        })

    denominator = corroborated + uncorroborated
    proxy_pct = None
    gate_pass = None
    if denominator > 0:
        proxy_pct = round((uncorroborated / denominator) * 100, 1)
        gate_pass = proxy_pct < BASIS_RISK_GATE_PCT

    return {
        "proxy_basis_risk_pct": proxy_pct,
        "gate_pass": gate_pass,
        "total_primary": len(primary_triggers),
        "corroborated": corroborated,
        "uncorroborated": uncorroborated,
        "no_ndvi_data": no_ndvi_data,
        "excluded_flood": excluded_flood,
        "month_breakdown": month_breakdown,
        "methodology_note": _METHODOLOGY_NOTE,
    }


def _fetch_primary_triggers(db: Session, location_id: Optional[int] = None):
    """Fetch evaluated primary-tier NDVI-relevant triggers, optionally filtered by zone."""
    q = (
        db.query(ForecastLog)
        .filter(
            ForecastLog.status == "evaluated",
            ForecastLog.forecast_type.in_(NDVI_RELEVANT_TYPES),
            ForecastLog.forecast_value >= PRIMARY_TIER_THRESHOLD,
            ForecastLog.lead_time_days <= PRIMARY_TIER_MAX_LEAD_DAYS,
        )
    )
    if location_id is not None:
        q = q.filter(ForecastLog.region_id == str(location_id))
    return q.order_by(ForecastLog.issued_at).all()


def _count_excluded_flood(db: Session, location_id: Optional[int] = None) -> int:
    """Count flood triggers excluded from basis risk scope."""
    q = db.query(func.count(ForecastLog.id)).filter(
        ForecastLog.status == "evaluated",
        ForecastLog.forecast_type == "flood",
        ForecastLog.forecast_value >= PRIMARY_TIER_THRESHOLD,
        ForecastLog.lead_time_days <= PRIMARY_TIER_MAX_LEAD_DAYS,
    )
    if location_id is not None:
        q = q.filter(ForecastLog.region_id == str(location_id))
    return q.scalar() or 0


def _load_ndvi_by_month(db: Session, location_id: Optional[int] = None) -> dict:
    """
    Load NDVI observations keyed by (year, month).

    When location_id is specified, prefer NDVI rows tagged with that zone.
    Falls back to untagged (basin-wide) rows when no zone-specific data exists.
    """
    q = db.query(NdviObservation)
    if location_id is not None:
        q = q.filter(
            (NdviObservation.location_id == location_id)
            | (NdviObservation.location_id.is_(None))
        )
    ndvi_obs = q.all()

    ndvi_by_month: dict[tuple, NdviObservation] = {}
    for obs in ndvi_obs:
        key = (obs.observed_date.year, obs.observed_date.month)
        existing = ndvi_by_month.get(key)
        # Prefer zone-specific over basin-wide (NULL location_id)
        if existing is None:
            ndvi_by_month[key] = obs
        elif location_id is not None and obs.location_id == location_id and existing.location_id != location_id:
            ndvi_by_month[key] = obs
    return ndvi_by_month


def compute_zone_basis_risk(db: Session, location_id: int) -> dict:
    """
    Compute NDVI proxy basis risk for a single zone.
    """
    try:
        triggers = _fetch_primary_triggers(db, location_id)
        excluded = _count_excluded_flood(db, location_id)
        ndvi = _load_ndvi_by_month(db, location_id)

        result = _compute_basis_risk_for_triggers(triggers, ndvi, excluded)

        location = db.query(Location).filter(Location.id == location_id).first()
        result["location_id"] = location_id
        result["zone_name"] = location.name if location else f"location_{location_id}"

        logger.info(
            f"Basis risk [{result['zone_name']}]: {result['proxy_basis_risk_pct']}% | "
            f"corr={result['corroborated']} uncorr={result['uncorroborated']} "
            f"no_ndvi={result['no_ndvi_data']}"
        )
        return result

    except Exception as e:
        logger.error(f"Basis risk computation failed for zone {location_id}: {e}", exc_info=True)
        err = _empty_result()
        err["location_id"] = location_id
        err["methodology_note"] = f"Basis risk computation failed: {e}. Manual review required."
        return err


def compute_ndvi_proxy_basis_risk(db: Session) -> dict:
    """
    Compute the NDVI proxy basis risk — aggregate AND per-zone.

    Returns the basin-wide aggregate with a mandatory ``zones`` dict containing
    per-zone breakdowns for every pilot zone.  Zone-blind output is no longer
    possible.
    """
    try:
        # ── Basin-wide aggregate ──
        all_triggers = _fetch_primary_triggers(db)
        excluded = _count_excluded_flood(db)
        ndvi_all = _load_ndvi_by_month(db)
        aggregate = _compute_basis_risk_for_triggers(all_triggers, ndvi_all, excluded)

        # ── Per-zone breakdown — always computed ──
        zones: dict[str, dict] = {}
        for loc_id in PILOT_ZONE_IDS:
            zones[str(loc_id)] = compute_zone_basis_risk(db, loc_id)

        aggregate["zones"] = zones

        logger.info(
            f"Basis risk aggregate: {aggregate['proxy_basis_risk_pct']}% | "
            f"corr={aggregate['corroborated']} uncorr={aggregate['uncorroborated']} "
            f"no_ndvi={aggregate['no_ndvi_data']} excluded_flood={excluded}"
        )
        return aggregate

    except Exception as e:
        logger.error(f"Basis risk computation failed: {e}", exc_info=True)
        err = _empty_result()
        err["methodology_note"] = f"Basis risk computation failed: {e}. Manual review required."
        err["zones"] = {}
        return err
