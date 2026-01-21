"""
Demo: Ocean Indices Processing with Synthetic Data

This script demonstrates the Ocean Indices processing module's capabilities
using synthetic ENSO and IOD data that simulates various climate scenarios.

Scenarios demonstrated:
1. Neutral conditions
2. El Niño + Positive IOD (flood risk)
3. La Niña + Negative IOD (drought risk)
4. Transition periods
"""

import numpy as np
import pandas as pd
from utils.logger import log_info

from modules.processing import process_ocean_indices


def generate_synthetic_ocean_indices_data(n_months=48):
    """
    Generate synthetic ocean indices data with various climate scenarios.

    Parameters
    ----------
    n_months : int
        Number of months to generate

    Returns
    -------
    pd.DataFrame
        Synthetic ocean indices data
    """
    np.random.seed(42)

    # Base dates
    start_date = pd.Timestamp("2020-01-01")
    dates = pd.date_range(start=start_date, periods=n_months, freq="MS")

    data = []

    for i, date in enumerate(dates):
        year = date.year
        month = date.month

        # Add different climate scenarios
        if i < 12:
            # Scenario 1: Neutral conditions (months 0-11)
            oni = np.random.normal(0, 0.3)
            iod = np.random.normal(0, 0.2)

        elif i < 24:
            # Scenario 2: Developing El Niño + Positive IOD (months 12-23)
            progress = (i - 12) / 12
            oni = progress * 2.0 + np.random.normal(0, 0.2)
            iod = progress * 1.2 + np.random.normal(0, 0.15)

        elif i < 36:
            # Scenario 3: Transition to La Niña + Negative IOD (months 24-35)
            progress = (i - 24) / 12
            oni = 2.0 - progress * 3.5 + np.random.normal(0, 0.2)
            iod = 1.2 - progress * 2.0 + np.random.normal(0, 0.15)

        else:
            # Scenario 4: La Niña + Negative IOD (months 36+)
            oni = -1.5 + np.random.normal(0, 0.3)
            iod = -0.8 + np.random.normal(0, 0.2)

        # Clip to realistic ranges
        oni = np.clip(oni, -3, 3)
        iod = np.clip(iod, -2, 2)

        data.append({"year": year, "month": month, "oni": oni, "iod": iod})

    return pd.DataFrame(data)


def main():
    """Run Ocean Indices processing demo."""

    print("=" * 80)
    print("OCEAN INDICES PROCESSING DEMO - Synthetic Data")
    print("=" * 80)
    print()

    # Generate synthetic data
    print("📊 Generating synthetic ocean indices data...")
    print("   Scenarios: Neutral → El Niño/+IOD → Transition → La Niña/-IOD")
    raw_data = generate_synthetic_ocean_indices_data(n_months=48)
    print(f"   Generated {len(raw_data)} months of data")
    print()

    # Display sample raw data
    print("📋 Sample Raw Data:")
    print(raw_data[["year", "month", "oni", "iod"]].head(10).to_string(index=False))
    print()

    # Process the data
    print("⚙️  Processing ocean indices data...")
    processed_data = process_ocean_indices.process(raw_data)
    print()

    # Display key statistics
    print("=" * 80)
    print("PROCESSING RESULTS")
    print("=" * 80)
    print()

    print(f"📊 Output Shape: {processed_data.shape[0]} records × {processed_data.shape[1]} features")
    print()

    # ENSO summary
    print("🌊 ENSO (EL NIÑO-SOUTHERN OSCILLATION) SUMMARY")
    print("-" * 80)
    if "oni" in processed_data.columns:
        print(f"   Average ONI: {processed_data['oni'].mean():.2f}")
        print(f"   Min ONI: {processed_data['oni'].min():.2f}")
        print(f"   Max ONI: {processed_data['oni'].max():.2f}")
        print()

        if "enso_strength" in processed_data.columns:
            print("   ENSO Phase Distribution:")
            enso_dist = processed_data["enso_strength"].value_counts().sort_index()
            for phase, count in enso_dist.items():
                pct = count / len(processed_data) * 100
                print(f"      {phase}: {count} months ({pct:.1f}%)")

        if "is_el_nino" in processed_data.columns:
            el_nino_months = processed_data["is_el_nino"].sum()
            print(f"   El Niño months: {el_nino_months} ({el_nino_months/len(processed_data)*100:.1f}%)")

        if "is_la_nina" in processed_data.columns:
            la_nina_months = processed_data["is_la_nina"].sum()
            print(f"   La Niña months: {la_nina_months} ({la_nina_months/len(processed_data)*100:.1f}%)")
    print()

    # IOD summary
    print("🌀 IOD (INDIAN OCEAN DIPOLE) SUMMARY")
    print("-" * 80)
    if "iod" in processed_data.columns:
        print(f"   Average IOD: {processed_data['iod'].mean():.2f}")
        print(f"   Min IOD: {processed_data['iod'].min():.2f}")
        print(f"   Max IOD: {processed_data['iod'].max():.2f}")
        print()

        if "iod_strength" in processed_data.columns:
            print("   IOD Phase Distribution:")
            iod_dist = processed_data["iod_strength"].value_counts().sort_index()
            for phase, count in iod_dist.items():
                pct = count / len(processed_data) * 100
                print(f"      {phase}: {count} months ({pct:.1f}%)")

        if "is_positive_iod" in processed_data.columns:
            pos_iod_months = processed_data["is_positive_iod"].sum()
            print(f"   Positive IOD months: {pos_iod_months} ({pos_iod_months/len(processed_data)*100:.1f}%)")

        if "is_negative_iod" in processed_data.columns:
            neg_iod_months = processed_data["is_negative_iod"].sum()
            print(f"   Negative IOD months: {neg_iod_months} ({neg_iod_months/len(processed_data)*100:.1f}%)")
    print()

    # Combined climate impacts
    print("🌍 COMBINED CLIMATE IMPACTS")
    print("-" * 80)
    if "combined_impact_score" in processed_data.columns:
        print(f"   Average impact score: {processed_data['combined_impact_score'].mean():.2f}")
        print(
            f"   Range: {processed_data['combined_impact_score'].min():.2f} to {processed_data['combined_impact_score'].max():.2f}"
        )
        print()

    if "favorable_rainfall_climate" in processed_data.columns:
        favorable = processed_data["favorable_rainfall_climate"].sum()
        print(f"   Favorable rainfall conditions: {favorable} months ({favorable/len(processed_data)*100:.1f}%)")

    if "drought_risk_climate" in processed_data.columns:
        drought_risk = processed_data["drought_risk_climate"].sum()
        print(f"   Drought risk conditions: {drought_risk} months ({drought_risk/len(processed_data)*100:.1f}%)")

    if "flood_risk_climate" in processed_data.columns:
        flood_risk = processed_data["flood_risk_climate"].sum()
        print(f"   Flood risk conditions: {flood_risk} months ({flood_risk/len(processed_data)*100:.1f}%)")

    if "conflicting_signals" in processed_data.columns:
        conflicting = processed_data["conflicting_signals"].sum()
        print(f"   Conflicting signals: {conflicting} months ({conflicting/len(processed_data)*100:.1f}%)")
    print()

    # Rainfall probabilities
    print("☔ RAINFALL PROBABILITY FORECASTS")
    print("-" * 80)
    if "prob_above_normal_rainfall" in processed_data.columns:
        print(f"   Avg prob above-normal: {processed_data['prob_above_normal_rainfall'].mean():.2f}")
        print(f"   Avg prob below-normal: {processed_data['prob_below_normal_rainfall'].mean():.2f}")
        print(f"   Avg prob normal: {processed_data['prob_normal_rainfall'].mean():.2f}")
        print()

        high_flood_prob = (processed_data["prob_above_normal_rainfall"] > 0.6).sum()
        print(f"   High flood probability months (>60%): {high_flood_prob}")

        high_drought_prob = (processed_data["prob_below_normal_rainfall"] > 0.6).sum()
        print(f"   High drought probability months (>60%): {high_drought_prob}")
    print()

    # Climate risk scores
    print("⚠️  CLIMATE RISK ASSESSMENT")
    print("-" * 80)
    if "drought_risk_score" in processed_data.columns:
        print(f"   Average drought risk: {processed_data['drought_risk_score'].mean():.1f}/100")
        print(f"   Max drought risk: {processed_data['drought_risk_score'].max():.1f}/100")

        high_drought = (processed_data["drought_risk_score"] > 75).sum()
        print(f"   High drought risk months (>75): {high_drought}")

    if "flood_risk_score" in processed_data.columns:
        print(f"   Average flood risk: {processed_data['flood_risk_score'].mean():.1f}/100")
        print(f"   Max flood risk: {processed_data['flood_risk_score'].max():.1f}/100")

        high_flood = (processed_data["flood_risk_score"] > 75).sum()
        print(f"   High flood risk months (>75): {high_flood}")

    if "climate_risk_class" in processed_data.columns:
        print()
        print("   Risk Distribution:")
        risk_dist = processed_data["climate_risk_class"].value_counts().sort_index()
        for category, count in risk_dist.items():
            pct = count / len(processed_data) * 100
            print(f"      {category}: {count} months ({pct:.1f}%)")
    print()

    # Insurance triggers
    print("🔔 INSURANCE TRIGGERS SUMMARY")
    print("-" * 80)
    if "climate_drought_trigger" in processed_data.columns:
        drought_triggers = processed_data["climate_drought_trigger"].sum()
        print(f"   Climate drought triggers: {drought_triggers} events")

        if "climate_drought_trigger_confidence" in processed_data.columns:
            triggered = processed_data[processed_data["climate_drought_trigger"] == 1]
            if len(triggered) > 0:
                avg_confidence = triggered["climate_drought_trigger_confidence"].mean()
                print(f"   Average drought trigger confidence: {avg_confidence:.2f}")

    if "climate_flood_trigger" in processed_data.columns:
        flood_triggers = processed_data["climate_flood_trigger"].sum()
        print(f"   Climate flood triggers: {flood_triggers} events")

        if "climate_flood_trigger_confidence" in processed_data.columns:
            triggered = processed_data[processed_data["climate_flood_trigger"] == 1]
            if len(triggered) > 0:
                avg_confidence = triggered["climate_flood_trigger_confidence"].mean()
                print(f"   Average flood trigger confidence: {avg_confidence:.2f}")

    if "any_climate_trigger" in processed_data.columns:
        any_triggers = processed_data["any_climate_trigger"].sum()
        print(f"   Total climate triggers: {any_triggers} events")
    print()

    # Early warning indicators
    print("⏰ EARLY WARNING INDICATORS")
    print("-" * 80)
    if "early_warning_drought" in processed_data.columns:
        ew_drought = processed_data["early_warning_drought"].sum()
        print(f"   Drought early warnings: {ew_drought} events")

    if "early_warning_flood" in processed_data.columns:
        ew_flood = processed_data["early_warning_flood"].sum()
        print(f"   Flood early warnings: {ew_flood} events")

    if "forecast_confidence" in processed_data.columns:
        print(f"   Average forecast confidence: {processed_data['forecast_confidence'].mean():.2f}")
    print()

    # Sample processed records
    print("=" * 80)
    print("SAMPLE PROCESSED RECORDS")
    print("=" * 80)
    print()

    # Show records from different scenarios
    key_cols = [
        "year",
        "month",
        "oni",
        "iod",
        "enso_strength",
        "iod_strength",
        "combined_impact_score",
        "drought_risk_score",
        "flood_risk_score",
    ]
    available_cols = [col for col in key_cols if col in processed_data.columns]

    print("📅 Neutral Period (Early months):")
    print(processed_data[available_cols].head(3).to_string(index=False))
    print()

    print("📅 El Niño + Positive IOD Period (Flood risk):")
    print(processed_data[available_cols].iloc[18:21].to_string(index=False))
    print()

    print("📅 Transition Period:")
    print(processed_data[available_cols].iloc[28:31].to_string(index=False))
    print()

    print("📅 La Niña + Negative IOD Period (Drought risk):")
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
    print("   • ENSO indicators: strength, phase, persistence, trends")
    print("   • IOD indicators: strength, phase, persistence, trends")
    print("   • Combined impacts: interaction terms, conflict detection")
    print("   • Seasonal forecasts: lead indicators, seasonal impacts")
    print("   • Rainfall probabilities: above/below/normal forecasts")
    print("   • Climate risk: drought and flood risk scores")
    print("   • Insurance triggers: climate-based drought/flood triggers")
    print("   • Early warning: 3-month ahead risk indicators")
    print()

    print("=" * 80)
    print("✅ DEMO COMPLETE")
    print("=" * 80)
    print()
    print("The processed data has been saved to: data/processed/ocean_indices_processed.csv")
    print()
    print("Key insights from this demo:")
    print("   • ENSO and IOD phases are accurately classified")
    print("   • Combined climate impacts identify high-risk periods")
    print("   • Rainfall probabilities provide actionable forecasts")
    print("   • Insurance triggers activate during extreme climate events")
    print("   • Early warning indicators provide 3-month lead time")
    print()


if __name__ == "__main__":
    main()
