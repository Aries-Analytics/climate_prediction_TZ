"""
ERA5 Ingestion - Phase 2
Fetches reanalysis climate data from Copernicus Climate Data Store (CDS)
"""

import os
from datetime import datetime
from typing import Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session

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
    start_year=1985,
    end_year=2025,
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
        df = pd.DataFrame(
            {"year": [2020, 2021], "month": [1, 1], "temp_2m": [296.5, 297.2], "total_precip": [0.05, 0.07]}
        )
        log_info("Dry run mode: returning placeholder data")
        return df

    # Check if ecmwf-datastores-client is installed (replaces deprecated cdsapi)
    try:
        from ecmwf.datastores import Client as ECMWFClient
    except ImportError:
        log_error(
            "ecmwf-datastores-client package not installed. Install with: pip install ecmwf-datastores-client\n"
            "Configure credentials: https://ecmwf.github.io/ecmwf-datastores-client/README.html#configuration"
        )
        raise ImportError("ecmwf-datastores-client package required for ERA5 data fetching")

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
            "volumetric_soil_water_layer_1",  # Soil moisture (0-7cm depth)
        ]

    try:
        # Initialize the new ECMWF Data Stores client
        # Reads from env vars: ECMWF_DATASTORES_URL, ECMWF_DATASTORES_KEY
        # Or from config file: ~/.ecmwfdatastoresrc
        api_url = os.getenv("ECMWF_DATASTORES_URL", "https://cds.climate.copernicus.eu/api")
        api_key = os.getenv("ECMWF_DATASTORES_KEY") or os.getenv("ERA5_API_KEY")
        
        if api_key:
            c = ECMWFClient(url=api_url, key=api_key)
        else:
            # Fall back to ~/.ecmwfdatastoresrc configuration
            c = ECMWFClient()

        # Prepare download path
        nc_file = get_data_path("raw", "era5_raw.nc")
        os.makedirs(os.path.dirname(nc_file), exist_ok=True)

        log_info(f"Requesting ERA5 data for years {start_year}-{end_year}")
        log_info(f"Variables: {', '.join(variables)}")

        # Build year list
        years = [str(year) for year in range(start_year, end_year + 1)]

        # Request data from CDS using new client
        # New API requires list values for most parameters
        c.retrieve(
            "reanalysis-era5-single-levels-monthly-means",
            {
                "product_type": ["monthly_averaged_reanalysis"],
                "variable": variables,
                "year": years,
                "month": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
                "time": ["00:00"],
                "area": [
                    bounds["north"],
                    bounds["west"],
                    bounds["south"],
                    bounds["east"],
                ],
                "data_format": "netcdf",
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
                "swvl1": "soil_moisture",  # Volumetric soil water layer 1
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


def ingest_era5(
    db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, incremental: bool = True
) -> Tuple[int, int]:
    """
    Ingest ERA5 data and store to database (orchestrator-compatible interface).

    This function is designed to be called by the pipeline orchestrator.
    It fetches ERA5 data for the specified date range and stores it in the database.

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

    # Set default date range
    if start_date is None:
        start_date = datetime(2010, 1, 1)
    if end_date is None:
        end_date = datetime.now()

    # Ensure dates are pandas-compatible timestamps for comparison
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    log_info(f"Ingesting ERA5 data from {start_date} to {end_date}")

    try:
        # Fetch data using existing function
        df = fetch_era5_data(start_year=start_date.year, end_year=end_date.year, dry_run=False)

        if df.empty:
            log_info("No ERA5 data fetched")
            return (0, 0)

        records_fetched = len(df)
        log_info(f"Fetched {records_fetched} ERA5 records")

        # Filter to exact date range (month-level granularity)
        df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

        # Store to database (ERA5 provides regional averages, use Tanzania center point)
        records_stored = 0
        tanzania_lat = -6.369028
        tanzania_lon = 34.888822

        for _, row in df.iterrows():
            try:
                # Check if record already exists
                existing = (
                    db.query(ClimateData)
                    .filter(
                        and_(
                            ClimateData.date == row["date"].date(),
                            ClimateData.location_lat == tanzania_lat,
                            ClimateData.location_lon == tanzania_lon,
                        )
                    )
                    .first()
                )

                if existing:
                    # Update existing record with ERA5 data
                    if "temp_2m" in row:
                        # Convert Kelvin to Celsius
                        existing.temperature_avg = float(row["temp_2m"]) - 273.15
                    if "soil_moisture" in row:
                        existing.soil_moisture = float(row["soil_moisture"])
                    if "dewpoint_2m" in row and row["dewpoint_2m"] is not None:
                        existing.dewpoint_2m = float(row["dewpoint_2m"]) - 273.15
                    if "surface_pressure" in row and row["surface_pressure"] is not None:
                        existing.surface_pressure = float(row["surface_pressure"])
                    if "wind_u_10m" in row and row["wind_u_10m"] is not None:
                        existing.wind_u_10m = float(row["wind_u_10m"])
                    if "wind_v_10m" in row and row["wind_v_10m"] is not None:
                        existing.wind_v_10m = float(row["wind_v_10m"])
                    # Derive wind speed and direction from u/v components
                    if "wind_u_10m" in row and "wind_v_10m" in row and row["wind_u_10m"] is not None and row["wind_v_10m"] is not None:
                        import math
                        u, v = float(row["wind_u_10m"]), float(row["wind_v_10m"])
                        existing.wind_speed_ms = math.sqrt(u**2 + v**2)
                        existing.wind_direction_deg = (math.degrees(math.atan2(-u, -v)) + 360) % 360
                    records_stored += 1
                else:
                    # Create new record
                    # Derive wind speed and direction from u/v components
                    ws = None
                    wd = None
                    if "wind_u_10m" in row and "wind_v_10m" in row and row["wind_u_10m"] is not None and row["wind_v_10m"] is not None:
                        import math
                        u, v = float(row["wind_u_10m"]), float(row["wind_v_10m"])
                        ws = math.sqrt(u**2 + v**2)
                        wd = (math.degrees(math.atan2(-u, -v)) + 360) % 360
                    climate_record = ClimateData(
                        date=row["date"].date(),
                        location_lat=tanzania_lat,
                        location_lon=tanzania_lon,
                        temperature_avg=float(row["temp_2m"]) - 273.15 if "temp_2m" in row else None,
                        soil_moisture=float(row["soil_moisture"]) if "soil_moisture" in row else None,
                        dewpoint_2m=float(row["dewpoint_2m"]) - 273.15 if "dewpoint_2m" in row and row["dewpoint_2m"] is not None else None,
                        surface_pressure=float(row["surface_pressure"]) if "surface_pressure" in row and row["surface_pressure"] is not None else None,
                        wind_u_10m=float(row["wind_u_10m"]) if "wind_u_10m" in row and row["wind_u_10m"] is not None else None,
                        wind_v_10m=float(row["wind_v_10m"]) if "wind_v_10m" in row and row["wind_v_10m"] is not None else None,
                        wind_speed_ms=ws,
                        wind_direction_deg=wd,
                    )
                    db.add(climate_record)
                    records_stored += 1

            except Exception as e:
                log_error(f"Failed to store ERA5 record for {row['date']}: {e}")
                continue

        # Commit all changes
        db.commit()
        log_info(f"Successfully stored {records_stored} ERA5 records to database")

        return (records_fetched, records_stored)

    except Exception as e:
        log_error(f"ERA5 ingestion failed: {e}")
        db.rollback()
        raise
