"""
One-time migration script to update old Kenya coordinates to Tanzania coordinates
Run this once to fix any existing data with Kenya coordinates
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.climate_data import ClimateData
from app.models.trigger_event import TriggerEvent

# Old Kenya coordinates
KENYA_LAT = -1.2921
KENYA_LON = 36.8219

# New Tanzania coordinates
TANZANIA_LAT = -6.369028
TANZANIA_LON = 34.888822

def migrate_coordinates():
    """Update all Kenya coordinates to Tanzania coordinates"""
    print("=" * 60)
    print("Migrating Kenya Coordinates to Tanzania")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Update climate data
        climate_updated = db.query(ClimateData).filter(
            ClimateData.location_lat == KENYA_LAT,
            ClimateData.location_lon == KENYA_LON
        ).update({
            'location_lat': TANZANIA_LAT,
            'location_lon': TANZANIA_LON
        })
        
        # Update trigger events
        trigger_updated = db.query(TriggerEvent).filter(
            TriggerEvent.location_lat == KENYA_LAT,
            TriggerEvent.location_lon == KENYA_LON
        ).update({
            'location_lat': TANZANIA_LAT,
            'location_lon': TANZANIA_LON
        })
        
        db.commit()
        
        print(f"\n✓ Updated {climate_updated} climate records")
        print(f"✓ Updated {trigger_updated} trigger events")
        print("\nMigration complete!")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_coordinates()
