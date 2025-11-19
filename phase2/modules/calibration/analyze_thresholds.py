"""
Threshold Analysis Module for Insurance Trigger Calibration

This module provides statistical analysis functions to determine appropriate
trigger thresholds based on historical climate data.

Functions:
- analyze_rainfall_distribution: Analyze rainfall patterns for flood triggers
- analyze_drought_indicators: Analyze drought patterns for drought triggers
- analyze_vegetation_stress: Analyze vegetation patterns for crop failure triggers
- generate_threshold_report: Generate comprehensive threshold analysis report
"""

import json
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from pathlib import Path

from utils.logger import log_info, log_error, log_warning


def analyze_rainfall_distribution(df: pd.DataFrame) -> Dict[str, float]:
    """
    Analyze rainfall distribution to determine flood trigger thresholds.

    Calculates percentiles and statistical summaries for daily, 7-day, and 30-day
    rainfall to inform flood trigger calibration. Identifies outliers that may
    indicate data quality issues.

    Parameters
    ----------
    df : pd.DataFrame
        Processed CHIRPS data with columns:
        - rainfall_mm: Daily rainfall
        - rainfall_7day: 7-day rolling rainfall
        - rainfall_30day: 30-day rolling rainfall

    Returns
    -------
    Dict[str, float]
        Dictionary containing:
        - Percentiles (90th, 95th, 97th, 99th) for each rainfall metric
        - Statistical summary (mean, median, std dev) for each metric
        - Outlier information (count, threshold, flagged values)
        - Data quality metrics

    Raises
    ------
    ValueError
        If required columns are missing from the dataframe

    Examples
    --------
    >>> df = pd.read_csv('data/processed/chirps_processed.csv')
    >>> results = analyze_rainfall_distribution(df)
    >>> print(f"99th percentile daily rainfall: {results['daily_rainfall_p99']:.1f}mm")
    """
    log_info("Analyzing rainfall distribution for flood trigger calibration...")

    # Validate required columns
    required_cols = ["rainfall_mm", "rainfall_7day", "rainfall_30day"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required columns: {missing_cols}"
        log_error(error_msg)
        raise ValueError(error_msg)

    # Remove NaN values for analysis
    df_clean = df[required_cols].dropna()

    if len(df_clean) == 0:
        error_msg = "No valid data available for analysis after removing NaN values"
        log_error(error_msg)
        raise ValueError(error_msg)

    log_info(f"Analyzing {len(df_clean)} valid rainfall records...")

    results = {}

    # Analyze each rainfall metric
    metrics = {"daily_rainfall": "rainfall_mm", "rainfall_7day": "rainfall_7day", "rainfall_30day": "rainfall_30day"}

    for metric_name, column_name in metrics.items():
        log_info(f"Analyzing {metric_name}...")

        data = df_clean[column_name]

        # Calculate percentiles
        percentiles = [90, 95, 97, 99]
        for p in percentiles:
            percentile_value = np.percentile(data, p)
            key = f"{metric_name}_p{p}"
            results[key] = float(percentile_value)
            log_info(f"  {p}th percentile: {percentile_value:.2f}mm")

        # Calculate statistical summary
        results[f"{metric_name}_mean"] = float(data.mean())
        results[f"{metric_name}_median"] = float(data.median())
        results[f"{metric_name}_std"] = float(data.std())
        results[f"{metric_name}_min"] = float(data.min())
        results[f"{metric_name}_max"] = float(data.max())
        results[f"{metric_name}_count"] = int(len(data))

        log_info(f"  Mean: {results[f'{metric_name}_mean']:.2f}mm")
        log_info(f"  Median: {results[f'{metric_name}_median']:.2f}mm")
        log_info(f"  Std Dev: {results[f'{metric_name}_std']:.2f}mm")

        # Identify outliers (beyond 5 standard deviations)
        mean = results[f"{metric_name}_mean"]
        std = results[f"{metric_name}_std"]
        outlier_threshold = mean + (5 * std)

        outliers = data[data > outlier_threshold]
        results[f"{metric_name}_outlier_count"] = int(len(outliers))
        results[f"{metric_name}_outlier_threshold"] = float(outlier_threshold)

        if len(outliers) > 0:
            results[f"{metric_name}_outlier_max"] = float(outliers.max())
            results[f"{metric_name}_outlier_values"] = outliers.tolist()
            log_warning(
                f"  Found {len(outliers)} outliers beyond 5 std dev "
                f"(>{outlier_threshold:.2f}mm). Max outlier: {outliers.max():.2f}mm"
            )
        else:
            results[f"{metric_name}_outlier_max"] = None
            results[f"{metric_name}_outlier_values"] = []
            log_info(f"  No outliers detected beyond 5 std dev threshold")

    # Calculate additional flood-relevant metrics
    log_info("Calculating flood-relevant metrics...")

    # Heavy rain day threshold (95th percentile of daily rainfall)
    heavy_rain_threshold = results["daily_rainfall_p95"]
    results["heavy_rain_day_threshold"] = heavy_rain_threshold

    # Count heavy rain days
    heavy_rain_days = (df_clean["rainfall_mm"] > heavy_rain_threshold).sum()
    results["heavy_rain_days_count"] = int(heavy_rain_days)
    results["heavy_rain_days_pct"] = float(heavy_rain_days / len(df_clean) * 100)

    log_info(f"  Heavy rain day threshold (95th percentile): {heavy_rain_threshold:.2f}mm")
    log_info(f"  Heavy rain days: {heavy_rain_days} ({results['heavy_rain_days_pct']:.1f}%)")

    # Extreme rain events (>100mm, >150mm, >200mm)
    extreme_thresholds = [100, 150, 200]
    for threshold in extreme_thresholds:
        count = (df_clean["rainfall_mm"] > threshold).sum()
        pct = count / len(df_clean) * 100
        results[f"extreme_rain_{threshold}mm_count"] = int(count)
        results[f"extreme_rain_{threshold}mm_pct"] = float(pct)
        log_info(f"  Days with >{threshold}mm: {count} ({pct:.2f}%)")

    # Data quality summary
    total_records = len(df)
    valid_records = len(df_clean)
    missing_records = total_records - valid_records

    results["total_records"] = int(total_records)
    results["valid_records"] = int(valid_records)
    results["missing_records"] = int(missing_records)
    results["data_completeness_pct"] = float(valid_records / total_records * 100)

    log_info(
        f"Data quality: {valid_records}/{total_records} valid records "
        f"({results['data_completeness_pct']:.1f}% complete)"
    )

    # Add metadata
    results["analysis_date"] = pd.Timestamp.now().isoformat()
    results["data_period_start"] = str(df["year"].min()) if "year" in df.columns else "unknown"
    results["data_period_end"] = str(df["year"].max()) if "year" in df.columns else "unknown"

    log_info("Rainfall distribution analysis complete!")

    return results


def analyze_drought_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """
    Analyze drought indicators to determine drought trigger thresholds.

    Calculates SPI distribution, consecutive dry days by season, and rainfall
    deficit statistics to inform drought trigger calibration.

    Parameters
    ----------
    df : pd.DataFrame
        Processed CHIRPS data with drought indicators including:
        - spi_30day: 30-day Standardized Precipitation Index
        - spi_90day: 90-day Standardized Precipitation Index
        - consecutive_dry_days: Number of consecutive days with <1mm rainfall
        - rainfall_deficit_mm: Rainfall deficit from climatological mean
        - rainfall_deficit_pct: Rainfall deficit as percentage
        - month: Month number (1-12) for seasonal analysis

    Returns
    -------
    Dict[str, float]
        Dictionary containing:
        - SPI percentiles and distribution statistics
        - Consecutive dry days statistics by season (wet/dry)
        - Rainfall deficit statistics
        - Drought severity thresholds
        - Data quality metrics

    Raises
    ------
    ValueError
        If required columns are missing from the dataframe

    Examples
    --------
    >>> df = pd.read_csv('data/processed/chirps_processed.csv')
    >>> results = analyze_drought_indicators(df)
    >>> print(f"Severe drought SPI threshold: {results['spi_30day_p10']:.2f}")
    """
    log_info("Analyzing drought indicators for drought trigger calibration...")

    # Validate required columns
    required_cols = [
        "spi_30day",
        "spi_90day",
        "consecutive_dry_days",
        "rainfall_deficit_mm",
        "rainfall_deficit_pct",
        "month",
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required columns: {missing_cols}"
        log_error(error_msg)
        raise ValueError(error_msg)

    # Remove NaN values for analysis
    df_clean = df[required_cols].dropna()

    if len(df_clean) == 0:
        error_msg = "No valid data available for analysis after removing NaN values"
        log_error(error_msg)
        raise ValueError(error_msg)

    log_info(f"Analyzing {len(df_clean)} valid drought indicator records...")

    results = {}

    # --- SPI ANALYSIS ---
    log_info("Analyzing SPI distribution...")

    for spi_col in ["spi_30day", "spi_90day"]:
        log_info(f"  Analyzing {spi_col}...")

        data = df_clean[spi_col]

        # Calculate percentiles (lower percentiles indicate drought)
        percentiles = [5, 10, 15, 20, 25]
        for p in percentiles:
            percentile_value = np.percentile(data, p)
            key = f"{spi_col}_p{p}"
            results[key] = float(percentile_value)
            log_info(f"    {p}th percentile: {percentile_value:.2f}")

        # Calculate statistical summary
        results[f"{spi_col}_mean"] = float(data.mean())
        results[f"{spi_col}_median"] = float(data.median())
        results[f"{spi_col}_std"] = float(data.std())
        results[f"{spi_col}_min"] = float(data.min())
        results[f"{spi_col}_max"] = float(data.max())

        log_info(f"    Mean: {results[f'{spi_col}_mean']:.2f}")
        log_info(f"    Median: {results[f'{spi_col}_median']:.2f}")
        log_info(f"    Std Dev: {results[f'{spi_col}_std']:.2f}")

        # Count drought severity levels (based on WMO standards)
        moderate_drought = (data < -1.0).sum()
        severe_drought = (data < -1.5).sum()
        extreme_drought = (data < -2.0).sum()

        results[f"{spi_col}_moderate_drought_count"] = int(moderate_drought)
        results[f"{spi_col}_moderate_drought_pct"] = float(moderate_drought / len(data) * 100)
        results[f"{spi_col}_severe_drought_count"] = int(severe_drought)
        results[f"{spi_col}_severe_drought_pct"] = float(severe_drought / len(data) * 100)
        results[f"{spi_col}_extreme_drought_count"] = int(extreme_drought)
        results[f"{spi_col}_extreme_drought_pct"] = float(extreme_drought / len(data) * 100)

        log_info(
            f"    Moderate drought (SPI < -1.0): {moderate_drought} ({results[f'{spi_col}_moderate_drought_pct']:.1f}%)"
        )
        log_info(f"    Severe drought (SPI < -1.5): {severe_drought} ({results[f'{spi_col}_severe_drought_pct']:.1f}%)")
        log_info(
            f"    Extreme drought (SPI < -2.0): {extreme_drought} ({results[f'{spi_col}_extreme_drought_pct']:.1f}%)"
        )

    # --- CONSECUTIVE DRY DAYS ANALYSIS ---
    log_info("Analyzing consecutive dry days...")

    # Define seasons
    # Wet season: October-May (months 10, 11, 12, 1, 2, 3, 4, 5)
    # Dry season: June-September (months 6, 7, 8, 9)
    df_clean["season"] = df_clean["month"].apply(lambda m: "wet" if m in [10, 11, 12, 1, 2, 3, 4, 5] else "dry")

    for season in ["wet", "dry"]:
        log_info(f"  Analyzing {season} season...")

        season_data = df_clean[df_clean["season"] == season]["consecutive_dry_days"]

        if len(season_data) == 0:
            log_warning(f"    No data available for {season} season")
            continue

        # Calculate percentiles
        percentiles = [50, 75, 90, 95, 99]
        for p in percentiles:
            percentile_value = np.percentile(season_data, p)
            key = f"consecutive_dry_days_{season}_p{p}"
            results[key] = float(percentile_value)
            log_info(f"    {p}th percentile: {percentile_value:.1f} days")

        # Calculate statistical summary
        results[f"consecutive_dry_days_{season}_mean"] = float(season_data.mean())
        results[f"consecutive_dry_days_{season}_median"] = float(season_data.median())
        results[f"consecutive_dry_days_{season}_std"] = float(season_data.std())
        results[f"consecutive_dry_days_{season}_max"] = float(season_data.max())

        log_info(f"    Mean: {results[f'consecutive_dry_days_{season}_mean']:.1f} days")
        log_info(f"    Median: {results[f'consecutive_dry_days_{season}_median']:.1f} days")
        log_info(f"    Max: {results[f'consecutive_dry_days_{season}_max']:.1f} days")

        # Count extended dry periods
        extended_dry_14 = (season_data >= 14).sum()
        extended_dry_21 = (season_data >= 21).sum()
        extended_dry_30 = (season_data >= 30).sum()
        extended_dry_45 = (season_data >= 45).sum()

        results[f"consecutive_dry_days_{season}_14plus_count"] = int(extended_dry_14)
        results[f"consecutive_dry_days_{season}_14plus_pct"] = float(extended_dry_14 / len(season_data) * 100)
        results[f"consecutive_dry_days_{season}_21plus_count"] = int(extended_dry_21)
        results[f"consecutive_dry_days_{season}_21plus_pct"] = float(extended_dry_21 / len(season_data) * 100)
        results[f"consecutive_dry_days_{season}_30plus_count"] = int(extended_dry_30)
        results[f"consecutive_dry_days_{season}_30plus_pct"] = float(extended_dry_30 / len(season_data) * 100)
        results[f"consecutive_dry_days_{season}_45plus_count"] = int(extended_dry_45)
        results[f"consecutive_dry_days_{season}_45plus_pct"] = float(extended_dry_45 / len(season_data) * 100)

        log_info(f"    14+ dry days: {extended_dry_14} ({results[f'consecutive_dry_days_{season}_14plus_pct']:.1f}%)")
        log_info(f"    21+ dry days: {extended_dry_21} ({results[f'consecutive_dry_days_{season}_21plus_pct']:.1f}%)")
        log_info(f"    30+ dry days: {extended_dry_30} ({results[f'consecutive_dry_days_{season}_30plus_pct']:.1f}%)")
        log_info(f"    45+ dry days: {extended_dry_45} ({results[f'consecutive_dry_days_{season}_45plus_pct']:.1f}%)")

    # --- RAINFALL DEFICIT ANALYSIS ---
    log_info("Analyzing rainfall deficit...")

    deficit_mm = df_clean["rainfall_deficit_mm"]
    deficit_pct = df_clean["rainfall_deficit_pct"]

    # Only analyze positive deficits (when actual < normal)
    positive_deficit_mm = deficit_mm[deficit_mm > 0]
    positive_deficit_pct = deficit_pct[deficit_pct > 0]

    if len(positive_deficit_mm) > 0:
        # Percentiles for deficit magnitude
        percentiles = [50, 75, 90, 95]
        for p in percentiles:
            results[f"rainfall_deficit_mm_p{p}"] = float(np.percentile(positive_deficit_mm, p))
            results[f"rainfall_deficit_pct_p{p}"] = float(np.percentile(positive_deficit_pct, p))

        # Statistical summary
        results["rainfall_deficit_mm_mean"] = float(positive_deficit_mm.mean())
        results["rainfall_deficit_mm_median"] = float(positive_deficit_mm.median())
        results["rainfall_deficit_pct_mean"] = float(positive_deficit_pct.mean())
        results["rainfall_deficit_pct_median"] = float(positive_deficit_pct.median())

        log_info(
            f"  Mean deficit: {results['rainfall_deficit_mm_mean']:.2f}mm ({results['rainfall_deficit_pct_mean']:.1f}%)"
        )
        log_info(
            f"  Median deficit: {results['rainfall_deficit_mm_median']:.2f}mm ({results['rainfall_deficit_pct_median']:.1f}%)"
        )
        log_info(
            f"  95th percentile: {results['rainfall_deficit_mm_p95']:.2f}mm ({results['rainfall_deficit_pct_p95']:.1f}%)"
        )

        # Count severe deficits
        severe_deficit_25 = (positive_deficit_pct >= 25).sum()
        severe_deficit_50 = (positive_deficit_pct >= 50).sum()
        severe_deficit_75 = (positive_deficit_pct >= 75).sum()

        results["rainfall_deficit_25pct_plus_count"] = int(severe_deficit_25)
        results["rainfall_deficit_25pct_plus_pct"] = float(severe_deficit_25 / len(df_clean) * 100)
        results["rainfall_deficit_50pct_plus_count"] = int(severe_deficit_50)
        results["rainfall_deficit_50pct_plus_pct"] = float(severe_deficit_50 / len(df_clean) * 100)
        results["rainfall_deficit_75pct_plus_count"] = int(severe_deficit_75)
        results["rainfall_deficit_75pct_plus_pct"] = float(severe_deficit_75 / len(df_clean) * 100)

        log_info(f"  Deficit ≥25%: {severe_deficit_25} ({results['rainfall_deficit_25pct_plus_pct']:.1f}%)")
        log_info(f"  Deficit ≥50%: {severe_deficit_50} ({results['rainfall_deficit_50pct_plus_pct']:.1f}%)")
        log_info(f"  Deficit ≥75%: {severe_deficit_75} ({results['rainfall_deficit_75pct_plus_pct']:.1f}%)")

    # --- COMBINED DROUGHT INDICATORS ---
    log_info("Analyzing combined drought conditions...")

    # Count records meeting various drought criteria
    spi_drought = (df_clean["spi_30day"] < -1.5).sum()
    dry_days_drought = (df_clean["consecutive_dry_days"] >= 28).sum()
    combined_drought = ((df_clean["spi_30day"] < -1.5) & (df_clean["consecutive_dry_days"] >= 28)).sum()

    results["spi_drought_count"] = int(spi_drought)
    results["spi_drought_pct"] = float(spi_drought / len(df_clean) * 100)
    results["dry_days_drought_count"] = int(dry_days_drought)
    results["dry_days_drought_pct"] = float(dry_days_drought / len(df_clean) * 100)
    results["combined_drought_count"] = int(combined_drought)
    results["combined_drought_pct"] = float(combined_drought / len(df_clean) * 100)

    log_info(f"  SPI < -1.5: {spi_drought} ({results['spi_drought_pct']:.1f}%)")
    log_info(f"  Dry days ≥28: {dry_days_drought} ({results['dry_days_drought_pct']:.1f}%)")
    log_info(f"  Combined (SPI AND dry days): {combined_drought} ({results['combined_drought_pct']:.1f}%)")

    # Data quality summary
    total_records = len(df)
    valid_records = len(df_clean)
    missing_records = total_records - valid_records

    results["total_records"] = int(total_records)
    results["valid_records"] = int(valid_records)
    results["missing_records"] = int(missing_records)
    results["data_completeness_pct"] = float(valid_records / total_records * 100)

    log_info(
        f"Data quality: {valid_records}/{total_records} valid records "
        f"({results['data_completeness_pct']:.1f}% complete)"
    )

    # Add metadata
    results["analysis_date"] = pd.Timestamp.now().isoformat()
    results["data_period_start"] = str(df["year"].min()) if "year" in df.columns else "unknown"
    results["data_period_end"] = str(df["year"].max()) if "year" in df.columns else "unknown"

    log_info("Drought indicator analysis complete!")

    return results


def analyze_vegetation_stress(df: pd.DataFrame) -> Dict[str, float]:
    """
    Analyze vegetation stress indicators for crop failure trigger thresholds.

    Calculates VCI percentiles, NDVI anomaly distribution, and stress duration
    statistics to inform crop failure trigger calibration.

    Parameters
    ----------
    df : pd.DataFrame
        Processed NDVI data with vegetation stress indicators including:
        - vci: Vegetation Condition Index (0-100)
        - ndvi: Normalized Difference Vegetation Index
        - ndvi_anomaly_std: Standardized NDVI anomaly
        - stress_duration: Consecutive days of vegetation stress
        - severe_stress_duration: Consecutive days of severe stress
        - crop_failure_risk: Crop failure risk score (0-100)

    Returns
    -------
    Dict[str, float]
        Dictionary containing:
        - VCI percentiles (5th, 10th, 15th, 20th, 25th)
        - NDVI anomaly distribution statistics
        - Stress duration statistics
        - Crop failure risk thresholds
        - Data quality metrics

    Raises
    ------
    ValueError
        If required columns are missing from the dataframe

    Examples
    --------
    >>> df = pd.read_csv('data/processed/ndvi_processed.csv')
    >>> results = analyze_vegetation_stress(df)
    >>> print(f"Critical VCI threshold: {results['vci_p10']:.1f}")
    """
    log_info("Analyzing vegetation stress indicators for crop failure trigger calibration...")

    # Validate required columns
    required_cols = [
        "vci",
        "ndvi",
        "ndvi_anomaly_std",
        "stress_duration",
        "severe_stress_duration",
        "crop_failure_risk",
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required columns: {missing_cols}"
        log_error(error_msg)
        raise ValueError(error_msg)

    # Remove NaN values for analysis
    df_clean = df[required_cols].dropna()

    if len(df_clean) == 0:
        error_msg = "No valid data available for analysis after removing NaN values"
        log_error(error_msg)
        raise ValueError(error_msg)

    log_info(f"Analyzing {len(df_clean)} valid vegetation stress records...")

    results = {}

    # --- VCI ANALYSIS ---
    log_info("Analyzing Vegetation Condition Index (VCI)...")

    vci_data = df_clean["vci"]

    # Calculate percentiles (lower percentiles indicate stress)
    percentiles = [5, 10, 15, 20, 25, 30, 35]
    for p in percentiles:
        percentile_value = np.percentile(vci_data, p)
        key = f"vci_p{p}"
        results[key] = float(percentile_value)
        log_info(f"  {p}th percentile: {percentile_value:.1f}")

    # Calculate statistical summary
    results["vci_mean"] = float(vci_data.mean())
    results["vci_median"] = float(vci_data.median())
    results["vci_std"] = float(vci_data.std())
    results["vci_min"] = float(vci_data.min())
    results["vci_max"] = float(vci_data.max())

    log_info(f"  Mean: {results['vci_mean']:.1f}")
    log_info(f"  Median: {results['vci_median']:.1f}")
    log_info(f"  Std Dev: {results['vci_std']:.1f}")

    # Count stress levels based on VCI thresholds
    extreme_stress = (vci_data < 20).sum()
    severe_stress = (vci_data < 35).sum()
    moderate_stress = (vci_data < 50).sum()

    results["vci_extreme_stress_count"] = int(extreme_stress)
    results["vci_extreme_stress_pct"] = float(extreme_stress / len(vci_data) * 100)
    results["vci_severe_stress_count"] = int(severe_stress)
    results["vci_severe_stress_pct"] = float(severe_stress / len(vci_data) * 100)
    results["vci_moderate_stress_count"] = int(moderate_stress)
    results["vci_moderate_stress_pct"] = float(moderate_stress / len(vci_data) * 100)

    log_info(f"  Extreme stress (VCI < 20): {extreme_stress} ({results['vci_extreme_stress_pct']:.1f}%)")
    log_info(f"  Severe stress (VCI < 35): {severe_stress} ({results['vci_severe_stress_pct']:.1f}%)")
    log_info(f"  Moderate stress (VCI < 50): {moderate_stress} ({results['vci_moderate_stress_pct']:.1f}%)")

    # --- NDVI ANALYSIS ---
    log_info("Analyzing NDVI values...")

    ndvi_data = df_clean["ndvi"]

    # Calculate percentiles
    percentiles = [5, 10, 15, 20, 25]
    for p in percentiles:
        percentile_value = np.percentile(ndvi_data, p)
        key = f"ndvi_p{p}"
        results[key] = float(percentile_value)
        log_info(f"  {p}th percentile: {percentile_value:.3f}")

    # Statistical summary
    results["ndvi_mean"] = float(ndvi_data.mean())
    results["ndvi_median"] = float(ndvi_data.median())
    results["ndvi_std"] = float(ndvi_data.std())
    results["ndvi_min"] = float(ndvi_data.min())
    results["ndvi_max"] = float(ndvi_data.max())

    log_info(f"  Mean: {results['ndvi_mean']:.3f}")
    log_info(f"  Median: {results['ndvi_median']:.3f}")

    # Count low NDVI periods
    low_ndvi_02 = (ndvi_data < 0.2).sum()
    low_ndvi_03 = (ndvi_data < 0.3).sum()
    low_ndvi_04 = (ndvi_data < 0.4).sum()

    results["ndvi_below_02_count"] = int(low_ndvi_02)
    results["ndvi_below_02_pct"] = float(low_ndvi_02 / len(ndvi_data) * 100)
    results["ndvi_below_03_count"] = int(low_ndvi_03)
    results["ndvi_below_03_pct"] = float(low_ndvi_03 / len(ndvi_data) * 100)
    results["ndvi_below_04_count"] = int(low_ndvi_04)
    results["ndvi_below_04_pct"] = float(low_ndvi_04 / len(ndvi_data) * 100)

    log_info(f"  NDVI < 0.2: {low_ndvi_02} ({results['ndvi_below_02_pct']:.1f}%)")
    log_info(f"  NDVI < 0.3: {low_ndvi_03} ({results['ndvi_below_03_pct']:.1f}%)")
    log_info(f"  NDVI < 0.4: {low_ndvi_04} ({results['ndvi_below_04_pct']:.1f}%)")

    # --- NDVI ANOMALY ANALYSIS ---
    log_info("Analyzing NDVI anomalies...")

    anomaly_data = df_clean["ndvi_anomaly_std"]

    # Calculate percentiles (lower = more stressed)
    percentiles = [5, 10, 15, 20, 25]
    for p in percentiles:
        percentile_value = np.percentile(anomaly_data, p)
        key = f"ndvi_anomaly_std_p{p}"
        results[key] = float(percentile_value)
        log_info(f"  {p}th percentile: {percentile_value:.2f} std")

    # Statistical summary
    results["ndvi_anomaly_std_mean"] = float(anomaly_data.mean())
    results["ndvi_anomaly_std_median"] = float(anomaly_data.median())
    results["ndvi_anomaly_std_std"] = float(anomaly_data.std())
    results["ndvi_anomaly_std_min"] = float(anomaly_data.min())
    results["ndvi_anomaly_std_max"] = float(anomaly_data.max())

    log_info(f"  Mean: {results['ndvi_anomaly_std_mean']:.2f} std")
    log_info(f"  Median: {results['ndvi_anomaly_std_median']:.2f} std")

    # Count significant negative anomalies
    anomaly_neg_1 = (anomaly_data < -1.0).sum()
    anomaly_neg_15 = (anomaly_data < -1.5).sum()
    anomaly_neg_2 = (anomaly_data < -2.0).sum()

    results["ndvi_anomaly_below_neg1_count"] = int(anomaly_neg_1)
    results["ndvi_anomaly_below_neg1_pct"] = float(anomaly_neg_1 / len(anomaly_data) * 100)
    results["ndvi_anomaly_below_neg15_count"] = int(anomaly_neg_15)
    results["ndvi_anomaly_below_neg15_pct"] = float(anomaly_neg_15 / len(anomaly_data) * 100)
    results["ndvi_anomaly_below_neg2_count"] = int(anomaly_neg_2)
    results["ndvi_anomaly_below_neg2_pct"] = float(anomaly_neg_2 / len(anomaly_data) * 100)

    log_info(f"  Anomaly < -1.0 std: {anomaly_neg_1} ({results['ndvi_anomaly_below_neg1_pct']:.1f}%)")
    log_info(f"  Anomaly < -1.5 std: {anomaly_neg_15} ({results['ndvi_anomaly_below_neg15_pct']:.1f}%)")
    log_info(f"  Anomaly < -2.0 std: {anomaly_neg_2} ({results['ndvi_anomaly_below_neg2_pct']:.1f}%)")

    # --- STRESS DURATION ANALYSIS ---
    log_info("Analyzing stress duration...")

    stress_duration = df_clean["stress_duration"]
    severe_stress_duration = df_clean["severe_stress_duration"]

    # Only analyze non-zero durations
    active_stress = stress_duration[stress_duration > 0]
    active_severe_stress = severe_stress_duration[severe_stress_duration > 0]

    if len(active_stress) > 0:
        # Percentiles for stress duration
        percentiles = [50, 75, 90, 95, 99]
        for p in percentiles:
            results[f"stress_duration_p{p}"] = float(np.percentile(active_stress, p))

        results["stress_duration_mean"] = float(active_stress.mean())
        results["stress_duration_median"] = float(active_stress.median())
        results["stress_duration_max"] = float(active_stress.max())

        log_info(f"  Mean stress duration: {results['stress_duration_mean']:.1f} days")
        log_info(f"  Median: {results['stress_duration_median']:.1f} days")
        log_info(f"  Max: {results['stress_duration_max']:.1f} days")
        log_info(f"  95th percentile: {results['stress_duration_p95']:.1f} days")

        # Count extended stress periods
        stress_14 = (stress_duration >= 14).sum()
        stress_21 = (stress_duration >= 21).sum()
        stress_30 = (stress_duration >= 30).sum()
        stress_45 = (stress_duration >= 45).sum()

        results["stress_duration_14plus_count"] = int(stress_14)
        results["stress_duration_14plus_pct"] = float(stress_14 / len(df_clean) * 100)
        results["stress_duration_21plus_count"] = int(stress_21)
        results["stress_duration_21plus_pct"] = float(stress_21 / len(df_clean) * 100)
        results["stress_duration_30plus_count"] = int(stress_30)
        results["stress_duration_30plus_pct"] = float(stress_30 / len(df_clean) * 100)
        results["stress_duration_45plus_count"] = int(stress_45)
        results["stress_duration_45plus_pct"] = float(stress_45 / len(df_clean) * 100)

        log_info(f"  Stress ≥14 days: {stress_14} ({results['stress_duration_14plus_pct']:.1f}%)")
        log_info(f"  Stress ≥21 days: {stress_21} ({results['stress_duration_21plus_pct']:.1f}%)")
        log_info(f"  Stress ≥30 days: {stress_30} ({results['stress_duration_30plus_pct']:.1f}%)")

    if len(active_severe_stress) > 0:
        results["severe_stress_duration_mean"] = float(active_severe_stress.mean())
        results["severe_stress_duration_median"] = float(active_severe_stress.median())
        results["severe_stress_duration_max"] = float(active_severe_stress.max())

        log_info(f"  Mean severe stress duration: {results['severe_stress_duration_mean']:.1f} days")

    # --- CROP FAILURE RISK ANALYSIS ---
    log_info("Analyzing crop failure risk...")

    risk_data = df_clean["crop_failure_risk"]

    # Calculate percentiles
    percentiles = [75, 90, 95, 99]
    for p in percentiles:
        percentile_value = np.percentile(risk_data, p)
        key = f"crop_failure_risk_p{p}"
        results[key] = float(percentile_value)
        log_info(f"  {p}th percentile: {percentile_value:.1f}")

    # Statistical summary
    results["crop_failure_risk_mean"] = float(risk_data.mean())
    results["crop_failure_risk_median"] = float(risk_data.median())
    results["crop_failure_risk_std"] = float(risk_data.std())

    log_info(f"  Mean: {results['crop_failure_risk_mean']:.1f}")
    log_info(f"  Median: {results['crop_failure_risk_median']:.1f}")

    # Count high risk periods
    risk_50 = (risk_data >= 50).sum()
    risk_75 = (risk_data >= 75).sum()
    risk_90 = (risk_data >= 90).sum()

    results["crop_failure_risk_50plus_count"] = int(risk_50)
    results["crop_failure_risk_50plus_pct"] = float(risk_50 / len(risk_data) * 100)
    results["crop_failure_risk_75plus_count"] = int(risk_75)
    results["crop_failure_risk_75plus_pct"] = float(risk_75 / len(risk_data) * 100)
    results["crop_failure_risk_90plus_count"] = int(risk_90)
    results["crop_failure_risk_90plus_pct"] = float(risk_90 / len(risk_data) * 100)

    log_info(f"  Risk ≥50: {risk_50} ({results['crop_failure_risk_50plus_pct']:.1f}%)")
    log_info(f"  Risk ≥75: {risk_75} ({results['crop_failure_risk_75plus_pct']:.1f}%)")
    log_info(f"  Risk ≥90: {risk_90} ({results['crop_failure_risk_90plus_pct']:.1f}%)")

    # --- COMBINED CROP FAILURE CONDITIONS ---
    log_info("Analyzing combined crop failure conditions...")

    # Count records meeting various crop failure criteria
    vci_failure = (df_clean["vci"] < 20).sum()
    duration_failure = (df_clean["stress_duration"] >= 30).sum()
    combined_failure = ((df_clean["vci"] < 20) & (df_clean["stress_duration"] >= 30)).sum()

    results["vci_failure_count"] = int(vci_failure)
    results["vci_failure_pct"] = float(vci_failure / len(df_clean) * 100)
    results["duration_failure_count"] = int(duration_failure)
    results["duration_failure_pct"] = float(duration_failure / len(df_clean) * 100)
    results["combined_failure_count"] = int(combined_failure)
    results["combined_failure_pct"] = float(combined_failure / len(df_clean) * 100)

    log_info(f"  VCI < 20: {vci_failure} ({results['vci_failure_pct']:.1f}%)")
    log_info(f"  Stress ≥30 days: {duration_failure} ({results['duration_failure_pct']:.1f}%)")
    log_info(f"  Combined (VCI AND duration): {combined_failure} ({results['combined_failure_pct']:.1f}%)")

    # Data quality summary
    total_records = len(df)
    valid_records = len(df_clean)
    missing_records = total_records - valid_records

    results["total_records"] = int(total_records)
    results["valid_records"] = int(valid_records)
    results["missing_records"] = int(missing_records)
    results["data_completeness_pct"] = float(valid_records / total_records * 100)

    log_info(
        f"Data quality: {valid_records}/{total_records} valid records "
        f"({results['data_completeness_pct']:.1f}% complete)"
    )

    # Add metadata
    results["analysis_date"] = pd.Timestamp.now().isoformat()
    results["data_period_start"] = str(df["year"].min()) if "year" in df.columns else "unknown"
    results["data_period_end"] = str(df["year"].max()) if "year" in df.columns else "unknown"

    log_info("Vegetation stress analysis complete!")

    return results


def generate_threshold_report(analysis_results: Dict, output_dir: str = "data/outputs/calibration") -> str:
    """
    Generate comprehensive threshold analysis report.

    Creates a JSON report with statistical summaries, threshold recommendations,
    and data quality assessments. The report includes results from rainfall,
    drought, and vegetation stress analyses.

    Parameters
    ----------
    analysis_results : Dict
        Combined results from all analysis functions. Should contain keys:
        - 'rainfall': Results from analyze_rainfall_distribution()
        - 'drought': Results from analyze_drought_indicators()
        - 'vegetation': Results from analyze_vegetation_stress()
    output_dir : str
        Directory to save the report (default: "data/outputs/calibration")

    Returns
    -------
    str
        Path to the generated report file

    Raises
    ------
    ValueError
        If required analysis results are missing

    Examples
    --------
    >>> rainfall_results = analyze_rainfall_distribution(chirps_df)
    >>> drought_results = analyze_drought_indicators(chirps_df)
    >>> vegetation_results = analyze_vegetation_stress(ndvi_df)
    >>> combined = {
    ...     'rainfall': rainfall_results,
    ...     'drought': drought_results,
    ...     'vegetation': vegetation_results
    ... }
    >>> report_path = generate_threshold_report(combined)
    >>> print(f"Report saved to: {report_path}")
    """
    log_info("Generating threshold analysis report...")

    # Validate input
    if not isinstance(analysis_results, dict):
        error_msg = "analysis_results must be a dictionary"
        log_error(error_msg)
        raise ValueError(error_msg)

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    log_info(f"Output directory: {output_path}")

    # Generate timestamp for report
    timestamp = pd.Timestamp.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")

    # Create report structure
    report = {
        "report_metadata": {
            "report_title": "Insurance Trigger Threshold Analysis Report",
            "generated_at": timestamp.isoformat(),
            "report_version": "1.0.0",
            "description": "Statistical analysis of climate indicators for insurance trigger calibration",
        },
        "analysis_results": analysis_results,
        "threshold_recommendations": {},
        "data_quality_summary": {},
        "warnings": [],
    }

    # Extract threshold recommendations from analysis results
    log_info("Extracting threshold recommendations...")

    # Rainfall/Flood thresholds
    if "rainfall" in analysis_results:
        rainfall = analysis_results["rainfall"]
        report["threshold_recommendations"]["flood_triggers"] = {
            "daily_rainfall_threshold_mm": {
                "value": rainfall.get("daily_rainfall_p99", None),
                "rationale": "99th percentile of daily rainfall - extreme rainfall events",
                "expected_trigger_rate_pct": 1.0,
            },
            "rainfall_7day_threshold_mm": {
                "value": rainfall.get("rainfall_7day_p97", None),
                "rationale": "97th percentile of 7-day rainfall - sustained heavy rainfall",
                "expected_trigger_rate_pct": 3.0,
            },
            "heavy_rain_day_threshold_mm": {
                "value": rainfall.get("heavy_rain_day_threshold", None),
                "rationale": "95th percentile of daily rainfall - definition of heavy rain day",
                "expected_trigger_rate_pct": 5.0,
            },
            "heavy_rain_days_7day_threshold": {
                "value": 5,
                "rationale": "5+ heavy rain days in 7-day window indicates flood risk",
                "expected_trigger_rate_pct": "varies",
            },
        }

        # Add data quality warnings for rainfall
        if rainfall.get("data_completeness_pct", 100) < 95:
            report["warnings"].append(
                f"Rainfall data completeness is {rainfall['data_completeness_pct']:.1f}% - "
                "thresholds may be less reliable"
            )

        if rainfall.get("daily_rainfall_outlier_count", 0) > 0:
            report["warnings"].append(
                f"Found {rainfall['daily_rainfall_outlier_count']} rainfall outliers beyond 5 std dev - "
                "review data quality"
            )

    # Drought thresholds
    if "drought" in analysis_results:
        drought = analysis_results["drought"]
        report["threshold_recommendations"]["drought_triggers"] = {
            "spi_30day_threshold": {
                "value": -1.5,
                "rationale": "Severe drought classification per WMO standards",
                "expected_trigger_rate_pct": drought.get("spi_drought_pct", None),
            },
            "consecutive_dry_days_wet_season": {
                "value": 35,
                "rationale": "Extended dry period during wet season (Oct-May)",
                "expected_trigger_rate_pct": drought.get("consecutive_dry_days_wet_30plus_pct", None),
            },
            "consecutive_dry_days_dry_season": {
                "value": 45,
                "rationale": "Extended dry period during dry season (Jun-Sep)",
                "expected_trigger_rate_pct": drought.get("consecutive_dry_days_dry_45plus_pct", None),
            },
            "combined_trigger_rate": {
                "value": "SPI < -1.5 AND dry days >= 28",
                "expected_trigger_rate_pct": drought.get("combined_drought_pct", None),
                "rationale": "Combined criteria for drought trigger activation",
            },
        }

        # Add data quality warnings for drought
        if drought.get("data_completeness_pct", 100) < 95:
            report["warnings"].append(
                f"Drought data completeness is {drought['data_completeness_pct']:.1f}% - "
                "thresholds may be less reliable"
            )

    # Vegetation/Crop failure thresholds
    if "vegetation" in analysis_results:
        vegetation = analysis_results["vegetation"]
        report["threshold_recommendations"]["crop_failure_triggers"] = {
            "vci_threshold": {
                "value": 20,
                "rationale": "Extreme vegetation stress per FAO standards",
                "expected_trigger_rate_pct": vegetation.get("vci_extreme_stress_pct", None),
            },
            "vci_duration_days": {
                "value": 30,
                "rationale": "Sustained stress period indicating crop failure risk",
                "expected_trigger_rate_pct": vegetation.get("stress_duration_30plus_pct", None),
            },
            "ndvi_anomaly_threshold_std": {
                "value": -2.0,
                "rationale": "Significant negative vegetation anomaly",
                "expected_trigger_rate_pct": vegetation.get("ndvi_anomaly_below_neg2_pct", None),
            },
            "ndvi_anomaly_duration_days": {
                "value": 21,
                "rationale": "Sustained anomaly period for crop failure",
                "expected_trigger_rate_pct": "varies",
            },
            "combined_trigger_rate": {
                "value": "VCI < 20 AND duration >= 30 days",
                "expected_trigger_rate_pct": vegetation.get("combined_failure_pct", None),
                "rationale": "Combined criteria for crop failure trigger activation",
            },
        }

        # Add data quality warnings for vegetation
        if vegetation.get("data_completeness_pct", 100) < 90:
            report["warnings"].append(
                f"Vegetation data completeness is {vegetation['data_completeness_pct']:.1f}% - "
                "thresholds may be less reliable"
            )

    # Generate data quality summary
    log_info("Generating data quality summary...")

    quality_summary = {}

    for analysis_type in ["rainfall", "drought", "vegetation"]:
        if analysis_type in analysis_results:
            data = analysis_results[analysis_type]
            quality_summary[analysis_type] = {
                "total_records": data.get("total_records", 0),
                "valid_records": data.get("valid_records", 0),
                "missing_records": data.get("missing_records", 0),
                "completeness_pct": data.get("data_completeness_pct", 0),
                "data_period": f"{data.get('data_period_start', 'unknown')} to {data.get('data_period_end', 'unknown')}",
            }

    report["data_quality_summary"] = quality_summary

    # Add overall assessment
    log_info("Adding overall assessment...")

    overall_warnings = []

    # Check if all analyses are present
    if "rainfall" not in analysis_results:
        overall_warnings.append("Rainfall analysis missing - flood trigger calibration incomplete")
    if "drought" not in analysis_results:
        overall_warnings.append("Drought analysis missing - drought trigger calibration incomplete")
    if "vegetation" not in analysis_results:
        overall_warnings.append("Vegetation analysis missing - crop failure trigger calibration incomplete")

    # Check trigger rates are in acceptable ranges
    if "rainfall" in analysis_results:
        # Flood should be 5-15%
        extreme_rain_pct = analysis_results["rainfall"].get("extreme_rain_100mm_pct", 0)
        if extreme_rain_pct < 5 or extreme_rain_pct > 15:
            overall_warnings.append(
                f"Extreme rainfall events ({extreme_rain_pct:.1f}%) outside target range (5-15%) - " "adjust thresholds"
            )

    if "drought" in analysis_results:
        # Drought should be 8-20%
        drought_pct = analysis_results["drought"].get("spi_drought_pct", 0)
        if drought_pct < 8 or drought_pct > 20:
            overall_warnings.append(
                f"Drought trigger rate ({drought_pct:.1f}%) outside target range (8-20%) - " "adjust thresholds"
            )

    if "vegetation" in analysis_results:
        # Crop failure should be 3-10%
        crop_failure_pct = analysis_results["vegetation"].get("vci_extreme_stress_pct", 0)
        if crop_failure_pct < 3 or crop_failure_pct > 10:
            overall_warnings.append(
                f"Crop failure trigger rate ({crop_failure_pct:.1f}%) outside target range (3-10%) - "
                "adjust thresholds"
            )

    report["warnings"].extend(overall_warnings)

    # Save report as JSON
    report_filename = f"threshold_analysis_report_{timestamp_str}.json"
    report_path = output_path / report_filename

    log_info(f"Saving report to: {report_path}")

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Also save a summary text file
    summary_filename = f"threshold_analysis_summary_{timestamp_str}.txt"
    summary_path = output_path / summary_filename

    log_info(f"Saving summary to: {summary_path}")

    with open(summary_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("INSURANCE TRIGGER THRESHOLD ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n")
        f.write(f"\nGenerated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Report Version: 1.0.0\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("THRESHOLD RECOMMENDATIONS\n")
        f.write("=" * 80 + "\n")

        # Flood triggers
        if "flood_triggers" in report["threshold_recommendations"]:
            f.write("\n--- FLOOD TRIGGERS ---\n")
            for key, value in report["threshold_recommendations"]["flood_triggers"].items():
                f.write(f"\n{key}:\n")
                f.write(f"  Value: {value['value']}\n")
                f.write(f"  Rationale: {value['rationale']}\n")
                rate = value["expected_trigger_rate_pct"]
                if isinstance(rate, (int, float)):
                    f.write(f"  Expected trigger rate: {rate:.1f}%\n")
                else:
                    f.write(f"  Expected trigger rate: {rate}\n")

        # Drought triggers
        if "drought_triggers" in report["threshold_recommendations"]:
            f.write("\n--- DROUGHT TRIGGERS ---\n")
            for key, value in report["threshold_recommendations"]["drought_triggers"].items():
                f.write(f"\n{key}:\n")
                f.write(f"  Value: {value['value']}\n")
                f.write(f"  Rationale: {value['rationale']}\n")
                if "expected_trigger_rate_pct" in value and value["expected_trigger_rate_pct"] is not None:
                    f.write(f"  Expected trigger rate: {value['expected_trigger_rate_pct']:.1f}%\n")

        # Crop failure triggers
        if "crop_failure_triggers" in report["threshold_recommendations"]:
            f.write("\n--- CROP FAILURE TRIGGERS ---\n")
            for key, value in report["threshold_recommendations"]["crop_failure_triggers"].items():
                f.write(f"\n{key}:\n")
                f.write(f"  Value: {value['value']}\n")
                f.write(f"  Rationale: {value['rationale']}\n")
                if "expected_trigger_rate_pct" in value and value["expected_trigger_rate_pct"] is not None:
                    rate = value["expected_trigger_rate_pct"]
                    if isinstance(rate, (int, float)):
                        f.write(f"  Expected trigger rate: {rate:.1f}%\n")
                    else:
                        f.write(f"  Expected trigger rate: {rate}\n")

        # Data quality
        f.write("\n" + "=" * 80 + "\n")
        f.write("DATA QUALITY SUMMARY\n")
        f.write("=" * 80 + "\n")

        for analysis_type, quality in quality_summary.items():
            f.write(f"\n{analysis_type.upper()}:\n")
            f.write(f"  Total records: {quality['total_records']}\n")
            f.write(f"  Valid records: {quality['valid_records']}\n")
            f.write(f"  Completeness: {quality['completeness_pct']:.1f}%\n")
            f.write(f"  Data period: {quality['data_period']}\n")

        # Warnings
        if report["warnings"]:
            f.write("\n" + "=" * 80 + "\n")
            f.write("WARNINGS AND RECOMMENDATIONS\n")
            f.write("=" * 80 + "\n\n")
            for i, warning in enumerate(report["warnings"], 1):
                f.write(f"{i}. {warning}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")

    log_info(f"Report generation complete!")
    log_info(f"  JSON report: {report_path}")
    log_info(f"  Text summary: {summary_path}")

    return str(report_path)
