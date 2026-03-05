"""
Generate Calibrated Trigger Configuration

This script runs the complete calibration workflow to generate an initial
trigger_thresholds.yaml configuration file with calibrated values based on
historical climate data.

Workflow:
1. Load historical CHIRPS and NDVI data
2. Run threshold analysis (rainfall, drought, vegetation)
3. Calibrate trigger thresholds to achieve target rates
4. Generate YAML configuration file with calibrated values
5. Validate generated configuration

Requirements: 1.5, 7.1, 7.4
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import pandas as pd
import yaml

from modules.calibration.analyze_thresholds import (
    analyze_drought_indicators,
    analyze_rainfall_distribution,
    analyze_vegetation_stress,
    generate_threshold_report,
)
from modules.calibration.calibrate_triggers import (
    calibrate_crop_failure_triggers,
    calibrate_drought_triggers,
    calibrate_flood_triggers,
    simulate_trigger_rates,
)
from modules.calibration.config_loader import validate_trigger_config
from utils.logger import log_error, log_info


def load_historical_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load historical CHIRPS and NDVI processed data for calibration.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        Tuple of (chirps_df, ndvi_df) containing processed historical data

    Raises
    ------
    FileNotFoundError
        If processed data files are not found
    """
    log_info("Loading historical climate data for calibration...")

    # Load CHIRPS processed data
    chirps_path = Path("outputs/processed/chirps_processed.csv")
    if not chirps_path.exists():
        error_msg = f"CHIRPS processed data not found: {chirps_path}"
        log_error(error_msg)
        raise FileNotFoundError(error_msg)

    log_info(f"Loading CHIRPS data from: {chirps_path}")
    df_chirps = pd.read_csv(chirps_path)
    log_info(f"  Loaded {len(df_chirps)} CHIRPS records")

    # Load NDVI processed data
    ndvi_path = Path("outputs/processed/ndvi_processed.csv")
    if not ndvi_path.exists():
        error_msg = f"NDVI processed data not found: {ndvi_path}"
        log_error(error_msg)
        raise FileNotFoundError(error_msg)

    log_info(f"Loading NDVI data from: {ndvi_path}")
    df_ndvi = pd.read_csv(ndvi_path)
    log_info(f"  Loaded {len(df_ndvi)} NDVI records")

    return df_chirps, df_ndvi


def generate_calibrated_config(
    df_chirps: pd.DataFrame,
    df_ndvi: pd.DataFrame,
    output_path: str = "configs/trigger_thresholds.yaml",
    target_flood_rate: float = 0.10,
    target_drought_rate: float = 0.12,
    target_crop_failure_rate: float = 0.06,
) -> Dict:
    """
    Generate calibrated trigger configuration from historical data.

    Parameters
    ----------
    df_chirps : pd.DataFrame
        Processed CHIRPS data with rainfall and drought indicators
    df_ndvi : pd.DataFrame
        Processed NDVI data with vegetation stress indicators
    output_path : str
        Path where configuration file should be saved
    target_flood_rate : float
        Target flood trigger rate (default: 0.10 = 10%)
    target_drought_rate : float
        Target drought trigger rate (default: 0.12 = 12%)
    target_crop_failure_rate : float
        Target crop failure trigger rate (default: 0.06 = 6%)

    Returns
    -------
    Dict
        Generated configuration dictionary

    Requirements: 1.5, 7.1, 7.4
    """
    log_info("=" * 80)
    log_info("GENERATING CALIBRATED TRIGGER CONFIGURATION")
    log_info("=" * 80)

    # ========================================================================
    # Step 1: Analyze historical data distributions
    # ========================================================================
    log_info("\nStep 1: Analyzing historical data distributions...")

    rainfall_stats = analyze_rainfall_distribution(df_chirps)
    drought_stats = analyze_drought_indicators(df_chirps)
    vegetation_stats = analyze_vegetation_stress(df_ndvi)

    # Generate threshold analysis report
    analysis_results = {"rainfall": rainfall_stats, "drought": drought_stats, "vegetation": vegetation_stats}

    report_path = generate_threshold_report(analysis_results)
    log_info(f"✓ Threshold analysis report saved: {report_path}")

    # ========================================================================
    # Step 2: Calibrate trigger thresholds
    # ========================================================================
    log_info("\nStep 2: Calibrating trigger thresholds...")

    # Calibrate flood triggers
    log_info("\n--- Calibrating Flood Triggers ---")
    flood_thresholds = calibrate_flood_triggers(rainfall_stats, df_chirps, target_trigger_rate=target_flood_rate)

    # Calibrate drought triggers
    log_info("\n--- Calibrating Drought Triggers ---")
    drought_thresholds = calibrate_drought_triggers(drought_stats, df_chirps, target_trigger_rate=target_drought_rate)

    # Calibrate crop failure triggers
    log_info("\n--- Calibrating Crop Failure Triggers ---")
    crop_failure_thresholds = calibrate_crop_failure_triggers(
        vegetation_stats, df_ndvi, target_trigger_rate=target_crop_failure_rate
    )

    # ========================================================================
    # Step 3: Simulate trigger rates with calibrated thresholds
    # ========================================================================
    log_info("\nStep 3: Simulating trigger rates...")

    simulation_results = simulate_trigger_rates(
        df_chirps,
        df_ndvi,
        {
            "flood_triggers": flood_thresholds,
            "drought_triggers": drought_thresholds,
            "crop_failure_triggers": crop_failure_thresholds,
        },
    )

    # ========================================================================
    # Step 4: Build configuration dictionary
    # ========================================================================
    log_info("\nStep 4: Building configuration dictionary...")

    # Get data period from dataframes
    data_period_start = str(df_chirps["year"].min()) if "year" in df_chirps.columns else "unknown"
    data_period_end = str(df_chirps["year"].max()) if "year" in df_chirps.columns else "unknown"
    data_period = f"{data_period_start}-01-01 to {data_period_end}-12-31"

    calibration_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    config = {
        "version": "1.0.0",
        "calibration_date": calibration_date,
        "data_period": data_period,
        "target_trigger_rates": {
            "flood": target_flood_rate,
            "drought": target_drought_rate,
            "crop_failure": target_crop_failure_rate,
        },
        "flood_triggers": {
            "daily_rainfall_mm": {
                "threshold": round(flood_thresholds["daily_rainfall_threshold"], 2),
                "rationale": f"Calibrated to 99th percentile of daily rainfall. Achieved trigger rate: {flood_thresholds['achieved_trigger_rate']*100:.1f}%",
                "data_source": f"CHIRPS {data_period}",
                "calibration_date": calibration_date,
            },
            "rainfall_7day_mm": {
                "threshold": round(flood_thresholds["rainfall_7day_threshold"], 2),
                "rationale": f"Calibrated to 97th percentile of 7-day rainfall. Sustained heavy rainfall leading to flooding",
                "data_source": f"CHIRPS {data_period}",
                "calibration_date": calibration_date,
            },
            "heavy_rain_days_7day": {
                "threshold": flood_thresholds["heavy_rain_days_required"],
                "heavy_rain_definition_mm": round(flood_thresholds["heavy_rain_day_threshold"], 2),
                "rationale": f"Multiple heavy rain days in 7-day window indicate flood risk. Heavy rain day defined as >{flood_thresholds['heavy_rain_day_threshold']:.1f}mm",
                "calibration_date": calibration_date,
            },
            "rainfall_percentile": {
                "threshold": flood_thresholds["rainfall_percentile_threshold"],
                "rationale": "Extreme rainfall events (top 1% of historical distribution)",
            },
        },
        "drought_triggers": {
            "spi_30day": {
                "threshold": drought_thresholds["spi_30day_threshold"],
                "rationale": f"Severe drought classification per WMO standards. Achieved trigger rate: {drought_thresholds['achieved_trigger_rate']*100:.1f}%",
                "data_source": f"Calculated from CHIRPS {data_period}",
                "calibration_date": calibration_date,
            },
            "consecutive_dry_days": {
                "wet_season_threshold": drought_thresholds["consecutive_dry_days_wet_season"],
                "dry_season_threshold": drought_thresholds["consecutive_dry_days_dry_season"],
                "dry_day_definition_mm": drought_thresholds["dry_day_definition_mm"],
                "rationale": f"Extended dry periods during growing season. Wet season (Oct-May): {drought_thresholds['consecutive_dry_days_wet_season']} days, Dry season (Jun-Sep): {drought_thresholds['consecutive_dry_days_dry_season']} days",
                "calibration_date": calibration_date,
            },
            "rainfall_deficit_pct": {
                "threshold": 50,
                "rationale": "Significant deficit from climatological normal indicates drought conditions",
                "calibration_date": calibration_date,
            },
        },
        "crop_failure_triggers": {
            "vci_threshold": {
                "critical": crop_failure_thresholds["vci_threshold"],
                "severe": 35,
                "duration_days": crop_failure_thresholds["vci_duration_days"],
                "rationale": f"FAO crop stress thresholds. VCI < {crop_failure_thresholds['vci_threshold']} for {crop_failure_thresholds['vci_duration_days']} days indicates crop failure risk. Achieved trigger rate: {crop_failure_thresholds['achieved_trigger_rate']*100:.1f}%",
                "data_source": f"MODIS NDVI {data_period}",
                "calibration_date": calibration_date,
            },
            "ndvi_anomaly_std": {
                "threshold": crop_failure_thresholds["ndvi_anomaly_threshold_std"],
                "duration_days": crop_failure_thresholds["ndvi_anomaly_duration_days"],
                "rationale": f"Significant vegetation stress. NDVI anomaly < {crop_failure_thresholds['ndvi_anomaly_threshold_std']:.1f} std for {crop_failure_thresholds['ndvi_anomaly_duration_days']} days",
                "calibration_date": calibration_date,
            },
            "crop_failure_risk_score": {
                "threshold": crop_failure_thresholds["crop_failure_risk_threshold"],
                "rationale": f"High probability of crop failure based on composite indicators. Risk score > {crop_failure_thresholds['crop_failure_risk_threshold']}",
                "calibration_date": calibration_date,
            },
        },
        "regional_adjustments": {
            "enabled": False,
            "regions": {
                "coastal": {
                    "flood_multiplier": 1.2,
                    "drought_multiplier": 1.0,
                    "crop_failure_multiplier": 1.0,
                    "description": "Coastal zone with higher rainfall and flood risk",
                },
                "highland": {
                    "flood_multiplier": 1.0,
                    "drought_multiplier": 0.8,
                    "crop_failure_multiplier": 0.9,
                    "description": "Highland zone with cooler temperatures and more consistent rainfall",
                },
                "lowland": {
                    "flood_multiplier": 1.1,
                    "drought_multiplier": 1.1,
                    "crop_failure_multiplier": 1.1,
                    "description": "Lowland zone with variable rainfall patterns",
                },
            },
        },
        "calibration_metadata": {
            "flood_achieved_rate": round(flood_thresholds["achieved_trigger_rate"], 4),
            "drought_achieved_rate": round(drought_thresholds["achieved_trigger_rate"], 4),
            "crop_failure_achieved_rate": round(crop_failure_thresholds["achieved_trigger_rate"], 4),
            "flood_confidence": round(flood_thresholds["confidence_score"], 4),
            "drought_confidence": round(drought_thresholds["confidence_score"], 4),
            "crop_failure_confidence": round(crop_failure_thresholds["confidence_score"], 4),
            "simulation_results": simulation_results,
        },
    }

    # ========================================================================
    # Step 5: Validate configuration
    # ========================================================================
    log_info("\nStep 5: Validating generated configuration...")

    is_valid, errors = validate_trigger_config(config)

    if not is_valid:
        log_error("Generated configuration is invalid!")
        for error in errors:
            log_error(f"  - {error}")
        raise ValueError("Generated configuration failed validation")

    log_info("✓ Configuration validation passed")

    # ========================================================================
    # Step 6: Save configuration to YAML file
    # ========================================================================
    log_info(f"\nStep 6: Saving configuration to: {output_path}")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        # Write header comment
        f.write("# " + "=" * 76 + "\n")
        f.write("# Insurance Trigger Thresholds Configuration\n")
        f.write("# " + "=" * 76 + "\n")
        f.write("# This configuration file was automatically generated by the calibration\n")
        f.write("# process using historical climate data.\n")
        f.write("#\n")
        f.write(f"# Generated: {calibration_date}\n")
        f.write(f"# Data Period: {data_period}\n")
        f.write("#\n")
        f.write("# Achieved Trigger Rates:\n")
        f.write(
            f"#   Flood: {flood_thresholds['achieved_trigger_rate']*100:.2f}% (target: {target_flood_rate*100:.1f}%)\n"
        )
        f.write(
            f"#   Drought: {drought_thresholds['achieved_trigger_rate']*100:.2f}% (target: {target_drought_rate*100:.1f}%)\n"
        )
        f.write(
            f"#   Crop Failure: {crop_failure_thresholds['achieved_trigger_rate']*100:.2f}% (target: {target_crop_failure_rate*100:.1f}%)\n"
        )
        f.write("#\n")
        f.write("# Requirements: 7.1, 7.4\n")
        f.write("# " + "=" * 76 + "\n\n")

        # Write YAML content
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

    log_info(f"✓ Configuration saved successfully")

    # ========================================================================
    # Step 7: Print summary
    # ========================================================================
    log_info("\n" + "=" * 80)
    log_info("CALIBRATION COMPLETE")
    log_info("=" * 80)
    log_info(f"\nConfiguration file: {output_path}")
    log_info(f"Version: {config['version']}")
    log_info(f"Calibration date: {calibration_date}")
    log_info(f"Data period: {data_period}")
    log_info(f"\nAchieved Trigger Rates:")
    log_info(
        f"  Flood: {flood_thresholds['achieved_trigger_rate']*100:.2f}% (target: {target_flood_rate*100:.1f}%, confidence: {flood_thresholds['confidence_score']:.3f})"
    )
    log_info(
        f"  Drought: {drought_thresholds['achieved_trigger_rate']*100:.2f}% (target: {target_drought_rate*100:.1f}%, confidence: {drought_thresholds['confidence_score']:.3f})"
    )
    log_info(
        f"  Crop Failure: {crop_failure_thresholds['achieved_trigger_rate']*100:.2f}% (target: {target_crop_failure_rate*100:.1f}%, confidence: {crop_failure_thresholds['confidence_score']:.3f})"
    )
    log_info("\n" + "=" * 80)

    return config


def main():
    """
    Main function to run the calibration workflow.
    """
    try:
        # Load historical data
        df_chirps, df_ndvi = load_historical_data()

        # Generate calibrated configuration
        generate_calibrated_config(df_chirps, df_ndvi, output_path="configs/trigger_thresholds.yaml")

        log_info("\n✓ Calibration workflow completed successfully!")

    except Exception as e:
        log_error(f"\n✗ Calibration workflow failed: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    main()
