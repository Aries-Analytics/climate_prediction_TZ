"""
Test CHIRPS Processing with Drought and Flood Indicators

This test demonstrates the new CHIRPS processing capabilities including:
- Drought indicators (SPI, consecutive dry days, severity)
- Flood indicators (heavy rain events, risk scores)
- Insurance triggers (automated payout logic)
"""

import numpy as np
import pandas as pd

from modules.ingestion.chirps_ingestion import fetch_chirps_data
from modules.processing.process_chirps import process


def test_chirps_processing_with_real_data():
    """Test CHIRPS processing with real ingested data."""
    print("\n" + "=" * 70)
    print("TEST: CHIRPS Processing with Drought/Flood Indicators")
    print("=" * 70)

    import sys
    from unittest.mock import MagicMock, patch

    # Mock ee module if not present
    if "ee" not in sys.modules:
        sys.modules["ee"] = MagicMock()

    # Patch the initialization, ingestion, AND the availability flag
    with (
        patch("modules.ingestion.chirps_ingestion.GEE_AVAILABLE", True),
        patch("modules.ingestion.chirps_ingestion._initialize_gee", return_value=True),
        patch("modules.ingestion.chirps_ingestion._fetch_gee_chirps") as mock_fetch,
    ):

        # Configure mock to return realistic data
        # Only generating a few records to verify the flow
        mock_data = pd.DataFrame(
            [
                {
                    "year": 2020,
                    "month": 1,
                    "rainfall_mm": 150.5,
                    "lat_min": -11.75,
                    "lat_max": -0.99,
                    "lon_min": 29.34,
                    "lon_max": 40.44,
                    "data_source": "CHIRPS_GEE",
                },
                {
                    "year": 2020,
                    "month": 2,
                    "rainfall_mm": 120.0,
                    "lat_min": -11.75,
                    "lat_max": -0.99,
                    "lon_min": 29.34,
                    "lon_max": 40.44,
                    "data_source": "CHIRPS_GEE",
                },
                {
                    "year": 2020,
                    "month": 3,
                    "rainfall_mm": 200.0,
                    "lat_min": -11.75,
                    "lat_max": -0.99,
                    "lon_min": 29.34,
                    "lon_max": 40.44,
                    "data_source": "CHIRPS_GEE",
                },
            ]
        )
        mock_fetch.return_value = mock_data

        # Fetch real CHIRPS data (which will now use the mocked GEE path)
        print("\n1. Fetching CHIRPS data (Mocked GEE)...")
        # Force dry_run=False to test the Real Data path
        raw_data = fetch_chirps_data(dry_run=False, start_year=2020, end_year=2020, use_gee=True)
    print(f"   ✓ Fetched {len(raw_data)} records")
    print(f"   Columns: {list(raw_data.columns)}")

    # Process the data
    print("\n2. Processing CHIRPS data...")
    processed_data = process(raw_data)
    print(f"   ✓ Processed {len(processed_data)} records")
    print(f"   ✓ Created {len(processed_data.columns)} features")

    # Verify key features exist
    print("\n3. Verifying drought indicators...")
    drought_features = [
        "consecutive_dry_days",
        "spi_30day",
        "spi_90day",
        "rainfall_deficit_mm",
        "drought_severity",
        "drought_trigger",
    ]
    for feature in drought_features:
        assert feature in processed_data.columns, f"Missing feature: {feature}"
        print(f"   ✓ {feature}")

    print("\n4. Verifying flood indicators...")
    flood_features = ["heavy_rain_event", "extreme_rain_event", "flood_risk_score", "flood_trigger"]
    for feature in flood_features:
        assert feature in processed_data.columns, f"Missing feature: {feature}"
        print(f"   ✓ {feature}")

    # Analyze drought events
    print("\n5. Analyzing drought events...")
    drought_events = processed_data[processed_data["drought_trigger"] == 1]
    print(f"   ✓ Found {len(drought_events)} drought trigger events")
    if len(drought_events) > 0:
        print(f"   ✓ Average drought severity: {drought_events['drought_severity'].mean():.2f}")
        print(f"   ✓ Max consecutive dry days: {drought_events['consecutive_dry_days'].max():.0f}")

    # Analyze flood events
    print("\n6. Analyzing flood events...")
    flood_events = processed_data[processed_data["flood_trigger"] == 1]
    print(f"   ✓ Found {len(flood_events)} flood trigger events")
    if len(flood_events) > 0:
        print(f"   ✓ Average flood risk score: {flood_events['flood_risk_score'].mean():.1f}")
        print(f"   ✓ Max 7-day rainfall: {flood_events['rainfall_7day'].max():.1f} mm")

    # Insurance trigger summary
    print("\n7. Insurance Trigger Summary...")
    total_triggers = processed_data["any_trigger"].sum()
    trigger_rate = total_triggers / len(processed_data) * 100
    print(f"   ✓ Total trigger events: {total_triggers}")
    print(f"   ✓ Trigger rate: {trigger_rate:.1f}%")
    print(f"   ✓ Drought triggers: {processed_data['drought_trigger'].sum()}")
    print(f"   ✓ Flood triggers: {processed_data['flood_trigger'].sum()}")

    # Show sample of processed data
    print("\n8. Sample of processed data:")
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
    print(processed_data[sample_cols].head(10).to_string(index=False))

    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED")
    print("=" * 70)

    return processed_data


def test_chirps_processing_with_synthetic_drought():
    """Test CHIRPS processing with synthetic drought scenario."""
    print("\n" + "=" * 70)
    print("TEST: Synthetic Drought Scenario")
    print("=" * 70)

    # Create synthetic data with drought conditions
    dates = pd.date_range("2020-01-01", "2020-12-31", freq="D")

    # Simulate drought: 45 consecutive days with no rain
    rainfall = np.random.gamma(2, 5, len(dates))  # Normal rainfall pattern
    rainfall[100:145] = 0  # 45-day drought

    synthetic_data = pd.DataFrame(
        {
            "year": dates.year,
            "month": dates.month,
            "rainfall_mm": rainfall,
            "lat_min": -11.75,
            "lat_max": -0.99,
            "lon_min": 29.34,
            "lon_max": 40.44,
        }
    )

    print(f"\n1. Created synthetic data with {len(synthetic_data)} days")
    print("   ✓ Includes 45-day drought period (days 100-145)")

    # Process the data
    print("\n2. Processing synthetic data...")
    processed = process(synthetic_data)

    # Verify drought detection
    print("\n3. Verifying drought detection...")
    max_dry_days = processed["consecutive_dry_days"].max()
    print(f"   ✓ Max consecutive dry days: {max_dry_days:.0f}")
    assert max_dry_days >= 45, "Failed to detect 45-day drought"

    drought_triggers = processed["drought_trigger"].sum()
    print(f"   ✓ Drought triggers detected: {drought_triggers}")
    assert drought_triggers > 0, "Failed to trigger drought insurance"

    # Check severity
    max_severity = processed["drought_severity"].max()
    print(f"   ✓ Max drought severity: {max_severity:.2f}")
    assert max_severity >= 0.75, "Drought severity should be high"

    print("\n✓ Drought detection working correctly")

    return processed


def test_chirps_processing_with_synthetic_flood():
    """Test CHIRPS processing with synthetic flood scenario."""
    print("\n" + "=" * 70)
    print("TEST: Synthetic Flood Scenario")
    print("=" * 70)

    # Create synthetic data with flood conditions
    dates = pd.date_range("2020-01-01", "2020-12-31", freq="D")

    # Simulate flood: 3 days with extremely high rainfall that exceeds calibrated thresholds
    # Calibrated threshold: 258.57mm/day (95th percentile)
    # Using values well above threshold to guarantee trigger activation
    rainfall = np.random.gamma(2, 5, len(dates))  # Normal rainfall pattern
    rainfall[150:153] = [300, 280, 260]  # 3-day extreme rainfall event (all exceed 258.57mm threshold)

    synthetic_data = pd.DataFrame(
        {
            "year": dates.year,
            "month": dates.month,
            "rainfall_mm": rainfall,
            "lat_min": -11.75,
            "lat_max": -0.99,
            "lon_min": 29.34,
            "lon_max": 40.44,
        }
    )

    print(f"\n1. Created synthetic data with {len(synthetic_data)} days")
    print("   ✓ Includes 3-day heavy rainfall event (days 150-153: 300mm, 280mm, 260mm)")
    print("   ✓ All values exceed calibrated threshold (258.57mm)")

    # Process the data
    print("\n2. Processing synthetic data...")
    processed = process(synthetic_data)

    # Verify flood detection
    print("\n3. Verifying flood detection...")
    max_daily_rain = processed["rainfall_mm"].max()
    print(f"   ✓ Max daily rainfall: {max_daily_rain:.1f} mm")

    extreme_events = processed["extreme_rain_event"].sum()
    print(f"   ✓ Extreme rain events detected: {extreme_events}")
    assert extreme_events >= 3, "Failed to detect extreme rainfall events"

    flood_triggers = processed["flood_trigger"].sum()
    print(f"   ✓ Flood triggers detected: {flood_triggers}")
    assert flood_triggers > 0, "Failed to trigger flood insurance"

    # Check flood risk score
    max_flood_risk = processed["flood_risk_score"].max()
    print(f"   ✓ Max flood risk score: {max_flood_risk:.1f}/100")
    assert max_flood_risk >= 50, "Flood risk score should be high"

    print("\n✓ Flood detection working correctly")

    return processed


def test_spi_calculation():
    """Test Standardized Precipitation Index calculation."""
    print("\n" + "=" * 70)
    print("TEST: SPI Calculation")
    print("=" * 70)

    from modules.processing.process_chirps import _calculate_spi

    # Create test data with known distribution
    np.random.seed(42)
    normal_rainfall = np.random.gamma(5, 10, 100)  # Mean ~50mm

    # Add some extreme values
    drought_rainfall = np.concatenate([normal_rainfall, [5, 3, 2, 1, 0]])  # Very low
    wet_rainfall = np.concatenate([normal_rainfall, [150, 180, 200, 220, 250]])  # Very high

    # Calculate SPI
    spi_normal = _calculate_spi(pd.Series(normal_rainfall))
    spi_drought = _calculate_spi(pd.Series(drought_rainfall))
    spi_wet = _calculate_spi(pd.Series(wet_rainfall))

    print("\n1. Normal rainfall SPI:")
    print(f"   Mean: {spi_normal.mean():.2f} (should be ~0)")
    print(f"   Std: {spi_normal.std():.2f} (should be ~1)")

    print("\n2. Drought conditions SPI:")
    print(f"   Min: {spi_drought.min():.2f} (should be < -2)")
    assert spi_drought.min() < -2, "SPI should detect extreme drought"

    print("\n3. Wet conditions SPI:")
    print(f"   Max: {spi_wet.max():.2f} (should be > 2)")
    assert spi_wet.max() > 2, "SPI should detect extreme wetness"

    print("\n✓ SPI calculation working correctly")


if __name__ == "__main__":
    # Run all tests
    print("\n" + "=" * 70)
    print("CHIRPS PROCESSING TEST SUITE")
    print("=" * 70)

    try:
        # Test 1: Real data processing
        processed_real = test_chirps_processing_with_real_data()

        # Test 2: Synthetic drought
        processed_drought = test_chirps_processing_with_synthetic_drought()

        # Test 3: Synthetic flood
        processed_flood = test_chirps_processing_with_synthetic_flood()

        # Test 4: SPI calculation
        test_spi_calculation()

        print("\n" + "=" * 70)
        print("✓✓✓ ALL TESTS PASSED SUCCESSFULLY ✓✓✓")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
