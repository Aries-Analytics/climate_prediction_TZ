"""
merge_processed.py

Merge all processed CSV outputs into a single master dataset.
Saves:
 - outputs/processed/master_dataset.csv
 - outputs/processed/master_dataset.parquet

## Deduplication Strategy

This module implements a **validation-based** approach to duplicates rather than
automatic deduplication:

### Multi-Location Data (Current System)
- **Structure**: Multiple locations × time periods (e.g., 6 locations × 312 months = 1872 records)
- **Validation**: Checks (location, year, month) uniqueness
- **Behavior**: RAISES ERROR if true duplicates found (same location-year-month appearing multiple times)
- **Rationale**: Each location should have exactly one record per time period

### Single-Location Data
- **Structure**: Single time series (e.g., 312 months = 312 records)
- **Validation**: Checks (year, month) uniqueness
- **Behavior**: RAISES ERROR if duplicates found (same year-month appearing multiple times)
- **Rationale**: Each time period should appear exactly once

### Why Validation Instead of Automatic Deduplication?

1. **Data Integrity**: Duplicates indicate upstream processing errors that should be fixed at source
2. **Transparency**: Explicit errors are better than silent data loss
3. **Debugging**: Helps identify which processing module is creating duplicates
4. **Correctness**: Prevents masking data quality issues

### If True Duplicates Are Found

If validation fails, investigate the source:
1. Check which processing module created the duplicates
2. Fix the root cause in that module
3. Re-run the pipeline to regenerate clean data

### Merge Strategy

The merge operation uses pandas outer joins which naturally handle:
- **Missing data**: Preserves records even if not all sources have data for that time period
- **Multiple sources**: Combines data from different sources using suffixes (_left, _right)
- **Spatial joins**: Merges on location when available to maintain multi-location structure
"""

import pandas as pd

from utils.config import get_data_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe

PROC_DIR = get_data_path("processed")  # data/processed directory as Path

# mapping of expected files -> expected columns (used for lightweight checks)
SOURCE_FILES = {
    "nasa_power_processed.csv": None,  # None means accept whatever columns exist
    "era5_processed.csv": None,
    "chirps_processed.csv": None,
    "ndvi_processed.csv": None,
    "ocean_indices_processed.csv": None,
}


def _load_if_exists(fname: str):
    p = PROC_DIR / fname
    if p.exists():
        log_info(f"Loading processed file: {p}")
        try:
            df = pd.read_csv(p)
            # normalize column names
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            # Validate that year and month columns exist
            if "year" not in df.columns or "month" not in df.columns:
                log_error(f"File {fname} is missing required 'year' and/or 'month' columns")
                log_error(f"Available columns: {list(df.columns)}")
                raise ValueError(f"File {fname} missing required temporal columns (year, month)")

            return df
        except Exception as e:
            log_error(f"Failed to read {p}: {e}")
            raise
    else:
        log_info(f"Processed file not found (skipping): {fname}")
        return None


def _validate_no_true_duplicates(df: pd.DataFrame) -> None:
    """
    Validate that there are no true duplicate records in the merged dataset.

    For multi-location data, checks (location, year, month) uniqueness.
    For single-location data, checks (year, month) uniqueness.

    Parameters
    ----------
    df : pd.DataFrame
        Merged dataset to validate

    Raises
    ------
    ValueError
        If true duplicate records are found

    Notes
    -----
    This function distinguishes between:
    - **Multi-location data**: Multiple locations with same year-month (VALID)
    - **True duplicates**: Same location-year-month appearing multiple times (INVALID)
    """
    if "location" in df.columns:
        # Multi-location data: check (location, year, month) uniqueness
        duplicates = df.duplicated(subset=["location", "year", "month"], keep=False)
        if duplicates.sum() > 0:
            dup_count = duplicates.sum()
            sample = df[duplicates][["location", "year", "month"]].head(10)
            log_error(f"Found {dup_count} true duplicate (location, year, month) records")
            log_error(f"Sample duplicates:\n{sample}")
            raise ValueError(f"Dataset contains {dup_count} duplicate (location, year, month) records")
        else:
            # Log info about multi-location structure
            n_locations = df["location"].nunique()
            n_year_months = df[["year", "month"]].drop_duplicates().shape[0]
            log_info(
                f"Multi-location dataset validated: {n_locations} locations × "
                f"{n_year_months} time periods = {len(df)} records"
            )
    else:
        # Single-location data: check (year, month) uniqueness
        duplicates = df.duplicated(subset=["year", "month"], keep=False)
        if duplicates.sum() > 0:
            dup_count = duplicates.sum()
            sample = df[duplicates][["year", "month"]].head(10)
            log_error(f"Found {dup_count} duplicate (year, month) records")
            log_error(f"Sample duplicates:\n{sample}")
            raise ValueError(f"Dataset contains {dup_count} duplicate (year, month) records")
        else:
            log_info(f"Single-location dataset validated: {len(df)} unique time periods")


def merge_all():
    """
    Load available processed datasets and merge them into a master DataFrame.

    Discovers all processed CSV files in data/processed/, loads them, and merges
    using an intelligent strategy based on available columns. Adds provenance tracking
    and saves both CSV and Parquet formats.

    Returns
    -------
    pd.DataFrame
        Master dataset containing merged data from all available sources with additional column:
        - _provenance_files (str): Comma-separated list of source files used

    Raises
    ------
    FileNotFoundError
        If no processed files are found in data/processed/ directory.
    ValueError
        If duplicate records are found after merging.
    Exception
        If merging fails due to data incompatibility or other errors.

    Notes
    -----
    **Merging Strategy:**

    The function uses intelligent merging based on available columns:

    1. **Location-Year-Month merge** (if 2+ datasets have location, year, month):
       - Outer join on ['location', 'year', 'month']
       - Best for multi-location time-series data
       - Preserves spatial and temporal structure

    2. **Year-Month merge** (if 2+ datasets have year, month but no location):
       - Outer join on ['year', 'month']
       - For single-location time-series data

    3. **Year-only merge** (fallback if month not available):
       - Outer join on 'year' column
       - Preserves all data from all sources
       - Columns from different sources may have suffixes (_left, _right)

    4. **Geo-based merge** (if datasets have latitude/longitude):
       - Outer join on ['latitude', 'longitude']
       - Aligns data by spatial location

    5. **Concatenation fallback** (if no common keys):
       - Concatenates rows with _source_file column
       - Used when no common merge keys exist

    **Duplicate Detection:**

    After merging, validates that no true duplicates exist:
    - For multi-location data: Checks (location, year, month) uniqueness
    - For single-location data: Checks (year, month) uniqueness
    - Note: Multiple locations with same year-month is VALID, not a duplicate

    **Output Files:**

    - data/processed/master_dataset.csv
    - data/processed/master_dataset.parquet

    **Expected Source Files:**

    - nasa_power_processed.csv
    - era5_processed.csv
    - chirps_processed.csv
    - ndvi_processed.csv
    - ocean_indices_processed.csv

    **Resilience:**

    - Continues with available files if some are missing
    - Logs warnings for missing files
    - Normalizes column names (lowercase, strip whitespace, replace spaces with underscores)

    Examples
    --------
    >>> from modules.processing.merge_processed import merge_all
    >>>
    >>> # Merge all processed files
    >>> master_df = merge_all()
    >>> print(f"Master dataset has {len(master_df)} rows")
    >>> print(f"Columns: {list(master_df.columns)}")
    >>> print(f"Sources used: {master_df['_provenance_files'].iloc[0]}")
    """
    dfs = {}
    # load all available
    for fname in SOURCE_FILES.keys():
        df = _load_if_exists(fname)
        if df is not None:
            dfs[fname] = df

    if not dfs:
        raise FileNotFoundError("No processed files found in data/processed/ to merge.")

    # Heuristic merging strategy:
    # 1) If multiple frames contain 'year' column -> merge on 'year' (outer)
    # 2) Else if latitude/longitude present -> merge on ['latitude','longitude'] (outer)
    # 3) Otherwise perform a cartesian concat with provenance (less ideal)
    merged = None
    provenance = []

    # Prefer join on 'year' and 'month' if available in at least two datasets
    df_list = list(dfs.values())
    year_month_count = sum(1 for df in df_list if {"year", "month"}.issubset(set(df.columns)))
    year_count = sum(1 for df in df_list if "year" in df.columns)
    geo_count = sum(1 for df in df_list if {"latitude", "longitude"}.issubset(set(df.columns)))

    try:
        if year_month_count >= 2:
            # Merge on location, year, and month (best for multi-location time-series data)
            for fname, df in dfs.items():
                # Check for location column availability
                has_location = "location" in df.columns

                if merged is None:
                    merged = df.copy()
                    provenance.append(fname)
                else:
                    # Determine merge keys dynamically
                    merge_keys = ["year", "month"]
                    if has_location and "location" in merged.columns:
                        merge_keys = ["location", "year", "month"]
                    elif has_location:
                        # If merged doesn't have location but new df does, we might have issues
                        # But typically 'merged' starts with first df.
                        pass

                    if set(merge_keys).issubset(set(df.columns)):
                        # Avoid duplicate coordinate columns causing merge errors
                        for coord_col in ["location_lat", "location_lon", "latitude", "longitude"]:
                            if coord_col in df.columns and coord_col in merged.columns and coord_col not in merge_keys:
                                df = df.drop(columns=[coord_col])

                        merged = pd.merge(merged, df, on=merge_keys, how="outer", suffixes=("_left", "_right"))
                        provenance.append(fname)
        elif year_count >= 2:
            # Fallback: merge on year only
            for fname, df in dfs.items():
                if "year" in df.columns:
                    if merged is None:
                        merged = df.copy()
                        provenance.append(fname)
                    else:
                        merged = pd.merge(merged, df, on="year", how="outer", suffixes=("_left", "_right"))
                        provenance.append(fname)
        elif geo_count >= 1:
            # merge on lat/lon where possible
            for fname, df in dfs.items():
                if merged is None:
                    merged = df.copy()
                    provenance.append(fname)
                else:
                    if {"latitude", "longitude"}.issubset(set(df.columns)):
                        merged = pd.merge(
                            merged, df, on=["latitude", "longitude"], how="outer", suffixes=("_left", "_right")
                        )
                        provenance.append(fname)
                    else:
                        # concat columns (keep rows) - align by index
                        merged = pd.concat([merged, df], axis=1)
                        provenance.append(fname)
        else:
            # fallback: concat by rows with provenance
            to_concat = []
            for fname, df in dfs.items():
                df = df.copy()
                df["_source_file"] = fname
                to_concat.append(df)
                provenance.append(fname)
            merged = pd.concat(to_concat, axis=0, ignore_index=True)

        # add provenance column summarizing sources used
        merged["_provenance_files"] = ",".join(provenance)

        # Validate no true duplicates exist
        _validate_no_true_duplicates(merged)

        # Basic validation: ensure it's a DataFrame and non-empty
        validate_dataframe(merged, expected_columns=None, dataset_name="Master Dataset")

        # Save outputs
        csv_path = get_data_path("processed", "master_dataset.csv")
        parquet_path = get_data_path("processed", "master_dataset.parquet")
        merged.to_csv(csv_path, index=False)
        merged.to_parquet(parquet_path, index=False)
        log_info(f"Master dataset written to: {csv_path} and {parquet_path}")

        return merged

    except Exception as e:
        log_error(f"Failed to merge processed datasets: {e}")
        raise
