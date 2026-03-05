"""
Feature Engineering Module for Production Serving.

Reconstructs the exact 88 features expected by the deployed ML models from
ClimateData database records. This module mirrors the preprocessing pipeline's
feature engineering logic but operates on a single time-series of ClimateData
records rather than the full master_dataset.csv.

The feature_schema.json file defines the exact feature names and order.
"""

import json
import math
import os
from typing import List, Optional

import numpy as np
import pandas as pd


# Load feature schema (singleton)
_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'feature_schema.json')
_FEATURE_SCHEMA = None


def get_feature_schema() -> dict:
    """Load feature schema from JSON file (cached)."""
    global _FEATURE_SCHEMA
    if _FEATURE_SCHEMA is None:
        # Try multiple paths (dev vs production)
        paths = [
            _SCHEMA_PATH,
            os.path.join(os.path.dirname(__file__), '..', '..', 'feature_schema.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'feature_schema.json'),
        ]
        for p in paths:
            if os.path.exists(p):
                with open(p, 'r') as f:
                    _FEATURE_SCHEMA = json.load(f)
                break
        if _FEATURE_SCHEMA is None:
            raise FileNotFoundError(f"feature_schema.json not found in any of: {paths}")
    return _FEATURE_SCHEMA


def get_expected_features() -> List[str]:
    """Get the list of 88 feature names in model-expected order."""
    return get_feature_schema()['feature_names']


def build_base_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build base (non-lagged, non-rolling) features from ClimateData columns.
    
    Input df columns (from ClimateData query):
        date, temperature, rainfall, ndvi, soil_moisture, enso, iod,
        humidity, rel_humidity, dewpoint, wind_u, wind_v, wind_speed,
        wind_direction, pressure, solar, location_name
    
    Output: DataFrame with all base features.
    """
    result = df.copy()
    
    # Fill None/NaN values in all numeric columns to prevent NoneType errors
    # Climate data often has gaps (e.g., missing ENSO/IOD for recent months)
    numeric_cols = ['temperature', 'rainfall', 'ndvi', 'soil_moisture', 'enso', 'iod',
                    'humidity', 'rel_humidity', 'dewpoint', 'wind_u', 'wind_v',
                    'wind_speed', 'wind_direction', 'pressure', 'solar']
    for col in numeric_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)
    
    # === Temperature features ===
    result['temp_2m'] = result['temperature']
    result['temp_max_c'] = result['temperature']  # Approximation: monthly avg ≈ max for this
    result['temp_min_c'] = result['temperature']   # Will improve with actual min/max data
    result['temp_mean_c'] = result['temperature']
    result['temp_range_c'] = 0.0  # No min/max distinction in monthly data
    result['temp_variability'] = result['temperature'].rolling(3, min_periods=1).std().fillna(0)
    
    # === Precipitation features ===
    result['precip_mm'] = result['rainfall']
    
    # Flood trigger (binary: 1 if precip > 200mm/month, typical flood threshold)
    result['flood_trigger'] = (result['precip_mm'] > 200).astype(float)
    result['flood_trigger_confidence'] = np.where(
        result['precip_mm'] > 200, 
        np.minimum(result['precip_mm'] / 300.0, 1.0),
        0.0
    )
    
    # Dry day proxy (monthly: < 30mm = dry month)
    result['is_dry_day'] = (result['precip_mm'] < 30).astype(float)
    result['consecutive_dry_days'] = result['is_dry_day'].rolling(3, min_periods=1).sum()
    
    # Heavy rain approximation
    result['heavy_rain_days_30day'] = (result['precip_mm'] > 150).astype(float).rolling(3, min_periods=1).sum()
    result['cumulative_excess_7day'] = np.maximum(result['precip_mm'] - 100, 0)
    
    # === NDVI features ===
    result['ndvi'] = result['ndvi_raw'] if 'ndvi_raw' in result.columns else result.get('ndvi', 0)
    
    # Climatological NDVI stats (based on monthly averages across the series)
    if 'month' in result.columns:
        ndvi_clim = result.groupby('month')['ndvi'].agg(['mean', 'std', 'min', 'max']).reset_index()
        ndvi_clim.columns = ['month', 'ndvi_clim_mean', 'ndvi_clim_std', 'ndvi_clim_min', 'ndvi_clim_max']
        result = result.merge(ndvi_clim, on='month', how='left')
    else:
        result['ndvi_clim_mean'] = result['ndvi'].expanding().mean()
        result['ndvi_clim_std'] = result['ndvi'].expanding().std().fillna(0)
        result['ndvi_clim_min'] = result['ndvi'].expanding().min()
        result['ndvi_clim_max'] = result['ndvi'].expanding().max()
    
    # NDVI anomalies
    result['ndvi_anomaly'] = result['ndvi'] - result['ndvi_clim_mean']
    result['ndvi_anomaly_std'] = np.where(
        result['ndvi_clim_std'] > 0,
        result['ndvi_anomaly'] / result['ndvi_clim_std'],
        0
    )
    result['ndvi_anomaly_pct'] = np.where(
        result['ndvi_clim_mean'] > 0,
        result['ndvi_anomaly'] / result['ndvi_clim_mean'] * 100,
        0
    )
    
    # VCI (Vegetation Condition Index)
    ndvi_range = result['ndvi_clim_max'] - result['ndvi_clim_min']
    result['vci'] = np.where(
        ndvi_range > 0,
        (result['ndvi'] - result['ndvi_clim_min']) / ndvi_range * 100,
        50.0
    )
    
    # NDVI change (month-over-month)
    result['ndvi_change_mom'] = result['ndvi'].diff().fillna(0)
    
    # NDVI change year-over-year (12-month diff)
    result['ndvi_change_yoy'] = result['ndvi'].diff(12).fillna(0)
    
    # NDVI percentile
    result['ndvi_percentile'] = result['ndvi'].rank(pct=True) * 100
    
    # NDVI deficit from max
    result['ndvi_deficit_from_max'] = result['ndvi_clim_max'] - result['ndvi']
    
    # NDVI deficit percentage
    result['ndvi_deficit_pct'] = np.where(
        result['ndvi_clim_max'] > 0,
        result['ndvi_deficit_from_max'] / result['ndvi_clim_max'] * 100,
        0
    )
    
    # NDVI 30-day mean (1-month rolling for monthly data)
    result['ndvi_30day_mean'] = result['ndvi'].rolling(1, min_periods=1).mean()
    
    # === ENSO features ===
    result['enso_intensity'] = result['enso'].abs()
    result['is_el_nino'] = (result['enso'] > 0.5).astype(float)
    result['is_strong_el_nino'] = (result['enso'] > 1.5).astype(float)
    result['enso_trend_3month'] = result['enso'].diff(3).fillna(0)
    
    # Rainfall probability categories based on ENSO state
    result['prob_normal_rainfall'] = np.where(result['enso'].abs() < 0.5, 0.6, 0.3)
    result['prob_above_normal_rainfall'] = np.where(result['enso'] > 0.5, 0.5, 0.2)
    result['prob_below_normal_rainfall'] = np.where(result['enso'] < -0.5, 0.5, 0.2)
    
    # === IOD features ===
    result['iod_seasonal_impact'] = result['iod'] * np.where(
        result.get('month', pd.Series([6]*len(result))).between(10, 12), 1.5, 0.5
    )
    
    # === Season features ===
    if 'month' in result.columns:
        result['is_long_rains'] = result['month'].between(3, 5).astype(float)
    else:
        result['is_long_rains'] = 0.0
    
    # === Atmospheric features (from expanded ClimateData) ===
    result['rel_humidity_pct'] = result.get('rel_humidity', pd.Series([65.0]*len(result)))
    result['humidity_pct'] = result.get('humidity', result.get('rel_humidity', pd.Series([65.0]*len(result))))
    result['dewpoint_2m'] = result.get('dewpoint', pd.Series([18.0]*len(result)))
    result['wind_u_10m'] = result.get('wind_u', pd.Series([0.0]*len(result)))
    result['wind_v_10m'] = result.get('wind_v', pd.Series([0.0]*len(result)))
    result['wind_speed_ms'] = result.get('wind_speed', pd.Series([2.0]*len(result)))
    result['wind_direction_deg'] = result.get('wind_direction', pd.Series([180.0]*len(result)))
    result['surface_pressure'] = result.get('pressure', pd.Series([92000.0]*len(result)))
    result['solar_rad_wm2'] = result.get('solar', pd.Series([200.0]*len(result)))
    
    # Derived: VPD (Vapor Pressure Deficit)
    temp_c = result['temperature'].fillna(25)
    rh = result['rel_humidity_pct'].fillna(65)
    sat_vp = 0.6108 * np.exp(17.27 * temp_c / (temp_c + 237.3))  # kPa
    result['vpd_kpa'] = sat_vp * (1 - rh / 100)
    
    # Derived: PET (Hargreaves simplified)
    solar = result['solar_rad_wm2'].fillna(200)
    result['pet_mm'] = 0.0023 * (temp_c + 17.8) * np.sqrt(np.maximum(result['temp_range_c'], 0.1)) * solar * 0.01
    
    # === Location encoding ===
    if 'location_name' in result.columns:
        result['loc_Dodoma'] = (result['location_name'].str.contains('Dodoma', case=False, na=False)).astype(float)
    else:
        result['loc_Dodoma'] = 0.0
    
    return result


def build_lag_features(df: pd.DataFrame, columns: List[str], lags: List[int] = [1, 3, 6]) -> pd.DataFrame:
    """Create lag features for specified columns."""
    result = df.copy()
    for col in columns:
        if col in result.columns:
            for lag in lags:
                lag_name = f"{col}_lag_{lag}"
                result[lag_name] = result[col].shift(lag)
    return result


def build_rolling_features(df: pd.DataFrame, columns: List[str], windows: List[int] = [3]) -> pd.DataFrame:
    """Create rolling mean and std features for specified columns."""
    result = df.copy()
    for col in columns:
        if col in result.columns:
            for window in windows:
                mean_name = f"{col}_rolling_mean_{window}"
                std_name = f"{col}_rolling_std_{window}"
                result[mean_name] = result[col].rolling(window, min_periods=1).mean()
                result[std_name] = result[col].rolling(window, min_periods=1).std().fillna(0)
    return result


def build_feature_vector(climate_records: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Build the complete 88-feature vector from ClimateData records.
    
    This is the main entry point called by forecast_service.prepare_features().
    
    Args:
        climate_records: DataFrame with columns from ClimateData query:
            date, temperature, rainfall, ndvi, soil_moisture, enso, iod,
            humidity, rel_humidity, dewpoint, wind_u, wind_v, wind_speed,
            wind_direction, pressure, solar, location_name, month
    
    Returns:
        DataFrame with a single row containing all 88 features,
        or None if insufficient data.
    """
    if len(climate_records) < 6:
        return None
    
    expected_features = get_expected_features()
    
    # Step 1: Ensure data is sorted by date
    df = climate_records.sort_values('date').reset_index(drop=True)
    
    # Extract month from date if not present
    if 'month' not in df.columns:
        df['month'] = pd.to_datetime(df['date']).dt.month
    
    # Step 2: Build base features
    df = build_base_features(df)
    
    # Step 3: Recursively resolve all expected features
    def resolve_feature(feat_name):
        if feat_name in df.columns:
            return True
        
        import re
        # Try _lag_X
        lag_match = re.search(r'(.+)_lag_(\d+)$', feat_name)
        if lag_match:
            base, lag_val = lag_match.groups()
            if resolve_feature(base):
                df[feat_name] = df[base].shift(int(lag_val))
                return True
                
        # Try _rolling_mean_X
        mean_match = re.search(r'(.+)_rolling_mean_(\d+)$', feat_name)
        if mean_match:
            base, window_val = mean_match.groups()
            if resolve_feature(base):
                df[feat_name] = df[base].rolling(int(window_val), min_periods=1).mean()
                return True
                
        # Try _rolling_std_X
        std_match = re.search(r'(.+)_rolling_std_(\d+)$', feat_name)
        if std_match:
            base, window_val = std_match.groups()
            if resolve_feature(base):
                df[feat_name] = df[base].rolling(int(window_val), min_periods=1).std().fillna(0)
                return True
                
        return False
        
    for feat in expected_features:
        resolve_feature(feat)
        
    # Step 4: Take the LAST row (most recent data point = prediction input)
    latest = df.iloc[[-1]].copy()
    
    # Step 5: Select and order features to match schema
    feature_row = pd.DataFrame()
    for feat in expected_features:
        if feat in latest.columns:
            feature_row[feat] = latest[feat].values
        else:
            # Feature not computed / missing base — use 0.0 as fallback
            feature_row[feat] = [0.0]
    
    # Step 7: Fill any NaN values with column median or 0
    feature_row = feature_row.fillna(0.0)
    
    return feature_row
