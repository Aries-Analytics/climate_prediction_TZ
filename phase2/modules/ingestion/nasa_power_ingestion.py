"""
NASA POWER Ingestion - Phase 2 (dry-run compatible)
"""

import pandas as pd

from utils.config import get_data_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe


def fetch_nasa_power_data(dry_run=False, *args, **kwargs):
    """
    Fetch NASA POWER data (dry-run placeholder).
    Returns a pandas DataFrame (or raise on error).
    """
    log_info("Fetching NASA POWER data... (dry run)" if dry_run else "Fetching NASA POWER data...")
    if dry_run:
        df = pd.DataFrame({"YEAR": [2020, 2021], "TEMP": [24.5, 25.0], "RADIATION": [200, 210]})
    else:
        # Real ingestion logic will go here later; keep placeholder DataFrame for now
        df = pd.DataFrame()

    # Basic validation (lightweight for dry-run)
    try:
        validate_dataframe(df, expected_columns=list(df.columns), dataset_name="NASA POWER")
    except Exception as e:
        log_error(f"NASA POWER validation failed: {e}")
        # re-raise so pipeline notices the failure
        raise

    # Optionally show where we'd save raw data
    data_path = get_data_path("raw", "nasa_power_raw.csv")
    log_info(f"(dry-run) would save raw NASA POWER data to: {data_path}")

    return df


# compatibility wrapper expected by run_pipeline
def fetch_data(*args, **kwargs):
    return fetch_nasa_power_data(*args, **kwargs)
