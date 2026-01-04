"""
Force fetch recent CHIRPS data from Google Earth Engine (2024-2025)
This will tell us exactly what's available and what's not
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.ingestion import chirps_ingestion
from datetime import datetime

print("=" * 70)
print("FORCING FRESH CHIRPS FETCH FROM GOOGLE EARTH ENGINE")
print("=" * 70)
print("\nThis will attempt to fetch 2024-2025 data directly from GEE")
print("We'll see exactly what's available and what's not\n")

# Delete cached files to force fresh fetch
import os
cache_files = [
    '../data/raw/chirps_raw.csv',
    '../data/raw/chirps_synthetic.csv'
]

for f in cache_files:
    if os.path.exists(f):
        print(f"Removing cached file: {f}")
        os.remove(f)

# Fetch 2024-2025 data
print("\nAttempting to fetch 2024-2025 CHIRPS data from GEE...")
print("-" * 70)

try:
    df = chirps_ingestion.fetch_chirps_data(
        start_year=2024,
        end_year=2025,
        use_gee=True,
        dry_run=False
    )
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"\nTotal records fetched: {len(df)}")
    print(f"Data source: {df['data_source'].iloc[0] if len(df) > 0 else 'NONE'}")
    print(f"\nDate range: {df['year'].min()}-{df['month'].min():02d} to {df['year'].max()}-{df['month'].max():02d}")
    
    # Check if it's real or synthetic
    if 'CHIRPS_GEE' in df['data_source'].values:
        print("\n✓ SUCCESS: Real satellite data from Google Earth Engine")
        print("\nData summary:")
        print(df.groupby('year')['month'].count())
        print("\nSample data:")
        print(df.head(10))
    elif 'climatology_based' in df['data_source'].values:
        print("\n❌ WARNING: Using SYNTHETIC climatology-based data")
        print("Real CHIRPS data not available for this period from GEE")
        print("\nThis means:")
        print("  - GEE doesn't have 2024-2025 data yet")
        print("  - OR there's an authentication/access issue")
        print("  - OR the CHIRPS dataset has a longer lag than expected")
    else:
        print(f"\n⚠️  Unknown data source: {df['data_source'].iloc[0]}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
