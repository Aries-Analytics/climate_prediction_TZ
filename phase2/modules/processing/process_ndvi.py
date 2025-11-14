"""
NDVI Vegetation Index Data Processing - Phase 3

Processes NDVI data with comprehensive vegetation health indicators and crop insurance triggers.

Features created:
- Vegetation health indicators: NDVI anomalies, trends, stress levels
- Temporal analysis: rolling means, seasonal patterns, growth stage detection
- Drought stress indicators: vegetation condition index, stress duration
- Crop failure risk: insurance trigger thresholds based on NDVI decline
- Recovery indicators: vegetation resilience and bounce-back metrics
"""

import numpy as np
import pandas as pd
from scipy import stats

from utils.config import get_output_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe


def process(data):
    """
    Process NDVI vegetation index data with comprehensive health and insurance indicators.
    
    Parameters
    ----------
    data : pd.DataFrame
        Raw NDVI data with columns: year, month, ndvi, lat_min, lat_max, lon_min, lon_max
    
    Returns
    -------
    pd.DataFrame
        Processed data with vegetation health and crop insurance trigger features
    
    Features Added
    --------------
    - NDVI anomalies and percentiles
    - Rolling NDVI statistics (30, 60, 90 days)
    - Vegetation Condition Index (VCI)
    - Drought stress indicators and duration
    - Crop failure risk score
    - Growth stage indicators
    - Recovery and resilience metrics
    - Insurance trigger flags
    """
    log_info("[PROCESS] Processing NDVI data with vegetation health and insurance indicators...")
    
    if data is None or data.empty:
        log_error("Input data is empty")
        raise ValueError("Cannot process empty NDVI data")
    
    df = data.copy()
    
    # Ensure required columns exist
    required_cols = ['year', 'month', 'ndvi']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        log_error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing columns: {missing_cols}")
    
    # Sort by date for time-series calculations
    df = df.sort_values(['year', 'month']).reset_index(drop=True)
    
    # Create date column for easier manipulation
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    
    # 1. NDVI TEMPORAL STATISTICS
    log_info("Calculating NDVI temporal statistics...")
    df = _add_ndvi_temporal_stats(df)
    
    # 2. NDVI ANOMALIES AND PERCENTILES
    log_info("Calculating NDVI anomalies...")
    df = _add_ndvi_anomalies(df)
    
    # 3. VEGETATION CONDITION INDEX (VCI)
    log_info("Calculating Vegetation Condition Index...")
    df = _add_vegetation_condition_index(df)
    
    # 4. DROUGHT STRESS INDICATORS
    log_info("Calculating drought stress indicators...")
    df = _add_drought_stress_indicators(df)
    
    # 5. CROP GROWTH STAGE INDICATORS
    log_info("Detecting crop growth stages...")
    df = _add_growth_stage_indicators(df)
    
    # 6. CROP FAILURE RISK
    log_info("Calculating crop failure risk...")
    df = _add_crop_failure_risk(df)
    
    # 7. INSURANCE TRIGGERS
    log_info("Calculating insurance triggers...")
    df = _add_insurance_triggers(df)
    
    # 8. QUALITY CHECKS
    df = _apply_quality_filters(df)
    
    # Drop temporary date column
    df = df.drop(columns=['date'])
    
    # Validate output
    expected_cols = ['year', 'month', 'ndvi', 'vci', 'crop_failure_risk']
    validate_dataframe(df, expected_columns=expected_cols, dataset_name="NDVI Processed")
    
    # Save processed data
    output_path = get_output_path("processed", "ndvi_processed.csv")
    df.to_csv(output_path, index=False)
    log_info(f"Processed NDVI data saved to: {output_path}")
    log_info(f"[PROCESS] NDVI processing complete. Output shape: {df.shape}")
    
    return df


def _add_ndvi_temporal_stats(df):
    """
    Add rolling NDVI statistics for temporal analysis.
    
    These help identify trends and sustained vegetation stress.
    """
    # 30-day rolling mean (monthly average)
    df['ndvi_30day_mean'] = df['ndvi'].rolling(window=30, min_periods=1).mean()
    
    # 60-day rolling mean (bi-monthly)
    df['ndvi_60day_mean'] = df['ndvi'].rolling(window=60, min_periods=1).mean()
    
    # 90-day rolling mean (seasonal)
    df['ndvi_90day_mean'] = df['ndvi'].rolling(window=90, min_periods=1).mean()
    
    # NDVI trend (30-day slope)
    df['ndvi_trend_30day'] = df['ndvi'].rolling(window=30, min_periods=10).apply(
        lambda x: _calculate_trend(x), raw=True
    )
    
    # NDVI volatility (30-day standard deviation)
    df['ndvi_volatility_30day'] = df['ndvi'].rolling(window=30, min_periods=1).std()
    
    # Month-to-month change
    df['ndvi_change_mom'] = df['ndvi'].diff()
    
    # Year-over-year change (same month, previous year)
    df['ndvi_change_yoy'] = df.groupby('month')['ndvi'].diff(12)
    
    return df


def _add_ndvi_anomalies(df):
    """
    Add NDVI anomaly indicators.
    
    Compares current NDVI to climatological normal.
    """
    # Calculate climatological mean and std by month
    monthly_stats = df.groupby('month')['ndvi'].agg(['mean', 'std', 'min', 'max']).reset_index()
    monthly_stats.columns = ['month', 'ndvi_clim_mean', 'ndvi_clim_std', 'ndvi_clim_min', 'ndvi_clim_max']
    
    # Merge with main dataframe
    df = df.merge(monthly_stats, on='month', how='left')
    
    # Calculate anomaly
    df['ndvi_anomaly'] = df['ndvi'] - df['ndvi_clim_mean']
    df['ndvi_anomaly_pct'] = (df['ndvi_anomaly'] / df['ndvi_clim_mean'] * 100).fillna(0)
    
    # Calculate standardized anomaly (z-score)
    df['ndvi_anomaly_std'] = (df['ndvi_anomaly'] / df['ndvi_clim_std']).fillna(0)
    
    # Calculate percentile rank
    df['ndvi_percentile'] = df.groupby('month')['ndvi'].rank(pct=True) * 100
    
    # Deviation from maximum (how far below peak greenness)
    df['ndvi_deficit_from_max'] = df['ndvi_clim_max'] - df['ndvi']
    df['ndvi_deficit_pct'] = (df['ndvi_deficit_from_max'] / df['ndvi_clim_max'] * 100).fillna(0)
    
    return df


def _add_vegetation_condition_index(df):
    """
    Calculate Vegetation Condition Index (VCI).
    
    VCI is a normalized measure of vegetation health:
    VCI = 100 * (NDVI - NDVI_min) / (NDVI_max - NDVI_min)
    
    Interpretation:
    - VCI > 50: Normal to good vegetation condition
    - VCI 35-50: Moderate vegetation stress
    - VCI 20-35: Severe vegetation stress
    - VCI < 20: Extreme vegetation stress (crop failure likely)
    """
    # Calculate VCI using climatological min/max
    ndvi_range = df['ndvi_clim_max'] - df['ndvi_clim_min']
    ndvi_range = ndvi_range.replace(0, np.nan)  # Avoid division by zero
    
    df['vci'] = 100 * (df['ndvi'] - df['ndvi_clim_min']) / ndvi_range
    df['vci'] = df['vci'].clip(0, 100).fillna(50)  # Clip to 0-100, default to 50 if missing
    
    # VCI classification
    df['vci_class'] = pd.cut(
        df['vci'],
        bins=[0, 20, 35, 50, 100],
        labels=['extreme_stress', 'severe_stress', 'moderate_stress', 'normal']
    )
    
    # Rolling VCI (30-day mean)
    df['vci_30day_mean'] = df['vci'].rolling(window=30, min_periods=1).mean()
    
    return df


def _add_drought_stress_indicators(df):
    """
    Add comprehensive drought stress indicators for vegetation.
    
    These indicators help identify crop stress and potential failure.
    """
    # Vegetation vigor score (0-100, based on NDVI)
    df['vegetation_vigor'] = (df['ndvi'] * 100).clip(0, 100)
    
    # Stress indicator (NDVI below threshold or large negative anomaly)
    df['is_stressed'] = (
        (df['ndvi'] < 0.3) |
        (df['ndvi_anomaly_std'] < -1.0) |
        (df['vci'] < 35)
    ).astype(int)
    
    # Stress duration (consecutive stressed periods)
    df['stress_duration'] = df.groupby(
        (df['is_stressed'] != df['is_stressed'].shift()).cumsum()
    )['is_stressed'].cumsum() * df['is_stressed']
    
    # Severe stress indicator (multiple criteria)
    df['is_severe_stress'] = (
        (df['ndvi'] < 0.2) |
        (df['ndvi_anomaly_std'] < -1.5) |
        (df['vci'] < 20)
    ).astype(int)
    
    # Severe stress duration
    df['severe_stress_duration'] = df.groupby(
        (df['is_severe_stress'] != df['is_severe_stress'].shift()).cumsum()
    )['is_severe_stress'].cumsum() * df['is_severe_stress']
    
    # Drought stress severity (0-1 scale)
    df['drought_stress_severity'] = _calculate_stress_severity(df)
    
    # Recovery indicator (NDVI increasing after stress)
    df['is_recovering'] = (
        (df['is_stressed'] == 0) &
        (df['is_stressed'].shift(1) == 1) &
        (df['ndvi_trend_30day'] > 0)
    ).astype(int)
    
    return df


def _add_growth_stage_indicators(df):
    """
    Add crop growth stage indicators based on NDVI patterns.
    
    Helps identify critical growth periods for insurance assessment.
    """
    # Peak greenness indicator (NDVI near seasonal maximum)
    df['is_peak_greenness'] = (df['ndvi'] >= df['ndvi_clim_mean'] * 0.9).astype(int)
    
    # Growing season indicator (NDVI increasing)
    df['is_growing_season'] = (df['ndvi_trend_30day'] > 0).astype(int)
    
    # Senescence indicator (NDVI decreasing from peak)
    df['is_senescence'] = (
        (df['ndvi_trend_30day'] < 0) &
        (df['ndvi'] < df['ndvi_clim_mean'])
    ).astype(int)
    
    # Critical growth period (high NDVI with positive trend)
    df['is_critical_period'] = (
        (df['ndvi'] > 0.4) &
        (df['ndvi_trend_30day'] > 0) &
        (df['vci'] > 35)
    ).astype(int)
    
    return df


def _add_crop_failure_risk(df):
    """
    Calculate crop failure risk score (0-100).
    
    Combines multiple vegetation stress indicators into a single risk score.
    """
    score = pd.Series(0.0, index=df.index)
    
    # Component 1: VCI-based risk (0-40 points)
    # VCI < 20 = 40 points, VCI > 50 = 0 points
    score += np.maximum(0, 40 - df['vci'] * 0.8)
    
    # Component 2: NDVI anomaly risk (0-25 points)
    # Standardized anomaly < -2 = 25 points
    score += np.maximum(0, np.minimum(25, -df['ndvi_anomaly_std'] * 12.5))
    
    # Component 3: Stress duration risk (0-20 points)
    # 60+ days of stress = 20 points
    score += np.minimum(20, df['stress_duration'] / 3)
    
    # Component 4: Trend risk (0-15 points)
    # Negative trend = up to 15 points
    score += np.maximum(0, np.minimum(15, -df['ndvi_trend_30day'] * 150))
    
    # Clip to 0-100 range
    df['crop_failure_risk'] = np.clip(score, 0, 100)
    
    # Crop failure risk classification
    df['crop_failure_risk_class'] = pd.cut(
        df['crop_failure_risk'],
        bins=[0, 25, 50, 75, 100],
        labels=['low', 'moderate', 'high', 'extreme']
    )
    
    return df


def _add_insurance_triggers(df):
    """
    Add insurance trigger indicators for crop insurance.
    
    These are the key features for parametric crop insurance payouts.
    """
    # CROP FAILURE TRIGGER
    # Trigger if: VCI < 20 for 30+ days OR NDVI < 0.2 for 30+ days OR crop failure risk > 75
    df['crop_failure_trigger'] = (
        (df['vci'] < 20) & (df['stress_duration'] >= 30) |
        (df['ndvi'] < 0.2) & (df['stress_duration'] >= 30) |
        (df['crop_failure_risk'] > 75)
    ).astype(int)
    
    # Crop failure trigger confidence (0-1)
    failure_signals = [
        ((df['vci'] < 20) & (df['stress_duration'] >= 30)).astype(float),
        ((df['ndvi'] < 0.2) & (df['stress_duration'] >= 30)).astype(float),
        (df['crop_failure_risk'] > 75).astype(float),
        (df['ndvi_percentile'] < 10).astype(float)
    ]
    df['crop_failure_trigger_confidence'] = np.mean(failure_signals, axis=0)
    
    # MODERATE STRESS TRIGGER (early warning)
    # Trigger if: VCI < 35 for 21+ days OR NDVI anomaly < -1.5 std
    df['moderate_stress_trigger'] = (
        ((df['vci'] < 35) & (df['stress_duration'] >= 21)) |
        (df['ndvi_anomaly_std'] < -1.5)
    ).astype(int)
    
    # SEVERE STRESS TRIGGER
    # Trigger if: VCI < 20 OR severe stress for 14+ days
    df['severe_stress_trigger'] = (
        (df['vci'] < 20) |
        (df['severe_stress_duration'] >= 14)
    ).astype(int)
    
    # Trigger severity (for payout calculation, 0-1 scale)
    df['trigger_severity'] = df['crop_failure_risk'] / 100
    
    # Days since last trigger (for tracking recovery)
    df['days_since_trigger'] = _calculate_days_since_trigger(df['crop_failure_trigger'])
    
    return df


def _calculate_trend(values):
    """
    Calculate linear trend (slope) for a time series.
    
    Returns slope of linear regression.
    """
    if len(values) < 2:
        return 0
    
    x = np.arange(len(values))
    try:
        slope, _ = np.polyfit(x, values, 1)
        return slope
    except:
        return 0


def _calculate_stress_severity(df):
    """
    Calculate drought stress severity (0-1 scale).
    
    Combines multiple stress indicators.
    """
    severity = pd.Series(0.0, index=df.index)
    
    # Mild stress: VCI < 50 OR NDVI < 0.4
    mild_stress = (df['vci'] < 50) | (df['ndvi'] < 0.4)
    severity[mild_stress] = 0.25
    
    # Moderate stress: VCI < 35 OR NDVI < 0.3
    moderate_stress = (df['vci'] < 35) | (df['ndvi'] < 0.3)
    severity[moderate_stress] = 0.5
    
    # Severe stress: VCI < 20 OR NDVI < 0.2
    severe_stress = (df['vci'] < 20) | (df['ndvi'] < 0.2)
    severity[severe_stress] = 0.75
    
    # Extreme stress: VCI < 10 OR NDVI < 0.15
    extreme_stress = (df['vci'] < 10) | (df['ndvi'] < 0.15)
    severity[extreme_stress] = 1.0
    
    return severity


def _calculate_days_since_trigger(trigger_series):
    """
    Calculate days since last trigger event.
    """
    days_since = pd.Series(0, index=trigger_series.index)
    last_trigger_idx = -1
    
    for i in range(len(trigger_series)):
        if trigger_series.iloc[i] == 1:
            last_trigger_idx = i
            days_since.iloc[i] = 0
        elif last_trigger_idx >= 0:
            days_since.iloc[i] = i - last_trigger_idx
        else:
            days_since.iloc[i] = -1  # No trigger yet
    
    return days_since


def _apply_quality_filters(df):
    """
    Apply quality filters to remove invalid data.
    """
    initial_count = len(df)
    
    # Remove invalid NDVI values (must be between -1 and 1)
    df = df[(df['ndvi'] >= -1) & (df['ndvi'] <= 1)]
    
    # Remove unrealistic values (NDVI < -0.5 is very rare for land)
    df = df[df['ndvi'] >= -0.5]
    
    # Log if significant data was removed
    removed_count = initial_count - len(df)
    if removed_count > 0:
        log_info(f"Quality filter removed {removed_count} invalid records ({removed_count/initial_count*100:.1f}%)")
    
    return df
