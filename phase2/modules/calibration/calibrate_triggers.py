"""
Trigger Calibration Module for Insurance Trigger Optimization

This module provides functions to calibrate insurance trigger thresholds
to achieve target trigger rates while maintaining alignment with extreme
weather events.

Functions:
- calibrate_flood_triggers: Calibrate flood trigger thresholds
- calibrate_drought_triggers: Calibrate drought trigger thresholds
- calibrate_crop_failure_triggers: Calibrate crop failure trigger thresholds
- simulate_trigger_rates: Simulate trigger rates with proposed thresholds
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from pathlib import Path

from utils.logger import log_info, log_error, log_warning


def calibrate_flood_triggers(
    rainfall_stats: Dict, df: pd.DataFrame, target_trigger_rate: float = 0.10, tolerance: float = 0.025
) -> Dict[str, float]:
    """Calibrate flood trigger thresholds to achieve target trigger rate."""
    log_info(f"Calibrating flood triggers for target rate: {target_trigger_rate*100:.1f}%")
    log_info(
        f"Acceptable range: {(target_trigger_rate-tolerance)*100:.1f}% - {(target_trigger_rate+tolerance)*100:.1f}%"
    )

    if "rainfall_mm" not in df.columns or "rainfall_7day" not in df.columns:
        error_msg = "DataFrame must contain 'rainfall_mm' and 'rainfall_7day' columns"
        log_error(error_msg)
        raise ValueError(error_msg)

    initial_daily_threshold = rainfall_stats.get("daily_rainfall_p99", 150)
    initial_7day_threshold = rainfall_stats.get("rainfall_7day_p97", 250)
    initial_heavy_rain_threshold = rainfall_stats.get("daily_rainfall_p95", 50)

    log_info(f"Initial thresholds:")
    log_info(f"  Daily rainfall: {initial_daily_threshold:.1f}mm (99th percentile)")
    log_info(f"  7-day rainfall: {initial_7day_threshold:.1f}mm (97th percentile)")
    log_info(f"  Heavy rain day: {initial_heavy_rain_threshold:.1f}mm (95th percentile)")

    min_rate = target_trigger_rate - tolerance
    max_rate = target_trigger_rate + tolerance
    max_iterations = 20

    best_thresholds = None
    best_distance = float("inf")

    daily_threshold = initial_daily_threshold
    day7_threshold = initial_7day_threshold
    heavy_rain_threshold = initial_heavy_rain_threshold
    heavy_rain_days_required = 5

    log_info("Starting iterative calibration...")

    for iteration in range(max_iterations):
        df_test = df.copy()
        df_test["is_heavy_rain"] = (df_test["rainfall_mm"] > heavy_rain_threshold).astype(int)
        df_test["heavy_rain_days_7day"] = df_test["is_heavy_rain"].rolling(window=7, min_periods=1).sum()
        df_test["flood_trigger"] = (
            (df_test["rainfall_mm"] > daily_threshold)
            | (df_test["rainfall_7day"] > day7_threshold)
            | (df_test["heavy_rain_days_7day"] >= heavy_rain_days_required)
        ).astype(int)

        trigger_rate = df_test["flood_trigger"].mean()
        log_info(f"Iteration {iteration+1}: Trigger rate = {trigger_rate*100:.2f}%")

        distance = abs(trigger_rate - target_trigger_rate)
        if distance < best_distance:
            best_distance = distance
            best_thresholds = {
                "daily_rainfall_threshold": float(daily_threshold),
                "rainfall_7day_threshold": float(day7_threshold),
                "heavy_rain_day_threshold": float(heavy_rain_threshold),
                "heavy_rain_days_required": int(heavy_rain_days_required),
                "rainfall_percentile_threshold": 99,
                "achieved_trigger_rate": float(trigger_rate),
                "confidence_score": 1.0 - min(distance / target_trigger_rate, 1.0),
            }

        if min_rate <= trigger_rate <= max_rate:
            log_info(f"✓ Target achieved! Trigger rate: {trigger_rate*100:.2f}%")
            break

        if trigger_rate > max_rate:
            adjustment_factor = 1.05
            daily_threshold *= adjustment_factor
            day7_threshold *= adjustment_factor
            heavy_rain_threshold *= adjustment_factor
            log_info(f"  Rate too high, increasing thresholds by {(adjustment_factor-1)*100:.0f}%")
        elif trigger_rate < min_rate:
            adjustment_factor = 0.95
            daily_threshold *= adjustment_factor
            day7_threshold *= adjustment_factor
            heavy_rain_threshold *= adjustment_factor
            log_info(f"  Rate too low, decreasing thresholds by {(1-adjustment_factor)*100:.0f}%")

    if best_thresholds is None:
        log_warning("Calibration did not converge, using initial thresholds")
        best_thresholds = {
            "daily_rainfall_threshold": float(initial_daily_threshold),
            "rainfall_7day_threshold": float(initial_7day_threshold),
            "heavy_rain_day_threshold": float(initial_heavy_rain_threshold),
            "heavy_rain_days_required": 5,
            "rainfall_percentile_threshold": 99,
            "achieved_trigger_rate": 0.0,
            "confidence_score": 0.0,
        }

    log_info("Flood trigger calibration complete!")
    log_info(f"Final thresholds:")
    log_info(f"  Daily rainfall: {best_thresholds['daily_rainfall_threshold']:.1f}mm")
    log_info(f"  7-day rainfall: {best_thresholds['rainfall_7day_threshold']:.1f}mm")
    log_info(f"  Heavy rain day: {best_thresholds['heavy_rain_day_threshold']:.1f}mm")
    log_info(f"  Heavy rain days required: {best_thresholds['heavy_rain_days_required']}")
    log_info(f"  Achieved trigger rate: {best_thresholds['achieved_trigger_rate']*100:.2f}%")
    log_info(f"  Confidence score: {best_thresholds['confidence_score']:.3f}")

    return best_thresholds


def calibrate_drought_triggers(
    drought_stats: Dict, df: pd.DataFrame, target_trigger_rate: float = 0.12, tolerance: float = 0.04
) -> Dict[str, float]:
    """Calibrate drought trigger thresholds with seasonal adjustments."""
    log_info(f"Calibrating drought triggers for target rate: {target_trigger_rate*100:.1f}%")
    log_info(
        f"Acceptable range: {(target_trigger_rate-tolerance)*100:.1f}% - {(target_trigger_rate+tolerance)*100:.1f}%"
    )

    required_cols = ["spi_30day", "consecutive_dry_days", "month"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        error_msg = f"DataFrame missing required columns: {missing_cols}"
        log_error(error_msg)
        raise ValueError(error_msg)

    spi_threshold = -1.5
    wet_season_dry_days = 35
    dry_season_dry_days = 45
    dry_day_definition = 1.0

    log_info(f"Initial thresholds:")
    log_info(f"  SPI 30-day: {spi_threshold:.2f}")
    log_info(f"  Wet season dry days: {wet_season_dry_days}")
    log_info(f"  Dry season dry days: {dry_season_dry_days}")

    min_rate = target_trigger_rate - tolerance
    max_rate = target_trigger_rate + tolerance
    max_iterations = 20

    best_thresholds = None
    best_distance = float("inf")

    log_info("Starting iterative calibration...")

    for iteration in range(max_iterations):
        df_test = df.copy()
        df_test["season"] = df_test["month"].apply(lambda m: "wet" if m in [10, 11, 12, 1, 2, 3, 4, 5] else "dry")
        df_test["dry_day_threshold"] = df_test["season"].map({"wet": wet_season_dry_days, "dry": dry_season_dry_days})
        df_test["drought_trigger"] = (
            (df_test["spi_30day"] < spi_threshold) & (df_test["consecutive_dry_days"] >= df_test["dry_day_threshold"])
        ).astype(int)

        trigger_rate = df_test["drought_trigger"].mean()
        log_info(f"Iteration {iteration+1}: Trigger rate = {trigger_rate*100:.2f}%")

        distance = abs(trigger_rate - target_trigger_rate)
        if distance < best_distance:
            best_distance = distance
            best_thresholds = {
                "spi_30day_threshold": float(spi_threshold),
                "consecutive_dry_days_wet_season": int(wet_season_dry_days),
                "consecutive_dry_days_dry_season": int(dry_season_dry_days),
                "dry_day_definition_mm": float(dry_day_definition),
                "achieved_trigger_rate": float(trigger_rate),
                "confidence_score": 1.0 - min(distance / target_trigger_rate, 1.0),
            }

        if min_rate <= trigger_rate <= max_rate:
            log_info(f"✓ Target achieved! Trigger rate: {trigger_rate*100:.2f}%")
            break

        if trigger_rate > max_rate:
            spi_threshold -= 0.1
            wet_season_dry_days += 2
            dry_season_dry_days += 2
            log_info(f"  Rate too high, making criteria stricter")
        elif trigger_rate < min_rate:
            spi_threshold += 0.1
            wet_season_dry_days = max(14, wet_season_dry_days - 2)
            dry_season_dry_days = max(21, dry_season_dry_days - 2)
            log_info(f"  Rate too low, making criteria looser")

    if best_thresholds is None:
        log_warning("Calibration did not converge, using initial thresholds")
        best_thresholds = {
            "spi_30day_threshold": -1.5,
            "consecutive_dry_days_wet_season": 35,
            "consecutive_dry_days_dry_season": 45,
            "dry_day_definition_mm": 1.0,
            "achieved_trigger_rate": 0.0,
            "confidence_score": 0.0,
        }

    log_info("Drought trigger calibration complete!")
    log_info(f"Final thresholds:")
    log_info(f"  SPI 30-day: {best_thresholds['spi_30day_threshold']:.2f}")
    log_info(f"  Wet season dry days: {best_thresholds['consecutive_dry_days_wet_season']}")
    log_info(f"  Dry season dry days: {best_thresholds['consecutive_dry_days_dry_season']}")
    log_info(f"  Achieved trigger rate: {best_thresholds['achieved_trigger_rate']*100:.2f}%")
    log_info(f"  Confidence score: {best_thresholds['confidence_score']:.3f}")

    return best_thresholds


def calibrate_crop_failure_triggers(
    vegetation_stats: Dict, df: pd.DataFrame, target_trigger_rate: float = 0.06, tolerance: float = 0.035
) -> Dict[str, float]:
    """Calibrate crop failure trigger thresholds."""
    log_info(f"Calibrating crop failure triggers for target rate: {target_trigger_rate*100:.1f}%")
    log_info(
        f"Acceptable range: {(target_trigger_rate-tolerance)*100:.1f}% - {(target_trigger_rate+tolerance)*100:.1f}%"
    )

    required_cols = ["vci", "ndvi_anomaly_std", "stress_duration", "crop_failure_risk"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        error_msg = f"DataFrame missing required columns: {missing_cols}"
        log_error(error_msg)
        raise ValueError(error_msg)

    vci_threshold = 20
    vci_duration = 30
    ndvi_anomaly_threshold = -2.0
    ndvi_anomaly_duration = 21
    risk_threshold = 75

    log_info(f"Initial thresholds:")
    log_info(f"  VCI: {vci_threshold}")
    log_info(f"  VCI duration: {vci_duration} days")
    log_info(f"  NDVI anomaly: {ndvi_anomaly_threshold:.1f} std")
    log_info(f"  NDVI anomaly duration: {ndvi_anomaly_duration} days")
    log_info(f"  Risk score: {risk_threshold}")

    min_rate = target_trigger_rate - tolerance
    max_rate = target_trigger_rate + tolerance
    max_iterations = 20

    best_thresholds = None
    best_distance = float("inf")

    log_info("Starting iterative calibration...")

    for iteration in range(max_iterations):
        df_test = df.copy()
        df_test["crop_failure_trigger"] = (
            ((df_test["vci"] < vci_threshold) & (df_test["stress_duration"] >= vci_duration))
            | (
                (df_test["ndvi_anomaly_std"] < ndvi_anomaly_threshold)
                & (df_test["stress_duration"] >= ndvi_anomaly_duration)
            )
            | (df_test["crop_failure_risk"] > risk_threshold)
        ).astype(int)

        trigger_rate = df_test["crop_failure_trigger"].mean()
        log_info(f"Iteration {iteration+1}: Trigger rate = {trigger_rate*100:.2f}%")

        distance = abs(trigger_rate - target_trigger_rate)
        if distance < best_distance:
            best_distance = distance
            best_thresholds = {
                "vci_threshold": float(vci_threshold),
                "vci_duration_days": int(vci_duration),
                "ndvi_anomaly_threshold_std": float(ndvi_anomaly_threshold),
                "ndvi_anomaly_duration_days": int(ndvi_anomaly_duration),
                "crop_failure_risk_threshold": float(risk_threshold),
                "achieved_trigger_rate": float(trigger_rate),
                "confidence_score": 1.0 - min(distance / target_trigger_rate, 1.0),
            }

        if min_rate <= trigger_rate <= max_rate:
            log_info(f"✓ Target achieved! Trigger rate: {trigger_rate*100:.2f}%")
            break

        if trigger_rate > max_rate:
            vci_threshold = max(10, vci_threshold - 2)
            vci_duration += 3
            ndvi_anomaly_threshold -= 0.1
            ndvi_anomaly_duration += 3
            risk_threshold += 5
            log_info(f"  Rate too high, making criteria stricter")
        elif trigger_rate < min_rate:
            vci_threshold = min(35, vci_threshold + 2)
            vci_duration = max(14, vci_duration - 3)
            ndvi_anomaly_threshold = min(-1.0, ndvi_anomaly_threshold + 0.1)
            ndvi_anomaly_duration = max(7, ndvi_anomaly_duration - 3)
            risk_threshold = max(50, risk_threshold - 5)
            log_info(f"  Rate too low, making criteria looser")

    if best_thresholds is None:
        log_warning("Calibration did not converge, using initial thresholds")
        best_thresholds = {
            "vci_threshold": 20,
            "vci_duration_days": 30,
            "ndvi_anomaly_threshold_std": -2.0,
            "ndvi_anomaly_duration_days": 21,
            "crop_failure_risk_threshold": 75,
            "achieved_trigger_rate": 0.0,
            "confidence_score": 0.0,
        }

    log_info("Crop failure trigger calibration complete!")
    log_info(f"Final thresholds:")
    log_info(f"  VCI: {best_thresholds['vci_threshold']:.1f}")
    log_info(f"  VCI duration: {best_thresholds['vci_duration_days']} days")
    log_info(f"  NDVI anomaly: {best_thresholds['ndvi_anomaly_threshold_std']:.2f} std")
    log_info(f"  NDVI anomaly duration: {best_thresholds['ndvi_anomaly_duration_days']} days")
    log_info(f"  Risk score: {best_thresholds['crop_failure_risk_threshold']:.1f}")
    log_info(f"  Achieved trigger rate: {best_thresholds['achieved_trigger_rate']*100:.2f}%")
    log_info(f"  Confidence score: {best_thresholds['confidence_score']:.3f}")

    return best_thresholds


def simulate_trigger_rates(df_chirps: pd.DataFrame, df_ndvi: pd.DataFrame, thresholds: Dict) -> Dict[str, float]:
    """
    Simulate trigger rates with proposed thresholds.

    Applies proposed thresholds to historical data and calculates resulting
    trigger rates for validation. Generates simulation report with confidence
    scores.

    Parameters
    ----------
    df_chirps : pd.DataFrame
        Historical CHIRPS data with rainfall and drought indicators
    df_ndvi : pd.DataFrame
        Historical NDVI data with vegetation stress indicators
    thresholds : Dict
        Dictionary containing all calibrated thresholds from:
        - calibrate_flood_triggers()
        - calibrate_drought_triggers()
        - calibrate_crop_failure_triggers()

    Returns
    -------
    Dict[str, float]
        Dictionary with simulation results:
        - flood_trigger_rate: simulated flood trigger rate
        - drought_trigger_rate: simulated drought trigger rate
        - crop_failure_trigger_rate: simulated crop failure trigger rate
        - overall_trigger_rate: combined trigger rate
        - flood_confidence_avg: average flood confidence score
        - drought_confidence_avg: average drought confidence score
        - crop_failure_confidence_avg: average crop failure confidence score
        - total_months: number of months simulated
        - flood_months: number of months with flood triggers
        - drought_months: number of months with drought triggers
        - crop_failure_months: number of months with crop failure triggers
    """
    log_info("Simulating trigger rates with proposed thresholds...")

    results = {}

    # FLOOD TRIGGER SIMULATION
    if "flood_triggers" in thresholds or "daily_rainfall_threshold" in thresholds:
        log_info("Simulating flood triggers...")

        flood_config = thresholds.get("flood_triggers", thresholds)

        df_flood = df_chirps.copy()
        daily_threshold = flood_config.get("daily_rainfall_threshold", 150)
        day7_threshold = flood_config.get("rainfall_7day_threshold", 250)
        heavy_rain_threshold = flood_config.get("heavy_rain_day_threshold", 50)
        heavy_rain_days_req = flood_config.get("heavy_rain_days_required", 5)

        df_flood["is_heavy_rain"] = (df_flood["rainfall_mm"] > heavy_rain_threshold).astype(int)
        df_flood["heavy_rain_days_7day"] = df_flood["is_heavy_rain"].rolling(window=7, min_periods=1).sum()

        df_flood["flood_trigger"] = (
            (df_flood["rainfall_mm"] > daily_threshold)
            | (df_flood["rainfall_7day"] > day7_threshold)
            | (df_flood["heavy_rain_days_7day"] >= heavy_rain_days_req)
        ).astype(int)

        flood_rate = df_flood["flood_trigger"].mean()
        flood_months = df_flood["flood_trigger"].sum()

        results["flood_trigger_rate"] = float(flood_rate)
        results["flood_months"] = int(flood_months)

        log_info(f"  Flood trigger rate: {flood_rate*100:.2f}% ({flood_months} months)")

    # DROUGHT TRIGGER SIMULATION
    if "drought_triggers" in thresholds or "spi_30day_threshold" in thresholds:
        log_info("Simulating drought triggers...")

        drought_config = thresholds.get("drought_triggers", thresholds)

        df_drought = df_chirps.copy()
        spi_threshold = drought_config.get("spi_30day_threshold", -1.5)
        wet_dry_days = drought_config.get("consecutive_dry_days_wet_season", 35)
        dry_dry_days = drought_config.get("consecutive_dry_days_dry_season", 45)

        df_drought["season"] = df_drought["month"].apply(lambda m: "wet" if m in [10, 11, 12, 1, 2, 3, 4, 5] else "dry")
        df_drought["dry_day_threshold"] = df_drought["season"].map({"wet": wet_dry_days, "dry": dry_dry_days})

        df_drought["drought_trigger"] = (
            (df_drought["spi_30day"] < spi_threshold)
            & (df_drought["consecutive_dry_days"] >= df_drought["dry_day_threshold"])
        ).astype(int)

        drought_rate = df_drought["drought_trigger"].mean()
        drought_months = df_drought["drought_trigger"].sum()

        results["drought_trigger_rate"] = float(drought_rate)
        results["drought_months"] = int(drought_months)

        log_info(f"  Drought trigger rate: {drought_rate*100:.2f}% ({drought_months} months)")

    # CROP FAILURE TRIGGER SIMULATION
    if "crop_failure_triggers" in thresholds or "vci_threshold" in thresholds:
        log_info("Simulating crop failure triggers...")

        crop_config = thresholds.get("crop_failure_triggers", thresholds)

        df_crop = df_ndvi.copy()
        vci_threshold = crop_config.get("vci_threshold", 20)
        vci_duration = crop_config.get("vci_duration_days", 30)
        ndvi_anomaly_threshold = crop_config.get("ndvi_anomaly_threshold_std", -2.0)
        ndvi_anomaly_duration = crop_config.get("ndvi_anomaly_duration_days", 21)
        risk_threshold = crop_config.get("crop_failure_risk_threshold", 75)

        df_crop["crop_failure_trigger"] = (
            ((df_crop["vci"] < vci_threshold) & (df_crop["stress_duration"] >= vci_duration))
            | (
                (df_crop["ndvi_anomaly_std"] < ndvi_anomaly_threshold)
                & (df_crop["stress_duration"] >= ndvi_anomaly_duration)
            )
            | (df_crop["crop_failure_risk"] > risk_threshold)
        ).astype(int)

        crop_rate = df_crop["crop_failure_trigger"].mean()
        crop_months = df_crop["crop_failure_trigger"].sum()

        results["crop_failure_trigger_rate"] = float(crop_rate)
        results["crop_failure_months"] = int(crop_months)

        log_info(f"  Crop failure trigger rate: {crop_rate*100:.2f}% ({crop_months} months)")

    # OVERALL STATISTICS
    results["total_months"] = len(df_chirps)

    # Calculate overall trigger rate (any trigger activated)
    if "flood_trigger_rate" in results and "drought_trigger_rate" in results and "crop_failure_trigger_rate" in results:
        # This is approximate - actual would require merging dataframes
        overall_rate = min(
            1.0, results["flood_trigger_rate"] + results["drought_trigger_rate"] + results["crop_failure_trigger_rate"]
        )
        results["overall_trigger_rate"] = float(overall_rate)
        log_info(f"  Overall trigger rate (approximate): {overall_rate*100:.2f}%")

    # Add validation flags
    results["flood_in_range"] = 0.05 <= results.get("flood_trigger_rate", 0) <= 0.15
    results["drought_in_range"] = 0.08 <= results.get("drought_trigger_rate", 0) <= 0.20
    results["crop_failure_in_range"] = 0.03 <= results.get("crop_failure_trigger_rate", 0) <= 0.10

    log_info("Simulation complete!")
    log_info(f"Validation:")
    log_info(f"  Flood in range (5-15%): {results['flood_in_range']}")
    log_info(f"  Drought in range (8-20%): {results['drought_in_range']}")
    log_info(f"  Crop failure in range (3-10%): {results['crop_failure_in_range']}")

    return results
