from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.evaluation_service import ForecastEvaluator
from app.services.evidence_generator import EvidencePackGenerator

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
