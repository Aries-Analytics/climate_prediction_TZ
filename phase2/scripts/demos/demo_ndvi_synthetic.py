"""
Demo: NDVI Processing with Synthetic Data

This script demonstrates the NDVI processing module's capabilities
using synthetic vegetation data that simulates various stress scenarios.

Scenarios demonstrated:
1. Normal vegetation growth cycle
2. Drought-induced vegetation stress
3. Crop failure scenario
4. Recovery after stress
"""

import numpy as np
import pandas as pd
from utils.logger import log_info

from modules.processing import process_ndvi


def generate_synthetic_ndvi_data(n_months=36):
    """
    Generate synthetic NDVI data with various vegetation scenarios.

    Parameters
    ----------
    n_months : int
        Number of months to generate

    Returns
    -------
    pd.DataFrame
        Synthetic NDVI data
    """
    np.random.seed(42)

    # Base dates
    start_date = pd.Timestamp("2021-01-01")
    dates = pd.date_range(start=start_date, periods=n_months, freq="MS")

    data = []

    for i, date in enumerate(dates):
        year = date.year
        month = date.month

        # Seasonal NDVI pattern (higher in rainy seasons)
        seasonal_base = 0.5 + 0.2 * np.sin(2 * np.pi * month / 12)

        # Add different scenarios
        if i < 12:
            # Scenario 1: Normal vegetation (months 0-11)
            ndvi = seasonal_base + np.random.normal(0, 0.05)

        elif i < 18:
            # Scenario 2: Drought stress (months 12-17)
            stress_factor = (i - 12) / 6  # Increasing stress
            ndvi = seasonal_base * (1 - 0.5 * stress_factor) + np.random.normal(0, 0.03)

        elif i < 24:
            # Scenario 3: Severe drought / crop failure (months 18-23)
            ndvi = 0.15 + np.random.normal(0, 0.02)

        else:
            # Scenario 4: Recovery (months 24+)
            recovery_factor = min(1.0, (i - 24) / 12)
            ndvi = (0.15 + (seasonal_base - 0.15) * recovery_factor) + np.random.normal(0, 0.04)

        # Clip to valid NDVI range
        ndvi = np.clip(ndvi, -0.1, 0.95)

        data.append(
            {
                "year": year,
                "month": month,
                "ndvi": ndvi,
                "lat_min": -6.0,
                "lat_max": -5.0,
                "lon_min": 35.0,
                "lon_max": 36.0,
            }
        )

    return pd.DataFrame(data)


def main():
    """Run NDVI processing demo."""

    print("=" * 80)
    print("NDVI PROCESSING DEMO - Synthetic Data")
    print("=" * 80)
    print()

    # Generate synthetic data
    print("📊 Generating synthetic NDVI data...")
    print("   Scenarios: Normal growth → Drought stress → Crop failure → Recovery")
    raw_data = generate_synthetic_ndvi_data(n_months=36)
    print(f"   Generated {len(raw_data)} months of data")
    print()

    # Display sample raw data
    print("📋 Sample Raw Data:")
    print(raw_data[["year", "month", "ndvi"]].head(10).to_string(index=False))
    print()

    # Process the data
    print("⚙️  Processing NDVI data...")
    processed_data = process_ndvi.process(raw_data)
    print()

    # Display key statistics
    print("=" * 80)
    print("PROCESSING RESULTS")
    print("=" * 80)
    print()

    print(f"📊 Output Shape: {processed_data.shape[0]} records × {processed_data.shape[1]} features")
    print()

    # Vegetation health summary
    print("🌱 VEGETATION HEALTH SUMMARY")
    print("-" * 80)
    if "vci" in processed_data.columns:
        print(f"   Average VCI: {processed_data['vci'].mean():.1f}")
        print(f"   Min VCI: {processed_data['vci'].min():.1f}")
        print(f"   Max VCI: {processed_data['vci'].max():.1f}")
        print()
        print("   VCI Distribution:")
        vci_dist = processed_data["vci_class"].value_counts().sort_index()
        for category, count in vci_dist.items():
            pct = count / len(processed_data) * 100
            print(f"      {category}: {count} months ({pct:.1f}%)")
    print()

    # Drought stress summary
    print("🌵 DROUGHT STRESS SUMMARY")
    print("-" * 80)
    if "is_stressed" in processed_data.columns:
        stressed_months = processed_data["is_stressed"].sum()
        print(f"   Stressed months: {stressed_months} ({stressed_months/len(processed_data)*100:.1f}%)")

        if "stress_duration" in processed_data.columns:
            max_duration = processed_data["stress_duration"].max()
            print(f"   Max consecutive stress: {max_duration} months")

        if "drought_stress_severity" in processed_data.columns:
            avg_severity = processed_data[processed_data["is_stressed"] == 1]["drought_stress_severity"].mean()
            print(f"   Average stress severity: {avg_severity:.2f}")
    print()

    # Crop failure risk summary
    print("⚠️  CROP FAILURE RISK SUMMARY")
    print("-" * 80)
    if "crop_failure_risk" in processed_data.columns:
        print(f"   Average risk: {processed_data['crop_failure_risk'].mean():.1f}/100")
        print(f"   Max risk: {processed_data['crop_failure_risk'].max():.1f}/100")

        high_risk = (processed_data["crop_failure_risk"] > 75).sum()
        print(f"   High risk months (>75): {high_risk} ({high_risk/len(processed_data)*100:.1f}%)")

        if "crop_failure_risk_class" in processed_data.columns:
            print()
            print("   Risk Distribution:")
            risk_dist = processed_data["crop_failure_risk_class"].value_counts().sort_index()
            for category, count in risk_dist.items():
                pct = count / len(processed_data) * 100
                print(f"      {category}: {count} months ({pct:.1f}%)")
    print()

    # Insurance triggers summary
    print("🔔 INSURANCE TRIGGERS SUMMARY")
    print("-" * 80)
    if "crop_failure_trigger" in processed_data.columns:
        triggers = processed_data["crop_failure_trigger"].sum()
        print(f"   Crop failure triggers: {triggers} events")

        if "crop_failure_trigger_confidence" in processed_data.columns:
            triggered = processed_data[processed_data["crop_failure_trigger"] == 1]
            if len(triggered) > 0:
                avg_confidence = triggered["crop_failure_trigger_confidence"].mean()
                print(f"   Average trigger confidence: {avg_confidence:.2f}")

    if "moderate_stress_trigger" in processed_data.columns:
        mod_triggers = processed_data["moderate_stress_trigger"].sum()
        print(f"   Moderate stress triggers: {mod_triggers} events")

    if "severe_stress_trigger" in processed_data.columns:
        sev_triggers = processed_data["severe_stress_trigger"].sum()
        print(f"   Severe stress triggers: {sev_triggers} events")
    print()

    # Sample processed records
    print("=" * 80)
    print("SAMPLE PROCESSED RECORDS")
    print("=" * 80)
    print()

    # Show records from different scenarios
    key_cols = ["year", "month", "ndvi", "vci", "crop_failure_risk", "crop_failure_trigger", "stress_duration"]
    available_cols = [col for col in key_cols if col in processed_data.columns]

    print("📅 Normal Period (Early months):")
    print(processed_data[available_cols].head(3).to_string(index=False))
    print()

    print("📅 Drought Stress Period (Middle months):")
    print(processed_data[available_cols].iloc[15:18].to_string(index=False))
    print()

    print("📅 Crop Failure Period (Peak stress):")
    print(processed_data[available_cols].iloc[20:23].to_string(index=False))
    print()

    print("📅 Recovery Period (Late months):")
    print(processed_data[available_cols].tail(3).to_string(index=False))
    print()

    # Feature summary
    print("=" * 80)
    print("FEATURES CREATED")
    print("=" * 80)
    print()
    print(f"Total features: {len(processed_data.columns)}")
    print()
    print("Feature categories:")
    print("   • Temporal statistics: rolling means, trends, volatility")
    print("   • Anomalies: deviations from climatology, percentiles")
    print("   • Vegetation Condition Index (VCI): normalized health metric")
    print("   • Drought stress: stress indicators, duration, severity")
    print("   • Growth stages: peak greenness, growing season, senescence")
    print("   • Crop failure risk: comprehensive risk scoring")
    print("   • Insurance triggers: crop failure, moderate/severe stress")
    print()

    print("=" * 80)
    print("✅ DEMO COMPLETE")
    print("=" * 80)
    print()
    print("The processed data has been saved to: data/processed/ndvi_processed.csv")
    print()
    print("Key insights from this demo:")
    print("   • VCI effectively identifies vegetation stress periods")
    print("   • Crop failure risk increases during prolonged drought")
    print("   • Insurance triggers activate during severe stress events")
    print("   • Recovery indicators track vegetation bounce-back")
    print()


if __name__ == "__main__":
    main()
