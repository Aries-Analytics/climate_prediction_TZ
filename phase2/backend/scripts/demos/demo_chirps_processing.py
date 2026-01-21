"""
Demo: CHIRPS Processing with Drought and Flood Indicators

This script demonstrates the new CHIRPS processing capabilities for insurance triggers.
"""

import numpy as np
import pandas as pd

from modules.ingestion.chirps_ingestion import fetch_chirps_data
from modules.processing.process_chirps import process


def demo_chirps_processing():
    """Demonstrate CHIRPS processing with real data."""
    print("\n" + "=" * 80)
    print(" CHIRPS PROCESSING DEMO: Drought & Flood Indicators for Insurance")
    print("=" * 80)

    # Step 1: Fetch CHIRPS data
    print("\n[STEP 1] Fetching CHIRPS rainfall data...")
    print("-" * 80)
    raw_data = fetch_chirps_data(dry_run=False, start_year=2020, end_year=2023)
    print(f"✓ Fetched {len(raw_data)} monthly records")
    print(f"✓ Date range: {raw_data['year'].min()}-{raw_data['year'].max()}")
    print(f"✓ Raw columns: {list(raw_data.columns)}")

    # Step 2: Process the data
    print("\n[STEP 2] Processing with drought/flood indicators...")
    print("-" * 80)
    processed_data = process(raw_data)
    print(f"✓ Processed {len(processed_data)} records")
    print(f"✓ Created {len(processed_data.columns)} total features")

    # Step 3: Show feature categories
    print("\n[STEP 3] Feature Categories Created:")
    print("-" * 80)

    print("\n📊 Rolling Statistics:")
    rolling_features = [c for c in processed_data.columns if "day" in c and "rainfall" in c]
    for feat in rolling_features[:5]:
        print(f"   • {feat}")

    print("\n🌵 Drought Indicators:")
    drought_features = [c for c in processed_data.columns if "drought" in c or "spi" in c or "dry" in c]
    for feat in drought_features[:8]:
        print(f"   • {feat}")

    print("\n🌊 Flood Indicators:")
    flood_features = [c for c in processed_data.columns if "flood" in c or "heavy" in c or "extreme" in c]
    for feat in flood_features[:8]:
        print(f"   • {feat}")

    print("\n📈 Anomaly Indicators:")
    anomaly_features = [c for c in processed_data.columns if "anomaly" in c or "percentile" in c]
    for feat in anomaly_features:
        print(f"   • {feat}")

    print("\n🎯 Insurance Triggers:")
    trigger_features = [c for c in processed_data.columns if "trigger" in c or "severity" in c]
    for feat in trigger_features:
        print(f"   • {feat}")

    # Step 4: Analyze triggers
    print("\n[STEP 4] Insurance Trigger Analysis:")
    print("-" * 80)

    total_months = len(processed_data)
    drought_triggers = processed_data["drought_trigger"].sum()
    flood_triggers = processed_data["flood_trigger"].sum()
    any_triggers = processed_data["any_trigger"].sum()

    print(f"\n📊 Trigger Statistics:")
    print(f"   • Total months analyzed: {total_months}")
    print(f"   • Drought triggers: {drought_triggers} ({drought_triggers/total_months*100:.1f}%)")
    print(f"   • Flood triggers: {flood_triggers} ({flood_triggers/total_months*100:.1f}%)")
    print(f"   • Any trigger: {any_triggers} ({any_triggers/total_months*100:.1f}%)")

    # Step 5: Show extreme events
    print("\n[STEP 5] Extreme Events Detected:")
    print("-" * 80)

    # Worst drought
    worst_drought = processed_data.nlargest(1, "drought_severity")
    if not worst_drought.empty:
        row = worst_drought.iloc[0]
        print(f"\n🌵 Worst Drought Event:")
        print(f"   • Date: {int(row['year'])}-{int(row['month']):02d}")
        print(f"   • Severity: {row['drought_severity']:.2f}")
        print(f"   • Consecutive dry days: {row['consecutive_dry_days']:.0f}")
        print(f"   • SPI (30-day): {row['spi_30day']:.2f}")
        print(f"   • Rainfall: {row['rainfall_mm']:.1f} mm")
        print(f"   • Trigger activated: {'YES ✓' if row['drought_trigger'] else 'NO'}")

    # Worst flood
    worst_flood = processed_data.nlargest(1, "flood_risk_score")
    if not worst_flood.empty:
        row = worst_flood.iloc[0]
        print(f"\n🌊 Worst Flood Event:")
        print(f"   • Date: {int(row['year'])}-{int(row['month']):02d}")
        print(f"   • Flood risk score: {row['flood_risk_score']:.1f}/100")
        print(f"   • Daily rainfall: {row['rainfall_mm']:.1f} mm")
        print(f"   • 7-day rainfall: {row['rainfall_7day']:.1f} mm")
        print(f"   • Heavy rain days (7d): {row['heavy_rain_days_7day']:.0f}")
        print(f"   • Trigger activated: {'YES ✓' if row['flood_trigger'] else 'NO'}")

    # Step 6: Show sample data
    print("\n[STEP 6] Sample of Processed Data:")
    print("-" * 80)

    sample_cols = [
        "year",
        "month",
        "rainfall_mm",
        "consecutive_dry_days",
        "spi_30day",
        "drought_severity",
        "flood_risk_score",
        "drought_trigger",
        "flood_trigger",
    ]

    print("\n" + processed_data[sample_cols].head(10).to_string(index=False))

    # Step 7: Insurance payout simulation
    print("\n[STEP 7] Insurance Payout Simulation:")
    print("-" * 80)

    # Simulate payout calculation
    base_payout = 1000  # USD per trigger event

    # Drought payouts (severity-based)
    drought_events = processed_data[processed_data["drought_trigger"] == 1]
    drought_payouts = drought_events["drought_severity"] * base_payout
    total_drought_payout = drought_payouts.sum()

    # Flood payouts (risk-score-based)
    flood_events = processed_data[processed_data["flood_trigger"] == 1]
    flood_payouts = (flood_events["flood_risk_score"] / 100) * base_payout
    total_flood_payout = flood_payouts.sum()

    total_payout = total_drought_payout + total_flood_payout

    print(f"\n💰 Payout Summary (Base: ${base_payout} per event):")
    print(f"   • Drought payouts: ${total_drought_payout:,.2f} ({len(drought_events)} events)")
    print(f"   • Flood payouts: ${total_flood_payout:,.2f} ({len(flood_events)} events)")
    print(f"   • Total payouts: ${total_payout:,.2f}")
    print(f"   • Average payout per trigger: ${total_payout/max(any_triggers, 1):,.2f}")

    # Calculate premium (simplified)
    expected_loss_ratio = 0.70  # 70% of premiums go to payouts
    required_premium = total_payout / expected_loss_ratio / total_months

    print(f"\n📊 Premium Calculation (70% loss ratio):")
    print(f"   • Required monthly premium: ${required_premium:,.2f}")
    print(f"   • Annual premium: ${required_premium * 12:,.2f}")

    print("\n" + "=" * 80)
    print(" ✓ DEMO COMPLETE")
    print("=" * 80)

    return processed_data


if __name__ == "__main__":
    try:
        processed_data = demo_chirps_processing()

        # Save sample output
        output_file = "outputs/processed/chirps_demo_output.csv"
        sample_cols = [
            "year",
            "month",
            "rainfall_mm",
            "rainfall_30day",
            "consecutive_dry_days",
            "spi_30day",
            "drought_severity",
            "flood_risk_score",
            "drought_trigger",
            "flood_trigger",
            "drought_trigger_confidence",
            "flood_trigger_confidence",
        ]
        processed_data[sample_cols].to_csv(output_file, index=False)
        print(f"\n💾 Sample output saved to: {output_file}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
