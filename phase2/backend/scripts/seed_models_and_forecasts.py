
import sys
import os
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.append(os.getcwd())

try:
    from app.core.database import SessionLocal
    from app.models.model_metric import ModelMetric
    from app.models.forecast import Forecast
    from app.models.location import Location
    from sqlalchemy import func
except ImportError:
    # Try alternate path for Docker
    sys.path.append("/app")
    from app.core.database import SessionLocal
    from app.models.model_metric import ModelMetric
    from app.models.forecast import Forecast
    from app.models.location import Location
    from sqlalchemy import func

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    db = SessionLocal()
    try:
        logger.info("Seeding Model Metrics (ML Models)...")
        
        # Standardized model names: lowercase with underscores
        # Added data_start_date, data_end_date, experiment_id for dashboard
        # Metrics from actual training run 2026-03-05 (test set / holdout)
        # Source: outputs/models/latest_training_results.json
        training_date = datetime(2026, 3, 5, tzinfo=timezone.utc)
        models_data = [
            {
                "model_name": "ensemble",
                "experiment_id": "ensemble_baseline",
                "r2_score": 0.840,
                "rmse": 0.439,
                "mae": 0.278,
                "mape": 74.8,
                "training_date": training_date,
                "data_start_date": datetime(2015, 1, 1).date(),
                "data_end_date": datetime(2025, 12, 31).date()
            },
            {
                "model_name": "xgboost",
                "experiment_id": "xgboost_baseline",
                "r2_score": 0.867,
                "rmse": 0.401,
                "mae": 0.252,
                "mape": 74.6,
                "training_date": training_date,
                "data_start_date": datetime(2015, 1, 1).date(),
                "data_end_date": datetime(2025, 12, 31).date()
            },
            {
                "model_name": "lstm",
                "experiment_id": "lstm_baseline",
                "r2_score": 0.787,
                "rmse": 0.510,
                "mae": 0.329,
                "mape": 94.0,
                "training_date": training_date,
                "data_start_date": datetime(2015, 1, 1).date(),
                "data_end_date": datetime(2025, 12, 31).date()
            },
            {
                "model_name": "random_forest",
                "experiment_id": "random_forest_baseline",
                "r2_score": 0.781,
                "rmse": 0.513,
                "mae": 0.320,
                "mape": 66.8,
                "training_date": training_date,
                "data_start_date": datetime(2015, 1, 1).date(),
                "data_end_date": datetime(2025, 12, 31).date()
            }
        ]

        for m_data in models_data:
            # Case-insensitive lookup to prevent duplicates
            existing = db.query(ModelMetric).filter(
                func.lower(ModelMetric.model_name) == m_data["model_name"].lower()
            ).first()
            
            if existing:
                # Update existing record
                for key, value in m_data.items():
                    setattr(existing, key, value)
                logger.info(f"Updated model metric: {m_data['model_name']}")
            else:
                # Create new record
                metric = ModelMetric(**m_data)
                db.add(metric)
                logger.info(f"Created model metric: {m_data['model_name']}")
        
        db.commit()

        # Seed Forecasts if missing
        logger.info("Checking Forecasts...")
        location = db.query(Location).first()
        if location:
            existing_forecast = db.query(Forecast).filter(Forecast.location_id == location.id).first()
            if not existing_forecast:
                logger.info(f"Seeding sample forecast for location: {location.name}")
                forecast = Forecast(
                    forecast_date=datetime.now(timezone.utc).date(),
                    target_date=(datetime.now(timezone.utc) + timedelta(days=90)).date(),
                    horizon_months=3,
                    trigger_type="drought",
                    probability=0.75,
                    confidence_lower=0.6,
                    confidence_upper=0.9,
                    model_version="XGBoost_v4",
                    expected_deficit=50.0,
                    location_id=location.id
                )
                db.add(forecast)
                db.commit()
                logger.info("✅ Sample forecast created")
            else:
                 logger.info("Forecasts already exist")
        else:
             logger.warning("No locations found to attach forecasts to!")

        logger.info("✅ Seeding complete!")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
