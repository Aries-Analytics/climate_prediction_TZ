"""
Investigate duplicate year-month records in master dataset.

This script analyzes the master dataset to identify and characterize duplicate records.
It distinguishes between:
- Multi-location data (multiple locations with same year-month - VALID)
- True duplicates (same location-year-month appearing multiple times - INVALID)
"""
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load master dataset
master_path = Path("outputs/processed/master_dataset.csv")
if not master_path.exists():
    print(f"Master dataset not found at {master_path}")
    exit(1)

df = pd.read_csv(master_path)

print(f"Total rows in master dataset: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print()

# Check for year and month columns
if "year" not in df.columns or "month" not in df.columns:
    print("ERROR: year or month columns not found!")
    exit(1)

# Find duplicates
duplicates = df.duplicated(subset=["year", "month"], keep=False)
print(f"Total duplicate year-month records: {duplicates.sum()}")
print()

# Show unique year-month combinations
unique_year_months = df[["year", "month"]].drop_duplicates()
print(f"Unique year-month combinations: {len(unique_year_months)}")
print()

# Check if there's a location column
if "location" in df.columns:
    print("Location column found!")
    print(f"Unique locations: {df['location'].nunique()}")
    print(f"Locations: {sorted(df['location'].unique())}")
    print()
    
    # Check duplicates per location
    duplicates_with_location = df.duplicated(subset=["location", "year", "month"], keep=False)
    print(f"Duplicate (location, year, month) records: {duplicates_with_location.sum()}")
    print()
    
    if duplicates_with_location.sum() == 0:
        print("✓ No true duplicates found! Data structure is correct for multi-location data.")
        print(f"  Structure: {df['location'].nunique()} locations × {len(unique_year_months)} time periods = {len(df)} records")
    else:
        print("✗ TRUE DUPLICATES FOUND! This indicates a data quality issue.")

# Show sample of duplicates
if duplicates.sum() > 0:
    print("\nSample of duplicate records:")
    dup_df = df[duplicates].sort_values(["year", "month"]).head(20)
    cols_to_show = ["year", "month"]
    if "location" in df.columns:
        cols_to_show.append("location")
    print(dup_df[cols_to_show])
    print()
    
    # Count duplicates per year-month
    dup_counts = df[duplicates].groupby(["year", "month"]).size().reset_index(name="count")
    print("Duplicate counts per year-month:")
    print(dup_counts.head(10))
    print()
    print(f"Max duplicates for a single year-month: {dup_counts['count'].max()}")
    print(f"Min duplicates for a single year-month: {dup_counts['count'].min()}")
    print(f"Mean duplicates per year-month: {dup_counts['count'].mean():.2f}")

# Check source files
if "_provenance_files" in df.columns:
    print("\nProvenance files:")
    print(df["_provenance_files"].unique())
