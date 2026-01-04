"""
Multi-Location Data Splitting - Time-Based Stratification

Creates train/validation/test splits using time-based stratification:
- Maintains temporal ordering within each location
- Ensures balanced location representation
- Prevents temporal leakage

Split Strategy:
- Train: First 70% of timeline (2000-2018) per location
- Validation: Next 15% of timeline (2019-2021) per location  
- Test: Last 15% of timeline (2022-2025) per location

Input: data/processed/features_engineered_multi_location.csv
Outputs: 
- data/processed/features_train_multi_location.parquet
- data/processed/features_val_multi_location.parquet
- data/processed/features_test_multi_location.parquet
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import get_data_path
from utils.logger import log_info, log_warning

# =============================================================================
# CONFIGURATION
# =============================================================================

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Verify ratios sum to 1
assert abs(TRAIN_RATIO + VAL_RATIO + TEST_RATIO - 1.0) < 1e-6, "Ratios must sum to 1.0"

# =============================================================================
# LOAD DATA
# =============================================================================

def load_engineered_features():
    """Load the engineered multi-location feature dataset."""
    log_info("Loading engineered features...")
    path = get_data_path("processed", "features_engineered_multi_location.csv")
    df = pd.read_csv(path)
    
    log_info(f"Loaded {len(df)} samples with {len(df.columns)} features")
    log_info(f"Locations: {sorted(df['location'].unique())}")
    log_info(f"Date range: {df['year'].min()}-{df['year'].max()}")
    
    return df


# =============================================================================
# TIME-BASED SPLITTING
# =============================================================================

def create_time_based_splits(df):
    """
    Create time-based train/val/test splits stratified by location.
    
    For each location:
    - Sort by year, month (chronological order)
    - First 70% → train
    - Next 15% → validation
    - Last 15% → test
    
    This ensures:
    1. No temporal leakage (test is always after validation, validation after train)
    2. Realistic forecasting scenario (predicting future data)
    3. Equal temporal coverage per location
    """
    log_info("Creating time-based stratified splits...")
    
    # Initialize empty dataframes for splits
    train_dfs = []
    val_dfs = []
    test_dfs = []
    
    # Get unique locations
    locations = sorted(df['location'].unique())
    
    # Split statistics
    split_stats = {
        'locations': {},
        'total_samples': len(df),
        'ratios': {
            'train': TRAIN_RATIO,
            'val': VAL_RATIO,
            'test': TEST_RATIO
        }
    }
    
    for location in locations:
        log_info(f"\nProcessing location: {location}")
        
        # Get data for this location
        loc_df = df[df['location'] == location].copy()
        
        # Sort by year, month (chronological order)
        loc_df = loc_df.sort_values(['year', 'month']).reset_index(drop=True)
        
        n_samples = len(loc_df)
        log_info(f"  Total samples: {n_samples}")
        
        # Calculate split indices
        train_end = int(n_samples * TRAIN_RATIO)
        val_end = train_end + int(n_samples * VAL_RATIO)
        
        # Create splits
        train_loc = loc_df.iloc[:train_end].copy()
        val_loc = loc_df.iloc[train_end:val_end].copy()
        test_loc = loc_df.iloc[val_end:].copy()
        
        # Log split details
        log_info(f"  Train: {len(train_loc)} samples ({train_loc['year'].min()}-{train_loc['year'].max()})")
        log_info(f"  Val:   {len(val_loc)} samples ({val_loc['year'].min()}-{val_loc['year'].max()})")
        log_info(f"  Test:  {len(test_loc)} samples ({test_loc['year'].min()}-{test_loc['year'].max()})")
        
        # Store statistics
        split_stats['locations'][location] = {
            'total': n_samples,
            'train': len(train_loc),
            'val': len(val_loc),
            'test': len(test_loc),
            'train_period': f"{train_loc['year'].min()}-{train_loc['year'].max()}",
            'val_period': f"{val_loc['year'].min()}-{val_loc['year'].max()}",
            'test_period': f"{test_loc['year'].min()}-{test_loc['year'].max()}"
        }
        
        # Append to split lists
        train_dfs.append(train_loc)
        val_dfs.append(val_loc)
        test_dfs.append(test_loc)
    
    # Combine all locations for each split
    train_df = pd.concat(train_dfs, ignore_index=True)
    val_df = pd.concat(val_dfs, ignore_index=True)
    test_df = pd.concat(test_dfs, ignore_index=True)
    
    # Add aggregate statistics
    split_stats['aggregated'] = {
        'train': len(train_df),
        'val': len(val_df),
        'test': len(test_df),
        'total': len(train_df) + len(val_df) + len(test_df)
    }
    
    log_info("\n" + "="*70)
    log_info("SPLIT SUMMARY")
    log_info("="*70)
    log_info(f"Train set: {len(train_df)} samples ({len(train_df)/len(df)*100:.1f}%)")
    log_info(f"Val set:   {len(val_df)} samples ({len(val_df)/len(df)*100:.1f}%)")
    log_info(f"Test set:  {len(test_df)} samples ({len(test_df)/len(df)*100:.1f}%)")
    log_info(f"Total:     {len(train_df) + len(val_df) + len(test_df)} samples")
    
    return train_df, val_df, test_df, split_stats


# =============================================================================
# VALIDATION
# =============================================================================

def validate_splits(train_df, val_df, test_df, original_df):
    """Validate the splits to ensure quality and correctness."""
    log_info("\n" + "="*70)
    log_info("VALIDATING SPLITS")
    log_info("="*70)
    
    # Check 1: No sample appears in multiple splits
    # Use (year, month, location) tuples as unique identifiers
    train_ids = set(train_df[['year', 'month', 'location']].apply(tuple, axis=1))
    val_ids = set(val_df[['year', 'month', 'location']].apply(tuple, axis=1))
    test_ids = set(test_df[['year', 'month', 'location']].apply(tuple, axis=1))
    
    overlap_tv = train_ids.intersection(val_ids)
    overlap_tt = train_ids.intersection(test_ids)
    overlap_vt = val_ids.intersection(test_ids)
    
    if overlap_tv or overlap_tt or overlap_vt:
        log_warning("⚠ WARNING: Sample overlap detected between splits!")
        if overlap_tv:
            log_warning(f"  Train-Val overlap: {len(overlap_tv)} samples")
        if overlap_tt:
            log_warning(f"  Train-Test overlap: {len(overlap_tt)} samples")
        if overlap_vt:
            log_warning(f"  Val-Test overlap: {len(overlap_vt)} samples")
    else:
        log_info("✓ No overlap between splits")
    
    # Check 2: All samples accounted for
    total_split_samples = len(train_df) + len(val_df) + len(test_df)
    if total_split_samples != len(original_df):
        log_warning(f"⚠ Sample count mismatch: {total_split_samples} vs {len(original_df)}")
    else:
        log_info(f"✓ All {total_split_samples} samples accounted for")
    
    # Check 3: Location balance
    locations = sorted(original_df['location'].unique())
    log_info("\n✓ Location distribution:")
    
    for split_name, split_df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
        loc_counts = split_df['location'].value_counts()
        log_info(f"\n{split_name}:")
        for loc in locations:
            count = loc_counts.get(loc, 0)
            pct = count / len(split_df) * 100
            log_info(f"  {loc}: {count} samples ({pct:.1f}%)")
    
    # Check 4: Temporal ordering within locations
    log_info("\n✓ Temporal ordering check:")
    for split_name, split_df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
        for loc in locations:
            loc_data = split_df[split_df['location'] == loc]
            if len(loc_data) > 0:
                # Check if sorted
                years = loc_data['year'].values
                months = loc_data['month'].values
                
                is_sorted = all(
                    years[i] < years[i+1] or (years[i] == years[i+1] and months[i] <= months[i+1])
                    for i in range(len(years)-1)
                )
                
                if not is_sorted:
                    log_warning(f"  ⚠ {split_name} - {loc}: NOT properly sorted")
                else:
                    log_info(f"  {split_name} - {loc}: Chronologically ordered ✓")
    
    # Check 5: Feature consistency
    log_info("\n✓ Feature consistency:")
    train_cols = set(train_df.columns)
    val_cols = set(val_df.columns)
    test_cols = set(test_df.columns)
    
    if train_cols == val_cols == test_cols:
        log_info(f"  All splits have {len(train_cols)} features ✓")
    else:
        log_warning("  ⚠ Feature mismatch between splits!")
        log_warning(f"    Train: {len(train_cols)}, Val: {len(val_cols)}, Test: {len(test_cols)}")
    
    log_info("\n" + "="*70)
    log_info("VALIDATION COMPLETE")
    log_info("="*70)


# =============================================================================
# SAVE SPLITS
# =============================================================================

def save_splits(train_df, val_df, test_df, split_stats):
    """Save the splits as parquet files for efficient loading."""
    log_info("\nSaving splits...")
    
    # Save as parquet (compressed and fast)
    train_path = get_data_path("processed", "features_train_multi_location.parquet")
    val_path = get_data_path("processed", "features_val_multi_location.parquet")
    test_path = get_data_path("processed", "features_test_multi_location.parquet")
    
    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    log_info(f"✓ Train set saved: {train_path}")
    log_info(f"✓ Val set saved: {val_path}")
    log_info(f"✓ Test set saved: {test_path}")
    
    # Also save as CSV for manual inspection
    train_csv = get_data_path("processed", "features_train_multi_location.csv")
    val_csv = get_data_path("processed", "features_val_multi_location.csv")
    test_csv = get_data_path("processed", "features_test_multi_location.csv")
    
    train_df.to_csv(train_csv, index=False)
    val_df.to_csv(val_csv, index=False)
    test_df.to_csv(test_csv, index=False)
    
    log_info(f"✓ Train CSV saved: {train_csv}")
    log_info(f"✓ Val CSV saved: {val_csv}")
    log_info(f"✓ Test CSV saved: {test_csv}")
    
    # Save split statistics
    stats_path = get_data_path("processed", "split_statistics.json")
    with open(stats_path, 'w') as f:
        json.dump(split_stats, f, indent=2)
    
    log_info(f"✓ Split statistics saved: {stats_path}")
    
    return {
        'train': train_path,
        'val': val_path,
        'test': test_path,
        'stats': stats_path
    }


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    log_info("="*70)
    log_info("MULTI-LOCATION DATA SPLITTING (TIME-BASED)")
    log_info("="*70)
    
    # Load data
    df = load_engineered_features()
    
    # Create splits
    train_df, val_df, test_df, split_stats = create_time_based_splits(df)
    
    # Validate splits
    validate_splits(train_df, val_df, test_df, df)
    
    # Save splits
    paths = save_splits(train_df, val_df, test_df, split_stats)
    
    # Final summary
    log_info("\n" + "="*70)
    log_info("SPLITTING COMPLETE")
    log_info("="*70)
    log_info(f"\nTrain set: {len(train_df)} samples")
    log_info(f"Val set:   {len(val_df)} samples")
    log_info(f"Test set:  {len(test_df)} samples")
    log_info(f"\nFiles saved to: data/processed/")
    log_info("  - features_train_multi_location.parquet")
    log_info("  - features_val_multi_location.parquet")
    log_info("  - features_test_multi_location.parquet")
    log_info("  - split_statistics.json")
    
    return train_df, val_df, test_df, split_stats


if __name__ == "__main__":
    train, val, test, stats = main()
