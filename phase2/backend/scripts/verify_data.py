"""
Data Verification Script

Verifies that all data has been loaded correctly into the dashboard database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.climate_data import ClimateData
from app.models.trigger_event import TriggerEvent
from app.models.model_metric import ModelMetric
from app.models.user import User
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_data():
    """
    Verify all data in the database.
    """
    logger.info("=" * 80)
    logger.info("DATABASE VERIFICATION")
    logger.info("=" * 80)
    logger.info(f"Verification time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    db = SessionLocal()
    
    try:
        all_checks_passed = True
        
        # Check 1: Climate Data
        logger.info("CHECK 1: Climate Data")
        logger.info("-" * 40)
        climate_count = db.query(ClimateData).count()
        logger.info(f"  Total records: {climate_count}")
        
        if climate_count == 0:
            logger.error("  ✗ FAIL: No climate data found")
            all_checks_passed = False
        elif climate_count < 72:
            logger.warning(f"  ⚠ WARNING: Expected 72 records, found {climate_count}")
        else:
            logger.info(f"  ✓ PASS: Climate data loaded")
        
        # Check date range
        if climate_count > 0:
            min_date = db.query(func.min(ClimateData.date)).scalar()
            max_date = db.query(func.max(ClimateData.date)).scalar()
            logger.info(f"  Date range: {min_date} to {max_date}")
        
        logger.info("")
        
        # Check 2: Trigger Events
        logger.info("CHECK 2: Trigger Events")
        logger.info("-" * 40)
        trigger_count = db.query(TriggerEvent).count()
        logger.info(f"  Total triggers: {trigger_count}")
        
        if trigger_count == 0:
            logger.warning("  ⚠ WARNING: No trigger events found")
        else:
            # Count by type
            drought_count = db.query(TriggerEvent).filter(TriggerEvent.event_type == 'drought').count()
            flood_count = db.query(TriggerEvent).filter(TriggerEvent.event_type == 'flood').count()
            crop_count = db.query(TriggerEvent).filter(TriggerEvent.event_type == 'crop_failure').count()
            
            logger.info(f"  - Drought: {drought_count}")
            logger.info(f"  - Flood: {flood_count}")
            logger.info(f"  - Crop Failure: {crop_count}")
            logger.info(f"  ✓ PASS: Trigger events loaded")
        
        logger.info("")
        
        # Check 3: Model Metrics
        logger.info("CHECK 3: Model Metrics")
        logger.info("-" * 40)
        model_count = db.query(ModelMetric).count()
        logger.info(f"  Total models: {model_count}")
        
        if model_count == 0:
            logger.warning("  ⚠ WARNING: No model metrics found")
        elif model_count < 4:
            logger.warning(f"  ⚠ WARNING: Expected 4 models, found {model_count}")
        else:
            # List models
            models = db.query(ModelMetric).all()
            for model in models:
                logger.info(f"  - {model.model_name}: R²={model.r2_score:.4f}")
            logger.info(f"  ✓ PASS: Model metrics loaded")
        
        logger.info("")
        
        # Check 4: Users
        logger.info("CHECK 4: Users")
        logger.info("-" * 40)
        user_count = db.query(User).count()
        logger.info(f"  Total users: {user_count}")
        
        if user_count == 0:
            logger.warning("  ⚠ WARNING: No users found")
        else:
            # Count by role
            admin_count = db.query(User).filter(User.role == 'admin').count()
            analyst_count = db.query(User).filter(User.role == 'analyst').count()
            viewer_count = db.query(User).filter(User.role == 'viewer').count()
            
            logger.info(f"  - Admin: {admin_count}")
            logger.info(f"  - Analyst: {analyst_count}")
            logger.info(f"  - Viewer: {viewer_count}")
            logger.info(f"  ✓ PASS: Users created")
        
        logger.info("")
        
        # Final summary
        logger.info("=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Climate Data: {climate_count} records")
        logger.info(f"Trigger Events: {trigger_count} records")
        logger.info(f"Model Metrics: {model_count} records")
        logger.info(f"Users: {user_count} records")
        logger.info("")
        
        if all_checks_passed and climate_count > 0:
            logger.info("✓ All critical checks passed!")
            logger.info("Database is ready for use.")
        else:
            logger.warning("⚠ Some checks failed or returned warnings")
            logger.warning("Review the output above for details.")
        
        logger.info("=" * 80)
        
        return all_checks_passed
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = verify_data()
    sys.exit(0 if success else 1)
