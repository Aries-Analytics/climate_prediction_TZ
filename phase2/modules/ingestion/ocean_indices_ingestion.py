"""
Ocean Indices Ingestion - Phase 2
Fetches ocean climate indices (ENSO, IOD) that influence East African climate.
Data sources: NOAA Climate Prediction Center
"""

import os

import pandas as pd
import requests

from utils.config import get_data_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe

# NOAA Climate Prediction Center URLs
ENSO_ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
ENSO_MEI_URL = "https://psl.noaa.gov/enso/mei/data/meiv2.data"
IOD_URL = "https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data"


def fetch_ocean_indices_data(
    dry_run=False,
    start_year=2010,
    end_year=2023,
    *args,
    **kwargs,
):
    """
    Fetch ocean climate indices data from NOAA.

    Fetches:
    - ONI (Oceanic Niño Index) - primary ENSO indicator
    - IOD (Indian Ocean Dipole) - influences East African rainfall

    Args:
        dry_run: If True, return placeholder data without downloading
        start_year: Start year for data retrieval
        end_year: End year for data retrieval

    Returns:
        pandas DataFrame with ocean indices data

    Note:
        Data is freely available from NOAA without authentication.
        ENSO and IOD indices are key predictors for East African climate.
    """
    log_info(f"Fetching ocean indices data... (dry run: {dry_run})")

    if dry_run:
        # Return placeholder data for testing
        df = pd.DataFrame({"YEAR": [2020, 2021], "ENSO_INDEX": [1.1, -0.3]})
        log_info("Dry run mode: returning placeholder data")
        return df

    try:
        all_data = []

        # Fetch ONI (Oceanic Niño Index) - ENSO indicator
        log_info("Fetching ONI (ENSO) data from NOAA...")
        try:
            oni_data = _fetch_oni_data(start_year, end_year)
            all_data.extend(oni_data)
            log_info(f"Successfully fetched {len(oni_data)} ONI records")
        except Exception as e:
            log_error(f"Failed to fetch ONI data: {e}")

        # Fetch IOD (Indian Ocean Dipole) data
        log_info("Fetching IOD data from NOAA...")
        try:
            iod_data = _fetch_iod_data(start_year, end_year)
            # Merge IOD data with ONI data
            if all_data and iod_data:
                all_data = _merge_indices(all_data, iod_data)
            log_info("Successfully fetched IOD data")
        except Exception as e:
            log_error(f"Failed to fetch IOD data: {e}")

        if not all_data:
            log_error("No ocean indices data was successfully downloaded")
            raise ValueError("Failed to fetch any ocean indices data")

        # Create DataFrame
        df = pd.DataFrame(all_data)
        df = df.sort_values(["year", "month"]).reset_index(drop=True)

        log_info(f"Successfully fetched {len(df)} ocean indices records")

        # Validate the dataframe
        expected_cols = ["year", "month"]
        validate_dataframe(df, expected_columns=expected_cols, dataset_name="Ocean Indices")

        # Save raw data
        csv_path = get_data_path("raw", "ocean_indices_raw.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
        log_info(f"Ocean indices data saved to: {csv_path}")

        return df

    except Exception as e:
        log_error(f"Failed to fetch ocean indices data: {e}")
        raise


def _fetch_oni_data(start_year, end_year):
    """Fetch ONI (Oceanic Niño Index) data from NOAA CPC."""
    response = requests.get(ENSO_ONI_URL, timeout=30)
    response.raise_for_status()

    # Parse the fixed-width format file
    lines = response.text.strip().split("\n")
    data = []

    for line in lines:
        # Skip header lines
        if line.startswith("Year") or not line.strip():
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        try:
            year = int(parts[0])
            if year < start_year or year > end_year:
                continue

            # ONI file has seasonal values (DJF, JFM, FMA, etc.)
            # We'll extract the monthly values
            for month in range(1, 13):
                if month < len(parts):
                    try:
                        oni_value = float(parts[month])
                        data.append(
                            {"year": year, "month": month, "oni": oni_value, "enso_phase": _classify_enso(oni_value)}
                        )
                    except (ValueError, IndexError):
                        continue
        except (ValueError, IndexError):
            continue

    return data


def _fetch_iod_data(start_year, end_year):
    """Fetch IOD (Indian Ocean Dipole) data from NOAA PSL."""
    response = requests.get(IOD_URL, timeout=30)
    response.raise_for_status()

    lines = response.text.strip().split("\n")
    data = []

    for line in lines:
        # Skip header/comment lines
        if not line.strip() or line.strip().startswith("#"):
            continue

        parts = line.split()
        if len(parts) < 13:
            continue

        try:
            year = int(parts[0])
            if year < start_year or year > end_year:
                continue

            # Monthly values are in columns 1-12
            for month in range(1, 13):
                try:
                    iod_value = float(parts[month])
                    # Filter out missing data (usually -999 or similar)
                    if iod_value > -99:
                        data.append({"year": year, "month": month, "iod": iod_value})
                except (ValueError, IndexError):
                    continue
        except (ValueError, IndexError):
            continue

    return data


def _merge_indices(oni_data, iod_data):
    """Merge ONI and IOD data by year and month."""
    # Convert to DataFrames for easier merging
    oni_df = pd.DataFrame(oni_data)
    iod_df = pd.DataFrame(iod_data)

    # Merge on year and month
    merged = pd.merge(oni_df, iod_df, on=["year", "month"], how="outer")

    return merged.to_dict("records")


def _classify_enso(oni_value):
    """Classify ENSO phase based on ONI value."""
    if oni_value >= 0.5:
        return "El Niño"
    elif oni_value <= -0.5:
        return "La Niña"
    else:
        return "Neutral"


def fetch_data(*args, **kwargs):
    return fetch_ocean_indices_data(*args, **kwargs)
