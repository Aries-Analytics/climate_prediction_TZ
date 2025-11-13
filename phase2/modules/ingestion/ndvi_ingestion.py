import pandas as pd
from utils.logger import log_info, log_error
from utils.validator import validate_dataframe

def fetch_ndvi_data(dry_run=False):
    log_info("Fetching NDVI data... (dry run)" if dry_run else "Fetching NDVI data...")
    if dry_run:
        df = pd.DataFrame({
            "YEAR": [2020, 2021],
            "NDVI": [0.72, 0.75]
        })
    else:
        df = pd.DataFrame()  # placeholder

    validate_dataframe(df, expected_columns=["YEAR", "NDVI"], dataset_name="NDVI")
    log_info("NDVI data validated successfully.")
    return df
def fetch_data(*args, **kwargs):
    return fetch_ndvi_data(*args, **kwargs)
