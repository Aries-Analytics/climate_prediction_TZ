
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.location import Location

# Ensure we can import app modules
sys.path.append(os.getcwd())

def seed_locations():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if locations exist
        count = db.query(Location).count()
        if count > 0:
            print(f"Database already has {count} locations.")
            return

        # Create Morogoro pilot location
        morogoro = Location(
            name="Morogoro",
            region="Morogoro",
            latitude=-6.8278,
            longitude=37.6591
        )
        db.add(morogoro)
        db.commit()
        print("✅ Successfully seeded 'Morogoro' location.")
        
    except Exception as e:
        print(f"❌ Failed to seed seeds: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_locations()
