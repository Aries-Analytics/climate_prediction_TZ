"""
Feature Engineering Pipeline

This module implements data loading, validation, and feature engineering
for the ML model development pipeline.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
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
    required_columns = ['year', 'month']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Validate data types
    if not pd.api.types.is_numeric_dtype(df['year']):
        raise ValueError("Column 'year' must be numeric")
    
    if not pd.api.types.is_numeric_dtype(df['month']):
        raise ValueError("Column 'month' must be numeric")
    
    # Validate year and month ranges
    if df['year'].min() < 1900 or df['year'].max() > 2100:
        raise ValueError(f"Year values out of valid range: {df['year'].min()} - {df['year'].max()}")
    
    if df['month'].min() < 1 or df['month'].max() > 12:
        raise ValueError(f"Month values out of valid range: {df['month'].min()} - {df['month'].max()}")
    
    # Check for duplicate time periods
    duplicates = df.duplicated(subset=['year', 'month'], keep=False)
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
        required_columns = ['year', 'month']
    
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
        if dtype == 'object':
            # Try to identify if it should be numeric
            try:
                pd.to_numeric(df[col], errors='raise')
                logger.warning(f"Column '{col}' is object type but could be numeric")
            except (ValueError, TypeError):
                pass
    
    numeric_count = sum(1 for dtype in type_summary.values() if 'int' in dtype or 'float' in dtype)
    logger.info(f"Data types: {numeric_count} numeric, {len(type_summary) - numeric_count} non-numeric")
    
    return type_summary


# ============================================================================
# Feature Engineering Functions (Task 2.2-2.7)
# ============================================================================

def create_lag_features(df: pd.DataFrame, columns: List[str], lags: List[int]) -> pd.DataFrame:
    """
    Create lag features for specified columns.
    
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
    
    # Ensure data is sorted by time
    df_lagged = df_lagged.sort_values(['year', 'month']).reset_index(drop=True)
    
    # Identify key variables for lagging
    key_variables = []
    for col in columns:
        # Match columns containing key climate variables
        if any(keyword in col.lower() for keyword in ['temp', 'rainfall', 'precip', 'ndvi', 'oni', 'enso', 'iod']):
            key_variables.append(col)
    
    if not key_variables:
        logger.warning(f"No matching columns found for lag features from: {columns[:5]}...")
        key_variables = [col for col in columns if col in df.columns][:10]  # Take first 10 if no matches
    
    logger.info(f"Creating lags for {len(key_variables)} key variables")
    
    features_created = 0
    for col in key_variables:
        if col not in df_lagged.columns:
            continue
            
        for lag in lags:
            lag_col_name = f"{col}_lag_{lag}"
            df_lagged[lag_col_name] = df_lagged[col].shift(lag)
            features_created += 1
    
    logger.info(f"Created {features_created} lag features")
    
    return df_lagged


def create_rolling_features(df: pd.DataFrame, columns: List[str], windows: List[int]) -> pd.DataFrame:
    """
    Create rolling mean and standard deviation features.
    
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
    
    # Ensure data is sorted by time
    df_rolling = df_rolling.sort_values(['year', 'month']).reset_index(drop=True)
    
    # Identify numeric columns for rolling statistics
    numeric_cols = df_rolling.select_dtypes(include=[np.number]).columns.tolist()
    
    # Filter to key variables
    key_variables = []
    for col in columns:
        if col in numeric_cols and any(keyword in col.lower() for keyword in 
                                       ['temp', 'rainfall', 'precip', 'ndvi', 'humidity', 'solar']):
            key_variables.append(col)
    
    if not key_variables:
        logger.warning(f"No matching numeric columns found for rolling features")
        key_variables = [col for col in columns if col in numeric_cols][:10]
    
    logger.info(f"Creating rolling features for {len(key_variables)} key variables")
    
    features_created = 0
    for col in key_variables:
        if col not in df_rolling.columns:
            continue
            
        for window in windows:
            # Rolling mean
            mean_col_name = f"{col}_rolling_mean_{window}"
            df_rolling[mean_col_name] = df_rolling[col].rolling(window=window, min_periods=1).mean()
            features_created += 1
            
            # Rolling standard deviation
            std_col_name = f"{col}_rolling_std_{window}"
            df_rolling[std_col_name] = df_rolling[col].rolling(window=window, min_periods=1).std()
            features_created += 1
    
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
    enso_cols = [col for col in numeric_cols if 'oni' in col.lower() or 'enso' in col.lower()]
    rainfall_cols = [col for col in numeric_cols if 'rainfall' in col.lower() or 'precip' in col.lower()]
    
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
    iod_cols = [col for col in numeric_cols if 'iod' in col.lower()]
    ndvi_cols = [col for col in numeric_cols if 'ndvi' in col.lower() and col in numeric_cols]
    
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
    df_filled = df_filled.sort_values(['year', 'month']).reset_index(drop=True)
    
    # Get numeric columns only
    numeric_cols = df_filled.select_dtypes(include=[np.number]).columns.tolist()
    
    # Track imputation statistics
    imputation_stats = {}
    
    for col in numeric_cols:
        if col in ['year', 'month']:
            continue
            
        missing_before = df_filled[col].isnull().sum()
        
        if missing_before > 0:
            # Forward fill with limit
            df_filled[col] = df_filled[col].fillna(method='ffill', limit=max_gap)
            
            missing_after = df_filled[col].isnull().sum()
            imputed_count = missing_before - missing_after
            
            if imputed_count > 0:
                imputation_stats[col] = {
                    'missing_before': int(missing_before),
                    'imputed': int(imputed_count),
                    'still_missing': int(missing_after)
                }
    
    total_imputed = sum(stats['imputed'] for stats in imputation_stats.values())
    logger.info(f"Imputed {total_imputed} values across {len(imputation_stats)} columns")
    
    # Log columns with remaining missing values
    still_missing = {col: stats['still_missing'] for col, stats in imputation_stats.items() 
                     if stats['still_missing'] > 0}
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
        exclude_cols = ['year', 'month']
    else:
        exclude_cols = list(set(exclude_cols + ['year', 'month']))
    
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
            'mean': float(mean_val) if not pd.isna(mean_val) else 0.0,
            'std': float(std_val) if not pd.isna(std_val) else 1.0
        }
        
        # Normalize (z-score)
        if std_val > 0 and not pd.isna(std_val):
            df_normalized[col] = (df_normalized[col] - mean_val) / std_val
        else:
            logger.warning(f"Column '{col}' has zero or NaN std, skipping normalization")
    
    logger.info(f"Normalized {len(scaler_params)} features")
    
    return df_normalized, scaler_params


def split_temporal_data(df: pd.DataFrame, train_pct: float = 0.7, 
                       val_pct: float = 0.15) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into train/validation/test sets maintaining chronological order.
    
    Args:
        df: Input DataFrame (must have year and month columns)
        train_pct: Percentage for training set (default 0.7)
        val_pct: Percentage for validation set (default 0.15)
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: train, validation, test DataFrames
        
    Requirements: 1.8
    """
    logger.info(f"Splitting data temporally: train={train_pct}, val={val_pct}, test={1-train_pct-val_pct}")
    
    # Ensure data is sorted by time
    df_sorted = df.sort_values(['year', 'month']).reset_index(drop=True)
    
    n_samples = len(df_sorted)
    
    # Calculate split indices
    train_end = int(n_samples * train_pct)
    val_end = int(n_samples * (train_pct + val_pct))
    
    # Split data
    train_df = df_sorted.iloc[:train_end].copy()
    val_df = df_sorted.iloc[train_end:val_end].copy()
    test_df = df_sorted.iloc[val_end:].copy()
    
    # Log split information
    logger.info(f"Train set: {len(train_df)} samples "
                f"({train_df['year'].min()}-{train_df['month'].min()} to "
                f"{train_df['year'].max()}-{train_df['month'].max()})")
    logger.info(f"Validation set: {len(val_df)} samples "
                f"({val_df['year'].min()}-{val_df['month'].min()} to "
                f"{val_df['year'].max()}-{val_df['month'].max()})")
    logger.info(f"Test set: {len(test_df)} samples "
                f"({test_df['year'].min()}-{test_df['month'].min()} to "
                f"{test_df['year'].max()}-{test_df['month'].max()})")
    
    return train_df, val_df, test_df


def preprocess_pipeline(input_path: str, output_dir: str, 
                       lag_periods: Optional[List[int]] = None,
                       rolling_windows: Optional[List[int]] = None) -> Dict:
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
    
    # Set defaults
    if lag_periods is None:
        lag_periods = [1, 3, 6, 12]
    if rolling_windows is None:
        rolling_windows = [3, 6]
    
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
    
    # Step 5: Handle missing values
    logger.info("\nStep 5: Handling missing values...")
    df = handle_missing_values(df, max_gap=2)
    
    # Step 6: Normalize features
    logger.info("\nStep 6: Normalizing features...")
    df, scaler_params = normalize_features(df)
    
    # Step 7: Split data temporally
    logger.info("\nStep 7: Splitting data temporally...")
    train_df, val_df, test_df = split_temporal_data(df, train_pct=0.7, val_pct=0.15)
    
    # Step 8: Save preprocessed datasets
    logger.info("\nStep 8: Saving preprocessed datasets...")
    
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
    with open(scaler_path, 'w') as f:
        json.dump(scaler_params, f, indent=2)
    
    logger.info(f"Saved scaler parameters to {scaler_path}")
    
    # Step 9: Generate metadata
    logger.info("\nStep 9: Generating feature engineering statistics...")
    
    metadata = {
        'input_file': input_path,
        'output_directory': output_dir,
        'initial_shape': initial_shape,
        'final_shape': df.shape,
        'features_added': df.shape[1] - initial_shape[1],
        'train_samples': len(train_df),
        'val_samples': len(val_df),
        'test_samples': len(test_df),
        'lag_periods': lag_periods,
        'rolling_windows': rolling_windows,
        'missing_values_before': int(pd.DataFrame(load_and_validate_data(input_path)).isnull().sum().sum()),
        'missing_values_after': int(df.isnull().sum().sum()),
        'normalized_features': len(scaler_params),
        'date_range': {
            'train': f"{train_df['year'].min()}-{train_df['month'].min()} to {train_df['year'].max()}-{train_df['month'].max()}",
            'val': f"{val_df['year'].min()}-{val_df['month'].min()} to {val_df['year'].max()}-{val_df['month'].max()}",
            'test': f"{test_df['year'].min()}-{test_df['month'].min()} to {test_df['year'].max()}-{test_df['month'].max()}"
        }
    }
    
    # Save metadata
    metadata_path = Path(output_dir) / "feature_metadata.json"
    with open(metadata_path, 'w') as f:
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
