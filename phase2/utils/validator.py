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

from utils.logger import log_error, log_info


def validate_dataframe(df: pd.DataFrame, expected_columns: list = None, dataset_name: str = "Dataset") -> bool:
    """
    Validate DataFrame structure, columns, and data integrity.

    Performs comprehensive validation checks on pandas DataFrames to ensure data quality
    and consistency across the pipeline.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to validate.
    expected_columns : list of str, optional
        List of column names expected in the DataFrame. If None, skips column validation.
    dataset_name : str, optional
        Friendly name of the dataset for logging purposes. Default is "Dataset".

    Returns
    -------
    bool
        True if validation passes.

    Raises
    ------
    ValueError
        If validation fails with detailed error message indicating the issue:
        - Not a valid pandas DataFrame
        - Missing expected columns
        - DataFrame is empty

    Notes
    -----
    **Validation Checks:**

    1. **Structure Check**: Verifies input is a pandas DataFrame
    2. **Column Check**: Ensures all expected columns exist (if specified)
    3. **Empty Check**: Verifies DataFrame has at least one row
    4. **Missing Values**: Logs warning if missing values detected (does not fail)

    **Logging:**

    - Logs validation start and completion
    - Logs warnings for missing values
    - Logs errors for validation failures
    - Includes row count and column list in success message

    Examples
    --------
    >>> import pandas as pd
    >>> from utils.validator import validate_dataframe
    >>>
    >>> # Basic validation
    >>> df = pd.DataFrame({'year': [2020, 2021], 'temp': [25.3, 26.1]})
    >>> validate_dataframe(df, dataset_name="Temperature Data")
    True
    >>>
    >>> # Validation with expected columns
    >>> validate_dataframe(
    ...     df,
    ...     expected_columns=['year', 'temp'],
    ...     dataset_name="Temperature Data"
    ... )
    True
    >>>
    >>> # Validation failure example
    >>> empty_df = pd.DataFrame()
    >>> validate_dataframe(empty_df)  # Raises ValueError
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
            log_info(
                f"[WARNING] {dataset_name} contains missing values in: " f"{list(null_summary[null_summary > 0].index)}"
            )

    log_info(f"[VALIDATION] {dataset_name} passed validation with {len(df)} rows and columns: {list(df.columns)}")
    return True
