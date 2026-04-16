from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from app.core.database import get_db
from app.services.evaluation_service import ForecastEvaluator
from app.services.evidence_generator import EvidencePackGenerator
from app.services.basis_risk_service import compute_ndvi_proxy_basis_risk, compute_zone_basis_risk
from app.models.pipeline_execution import PipelineExecution
from app.models.forecast_log import ForecastLog
from app.models.location import Location
from app.services.evaluation_service import PILOT_ZONE_IDS
from app.config.shadow_run import (
    SHADOW_RUN_START,
    SHADOW_RUN_END,
    SHADOW_RUN_TARGET_DAYS,
    SHADOW_RUN_TARGET_FORECASTS,
    projected_end_date,
    projected_brier_eval_date,
)

router = APIRouter(prefix="/v1/evidence-pack", tags=["Evidence Pack"])

@router.post("/evaluate")
def trigger_evaluation(db: Session = Depends(get_db)):
    """
    Triggers the evaluation of all pending forecasts whose validity period has elapsed.
    """
    try:
        evaluator = ForecastEvaluator(db)
        result = evaluator.evaluate_pending_forecasts()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
def get_evidence_metrics(
    location_id: Optional[int] = Query(
        None,
        description="Filter by zone: 7 = Ifakara TC, 8 = Mlimba DC. "
                    "Omit for aggregate + per-zone breakdown.",
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieves Brier Score, RMSE, and Calibration Error for the Shadow Run.

    - **No location_id**: returns aggregate metrics with a ``zones`` dict
      containing per-zone breakdowns (Ifakara TC + Mlimba DC).
    - **location_id=7** or **location_id=8**: returns metrics for that zone only.
    """
    try:
        evaluator = ForecastEvaluator(db)
        if location_id is not None:
            return evaluator.get_zone_metrics(location_id)
        return evaluator.get_aggregate_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/observations")
def backfill_observations(
    observations: List[Dict[str, Any]] = Body(
        ..., 
        example=[{"log_id": "uuid-here", "observed_value": 155.0}]
    ),
    db: Session = Depends(get_db)
):
    """
    Manually inject actual observed payload data into specific ForecastLog entries.
    Allows immediate testing of the evaluation engine without waiting for 
    asynchronous climate data ingestion later in the year.
    """
    try:
        evaluator = ForecastEvaluator(db)
        result = evaluator.backfill_observations(observations)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/execution-log")
def get_execution_log(db: Session = Depends(get_db)):
    """
    Returns shadow run progress (total forecast_logs vs target from shadow_run config)
    and the last 30 pipeline execution records for the Evidence Pack dashboard.

    Shadow run v2 — two-zone split (Ifakara TC + Mlimba DC).
    24 forecasts/day = 3 triggers × 4 horizons × 2 locations.
    DB wiped clean before restart — all logs belong to the current run.
    """
    try:
        total_logs = db.query(sqlfunc.count(ForecastLog.id)).filter(
            sqlfunc.date(ForecastLog.issued_at) >= SHADOW_RUN_START
        ).scalar() or 0
        valid_run_days = db.query(
            sqlfunc.count(sqlfunc.distinct(sqlfunc.date(ForecastLog.issued_at)))
        ).filter(
            sqlfunc.date(ForecastLog.issued_at) >= SHADOW_RUN_START
        ).scalar() or 0
        target = SHADOW_RUN_TARGET_FORECASTS

        executions = (
            db.query(PipelineExecution)
            .order_by(PipelineExecution.started_at.desc())
            .limit(30)
            .all()
        )

        # Build zone list from DB — no hardcoding
        zone_list = []
        for loc_id in PILOT_ZONE_IDS:
            loc = db.query(Location).filter(Location.id == loc_id).first()
            if loc:
                zone_list.append({
                    "location_id": loc.id,
                    "name": loc.name,
                    "latitude": float(loc.latitude),
                    "longitude": float(loc.longitude),
                })

        num_zones = len(zone_list) or 1
        triggers_per_zone = 3  # drought, flood, crop_failure
        horizons = 4           # 3, 4, 5, 6 months
        forecasts_per_day = triggers_per_zone * horizons * num_zones

        proj_end = projected_end_date(valid_run_days)
        proj_brier = projected_brier_eval_date(valid_run_days)
        return {
            "shadow_run": {
                "total_forecast_logs": total_logs,
                "target": target,
                "pct_complete": round((total_logs / target) * 100, 1) if target > 0 else 0,
                "valid_run_days": valid_run_days,
                "target_days": SHADOW_RUN_TARGET_DAYS,
                "start_date": SHADOW_RUN_START.isoformat(),
                "end_date": SHADOW_RUN_END.isoformat(),          # TARGET (zero-gap)
                "projected_end_date": proj_end.isoformat(),       # LIVE (adapts to gaps)
                "projected_brier_eval_date": proj_brier.isoformat(),
                "gap_days": max(0, (proj_end - SHADOW_RUN_END).days),
                "zones": zone_list,
                "forecasts_per_day": forecasts_per_day,
            },
            "executions": [
                {
                    "id": e.id,
                    "execution_type": e.execution_type,
                    "status": e.status,
                    "started_at": e.started_at.isoformat() if e.started_at else None,
                    "duration_seconds": e.duration_seconds,
                    "forecasts_generated": e.forecasts_generated,
                    "records_stored": e.records_stored,
                    "sources_succeeded": e.sources_succeeded or [],
                    "sources_failed": e.sources_failed or [],
                    "error_message": e.error_message,
                }
                for e in executions
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/basis-risk")
def get_basis_risk(
    location_id: Optional[int] = Query(
        None,
        description="Filter by zone: 7 = Ifakara TC, 8 = Mlimba DC. "
                    "Omit for aggregate + per-zone breakdown.",
    ),
    db: Session = Depends(get_db),
):
    """
    Returns the live NDVI proxy basis risk computation.

    - **No location_id**: returns basin-wide aggregate with a ``zones`` dict
      containing per-zone breakdowns (Ifakara TC + Mlimba DC).
    - **location_id=7** or **location_id=8**: returns basis risk for that zone only.

    Available incrementally — does not wait for shadow run completion.
    Returns the current state based on however many evaluated primary-tier
    forecasts exist.  Will return empty counts before first 3-month forecasts
    mature (~June 9, 2026).

    Basis risk = % of primary-tier drought/crop_failure triggers (≥75%, ≤4mo)
    that are NOT corroborated by a below-normal NDVI anomaly in the same month.
    Flood triggers are excluded (NDVI is not a reliable flood signal).
    """
    try:
        if location_id is not None:
            return compute_zone_basis_risk(db, location_id)
        return compute_ndvi_proxy_basis_risk(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/final-report")
def get_final_report():
    """
    Returns the shadow run completion report generated when valid_run_days reaches 90.

    Includes go/no-go gate results (Brier Score, Basis Risk) and aggregate metrics.
    Returns 404 before the shadow run completes.  The Evidence Pack dashboard
    uses this endpoint to display the completion state and gate verdicts.
    """
    report = EvidencePackGenerator.get_final_report()
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Shadow run not yet complete. Report will be available after 90 valid run-days.",
        )
    return report

@router.post("/generate")
def generate_evidence_pack(db: Session = Depends(get_db)):
    """
    Generates a cryptographically sound, auditable Evidence Pack for Reinsurers.
    Bundles the evaluation metrics, model version data, and entire forecast history into a ZIP.
    Returns a downloadable .zip file.
    """
    try:
        generator = EvidencePackGenerator(db)
        return generator.generate_zip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
