
import sys
import os

# Add /app to python path to ensure modules are found
sys.path.append('/app')

from modules.ingestion.chirps_ingestion import fetch_chirps_data

def verify_chirps():
    print("Verifying CHIRPS GEE Data Fetching...")
    try:
        # Fetch real data for a short period
        df = fetch_chirps_data(start_year=2022, end_year=2022)
        
        if df.empty:
            print("❌ No data fetched!")
            return
            
        source = df['data_source'].iloc[0]
        print(f"✅ Data fetched successfully!")
        print(f"📊 Data source: {source}")
        
        if source == "CHIRPS_GEE":
            print("✅ SUCCESS: Real GEE data retrieved.")
        else:
            print(f"⚠️ WARNING: Unexpected data source: {source}")
            
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch CHIRPS data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_chirps()
