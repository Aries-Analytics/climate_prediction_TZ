"""
Seed script to populate the locations table with monitored locations in Tanzania.

Run this after creating the database tables.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.location import Location

# 6 monitored locations in Tanzania
LOCATIONS = [
    {
        "name": "Arusha",
        "latitude": -3.3869,
        "longitude": 36.6830,
        "region": "Arusha",
        "population": 416442,
        "climate_zone": "Temperate"
    },
    {
        "name": "Dar es Salaam",
        "latitude": -6.7924,
        "longitude": 39.2083,
        "region": "Coastal",
        "population": 4364541,
        "climate_zone": "Tropical"
    },
    {
        "name": "Dodoma",
        "latitude": -6.1630,
        "longitude": 35.7516,
        "region": "Central",
        "population": 410956,
        "climate_zone": "Semi-arid"
    },
    {
        "name": "Mbeya",
        "latitude": -8.9094,
        "longitude": 33.4606,
        "region": "Highlands",
        "population": 385279,
        "climate_zone": "Highland"
    },
    {
        "name": "Mwanza",
        "latitude": -2.5164,
        "longitude": 32.9175,
        "region": "Lake",
        "population": 706453,
        "climate_zone": "Tropical"
    },
    {
        "name": "Morogoro",
        "latitude": -6.8211,
        "longitude": 37.6595,
        "region": "Eastern",
        "population": 315866,
        "climate_zone": "Tropical"
    }
]


def seed_locations(db: Session):
    """Seed the locations table with monitored locations."""
    print("=" * 60)
    print("Seeding Locations Table")
    print("=" * 60)
    
    # Check if locations already exist
    existing_count = db.query(Location).count()
    if existing_count > 0:
        print(f"\n⚠️  {existing_count} locations already exist in database")
        response = input("Do you want to clear and reseed? (y/N): ")
        if response.lower() != 'y':
            print("Skipping seed.")
            return
        
        # Delete existing locations
        db.query(Location).delete()
        db.commit()
        print("✓ Cleared existing locations")
    
    # Insert locations
    print(f"\nInserting {len(LOCATIONS)} locations...")
    locations_added = []
    
    for loc_data in LOCATIONS:
        location = Location(**loc_data)
        db.add(location)
        locations_added.append(loc_data['name'])
        print(f"  + {loc_data['name']} ({loc_data['latitude']:.4f}, {loc_data['longitude']:.4f})")
    
    db.commit()
    
    print(f"\n✓ Successfully added {len(locations_added)} locations:")
    for name in locations_added:
        print(f"  - {name}")
    
    print("\n" + "=" * 60)
    print("Locations Seeding Complete!")
    print("=" * 60)


def main():
    """Main function."""
    # Create tables if they don't exist
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created/verified")
    
    # Create database session
    db = SessionLocal()
    
    try:
        seed_locations(db)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
