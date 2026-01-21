"""
Populate expected_deficit values for existing forecasts.

Expected deficit represents the forecasted rainfall shortage in mm.
For drought triggers, this is a positive value (deficit).
For flood/crop_failure, we can estimate based on probability.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from app.core.database import SessionLocal
from app.models.forecast import Forecast
import random

def populate_expected_deficit():
    db = SessionLocal()
    
    try:
        forecasts = db.query(Forecast).all()
        print(f"[OK] Found {len(forecasts)} forecasts to update")
        
        updated = 0
        for forecast in forecasts:
            # Calculate expected deficit based on trigger type and probability
            if forecast.trigger_type == 'drought':
                # Drought: deficit proportional to probability
                # High probability = more severe deficit
                # Range: 10mm to 150mm
                deficit = 10 + (forecast.probability * 140)
            elif forecast.trigger_type == 'flood':
                # Flood: negative deficit (excess rainfall)
                # Range: -10mm to -100mm
                deficit = -(10 + (forecast.probability * 90))
            else:  # crop_failure
                # Crop failure: moderate deficit
                # Range: 20mm to 100mm
                deficit = 20 + (forecast.probability * 80)
            
            forecast.expected_deficit = round(float(deficit), 2)
            updated += 1
        
        db.commit()
        print(f"[SUCCESS] Updated {updated} forecasts with expected_deficit values")
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("POPULATING EXPECTED DEFICIT VALUES")
    print("=" * 60)
    populate_expected_deficit()
