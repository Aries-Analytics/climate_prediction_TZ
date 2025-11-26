"""
Script to load sample data into the dashboard via API
Run this from the project root directory
"""
import requests
import pandas as pd
from datetime import datetime
import time

API_BASE = "http://localhost:8000"

# Login to get token
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
    """Load climate data from master dataset"""
    print("Loading climate data...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Read the features dataset (has more data)
    df = pd.read_csv('outputs/processed/features_train.csv')
    
    # Create date from year and month
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    
    # Sample every 20th row to avoid too much data
    df_sample = df.iloc[::20].copy()
    
    print(f"Uploading {len(df_sample)} climate records...")
    
    records_added = 0
    batch = []
    
    for _, row in df_sample.iterrows():
        record = {
            "date": row['date'].strftime('%Y-%m-%d'),
            "location_lat": -1.2921,
            "location_lon": 36.8219,
            "temperature_avg": float(row.get('temperature_2m_mean', 0)) if pd.notna(row.get('temperature_2m_mean')) else None,
            "rainfall_mm": float(row.get('rainfall_mm', 0)) if pd.notna(row.get('rainfall_mm')) else None,
            "ndvi": float(row.get('ndvi_mean', 0)) if pd.notna(row.get('ndvi_mean')) else None,
            "enso_index": float(row.get('nino34', 0)) if pd.notna(row.get('nino34')) else None,
            "iod_index": float(row.get('dmi', 0)) if pd.notna(row.get('dmi')) else None
        }
        
        batch.append(record)
        
        # Send in batches of 50
        if len(batch) >= 50:
            response = requests.post(
                f"{API_BASE}/api/climate/batch",
                json=batch,
                headers=headers
            )
            if response.status_code == 200:
                records_added += len(batch)
                print(f"  Added {records_added} records...")
            else:
                print(f"  Error: {response.text}")
            batch = []
            time.sleep(0.1)  # Small delay to avoid overwhelming the API
    
    # Send remaining records
    if batch:
        response = requests.post(
            f"{API_BASE}/api/climate/batch",
            json=batch,
            headers=headers
        )
        if response.status_code == 200:
            records_added += len(batch)
    
    print(f"✓ Loaded {records_added} climate records")

def load_trigger_events(token):
    """Load trigger events from insurance triggers CSV"""
    print("Loading trigger events...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Read the triggers CSV
    df = pd.read_csv('outputs/business_reports/insurance_triggers_detailed.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter only main trigger types
    main_triggers = df[df['trigger_type'].isin(['Drought', 'Flood', 'Crop Failure'])].copy()
    main_triggers = main_triggers.drop_duplicates(subset=['date', 'trigger_type'], keep='first')
    
    print(f"Uploading {len(main_triggers)} trigger events...")
    
    records_added = 0
    batch = []
    
    for _, row in main_triggers.iterrows():
        # Parse confidence
        confidence_str = str(row['confidence']).replace('%', '')
        try:
            confidence = float(confidence_str) / 100.0
        except:
            confidence = 0.0
        
        # Calculate payout
        severity = float(row['severity'])
        base_payout = 10000
        payout = base_payout * severity if severity > 0.3 else 0
        
        record = {
            "date": row['date'].strftime('%Y-%m-%d'),
            "trigger_type": row['trigger_type'].lower().replace(' ', '_'),
            "confidence": confidence,
            "severity": severity,
            "payout_amount": payout,
            "location_lat": -1.2921,
            "location_lon": 36.8219
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
                print(f"  Added {records_added} events...")
            else:
                print(f"  Error: {response.text}")
            batch = []
            time.sleep(0.1)
    
    # Send remaining records
    if batch:
        response = requests.post(
            f"{API_BASE}/api/triggers/batch",
            json=batch,
            headers=headers
        )
        if response.status_code == 200:
            records_added += len(batch)
    
    print(f"✓ Loaded {records_added} trigger events")

def main():
    """Main function"""
    print("=" * 60)
    print("Loading Sample Data into Dashboard")
    print("=" * 60)
    
    # Get auth token
    print("\nAuthenticating...")
    token = get_auth_token()
    if not token:
        print("Failed to authenticate. Make sure:")
        print("  1. Backend is running (docker-compose up)")
        print("  2. Admin user exists (username: admin, password: admin123)")
        return
    
    print("✓ Authenticated successfully")
    
    try:
        # Load data
        load_climate_data(token)
        load_trigger_events(token)
        
        print("\n" + "=" * 60)
        print("Data Loading Complete!")
        print("=" * 60)
        print("\nRefresh your dashboard at http://localhost:3000")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
