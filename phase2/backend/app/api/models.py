from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.model import (
    ModelMetricsResponse,
    ModelComparison,
    FeatureImportance,
    DriftStatus,
    ModelPredictionResponse
)
from app.services import model_service
from app.models.user import User

router = APIRouter(prefix="/models", tags=["models"])

@router.get("", response_model=List[ModelMetricsResponse])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all models with their latest metrics"""
    return model_service.get_all_models(db)

@router.get("/{model_name}/metrics", response_model=ModelMetricsResponse)
def get_model_metrics(
    model_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get metrics for a specific model"""
    metrics = model_service.get_model_metrics(db, model_name)
    
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    
    return metrics

@router.get("/{model_name}/importance", response_model=List[FeatureImportance])
def get_feature_importance(
    model_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get feature importance for a model"""
    importance = model_service.get_feature_importance(model_name)
    
    if not importance:
        raise HTTPException(
            status_code=404,
            detail=f"Feature importance not found for model '{model_name}'"
        )
    
    return importance

@router.get("/{model_name}/drift", response_model=DriftStatus)
def check_model_drift(
    model_name: str,
    threshold: float = Query(0.1, ge=0, le=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check if a model is experiencing drift"""
    return model_service.check_model_drift(db, model_name, threshold)

@router.get("/{model_name}/predictions", response_model=List[ModelPredictionResponse])
def get_prediction_history(
    model_name: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get prediction history for a model"""
    return model_service.get_prediction_history(db, model_name, limit)

@router.get("/compare", response_model=ModelComparison)
def compare_models(
    model_names: List[str] = Query(..., description="List of model names to compare"),
    metric: str = Query("r2_score", description="Metric to use for comparison"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Compare multiple models"""
    return model_service.compare_models(db, model_names, metric)
