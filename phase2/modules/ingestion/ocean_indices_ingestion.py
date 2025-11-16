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

    Downloads and parses ONI (Oceanic Niño Index) and IOD (Indian Ocean Dipole) data
    from NOAA servers. These indices are key predictors for East African climate variability.

    Parameters
    ----------
    dry_run : bool, optional
        If True, return placeholder data without downloading. Default is False.
    start_year : int, optional
        Start year for data retrieval (inclusive). Default is 2010.
    end_year : int, optional
        End year for data retrieval (inclusive). Default is 2023.

    Returns
    -------
    pd.DataFrame
        DataFrame with monthly ocean indices data containing columns:
        - year (int): Year of observation
        - month (int): Month of observation (1-12)
        - oni (float): Oceanic Niño Index value (°C)
        - enso_phase (str): ENSO phase classification ("El Niño", "La Niña", or "Neutral")
        - iod (float): Indian Ocean Dipole index value (°C)

    Notes
    -----
    **Index Interpretations:**

    ONI (Oceanic Niño Index):
        - ONI ≥ +0.5°C: El Niño conditions (warmer than average Pacific)
        - -0.5°C to +0.5°C: Neutral conditions
        - ONI ≤ -0.5°C: La Niña conditions (cooler than average Pacific)

    IOD (Indian Ocean Dipole):
        - Positive IOD (> +0.4°C): Western Indian Ocean warmer - typically increases East African rainfall
        - Neutral IOD (-0.4°C to +0.4°C): Normal conditions
        - Negative IOD (< -0.4°C): Eastern Indian Ocean warmer - typically decreases East African rainfall

    **Climate Impacts on Tanzania:**

    - El Niño + Positive IOD: Significantly increased rainfall, potential flooding
    - La Niña + Negative IOD: Reduced rainfall, drought risk
    - El Niño alone: Moderately increased rainfall during short rains (Oct-Dec)
    - Positive IOD alone: Increased rainfall during short rains

    **Data Sources:**

    1. ONI Data: NOAA Climate Prediction Center
       - URL: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
       - Based on 3-month running mean of SST anomalies in Niño 3.4 region

    2. IOD Data: NOAA Physical Sciences Laboratory
       - URL: https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data
       - Dipole Mode Index (DMI) based on SST difference

    Examples
    --------
    >>> from modules.ingestion.ocean_indices_ingestion import fetch_ocean_indices_data
    >>>
    >>> # Fetch ocean indices data
    >>> df = fetch_ocean_indices_data(start_year=2020, end_year=2023)
    >>> print(f"Fetched {len(df)} monthly records")
    >>>
    >>> # Analyze ENSO phases
    >>> print(df['enso_phase'].value_counts())
    """
    log_info(f"Fetching ocean indices data... (dry run: {dry_run})")

    if dry_run:
        # Return placeholder data for testing
        df = pd.DataFrame(
            {
                "year": [2020, 2020, 2021, 2021],
                "month": [1, 6, 1, 6],
                "oni": [0.5, -0.3, 1.1, -0.8],
                "enso_phase": ["El Niño", "Neutral", "El Niño", "La Niña"],
                "iod": [0.2, -0.1, 0.5, -0.3],
            }
        )
        log_info("Dry run mode: returning placeholder data")
        return df

    try:
        # Fetch ONI (Oceanic Niño Index) - ENSO indicator
        log_info("Fetching ONI (ENSO) data from NOAA...")
        oni_df = None
        try:
            oni_data = _fetch_oni_data(start_year, end_year)
            if oni_data:
                oni_df = pd.DataFrame(oni_data)
                log_info(f"Successfully fetched {len(oni_data)} ONI records")
        except Exception as e:
            log_error(f"Failed to fetch ONI data: {e}")

        # Fetch IOD (Indian Ocean Dipole) data
        log_info("Fetching IOD data from NOAA...")
        iod_df = None
        try:
            iod_data = _fetch_iod_data(start_year, end_year)
            if iod_data:
                iod_df = pd.DataFrame(iod_data)
                log_info(f"Successfully fetched {len(iod_data)} IOD records")
        except Exception as e:
            log_error(f"Failed to fetch IOD data: {e}")

        # Merge the datasets
        if oni_df is not None and iod_df is not None:
            df = pd.merge(oni_df, iod_df, on=["year", "month"], how="outer")
        elif oni_df is not None:
            df = oni_df
        elif iod_df is not None:
            df = iod_df
        else:
            log_error("No ocean indices data was successfully downloaded")
            raise ValueError("Failed to fetch any ocean indices data")

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

    # Parse the ONI file format
    # Format: SEAS YR TOTAL ANOM
    # Example: DJF 1950 24.73 -1.53
    lines = response.text.strip().split("\n")
    data = []

    # Map season codes to middle month
    season_to_month = {
        "DJF": 1,
        "JFM": 2,
        "FMA": 3,
        "MAM": 4,
        "AMJ": 5,
        "MJJ": 6,
        "JJA": 7,
        "JAS": 8,
        "ASO": 9,
        "SON": 10,
        "OND": 11,
        "NDJ": 12,
    }

    for line in lines:
        # Skip header lines and empty lines
        if not line.strip() or "SEAS" in line or "Year" in line:
            continue

        parts = line.split()
        if len(parts) < 4:
            continue

        try:
            season = parts[0]
            year = int(parts[1])
            oni_value = float(parts[3])  # ANOM column

            if year < start_year or year > end_year:
                continue

            if season in season_to_month:
                month = season_to_month[season]
                data.append(
                    {"year": year, "month": month, "oni": round(oni_value, 3), "enso_phase": _classify_enso(oni_value)}
                )
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
        if not line.strip() or line.strip().startswith("#") or "Year" in line:
            continue

        parts = line.split()
        if len(parts) < 13:
            continue

        try:
            year = int(float(parts[0]))  # Handle potential decimal years
            if year < start_year or year > end_year:
                continue

            # Monthly values are in columns 1-12
            for month_idx in range(1, 13):
                try:
                    iod_value = float(parts[month_idx])
                    # Filter out missing data (usually -999 or similar)
                    if iod_value > -90:  # More lenient threshold
                        data.append({"year": year, "month": month_idx, "iod": round(iod_value, 3)})
                except (ValueError, IndexError):
                    continue
        except (ValueError, IndexError):
            continue

    return data


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
