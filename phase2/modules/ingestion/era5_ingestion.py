import pandas as pd

from utils.logger import log_info
from utils.validator import validate_dataframe


def fetch_era5_data(dry_run=False):
    log_info("Fetching ERA5 data... (dry run)" if dry_run else "Fetching ERA5 data...")
    if dry_run:
        df = pd.DataFrame({"YEAR": [2020, 2021], "TEMP": [23.5, 24.2], "HUMIDITY": [70, 72]})
    else:
        df = pd.DataFrame()  # placeholder

    validate_dataframe(df, expected_columns=["YEAR", "TEMP", "HUMIDITY"], dataset_name="ERA5")
    log_info("ERA5 data validated successfully.")
    return df


def fetch_data(*args, **kwargs):
    return fetch_era5_data(*args, **kwargs)
