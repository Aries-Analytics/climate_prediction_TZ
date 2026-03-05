"""
Forecast Logs API endpoints

Provides access to shadow-run ForecastLog entries stored by the pipeline.
Supports filtering, pagination, and aggregate summary statistics.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime
from typing import Optional, List

from app.core.database import get_db
from app.models.forecast_log import ForecastLog

router = APIRouter(prefix="/v1/forecast-logs", tags=["forecast-logs"])


@router.get("/")
def list_forecast_logs(
    region_id: Optional[str] = Query(None, description="Filter by region ID"),
    forecast_type: Optional[str] = Query(
        None,
        description="Filter by forecast type (rainfall, flood, crop_failure)",
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status (pending, evaluated)",
    ),
    model_version: Optional[str] = Query(None, description="Filter by model version"),
    issued_after: Optional[datetime] = Query(None, description="Logs issued after this datetime"),
    issued_before: Optional[datetime] = Query(None, description="Logs issued before this datetime"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """
    List forecast log entries with optional filters.

    Returns paginated forecast log records from the shadow-run pipeline.
    Each record captures a single forecast prediction snapshot including
    the probability, threshold, lead time, and (once evaluated) the
    observed value and Brier score.
    """
    query = db.query(ForecastLog)

    # Apply filters
    if region_id:
        query = query.filter(ForecastLog.region_id == region_id)
    if forecast_type:
        query = query.filter(ForecastLog.forecast_type == forecast_type)
    if status:
        query = query.filter(ForecastLog.status == status)
    if model_version:
        query = query.filter(ForecastLog.model_version == model_version)
    if issued_after:
        query = query.filter(ForecastLog.issued_at >= issued_after)
    if issued_before:
        query = query.filter(ForecastLog.issued_at <= issued_before)

    # Total count (before pagination)
    total = query.count()

    # Order by most recent first, apply pagination
    logs = (
        query
        .order_by(desc(ForecastLog.issued_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": log.id,
                "issued_at": log.issued_at.isoformat() if log.issued_at else None,
                "valid_from": log.valid_from.isoformat() if log.valid_from else None,
                "valid_until": log.valid_until.isoformat() if log.valid_until else None,
                "region_id": log.region_id,
                "model_version": log.model_version,
                "forecast_type": log.forecast_type,
                "forecast_value": float(log.forecast_value) if log.forecast_value is not None else None,
                "threshold_used": float(log.threshold_used) if log.threshold_used is not None else None,
                "lead_time_days": log.lead_time_days,
                "status": log.status,
                "observed_value": float(log.observed_value) if log.observed_value is not None else None,
                "brier_score": float(log.brier_score) if log.brier_score is not None else None,
            }
            for log in logs
        ],
    }


@router.get("/summary")
def get_forecast_logs_summary(
    region_id: Optional[str] = Query(None, description="Filter by region ID"),
    db: Session = Depends(get_db),
):
    """
    Aggregate statistics across all forecast log entries.

    Returns:
    - Total logs, breakdown by status (pending/evaluated)
    - Count per forecast type
    - Average Brier score for evaluated forecasts
    - Latest and earliest issued_at timestamps
    """
    base_query = db.query(ForecastLog)
    if region_id:
        base_query = base_query.filter(ForecastLog.region_id == region_id)

    total = base_query.count()
    pending = base_query.filter(ForecastLog.status == "pending").count()
    evaluated = base_query.filter(ForecastLog.status == "evaluated").count()

    # Average Brier score (evaluated only)
    avg_brier = (
        base_query
        .filter(ForecastLog.status == "evaluated", ForecastLog.brier_score.isnot(None))
        .with_entities(func.avg(ForecastLog.brier_score))
        .scalar()
    )

    # Count by forecast type
    type_counts_raw = (
        base_query
        .with_entities(ForecastLog.forecast_type, func.count(ForecastLog.id))
        .group_by(ForecastLog.forecast_type)
        .all()
    )
    type_counts = {ft: count for ft, count in type_counts_raw}

    # Latest / earliest
    latest = base_query.with_entities(func.max(ForecastLog.issued_at)).scalar()
    earliest = base_query.with_entities(func.min(ForecastLog.issued_at)).scalar()

    # Distinct model versions
    model_versions = [
        v[0]
        for v in base_query
        .with_entities(ForecastLog.model_version)
        .distinct()
        .all()
    ]

    return {
        "total": total,
        "pending": pending,
        "evaluated": evaluated,
        "avg_brier_score": round(float(avg_brier), 4) if avg_brier is not None else None,
        "by_forecast_type": type_counts,
        "model_versions": model_versions,
        "latest_issued_at": latest.isoformat() if latest else None,
        "earliest_issued_at": earliest.isoformat() if earliest else None,
    }
