"""
ERA5 Ingestion - Phase 2
Fetches reanalysis climate data from Copernicus Climate Data Store (CDS)
"""

import os

import pandas as pd

from utils.config import get_data_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe

# Tanzania bounding box
TANZANIA_BOUNDS = {
    "north": -0.99,
    "south": -11.75,
    "west": 29.34,
    "east": 40.44,
}


def fetch_era5_data(
    dry_run=False,
    start_year=2010,
    end_year=2023,
    bounds=None,
    variables=None,
    *args,
    **kwargs,
):
    """
    Fetch ERA5 reanalysis data from Copernicus Climate Data Store.

    Args:
        dry_run: If True, return placeholder data without API call
        start_year: Start year for data retrieval
        end_year: End year for data retrieval
        bounds: Geographic bounds dict with north, south, west, east keys
        variables: List of ERA5 variables to fetch

    Returns:
        pandas DataFrame with climate data

    Note:
        Requires cdsapi package and valid CDS API credentials in ~/.cdsapirc
        To set up: https://cds.climate.copernicus.eu/api-how-to
    """
    log_info(f"Fetching ERA5 data... (dry run: {dry_run})")

    if dry_run:
        # Return placeholder data for testing
        df = pd.DataFrame({"YEAR": [2020, 2021], "TEMP": [23.5, 24.2], "HUMIDITY": [70, 72]})
        log_info("Dry run mode: returning placeholder data")
        return df

    # Check if cdsapi is installed
    try:
        import cdsapi
    except ImportError:
        log_error(
            "cdsapi package not installed. Install with: pip install cdsapi\n"
            "Also configure credentials: https://cds.climate.copernicus.eu/api-how-to"
        )
        raise ImportError("cdsapi package required for ERA5 data fetching")

    # Use default bounds if not specified
    if bounds is None:
        bounds = TANZANIA_BOUNDS

    # Default variables if not specified
    if variables is None:
        variables = [
            "2m_temperature",
            "2m_dewpoint_temperature",
            "total_precipitation",
            "surface_pressure",
            "10m_u_component_of_wind",
            "10m_v_component_of_wind",
        ]

    try:
        # Initialize CDS API client
        c = cdsapi.Client()

        # Prepare download path
        nc_file = get_data_path("raw", "era5_raw.nc")
        os.makedirs(os.path.dirname(nc_file), exist_ok=True)

        log_info(f"Requesting ERA5 data for years {start_year}-{end_year}")
        log_info(f"Variables: {', '.join(variables)}")

        # Build year list
        years = [str(year) for year in range(start_year, end_year + 1)]

        # Request data from CDS
        c.retrieve(
            "reanalysis-era5-single-levels-monthly-means",
            {
                "product_type": "monthly_averaged_reanalysis",
                "variable": variables,
                "year": years,
                "month": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
                "time": "00:00",
                "area": [
                    bounds["north"],
                    bounds["west"],
                    bounds["south"],
                    bounds["east"],
                ],
                "format": "netcdf",
            },
            nc_file,
        )

        log_info(f"ERA5 data downloaded to: {nc_file}")

        # Convert NetCDF to DataFrame
        try:
            import xarray as xr

            ds = xr.open_dataset(nc_file)

            # Extract data and convert to DataFrame
            records = []
            for time_idx in range(len(ds.time)):
                time_val = pd.Timestamp(ds.time.values[time_idx])
                year = time_val.year
                month = time_val.month

                # Get spatial mean for each variable
                record = {"year": year, "month": month}

                for var in ds.data_vars:
                    # Calculate spatial mean (average over lat/lon)
                    var_data = ds[var].isel(time=time_idx)
                    mean_val = float(var_data.mean().values)
                    record[var] = mean_val

                records.append(record)

            df = pd.DataFrame(records)

            # Rename columns to more readable names
            column_mapping = {
                "t2m": "temp_2m",
                "d2m": "dewpoint_2m",
                "tp": "total_precip",
                "sp": "surface_pressure",
                "u10": "wind_u_10m",
                "v10": "wind_v_10m",
            }
            df = df.rename(columns=column_mapping)

            log_info(f"Successfully processed {len(df)} records from ERA5 data")

            # Validate the dataframe
            expected_cols = ["year", "month"]
            validate_dataframe(df, expected_columns=expected_cols, dataset_name="ERA5")

            # Save as CSV
            csv_path = get_data_path("raw", "era5_raw.csv")
            df.to_csv(csv_path, index=False)
            log_info(f"ERA5 data saved to: {csv_path}")

            return df

        except ImportError:
            log_error("xarray package not installed. Install with: pip install xarray netCDF4")
            raise ImportError("xarray and netCDF4 packages required for processing ERA5 NetCDF files")

    except Exception as e:
        log_error(f"Failed to fetch ERA5 data: {e}")
        raise


def fetch_data(*args, **kwargs):
    return fetch_era5_data(*args, **kwargs)
