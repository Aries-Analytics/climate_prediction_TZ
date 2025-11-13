"""
NASA POWER Ingestion - Phase 2
Fetches climate data from NASA POWER API for Tanzania region
"""

import os

import pandas as pd
import requests

from utils.config import get_data_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe

# Tanzania bounding box (approximate)
TANZANIA_LAT = -6.369028  # Central latitude
TANZANIA_LON = 34.888822  # Central longitude

# NASA POWER API endpoint (using daily data, will aggregate to monthly)
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch_nasa_power_data(
    dry_run=False,
    latitude=TANZANIA_LAT,
    longitude=TANZANIA_LON,
    start_year=2010,
    end_year=2023,
    parameters=None,
    *args,
    **kwargs,
):
    """
    Fetch NASA POWER climate data for specified location and time range.

    Args:
        dry_run: If True, return placeholder data without API call
        latitude: Latitude coordinate (default: Tanzania center)
        longitude: Longitude coordinate (default: Tanzania center)
        start_year: Start year for data retrieval
        end_year: End year for data retrieval
        parameters: List of climate parameters to fetch (default: temperature and radiation)

    Returns:
        pandas DataFrame with climate data
    """
    log_info(f"Fetching NASA POWER data... (dry run: {dry_run})")

    if dry_run:
        # Return placeholder data for testing
        df = pd.DataFrame({"YEAR": [2020, 2021], "TEMP": [24.5, 25.0], "RADIATION": [200, 210]})
        log_info("Dry run mode: returning placeholder data")
        return df

    # Default parameters if not specified
    if parameters is None:
        parameters = [
            "T2M",  # Temperature at 2 Meters
            "T2M_MAX",  # Maximum Temperature at 2 Meters
            "T2M_MIN",  # Minimum Temperature at 2 Meters
            "PRECTOTCORR",  # Precipitation Corrected
            "RH2M",  # Relative Humidity at 2 Meters
            "ALLSKY_SFC_SW_DWN",  # All Sky Surface Shortwave Downward Irradiance
        ]

    # Build API request
    params_str = ",".join(parameters)
    start_date = f"{start_year}0101"  # YYYYMMDD format
    end_date = f"{end_year}1231"  # YYYYMMDD format

    url = f"{NASA_POWER_BASE_URL}"
    params = {
        "parameters": params_str,
        "community": "AG",  # Agroclimatology community
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date,
        "end": end_date,
        "format": "JSON",
    }

    try:
        log_info(f"Requesting NASA POWER data for lat={latitude}, lon={longitude}, years={start_year}-{end_year}")
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()

        # Extract parameter data from response
        if "properties" not in data or "parameter" not in data["properties"]:
            raise ValueError("Unexpected API response structure")

        parameter_data = data["properties"]["parameter"]

        # Convert to DataFrame (daily data)
        daily_records = []
        for param_name, param_values in parameter_data.items():
            for date_str, value in param_values.items():
                # Parse date (format: YYYYMMDD)
                if len(date_str) == 8:
                    year = int(date_str[:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])

                    # Find or create record for this date
                    record = next(
                        (r for r in daily_records if r["year"] == year and r["month"] == month and r["day"] == day),
                        None,
                    )
                    if record is None:
                        record = {
                            "year": year,
                            "month": month,
                            "day": day,
                            "latitude": latitude,
                            "longitude": longitude,
                        }
                        daily_records.append(record)

                    # Add parameter value (-999 is missing data flag)
                    record[param_name.lower()] = value if value != -999 else None

        daily_df = pd.DataFrame(daily_records)

        if daily_df.empty:
            log_error("No data returned from NASA POWER API")
            raise ValueError("Empty dataset returned from API")

        # Aggregate daily data to monthly averages
        agg_dict = {}
        for col in daily_df.columns:
            if col not in ["year", "month", "day", "latitude", "longitude"]:
                # Use mean for temperature and radiation, sum for precipitation
                if "prec" in col.lower():
                    agg_dict[col] = "sum"
                else:
                    agg_dict[col] = "mean"

        # Add latitude and longitude to aggregation (take first value)
        agg_dict["latitude"] = "first"
        agg_dict["longitude"] = "first"

        df = daily_df.groupby(["year", "month"]).agg(agg_dict).reset_index()

        if df.empty:
            log_error("No data returned from NASA POWER API")
            raise ValueError("Empty dataset returned from API")

        # Sort by year and month
        df = df.sort_values(["year", "month"]).reset_index(drop=True)

        log_info(f"Successfully fetched {len(df)} records from NASA POWER API")

        # Validate the dataframe
        expected_cols = ["year", "month", "latitude", "longitude"]
        validate_dataframe(df, expected_columns=expected_cols, dataset_name="NASA POWER")

        # Save raw data
        data_path = get_data_path("raw", "nasa_power_raw.csv")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        df.to_csv(data_path, index=False)
        log_info(f"Raw NASA POWER data saved to: {data_path}")

        return df

    except requests.exceptions.RequestException as e:
        log_error(f"Failed to fetch NASA POWER data: {e}")
        raise
    except Exception as e:
        log_error(f"Error processing NASA POWER data: {e}")
        raise


# compatibility wrapper expected by run_pipeline
def fetch_data(*args, **kwargs):
    return fetch_nasa_power_data(*args, **kwargs)
