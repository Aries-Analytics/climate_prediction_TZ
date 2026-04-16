"""
NASA POWER Data Processing - Phase 3
Transforms raw NASA POWER data with real climate indices and quality filtering.
"""

import numpy as np
import pandas as pd

from utils.config import get_data_path
from utils.logger import log_info
from utils.validator import validate_dataframe


def calculate_heat_index(temp_c, humidity_pct):
    """
    Calculate heat index (feels-like temperature).

    Parameters
    ----------
    temp_c : pd.Series
        Temperature in Celsius.
    humidity_pct : pd.Series
        Relative humidity in percentage.

    Returns
    -------
    pd.Series
        Heat index in Celsius.

    Notes
    -----
    Uses simplified Steadman formula for heat index calculation.
    """
    # Convert to Fahrenheit for calculation
    temp_f = temp_c * 9 / 5 + 32

    # Simplified heat index formula
    hi_f = (
        -42.379
        + 2.04901523 * temp_f
        + 10.14333127 * humidity_pct
        - 0.22475541 * temp_f * humidity_pct
        - 6.83783e-3 * temp_f**2
        - 5.481717e-2 * humidity_pct**2
        + 1.22874e-3 * temp_f**2 * humidity_pct
        + 8.5282e-4 * temp_f * humidity_pct**2
        - 1.99e-6 * temp_f**2 * humidity_pct**2
    )

    # Convert back to Celsius
    hi_c = (hi_f - 32) * 5 / 9

    # Only apply heat index when temp > 27°C and humidity > 40%
    hi_c = np.where((temp_c > 27) & (humidity_pct > 40), hi_c, temp_c)

    return hi_c


def calculate_gdd(temp_mean_c, base_temp=10, max_temp=30):
    """
    Calculate Growing Degree Days (GDD).

    Parameters
    ----------
    temp_mean_c : pd.Series
        Mean daily temperature in Celsius.
    base_temp : float, optional
        Base temperature for crop growth (default: 10°C).
    max_temp : float, optional
        Maximum effective temperature (default: 30°C).

    Returns
    -------
    pd.Series
        Growing degree days.

    Notes
    -----
    GDD = max(0, min(temp_mean, max_temp) - base_temp)
    Used for crop development stage prediction.
    """
    effective_temp = np.minimum(temp_mean_c, max_temp)
    gdd = np.maximum(0, effective_temp - base_temp)
    return gdd


def calculate_vapor_pressure_deficit(temp_c, humidity_pct):
    """
    Calculate Vapor Pressure Deficit (VPD).

    Parameters
    ----------
    temp_c : pd.Series
        Temperature in Celsius.
    humidity_pct : pd.Series
        Relative humidity in percentage.

    Returns
    -------
    pd.Series
        VPD in kPa.

    Notes
    -----
    VPD indicates atmospheric moisture demand.
    High VPD = dry air, plant stress.
    """
    # Saturation vapor pressure (kPa)
    svp = 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))

    # Actual vapor pressure
    avp = svp * (humidity_pct / 100)

    # VPD
    vpd = svp - avp

    return vpd


def process(data):
    """
    Process NASA POWER climate data with real transformations.

    Parameters
    ----------
    data : pd.DataFrame
        Raw NASA POWER data from ingestion.

    Returns
    -------
    pd.DataFrame
        Processed dataset with derived climate indices.

    Transformations
    ---------------
    1. Column standardization and renaming
    2. Unit conversions (if needed)
    3. Derived climate indices:
       - Heat index (feels-like temperature)
       - Growing Degree Days (GDD)
       - Vapor Pressure Deficit (VPD)
       - Temperature range
    4. Quality filtering:
       - Remove unrealistic temperature values
       - Remove negative precipitation
       - Flag suspicious data points
    5. Data validation and persistence

    Notes
    -----
    Output includes both original and derived features for downstream modeling.
    """
    log_info("[PROCESS] Running NASA POWER data transformation...")

    if data is None or data.empty:
        log_info("[PROCESS] No data to process, returning empty DataFrame")
        return pd.DataFrame()

    df = data.copy()

    # 1. Standardize column names
    column_mapping = {
        "t2m": "temp_mean_c",
        "t2m_max": "temp_max_c",
        "t2m_min": "temp_min_c",
        "prectotcorr": "precip_mm",
        "rh2m": "humidity_pct",
        "allsky_sfc_sw_dwn": "solar_rad_wm2",
    }

    # Rename columns that exist
    existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_cols)

    log_info(f"[PROCESS] Processing {len(df)} records with columns: {list(df.columns)}")

    # 2. Calculate derived climate indices
    if "temp_mean_c" in df.columns and "humidity_pct" in df.columns:
        log_info("[PROCESS] Calculating heat index...")
        df["heat_index_c"] = calculate_heat_index(df["temp_mean_c"], df["humidity_pct"])

        log_info("[PROCESS] Calculating vapor pressure deficit...")
        df["vpd_kpa"] = calculate_vapor_pressure_deficit(df["temp_mean_c"], df["humidity_pct"])

    if "temp_mean_c" in df.columns:
        log_info("[PROCESS] Calculating growing degree days...")
        df["gdd_base10"] = calculate_gdd(df["temp_mean_c"], base_temp=10)
        df["gdd_base15"] = calculate_gdd(df["temp_mean_c"], base_temp=15)

    if "temp_max_c" in df.columns and "temp_min_c" in df.columns:
        log_info("[PROCESS] Calculating temperature range...")
        df["temp_range_c"] = df["temp_max_c"] - df["temp_min_c"]
        df["temp_variability"] = df["temp_range_c"] / df["temp_mean_c"].abs()

    # 3. Quality filtering
    initial_count = len(df)

    # Filter unrealistic temperatures for Tanzania (-10°C to 50°C)
    if "temp_mean_c" in df.columns:
        df = df[df["temp_mean_c"].between(-10, 50)]

    if "temp_max_c" in df.columns:
        df = df[df["temp_max_c"].between(-5, 55)]

    if "temp_min_c" in df.columns:
        df = df[df["temp_min_c"].between(-15, 45)]

    # Filter negative precipitation
    if "precip_mm" in df.columns:
        df = df[df["precip_mm"] >= 0]

    # Filter unrealistic humidity (0-100%)
    if "humidity_pct" in df.columns:
        df = df[df["humidity_pct"].between(0, 100)]

    # Filter unrealistic solar radiation (0-500 W/m²)
    if "solar_rad_wm2" in df.columns:
        df = df[df["solar_rad_wm2"].between(0, 500)]

    filtered_count = initial_count - len(df)
    if filtered_count > 0:
        log_info(f"[PROCESS] Filtered out {filtered_count} records with unrealistic values")

    # 4. Add data quality flags
    df["data_quality"] = "good"

    # Flag extreme values (potential outliers)
    if "temp_mean_c" in df.columns:
        temp_mean = df["temp_mean_c"].mean()
        temp_std = df["temp_mean_c"].std()
        df.loc[df["temp_mean_c"] > temp_mean + 3 * temp_std, "data_quality"] = "extreme_high_temp"
        df.loc[df["temp_mean_c"] < temp_mean - 3 * temp_std, "data_quality"] = "extreme_low_temp"

    # 5. Validate processed data
    # Only validate if we have the expected structure
    # Create date column for easier manipulation
    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

    # Process by location if 'location' column exists
    if "location" in df.columns:
        log_info(f"Processing data for {df['location'].nunique()} locations...")
        # Most operations in NASA POWER are row-wise (heat index, GDD, filters)
        # However, outlier detection (mean + 3*std) should ideally be per-location
        # We'll stick to global processing for now as it's efficient, unless specific rolling stats are added.
        # But we must ensure validation is happy.

    # Drop temporary date column
    df = df.drop(columns=["date"])

    # Validate output
    expected_cols = ["year", "month", "temp_mean_c", "precip_mm"]
    validate_dataframe(df, expected_columns=expected_cols, dataset_name="NASA POWER Processed")

    # Save processed data
    output_path = get_data_path("processed", "nasa_power_processed.csv")
    df.to_csv(output_path, index=False)
    log_info(f"Processed NASA POWER data saved to: {output_path}")

    return df


def _process_single_location(df):
    """Process logic for a single location group (placeholder for future use)."""
    return df
