from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import os
import json
from app.models.model_metric import ModelMetric
from app.models.model_prediction import ModelPrediction
from app.schemas.model import (
    ModelMetricsResponse,
    ModelComparison,
    FeatureImportance,
    DriftStatus,
    ModelPredictionResponse
)
from app.core.config import settings

def get_model_metrics(db: Session, model_name: str) -> Optional[ModelMetricsResponse]:
    """Get the latest metrics for a specific model"""
    metric = db.query(ModelMetric).filter(
        ModelMetric.model_name == model_name
    ).order_by(desc(ModelMetric.training_date)).first()
    
    if not metric:
        return None
    
    return ModelMetricsResponse.model_validate(metric)

def get_all_models(db: Session) -> List[ModelMetricsResponse]:
    """Get latest metrics for all models"""
    # Get the latest metric for each model
    # Use a simpler approach that works with SQLite
    subquery = db.query(
        ModelMetric.model_name,
        func.max(ModelMetric.training_date).label('max_date')
    ).group_by(ModelMetric.model_name).subquery()
    
    metrics = db.query(ModelMetric).join(
        subquery,
        (ModelMetric.model_name == subquery.c.model_name) &
        (ModelMetric.training_date == subquery.c.max_date)
    ).all()
    
    return [ModelMetricsResponse.model_validate(m) for m in metrics]

def compare_models(db: Session, model_names: List[str], metric: str = "r2_score") -> ModelComparison:
    """Compare multiple models by a specific metric"""
    models = []
    
    for model_name in model_names:
        model_metric = get_model_metrics(db, model_name)
        if model_metric:
            models.append(model_metric)
    
    if not models:
        return ModelComparison(
            models=[],
            best_model="",
            comparison_metric=metric
        )
    
    # Determine best model based on metric
    if metric in ["r2_score"]:
        # Higher is better
        best_model = max(models, key=lambda m: getattr(m, metric) or 0)
    else:
        # Lower is better (rmse, mae, mape)
        best_model = min(models, key=lambda m: getattr(m, metric) or float('inf'))
    
    return ModelComparison(
        models=models,
        best_model=best_model.model_name,
        comparison_metric=metric
    )

def get_feature_importance(model_name: str) -> List[FeatureImportance]:
    """Get feature importance for a model from saved files"""
    # Try to load from outputs directory
    importance_file = os.path.join(
        settings.OUTPUTS_DIR,
        "evaluation",
        f"{model_name}_feature_importance.json"
    )
    
    if not os.path.exists(importance_file):
        return []
    
    try:
        with open(importance_file, 'r') as f:
            data = json.load(f)
        
        # Convert to FeatureImportance objects
        features = []
        for rank, (feature, importance) in enumerate(data.items(), 1):
            features.append(FeatureImportance(
                feature_name=feature,
                importance=float(importance),
                rank=rank
            ))
        
        return sorted(features, key=lambda x: x.importance, reverse=True)
    
    except Exception:
        return []

def check_model_drift(db: Session, model_name: str, threshold: float = 0.1) -> DriftStatus:
    """Check if a model is experiencing drift"""
    # Get the two most recent metrics
    metrics = db.query(ModelMetric).filter(
        ModelMetric.model_name == model_name
    ).order_by(desc(ModelMetric.training_date), desc(ModelMetric.id)).limit(2).all()
    
    if len(metrics) < 2:
        return DriftStatus(
            model_name=model_name,
            is_drifting=False,
            drift_score=0.0,
            threshold=threshold,
            recommendation="Insufficient data to determine drift"
        )
    
    latest, previous = metrics[0], metrics[1]
    
    # Calculate drift based on R² score change
    if latest.r2_score is not None and previous.r2_score is not None:
        drift_score = abs(float(latest.r2_score) - float(previous.r2_score))
        is_drifting = drift_score > threshold
        
        if is_drifting:
            recommendation = f"Model performance has changed by {drift_score:.2%}. Consider retraining."
        else:
            recommendation = "Model performance is stable."
    else:
        drift_score = 0.0
        is_drifting = False
        recommendation = "Unable to calculate drift - missing metrics"
    
    return DriftStatus(
        model_name=model_name,
        is_drifting=is_drifting,
        drift_score=drift_score,
        threshold=threshold,
        recommendation=recommendation
    )

def get_prediction_history(
    db: Session,
    model_name: str,
    limit: int = 100
) -> List[ModelPredictionResponse]:
    """Get prediction history for a model"""
    predictions = db.query(ModelPrediction).filter(
        ModelPrediction.model_name == model_name
    ).order_by(desc(ModelPrediction.target_date), desc(ModelPrediction.id)).limit(limit).all()
    
    return [ModelPredictionResponse.model_validate(p) for p in predictions]
