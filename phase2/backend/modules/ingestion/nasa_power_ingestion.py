"""
NASA POWER Ingestion - Phase 2
Fetches climate data from NASA POWER API for Tanzania region.

TZ CONTRACT: This module follows the ingestion tz-naive `date` contract.
See `utils/dates.py` for the full contract. All date parameters are
coerced to tz-naive `date` objects at entry; no `datetime.now(timezone.utc)`
or `tz_localize` calls anywhere below the public API boundary.
"""

import os
import time
from datetime import date
from typing import Optional, Tuple

import pandas as pd
import requests
from sqlalchemy.orm import Session

from utils.config import get_data_path
from utils.dates import as_date, last_complete_month
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe

# Kilombero Basin pilot zones (Apr 2026 two-zone split)
# Replaces single Morogoro city point with actual basin coordinates.
PILOT_LOCATIONS = [
    {"name": "Ifakara TC", "lat": -8.1333, "lon": 36.6833},
    {"name": "Mlimba DC", "lat": -8.0167, "lon": 35.9500},
]

# Default coordinate kept for fetch_nasa_power_data() backward compat
TANZANIA_LAT = PILOT_LOCATIONS[0]["lat"]
TANZANIA_LON = PILOT_LOCATIONS[0]["lon"]

# NASA POWER API endpoint (using daily data, will aggregate to monthly)
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch_nasa_power_data(
    dry_run=False,
    latitude=TANZANIA_LAT,
    longitude=TANZANIA_LON,
    start_year=1985,
    end_year=2025,
    parameters=None,
    *args,
    **kwargs,
):
    """
    Fetch NASA POWER climate data for specified location and time range.

    Retrieves daily climate data from NASA POWER API and aggregates to monthly values.
    Data includes temperature, precipitation, humidity, and solar radiation.

    Parameters
    ----------
    dry_run : bool, optional
        If True, return placeholder data without making API call. Default is False.
    latitude : float, optional
        Latitude coordinate for data retrieval. Default is Morogoro (-6.8211).
    longitude : float, optional
        Longitude coordinate for data retrieval. Default is Morogoro (37.6595).
    start_year : int, optional
        Start year for data retrieval (inclusive). Default is 2010.
    end_year : int, optional
        End year for data retrieval (inclusive). Default is 2023.
    parameters : list of str, optional
        List of NASA POWER parameter codes to fetch. If None, fetches default parameters:
        ['T2M', 'T2M_MAX', 'T2M_MIN', 'PRECTOTCORR', 'RH2M', 'ALLSKY_SFC_SW_DWN'].

    Returns
    -------
    pd.DataFrame
        DataFrame with monthly aggregated climate data containing columns:
        - year (int): Year of observation
        - month (int): Month of observation (1-12)
        - latitude (float): Latitude coordinate
        - longitude (float): Longitude coordinate
        - t2m (float): Mean temperature at 2m (°C)
        - t2m_max (float): Mean maximum temperature (°C)
        - t2m_min (float): Mean minimum temperature (°C)
        - prectotcorr (float): Total monthly precipitation (mm)
        - rh2m (float): Mean relative humidity (%)
        - allsky_sfc_sw_dwn (float): Mean solar radiation (W/m²)

    Raises
    ------
    requests.exceptions.RequestException
        If API request fails (network error, timeout, HTTP error).
    ValueError
        If API returns unexpected response structure or empty dataset.

    Notes
    -----
    - NASA POWER data is derived from satellite observations and climate models
    - Data has 0.5° x 0.5° spatial resolution
    - Missing data (flagged as -999 in API) is converted to None/NaN
    - Temperature variables are averaged over the month
    - Precipitation is summed over the month
    - Raw data is saved to data/raw/nasa_power_raw.csv

    Examples
    --------
    >>> from modules.ingestion.nasa_power_ingestion import fetch_nasa_power_data
    >>>
    >>> # Fetch data for Tanzania (default location)
    >>> df = fetch_nasa_power_data(start_year=2020, end_year=2023)
    >>> print(f"Fetched {len(df)} monthly records")
    >>>
    >>> # Fetch data for custom location
    >>> df = fetch_nasa_power_data(
    ...     latitude=-6.8,
    ...     longitude=39.3,  # Dar es Salaam
    ...     start_year=2020,
    ...     end_year=2023
    ... )
    >>>
    >>> # Dry-run mode for testing
    >>> df = fetch_nasa_power_data(dry_run=True)
    """
    log_info(f"Fetching NASA POWER data... (dry run: {dry_run})")

    if dry_run:
        # Return placeholder data for testing
        df = pd.DataFrame(
            {
                "year": [2020, 2021],
                "month": [1, 1],
                "t2m": [24.5, 25.0],
                "prectotcorr": [50.0, 55.0],
                "rh2m": [70.0, 72.0],
                "allsky_sfc_sw_dwn": [200, 210],
            }
        )
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
            "GWETPROF",  # Profile Soil Moisture (0-1 fraction)
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

        # Add retry logic with exponential backoff
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=90)
                response.raise_for_status()
                data = response.json()
                break  # Success, exit retry loop
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                if attempt < max_retries - 1:
                    log_info(f"Connection error (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    log_error(f"Failed after {max_retries} attempts: {e}")
                    raise

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


def ingest_nasa_power(
    db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None, incremental: bool = True
) -> Tuple[int, int]:
    """
    Ingest NASA POWER data and store to database (orchestrator-compatible interface).

    This function is designed to be called by the pipeline orchestrator.
    It fetches NASA POWER data for the specified date range and stores it in the database.

    Parameters
    ----------
    db : Session
        SQLAlchemy database session for storing data
    start_date : datetime, optional
        Start date for data retrieval. If None, defaults to 2010-01-01
    end_date : datetime, optional
        End date for data retrieval. If None, defaults to current date
    incremental : bool, optional
        Whether to use incremental ingestion (only fetch new data). Default is True.

    Returns
    -------
    Tuple[int, int]
        Tuple of (records_fetched, records_stored)
        - records_fetched: Number of records retrieved from source
        - records_stored: Number of records successfully stored to database
    """
    try:
        from app.models.climate_data import ClimateData
    except ImportError:
        from backend.app.models.climate_data import ClimateData
    from sqlalchemy import and_

    # Normalize inputs to tz-naive dates (see utils/dates.py tz contract).
    start_date = as_date(start_date, default=date(2010, 1, 1))
    end_date = as_date(end_date, default=date.today())

    # Cap end_date to the last complete month — never ingest the current
    # (incomplete) month. NASA POWER aggregates daily→monthly; a partial
    # month (e.g. April 1 with only 1 day of data) produces NaN values
    # for all variables that corrupt the ML feature set.
    cap = last_complete_month()
    if end_date > cap:
        end_date = cap
        log_info(f"NASA POWER end_date capped to last complete month: {end_date}")

    log_info(f"Ingesting NASA POWER data from {start_date} to {end_date}")

    # Convert to tz-naive pd.Timestamp for pandas DataFrame comparison below.
    # The date math above was done in pure `date`; this is the boundary where
    # we hand off to pandas, which uses datetime64[ns].
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)

    try:
        total_fetched = 0
        total_stored = 0

        for loc in PILOT_LOCATIONS:
            log_info(f"Fetching NASA POWER data for {loc['name']} ({loc['lat']}, {loc['lon']})")

            # Fetch data for this pilot location
            df = fetch_nasa_power_data(
                start_year=start_date.year,
                end_year=end_date.year,
                latitude=loc["lat"],
                longitude=loc["lon"],
                dry_run=False,
            )

            if df.empty:
                log_info(f"No NASA POWER data fetched for {loc['name']}")
                continue

            records_fetched = len(df)
            total_fetched += records_fetched
            log_info(f"Fetched {records_fetched} NASA POWER records for {loc['name']}")

            # Filter to exact date range (month-level granularity)
            df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
            df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)]

            # Store to database
            for _, row in df.iterrows():
                try:
                    # Check if record already exists
                    existing = (
                        db.query(ClimateData)
                        .filter(
                            and_(
                                ClimateData.date == row["date"].date(),
                                ClimateData.location_lat == loc["lat"],
                                ClimateData.location_lon == loc["lon"],
                            )
                        )
                        .first()
                    )

                    if existing:
                        # Update existing record with NASA POWER data
                        if "t2m" in row:
                            existing.temperature_avg = float(row["t2m"])
                        if "gwetprof" in row:
                            existing.soil_moisture = float(row["gwetprof"])
                        if "rh2m" in row and row["rh2m"] is not None:
                            existing.rel_humidity_pct = float(row["rh2m"])
                        if "allsky_sfc_sw_dwn" in row and row["allsky_sfc_sw_dwn"] is not None:
                            existing.solar_rad_wm2 = float(row["allsky_sfc_sw_dwn"])
                        total_stored += 1
                    else:
                        # Create new record
                        climate_record = ClimateData(
                            date=row["date"].date(),
                            location_lat=loc["lat"],
                            location_lon=loc["lon"],
                            temperature_avg=float(row["t2m"]) if "t2m" in row else None,
                            soil_moisture=float(row["gwetprof"]) if "gwetprof" in row else None,
                            rel_humidity_pct=float(row["rh2m"]) if "rh2m" in row and row["rh2m"] is not None else None,
                            solar_rad_wm2=(
                                float(row["allsky_sfc_sw_dwn"])
                                if "allsky_sfc_sw_dwn" in row and row["allsky_sfc_sw_dwn"] is not None
                                else None
                            ),
                        )
                        db.add(climate_record)
                        total_stored += 1

                except Exception as e:
                    log_error(f"Failed to store NASA POWER record for {row['date']} @ {loc['name']}: {e}")
                    continue

        # Commit all changes
        db.commit()
        log_info(f"Successfully stored {total_stored} NASA POWER records to database")

        return (total_fetched, total_stored)

    except Exception as e:
        log_error(f"NASA POWER ingestion failed: {e}")
        db.rollback()
        raise
