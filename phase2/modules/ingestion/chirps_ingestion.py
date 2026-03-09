"""
CHIRPS Ingestion - Phase 2
Fetches rainfall data from Climate Hazards Group InfraRed Precipitation with Station data.
Data source: Google Earth Engine (UCSB-CHG/CHIRPS/DAILY)
"""

import os
from datetime import date, datetime
from typing import Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from utils.config import get_data_path
from utils.logger import log_error, log_info, log_warning
from utils.validator import validate_dataframe

# Tanzania bounding box
TANZANIA_BOUNDS = {
    "lat_min": -11.75,
    "lat_max": -0.99,
    "lon_min": 29.34,
    "lon_max": 40.44,
}

# Try to import Google Earth Engine
try:
    import ee

    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False
    log_warning("Google Earth Engine not available. Install with: pip install earthengine-api")


def _initialize_gee():
    """Initialize Google Earth Engine (service account or user credentials)."""
    if not GEE_AVAILABLE:
        return False
    try:
        from utils.earth_engine_auth import initialize_gee
        return initialize_gee()
    except ImportError:
        pass

    # Fallback: direct init (local dev)
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "climate-prediction-using-ml")
        ee.Initialize(project=project_id)
        return True
    except Exception as e:
        log_warning(f"Failed to initialize Google Earth Engine: {e}")
        return False


def _fetch_gee_chirps(start_year, end_year, bounds):
    """
    Fetch CHIRPS data from Google Earth Engine.

    Uses daily CHIRPS data, aggregates to monthly totals, and calculates spatial mean.
    """
    log_info("Fetching CHIRPS from Google Earth Engine")

    # Define region of interest
    region = ee.Geometry.Rectangle([bounds["lon_min"], bounds["lat_min"], bounds["lon_max"], bounds["lat_max"]])

    # Get CHIRPS daily collection
    chirps = (
        ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
        .filterDate(f"{start_year}-01-01", f"{end_year}-12-31")
        .filterBounds(region)
        .select("precipitation")
    )

    # Function to aggregate to monthly and extract data
    records = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # Get data for this month
            start_date = f"{year}-{month:02d}-01"

            # Calculate end date (last day of month)
            if month == 12:
                end_date = f"{year + 1}-01-01"
            else:
                end_date = f"{year}-{month + 1:02d}-01"

            # Filter to this month and sum daily values
            monthly = chirps.filterDate(start_date, end_date).sum()

            # Calculate mean over region
            stats = monthly.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=5000,  # 5km resolution (CHIRPS native is ~5.5km)
                maxPixels=1e9,
            )

            # Get the value - handle missing data gracefully
            try:
                rainfall_obj = stats.get("precipitation")
                if rainfall_obj is not None:
                    rainfall = rainfall_obj.getInfo()
                else:
                    rainfall = None
            except Exception as e:
                log_warning(f"Failed to get precipitation for {year}-{month:02d}: {e}")
                rainfall = None

            if rainfall is not None:
                records.append(
                    {
                        "year": year,
                        "month": month,
                        "rainfall_mm": round(rainfall, 2),
                        "lat_min": bounds["lat_min"],
                        "lat_max": bounds["lat_max"],
                        "lon_min": bounds["lon_min"],
                        "lon_max": bounds["lon_max"],
                        "data_source": "CHIRPS_GEE",
                    }
                )

                log_info(f"Retrieved CHIRPS data for {year}-{month:02d}: {rainfall:.2f} mm")
            else:
                log_warning(f"No CHIRPS data available for {year}-{month:02d}")

    df = pd.DataFrame(records)
    log_info(f"Retrieved {len(df)} monthly CHIRPS records from GEE")

    return df


def fetch_chirps_data(
    dry_run=False,
    start_year=1985,
    end_year=2025,
    bounds=None,
    use_gee=True,
    *args,
    **kwargs,
):
    """
    Fetch CHIRPS rainfall data from Google Earth Engine or generate synthetic data.

    Uses Google Earth Engine to access CHIRPS daily data, aggregates to monthly totals,
    and calculates spatial mean over the region. Falls back to synthetic data if GEE
    is unavailable.

    Parameters
    ----------
    dry_run : bool, optional
        If True, return placeholder data without fetching from GEE. Default is False.
    start_year : int, optional
        Start year for data retrieval (inclusive). Default is 2010.
    end_year : int, optional
        End year for data retrieval (inclusive). Default is 2023.
    bounds : dict, optional
        Geographic bounding box with keys: 'lat_min', 'lat_max', 'lon_min', 'lon_max' (degrees).
        If None, uses Tanzania bounds: {lat_min: -11.75, lat_max: -0.99, lon_min: 29.34, lon_max: 40.44}.
    use_gee : bool, optional
        If True, attempt to use Google Earth Engine. Default is True.

    Returns
    -------
    pd.DataFrame
        DataFrame with monthly rainfall data containing columns:
        - year (int): Year of observation
        - month (int): Month of observation (1-12)
        - rainfall_mm (float): Mean monthly rainfall over region (mm)
        - lat_min (float): Minimum latitude of bounding box
        - lat_max (float): Maximum latitude of bounding box
        - lon_min (float): Minimum longitude of bounding box
        - lon_max (float): Maximum longitude of bounding box
        - data_source (str): Data source identifier ("CHIRPS_GEE" or "climatology_based")

    Raises
    ------
    Exception
        If data fetching fails from all sources.

    Notes
    -----
    **Prerequisites:**

    Install and authenticate Google Earth Engine:
        ``pip install earthengine-api``
        ``earthengine authenticate``

    **Data Processing:**

    - Accesses CHIRPS daily data via Google Earth Engine
    - No large file downloads required
    - Aggregates daily precipitation to monthly totals
    - Calculates spatial mean over the specified region
    - Server-side processing on Google's infrastructure
    - Saves processed data to data/raw/chirps_raw.csv

    **Data Source:**

    - Dataset: UCSB-CHG/CHIRPS/DAILY
    - Resolution: ~5.5 km
    - Temporal: Daily, aggregated to monthly
    - Coverage: 1981-present (near real-time)

    **Performance:**

    - Much faster than downloading NetCDF files (no 1-2 GB downloads)
    - Processing time: ~1-2 seconds per month
    - For 10 years: ~2-4 minutes total

    Examples
    --------
    >>> from modules.ingestion.chirps_ingestion import fetch_chirps_data
    >>>
    >>> # Fetch data for Tanzania (default bounds)
    >>> df = fetch_chirps_data(start_year=2020, end_year=2023)
    >>> print(f"Fetched {len(df)} monthly records")
    >>>
    >>> # Fetch data for custom region
    >>> custom_bounds = {
    ...     'lat_min': -8.0,
    ...     'lat_max': -5.0,
    ...     'lon_min': 33.0,
    ...     'lon_max': 36.0
    ... }
    >>> df = fetch_chirps_data(bounds=custom_bounds, start_year=2015, end_year=2020)
    """
    log_info(f"Fetching CHIRPS data... (dry run: {dry_run})")

    if dry_run:
        # Return placeholder data for testing
        df = pd.DataFrame(
            {
                "year": [2020, 2020, 2020, 2021, 2021, 2021],
                "month": [1, 2, 3, 1, 2, 3],
                "rainfall_mm": [125.5, 83.3, 157.7, 10.0, 5.5, 182.2],
                "lat_min": [-11.75] * 6,
                "lat_max": [-0.99] * 6,
                "lon_min": [29.34] * 6,
                "lon_max": [40.44] * 6,
                "data_source": ["dry_run"] * 6,
            }
        )
        log_info("Dry run mode: returning placeholder data")
        return df

    # Use default bounds if not specified
    if bounds is None:
        bounds = TANZANIA_BOUNDS

    try:
        # TIER 1: Try to use Google Earth Engine (real satellite data)
        if use_gee and GEE_AVAILABLE:
            if _initialize_gee():
                try:
                    log_info("Attempting to fetch real CHIRPS data from Google Earth Engine...")
                    df = _fetch_gee_chirps(start_year, end_year, bounds)

                    # Validate the dataframe
                    expected_cols = ["year", "month", "rainfall_mm"]
                    validate_dataframe(df, expected_columns=expected_cols, dataset_name="CHIRPS")

                    # Save raw data (cache for future use)
                    csv_path = get_data_path("raw", "chirps_raw.csv")
                    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                    df.to_csv(csv_path, index=False)
                    log_info(f"✓ Real CHIRPS data saved to: {csv_path}")

                    return df

                except Exception as e:
                    log_error(f"Failed to fetch CHIRPS from Google Earth Engine: {e}")
                    log_info("Attempting fallback strategies...")

        # TIER 2: Try to use cached data from previous successful fetch
        log_info("Checking for cached CHIRPS data...")
        cached_file = get_data_path("raw", "chirps_raw.csv")
        if cached_file.exists():
            try:
                df = pd.read_csv(cached_file)

                # Check if cached data covers the requested date range
                cached_years = set(df["year"].unique())
                requested_years = set(range(start_year, end_year + 1))

                if requested_years.issubset(cached_years):
                    # Filter to requested date range
                    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
                    log_info(f"✓ Using cached CHIRPS data from: {cached_file}")
                    log_info(
                        f"  Data source: {df['data_source'].iloc[0] if 'data_source' in df.columns else 'unknown'}"
                    )
                    return df
                else:
                    missing_years = requested_years - cached_years
                    log_info(f"Cached data missing years: {sorted(missing_years)}")
                    log_info("Proceeding to synthetic data generation...")
            except Exception as e:
                log_warning(f"Failed to load cached data: {e}")

        if use_gee and not GEE_AVAILABLE:
             raise ImportError("Google Earth Engine not available. Install 'earthengine-api' and authenticate.")
        
        raise RuntimeError("Failed to fetch CHIRPS data from Google Earth Engine and no cached data available.")

    except Exception:
        raise


def _generate_sample_chirps_data(start_year, end_year, bounds):
    """
    Generate realistic sample CHIRPS data for testing when downloads fail.

    Creates synthetic rainfall data with:
    - Seasonal patterns (bimodal for Tanzania)
    - Realistic rainfall distribution
    - Some extreme events (droughts and floods)
    """
    import numpy as np

    # Create monthly data for the date range
    dates = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            dates.append({"year": year, "month": month})

    df = pd.DataFrame(dates)

    # Generate realistic rainfall using gamma distribution
    np.random.seed(42)  # For reproducibility
    n_months = len(df)

    # Base rainfall (gamma distribution typical for tropical rainfall)
    base_rainfall = np.random.gamma(shape=3, scale=30, size=n_months)

    # Add seasonal pattern (Tanzania has bimodal rainfall)
    seasonal_factor = df["month"].apply(
        lambda m: (
            1.5 if 3 <= m <= 5 else 1.3 if 10 <= m <= 12 else 0.5  # Long rains (MAM), Short rains (OND), Dry seasons
        )
    )

    df["rainfall_mm"] = base_rainfall * seasonal_factor

    # Add some extreme events
    # Drought: very low rainfall for 3 consecutive months
    if len(df) > 20:
        drought_start = len(df) // 3
        df.loc[drought_start : drought_start + 2, "rainfall_mm"] = np.random.uniform(0, 10, 3)

    # Flood: very high rainfall for 2 months
    if len(df) > 30:
        flood_start = 2 * len(df) // 3
        df.loc[flood_start : flood_start + 1, "rainfall_mm"] = np.random.uniform(200, 300, 2)

    # Add bounds and data source
    df["lat_min"] = bounds["lat_min"]
    df["lat_max"] = bounds["lat_max"]
    df["lon_min"] = bounds["lon_min"]
    df["lon_max"] = bounds["lon_max"]
    df["data_source"] = "climatology_based"

    log_info(f"Generated {len(df)} months of sample CHIRPS data")
    log_info(f"Rainfall range: {df['rainfall_mm'].min():.1f} - {df['rainfall_mm'].max():.1f} mm/month")

    return df


def fetch_data(*args, **kwargs):
    return fetch_chirps_data(*args, **kwargs)


def ingest_chirps(
    db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, incremental: bool = True
) -> Tuple[int, int]:
    """
    Ingest CHIRPS data and store to database (orchestrator-compatible interface).

    This function is designed to be called by the pipeline orchestrator.
    It fetches CHIRPS data for the specified date range and stores it in the database.

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

    Examples
    --------
    >>> from sqlalchemy.orm import Session
    >>> from datetime import datetime
    >>>
    >>> # Full refresh for 2020-2023
    >>> records_fetched, records_stored = ingest_chirps(
    ...     db=db_session,
    ...     start_date=datetime(2020, 1, 1),
    ...     end_date=datetime(2023, 12, 31),
    ...     incremental=False
    ... )
    >>> print(f"Fetched {records_fetched}, stored {records_stored}")
    """
    try:
        from app.models.climate_data import ClimateData
    except ImportError:
        from backend.app.models.climate_data import ClimateData
    from sqlalchemy import and_

    # Set default date range
    if start_date is None:
        start_date = datetime(2010, 1, 1)
    if end_date is None:
        end_date = datetime.now()

    # Ensure dates are timezone-naive pandas Timestamps for DataFrame comparison
    start_date = pd.to_datetime(start_date).tz_localize(None) if pd.to_datetime(start_date).tzinfo else pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date).tz_localize(None) if pd.to_datetime(end_date).tzinfo else pd.to_datetime(end_date)

    log_info(f"Ingesting CHIRPS data from {start_date} to {end_date}")

    try:
        # Fetch data using existing function
        df = fetch_chirps_data(start_year=start_date.year, end_year=end_date.year, dry_run=False)

        if df.empty:
            log_warning("No CHIRPS data fetched")
            return (0, 0)

        records_fetched = len(df)
        log_info(f"Fetched {records_fetched} CHIRPS records")

        # Filter to exact date range (month-level granularity)
        df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        # Store to database — Kilombero Pilot location: Morogoro, Tanzania
        # Source: locations table (id=6), seed_locations.py
        records_stored = 0
        morogoro_lat = -6.8211
        morogoro_lon = 37.6595

        for _, row in df.iterrows():
            try:
                # Check if record already exists
                existing = (
                    db.query(ClimateData)
                    .filter(
                        and_(
                            ClimateData.date == row["date"].date(),
                            ClimateData.location_lat == morogoro_lat,
                            ClimateData.location_lon == morogoro_lon,
                        )
                    )
                    .first()
                )

                if existing:
                    # Update existing record
                    existing.rainfall_mm = float(row["rainfall_mm"])
                    records_stored += 1
                else:
                    # Create new record
                    climate_record = ClimateData(
                        date=row["date"].date(),
                        location_lat=morogoro_lat,
                        location_lon=morogoro_lon,
                        rainfall_mm=float(row["rainfall_mm"]),
                    )
                    db.add(climate_record)
                    records_stored += 1

            except Exception as e:
                log_error(f"Failed to store CHIRPS record for {row['date']}: {e}")
                continue

        # Commit all changes
        db.commit()
        log_info(f"Successfully stored {records_stored} CHIRPS records to database")

        return (records_fetched, records_stored)

    except Exception as e:
        log_error(f"CHIRPS ingestion failed: {e}")
        db.rollback()
        raise
