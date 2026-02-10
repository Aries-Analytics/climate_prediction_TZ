#!/usr/bin/env python3
"""
Prepare Seasonal Training Data for Rice Growing Season Forecasting

Creates seasonal aggregated dataset for training models to predict:
1. 4-month seasonal rainfall totals (Mar-Jun rice growing season)
2. Binary drought/flood classification
3. Trigger event probabilities

Usage:
    python scripts/prepare_seasonal_training_data.py
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Constants
RICE_SEASON_START = 3  # March
RICE_SEASON_DURATION = 4  # Mar-Jun (4 months)
DROUGHT_THRESHOLD_MM = 400  # Seasonal total < 400mm = drought
FLOOD_DAILY_THRESHOLD_MM = 258  # Any day > 258mm = flood risk

# Data paths
DATA_DIR = Path(__file__).parent.parent
# Use the complete 6-location dataset (1,872 samples, 2000-2025, 6 locations including Morogoro)
MASTER_DATASET = DATA_DIR / "outputs" / "processed" / "master_dataset_6loc_2000_2025.csv"
OUTPUT_FILE = DATA_DIR / "data" / "processed" / "seasonal_training_data.csv"

def load_master_dataset():
    """Load the master monthly dataset"""
    print("Loading master dataset...")
    df = pd.read_csv(MASTER_DATASET)
    
    # Dataset already has year and month columns
    if 'year' not in df.columns or 'month' not in df.columns:
        raise ValueError("Dataset must have 'year' and 'month' columns")
    
    # Check for location column
    if 'location' in df.columns:
        print(f"Loaded {len(df)} monthly records")
        print(f"Year range: {df['year'].min()} to {df['year'].max()}")
        print(f"Locations: {df['location'].unique() if 'location' in df.columns else 'N/A'}")
    else:
        # Add default location if missing
        df['location'] = 'default'
        print(f"WARNING: No location column found, using 'default' location")
        print(f"Loaded {len(df)} monthly records")
        print(f"Year range: {df['year'].min()} to {df['year'].max()}")
    
    # Verify rainfall column
    if 'rainfall_mm' not in df.columns:
        raise ValueError("Dataset must have 'rainfall_mm' column")
    
    return df

def create_seasonal_aggregates(df):
    """
    Aggregate monthly data to seasonal totals for rice growing season
    """
    print("\nCreating seasonal aggregates...")
    
    # Filter to growing season months only (Mar-Jun)
    season_months = list(range(RICE_SEASON_START, RICE_SEASON_START + RICE_SEASON_DURATION))
    season_df = df[df['month'].isin(season_months)].copy()
    
    print(f"Filtered to {len(season_df)} records in Mar-Jun")
    
    # Prepare aggregation dict based on available columns
    agg_dict = {'rainfall_mm': ['sum', 'max']}
    if 'temp_mean_c' in df.columns:
        agg_dict['temp_mean_c'] = 'mean'
    if 'ndvi_mean' in df.columns:
        agg_dict['ndvi_mean'] = 'min'
    if 'soil_moisture_mean' in df.columns:
        agg_dict['soil_moisture_mean'] = 'mean'
    
    # Group by location and year
    seasonal = season_df.groupby(['location', 'year']).agg(agg_dict).reset_index()
    
    # Flatten column names
    new_columns = ['location', 'year', 'seasonal_total_mm', 'max_daily_rainfall']
    if 'temp_mean_c' in agg_dict:
        new_columns.append('avg_temperature')
    if 'ndvi_mean' in agg_dict:
        new_columns.append('min_ndvi')
    if 'soil_moisture_mean' in agg_dict:
        new_columns.append('avg_soil_moisture')
    
    seasonal.columns = new_columns
    
    # Create binary labels
    seasonal['drought_occurred'] = (seasonal['seasonal_total_mm'] < DROUGHT_THRESHOLD_MM).astype(int)
    seasonal['flood_risk'] = (seasonal['max_daily_rainfall'] > FLOOD_DAILY_THRESHOLD_MM).astype(int)
    
    print(f"Created {len(seasonal)} seasonal records")
    print(f"\nLabel distribution:")
    print(f"  Drought events: {seasonal['drought_occurred'].sum()} ({seasonal['drought_occurred'].mean()*100:.1f}%)")
    print(f"  Flood events: {seasonal['flood_risk'].sum()} ({seasonal['flood_risk'].mean()*100:.1f}%)")
    
    return seasonal

def create_seasonal_features(df, seasonal_df):
    """
    Create features from preceding months (Nov-Feb) to predict upcoming season
    
    For each season, use data from Nov (year-1) to Feb (year) as predictors
    """
    print("\nCreating seasonal features from pre-season months...")
    
    features_list = []
    
    for _, row in seasonal_df.iterrows():
        location = row['location']
        year = row['year']
        
        # Get pre-season months (Nov-Feb before growing season)
        # Nov-Dec of previous year + Jan-Feb of current year
        pre_season = df[
            (df['location'] == location) &
            (
                ((df['year'] == year - 1) & (df['month'].isin([11, 12]))) |
                ((df['year'] == year) & (df['month'].isin([1, 2])))
            )
        ].copy()
        
        if len(pre_season) < 4:
            # Skip if insufficient data
            continue
        
        # Aggregate pre-season features (use available columns)
        features = {
            'location': location,
            'year': year,
            'pre_season_rainfall_total': pre_season['rainfall_mm'].sum(),
            'pre_season_rainfall_mean': pre_season['rainfall_mm'].mean(),
        }
        
        # Add optional features if available
        if 'temp_mean_c' in pre_season.columns:
            features['pre_season_temp_mean'] = pre_season['temp_mean_c'].mean()
        if 'ndvi_mean' in pre_season.columns:
            features['pre_season_ndvi_mean'] = pre_season['ndvi_mean'].mean()
        if 'soil_moisture_mean' in pre_season.columns:
            features['pre_season_soil_moisture'] = pre_season['soil_moisture_mean'].mean()
        if 'enso' in pre_season.columns:
            feb_data = pre_season[pre_season['month'] == 2]
            if len(feb_data) > 0:
                features['enso_at_planting'] = feb_data['enso'].iloc[0]
        if 'iod' in pre_season.columns:
            feb_data = pre_season[pre_season['month'] == 2]
            if len(feb_data) > 0:
                features['iod_at_planting'] = feb_data['iod'].iloc[0]
        
        features_list.append(features)
    
    features_df = pd.DataFrame(features_list)
    
    # Merge with seasonal targets
    final_df = features_df.merge(seasonal_df, on=['location', 'year'], how='inner')
    
    print(f"Created features for {len(final_df)} seasonal records")
    print(f"Features: {list(features_df.columns)}")
    
    return final_df

def validate_dataset(df):
    """Validate the seasonal training dataset"""
    print("\nValidating dataset...")
    
    # Check for missing values
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print("WARNING: Missing values detected:")
        print(missing[missing > 0])
    
    # Check drought rate
    drought_rate = df['drought_occurred'].mean()
    print(f"\nDrought rate: {drought_rate*100:.1f}%")
    if drought_rate < 0.05 or drought_rate > 0.20:
        print(f"WARNING: Drought rate outside expected range (5-20%)")
    
    # Check sample size per location
    print(f"\nSamples per location:")
    print(df['location'].value_counts())
    
    # Date range
    print(f"\nYear range: {df['year'].min()} to {df['year'].max()}")
    print(f"Total years: {df['year'].nunique()}")
    
    return True

def main():
    print("="*70)
    print("Seasonal Training Data Preparation")
    print("="*70)
    
    # Load data
    df = load_master_dataset()
    
    # Create seasonal aggregates
    seasonal_df = create_seasonal_aggregates(df)
    
    # Create features
    training_df = create_seasonal_features(df, seasonal_df)
    
    # Validate
    validate_dataset(training_df)
    
    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    training_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\n[OK] Seasonal training data saved to: {OUTPUT_FILE}")
    print(f"  Shape: {training_df.shape}")
    print(f"  Features: {training_df.shape[1] - 3}")  # Subtract location, year, targets
    print(f"  Samples: {len(training_df)}")
    
    # Summary stats
    print(f"\nTarget Variable Statistics:")
    print(f"  Seasonal Rainfall (mm):")
    print(f"    Mean: {training_df['seasonal_total_mm'].mean():.1f}")
    print(f"    Std:  {training_df['seasonal_total_mm'].std():.1f}")
    print(f"    Min:  {training_df['seasonal_total_mm'].min():.1f}")
    print(f"    Max:  {training_df['seasonal_total_mm'].max():.1f}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
