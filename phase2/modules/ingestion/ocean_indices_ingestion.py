import pandas as pd

from utils.logger import log_info
from utils.validator import validate_dataframe


def fetch_ocean_indices_data(dry_run=False):
    log_info("Fetching ocean indices data... (dry run)" if dry_run else "Fetching ocean indices data...")
    if dry_run:
        df = pd.DataFrame({"YEAR": [2020, 2021], "ENSO_INDEX": [1.1, -0.3]})
    else:
        df = pd.DataFrame()  # placeholder

    validate_dataframe(df, expected_columns=["YEAR", "ENSO_INDEX"], dataset_name="Ocean Indices")
    log_info("Ocean Indices data validated successfully.")
    return df


def fetch_data(*args, **kwargs):
    return fetch_ocean_indices_data(*args, **kwargs)
