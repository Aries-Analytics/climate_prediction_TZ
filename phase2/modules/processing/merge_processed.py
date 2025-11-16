"""
merge_processed.py

Merge all processed CSV outputs into a single master dataset.
Saves:
 - outputs/processed/master_dataset.csv
 - outputs/processed/master_dataset.parquet
"""

import pandas as pd

from utils.config import get_output_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe

PROC_DIR = get_output_path("processed")  # outputs/processed directory as Path

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
            return df
        except Exception as e:
            log_error(f"Failed to read {p}: {e}")
            raise
    else:
        log_info(f"Processed file not found (skipping): {fname}")
        return None


def merge_all():
    """
    Load available processed datasets and merge them into a master DataFrame.

    Discovers all processed CSV files in outputs/processed/, loads them, and merges
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
        If no processed files are found in outputs/processed/ directory.
    Exception
        If merging fails due to data incompatibility or other errors.

    Notes
    -----
    **Merging Strategy:**

    The function uses intelligent merging based on available columns:

    1. **Year-based merge** (if 2+ datasets have 'year' column):
       - Outer join on 'year' column
       - Preserves all data from all sources
       - Columns from different sources may have suffixes (_left, _right)

    2. **Geo-based merge** (if datasets have latitude/longitude):
       - Outer join on ['latitude', 'longitude']
       - Aligns data by spatial location

    3. **Concatenation fallback** (if no common keys):
       - Concatenates rows with _source_file column
       - Used when no common merge keys exist

    **Output Files:**

    - outputs/processed/master_dataset.csv
    - outputs/processed/master_dataset.parquet

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
        raise FileNotFoundError("No processed files found in outputs/processed/ to merge.")

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
            # Merge on both year and month (best for time-series data)
            for fname, df in dfs.items():
                if {"year", "month"}.issubset(set(df.columns)):
                    if merged is None:
                        merged = df.copy()
                        provenance.append(fname)
                    else:
                        merged = pd.merge(merged, df, on=["year", "month"], how="outer", suffixes=("_left", "_right"))
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

        # Basic validation: ensure it's a DataFrame and non-empty
        validate_dataframe(merged, expected_columns=None, dataset_name="Master Dataset")

        # Save outputs
        csv_path = get_output_path("processed", "master_dataset.csv")
        parquet_path = get_output_path("processed", "master_dataset.parquet")
        merged.to_csv(csv_path, index=False)
        merged.to_parquet(parquet_path, index=False)
        log_info(f"Master dataset written to: {csv_path} and {parquet_path}")

        return merged

    except Exception as e:
        log_error(f"Failed to merge processed datasets: {e}")
        raise
