import sys
import os

# Ensure we're in the backend directory for imports
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

# If 'backend' subdirectory exists (local dev), add it too
backend_dir = os.path.join(root_dir, 'backend')
if os.path.exists(backend_dir):
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.forecast import Forecast, ForecastRecommendation, ForecastValidation
from sqlalchemy import text

def delete_all_forecasts():
    print("Connecting to database...")
    db = SessionLocal()
    try:
        print("Emptying forecast-related tables...")
        # Use simple delete
        db.query(ForecastRecommendation).delete()
        db.query(ForecastValidation).delete()
        deleted = db.query(Forecast).delete()
        
        db.commit()
        print(f"✅ Successfully deleted {deleted} forecasts and related data.")
        
    except Exception as e:
        print(f"❌ Error deleting forecasts: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_forecasts()
