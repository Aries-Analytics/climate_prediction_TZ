"""
Script to fix trigger event data with proper payouts
"""
import sys
import os
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.trigger_event import TriggerEvent

def load_trigger_events(db: Session):
    """Load trigger events from insurance triggers CSV"""
    print("Loading trigger events...")
    
    # Read the triggers CSV
    df = pd.read_csv('../outputs/business_reports/insurance_triggers_detailed.csv')
    
    # Convert date column
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter only main trigger types
    main_triggers = df[df['trigger_type'].isin(['Drought', 'Flood', 'Crop Failure'])].copy()
    
    # Remove duplicates (keep first occurrence per date/type)
    main_triggers = main_triggers.drop_duplicates(subset=['date', 'trigger_type'], keep='first')
    
    print(f"Loading {len(main_triggers)} trigger events...")
    
    records_added = 0
    for _, row in main_triggers.iterrows():
        # Parse confidence (remove % and convert)
        confidence_str = str(row['confidence']).replace('%', '')
        try:
            confidence = float(confidence_str) / 100.0
        except:
            confidence = 0.0
        
        # Calculate payout based on severity and trigger type
        severity = float(row['severity'])
        trigger_type = row['trigger_type'].lower()
        
        # Realistic base payouts for Tanzania (in TZS, converted to USD equivalent)
        # Tanzania agricultural insurance typical payouts
        base_payouts = {
            'drought': 25000,      # Drought affects larger areas, higher base
            'flood': 35000,        # Flood damage can be severe
            'crop failure': 20000  # Direct crop loss
        }
        
        base_payout = base_payouts.get(trigger_type, 25000)
        # Only pay out if severity exceeds 30% threshold
        payout = base_payout * severity if severity > 0.3 else 0
        
        trigger_event = TriggerEvent(
            date=row['date'].date(),
            trigger_type=row['trigger_type'].lower().replace(' ', '_'),
            confidence=confidence,
            severity=severity,
            payout_amount=payout,
            location_lat=-6.3690,  # Tanzania coordinates (Dodoma)
            location_lon=34.8888
        )
        db.add(trigger_event)
        records_added += 1
        
        if records_added % 50 == 0:
            db.commit()
            print(f"  Added {records_added} events...")
    
    db.commit()
    print(f"✓ Loaded {records_added} trigger events")

def main():
    """Main function to load all data"""
    print("=" * 60)
    print("Fixing Trigger Event Data")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Clear existing trigger events
        print("\nClearing existing trigger events...")
        db.query(TriggerEvent).delete()
        db.commit()
        print("✓ Cleared existing data")
        
        # Load data
        load_trigger_events(db)
        
        # Print summary
        print("\n" + "=" * 60)
        print("Data Loading Complete!")
        print("=" * 60)
        
        trigger_count = db.query(TriggerEvent).count()
        print(f"\nFinal counts:")
        print(f"  - Trigger events: {trigger_count}")
        
    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
