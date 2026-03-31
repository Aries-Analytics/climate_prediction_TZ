from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from app.core.database import get_db
from app.services.evaluation_service import ForecastEvaluator
from app.services.evidence_generator import EvidencePackGenerator
from app.models.pipeline_execution import PipelineExecution
from app.models.forecast_log import ForecastLog

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
def get_evidence_metrics(db: Session = Depends(get_db)):
    """
    Retrieves the aggregate Brier Score, RMSE, and Calibration Error for the Shadow Run.
    """
    try:
        evaluator = ForecastEvaluator(db)
        metrics = evaluator.get_aggregate_metrics()
        return metrics
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
    Returns shadow run progress (total forecast_logs vs 1080 target)
    and the last 30 pipeline execution records for the Evidence Pack dashboard.
    """
    try:
        total_logs = db.query(sqlfunc.count(ForecastLog.id)).scalar() or 0
        target = 1080  # 90 days × 12 forecasts/day

        executions = (
            db.query(PipelineExecution)
            .order_by(PipelineExecution.started_at.desc())
            .limit(30)
            .all()
        )

        return {
            "shadow_run": {
                "total_forecast_logs": total_logs,
                "target": target,
                "pct_complete": round((total_logs / target) * 100, 1) if target > 0 else 0,
                "start_date": "2026-03-07",
                "end_date": "2026-06-12",
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
