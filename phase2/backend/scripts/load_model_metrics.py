"""
Model Metrics Loading Script

Loads ML model performance metrics and feature importance into database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pandas as pd
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.model_metric import ModelMetric
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_model_metrics(
    results_file: str = None,
    clear_existing: bool = False
):
    """
    Load model metrics from training results JSON.
    """
    # Resolve project-relative paths (works on both Windows and Unix)
    project_root = Path(__file__).resolve().parent.parent.parent
    models_dir = project_root / "outputs" / "models"

    # Default: use canonical latest_training_results.json
    if results_file is None:
        results_file = str(models_dir / "latest_training_results.json")

    # If specified file doesn't exist, find the most recent timestamped one
    if not Path(results_file).exists():
        if models_dir.exists():
            result_files = list(models_dir.glob("training_results_*.json"))
            if result_files:
                results_file = str(max(result_files, key=lambda p: p.stat().st_mtime))
                logger.info(f"Using most recent training results: {results_file}")
    
    logger.info(f"Loading model metrics from {results_file}")
    
    # Read training results
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        logger.info(f"Read training results for {len(results.get('models', {}))} models")
    except Exception as e:
        logger.error(f"Failed to read training results: {e}")
        return False
    
    db = SessionLocal()
    
    try:
        # Clear existing data if requested
        if clear_existing:
            logger.info("Clearing existing model metrics...")
            db.query(ModelMetric).delete()
            db.commit()
            logger.info("Existing data cleared")
        
        models_loaded = 0
        
        # Extract models from results
        models_data = results.get('models', {})
        
        for model_name, metrics in models_data.items():
            if not metrics:
                continue
            
            # Handle ensemble differently - it has ensemble_metrics
            if model_name == 'ensemble':
                test_metrics = metrics.get('ensemble_metrics', {})
            else:
                # Get test metrics (or val metrics as fallback)
                test_metrics = metrics.get('test_metrics', metrics.get('val_metrics', {}))
            
            # Create ModelMetric record
            # Handle None values properly - don't default to 0
            metric = ModelMetric(
                model_name=model_name,
                r2_score=test_metrics.get('r2') if test_metrics.get('r2') is not None else None,
                rmse=test_metrics.get('rmse') if test_metrics.get('rmse') is not None else None,
                mae=test_metrics.get('mae') if test_metrics.get('mae') is not None else None,
                mape=test_metrics.get('mape') if test_metrics.get('mape') is not None else None,
                training_date=datetime.fromisoformat(results.get('training_start_time', datetime.now(timezone.utc).isoformat())),
                hyperparameters={
                    'n_features': metrics.get('n_features'),
                    'training_time': metrics.get('training_time'),
                    'n_estimators': metrics.get('n_estimators'),
                    'epochs_trained': metrics.get('epochs_trained'),
                    'sequence_length': metrics.get('sequence_length')
                }
            )
            
            db.add(metric)
            models_loaded += 1
            logger.info(f"  - {model_name}: R²={metric.r2_score:.4f}, RMSE={metric.rmse:.4f}")
        
        db.commit()
        
        logger.info(f"✓ Successfully loaded {models_loaded} model metrics")
        
        # Verification
        total_count = db.query(ModelMetric).count()
        logger.info(f"✓ Total model metrics in database: {total_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading model metrics: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def load_feature_importance(
    rf_file: str = "outputs/models/random_forest_climate_feature_importance.csv",
    xgb_file: str = "outputs/models/xgboost_climate_feature_importance_gain.csv"
):
    """
    Load feature importance data (placeholder - would need FeatureImportance model).
    """
    logger.info("Feature importance loading not yet implemented")
    logger.info("(Requires FeatureImportance model to be added)")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load model metrics into dashboard database")
    parser.add_argument("--results", default=None, help="Path to training results JSON (default: outputs/models/latest_training_results.json)")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before loading")
    
    args = parser.parse_args()
    
    success = load_model_metrics(args.results, args.clear)
    sys.exit(0 if success else 1)
