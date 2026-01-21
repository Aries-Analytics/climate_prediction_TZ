"""
Fill climate data gap for testing forecast generation.

Forward-fills climate data from 2025-12-01 to today using last known values.
This is a testing utility - production will use the automated pipeline.

Usage:
    python scripts/fill_climate_data_gap.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from app.core.database import SessionLocal
from app.models.climate_data import ClimateData

def fill_gap():
    """Forward-fill climate data from last date to today"""
    db = SessionLocal()
    
    try:
        # Get the last date in database
        last_record = db.query(ClimateData).order_by(ClimateData.date.desc()).first()
        
        if not last_record:
            print("[ERROR] No climate data found in database!")
            return
        
        last_date = last_record.date
        today = datetime.now().date()
        
        print(f"[OK] Last climate data date: {last_date}")
        print(f"[OK] Today: {today}")
        
        if last_date >= today:
            print("[OK] No gap to fill - data is up to date!")
            return
        
        gap_days = (today - last_date).days
        print(f"[WARN] Gap: {gap_days} days")
        
        # Get all unique locations from last date
        last_date_records = db.query(ClimateData).filter(
            ClimateData.date == last_date
        ).all()
        
        print(f"[OK] Found {len(last_date_records)} locations")
        
        # Forward-fill for each location
        records_added = 0
        current_date = last_date + timedelta(days=1)
        
        while current_date <= today:
            for record in last_date_records:
                # Create new record with same values
                new_record = ClimateData(
                    date=current_date,
                    location_lat=record.location_lat,
                    location_lon=record.location_lon,
                    temperature_avg=record.temperature_avg,
                    rainfall_mm=record.rainfall_mm,
                    ndvi=record.ndvi,
                    enso_index=record.enso_index,
                    iod_index=record.iod_index
                )
                db.add(new_record)
                records_added += 1
            
            # Commit every 10 days
            if (current_date - last_date).days % 10 == 0:
                db.commit()
                print(f"  [OK] Filled through {current_date} ({records_added} records)")
            
            current_date += timedelta(days=1)
        
        # Final commit
        db.commit()
        
        print(f"\n[SUCCESS]")
        print(f"   Added {records_added} climate records")
        print(f"   Filled gap from {last_date + timedelta(days=1)} to {today}")
        print(f"\n[INFO] You can now generate forecasts!")
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("FILLING CLIMATE DATA GAP FOR TESTING")
    print("=" * 60)
    fill_gap()
