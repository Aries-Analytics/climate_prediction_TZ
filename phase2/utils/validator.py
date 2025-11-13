"""
validator.py

Utility module for validating input DataFrames in the Tanzania Climate Prediction pipeline.
Ensures consistency of expected columns, datatypes, and structural integrity across ingestion
and processing stages.

This module is lightweight but designed for extensibility — ready for deeper
validation once real data (from CHIRPS, NASA POWER, ERA5, NDVI, and Ocean Indices)
is integrated beyond the dry-run stage.
"""

import pandas as pd
from utils.logger import log_info, log_error


def validate_dataframe(df: pd.DataFrame, expected_columns: list = None, dataset_name: str = "Dataset") -> bool:
    """
    Validates that a given DataFrame contains all expected columns and no unexpected null structure.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to validate.
    expected_columns : list, optional
        List of column names expected in the DataFrame. If None, skips column validation.
    dataset_name : str
        Optional; the friendly name of the dataset being validated (for clearer logging).

    Returns
    -------
    bool
        True if validation passes, raises ValueError otherwise.
    """
    log_info(f"[VALIDATION] Starting validation for {dataset_name}...")

    # --- 1. Structure Check ---
    if not isinstance(df, pd.DataFrame):
        msg = f"[ERROR] {dataset_name} is not a valid pandas DataFrame."
        log_error(msg)
        raise ValueError(msg)

    # --- 2. Column Check ---
    if expected_columns is not None:
        missing_cols = [col for col in expected_columns if col not in df.columns]
        if missing_cols:
            msg = f"[ERROR] {dataset_name} missing expected columns: {missing_cols}"
            log_error(msg)
            raise ValueError(msg)

    # --- 3. Empty Check ---
    if df.empty:
        msg = f"[ERROR] {dataset_name} DataFrame is empty."
        log_error(msg)
        raise ValueError(msg)

    # --- 4. Optional: Type Sanity (light check for dry-run) ---
    if len(df) > 0:
        null_summary = df.isnull().sum()
        if null_summary.sum() > 0:
            log_info(f"[WARNING] {dataset_name} contains missing values in: "
                     f"{list(null_summary[null_summary > 0].index)}")

    log_info(f"[VALIDATION] {dataset_name} passed validation with {len(df)} rows and columns: {list(df.columns)}")
    return True
