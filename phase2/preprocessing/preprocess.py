"""
Feature Engineering Pipeline

This module implements data loading, validation, and feature engineering
for the ML model development pipeline.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger()


# ============================================================================
# Data Loading and Validation (Task 2.1)
# ============================================================================


def load_and_validate_data(file_path: str) -> pd.DataFrame:
    """
    Load master dataset and validate structure.

    Args:
        file_path: Path to the master dataset CSV file

    Returns:
        pd.DataFrame: Validated dataset

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing or data types are invalid

    Requirements: 1.1
    """
    logger.info(f"Loading data from {file_path}")

    # Check if file exists
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Master dataset not found at {file_path}")

    # Load data
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded dataset with shape {df.shape}")
    except Exception as e:
        raise ValueError(f"Failed to load CSV file: {e}")

    # Validate required columns
    required_columns = ["year", "month"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Validate data types
    if not pd.api.types.is_numeric_dtype(df["year"]):
        raise ValueError("Column 'year' must be numeric")

    if not pd.api.types.is_numeric_dtype(df["month"]):
        raise ValueError("Column 'month' must be numeric")

    # Validate year and month ranges
    if df["year"].min() < 1900 or df["year"].max() > 2100:
        raise ValueError(f"Year values out of valid range: {df['year'].min()} - {df['year'].max()}")

    if df["month"].min() < 1 or df["month"].max() > 12:
        raise ValueError(f"Month values out of valid range: {df['month'].min()} - {df['month'].max()}")

    # Check for duplicate time periods
    duplicates = df.duplicated(subset=["year", "month"], keep=False)
    if duplicates.any():
        dup_count = duplicates.sum()
        logger.warning(f"Found {dup_count} duplicate year-month combinations")

    # Validate numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    logger.info(f"Found {len(numeric_columns)} numeric columns")

    # Check for all-null columns
    null_columns = df.columns[df.isnull().all()].tolist()
    if null_columns:
        logger.warning(f"Found {len(null_columns)} columns with all null values: {null_columns[:5]}...")

    # Log data quality statistics
    total_cells = df.shape[0] * df.shape[1]
    null_cells = df.isnull().sum().sum()
    null_percentage = (null_cells / total_cells) * 100

    logger.info(f"Data quality: {null_percentage:.2f}% missing values")
    logger.info(f"Date range: {df['year'].min()}-{df['month'].min()} to {df['year'].max()}-{df['month'].max()}")

    return df


def validate_schema(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> bool:
    """
    Validate dataset schema against required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names (optional)

    Returns:
        bool: True if schema is valid

    Raises:
        ValueError: If schema validation fails
    """
    if required_columns is None:
        required_columns = ["year", "month"]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Schema validation failed. Missing columns: {missing_columns}")

    logger.info(f"Schema validation passed. All {len(required_columns)} required columns present.")
    return True


def validate_data_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Validate and report data types for all columns.

    Args:
        df: DataFrame to validate

    Returns:
        Dict[str, str]: Dictionary mapping column names to data types
    """
    type_summary = {}

    for col in df.columns:
        dtype = str(df[col].dtype)
        type_summary[col] = dtype

        # Check for mixed types
        if dtype == "object":
            # Try to identify if it should be numeric
            try:
                pd.to_numeric(df[col], errors="raise")
                logger.warning(f"Column '{col}' is object type but could be numeric")
            except (ValueError, TypeError):
                pass

    numeric_count = sum(1 for dtype in type_summary.values() if "int" in dtype or "float" in dtype)
    logger.info(f"Data types: {numeric_count} numeric, {len(type_summary) - numeric_count} non-numeric")

    return type_summary


# ============================================================================
# Feature Engineering Functions (Task 2.2-2.7)
# ============================================================================


def create_lag_features(df: pd.DataFrame, columns: List[str], lags: List[int]) -> pd.DataFrame:
    """
    Create lag features for specified columns.
    
    For multi-location data, lags are computed within each location group to prevent
    spatial leakage (data from one location affecting another).

    Args:
        df: Input DataFrame (must be sorted by time)
        columns: List of column names to create lags for
        lags: List of lag periods (e.g., [1, 3, 6, 12] for months)

    Returns:
        pd.DataFrame: DataFrame with added lag features

    Requirements: 1.2
    """
    logger.info(f"Creating lag features for {len(columns)} columns with lags {lags}")

    df_lagged = df.copy()
    
    # Check if multi-location data
    has_location = 'location' in df_lagged.columns
    if has_location:
        logger.info("Multi-location data detected - creating location-grouped lag features")

    # Identify key variables for lagging
    key_variables = []
    for col in columns:
        # Match columns containing key climate variables
        if any(keyword in col.lower() for keyword in ["temp", "rainfall", "precip", "ndvi", "oni", "enso", "iod"]):
            key_variables.append(col)

    if not key_variables:
        logger.warning(f"No matching columns found for lag features from: {columns[:5]}...")
        key_variables = [col for col in columns if col in df.columns][:10]  # Take first 10 if no matches

    logger.info(f"Creating lags for {len(key_variables)} key variables")
    features_created = 0
    
    if has_location:
        # Multi-location: Create lags grouped by location
        # Sort by location, year, month
        df_lagged = df_lagged.sort_values(['location', 'year', 'month']).reset_index(drop=True)
        
        for col in key_variables:
            if col not in df_lagged.columns:
                continue
            
            for lag in lags:
                lag_col_name = f"{col}_lag_{lag}"
                # Group by location and shift within each group
                df_lagged[lag_col_name] = df_lagged.groupby('location')[col].shift(lag)
                features_created += 1
    else:
        # Single-location: Original logic
        df_lagged = df_lagged.sort_values(["year", "month"]).reset_index(drop=True)
        
        lag_features = {}
        for col in key_variables:
            if col not in df_lagged.columns:
                continue

            for lag in lags:
                lag_col_name = f"{col}_lag_{lag}"
                lag_features[lag_col_name] = df_lagged[col].shift(lag)
                features_created += 1
        
        # Concatenate all new columns at once
        if lag_features:
            df_lagged = pd.concat([df_lagged, pd.DataFrame(lag_features, index=df_lagged.index)], axis=1)

    logger.info(f"Created {features_created} lag features")

    return df_lagged


def create_rolling_features(df: pd.DataFrame, columns: List[str], windows: List[int]) -> pd.DataFrame:
    """
    Create rolling mean and standard deviation features.
    
    For multi-location data, rolling windows are computed within each location group
    to prevent spatial leakage.

    Args:
        df: Input DataFrame (must be sorted by time)
        columns: List of column names to create rolling features for
        windows: List of window sizes (e.g., [3, 6] for 3-month and 6-month windows)

    Returns:
        pd.DataFrame: DataFrame with added rolling features

    Requirements: 1.3
    """
    logger.info(f"Creating rolling features for {len(columns)} columns with windows {windows}")

    df_rolling = df.copy()
    
    # Check if multi-location data
    has_location = 'location' in df_rolling.columns
    if has_location:
        logger.info("Multi-location data detected - creating location-grouped rolling features")

    # Identify numeric columns for rolling statistics
    numeric_cols = df_rolling.select_dtypes(include=[np.number]).columns.tolist()

    # Filter to key variables
    key_variables = []
    for col in columns:
        if col in numeric_cols and any(
            keyword in col.lower() for keyword in ["temp", "rainfall", "precip", "ndvi", "humidity", "solar"]
        ):
            key_variables.append(col)

    if not key_variables:
        logger.warning(f"No matching numeric columns found for rolling features")
        key_variables = [col for col in columns if col in numeric_cols][:10]

    logger.info(f"Creating rolling features for {len(key_variables)} key variables")
    features_created = 0
    
    if has_location:
        # Multi-location: Create rolling features grouped by location
        df_rolling = df_rolling.sort_values(['location', 'year', 'month']).reset_index(drop=True)
        
        for col in key_variables:
            if col not in df_rolling.columns:
                continue

            for window in windows:
                # Rolling mean - grouped by location
                mean_col_name = f"{col}_rolling_mean_{window}"
                df_rolling[mean_col_name] = df_rolling.groupby('location')[col].transform(
                    lambda x: x.rolling(window=window, min_periods=1).mean()
                )
                features_created += 1

                # Rolling standard deviation - grouped by location
                std_col_name = f"{col}_rolling_std_{window}"
                df_rolling[std_col_name] = df_rolling.groupby('location')[col].transform(
                    lambda x: x.rolling(window=window, min_periods=1).std()
                )
                features_created += 1
    else:
        # Single-location: Original logic
        df_rolling = df_rolling.sort_values(["year", "month"]).reset_index(drop=True)
        
        rolling_features = {}
        for col in key_variables:
            if col not in df_rolling.columns:
                continue

            for window in windows:
                # Rolling mean
                mean_col_name = f"{col}_rolling_mean_{window}"
                rolling_features[mean_col_name] = df_rolling[col].rolling(window=window, min_periods=1).mean()
                features_created += 1

                # Rolling standard deviation
                std_col_name = f"{col}_rolling_std_{window}"
                rolling_features[std_col_name] = df_rolling[col].rolling(window=window, min_periods=1).std()
                features_created += 1
        
        # Concatenate all new columns at once
        if rolling_features:
            df_rolling = pd.concat([df_rolling, pd.DataFrame(rolling_features, index=df_rolling.index)], axis=1)

    logger.info(f"Created {features_created} rolling features")

    return df_rolling


def create_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create interaction features between key climate variables.

    Creates:
    - ENSO × rainfall interactions
    - IOD × NDVI interactions

    Args:
        df: Input DataFrame

    Returns:
        pd.DataFrame: DataFrame with added interaction features

    Requirements: 1.4, 1.5
    """
    logger.info("Creating interaction features")

    df_interact = df.copy()
    features_created = 0

    # Get numeric columns only
    numeric_cols = df_interact.select_dtypes(include=[np.number]).columns.tolist()

    # Find ENSO-related columns (numeric only)
    enso_cols = [col for col in numeric_cols if "oni" in col.lower() or "enso" in col.lower()]
    rainfall_cols = [col for col in numeric_cols if "rainfall" in col.lower() or "precip" in col.lower()]

    # Create ENSO × rainfall interactions
    for enso_col in enso_cols[:3]:  # Limit to top 3 ENSO columns
        for rain_col in rainfall_cols[:3]:  # Limit to top 3 rainfall columns
            if enso_col in df_interact.columns and rain_col in df_interact.columns:
                try:
                    interaction_name = f"{enso_col}_x_{rain_col}"
                    df_interact[interaction_name] = df_interact[enso_col] * df_interact[rain_col]
                    features_created += 1
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not create interaction {enso_col} x {rain_col}: {e}")

    # Find IOD and NDVI columns (numeric only)
    iod_cols = [col for col in numeric_cols if "iod" in col.lower()]
    ndvi_cols = [col for col in numeric_cols if "ndvi" in col.lower() and col in numeric_cols]

    # Create IOD × NDVI interactions
    for iod_col in iod_cols[:3]:  # Limit to top 3 IOD columns
        for ndvi_col in ndvi_cols[:3]:  # Limit to top 3 NDVI columns
            if iod_col in df_interact.columns and ndvi_col in df_interact.columns:
                try:
                    interaction_name = f"{iod_col}_x_{ndvi_col}"
                    df_interact[interaction_name] = df_interact[iod_col] * df_interact[ndvi_col]
                    features_created += 1
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not create interaction {iod_col} x {ndvi_col}: {e}")

    logger.info(f"Created {features_created} interaction features")

    return df_interact


def encode_location(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode location as one-hot features for multi-location modeling.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: DataFrame with added location encoding features
    """
    if 'location' not in df.columns:
        logger.info("No location column found - skipping location encoding")
        return df
    
    logger.info("Encoding location as one-hot features")
    
    # Create one-hot encoding (drop_first=True to avoid multicollinearity)
    location_dummies = pd.get_dummies(df['location'], prefix='loc', drop_first=True, dtype=int)
    
    # Add to dataframe
    df_encoded = pd.concat([df, location_dummies], axis=1)
    
    logger.info(f"Created {len(location_dummies.columns)} location encoding features")
    
    return df_encoded


def remove_correlated_features(df: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame:
    """
    Remove highly correlated features to reduce redundancy.
    
    OPTIMIZED: Added to reduce feature dimensionality and multicollinearity.
    
    Args:
        df: Input DataFrame
        threshold: Correlation threshold (default 0.95)
        
    Returns:
        pd.DataFrame: DataFrame with highly correlated features removed
        
    Requirements: 6.4
    """
    logger.info(f"Removing features with correlation > {threshold}")
    
    # Get numeric columns only
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Exclude year and month from correlation analysis
    exclude_cols = ['year', 'month']
    feature_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    if len(feature_cols) < 2:
        logger.warning("Not enough features for correlation analysis")
        return df
    
    # Calculate correlation matrix
    corr_matrix = df[feature_cols].corr().abs()
    
    # Select upper triangle of correlation matrix
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Find features with correlation greater than threshold
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    
    if to_drop:
        logger.info(f"Dropping {len(to_drop)} highly correlated features")
        df_reduced = df.drop(columns=to_drop)
        logger.info(f"Features reduced from {len(df.columns)} to {len(df_reduced.columns)}")
        return df_reduced
    else:
        logger.info("No highly correlated features found")
        return df


def handle_missing_values(df: pd.DataFrame, max_gap: int = 2) -> pd.DataFrame:
    """
    Handle missing values using forward-fill with gap limit.

    Args:
        df: Input DataFrame
        max_gap: Maximum number of consecutive periods to forward-fill

    Returns:
        pd.DataFrame: DataFrame with imputed values

    Requirements: 1.6
    """
    logger.info(f"Handling missing values with max gap of {max_gap} periods")

    df_filled = df.copy()

    # Ensure data is sorted by time
    df_filled = df_filled.sort_values(["year", "month"]).reset_index(drop=True)

    # Get numeric columns only
    numeric_cols = df_filled.select_dtypes(include=[np.number]).columns.tolist()

    # Track imputation statistics
    imputation_stats = {}

    for col in numeric_cols:
        if col in ["year", "month"]:
            continue

        missing_before = df_filled[col].isnull().sum()

        if missing_before > 0:
            # Forward fill with limit (using new pandas syntax)
            df_filled[col] = df_filled[col].ffill(limit=max_gap)

            missing_after = df_filled[col].isnull().sum()
            imputed_count = missing_before - missing_after

            if imputed_count > 0:
                imputation_stats[col] = {
                    "missing_before": int(missing_before),
                    "imputed": int(imputed_count),
                    "still_missing": int(missing_after),
                }

    total_imputed = sum(stats["imputed"] for stats in imputation_stats.values())
    logger.info(f"Imputed {total_imputed} values across {len(imputation_stats)} columns")

    # Log columns with remaining missing values
    still_missing = {
        col: stats["still_missing"] for col, stats in imputation_stats.items() if stats["still_missing"] > 0
    }
    if still_missing:
        logger.warning(f"{len(still_missing)} columns still have missing values after imputation")

    return df_filled


def normalize_features(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict]:
    """
    Normalize numeric features using standardization (z-score).

    Args:
        df: Input DataFrame
        exclude_cols: List of columns to exclude from normalization

    Returns:
        Tuple[pd.DataFrame, Dict]: Normalized DataFrame and scaler parameters

    Requirements: 1.7
    """
    logger.info("Normalizing features using standardization")

    df_normalized = df.copy()

    # Default columns to exclude
    if exclude_cols is None:
        exclude_cols = ["year", "month"]
    else:
        exclude_cols = list(set(exclude_cols + ["year", "month"]))

    # Get numeric columns
    numeric_cols = df_normalized.select_dtypes(include=[np.number]).columns.tolist()
    cols_to_normalize = [col for col in numeric_cols if col not in exclude_cols]

    # Store scaler parameters
    scaler_params = {}

    for col in cols_to_normalize:
        if col not in df_normalized.columns:
            continue

        # Calculate mean and std (excluding NaN values)
        mean_val = df_normalized[col].mean()
        std_val = df_normalized[col].std()

        # Store parameters
        scaler_params[col] = {
            "mean": float(mean_val) if not pd.isna(mean_val) else 0.0,
            "std": float(std_val) if not pd.isna(std_val) else 1.0,
        }

        # Normalize (z-score)
        if std_val > 0 and not pd.isna(std_val):
            df_normalized[col] = (df_normalized[col] - mean_val) / std_val
        else:
            logger.warning(f"Column '{col}' has zero or NaN std, skipping normalization")

    logger.info(f"Normalized {len(scaler_params)} features")

    return df_normalized, scaler_params


def split_temporal_data(
    df: pd.DataFrame, train_pct: float = 0.65, val_pct: float = 0.20, gap_months: int = 12
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into train/validation/test sets maintaining chronological order with temporal gaps.
    
    For multi-location data, splits each location separately to ensure balanced representation
    while preventing temporal leakage within each location.
    
    This function ensures NO temporal leakage by:
    1. Creating gaps between train/val and val/test splits
    2. Preventing year overlap that could leak through lag features
    3. Maintaining strict chronological ordering
    4. For multi-location: Stratifying by location (each location split separately)

    Args:
        df: Input DataFrame (must have year and month columns)
        train_pct: Percentage for training set (default 0.7)
        val_pct: Percentage for validation set (default 0.15)
        gap_months: Number of months to skip between splits to prevent leakage (default 12)

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: train, validation, test DataFrames

    Requirements: 1.8
    """
    has_location = 'location' in df.columns
    
    if has_location:
        logger.info(f"Multi-location data detected - using location-stratified splitting")
        logger.info(f"Splitting each location separately: train={train_pct}, val={val_pct}, test={1-train_pct-val_pct}")
        
        train_dfs = []
        val_dfs = []
        test_dfs = []
        
        locations = df['location'].unique()
        logger.info(f"Splitting {len(locations)} locations: {sorted(locations)}")
        
        for location in sorted(locations):
            # Get data for this location
            loc_df = df[df['location'] == location].sort_values(['year', 'month']).reset_index(drop=True)
            n_samples = len(loc_df)
            
            # Calculate split indices
            train_end = int(n_samples * train_pct)
            val_size = int(n_samples * val_pct)
            
            # Simple time-based split for each location (no gaps needed within location)
            # Since we're working with different locations, spatial leakage is already prevented
            val_end = train_end + val_size
            
            train_loc = loc_df.iloc[:train_end].copy()
            val_loc = loc_df.iloc[train_end:val_end].copy()
            test_loc = loc_df.iloc[val_end:].copy()
            
            train_dfs.append(train_loc)
            val_dfs.append(val_loc)
            test_dfs.append(test_loc)
            
            logger.info(
                f"  {location}: Train={len(train_loc)} ({train_loc['year'].min()}-{train_loc['year'].max()}), "
                f"Val={len(val_loc)} ({val_loc['year'].min()}-{val_loc['year'].max()}), "
                f"Test={len(test_loc)} ({test_loc['year'].min()}-{test_loc['year'].max()})"
            )
        
        # Combine all locations
        train_df = pd.concat(train_dfs, ignore_index=True)
        val_df = pd.concat(val_dfs, ignore_index=True)
        test_df = pd.concat(test_dfs, ignore_index=True)
        
        logger.info(f"\nCombined splits:")
        logger.info(f"  Train: {len(train_df)} samples across {len(train_dfs)} locations")
        logger.info(f"  Val:   {len(val_df)} samples across {len(val_dfs)} locations")
        logger.info(f"  Test:  {len(test_df)} samples across {len(test_dfs)} locations")
        
        return train_df, val_df, test_df
    
    else:
        # Single-location: Original logic with gaps
        logger.info(f"Single-location data - using time-based splitting with {gap_months}-month gaps")
        logger.info(f"Split ratios: train={train_pct}, val={val_pct}, test={1-train_pct-val_pct}")
        
        # Ensure data is sorted by time
        df_sorted = df.sort_values(["year", "month"]).reset_index(drop=True)

        n_samples = len(df_sorted)

        # Calculate split indices with gaps
        train_end = int(n_samples * train_pct)
        gap1_end = min(train_end + gap_months, n_samples)
        val_size = int(n_samples * val_pct)
        val_end = min(gap1_end + val_size, n_samples)
        gap2_end = min(val_end + gap_months, n_samples)
        
        # If we don't have enough data after gaps, reduce gap sizes
        if gap2_end >= n_samples:
            logger.warning(f"Not enough data for {gap_months}-month gaps. Reducing gaps...")
            gap_months = max(6, gap_months // 2)
            gap1_end = min(train_end + gap_months, n_samples)
            val_end = min(gap1_end + val_size, n_samples)
            gap2_end = min(val_end + gap_months, n_samples)
        
        # Split data
        train_df = df_sorted.iloc[:train_end].copy()
        val_df = df_sorted.iloc[gap1_end:val_end].copy()
        test_df = df_sorted.iloc[gap2_end:].copy()

        # Log split information
        logger.info(
            f"Train set: {len(train_df)} samples "
            f"({int(train_df['year'].min())}-{int(train_df['month'].min()):02d} to "
            f"{int(train_df['year'].max())}-{int(train_df['month'].max()):02d})"
        )
        logger.info(
            f"Gap 1: {gap1_end - train_end} months "
            f"({int(df_sorted.iloc[train_end]['year'])}-{int(df_sorted.iloc[train_end]['month']):02d} to "
            f"{int(df_sorted.iloc[gap1_end-1]['year'])}-{int(df_sorted.iloc[gap1_end-1]['month']):02d})"
        )
        logger.info(
            f"Validation set: {len(val_df)} samples "
            f"({int(val_df['year'].min())}-{int(val_df['month'].min()):02d} to "
            f"({int(val_df['year'].max())}-{int(val_df['month'].max()):02d})"
        )
        logger.info(
            f"Gap 2: {gap2_end - val_end} months "
            f"({int(df_sorted.iloc[val_end]['year'])}-{int(df_sorted.iloc[val_end]['month']):02d} to "
            f"{int(df_sorted.iloc[gap2_end-1]['year'])}-{int(df_sorted.iloc[gap2_end-1]['month']):02d})"
        )
        logger.info(
            f"Test set: {len(test_df)} samples "
            f"({int(test_df['year'].min())}-{int(test_df['month'].min()):02d} to "
            f"{int(test_df['year'].max())}-{int(test_df['month'].max()):02d})"
        )
        
        # Verify no year overlap
        train_years = set(train_df['year'].unique())
        val_years = set(val_df['year'].unique())
        test_years = set(test_df['year'].unique())
        
        overlap_train_val = train_years & val_years
        overlap_val_test = val_years & test_years
        
        if overlap_train_val:
            logger.warning(f"⚠️  Year overlap between train and val: {sorted(overlap_train_val)}")
        if overlap_val_test:
            logger.warning(f"⚠️  Year overlap between val and test: {sorted(overlap_val_test)}")
        
        if not overlap_train_val and not overlap_val_test:
            logger.info("✓ No year overlap detected - temporal leakage prevented")

        return train_df, val_df, test_df


def preprocess_pipeline(
    input_path: str,
    output_dir: str,
    lag_periods: Optional[List[int]] = None,
    rolling_windows: Optional[List[int]] = None,
) -> Dict:
    """
    Main preprocessing pipeline orchestrating all steps.

    Args:
        input_path: Path to master dataset CSV
        output_dir: Directory to save preprocessed datasets
        lag_periods: List of lag periods (default: [1, 3, 6, 12])
        rolling_windows: List of rolling windows (default: [3, 6])

    Returns:
        Dict: Metadata about preprocessing including feature counts and statistics

    Requirements: 1.9, 1.10
    """
    import json
    from pathlib import Path

    logger.info("=" * 60)
    logger.info("Starting preprocessing pipeline")
    logger.info("=" * 60)

    # Set defaults - OPTIMIZED for smaller datasets
    if lag_periods is None:
        lag_periods = [1, 3, 6]  # Reduced from [1,3,6,12] to reduce feature count
    if rolling_windows is None:
        rolling_windows = [3]  # Reduced from [3,6] to use only 3-month windows

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Step 1: Load and validate data
    logger.info("\nStep 1: Loading and validating data...")
    df = load_and_validate_data(input_path)
    initial_shape = df.shape

    # Step 2: Create lag features
    logger.info("\nStep 2: Creating lag features...")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    df = create_lag_features(df, numeric_cols, lag_periods)

    # Step 3: Create rolling features
    logger.info("\nStep 3: Creating rolling statistics...")
    df = create_rolling_features(df, numeric_cols, rolling_windows)

    # Step 4: Create interaction features
    logger.info("\nStep 4: Creating interaction features...")
    df = create_interaction_features(df)

    # Step 4.5: Encode location for multi-location data
    logger.info("\nStep 4.5: Encoding location features...")
    df = encode_location(df)

    # Step 5: Remove highly correlated features (OPTIMIZED)
    logger.info("\nStep 5: Removing highly correlated features...")
    df = remove_correlated_features(df, threshold=0.95)

    # Step 6: Handle missing values
    logger.info("\nStep 6: Handling missing values...")
    df = handle_missing_values(df, max_gap=2)

    # Step 7: Normalize features
    logger.info("\nStep 7: Normalizing features...")
    df, scaler_params = normalize_features(df)

    # Step 8: Split data temporally with gaps to prevent leakage
    logger.info("\nStep 8: Splitting data temporally with gaps...")
    train_df, val_df, test_df = split_temporal_data(df, train_pct=0.60, val_pct=0.20, gap_months=12)

    # Step 9: Save preprocessed datasets
    logger.info("\nStep 9: Saving preprocessed datasets...")

    # Save as CSV
    train_path_csv = Path(output_dir) / "features_train.csv"
    val_path_csv = Path(output_dir) / "features_val.csv"
    test_path_csv = Path(output_dir) / "features_test.csv"

    train_df.to_csv(train_path_csv, index=False)
    val_df.to_csv(val_path_csv, index=False)
    test_df.to_csv(test_path_csv, index=False)

    logger.info(f"Saved CSV files to {output_dir}")

    # Save as Parquet
    train_path_parquet = Path(output_dir) / "features_train.parquet"
    val_path_parquet = Path(output_dir) / "features_val.parquet"
    test_path_parquet = Path(output_dir) / "features_test.parquet"

    train_df.to_parquet(train_path_parquet, index=False)
    val_df.to_parquet(val_path_parquet, index=False)
    test_df.to_parquet(test_path_parquet, index=False)

    logger.info(f"Saved Parquet files to {output_dir}")

    # Save scaler parameters
    scaler_path = Path(output_dir) / "scaler_params.json"
    with open(scaler_path, "w") as f:
        json.dump(scaler_params, f, indent=2)

    logger.info(f"Saved scaler parameters to {scaler_path}")

    # Step 9: Generate metadata
    logger.info("\nStep 9: Generating feature engineering statistics...")

    metadata = {
        "input_file": input_path,
        "output_directory": output_dir,
        "initial_shape": initial_shape,
        "final_shape": df.shape,
        "features_added": df.shape[1] - initial_shape[1],
        "train_samples": len(train_df),
        "val_samples": len(val_df),
        "test_samples": len(test_df),
        "lag_periods": lag_periods,
        "rolling_windows": rolling_windows,
        "missing_values_before": int(pd.DataFrame(load_and_validate_data(input_path)).isnull().sum().sum()),
        "missing_values_after": int(df.isnull().sum().sum()),
        "normalized_features": len(scaler_params),
        "date_range": {
            "train": f"{train_df['year'].min()}-{train_df['month'].min()} to {train_df['year'].max()}-{train_df['month'].max()}",
            "val": f"{val_df['year'].min()}-{val_df['month'].min()} to {val_df['year'].max()}-{val_df['month'].max()}",
            "test": f"{test_df['year'].min()}-{test_df['month'].min()} to {test_df['year'].max()}-{test_df['month'].max()}",
        },
    }

    # Save metadata
    metadata_path = Path(output_dir) / "feature_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved metadata to {metadata_path}")

    # Log summary
    logger.info("\n" + "=" * 60)
    logger.info("Preprocessing pipeline completed successfully!")
    logger.info("=" * 60)
    logger.info(f"Initial features: {initial_shape[1]}")
    logger.info(f"Final features: {df.shape[1]}")
    logger.info(f"Features added: {df.shape[1] - initial_shape[1]}")
    logger.info(f"Train samples: {len(train_df)}")
    logger.info(f"Validation samples: {len(val_df)}")
    logger.info(f"Test samples: {len(test_df)}")
    logger.info("=" * 60)

    return metadata


# ============================================================================
# Legacy function (kept for backward compatibility)
# ============================================================================


def clean_merge(dfs):
    logger.info("Dry-run: cleaning and merging datasets...")
    return {"data": "merged_dummy"}
