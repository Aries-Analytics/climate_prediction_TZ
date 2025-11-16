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

    Downloads monthly averaged ERA5 reanalysis data as NetCDF files and processes
    them into pandas DataFrame with spatial mean over specified region.

    Parameters
    ----------
    dry_run : bool, optional
        If True, return placeholder data without making API call. Default is False.
    start_year : int, optional
        Start year for data retrieval (inclusive). Default is 2010.
    end_year : int, optional
        End year for data retrieval (inclusive). Default is 2023.
    bounds : dict, optional
        Geographic bounding box with keys: 'north', 'south', 'west', 'east' (degrees).
        If None, uses Tanzania bounds: {north: -0.99, south: -11.75, west: 29.34, east: 40.44}.
    variables : list of str, optional
        List of ERA5 variable names to fetch. If None, fetches default variables:
        ['2m_temperature', '2m_dewpoint_temperature', 'total_precipitation',
         'surface_pressure', '10m_u_component_of_wind', '10m_v_component_of_wind'].

    Returns
    -------
    pd.DataFrame
        DataFrame with monthly climate data containing columns:
        - year (int): Year of observation
        - month (int): Month of observation (1-12)
        - temp_2m (float): Mean temperature at 2m (K)
        - dewpoint_2m (float): Mean dewpoint temperature (K)
        - total_precip (float): Total precipitation (m)
        - surface_pressure (float): Mean surface pressure (Pa)
        - wind_u_10m (float): Mean U-component of wind (m/s)
        - wind_v_10m (float): Mean V-component of wind (m/s)

    Raises
    ------
    ImportError
        If cdsapi or xarray packages are not installed.
    Exception
        If CDS API request fails (authentication error, network error, invalid parameters).

    Notes
    -----
    **Prerequisites:**

    1. Install required packages:
       ``pip install cdsapi xarray netCDF4``

    2. Configure CDS API credentials in ~/.cdsapirc:

       .. code-block:: text

           url: https://cds.climate.copernicus.eu/api/v2
           key: {UID}:{API-KEY}

    3. Get credentials from: https://cds.climate.copernicus.eu/user

    **Data Processing:**

    - Downloads NetCDF file to data/raw/era5_raw.nc
    - Calculates spatial mean over specified geographic region
    - Saves processed data to data/raw/era5_raw.csv
    - Temperature values are in Kelvin (convert to Celsius: K - 273.15)
    - Precipitation is in meters (convert to mm: m × 1000)

    **Performance:**

    - Requests can take several minutes as CDS queues large downloads
    - Downloaded NetCDF files can be tens to hundreds of MB

    Examples
    --------
    >>> from modules.ingestion.era5_ingestion import fetch_era5_data
    >>>
    >>> # Fetch data for Tanzania (default bounds)
    >>> df = fetch_era5_data(start_year=2020, end_year=2023)
    >>>
    >>> # Fetch data for custom region
    >>> custom_bounds = {
    ...     'north': -5.0,
    ...     'south': -8.0,
    ...     'west': 33.0,
    ...     'east': 36.0
    ... }
    >>> df = fetch_era5_data(bounds=custom_bounds, start_year=2020, end_year=2023)
    >>>
    >>> # Fetch specific variables only
    >>> df = fetch_era5_data(
    ...     variables=['2m_temperature', 'total_precipitation'],
    ...     start_year=2020,
    ...     end_year=2023
    ... )
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

        # Check if file is a ZIP archive and extract if needed
        import zipfile

        if zipfile.is_zipfile(nc_file):
            log_info("Downloaded file is a ZIP archive, extracting...")
            with zipfile.ZipFile(nc_file, "r") as zip_ref:
                # Extract all files
                zip_ref.extractall(os.path.dirname(nc_file))
                # Get the first .nc or .grib file
                extracted_files = [f for f in zip_ref.namelist() if f.endswith((".nc", ".grib", ".grib2"))]
                if extracted_files:
                    nc_file = os.path.join(os.path.dirname(nc_file), extracted_files[0])
                    log_info(f"Extracted file: {nc_file}")
                else:
                    raise ValueError("No NetCDF or GRIB files found in ZIP archive")

        # Convert NetCDF/GRIB to DataFrame
        try:
            import xarray as xr

            # Try to open with different engines
            ds = None
            engines_to_try = ["netcdf4", "h5netcdf", "scipy"]

            for engine in engines_to_try:
                try:
                    log_info(f"Trying to open with engine: {engine}")
                    ds = xr.open_dataset(nc_file, engine=engine)
                    log_info(f"Successfully opened with {engine} engine")
                    break
                except Exception as e:
                    log_info(f"Failed with {engine}: {str(e)[:100]}")
                    continue

            if ds is None:
                # Try cfgrib as last resort
                try:
                    log_info("Trying cfgrib engine...")
                    ds = xr.open_dataset(nc_file, engine="cfgrib", backend_kwargs={"errors": "ignore"})
                    log_info("Successfully opened with cfgrib engine")
                except Exception as e:
                    raise ValueError(f"Could not open file with any engine. Last error: {e}")

            if ds is None:
                raise ValueError("Failed to open ERA5 data file with any available engine")

            # Check available dimensions and coordinates
            log_info(f"Dataset dimensions: {list(ds.dims.keys())}")
            log_info(f"Dataset coordinates: {list(ds.coords.keys())}")
            log_info(f"Dataset variables: {list(ds.data_vars.keys())}")

            # Find time dimension (might be 'time', 'valid_time', or other)
            time_dim = None
            for dim in ["time", "valid_time", "forecast_reference_time"]:
                if dim in ds.dims or dim in ds.coords:
                    time_dim = dim
                    break

            if time_dim is None:
                log_error("No time dimension found in ERA5 dataset")
                raise ValueError("Unable to find time dimension in ERA5 dataset. Check NetCDF file structure.")
            else:
                # Extract data and convert to DataFrame
                records = []
                for time_idx in range(len(ds[time_dim])):
                    time_val = pd.Timestamp(ds[time_dim].values[time_idx])
                    year = time_val.year
                    month = time_val.month

                    # Get spatial mean for each variable
                    record = {"year": year, "month": month}

                    for var in ds.data_vars:
                        try:
                            # Calculate spatial mean (average over lat/lon)
                            var_data = ds[var].isel({time_dim: time_idx})
                            mean_val = float(var_data.mean().values)
                            record[var] = mean_val
                        except Exception as e:
                            log_error(f"Error processing variable {var}: {e}")
                            continue

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
