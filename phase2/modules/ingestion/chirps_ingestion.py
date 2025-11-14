"""
CHIRPS Ingestion - Phase 2
Fetches rainfall data from Climate Hazards Group InfraRed Precipitation with Station data
"""

import os
import tempfile

import pandas as pd
import requests

from utils.config import get_data_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe

# CHIRPS data URL (monthly data)
CHIRPS_BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/netcdf"

# Tanzania bounding box
TANZANIA_BOUNDS = {
    "lat_min": -11.75,
    "lat_max": -0.99,
    "lon_min": 29.34,
    "lon_max": 40.44,
}


def fetch_chirps_data(
    dry_run=False,
    start_year=2010,
    end_year=2023,
    bounds=None,
    *args,
    **kwargs,
):
    """
    Fetch CHIRPS rainfall data from UCSB Climate Hazards Center.

    Args:
        dry_run: If True, return placeholder data without downloading
        start_year: Start year for data retrieval
        end_year: End year for data retrieval
        bounds: Geographic bounds dict with lat_min, lat_max, lon_min, lon_max

    Returns:
        pandas DataFrame with rainfall data

    Note:
        CHIRPS data is freely available without authentication.
        Data is downloaded as NetCDF files and processed to extract Tanzania region.
    """
    log_info(f"Fetching CHIRPS data... (dry run: {dry_run})")

    if dry_run:
        # Return placeholder data for testing
        df = pd.DataFrame({"YEAR": [2020, 2021], "RAINFALL": [900, 1100]})
        log_info("Dry run mode: returning placeholder data")
        return df

    # Use default bounds if not specified
    if bounds is None:
        bounds = TANZANIA_BOUNDS

    try:
        # Check if required packages are available
        try:
            import xarray as xr
        except ImportError:
            log_error("xarray package not installed. Install with: pip install xarray netCDF4")
            raise ImportError("xarray and netCDF4 packages required for processing CHIRPS NetCDF files")

        all_data = []

        # Download and process data year by year
        for year in range(start_year, end_year + 1):
            log_info(f"Downloading CHIRPS data for year {year}...")

            # CHIRPS filename format: chirps-v2.0.{year}.days_p05.nc
            filename = f"chirps-v2.0.{year}.days_p05.nc"
            url = f"{CHIRPS_BASE_URL}/{filename}"

            try:
                # Download the NetCDF file
                response = requests.get(url, timeout=120)
                response.raise_for_status()

                # Load NetCDF data from memory
                with tempfile.NamedTemporaryFile(delete=False, suffix=".nc") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name

                # Open with xarray
                ds = xr.open_dataset(tmp_path)

                # Extract Tanzania region
                ds_tanzania = ds.sel(
                    latitude=slice(bounds["lat_max"], bounds["lat_min"]),
                    longitude=slice(bounds["lon_min"], bounds["lon_max"]),
                )

                # Calculate monthly totals (sum daily precipitation)
                # Group by month and sum
                ds_monthly = ds_tanzania.resample(time="1MS").sum()

                # Calculate spatial mean (average over Tanzania region)
                for time_idx in range(len(ds_monthly.time)):
                    time_val = pd.Timestamp(ds_monthly.time.values[time_idx])
                    precip_data = ds_monthly["precip"].isel(time=time_idx)

                    # Calculate mean rainfall over the region
                    mean_rainfall = float(precip_data.mean().values)

                    all_data.append(
                        {
                            "year": time_val.year,
                            "month": time_val.month,
                            "rainfall_mm": mean_rainfall,
                            "lat_min": bounds["lat_min"],
                            "lat_max": bounds["lat_max"],
                            "lon_min": bounds["lon_min"],
                            "lon_max": bounds["lon_max"],
                        }
                    )

                # Clean up temp file
                ds.close()
                os.unlink(tmp_path)

                log_info(f"Successfully processed CHIRPS data for {year}")

            except requests.exceptions.RequestException as e:
                log_error(f"Failed to download CHIRPS data for {year}: {e}")
                # Continue with other years
                continue
            except Exception as e:
                log_error(f"Error processing CHIRPS data for {year}: {e}")
                continue

        if not all_data:
            log_error("No CHIRPS data was successfully downloaded")
            raise ValueError("Failed to fetch any CHIRPS data")

        # Create DataFrame
        df = pd.DataFrame(all_data)
        df = df.sort_values(["year", "month"]).reset_index(drop=True)

        log_info(f"Successfully fetched {len(df)} records from CHIRPS")

        # Validate the dataframe
        expected_cols = ["year", "month", "rainfall_mm"]
        validate_dataframe(df, expected_columns=expected_cols, dataset_name="CHIRPS")

        # Save raw data
        csv_path = get_data_path("raw", "chirps_raw.csv")
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
        log_info(f"CHIRPS data saved to: {csv_path}")

        return df

    except Exception as e:
        log_error(f"Failed to fetch CHIRPS data: {e}")
        raise


def fetch_data(*args, **kwargs):
    return fetch_chirps_data(*args, **kwargs)
