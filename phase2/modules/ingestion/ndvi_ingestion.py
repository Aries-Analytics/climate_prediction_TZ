"""
NDVI Ingestion - Phase 2
Fetches Normalized Difference Vegetation Index data from MODIS via Google Earth Engine
or alternative sources
"""

import os

import pandas as pd
import requests

from utils.config import get_data_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe

# Tanzania bounding box
TANZANIA_BOUNDS = {
    "lat_min": -11.75,
    "lat_max": -0.99,
    "lon_min": 29.34,
    "lon_max": 40.44,
}

# MODIS NDVI data via NASA POWER-like service (simplified approach)
# Alternative: Use Google Earth Engine API (requires authentication)


def fetch_ndvi_data(
    dry_run=False,
    start_year=2010,
    end_year=2023,
    bounds=None,
    *args,
    **kwargs,
):
    """
    Fetch NDVI (Normalized Difference Vegetation Index) data.

    Args:
        dry_run: If True, return placeholder data without API call
        start_year: Start year for data retrieval
        end_year: End year for data retrieval
        bounds: Geographic bounds dict with lat_min, lat_max, lon_min, lon_max

    Returns:
        pandas DataFrame with NDVI data

    Note:
        This implementation uses a simplified approach with synthetic data based on
        typical NDVI patterns for Tanzania. For production use, consider:
        - Google Earth Engine API (requires authentication)
        - NASA AppEEARS API (requires registration)
        - Direct MODIS HDF file processing

        NDVI values range from -1 to 1, where:
        - Negative values: Water bodies
        - 0.1-0.2: Bare soil or sparse vegetation
        - 0.2-0.5: Grassland, shrubs
        - 0.5-0.8: Dense vegetation, forests
    """
    log_info(f"Fetching NDVI data... (dry run: {dry_run})")

    if dry_run:
        # Return placeholder data for testing
        df = pd.DataFrame({"YEAR": [2020, 2021], "NDVI": [0.72, 0.75]})
        log_info("Dry run mode: returning placeholder data")
        return df

    # Use default bounds if not specified
    if bounds is None:
        bounds = TANZANIA_BOUNDS

    try:
        log_info(f"Generating NDVI data for years {start_year}-{end_year}")
        log_info(
            "Note: Using climatological NDVI patterns. For production, integrate with "
            "Google Earth Engine or NASA AppEEARS API."
        )

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

        log_info(f"Generated {len(df)} NDVI records")

        # Validate the dataframe
        expected_cols = ["year", "month", "ndvi"]
        validate_dataframe(df, expected_columns=expected_cols, dataset_name="NDVI")

        # Save raw data
        csv_path = get_data_path("raw", "ndvi_raw.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
        log_info(f"NDVI data saved to: {csv_path}")

        return df

    except Exception as e:
        log_error(f"Failed to generate NDVI data: {e}")
        raise


def fetch_data(*args, **kwargs):
    return fetch_ndvi_data(*args, **kwargs)
