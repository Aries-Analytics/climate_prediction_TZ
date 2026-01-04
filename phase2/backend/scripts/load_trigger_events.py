"""
Trigger Events Loading Script

Loads trigger events (drought, flood, crop failure) from processed data into database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.trigger_event import TriggerEvent
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tanzania coordinates (correct location)
TANZANIA_LAT = -6.369028
TANZANIA_LON = 34.888822


def load_trigger_events(
    master_csv: str = "../data/processed/merged_data_2010_2025.csv",
    clear_existing: bool = False
):
    """
    Load trigger events from master dataset.
    
    Extracts drought, flood, and crop failure triggers from the merged 2010-2025 dataset.
    """
    logger.info(f"Loading trigger events from {master_csv}")
    
    # Read CSV
    try:
        df = pd.read_csv(master_csv)
        logger.info(f"Read {len(df)} rows")
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return False
    
    db = SessionLocal()
    
    try:
        # Clear existing data if requested
        if clear_existing:
            logger.info("Clearing existing trigger events...")
            db.query(TriggerEvent).delete()
            db.commit()
            logger.info("Existing data cleared")
        
        triggers_loaded = {
            'drought': 0,
            'flood': 0,
            'crop_failure': 0
        }
        
        batch = []
        batch_size = 100
        
        for idx, row in df.iterrows():
            # Create date
            try:
                date = datetime(int(row['year']), int(row['month']), 1).date()
            except:
                continue
            
            # Extract drought triggers
            if row.get('drought_trigger') == True or row.get('drought_trigger') == 1:
                # Handle NaN values properly
                severity_val = row.get('drought_severity', 0.5)
                severity = float(severity_val) if pd.notna(severity_val) else 0.5
                
                # Skip triggers with severity below minimum threshold (10%)
                # Triggers with 0% severity don't make practical sense
                if severity < 0.1:
                    logger.debug(f"Skipping drought trigger at {date} with severity {severity:.2f} (below 10% threshold)")
                    continue
                
                # Check if exists (smart upsert)
                existing = db.query(TriggerEvent).filter(
                    TriggerEvent.date == date,
                    TriggerEvent.trigger_type == 'drought',
                    TriggerEvent.location_lat == TANZANIA_LAT,
                    TriggerEvent.location_lon == TANZANIA_LON
                ).first()
                
                confidence_val = row.get('drought_trigger_confidence', 0.8)
                confidence = float(confidence_val) if pd.notna(confidence_val) else 0.8
                
                # Calculate payout in Tanzanian Shillings (TZS)
                # Base: 500,000 TZS for drought, scaled by severity
                # Only pay out if severity >= 30% threshold (moderate drought)
                payout = float(500000 * severity) if severity >= 0.3 else 0.0
                
                if existing:
                    existing.severity = severity
                    existing.confidence = confidence
                    existing.payout_amount = payout
                else:
                    trigger = TriggerEvent(
                        date=date,
                        trigger_type='drought',
                        severity=severity,
                        confidence=confidence,
                        payout_amount=payout,
                        location_lat=TANZANIA_LAT,
                        location_lon=TANZANIA_LON,
                        location='Tanzania'  # Location name for map display
                    )
                    batch.append(trigger)
                triggers_loaded['drought'] += 1
                
                logger.debug(f"Drought trigger: {date}, severity={severity:.2f}, confidence={confidence:.2f}, payout=${payout:.2f}")
            
            # Extract flood triggers
            if row.get('flood_trigger') == True or row.get('flood_trigger') == 1:
                # Handle NaN values properly - flood_risk_score is 0-100, normalize to 0-1
                severity_val = row.get('flood_risk_score_left', row.get('flood_risk_score_right', 50.0))
                if pd.notna(severity_val):
                    severity = min(float(severity_val) / 100.0, 1.0)  # Normalize to 0-1
                else:
                    severity = 0.5
                
                # Skip triggers with severity below minimum threshold (10%)
                if severity < 0.1:
                    logger.debug(f"Skipping flood trigger at {date} with severity {severity:.2f} (below 10% threshold)")
                    continue
                
                # Check if exists (smart upsert)
                existing = db.query(TriggerEvent).filter(
                    TriggerEvent.date == date,
                    TriggerEvent.trigger_type == 'flood',
                    TriggerEvent.location_lat == TANZANIA_LAT,
                    TriggerEvent.location_lon == TANZANIA_LON
                ).first()
                
                confidence_val = row.get('flood_trigger_confidence', 0.8)
                confidence = float(confidence_val) if pd.notna(confidence_val) else 0.8
                
                # Calculate payout in Tanzanian Shillings (TZS)
                # Base: 750,000 TZS for flood, scaled by severity
                # Only pay out if severity >= 30% threshold (moderate flood risk)
                payout = float(750000 * severity) if severity >= 0.3 else 0.0
                
                if existing:
                    existing.severity = severity
                    existing.confidence = confidence
                    existing.payout_amount = payout
                else:
                    trigger = TriggerEvent(
                        date=date,
                        trigger_type='flood',
                        severity=severity,
                        confidence=confidence,
                        payout_amount=payout,
                        location_lat=TANZANIA_LAT,
                        location_lon=TANZANIA_LON,
                        location='Tanzania'  # Location name for map display
                    )
                    batch.append(trigger)
                triggers_loaded['flood'] += 1
                
                logger.debug(f"Flood trigger: {date}, severity={severity:.2f}, confidence={confidence:.2f}, payout=${payout:.2f}")
            
            # Extract crop failure triggers
            if row.get('crop_failure_trigger') == True or row.get('crop_failure_trigger') == 1:
                # Handle NaN values properly - crop_failure_risk is 0-100, normalize to 0-1
                severity_val = row.get('crop_failure_risk', 50.0)
                if pd.notna(severity_val):
                    severity = min(float(severity_val) / 100.0, 1.0)  # Normalize to 0-1
                else:
                    severity = 0.5
                
                # Skip triggers with severity below minimum threshold (10%)
                if severity < 0.1:
                    logger.debug(f"Skipping crop failure trigger at {date} with severity {severity:.2f} (below 10% threshold)")
                    continue
                
                # Check if exists (smart upsert)
                existing = db.query(TriggerEvent).filter(
                    TriggerEvent.date == date,
                    TriggerEvent.trigger_type == 'crop_failure',
                    TriggerEvent.location_lat == TANZANIA_LAT,
                    TriggerEvent.location_lon == TANZANIA_LON
                ).first()
                
                confidence_val = row.get('crop_failure_trigger_confidence', 0.8)
                # Handle 0.0 confidence - use default
                if pd.notna(confidence_val) and float(confidence_val) > 0:
                    confidence = float(confidence_val)
                else:
                    confidence = 0.75  # Default confidence for crop failure
                
                # Calculate payout in Tanzanian Shillings (TZS)
                # Base: 625,000 TZS for crop failure, scaled by severity
                # Only pay out if severity >= 30% threshold (moderate crop stress)
                payout = float(625000 * severity) if severity >= 0.3 else 0.0
                
                if existing:
                    existing.severity = severity
                    existing.confidence = confidence
                    existing.payout_amount = payout
                else:
                    trigger = TriggerEvent(
                        date=date,
                        trigger_type='crop_failure',
                        severity=severity,
                        confidence=confidence,
                        payout_amount=payout,
                        location_lat=TANZANIA_LAT,
                        location_lon=TANZANIA_LON,
                        location='Tanzania'  # Location name for map display
                    )
                    batch.append(trigger)
                triggers_loaded['crop_failure'] += 1
                
                logger.debug(f"Crop failure trigger: {date}, severity={severity:.2f}, confidence={confidence:.2f}, payout=${payout:.2f}")
            
            # Bulk insert when batch is full
            if len(batch) >= batch_size:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
        
        # Insert remaining records
        if batch:
            db.bulk_save_objects(batch)
            db.commit()
        
        logger.info(f"✓ Loaded trigger events:")
        logger.info(f"  - Drought: {triggers_loaded['drought']}")
        logger.info(f"  - Flood: {triggers_loaded['flood']}")
        logger.info(f"  - Crop Failure: {triggers_loaded['crop_failure']}")
        logger.info(f"  - Total: {sum(triggers_loaded.values())}")
        
        # Verification
        total_count = db.query(TriggerEvent).count()
        logger.info(f"✓ Total trigger events in database: {total_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error loading trigger events: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load trigger events into dashboard database")
    parser.add_argument("--csv", default="../data/processed/merged_data_2010_2025.csv", help="Path to master CSV")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before loading")
    
    args = parser.parse_args()
    
    success = load_trigger_events(args.csv, args.clear)
    sys.exit(0 if success else 1)
