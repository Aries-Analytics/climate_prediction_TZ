"""
ERA5 Data Processing - Phase 3
Transforms raw ERA5 reanalysis data with unit conversions and derived features.
"""

import numpy as np
import pandas as pd

from utils.config import get_data_path, get_output_path
from utils.logger import log_info
from utils.validator import validate_dataframe


def kelvin_to_celsius(temp_k):
    """Convert temperature from Kelvin to Celsius."""
    return temp_k - 273.15


def meters_to_mm(precip_m):
    """Convert precipitation from meters to millimeters."""
    return precip_m * 1000


def pa_to_hpa(pressure_pa):
    """Convert pressure from Pascals to hectoPascals (millibars)."""
    return pressure_pa / 100


def calculate_wind_speed(u_component, v_component):
    """
    Calculate wind speed from U and V components.

    Parameters
    ----------
    u_component : pd.Series
        U-component of wind (m/s).
    v_component : pd.Series
        V-component of wind (m/s).

    Returns
    -------
    pd.Series
        Wind speed in m/s.
    """
    return np.sqrt(u_component**2 + v_component**2)


def calculate_relative_humidity(temp_c, dewpoint_c):
    """
    Calculate relative humidity from temperature and dewpoint.

    Parameters
    ----------
    temp_c : pd.Series
        Temperature in Celsius.
    dewpoint_c : pd.Series
        Dewpoint temperature in Celsius.

    Returns
    -------
    pd.Series
        Relative humidity in percentage.
    """
    # Magnus formula for saturation vapor pressure
    a = 17.27
    b = 237.7

    alpha_t = (a * temp_c) / (b + temp_c)
    alpha_td = (a * dewpoint_c) / (b + dewpoint_c)

    rh = 100 * np.exp(alpha_td - alpha_t)

    # Clip to valid range
    rh = np.clip(rh, 0, 100)

    return rh


def calculate_pet_penman(temp_c, wind_speed_ms, rel_humidity_pct, solar_rad_wm2=None):
    """
    Calculate Potential Evapotranspiration using simplified Penman method.

    Parameters
    ----------
    temp_c : pd.Series
        Temperature in Celsius.
    wind_speed_ms : pd.Series
        Wind speed in m/s.
    rel_humidity_pct : pd.Series
        Relative humidity in percentage.
    solar_rad_wm2 : pd.Series, optional
        Solar radiation in W/m². If None, uses temperature-based estimate.

    Returns
    -------
    pd.Series
        PET in mm/day.

    Notes
    -----
    Simplified Penman-Monteith equation for daily PET estimation.
    """
    # Simplified PET calculation (Hargreaves-Samani if no solar radiation)
    if solar_rad_wm2 is None:
        # Temperature-based estimate
        pet = 0.0023 * (temp_c + 17.8) * np.sqrt(temp_c + 17.8) * 0.408
    else:
        # Radiation-based estimate
        pet = 0.0135 * solar_rad_wm2 * (temp_c + 17.8) / 2450

    # Adjust for humidity and wind
    humidity_factor = 1 + (100 - rel_humidity_pct) / 100 * 0.3
    wind_factor = 1 + wind_speed_ms * 0.1

    pet = pet * humidity_factor * wind_factor

    return np.maximum(0, pet)


def process(data):
    """
    Process ERA5 reanalysis data with unit conversions and derived features.

    Parameters
    ----------
    data : pd.DataFrame
        Raw ERA5 data from ingestion.

    Returns
    -------
    pd.DataFrame
        Processed dataset with converted units and derived features.

    Transformations
    ---------------
    1. Unit conversions:
       - Temperature: Kelvin → Celsius
       - Precipitation: meters → millimeters
       - Pressure: Pascals → hectoPascals
    2. Derived features:
       - Wind speed from U/V components
       - Relative humidity from temp/dewpoint
       - Potential evapotranspiration (PET)
       - Dew point depression
    3. Quality filtering and validation
    """
    log_info("[PROCESS] Running ERA5 data transformation...")

    if data is None or data.empty:
        log_info("[PROCESS] No data to process, returning empty DataFrame")
        return pd.DataFrame()

    df = data.copy()

    log_info(f"[PROCESS] Processing {len(df)} records")

    # 1. Unit conversions
    if "temp_2m" in df.columns:
        log_info("[PROCESS] Converting temperature from Kelvin to Celsius...")
        df["temp_2m_c"] = kelvin_to_celsius(df["temp_2m"])

    if "dewpoint_2m" in df.columns:
        log_info("[PROCESS] Converting dewpoint from Kelvin to Celsius...")
        df["dewpoint_2m_c"] = kelvin_to_celsius(df["dewpoint_2m"])

    if "total_precip" in df.columns:
        log_info("[PROCESS] Converting precipitation from meters to millimeters...")
        df["precip_mm"] = meters_to_mm(df["total_precip"])

    if "surface_pressure" in df.columns:
        log_info("[PROCESS] Converting pressure from Pa to hPa...")
        df["pressure_hpa"] = pa_to_hpa(df["surface_pressure"])

    # 2. Calculate wind speed
    if "wind_u_10m" in df.columns and "wind_v_10m" in df.columns:
        log_info("[PROCESS] Calculating wind speed...")
        df["wind_speed_ms"] = calculate_wind_speed(df["wind_u_10m"], df["wind_v_10m"])

        # Wind direction (degrees from north)
        df["wind_direction_deg"] = np.degrees(np.arctan2(df["wind_v_10m"], df["wind_u_10m"])) % 360

    # 3. Calculate relative humidity
    if "temp_2m_c" in df.columns and "dewpoint_2m_c" in df.columns:
        log_info("[PROCESS] Calculating relative humidity...")
        df["rel_humidity_pct"] = calculate_relative_humidity(df["temp_2m_c"], df["dewpoint_2m_c"])

        # Dew point depression (indicator of atmospheric moisture)
        df["dewpoint_depression_c"] = df["temp_2m_c"] - df["dewpoint_2m_c"]

    # 4. Calculate potential evapotranspiration
    if all(col in df.columns for col in ["temp_2m_c", "wind_speed_ms", "rel_humidity_pct"]):
        log_info("[PROCESS] Calculating potential evapotranspiration...")
        df["pet_mm"] = calculate_pet_penman(df["temp_2m_c"], df["wind_speed_ms"], df["rel_humidity_pct"])

    # 5. Quality filtering
    initial_count = len(df)

    if "temp_2m_c" in df.columns:
        df = df[df["temp_2m_c"].between(-20, 50)]

    if "precip_mm" in df.columns:
        df = df[df["precip_mm"] >= 0]
        df = df[df["precip_mm"] < 500]  # Remove extreme outliers

    if "rel_humidity_pct" in df.columns:
        df = df[df["rel_humidity_pct"].between(0, 100)]

    filtered_count = initial_count - len(df)
    if filtered_count > 0:
        log_info(f"[PROCESS] Filtered out {filtered_count} records with unrealistic values")

    # 6. Validate and save
    # Only validate if we have the expected structure
    if "year" in df.columns and "month" in df.columns:
        expected_cols = ["year", "month"]
        validate_dataframe(df, expected_columns=expected_cols, dataset_name="ERA5 Processed")
    else:
        # For dry-run or minimal data, just validate it's not empty
        validate_dataframe(df, expected_columns=None, dataset_name="ERA5 Processed")

    output_path = get_data_path("processed", "era5_processed.csv")
    df.to_csv(output_path, index=False)
    log_info(f"[SAVE] Processed output saved to {output_path}")
    log_info(f"[PROCESS] ERA5 data processed successfully: {len(df)} records, {len(df.columns)} features")

    return df
