"""
Multi-Location Feature Engineering Script

Creates location-aware features from the master dataset:
1. Location encoding (one-hot)
2. Location-grouped temporal lags
3. Location-grouped rolling windows
4. Interaction features
5. Feature selection to achieve 10:1 feature-to-sample ratio

Input: data/processed/master_dataset.csv (1,560 rows × 179 features)
Output: data/processed/features_engineered_multi_location.csv (~75-100 features)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_selection import mutual_info_regression, SelectKBest
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import get_data_path
from utils.logger import log_info, log_warning

# =============================================================================
# CONFIGURATION
# =============================================================================

# Lag periods (months)
LAG_PERIODS = [1, 3, 6]

# Rolling window sizes (months)
ROLLING_WINDOWS = [3]

# Features to create lags for (high-priority predictors)
LAG_FEATURES = [
    'rainfall_mm',
    'temp_mean_c',
    'ndvi',
    'vci',
    'oni',
    'iod',
    'spi_30day',
]

# Features to create rolling stats for
ROLLING_FEATURES = [
    'rainfall_mm',
    'temp_mean_c',
    'ndvi',
]

# Interaction pairs (feature1, feature2, name)
INTERACTIONS = [
    ('oni', 'rainfall_mm', 'enso_rainfall_interaction'),
    ('iod', 'ndvi', 'iod_ndvi_interaction'),
    ('temp_mean_c', 'ndvi', 'temp_ndvi_interaction'),
    ('rainfall_mm', 'ndvi', 'rainfall_ndvi_interaction'),
    ('combined_impact_score', 'rainfall_mm', 'climate_rainfall_interaction'),
]

# Target number of features after selection
TARGET_FEATURES = 85  # Conservative target for 10:1+ ratio


# =============================================================================
# STEP 1: LOAD DATA
# =============================================================================

def load_master_dataset():
    """Load the master dataset."""
    log_info("Loading master dataset...")
    path = get_data_path("processed", "master_dataset.csv")
    df = pd.read_csv(path)
    log_info(f"Loaded {len(df)} samples with {len(df.columns)} features")
    log_info(f"Locations: {df['location'].unique().tolist()}")
    log_info(f"Date range: {df['year'].min()}-{df['year'].max()}")
    return df


# =============================================================================
# STEP 2: LOCATION ENCODING
# =============================================================================

def add_location_encoding(df):
    """
    Add one-hot encoding for locations.
    
    Uses drop_first=True to avoid perfect multicollinearity.
    This creates n-1 binary features for n locations.
    """
    log_info("Adding location encoding...")
    
    # Create one-hot encoding (drop first to avoid multicollinearity)
    location_dummies = pd.get_dummies(df['location'], prefix='loc', drop_first=True)
    
    # Add to dataframe
    df = pd.concat([df, location_dummies], axis=1)
    
    log_info(f"Added {len(location_dummies.columns)} location encoding features")
    log_info(f"Features: {location_dummies.columns.tolist()}")
    
    return df


# =============================================================================
# STEP 3: LOCATION-GROUPED LAG FEATURES
# =============================================================================

def add_lag_features(df):
    """
    Add lag features grouped by location.
    
    CRITICAL: Groups by location before shifting to prevent temporal leakage
    across different locations.
    """
    log_info("Adding location-grouped lag features...")
    
    added_features = []
    
    for feature in LAG_FEATURES:
        if feature not in df.columns:
            log_warning(f"Feature '{feature}' not found, skipping lags")
            continue
            
        for lag in LAG_PERIODS:
            new_col = f'{feature}_lag{lag}'
            df[new_col] = df.groupby('location')[feature].shift(lag)
            added_features.append(new_col)
    
    log_info(f"Added {len(added_features)} lag features")
    
    return df, added_features


# =============================================================================
# STEP 4: LOCATION-GROUPED ROLLING FEATURES
# =============================================================================

def add_rolling_features(df):
    """
    Add rolling window features grouped by location.
    
    CRITICAL: Applies rolling windows within each location to prevent
    spatial leakage.
    """
    log_info("Adding location-grouped rolling features...")
    
    added_features = []
    
    for feature in ROLLING_FEATURES:
        if feature not in df.columns:
            log_warning(f"Feature '{feature}' not found, skipping rolling")
            continue
            
        for window in ROLLING_WINDOWS:
            # Rolling mean
            mean_col = f'{feature}_roll{window}_mean'
            df[mean_col] = df.groupby('location')[feature].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean()
            )
            added_features.append(mean_col)
            
            # Rolling std
            std_col = f'{feature}_roll{window}_std'
            df[std_col] = df.groupby('location')[feature].transform(
                lambda x: x.rolling(window=window, min_periods=1).std()
            )
            added_features.append(std_col)
    
    log_info(f"Added {len(added_features)} rolling features")
    
    return df, added_features


# =============================================================================
# STEP 5: INTERACTION FEATURES
# =============================================================================

def add_interaction_features(df):
    """Add interaction features between key predictors."""
    log_info("Adding interaction features...")
    
    added_features = []
    
    for feat1, feat2, name in INTERACTIONS:
        if feat1 in df.columns and feat2 in df.columns:
            df[name] = df[feat1] * df[feat2]
            added_features.append(name)
        else:
            missing = []
            if feat1 not in df.columns:
                missing.append(feat1)
            if feat2 not in df.columns:
                missing.append(feat2)
            log_warning(f"Cannot create '{name}': missing {missing}")
    
    log_info(f"Added {len(added_features)} interaction features")
    
    return df, added_features


# =============================================================================
# STEP 6: FEATURE VALIDATION
# =============================================================================

def validate_features(df):
    """Validate feature distributions across locations."""
    log_info("Validating features across locations...")
    
    # Check for NaN patterns
    nan_counts = df.isnull().sum()
    high_nan_features = nan_counts[nan_counts > len(df) * 0.1].index.tolist()
    
    if high_nan_features:
        log_warning(f"Features with >10% NaN: {len(high_nan_features)}")
        for feat in high_nan_features[:5]:  # Show first 5
            log_info(f"  {feat}: {nan_counts[feat]} NaN ({nan_counts[feat]/len(df)*100:.1f}%)")
    
    # Check location-wise statistics for key features
    key_features = ['rainfall_mm', 'temp_mean_c', 'ndvi', 'oni', 'iod']
    
    log_info("Location-wise statistics for key features:")
    for feat in key_features:
        if feat in df.columns:
            stats = df.groupby('location')[feat].agg(['mean', 'std', 'min', 'max'])
            log_info(f"\n{feat}:")
            log_info(stats.to_string())
    
    return df


# =============================================================================
# STEP 7: FEATURE SELECTION
# =============================================================================

def select_features(df, target_col='rainfall_mm', n_features=TARGET_FEATURES):
    """
    Select top features using mutual information.
    
    Strategy:
    1. Separate essential features (year, month, location) from candidate features
    2. Use mutual information to rank candidate features
    3. Select top N candidates
    4. Combine with essential features
    """
    log_info(f"Selecting top {n_features} features using mutual information...")
    
    # Essential features that must be kept
    essential_features = [
        'year', 'month', 'location', 'location_lat', 'location_lon'
    ]
    
    # Add location encoding features (they're essential for location patterns)
    location_encoding_cols = [col for col in df.columns if col.startswith('loc_')]
    essential_features.extend(location_encoding_cols)
    
    # Target variable
    if target_col not in df.columns:
        log_warning(f"Target '{target_col}' not found, using first suitable numeric column")
        # Find first numeric column that's not in essential features
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        target_col = [c for c in numeric_cols if c not in essential_features][0]
    
    y = df[target_col].fillna(df[target_col].median())
    
    # Candidate features (numeric, not essential, not target)
    candidate_features = [
        col for col in df.columns 
        if df[col].dtype in [np.float64, np.int64, np.float32, np.int32]
        and col not in essential_features
        and col != target_col
        and col != '_provenance_files'
        and not col.endswith('_class')  # Exclude categorical encodings
    ]
    
    log_info(f"Essential features: {len(essential_features)}")
    log_info(f"Candidate features: {len(candidate_features)}")
    
    # Prepare candidate features (fill NaN, handle inf)
    X_candidates = df[candidate_features].copy()
    
    # Fill NaN with median
    for col in X_candidates.columns:
        if X_candidates[col].isnull().any():
            X_candidates[col].fillna(X_candidates[col].median(), inplace=True)
    
    # Replace inf with large values
    X_candidates.replace([np.inf, -np.inf], [1e10, -1e10], inplace=True)
    
    # Calculate mutual information
    log_info("Calculating mutual information scores...")
    mi_scores = mutual_info_regression(X_candidates, y, random_state=42)
    
    # Create feature importance DataFrame
    feature_importance = pd.DataFrame({
        'feature': candidate_features,
        'mi_score': mi_scores
    }).sort_values('mi_score', ascending=False)
    
    # Select top features
    n_candidates_to_select = n_features - len(essential_features)
    
    if n_candidates_to_select <= 0:
        log_warning(f"Essential features ({len(essential_features)}) exceed target ({n_features})")
        log_warning("Using all essential features only")
        selected_candidates = []
    else:
        selected_candidates = feature_importance.head(n_candidates_to_select)['feature'].tolist()
    
    # Combine essential + selected candidates
    final_features = essential_features + selected_candidates
    
    log_info(f"Final feature count: {len(final_features)}")
    log_info(f"  Essential: {len(essential_features)}")
    log_info(f"  Selected: {len(selected_candidates)}")
    
    # Show top 15 selected features
    log_info("\nTop 15 selected features by mutual information:")
    for i, row in feature_importance.head(15).iterrows():
        selected_mark = "✓" if row['feature'] in selected_candidates else "✗"
        log_info(f"  {selected_mark} {row['feature']}: {row['mi_score']:.4f}")
    
    # Save feature importance report
    importance_path = get_data_path("processed", "feature_importance_report.csv")
    feature_importance.to_csv(importance_path, index=False)
    log_info(f"\nFeature importance report saved to: {importance_path}")
    
    return df[final_features + [target_col, '_provenance_files']], feature_importance


# =============================================================================
# STEP 8: SAVE OUTPUT
# =============================================================================

def save_engineered_features(df):
    """Save the engineered feature dataset."""
    output_path = get_data_path("processed", "features_engineered_multi_location.csv")
    df.to_csv(output_path, index=False)
    log_info(f"Saved engineered features to: {output_path}")
    
    # Also save as parquet for efficiency
    parquet_path = get_data_path("processed", "features_engineered_multi_location.parquet")
    df.to_parquet(parquet_path, index=False)
    log_info(f"Saved parquet version to: {parquet_path}")
    
    return output_path


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    log_info("="*70)
    log_info("MULTI-LOCATION FEATURE ENGINEERING")
    log_info("="*70)
    
    # Step 1: Load data
    df = load_master_dataset()
    initial_features = len(df.columns)
    
    # Step 2: Add location encoding
    df = add_location_encoding(df)
    
    # Step 3: Add lag features
    df, lag_features = add_lag_features(df)
    
    # Step 4: Add rolling features
    df, rolling_features = add_rolling_features(df)
    
    # Step 5: Add interaction features
    df, interaction_features = add_interaction_features(df)
    
    # Report feature counts
    total_features = len(df.columns)
    added_features = total_features - initial_features
    
    log_info("="*70)
    log_info("FEATURE ENGINEERING SUMMARY")
    log_info("="*70)
    log_info(f"Initial features: {initial_features}")
    log_info(f"Location encoding: {len([c for c in df.columns if c.startswith('loc_')])}")
    log_info(f"Lag features: {len(lag_features)}")
    log_info(f"Rolling features: {len(rolling_features)}")
    log_info(f"Interaction features: {len(interaction_features)}")
    log_info(f"Total features: {total_features}")
    log_info(f"Added features: {added_features}")
    
    # Step 6: Validate features
    df = validate_features(df)
    
    # Step 7: Feature selection
    df_selected, feature_importance = select_features(df, target_col='rainfall_mm', n_features=TARGET_FEATURES)
    
    # Calculate feature-to-sample ratio
    training_samples = int(len(df_selected) * 0.70)  # 70% train split
    feature_count = len(df_selected.columns) - 2  # Exclude target and provenance
    ratio = training_samples / feature_count
    
    log_info("="*70)
    log_info("FINAL STATISTICS")
    log_info("="*70)
    log_info(f"Total samples: {len(df_selected)}")
    log_info(f"Training samples (70%): {training_samples}")
    log_info(f"Final feature count: {feature_count}")
    log_info(f"Feature-to-sample ratio: {ratio:.2f}:1")
    
    if ratio >= 10:
        log_info("✓ Target ratio (10:1) achieved!")
    else:
        log_warning(f"✗ Ratio below target (need 10:1, have {ratio:.2f}:1)")
    
    # Step 8: Save output
    output_path = save_engineered_features(df_selected)
    
    log_info("="*70)
    log_info("FEATURE ENGINEERING COMPLETE")
    log_info("="*70)
    log_info(f"Output saved to: {output_path}")
    
    return df_selected


if __name__ == "__main__":
    engineered_df = main()
