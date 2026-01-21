"""
Check what columns are in outputs/processed files.

This script inspects the structure of files in outputs/processed/ directory
to verify multi-location data structure and column availability.
"""
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

proc_dir = Path("outputs/processed")

files = [
    "nasa_power_processed.csv",
    "era5_processed.csv",
    "chirps_processed.csv",
    "ndvi_processed.csv",
    "ocean_indices_processed.csv",
    "master_dataset.csv",
]

print("Checking processed files in outputs/processed/\n")
print("=" * 80)

for fname in files:
    fpath = proc_dir / fname
    if fpath.exists():
        df = pd.read_csv(fpath)
        print(f"\n{fname}:")
        print(f"  Rows: {len(df)}")
        print(f"  Has 'location': {'location' in df.columns}")
        print(f"  Has 'year': {'year' in df.columns}")
        print(f"  Has 'month': {'month' in df.columns}")
        if "location" in df.columns:
            print(f"  Unique locations: {df['location'].nunique()}")
            print(f"  Locations: {sorted(df['location'].unique())}")
        print(f"  Sample columns: {list(df.columns[:15])}")
    else:
        print(f"\n{fname}: NOT FOUND")

print("\n" + "=" * 80)
