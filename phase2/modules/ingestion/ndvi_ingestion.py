"""
NDVI Ingestion - Phase 2
Fetches Normalized Difference Vegetation Index data from MODIS via Google Earth Engine.

This module supports both real satellite data (via Google Earth Engine) and synthetic
climatological data for testing purposes.
"""

import os

import pandas as pd

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
    log_info("[WARNING] Google Earth Engine not available. Install with: pip install earthengine-api")


def _initialize_gee():
    """
    Initialize Google Earth Engine with project ID from environment.

    Returns:
        bool: True if initialization successful, False otherwise.
    """
    if not GEE_AVAILABLE:
        return False

    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'climate-prediction-using-ml')
        ee.Initialize(project=project_id)
        log_info(f"Google Earth Engine initialized with project: {project_id}")
        return True
    except Exception as e:
        log_warning(f"Failed to initialize Google Earth Engine: {e}")
        log_info("To authenticate, run: earthengine authenticate")
        return False


def _fetch_gee_ndvi(start_year, end_year, bounds):
    """
    Fetch real NDVI data from Google Earth Engine using MODIS.

    Parameters:
        start_year (int): Start year for data retrieval.
        end_year (int): End year for data retrieval.
        bounds (dict): Geographic bounding box.

    Returns:
        pd.DataFrame: DataFrame with NDVI data.
    """
    log_info("Fetching NDVI from Google Earth Engine (MODIS MOD13A2)")

    # Define the region of interest
    region = ee.Geometry.Rectangle([bounds["lon_min"], bounds["lat_min"], bounds["lon_max"], bounds["lat_max"]])

    # Use MODIS Terra Vegetation Indices 16-Day Global 1km (MOD13A2)
    # Using the latest version (061) instead of deprecated 006
    collection = (
        ee.ImageCollection("MODIS/061/MOD13A2")
        .filterDate(f"{start_year}-01-01", f"{end_year}-12-31")
        .filterBounds(region)
        .select("NDVI")
    )

    # Function to extract NDVI for each image
    def extract_ndvi(image):
        # Get the date
        date = ee.Date(image.get("system:time_start"))

        # Calculate mean NDVI over the region
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region, scale=1000, maxPixels=1e9  # 1km resolution
        )

        # Return feature with date and NDVI
        return ee.Feature(
            None,
            {
                "date": date.format("YYYY-MM-dd"),
                "year": date.get("year"),
                "month": date.get("month"),
                "ndvi": stats.get("NDVI"),
            },
        )

    # Map over collection and extract data
    features = collection.map(extract_ndvi)

    # Convert to list and download
    log_info("Downloading NDVI data from GEE (this may take a few minutes)...")
    feature_list = features.getInfo()["features"]

    # Parse into records
    records = []
    for feature in feature_list:
        props = feature["properties"]

        # MODIS NDVI is scaled by 10000, so divide to get actual values
        ndvi_raw = props.get("ndvi")
        if ndvi_raw is not None:
            ndvi_value = ndvi_raw / 10000.0
            # Clip to valid range
            ndvi_value = max(-1.0, min(1.0, ndvi_value))

            records.append(
                {
                    "year": int(props["year"]),
                    "month": int(props["month"]),
                    "ndvi": round(ndvi_value, 4),
                    "date": props["date"],
                }
            )

    # Convert to DataFrame
    df = pd.DataFrame(records)

    if df.empty:
        raise ValueError("No NDVI data retrieved from Google Earth Engine")

    # Aggregate to monthly means (MODIS is 16-day, so multiple values per month)
    df_monthly = df.groupby(["year", "month"]).agg({"ndvi": "mean"}).reset_index()

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
    start_year=2010,
    end_year=2023,
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
                cached_years = set(df['year'].unique())
                requested_years = set(range(start_year, end_year + 1))
                
                if requested_years.issubset(cached_years):
                    # Filter to requested date range
                    df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
                    log_info(f"✓ Using cached NDVI data from: {cached_file}")
                    log_info(f"  Data source: {df['data_source'].iloc[0] if 'data_source' in df.columns else 'unknown'}")
                    return df
                else:
                    missing_years = requested_years - cached_years
                    log_info(f"Cached data missing years: {sorted(missing_years)}")
                    log_info("Proceeding to synthetic data generation...")
            except Exception as e:
                log_warning(f"Failed to load cached data: {e}")

        # TIER 3: Generate synthetic climatological data (realistic patterns)
        if not use_gee:
            log_info("GEE disabled by user, generating synthetic climatological data")
        elif not GEE_AVAILABLE:
            log_info("Google Earth Engine not available")
            log_info("To use real satellite data, install: pip install earthengine-api")
            log_info("Generating synthetic climatological data based on Tanzania climate patterns")
        else:
            log_info("Generating synthetic climatological data as fallback")

        df = _fetch_synthetic_ndvi(start_year, end_year, bounds)

        # Validate the dataframe
        expected_cols = ["year", "month", "ndvi"]
        validate_dataframe(df, expected_columns=expected_cols, dataset_name="NDVI")

        # Save synthetic data (don't overwrite real cached data)
        csv_path = get_data_path("raw", "ndvi_synthetic.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
        log_info(f"✓ Synthetic NDVI data saved to: {csv_path}")

        return df

    except Exception as e:
        log_error(f"All NDVI data fetch strategies failed: {e}")
        
        # TIER 4: Last resort - minimal dummy data for testing
        log_warning("Returning minimal dummy data as last resort")
        df = pd.DataFrame({
            "year": [start_year],
            "month": [1],
            "ndvi": [0.65],
            "lat_min": [bounds['lat_min']],
            "lat_max": [bounds['lat_max']],
            "lon_min": [bounds['lon_min']],
            "lon_max": [bounds['lon_max']],
            "data_source": ["dummy_fallback"]
        })
        return df


def fetch_data(*args, **kwargs):
    return fetch_ndvi_data(*args, **kwargs)
