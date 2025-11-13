"""
merge_processed.py

Merge all processed CSV outputs into a single master dataset.
Saves:
 - outputs/processed/master_dataset.csv
 - outputs/processed/master_dataset.parquet
"""

import pandas as pd
from pathlib import Path
from utils.config import get_output_path
from utils.validator import validate_dataframe
from utils.logger import log_info, log_error

PROC_DIR = get_output_path("processed")  # outputs/processed directory as Path

# mapping of expected files -> expected columns (used for lightweight checks)
SOURCE_FILES = {
    "nasa_power_processed.csv": None,   # None means accept whatever columns exist
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
    Returns the master DataFrame and saves CSV + parquet copies.
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

    # Prefer join on 'year' if available in at least two datasets
    df_list = list(dfs.values())
    year_count = sum(1 for df in df_list if "year" in df.columns)
    geo_count = sum(1 for df in df_list if {"latitude", "longitude"}.issubset(set(df.columns)))

    try:
        if year_count >= 2:
            # start from first dataframe that has year
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
                        merged = pd.merge(merged, df, on=["latitude", "longitude"], how="outer", suffixes=("_left", "_right"))
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
