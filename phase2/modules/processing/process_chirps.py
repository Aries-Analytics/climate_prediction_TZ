"""
CHIRPS Rainfall Data Processing - Phase 3

Processes CHIRPS rainfall data with drought and flood indicators for insurance triggers.

Features created:
- Drought indicators: consecutive dry days, SPI, rainfall deficit
- Flood indicators: heavy rain events, cumulative excess rainfall
- Rolling statistics: 7-day, 14-day, 30-day, 90-day rainfall
- Anomalies: deviation from climatological normal
- Insurance triggers: drought and flood risk scores
"""

import numpy as np
import pandas as pd
from scipy import stats

from utils.config import get_output_path
from utils.logger import log_error, log_info
from utils.validator import validate_dataframe


def process(data):
    """
    Process CHIRPS rainfall data with comprehensive drought and flood indicators.
    
    Parameters
    ----------
    data : pd.DataFrame
        Raw CHIRPS data with columns: year, month, rainfall_mm, lat_min, lat_max, lon_min, lon_max
    
    Returns
    -------
    pd.DataFrame
        Processed data with drought/flood indicators and insurance trigger features
    
    Features Added
    --------------
    - Rolling rainfall sums (7, 14, 30, 90 days)
    - Consecutive dry days
    - Standardized Precipitation Index (SPI)
    - Rainfall anomaly and percentile
    - Drought severity index
    - Flood risk indicators
    - Heavy rainfall event flags
    - Insurance trigger scores
    """
    log_info("[PROCESS] Processing CHIRPS rainfall data with drought/flood indicators...")
    
    if data is None or data.empty:
        log_error("Input data is empty")
        raise ValueError("Cannot process empty CHIRPS data")
    
    df = data.copy()
    
    # Ensure required columns exist
    required_cols = ['year', 'month', 'rainfall_mm']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        log_error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing columns: {missing_cols}")
    
    # Sort by date for time-series calculations
    df = df.sort_values(['year', 'month']).reset_index(drop=True)
    
    # Create date column for easier manipulation
    df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
    
    # 1. ROLLING RAINFALL STATISTICS
    log_info("Calculating rolling rainfall statistics...")
    df = _add_rolling_rainfall(df)
    
    # 2. RAINFALL ANOMALIES (must come before drought indicators)
    log_info("Calculating rainfall anomalies...")
    df = _add_rainfall_anomalies(df)
    
    # 3. DROUGHT INDICATORS
    log_info("Calculating drought indicators...")
    df = _add_drought_indicators(df)
    
    # 4. FLOOD INDICATORS
    log_info("Calculating flood indicators...")
    df = _add_flood_indicators(df)
    
    # 5. INSURANCE TRIGGER SCORES
    log_info("Calculating insurance trigger scores...")
    df = _add_insurance_triggers(df)
    
    # 6. QUALITY CHECKS
    df = _apply_quality_filters(df)
    
    # Drop temporary date column
    df = df.drop(columns=['date'])
    
    # Validate output
    expected_cols = ['year', 'month', 'rainfall_mm', 'drought_severity', 'flood_risk_score']
    validate_dataframe(df, expected_columns=expected_cols, dataset_name="CHIRPS Processed")
    
    # Save processed data
    output_path = get_output_path("processed", "chirps_processed.csv")
    df.to_csv(output_path, index=False)
    log_info(f"Processed CHIRPS data saved to: {output_path}")
    log_info(f"[PROCESS] CHIRPS processing complete. Output shape: {df.shape}")
    
    return df


def _add_rolling_rainfall(df):
    """
    Add rolling rainfall sums for various time windows.
    
    Critical for drought and flood detection.
    """
    # 7-day rolling (weekly)
    df['rainfall_7day'] = df['rainfall_mm'].rolling(window=7, min_periods=1).sum()
    
    # 14-day rolling (bi-weekly)
    df['rainfall_14day'] = df['rainfall_mm'].rolling(window=14, min_periods=1).sum()
    
    # 30-day rolling (monthly)
    df['rainfall_30day'] = df['rainfall_mm'].rolling(window=30, min_periods=1).sum()
    
    # 90-day rolling (seasonal)
    df['rainfall_90day'] = df['rainfall_mm'].rolling(window=90, min_periods=1).sum()
    
    # 180-day rolling (half-year)
    df['rainfall_180day'] = df['rainfall_mm'].rolling(window=180, min_periods=1).sum()
    
    return df


def _add_drought_indicators(df):
    """
    Add comprehensive drought indicators for insurance triggers.
    
    Indicators:
    - Consecutive dry days
    - Standardized Precipitation Index (SPI)
    - Rainfall deficit
    - Drought severity classification
    """
    # Consecutive dry days (threshold: <1mm is considered dry)
    df['is_dry_day'] = (df['rainfall_mm'] < 1.0).astype(int)
    df['consecutive_dry_days'] = df.groupby(
        (df['is_dry_day'] != df['is_dry_day'].shift()).cumsum()
    )['is_dry_day'].cumsum() * df['is_dry_day']
    
    # Standardized Precipitation Index (SPI) - 30-day
    df['spi_30day'] = _calculate_spi(df['rainfall_30day'])
    
    # Standardized Precipitation Index (SPI) - 90-day
    df['spi_90day'] = _calculate_spi(df['rainfall_90day'])
    
    # Rainfall deficit (compared to long-term mean)
    long_term_mean = df.groupby('month')['rainfall_mm'].transform('mean')
    df['rainfall_deficit_mm'] = long_term_mean - df['rainfall_mm']
    df['rainfall_deficit_pct'] = (df['rainfall_deficit_mm'] / long_term_mean * 100).fillna(0)
    
    # Drought severity classification
    df['drought_severity'] = _classify_drought_severity(df)
    
    # Drought duration (consecutive months with SPI < -1)
    df['is_drought_month'] = (df['spi_30day'] < -1.0).astype(int)
    df['drought_duration_months'] = df.groupby(
        (df['is_drought_month'] != df['is_drought_month'].shift()).cumsum()
    )['is_drought_month'].cumsum() * df['is_drought_month']
    
    return df


def _add_flood_indicators(df):
    """
    Add flood risk indicators for insurance triggers.
    
    Indicators:
    - Heavy rainfall events
    - Extreme rainfall events
    - Cumulative excess rainfall
    - Flood risk score
    """
    # Heavy rainfall event (>50mm in a day)
    df['heavy_rain_event'] = (df['rainfall_mm'] > 50).astype(int)
    
    # Extreme rainfall event (>100mm in a day)
    df['extreme_rain_event'] = (df['rainfall_mm'] > 100).astype(int)
    
    # Very extreme rainfall event (>150mm in a day)
    df['very_extreme_rain_event'] = (df['rainfall_mm'] > 150).astype(int)
    
    # Cumulative heavy rain days in past 7 days
    df['heavy_rain_days_7day'] = df['heavy_rain_event'].rolling(window=7, min_periods=1).sum()
    
    # Cumulative heavy rain days in past 30 days
    df['heavy_rain_days_30day'] = df['heavy_rain_event'].rolling(window=30, min_periods=1).sum()
    
    # Excess rainfall (above 95th percentile)
    rainfall_95th = df['rainfall_mm'].quantile(0.95)
    df['excess_rainfall_mm'] = np.maximum(0, df['rainfall_mm'] - rainfall_95th)
    
    # Cumulative excess rainfall (7-day)
    df['cumulative_excess_7day'] = df['excess_rainfall_mm'].rolling(window=7, min_periods=1).sum()
    
    # Flood risk score (0-100)
    df['flood_risk_score'] = _calculate_flood_risk_score(df)
    
    return df


def _add_rainfall_anomalies(df):
    """
    Add rainfall anomaly indicators.
    
    Compares current rainfall to climatological normal.
    """
    # Calculate climatological mean and std by month
    monthly_stats = df.groupby('month')['rainfall_mm'].agg(['mean', 'std']).reset_index()
    monthly_stats.columns = ['month', 'rainfall_clim_mean', 'rainfall_clim_std']
    
    # Merge with main dataframe
    df = df.merge(monthly_stats, on='month', how='left')
    
    # Calculate anomaly
    df['rainfall_anomaly_mm'] = df['rainfall_mm'] - df['rainfall_clim_mean']
    df['rainfall_anomaly_pct'] = (df['rainfall_anomaly_mm'] / df['rainfall_clim_mean'] * 100).fillna(0)
    
    # Calculate standardized anomaly
    df['rainfall_anomaly_std'] = (df['rainfall_anomaly_mm'] / df['rainfall_clim_std']).fillna(0)
    
    # Calculate percentile rank
    df['rainfall_percentile'] = df.groupby('month')['rainfall_mm'].rank(pct=True) * 100
    
    return df


def _add_insurance_triggers(df):
    """
    Add insurance trigger indicators.
    
    These are the key features for parametric insurance payouts.
    """
    # DROUGHT TRIGGER
    # Trigger if: 21+ consecutive dry days OR 30-day rainfall < 25mm OR SPI < -1.5
    df['drought_trigger'] = (
        (df['consecutive_dry_days'] >= 21) |
        (df['rainfall_30day'] < 25) |
        (df['spi_30day'] < -1.5)
    ).astype(int)
    
    # Drought trigger confidence (0-1)
    drought_signals = [
        (df['consecutive_dry_days'] >= 21).astype(float),
        (df['rainfall_30day'] < 25).astype(float),
        (df['spi_30day'] < -1.5).astype(float),
        (df['rainfall_percentile'] < 10).astype(float)
    ]
    df['drought_trigger_confidence'] = np.mean(drought_signals, axis=0)
    
    # FLOOD TRIGGER
    # Trigger if: >150mm in 7 days OR >100mm in 1 day OR 3+ heavy rain days in 7 days
    df['flood_trigger'] = (
        (df['rainfall_7day'] > 150) |
        (df['rainfall_mm'] > 100) |
        (df['heavy_rain_days_7day'] >= 3)
    ).astype(int)
    
    # Flood trigger confidence (0-1)
    flood_signals = [
        (df['rainfall_7day'] > 150).astype(float),
        (df['rainfall_mm'] > 100).astype(float),
        (df['heavy_rain_days_7day'] >= 3).astype(float),
        (df['rainfall_percentile'] > 95).astype(float)
    ]
    df['flood_trigger_confidence'] = np.mean(flood_signals, axis=0)
    
    # COMBINED TRIGGER
    df['any_trigger'] = (df['drought_trigger'] | df['flood_trigger']).astype(int)
    
    # Trigger severity (for payout calculation)
    df['trigger_severity'] = np.maximum(
        df['drought_severity'],
        df['flood_risk_score'] / 100  # Normalize to 0-1
    )
    
    return df


def _calculate_spi(rainfall_series, distribution='gamma'):
    """
    Calculate Standardized Precipitation Index (SPI).
    
    SPI is a widely used drought indicator that normalizes rainfall
    to a standard normal distribution.
    
    Parameters
    ----------
    rainfall_series : pd.Series
        Rainfall data (e.g., 30-day or 90-day totals)
    distribution : str
        Distribution to fit ('gamma' or 'normal')
    
    Returns
    -------
    pd.Series
        SPI values (mean=0, std=1)
    
    Interpretation:
    - SPI > 2.0: Extremely wet
    - SPI 1.5 to 2.0: Very wet
    - SPI 1.0 to 1.5: Moderately wet
    - SPI -1.0 to 1.0: Near normal
    - SPI -1.5 to -1.0: Moderately dry
    - SPI -2.0 to -1.5: Severely dry
    - SPI < -2.0: Extremely dry
    """
    # Remove NaN values for fitting
    valid_data = rainfall_series.dropna()
    
    if len(valid_data) < 30:
        # Not enough data for reliable SPI
        return pd.Series(0, index=rainfall_series.index)
    
    try:
        if distribution == 'gamma':
            # Fit gamma distribution (common for rainfall)
            # Add small constant to avoid zero values
            data_positive = valid_data + 0.01
            shape, loc, scale = stats.gamma.fit(data_positive, floc=0)
            
            # Calculate cumulative probability
            cdf = stats.gamma.cdf(rainfall_series + 0.01, shape, loc, scale)
        else:
            # Fit normal distribution
            mean, std = valid_data.mean(), valid_data.std()
            cdf = stats.norm.cdf(rainfall_series, mean, std)
        
        # Convert to standard normal (SPI)
        # Clip to avoid infinite values
        cdf = np.clip(cdf, 0.001, 0.999)
        spi = stats.norm.ppf(cdf)
        
        return pd.Series(spi, index=rainfall_series.index)
    
    except Exception as e:
        log_error(f"Error calculating SPI: {e}")
        return pd.Series(0, index=rainfall_series.index)


def _classify_drought_severity(df):
    """
    Classify drought severity based on multiple indicators.
    
    Returns
    -------
    pd.Series
        Drought severity score (0-1)
        0 = No drought
        0.25 = Mild drought
        0.5 = Moderate drought
        0.75 = Severe drought
        1.0 = Extreme drought
    """
    severity = pd.Series(0.0, index=df.index)
    
    # Mild drought: SPI < -1.0 OR 14+ dry days OR rainfall < 50th percentile
    mild_drought = (
        (df['spi_30day'] < -1.0) |
        (df['consecutive_dry_days'] >= 14) |
        (df['rainfall_percentile'] < 50)
    )
    severity[mild_drought] = 0.25
    
    # Moderate drought: SPI < -1.5 OR 21+ dry days OR rainfall < 25th percentile
    moderate_drought = (
        (df['spi_30day'] < -1.5) |
        (df['consecutive_dry_days'] >= 21) |
        (df['rainfall_percentile'] < 25)
    )
    severity[moderate_drought] = 0.5
    
    # Severe drought: SPI < -2.0 OR 30+ dry days OR rainfall < 10th percentile
    severe_drought = (
        (df['spi_30day'] < -2.0) |
        (df['consecutive_dry_days'] >= 30) |
        (df['rainfall_percentile'] < 10)
    )
    severity[severe_drought] = 0.75
    
    # Extreme drought: SPI < -2.5 OR 45+ dry days OR rainfall < 5th percentile
    extreme_drought = (
        (df['spi_30day'] < -2.5) |
        (df['consecutive_dry_days'] >= 45) |
        (df['rainfall_percentile'] < 5)
    )
    severity[extreme_drought] = 1.0
    
    return severity


def _calculate_flood_risk_score(df):
    """
    Calculate flood risk score (0-100).
    
    Combines multiple flood indicators into a single risk score.
    """
    score = pd.Series(0.0, index=df.index)
    
    # Component 1: Daily rainfall intensity (0-40 points)
    score += np.minimum(40, df['rainfall_mm'] / 2.5)  # 100mm = 40 points
    
    # Component 2: 7-day cumulative (0-30 points)
    score += np.minimum(30, df['rainfall_7day'] / 5)  # 150mm = 30 points
    
    # Component 3: Heavy rain frequency (0-20 points)
    score += np.minimum(20, df['heavy_rain_days_7day'] * 5)  # 4 days = 20 points
    
    # Component 4: Excess rainfall (0-10 points)
    score += np.minimum(10, df['cumulative_excess_7day'] / 5)  # 50mm excess = 10 points
    
    # Clip to 0-100 range
    score = np.clip(score, 0, 100)
    
    return score


def _apply_quality_filters(df):
    """
    Apply quality filters to remove invalid data.
    """
    initial_count = len(df)
    
    # Remove negative rainfall (data error)
    df = df[df['rainfall_mm'] >= 0]
    
    # Remove unrealistic extreme values (>500mm/day is extremely rare)
    df = df[df['rainfall_mm'] <= 500]
    
    # Log if significant data was removed
    removed_count = initial_count - len(df)
    if removed_count > 0:
        log_info(f"Quality filter removed {removed_count} invalid records ({removed_count/initial_count*100:.1f}%)")
    
    return df
