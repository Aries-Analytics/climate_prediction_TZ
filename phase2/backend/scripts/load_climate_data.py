"""
Climate Data Loading Script

Loads processed climate data from master_dataset.csv into the dashboard database.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.climate_data import ClimateData
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tanzania coordinates (correct location)
TANZANIA_LAT = -6.369028
TANZANIA_LON = 34.888822


def load_climate_data(csv_path: str = "../data/processed/merged_data_2010_2025.csv", clear_existing: bool = False):
    """
    Load climate data from CSV into database.
    
    Args:
        csv_path: Path to merged_data_2010_2025.csv (2010-2025 dataset)
        clear_existing: If True, truncate table before loading
    """
    logger.info(f"Loading climate data from {csv_path}")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Read {len(df)} rows with {len(df.columns)} columns")
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return False
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data if requested
        if clear_existing:
            logger.info("Clearing existing climate data...")
            db.query(ClimateData).delete()
            db.commit()
            logger.info("Existing data cleared")
        
        # Transform and load data
        records_loaded = 0
        batch_size = 100
        batch = []
        
        for idx, row in df.iterrows():
            # Create date from year and month
            try:
                date = datetime(int(row['year']), int(row['month']), 1).date()
            except:
                logger.warning(f"Skipping row {idx}: invalid date")
                continue
            
            # Use per-row lat/lon if available (multi-location datasets)
            row_lat = float(row.get('latitude', row.get('location_lat', TANZANIA_LAT)))
            row_lon = float(row.get('longitude', row.get('location_lon', TANZANIA_LON)))

            # Check if record exists (smart upsert)
            existing = db.query(ClimateData).filter(
                ClimateData.date == date,
                ClimateData.location_lat == row_lat,
                ClimateData.location_lon == row_lon
            ).first()

            if existing:
                # Update existing record
                existing.temperature_avg = row.get('temp_mean_c')
                existing.rainfall_mm = row.get('rainfall_mm', row.get('precip_mm'))
                existing.ndvi = row.get('ndvi')
                existing.enso_index = row.get('oni')
                existing.iod_index = row.get('iod')
            else:
                # Create new ClimateData record
                record = ClimateData(
                    date=date,
                    location_lat=row_lat,
                    location_lon=row_lon,
                    temperature_avg=row.get('temp_mean_c'),
                    rainfall_mm=row.get('rainfall_mm', row.get('precip_mm')),
                    ndvi=row.get('ndvi'),
                    enso_index=row.get('oni'),
                    iod_index=row.get('iod')
                )
                batch.append(record)
            
            # Bulk insert when batch is full
            if len(batch) >= batch_size:
                db.bulk_save_objects(batch)
                db.commit()
                records_loaded += len(batch)
                logger.info(f"Loaded {records_loaded} records...")
                batch = []
        
        # Insert remaining records
        if batch:
            db.bulk_save_objects(batch)
            db.commit()
            records_loaded += len(batch)
        
        logger.info(f"✓ Successfully loaded {records_loaded} climate data records")
        
        # Verification
        total_count = db.query(ClimateData).count()
        logger.info(f"✓ Total records in database: {total_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load climate data into dashboard database")
    parser.add_argument("--csv", default="../data/processed/merged_data_2010_2025.csv", help="Path to CSV file")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before loading")
    
    args = parser.parse_args()
    
    success = load_climate_data(args.csv, args.clear)
    sys.exit(0 if success else 1)
