"""
Script to clean up old records with incorrect Kenya coordinates
Run this once to remove duplicate records from the database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.climate_data import ClimateData
from app.models.trigger_event import TriggerEvent

# Old Kenya coordinates (incorrect)
KENYA_LAT = -1.2921
KENYA_LON = 36.8219

# Tanzania coordinates (correct - precise)
TANZANIA_LAT_PRECISE = -6.369028
TANZANIA_LON_PRECISE = 34.888822

# Tanzania coordinates (rounded - old version)
TANZANIA_LAT_ROUNDED = -6.369000
TANZANIA_LON_ROUNDED = 34.888800

def cleanup_old_coordinates():
    """Remove records with old Kenya coordinates"""
    print("=" * 60)
    print("Cleaning Up Old Kenya Coordinates")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Count records with old Kenya coordinates
        kenya_climate = db.query(ClimateData).filter(
            ClimateData.location_lat == KENYA_LAT,
            ClimateData.location_lon == KENYA_LON
        ).count()
        
        kenya_triggers = db.query(TriggerEvent).filter(
            TriggerEvent.location_lat == KENYA_LAT,
            TriggerEvent.location_lon == KENYA_LON
        ).count()
        
        # Count records with rounded Tanzania coordinates (old version)
        rounded_climate = db.query(ClimateData).filter(
            ClimateData.location_lat == TANZANIA_LAT_ROUNDED,
            ClimateData.location_lon == TANZANIA_LON_ROUNDED
        ).count()
        
        rounded_triggers = db.query(TriggerEvent).filter(
            TriggerEvent.location_lat == TANZANIA_LAT_ROUNDED,
            TriggerEvent.location_lon == TANZANIA_LON_ROUNDED
        ).count()
        
        # Count records with precise Tanzania coordinates (correct)
        precise_climate = db.query(ClimateData).filter(
            ClimateData.location_lat == TANZANIA_LAT_PRECISE,
            ClimateData.location_lon == TANZANIA_LON_PRECISE
        ).count()
        
        precise_triggers = db.query(TriggerEvent).filter(
            TriggerEvent.location_lat == TANZANIA_LAT_PRECISE,
            TriggerEvent.location_lon == TANZANIA_LON_PRECISE
        ).count()
        
        print(f"\nCurrent database status:")
        print(f"\nKenya coordinates (incorrect):")
        print(f"  - Climate records: {kenya_climate}")
        print(f"  - Trigger events: {kenya_triggers}")
        print(f"\nTanzania coordinates - Rounded (old):")
        print(f"  - Climate records: {rounded_climate}")
        print(f"  - Trigger events: {rounded_triggers}")
        print(f"\nTanzania coordinates - Precise (correct):")
        print(f"  - Climate records: {precise_climate}")
        print(f"  - Trigger events: {precise_triggers}")
        
        total_to_clean = kenya_climate + kenya_triggers + rounded_climate + rounded_triggers
        
        if total_to_clean == 0:
            print("\n✓ No old or duplicate records found. Database is clean!")
            return
        
        print(f"\n⚠️  Found {total_to_clean} records with old/incorrect coordinates")
        print("These are duplicates that should be removed.")
        
        response = input("\nDo you want to delete the old/duplicate records? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Cancelled. No changes made.")
            return
        
        # Delete old records
        print("\nDeleting old/duplicate records...")
        
        deleted_kenya_climate = db.query(ClimateData).filter(
            ClimateData.location_lat == KENYA_LAT,
            ClimateData.location_lon == KENYA_LON
        ).delete()
        
        deleted_kenya_triggers = db.query(TriggerEvent).filter(
            TriggerEvent.location_lat == KENYA_LAT,
            TriggerEvent.location_lon == KENYA_LON
        ).delete()
        
        deleted_rounded_climate = db.query(ClimateData).filter(
            ClimateData.location_lat == TANZANIA_LAT_ROUNDED,
            ClimateData.location_lon == TANZANIA_LON_ROUNDED
        ).delete()
        
        deleted_rounded_triggers = db.query(TriggerEvent).filter(
            TriggerEvent.location_lat == TANZANIA_LAT_ROUNDED,
            TriggerEvent.location_lon == TANZANIA_LON_ROUNDED
        ).delete()
        
        db.commit()
        
        total_deleted = deleted_kenya_climate + deleted_kenya_triggers + deleted_rounded_climate + deleted_rounded_triggers
        
        print(f"\n✓ Deleted {deleted_kenya_climate} Kenya climate records")
        print(f"✓ Deleted {deleted_kenya_triggers} Kenya trigger events")
        print(f"✓ Deleted {deleted_rounded_climate} rounded Tanzania climate records")
        print(f"✓ Deleted {deleted_rounded_triggers} rounded Tanzania trigger events")
        print(f"\nTotal deleted: {total_deleted} records")
        
        # Show final counts
        final_climate = db.query(ClimateData).count()
        final_triggers = db.query(TriggerEvent).count()
        
        print("\n" + "=" * 60)
        print("Cleanup Complete!")
        print("=" * 60)
        print(f"Remaining climate records: {final_climate}")
        print(f"Remaining trigger events: {final_triggers}")
        print("\n✓ All records now use correct Tanzania coordinates!")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_old_coordinates()
