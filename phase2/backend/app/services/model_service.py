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
    """Get latest metrics for all models with CV and feature selection data"""
    # Get the latest metric for each model by ID (most recent insert)
    # Using MAX(id) ensures we get the truly latest record even when training_date is same
    subquery = db.query(
        ModelMetric.model_name,
        func.max(ModelMetric.id).label('max_id')
    ).group_by(ModelMetric.model_name).subquery()
    
    metrics = db.query(ModelMetric).join(
        subquery,
        (ModelMetric.model_name == subquery.c.model_name) &
        (ModelMetric.id == subquery.c.max_id)
    ).all()
    
    # Load CV and feature selection data from latest training results
    cv_data, feature_data = _load_latest_training_results()
    
    # Enhance metrics with CV and feature selection data
    enhanced_metrics = []
    for m in metrics:
        metric_dict = {
            "id": m.id,
            "model_name": m.model_name,
            "experiment_id": m.experiment_id,
            "r2_score": m.r2_score,
            "rmse": m.rmse,
            "mae": m.mae,
            "mape": m.mape,
            "training_date": m.training_date,
            "data_start_date": m.data_start_date,
            "data_end_date": m.data_end_date,
            "hyperparameters": m.hyperparameters,
            "created_at": m.created_at,
        }
        
        # Add CV data if available
        # Try exact match first, then try with underscores replaced
        model_key = m.model_name
        if model_key not in cv_data:
            # Try alternative naming (e.g., "random_forest" vs "Random Forest")
            model_key = model_key.replace('_', ' ').title()
        if model_key not in cv_data:
            # Try lowercase with underscores
            model_key = m.model_name.lower().replace(' ', '_')
        
        if model_key in cv_data:
            cv = cv_data[model_key]
            metric_dict.update({
                "cv_r2_mean": cv.get("r2_mean"),
                "cv_r2_std": cv.get("r2_std"),
                "cv_r2_ci_lower": cv.get("r2_ci_lower"),
                "cv_r2_ci_upper": cv.get("r2_ci_upper"),
                "cv_rmse_mean": cv.get("rmse_mean"),
                "cv_rmse_std": cv.get("rmse_std"),
                "cv_mae_mean": cv.get("mae_mean"),
                "cv_mae_std": cv.get("mae_std"),
                "cv_n_splits": cv.get("n_splits"),
            })
        
        # Add feature selection data and sample counts
        if feature_data:
            metric_dict.update({
                "n_features": feature_data.get("selected_features"),
                "feature_to_sample_ratio": feature_data.get("feature_to_sample_ratio"),
                "n_train_samples": feature_data.get("n_train_samples"),
                "n_val_samples": feature_data.get("n_val_samples"),
                "n_test_samples": feature_data.get("n_test_samples"),
            })
        
        enhanced_metrics.append(ModelMetricsResponse(**metric_dict))
    
    return enhanced_metrics


def _load_latest_training_results():
    """Load CV and feature selection data from latest training results JSON"""
    import glob
    
    models_dir = os.path.join(settings.OUTPUTS_DIR, "models")
    
    # Find the latest training_results JSON file
    pattern = os.path.join(models_dir, "training_results_*.json")
    result_files = glob.glob(pattern)
    
    if not result_files:
        return {}, {}
    
    # Get the most recent file
    latest_file = max(result_files, key=os.path.getmtime)
    
    try:
        with open(latest_file, 'r') as f:
            results = json.load(f)
        
        # Extract CV data
        cv_data = {}
        if "cross_validation" in results and results["cross_validation"]:
            for model_name, cv_metrics in results["cross_validation"].items():
                cv_data[model_name] = cv_metrics
        
        # Extract feature selection data
        feature_data = {}
        if "feature_selection" in results:
            fs = results["feature_selection"]
            feature_data = {
                "selected_features": fs.get("selected_features"),
                "original_features": fs.get("original_features"),
            }
            
            # Add sample counts from data_shapes
            if "data_shapes" in results:
                shapes = results["data_shapes"]
                if "train" in shapes:
                    feature_data["n_train_samples"] = shapes["train"][0]
                if "val" in shapes:
                    feature_data["n_val_samples"] = shapes["val"][0]
                if "test" in shapes:
                    feature_data["n_test_samples"] = shapes["test"][0]
            
            # Calculate feature-to-sample ratio
            if "data_shapes" in results and "train" in results["data_shapes"]:
                n_train_samples = results["data_shapes"]["train"][0]
                n_features = fs.get("selected_features", 1)
                if n_features > 0:
                    feature_data["feature_to_sample_ratio"] = n_train_samples / n_features
        
        return cv_data, feature_data
    
    except Exception as e:
        # Silently fail and return empty dicts
        return {}, {}

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
    import pandas as pd
    import glob
    
    # Try multiple file name patterns
    models_dir = os.path.join(settings.OUTPUTS_DIR, "models")
    
    # Pattern 1: exact match
    importance_file = os.path.join(models_dir, f"{model_name}_feature_importance.csv")
    
    # Pattern 2: with _climate suffix (common pattern)
    if not os.path.exists(importance_file):
        importance_file = os.path.join(models_dir, f"{model_name}_climate_feature_importance.csv")
    
    # Pattern 3: search for any file containing the model name and feature_importance
    # This handles cases like xgboost_climate_feature_importance_gain.csv
    if not os.path.exists(importance_file):
        pattern = os.path.join(models_dir, f"*{model_name}*feature_importance*.csv")
        matches = glob.glob(pattern)
        if matches:
            importance_file = matches[0]
    
    if not os.path.exists(importance_file):
        return []
    
    try:
        # Read CSV file
        df = pd.read_csv(importance_file)
        
        # Convert to FeatureImportance objects
        features = []
        for idx, row in df.iterrows():
            features.append(FeatureImportance(
                feature_name=row['feature'],
                importance=float(row['importance']),
                rank=int(row['rank']) if 'rank' in df.columns else idx + 1
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
