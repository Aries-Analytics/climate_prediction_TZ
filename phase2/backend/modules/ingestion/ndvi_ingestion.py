"""
NDVI Ingestion - Phase 2
Fetches Normalized Difference Vegetation Index data from MODIS via Google Earth Engine.

This module supports both real satellite data (via Google Earth Engine) and synthetic
climatological data for testing purposes.

TZ CONTRACT: This module follows the ingestion tz-naive `date` contract.
See `utils/dates.py` for the full contract.
"""

import os
from datetime import date
from typing import Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

from utils.config import get_data_path
from utils.dates import as_date, last_complete_month
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
    log_info("[WARNING] Google Earth Engine not available. Install with: pip install earthengine-api")


def _initialize_gee():
    """
    Initialize Google Earth Engine (service account or user credentials).

    Returns:
        bool: True if initialization successful, False otherwise.
    """
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
        log_info(f"Google Earth Engine initialized with project: {project_id}")
        return True
    except Exception as e:
        log_warning(f"Failed to initialize Google Earth Engine: {e}")
        log_info("To authenticate, run: earthengine authenticate")
        return False


def _extract_ndvi_from_collection(collection, region, data_source, scale_factor=1.0):
    """
    Extract NDVI data from an Earth Engine ImageCollection.

    Parameters:
        collection: ee.ImageCollection with NDVI data
        region: ee.Geometry for spatial aggregation
        data_source: String identifier for data source
        scale_factor: Factor to divide raw NDVI values (e.g., 10000 for MODIS)

    Returns:
        list: List of dictionaries with NDVI records
    """

    # Function to extract NDVI for each image
    def extract_ndvi(image):
        # Get the date
        date = ee.Date(image.get("system:time_start"))

        # Calculate mean NDVI over the region
        # Use appropriate scale based on dataset (1km for MODIS, 8km for AVHRR)
        scale = 1000 if "MODIS" in data_source else 8000

        stats = image.reduceRegion(reducer=ee.Reducer.mean(), geometry=region, scale=scale, maxPixels=1e9)

        # Return feature with date and NDVI
        return ee.Feature(
            None,
            {
                "date": date.format("YYYY-MM-dd"),
                "year": date.get("year"),
                "month": date.get("month"),
                "ndvi": stats.get("NDVI"),
                "data_source": data_source,
            },
        )

    # Map over collection and extract data
    features = collection.map(extract_ndvi)

    # Convert to list and download
    log_info(f"Downloading {data_source} NDVI data from GEE...")
    feature_list = features.getInfo()["features"]

    # Parse into records
    records = []
    for feature in feature_list:
        props = feature["properties"]

        # Apply scale factor (MODIS NDVI is scaled by 10000, AVHRR by 1)
        ndvi_raw = props.get("ndvi")
        if ndvi_raw is not None:
            ndvi_value = ndvi_raw / scale_factor
            # Clip to valid range
            ndvi_value = max(-1.0, min(1.0, ndvi_value))

            records.append(
                {
                    "year": int(props["year"]),
                    "month": int(props["month"]),
                    "ndvi": round(ndvi_value, 4),
                    "date": props["date"],
                    "data_source": props["data_source"],
                }
            )

    return records


def _fetch_gee_ndvi(start_year, end_year, bounds):
    """
    Fetch real NDVI data from Google Earth Engine using hybrid AVHRR+MODIS approach.

    Uses AVHRR for 1985-1999 (historical) and MODIS for 2000-present (higher quality).

    Parameters:
        start_year (int): Start year for data retrieval.
        end_year (int): End year for data retrieval.
        bounds (dict): Geographic bounding box.

    Returns:
        pd.DataFrame: DataFrame with NDVI data.
    """
    log_info(f"Fetching NDVI from Google Earth Engine (Hybrid AVHRR+MODIS: {start_year}-{end_year})")

    # Define the region of interest
    region = ee.Geometry.Rectangle([bounds["lon_min"], bounds["lat_min"], bounds["lon_max"], bounds["lat_max"]])

    all_records = []

    # PART 1: AVHRR NDVI for historical data (1985-1999)
    if start_year < 2000:
        avhrr_start = max(start_year, 1981)  # AVHRR starts in 1981
        avhrr_end = min(end_year, 1999)

        log_info(f"Fetching AVHRR NDVI for {avhrr_start}-{avhrr_end} (historical data)")

        try:
            # Use NOAA CDR AVHRR NDVI V5 (8km resolution, 1981-present)
            avhrr_collection = (
                ee.ImageCollection("NOAA/CDR/AVHRR/NDVI/V5")
                .filterDate(f"{avhrr_start}-01-01", f"{avhrr_end}-12-31")
                .filterBounds(region)
                .select("NDVI")
            )

            avhrr_records = _extract_ndvi_from_collection(avhrr_collection, region, "AVHRR_CDR_V5")
            all_records.extend(avhrr_records)
            log_info(f"Retrieved {len(avhrr_records)} AVHRR records")

        except Exception as e:
            log_error(f"Failed to fetch AVHRR data: {e}")
            log_warning("Continuing with MODIS data only...")

    # PART 2: MODIS NDVI for modern data (2000-present)
    if end_year >= 2000:
        modis_start = max(start_year, 2000)  # MODIS starts in 2000
        modis_end = end_year

        log_info(f"Fetching MODIS NDVI for {modis_start}-{modis_end} (high-quality modern data)")

        try:
            # Use MODIS Terra Vegetation Indices 16-Day Global 1km (MOD13A2)
            # Using the latest version (061) instead of deprecated 006
            modis_collection = (
                ee.ImageCollection("MODIS/061/MOD13A2")
                .filterDate(f"{modis_start}-01-01", f"{modis_end}-12-31")
                .filterBounds(region)
                .select("NDVI")
            )

            modis_records = _extract_ndvi_from_collection(modis_collection, region, "MODIS_MOD13A2", scale_factor=10000)
            all_records.extend(modis_records)
            log_info(f"Retrieved {len(modis_records)} MODIS records")

        except Exception as e:
            log_error(f"Failed to fetch MODIS data: {e}")
            if not all_records:  # If we have no AVHRR data either, raise error
                raise

    if not all_records:
        raise ValueError("No NDVI data retrieved from Google Earth Engine")

    # Convert to DataFrame
    df = pd.DataFrame(all_records)

    # Aggregate to monthly means (both AVHRR and MODIS have multiple values per month)
    df_monthly = df.groupby(["year", "month"]).agg({"ndvi": "mean", "data_source": "first"}).reset_index()

    # Add bounds information
    df_monthly["lat_min"] = bounds["lat_min"]
    df_monthly["lat_max"] = bounds["lat_max"]
    df_monthly["lon_min"] = bounds["lon_min"]
    df_monthly["lon_max"] = bounds["lon_max"]
    df_monthly["data_source"] = "MODIS_MOD13A2_GEE"

    # Round NDVI values
    df_monthly["ndvi"] = df_monthly["ndvi"].round(4)

    log_info(f"Retrieved {len(df_monthly)} monthly NDVI records from GEE")

    return df_monthly


def _fetch_synthetic_ndvi(start_year, end_year, bounds):
    """
    Generate synthetic NDVI data based on climatological patterns.

    Parameters:
        start_year (int): Start year for data generation.
        end_year (int): End year for data generation.
        bounds (dict): Geographic bounding box.

    Returns:
        pd.DataFrame: DataFrame with synthetic NDVI data.
    """
    log_info("Generating synthetic NDVI data based on climatological patterns")

    # Generate realistic NDVI data based on Tanzania's climate patterns
    # Tanzania has two rainy seasons: March-May (long rains) and October-December (short rains)
    records = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # Simulate seasonal NDVI patterns
            # Higher NDVI during/after rainy seasons, lower during dry seasons
            if month in [4, 5, 6]:  # After long rains
                base_ndvi = 0.65
                variation = 0.10
            elif month in [11, 12, 1]:  # After short rains
                base_ndvi = 0.60
                variation = 0.08
            elif month in [7, 8, 9]:  # Dry season
                base_ndvi = 0.45
                variation = 0.05
            else:  # Transition periods
                base_ndvi = 0.55
                variation = 0.07

            # Add some year-to-year variation
            import random

            random.seed(year * 100 + month)  # Reproducible randomness
            ndvi_value = base_ndvi + random.uniform(-variation, variation)

            # Ensure NDVI is within valid range
            ndvi_value = max(0.0, min(1.0, ndvi_value))

            records.append(
                {
                    "year": year,
                    "month": month,
                    "ndvi": round(ndvi_value, 4),
                    "lat_min": bounds["lat_min"],
                    "lat_max": bounds["lat_max"],
                    "lon_min": bounds["lon_min"],
                    "lon_max": bounds["lon_max"],
                    "data_source": "climatology_based",
                }
            )

    df = pd.DataFrame(records)
    df = df.sort_values(["year", "month"]).reset_index(drop=True)

    log_info(f"Generated {len(df)} synthetic NDVI records")

    return df


def fetch_ndvi_data(
    dry_run=False,
    start_year=1985,
    end_year=2025,
    bounds=None,
    use_gee=True,
    *args,
    **kwargs,
):
    """
    Fetch NDVI (Normalized Difference Vegetation Index) data from satellite or synthetic sources.

    This function automatically attempts to use Google Earth Engine for real MODIS NDVI data.
    If GEE is not available or authentication fails, it falls back to synthetic climatological data.

    Parameters
    ----------
    dry_run : bool, optional
        If True, return minimal placeholder data for testing. Default is False.
    start_year : int, optional
        Start year for data retrieval (inclusive). Default is 2010.
    end_year : int, optional
        End year for data retrieval (inclusive). Default is 2023.
    bounds : dict, optional
        Geographic bounding box with keys: 'lat_min', 'lat_max', 'lon_min', 'lon_max' (degrees).
        If None, uses Tanzania bounds: {lat_min: -11.75, lat_max: -0.99, lon_min: 29.34, lon_max: 40.44}.
    use_gee : bool, optional
        If True, attempt to use Google Earth Engine for real satellite data. Default is True.

    Returns
    -------
    pd.DataFrame
        DataFrame with monthly NDVI data containing columns:
        - year (int): Year of observation
        - month (int): Month of observation (1-12)
        - ndvi (float): NDVI value (range: -1.0 to 1.0, typically 0.0 to 1.0 for vegetation)
        - lat_min (float): Minimum latitude of bounding box
        - lat_max (float): Maximum latitude of bounding box
        - lon_min (float): Minimum longitude of bounding box
        - lon_max (float): Maximum longitude of bounding box
        - data_source (str): Data source identifier ("MODIS_MOD13A2_GEE" or "climatology_based")

    Raises
    ------
    ValueError
        If no data could be retrieved from any source.
    Exception
        For other errors during data fetching or processing.

    Notes
    -----
    **Data Sources:**

    1. **Google Earth Engine (Primary)**:
       - Dataset: MODIS/006/MOD13A2 (Terra Vegetation Indices 16-Day Global 1km)
       - Resolution: 1 km
       - Temporal: 16-day composite, aggregated to monthly means
       - Requires: earthengine-api package and authentication
       - Setup: Run `earthengine authenticate` in terminal

    2. **Synthetic Climatology (Fallback)**:
       - Based on Tanzania's seasonal rainfall patterns
       - Reproducible values for testing
       - Reflects bimodal rainfall regime

    **NDVI Value Interpretation:**

    - -1 to 0: Water bodies, clouds, snow
    - 0 to 0.1: Bare soil, rock, sand
    - 0.1 to 0.2: Sparse vegetation, shrubs
    - 0.2 to 0.5: Grassland, crops, moderate vegetation
    - 0.5 to 0.8: Dense vegetation, healthy forests
    - 0.8 to 1.0: Very dense, healthy vegetation

    **Seasonal Patterns (Tanzania):**

    - April-June (after long rains): High NDVI (0.55-0.75) - peak vegetation
    - November-January (after short rains): Moderate-high NDVI (0.52-0.68)
    - July-September (dry season): Lower NDVI (0.40-0.50) - vegetation stress
    - February-March, October (transition): Moderate NDVI (0.48-0.62)

    **Setup for Google Earth Engine:**

    1. Install the package:
       ```bash
       pip install earthengine-api
       ```

    2. Authenticate (one-time setup):
       ```bash
       earthengine authenticate
       ```
       This will open a browser for you to authorize access.

    3. The module will automatically use GEE if available and authenticated.

    Examples
    --------
    >>> from modules.ingestion.ndvi_ingestion import fetch_ndvi_data
    >>>
    >>> # Fetch real MODIS NDVI data from Google Earth Engine
    >>> df = fetch_ndvi_data(start_year=2020, end_year=2023)
    >>> print(f"Fetched {len(df)} monthly NDVI records")
    >>> print(f"Data source: {df['data_source'].iloc[0]}")
    >>>
    >>> # Force synthetic data (skip GEE)
    >>> df = fetch_ndvi_data(start_year=2020, end_year=2023, use_gee=False)
    >>>
    >>> # Custom region
    >>> custom_bounds = {
    ...     'lat_min': -8.0,
    ...     'lat_max': -5.0,
    ...     'lon_min': 33.0,
    ...     'lon_max': 36.0
    ... }
    >>> df = fetch_ndvi_data(bounds=custom_bounds, start_year=2020, end_year=2023)
    >>>
    >>> # Dry-run mode for quick testing
    >>> df = fetch_ndvi_data(dry_run=True)
    """
    log_info(f"Fetching NDVI data... (dry run: {dry_run})")

    if dry_run:
        # Return minimal placeholder data for testing
        df = pd.DataFrame(
            {
                "year": [2020, 2021],
                "month": [1, 1],
                "ndvi": [0.72, 0.75],
                "lat_min": [TANZANIA_BOUNDS["lat_min"]] * 2,
                "lat_max": [TANZANIA_BOUNDS["lat_max"]] * 2,
                "lon_min": [TANZANIA_BOUNDS["lon_min"]] * 2,
                "lon_max": [TANZANIA_BOUNDS["lon_max"]] * 2,
                "data_source": ["dry_run"] * 2,
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
                    log_info("Attempting to fetch real MODIS NDVI data from Google Earth Engine...")
                    df = _fetch_gee_ndvi(start_year, end_year, bounds)

                    # Validate the dataframe
                    expected_cols = ["year", "month", "ndvi"]
                    validate_dataframe(df, expected_columns=expected_cols, dataset_name="NDVI")

                    # Save raw data (cache for future use)
                    csv_path = get_data_path("raw", "ndvi_raw.csv")
                    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                    df.to_csv(csv_path, index=False)
                    log_info(f"✓ Real NDVI data saved to: {csv_path}")

                    return df

                except Exception as e:
                    log_error(f"Failed to fetch NDVI from Google Earth Engine: {e}")
                    log_info("Attempting fallback strategies...")

        # TIER 2: Try to use cached data from previous successful fetch
        log_info("Checking for cached NDVI data...")
        cached_file = get_data_path("raw", "ndvi_raw.csv")
        if cached_file.exists():
            try:
                df = pd.read_csv(cached_file)

                # Check if cached data covers the requested date range
                cached_years = set(df["year"].unique())
                requested_years = set(range(start_year, end_year + 1))

                if requested_years.issubset(cached_years):
                    # Filter to requested date range
                    df = df[(df["year"] >= start_year) & (df["year"] <= end_year)]
                    log_info(f"✓ Using cached NDVI data from: {cached_file}")
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

        raise RuntimeError("Failed to fetch NDVI data from Google Earth Engine and no cached data available.")

    except Exception:
        raise


def fetch_data(*args, **kwargs):
    return fetch_ndvi_data(*args, **kwargs)


def ingest_ndvi(
    db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None, incremental: bool = True
) -> Tuple[int, int]:
    """
    Ingest NDVI data and store to database (orchestrator-compatible interface).

    This function is designed to be called by the pipeline orchestrator.
    It fetches NDVI data for the specified date range and stores it in the database.

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
    # (incomplete) month. MODIS NDVI composites are 16-day windows; a
    # monthly aggregate built from only the first composite (early-month)
    # misrepresents vegetation state for the full month.
    cap = last_complete_month()
    if end_date > cap:
        end_date = cap
        log_info(f"NDVI end_date capped to last complete month: {end_date}")

    log_info(f"Ingesting NDVI data from {start_date} to {end_date}")

    # Convert to tz-naive pd.Timestamp at the pandas boundary.
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)

    try:
        # Fetch data using existing function
        df = fetch_ndvi_data(start_year=start_date.year, end_year=end_date.year, dry_run=False)

        if df.empty:
            log_info("No NDVI data fetched")
            return (0, 0)

        records_fetched = len(df)
        log_info(f"Fetched {records_fetched} NDVI records")

        # Filter to exact date range (month-level granularity)
        df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
        df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)]

        # Kilombero Basin pilot zones (Apr 2026 two-zone split)
        # Replaces single Morogoro city point with actual basin coordinates.
        PILOT_LOCATIONS = [
            {"name": "Ifakara TC", "lat": -8.1333, "lon": 36.6833},
            {"name": "Mlimba DC", "lat": -8.0167, "lon": 35.9500},
        ]

        records_stored = 0

        for _, row in df.iterrows():
            try:
                for loc in PILOT_LOCATIONS:
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
                        # Update existing record with NDVI data
                        existing.ndvi = float(row["ndvi"])
                        records_stored += 1
                    else:
                        # Create new record
                        climate_record = ClimateData(
                            date=row["date"].date(),
                            location_lat=loc["lat"],
                            location_lon=loc["lon"],
                            ndvi=float(row["ndvi"]),
                        )
                        db.add(climate_record)
                        records_stored += 1

            except Exception as e:
                log_error(f"Failed to store NDVI record for {row['date']} @ {loc['name']}: {e}")
                continue

        # Commit all changes
        db.commit()
        log_info(f"Successfully stored {records_stored} NDVI records to database")

        return (records_fetched, records_stored)

    except Exception as e:
        log_error(f"NDVI ingestion failed: {e}")
        db.rollback()
        raise
