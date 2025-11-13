import pandas as pd

from utils.logger import log_info
from utils.validator import validate_dataframe


def fetch_chirps_data(dry_run=False):
    log_info("Fetching CHIRPS data... (dry run)" if dry_run else "Fetching CHIRPS data...")
    if dry_run:
        df = pd.DataFrame({"YEAR": [2020, 2021], "RAINFALL": [900, 1100]})
    else:
        df = pd.DataFrame()  # placeholder

    validate_dataframe(df, expected_columns=["YEAR", "RAINFALL"], dataset_name="CHIRPS")
    log_info("CHIRPS data validated successfully.")
    return df


def fetch_data(*args, **kwargs):
    return fetch_chirps_data(*args, **kwargs)
