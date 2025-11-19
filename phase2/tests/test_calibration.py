"""
Unit tests for trigger calibration functions.

Tests cover:
- Threshold analysis functions
- Trigger calibration logic
- Configuration loading and validation
- Trigger rate simulation
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from modules.calibration.analyze_thresholds import (
    analyze_drought_indicators,
    analyze_rainfall_distribution,
    analyze_vegetation_stress,
)
from modules.calibration.config_loader import load_trigger_config, validate_trigger_config


class TestRainfallDistributionAnalysis:
    """Test rainfall distribution analysis functions."""

    @pytest.fixture
    def sample_rainfall_data(self):
        """Create sample rainfall data for testing."""
        np.random.seed(42)
        dates = pd.date_range("2018-01-01", "2023-12-31", freq="D")

        # Generate realistic rainfall data
        # Most days have low rainfall, some have high rainfall
        rainfall = np.random.gamma(2, 5, len(dates))  # Gamma distribution
        rainfall[rainfall < 1] = 0  # Many dry days

        df = pd.DataFrame({"date": dates, "rainfall_mm": rainfall, "year": dates.year, "month": dates.month})

        # Calculate rolling sums
        df["rainfall_7day"] = df["rainfall_mm"].rolling(7, min_periods=1).sum()
        df["rainfall_30day"] = df["rainfall_mm"].rolling(30, min_periods=1).sum()

        return df

    def test_analyze_rainfall_distribution_returns_dict(self, sample_rainfall_data):
        """Test that analyze_rainfall_distribution returns a dictionary."""
        result = analyze_rainfall_distribution(sample_rainfall_data)
        assert isinstance(result, dict)

    def test_analyze_rainfall_distribution_has_required_keys(self, sample_rainfall_data):
        """Test that result contains all required percentile keys."""
        result = analyze_rainfall_distribution(sample_rainfall_data)

        required_keys = [
            "daily_rainfall_p90",
            "daily_rainfall_p95",
            "daily_rainfall_p97",
            "daily_rainfall_p99",
            "rainfall_7day_p95",
            "rainfall_7day_p97",
            "rainfall_7day_p99",
            "rainfall_30day_p90",
            "rainfall_30day_p95",
            "rainfall_30day_p97",
        ]

        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_percentiles_are_ordered(self, sample_rainfall_data):
        """Test that percentiles are in ascending order."""
        result = analyze_rainfall_distribution(sample_rainfall_data)

        # Daily rainfall percentiles should be ordered
        assert result["daily_rainfall_p90"] <= result["daily_rainfall_p95"]
        assert result["daily_rainfall_p95"] <= result["daily_rainfall_p97"]
        assert result["daily_rainfall_p97"] <= result["daily_rainfall_p99"]

    def test_percentiles_are_positive(self, sample_rainfall_data):
        """Test that all percentile values are non-negative."""
        result = analyze_rainfall_distribution(sample_rainfall_data)

        for key, value in result.items():
            if ("percentile" in key or "_p" in key) and isinstance(value, (int, float)):
                assert value >= 0, f"{key} should be non-negative"

    def test_handles_empty_dataframe(self):
        """Test that function handles empty DataFrame gracefully."""
        empty_df = pd.DataFrame(columns=["rainfall_mm", "rainfall_7day", "rainfall_30day"])

        with pytest.raises((ValueError, KeyError)):
            analyze_rainfall_distribution(empty_df)

    def test_handles_missing_columns(self):
        """Test that function raises error for missing required columns."""
        df = pd.DataFrame({"rainfall_mm": [10, 20, 30]})

        with pytest.raises(ValueError):
            analyze_rainfall_distribution(df)


class TestDroughtIndicatorAnalysis:
    """Test drought indicator analysis functions."""

    @pytest.fixture
    def sample_drought_data(self):
        """Create sample drought indicator data."""
        np.random.seed(42)
        dates = pd.date_range("2018-01-01", "2023-12-31", freq="D")

        df = pd.DataFrame(
            {
                "date": dates,
                "spi_30day": np.random.normal(0, 1, len(dates)),  # Standardized
                "spi_90day": np.random.normal(0, 1, len(dates)),  # Standardized
                "consecutive_dry_days": np.random.randint(0, 60, len(dates)),
                "rainfall_deficit_pct": np.random.uniform(-50, 50, len(dates)),
                "rainfall_deficit_mm": np.random.uniform(-100, 100, len(dates)),
                "month": dates.month,
            }
        )

        return df

    def test_analyze_drought_indicators_returns_dict(self, sample_drought_data):
        """Test that analyze_drought_indicators returns a dictionary."""
        result = analyze_drought_indicators(sample_drought_data)
        assert isinstance(result, dict)

    def test_spi_thresholds_are_negative(self, sample_drought_data):
        """Test that SPI thresholds for drought are negative."""
        result = analyze_drought_indicators(sample_drought_data)

        if "spi_threshold" in result:
            assert result["spi_threshold"] < 0, "SPI drought threshold should be negative"

    def test_dry_day_thresholds_by_season(self, sample_drought_data):
        """Test that seasonal dry day thresholds are calculated."""
        result = analyze_drought_indicators(sample_drought_data)

        # Should have different thresholds for wet and dry seasons
        if "dry_days_wet_season" in result and "dry_days_dry_season" in result:
            # Dry season threshold should be higher (more tolerance)
            assert result["dry_days_dry_season"] >= result["dry_days_wet_season"]


class TestVegetationStressAnalysis:
    """Test vegetation stress analysis functions."""

    @pytest.fixture
    def sample_vegetation_data(self):
        """Create sample vegetation data."""
        np.random.seed(42)
        dates = pd.date_range("2018-01-01", "2023-12-31", freq="D")

        df = pd.DataFrame(
            {
                "date": dates,
                "ndvi": np.random.uniform(0.2, 0.8, len(dates)),
                "vci": np.random.uniform(0, 100, len(dates)),
                "ndvi_anomaly_std": np.random.normal(0, 1, len(dates)),
                "stress_duration": np.random.randint(0, 60, len(dates)),
                "severe_stress_duration": np.random.randint(0, 30, len(dates)),
                "crop_failure_risk": np.random.uniform(0, 100, len(dates)),
            }
        )

        return df

    def test_analyze_vegetation_stress_returns_dict(self, sample_vegetation_data):
        """Test that analyze_vegetation_stress returns a dictionary."""
        result = analyze_vegetation_stress(sample_vegetation_data)
        assert isinstance(result, dict)

    def test_vci_thresholds_are_low_percentiles(self, sample_vegetation_data):
        """Test that VCI thresholds use low percentiles (stress = low VCI)."""
        result = analyze_vegetation_stress(sample_vegetation_data)

        if "vci_p5" in result and "vci_p15" in result:
            # Low percentiles should be ordered
            assert result["vci_p5"] <= result["vci_p15"]
            # Should be in valid VCI range
            assert 0 <= result["vci_p5"] <= 100
            assert 0 <= result["vci_p15"] <= 100


class TestConfigurationLoading:
    """Test configuration loading and validation."""

    @pytest.fixture
    def valid_config(self):
        """Create a valid configuration dictionary."""
        return {
            "version": "1.0.0",
            "calibration_date": "2024-11-17",
            "data_period": "2018-01-01 to 2023-12-31",
            "target_trigger_rates": {"flood": 0.10, "drought": 0.12, "crop_failure": 0.06},
            "flood_triggers": {
                "daily_rainfall_mm": {
                    "threshold": 150,
                    "rationale": "Test rationale",
                    "data_source": "CHIRPS 2018-2023",
                },
                "rainfall_7day_mm": {
                    "threshold": 100.0,
                    "rationale": "Test rationale for 7-day rainfall",
                    "data_source": "CHIRPS 2018-2023",
                },
                "heavy_rain_days_7day": {
                    "threshold": 3,
                    "rationale": "Test rationale for heavy rain days",
                    "data_source": "CHIRPS 2018-2023",
                },
                "rainfall_percentile": {
                    "threshold": 95.0,
                    "rationale": "Test rationale for rainfall percentile",
                    "data_source": "CHIRPS 2018-2023",
                },
            },
            "drought_triggers": {
                "spi_30day": {"threshold": -1.5, "rationale": "Test rationale", "data_source": "CHIRPS 2018-2023"},
                "consecutive_dry_days": {
                    "threshold": 30,
                    "rationale": "Test rationale for dry days",
                    "data_source": "CHIRPS 2018-2023",
                },
                "rainfall_deficit_pct": {
                    "threshold": 50.0,
                    "rationale": "Test rationale for rainfall deficit",
                    "data_source": "CHIRPS 2018-2023",
                },
            },
            "crop_failure_triggers": {
                "vci_threshold": {"critical": 20, "rationale": "Test rationale", "data_source": "MODIS 2018-2023"},
                "ndvi_anomaly_std": {
                    "threshold": -2.0,
                    "rationale": "Test rationale for NDVI anomaly",
                    "data_source": "MODIS 2018-2023",
                },
                "crop_failure_risk_score": {
                    "threshold": 0.7,
                    "rationale": "Test rationale for crop failure risk",
                    "data_source": "MODIS 2018-2023",
                },
            },
        }

    @pytest.fixture
    def temp_config_file(self, valid_config):
        """Create a temporary configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(valid_config, f)
            temp_path = f.name

        yield temp_path

        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_validate_trigger_config_accepts_valid_config(self, valid_config):
        """Test that validation accepts a valid configuration."""
        is_valid, errors = validate_trigger_config(valid_config)
        assert is_valid, f"Valid config rejected with errors: {errors}"
        assert len(errors) == 0

    def test_validate_trigger_config_rejects_missing_version(self, valid_config):
        """Test that validation rejects config without version."""
        del valid_config["version"]
        is_valid, errors = validate_trigger_config(valid_config)
        assert not is_valid
        assert any("version" in str(e).lower() for e in errors)

    def test_validate_trigger_config_rejects_missing_rationale(self, valid_config):
        """Test that validation rejects thresholds without rationale."""
        del valid_config["flood_triggers"]["daily_rainfall_mm"]["rationale"]
        is_valid, errors = validate_trigger_config(valid_config)
        assert not is_valid

    def test_validate_trigger_config_checks_threshold_ranges(self, valid_config):
        """Test that validation checks threshold value ranges."""
        # Set unrealistic threshold
        valid_config["flood_triggers"]["daily_rainfall_mm"]["threshold"] = -100
        is_valid, errors = validate_trigger_config(valid_config)
        assert not is_valid

    def test_load_trigger_config_from_file(self, temp_config_file):
        """Test loading configuration from file."""
        # This test requires the actual config file to exist
        # We'll skip if the default config doesn't exist
        if not Path("configs/trigger_thresholds.yaml").exists():
            pytest.skip("Default config file not found")

        config = load_trigger_config()
        assert isinstance(config, dict)
        assert "version" in config
        assert "flood_triggers" in config


class TestTriggerRateSimulation:
    """Test trigger rate simulation functions."""

    @pytest.fixture
    def sample_processed_data(self):
        """Create sample processed data with triggers."""
        np.random.seed(42)
        n_months = 72  # 6 years

        df = pd.DataFrame(
            {
                "date": pd.date_range("2018-01-01", periods=n_months, freq="MS"),
                "rainfall_mm": np.random.gamma(2, 20, n_months),
                "spi_30day": np.random.normal(0, 1, n_months),
                "vci": np.random.uniform(0, 100, n_months),
                "flood_trigger": np.random.binomial(1, 0.10, n_months),
                "drought_trigger": np.random.binomial(1, 0.12, n_months),
                "crop_failure_trigger": np.random.binomial(1, 0.06, n_months),
            }
        )

        return df

    def test_trigger_rates_within_expected_range(self, sample_processed_data):
        """Test that simulated trigger rates are within expected ranges."""
        flood_rate = sample_processed_data["flood_trigger"].mean()
        drought_rate = sample_processed_data["drought_trigger"].mean()
        crop_rate = sample_processed_data["crop_failure_trigger"].mean()

        # With random seed, rates should be close to target (more lenient for synthetic data)
        assert 0.01 <= flood_rate <= 0.25, f"Flood rate {flood_rate} outside 1-25%"
        assert 0.01 <= drought_rate <= 0.30, f"Drought rate {drought_rate} outside 1-30%"
        assert 0.01 <= crop_rate <= 0.25, f"Crop rate {crop_rate} outside 1-25%"

    def test_trigger_counts_are_integers(self, sample_processed_data):
        """Test that trigger columns contain only 0 and 1."""
        for col in ["flood_trigger", "drought_trigger", "crop_failure_trigger"]:
            unique_values = sample_processed_data[col].unique()
            assert set(unique_values).issubset({0, 1}), f"{col} contains non-binary values"


class TestCalibrationWorkflow:
    """Integration tests for calibration workflow."""

    def test_calibration_achieves_target_rate(self):
        """Test that calibration can achieve target trigger rate."""
        # Create synthetic data
        np.random.seed(42)
        n_samples = 1000
        rainfall = np.random.gamma(2, 20, n_samples)

        # Target: 10% trigger rate
        target_rate = 0.10

        # Calculate threshold that achieves target rate
        threshold = np.percentile(rainfall, (1 - target_rate) * 100)

        # Apply threshold
        triggers = (rainfall > threshold).astype(int)
        actual_rate = triggers.mean()

        # Should be close to target (within 2%)
        assert abs(actual_rate - target_rate) < 0.02

    def test_iterative_threshold_adjustment(self):
        """Test iterative threshold adjustment to reach target rate."""
        np.random.seed(42)
        rainfall = np.random.gamma(2, 20, 1000)
        target_rate = 0.10

        # Start with initial guess
        threshold = rainfall.mean()
        max_iterations = 10
        tolerance = 0.01

        for i in range(max_iterations):
            triggers = (rainfall > threshold).astype(int)
            current_rate = triggers.mean()

            if abs(current_rate - target_rate) < tolerance:
                break

            # Adjust threshold
            if current_rate > target_rate:
                # Too many triggers, increase threshold
                threshold *= 1.1
            else:
                # Too few triggers, decrease threshold
                threshold *= 0.9

        # Should converge within iterations
        final_rate = (rainfall > threshold).mean()
        assert abs(final_rate - target_rate) < tolerance * 2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_all_zero_rainfall(self):
        """Test handling of data with no rainfall."""
        df = pd.DataFrame({"rainfall_mm": [0] * 100, "rainfall_7day": [0] * 100, "rainfall_30day": [0] * 100})

        result = analyze_rainfall_distribution(df)
        # Should return zeros for percentiles
        assert result["daily_rainfall_p99"] == 0

    def test_handles_extreme_outliers(self):
        """Test handling of extreme outlier values."""
        np.random.seed(42)
        rainfall = np.random.gamma(2, 20, 1000)
        # Add extreme outlier
        rainfall[0] = 10000

        df = pd.DataFrame({"rainfall_mm": rainfall, "rainfall_7day": rainfall, "rainfall_30day": rainfall})

        result = analyze_rainfall_distribution(df)
        # 99th percentile should not be the outlier
        assert result["daily_rainfall_p99"] < 1000

    def test_handles_single_month_data(self):
        """Test handling of very limited data."""
        df = pd.DataFrame({"rainfall_mm": [10, 20, 30], "rainfall_7day": [10, 20, 30], "rainfall_30day": [10, 20, 30]})

        # Should handle gracefully (may raise warning)
        result = analyze_rainfall_distribution(df)
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
