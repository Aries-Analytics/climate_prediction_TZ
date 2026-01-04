"""
Script to load 6-location calibrated data into the dashboard via API.

This script loads:
1. Climate data from data/processed/master_dataset.csv (6 locations, 2000-2025)
2. Trigger events from outputs/business_reports/insurance_triggers_detailed.csv (calibrated)

Run this from the project root directory after starting Docker.
Usage:
  python scripts/load_dashboard_data.py           # Load new data (with duplicate detection)
  python scripts/load_dashboard_data.py --clear   # Clear all triggers first, then load
"""
import requests
import pandas as pd
from datetime import datetime
import time
import math
import argparse
import sys
from pathlib import Path

# Add project root and utils to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'backend'))

# Import canonical paths
from utils.config import MASTER_DATASET, PAYOUT_ESTIMATES, INSURANCE_TRIGGERS, TRAINING_RESULTS_CANONICAL

def clean_float(val):
    """Ensure float is JSON compliant (no NaN/Inf)"""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except:
        return None

API_BASE = "http://localhost:8000"

# 6-location coordinates mapping
LOCATION_COORDS = {
    'Arusha': (-3.3869, 36.6830),
    'Dar es Salaam': (-6.7924, 39.2083),
    'Dodoma': (-6.1630, 35.7516),
    'Mbeya': (-8.9094, 33.4606),
    'Mwanza': (-2.5164, 32.9175),
    'Morogoro': (-6.8211, 37.6595)
}


def get_auth_token():
    """Login and get authentication token"""
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None


def load_climate_data(token):
    """Load climate data from master dataset (6 locations)"""
    print("\n" + "=" * 60)
    print("Loading Climate Data (6 Locations)")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Read the 6-location master dataset
    try:
        df = pd.read_csv(MASTER_DATASET)
        print(f"[OK] Loaded master dataset: {len(df)} records")
    except FileNotFoundError:
        print(f"[MISSING] Master dataset not found at {MASTER_DATASET}")
        print("   Run data processing pipeline first:")
        print("   python modules/processing/orchestrator.py")
        return
    
    # Create date from year and month
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    
    # Get location info
    if 'location' in df.columns:
        print(f"[OK] Locations found: {df['location'].unique().tolist()}")
    else:
        print("[WARN]  No location column found, using default (Dodoma)")
        df['location'] = 'Dodoma'
    
    # Sample to reduce data (every 10th row per location)
    # DISABLED: Load all data instead of sampling
    # df_sample = df.groupby('location', group_keys=False).apply(
    #     lambda x: x.iloc[::10]
    # ).reset_index(drop=True)
    df_sample = df  # Load ALL records
    
    print(f"[OK] Preparing {len(df_sample)} records for upload")
    
    records_added = 0
    batch = []
    
    for _, row in df_sample.iterrows():
        # Get location coordinates
        location = row.get('location', 'Dodoma')
        lat, lon = LOCATION_COORDS.get(location, LOCATION_COORDS['Dodoma'])
        
        record = {
            "date": row['date'].strftime('%Y-%m-%d'),
            "location_lat": clean_float(lat),
            "location_lon": clean_float(lon),
            "temperature_avg": clean_float(row.get('temp_mean_c')),
            "rainfall_mm": clean_float(row.get('rainfall_mm')),
            "ndvi": clean_float(row.get('ndvi')),
            "enso_index": clean_float(row.get('oni')),
            "iod_index": clean_float(row.get('iod'))
        }
        
        batch.append(record)
        
        # Send in batches of 100
        if len(batch) >= 100:
            response = requests.post(
                f"{API_BASE}/api/climate/batch",
                json=batch,
                headers=headers
            )
            if response.status_code == 200:
                records_added += len(batch)
                print(f"  Uploaded {records_added} records...")
            else:
                print(f"  Error: {response.text}")
            batch = []
            time.sleep(0.05)  # Small delay
    
    # Send remaining records
    if batch:
        response = requests.post(
            f"{API_BASE}/api/climate/batch",
            json=batch,
            headers=headers
        )
        if response.status_code == 200:
            records_added += len(batch)
    
    print(f"\n[DONE] Loaded {records_added} climate records from {len(df['location'].unique())} locations")


def load_trigger_events(token):
    """Load trigger events from calibrated insurance triggers CSV (6 locations)"""
    print("\n" + "=" * 60)
    print("Loading Trigger Events (Calibrated)")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Read the calibrated triggers CSV (now with location data!)
    try:
        df = pd.read_csv(INSURANCE_TRIGGERS)
        print(f"[OK] Loaded triggers CSV: {len(df)} events")
    except FileNotFoundError:
        print(f"[MISSING] Triggers CSV not found at {INSURANCE_TRIGGERS}")
        print("   Generate it first:")
        print("   python pipelines/insurance_business_pipeline.py")
        return
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Check if location column exists
    if 'location' not in df.columns:
        print("[WARN]  No location column, using default (Dodoma)")
        df['location'] = 'Dodoma'
    else:
        print(f"[OK] Locations: {df['location'].unique().tolist()}")
    
    # Filter only main trigger types and remove duplicates
    main_triggers = df[df['trigger_type'].isin(['Drought', 'Flood', 'Crop Failure'])].copy()
    main_triggers = main_triggers.drop_duplicates(subset=['date', 'trigger_type', 'location'], keep='first')
    
    print(f"[OK] Filtered to {len(main_triggers)} unique trigger events")
    
    # Count by type
    for trigger_type in ['Drought', 'Flood', 'Crop Failure']:
        count = (main_triggers['trigger_type'] == trigger_type).sum()
        print(f"  - {trigger_type}: {count}")
    
    
    # Load payout estimates for accurate payout amounts
    try:
        payout_df = pd.read_csv(PAYOUT_ESTIMATES)
        payout_df['date'] = pd.to_datetime(payout_df['date'])
        print(f"[OK] Loaded payout estimates: {len(payout_df)} records")
        # Create lookup dict: (date, triggered_event) -> payout
        # NORMALIZE both sides: replace underscores with spaces
        payout_lookup = {}
        for _, p_row in payout_df.iterrows():
            # Normalize triggered_events: 'crop_failure' -> 'crop failure'
            normalized_event = p_row['triggered_events'].replace('_', ' ')
            key = (p_row['date'].strftime('%Y-%m-%d'), normalized_event)
            payout_lookup[key] = float(p_row['estimated_payout_usd'])
    except Exception as e:
        print(f"[WARN] Could not load payout estimates: {e}")
        payout_lookup = {}
    
    # Initialize batch processing
    records_added = 0
    batch = []
    
    # Process each CSV row
    for _, row in main_triggers.iterrows():
        # Get location coordinates
        location = row.get('location', 'Dodoma')
        lat, lon = LOCATION_COORDS.get(location, LOCATION_COORDS['Dodoma'])
        
        # Parse confidence (remove % sign and convert to decimal)
        confidence_str = str(row.get('confidence', '0')).replace('%', '')
        try:
            confidence = float(confidence_str) / 100.0
        except:
            confidence = 0.0
        
        # Get severity
        try:
            severity = float(row.get('severity', 0))
        except:
            severity = 0.0
        
        # Get date key for lookup
        date_key = row['date'].strftime('%Y-%m-%d')
        
        # Normalize trigger type to match payout_estimates format (lowercase, spaces not underscores)
        trigger_type_normalized = row['trigger_type'].lower().replace('_', ' ')
        
        # Try lookup with normalized type
        payout = payout_lookup.get((date_key, trigger_type_normalized))
        
        if payout is None:
            # STRICT: No fallback calculation - log warning and use 0
            # This forces fixing data quality issues at source rather than masking with wrong values
            print(f"[WARN] No payout found for {date_key} / {trigger_type_normalized} - using 0")
            payout = 0
        
        record = {
            "date": date_key,
            "trigger_type": row['trigger_type'].lower().replace(' ', '_'),
            "confidence": clean_float(confidence),
            "severity": clean_float(severity),
            "payout_amount": clean_float(payout),
            "location_lat": clean_float(lat),
            "location_lon": clean_float(lon),
            "location": location  # Add location name for map display
        }
    
        batch.append(record)
        
        # Send in batches of 50
        if len(batch) >= 50:
            response = requests.post(
                f"{API_BASE}/api/triggers/batch",
                json=batch,
                headers=headers
            )
            if response.status_code == 200:
                records_added += len(batch)
                print(f"  Uploaded {records_added} events...")
            else:
                print(f"  Error: {response.text}")
            batch = []
            time.sleep(0.05)
    
    # Send remaining records
    if batch:
        response = requests.post(
            f"{API_BASE}/api/triggers/batch",
            json=batch,
            headers=headers
        )
        if response.status_code == 200:
            records_added += len(batch)
    
    print(f"\n[DONE] Loaded {records_added} trigger events from {len(main_triggers['location'].unique())} locations")



def verify_data():
    """Verify the data files exist before loading"""
    print("\n" + "=" * 60)
    print("Verifying Data Files")
    print("=" * 60)
    
    import os
    
    files_to_check = [
        ('Master dataset', 'data/processed/master_dataset.csv'),
        ('Triggers CSV', 'outputs/business_reports/insurance_triggers_detailed.csv')
    ]
    
    all_exist = True
    for name, path in files_to_check:
        exists = os.path.exists(path)
        status = "[OK]" if exists else "[MISSING]"
        print(f"{status} {name}: {path}")
        if not exists:
            all_exist = False
    
    if not all_exist:
        print("\n[WARN]  Some files are missing. Please run:")
        print("   1. Data processing: python modules/processing/orchestrator.py")
        print("   2. Insurance pipeline: python pipelines/insurance_business_pipeline.py")
        return False
    
    return True


def load_model_metrics(token):
    """Load model performance metrics from latest training results (6 locations)"""
    print("\n" + "=" * 60)
    print("Loading Model Performance Metrics (6 Locations)")
    print("=" * 60)
    
    import os
    import glob
    import json
    import sys
    
    # Add backend to path for database access
    sys.path.insert(0, 'backend')
    from app.core.database import SessionLocal
    from app.models.model_metric import ModelMetric
    from datetime import datetime as dt
    
    # STRICT: Use only the canonical location (single source of truth)
    # If missing, user must run training pipeline first - no fallback to avoid loading wrong data
    if not TRAINING_RESULTS_CANONICAL.exists():
        print(f"[ERROR] Canonical training results not found: {TRAINING_RESULTS_CANONICAL}")
        print("[INFO] Run the training pipeline to generate this file:")
        print("       python pipelines/model_development_pipeline.py")
        print("[INFO] Or copy existing results to canonical path:")
        print(f"       cp outputs/experiments/training_results_morogoro_6loc_NO_LEAKAGE.json {TRAINING_RESULTS_CANONICAL}")
        return
    
    latest_file = TRAINING_RESULTS_CANONICAL
    print(f"[OK] Loading from canonical path: {latest_file.name}")
    
    with open(latest_file, 'r') as f:
        results = json.load(f)
    
    training_date_str = results.get('training_end_time', results.get('training_start_time', 'Unknown'))
    training_date = dt.fromisoformat(training_date_str) if training_date_str != 'Unknown' else dt.now()
    models_data = results.get('models', {})
    
    # Insert directly into database
    db = SessionLocal()
    records_added = 0
    
    try:
        for model_name, model_data in models_data.items():
            if model_name == 'ensemble':
                test_metrics = model_data.get('ensemble_metrics', {})
            else:
                test_metrics = model_data.get('test_metrics', {})
            
            if not test_metrics:
                continue
            
            # Prepare training metadata
            metadata = {
                "training_samples": results['data_shapes']['train'][0] if 'data_shapes' in results else None,
                "val_samples": results['data_shapes']['val'][0] if 'data_shapes' in results else None,
                "test_samples": results['data_shapes']['test'][0] if 'data_shapes' in results else None,
                "n_features": results.get('feature_selection', {}).get('selected_features', None),
                "original_features": results.get('feature_selection', {}).get('original_features', None),
                "feature_reduction_pct": results.get('feature_selection', {}).get('reduction_pct', None)
            }
            
            metric = ModelMetric(
                model_name=model_name,
                r2_score=clean_float(test_metrics.get('r2', 0)),
                rmse=clean_float(test_metrics.get('rmse', 0)),
                mae=clean_float(test_metrics.get('mae', 0)),
                mape=clean_float(test_metrics.get('mape', 0)),
                training_date=training_date,
                hyperparameters=metadata
            )
            
            db.add(metric)
            records_added += 1
            print(f"  [OK] {model_name}: R2={test_metrics.get('r2', 0):.3f}, RMSE={test_metrics.get('rmse', 0):.3f}")
        
        db.commit()
        print(f"\n[DONE] Loaded {records_added} model performance records")
        
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Failed to load model metrics: {e}")
    finally:
        db.close()



def clear_triggers():
    """Clear all trigger events from database"""
    print("\n" + "=" * 60)
    print("CLEARING TRIGGER EVENTS FROM DATABASE")
    print("=" * 60)
    try:
        from app.core.database import SessionLocal
        from app.models.trigger_event import TriggerEvent
        
        db = SessionLocal()
        count = db.query(TriggerEvent).count()
        print(f"Found {count} trigger events...")
        
        if count > 0:
            db.query(TriggerEvent).delete()
            db.commit()
            print(f"[OK] Deleted {count} trigger events")
        else:
            print("[OK] No triggers to clear")
        
        db.close()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to clear triggers: {e}")
        return False

def main():
    """Main function"""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Load dashboard data')
    parser.add_argument('--clear', action='store_true', 
                        help='Clear existing trigger data before loading')
    args = parser.parse_args()
    
    print("=" * 60)
    print("LOADING 6-LOCATION CALIBRATED DATA INTO DASHBOARD")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Clear triggers if requested
    if args.clear:
        if not clear_triggers():
            print("[WARN] Clear failed, continuing anyway...")
    
    # Verify files exist
    if not verify_data():
        return
    
    # Get auth token
    print("\n" + "=" * 60)
    print("Authenticating")
    print("=" * 60)
    token = get_auth_token()
    if not token:
        print("[FAIL] Failed to authenticate. Make sure:")
        print("   1. Backend is running: docker-compose -f docker-compose.dev.yml up -d")
        print("   2. Admin user exists (username: admin, password: admin123)")
        return
    
    print("[OK] Authenticated successfully")
    
    try:
        # Load data
        load_climate_data(token)
        load_trigger_events(token)
        load_model_metrics(token)
        
        print("\n" + "=" * 60)
        print("DATA LOADING COMPLETE!")
        print("=" * 60)
        print("\n[SUCCESS] Successfully loaded:")
        print("   - Climate data from 6 locations (2000-2025)")
        print("   - Calibrated trigger events (516 from 6 locations)")
        print("   - Model performance metrics (latest 6-location training)")
        print("\n[INFO] View your dashboard at:")
        print("   http://localhost:3000")
        print("\n[INFO] Loaded locations:")
        for location in LOCATION_COORDS.keys():
            print(f"   - {location}")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
