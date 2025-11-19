"""
Unit tests for preprocessing pipeline.

Tests lag features, rolling statistics, normalization, and temporal splitting.
"""

import numpy as np
import pandas as pd
import pytest
from preprocessing.preprocess import (
    create_interaction_features,
    create_lag_features,
    create_rolling_features,
    handle_missing_values,
    load_and_validate_data,
    normalize_features,
    split_temporal_data,
    validate_schema,
)


@pytest.fixture
def sample_data():
    """Create sample climate data for testing."""
    np.random.seed(42)
    n_samples = 24  # 2 years of monthly data

    data = {
        "year": [2020] * 12 + [2021] * 12,
        "month": list(range(1, 13)) * 2,
        "temperature": np.random.uniform(20, 35, n_samples),
        "rainfall": np.random.uniform(0, 200, n_samples),
        "ndvi": np.random.uniform(0.2, 0.8, n_samples),
        "oni": np.random.uniform(-2, 2, n_samples),
        "iod": np.random.uniform(-1, 1, n_samples),
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_data_with_missing():
    """Create sample data with missing values."""
    np.random.seed(42)
    n_samples = 24

    data = {
        "year": [2020] * 12 + [2021] * 12,
        "month": list(range(1, 13)) * 2,
        "temperature": np.random.uniform(20, 35, n_samples),
        "rainfall": np.random.uniform(0, 200, n_samples),
    }

    df = pd.DataFrame(data)
    # Add missing values
    df.loc[5:7, "temperature"] = np.nan  # 3 consecutive missing
    df.loc[15, "rainfall"] = np.nan  # 1 missing

    return df


# ============================================================================
# Test Data Loading and Validation
# ============================================================================


def test_validate_schema_success(sample_data):
    """Test schema validation with valid data."""
    assert validate_schema(sample_data, ["year", "month"]) is True


def test_validate_schema_missing_columns(sample_data):
    """Test schema validation fails with missing columns."""
    with pytest.raises(ValueError, match="Missing columns"):
        validate_schema(sample_data, ["year", "month", "nonexistent_column"])


def test_load_and_validate_data_file_not_found():
    """Test loading fails with non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_and_validate_data("nonexistent_file.csv")


# ============================================================================
# Test Lag Features
# ============================================================================


def test_create_lag_features_basic(sample_data):
    """Test lag feature creation with known inputs."""
    lags = [1, 3]
    result = create_lag_features(sample_data, ["temperature"], lags)

    # Check lag columns exist
    assert "temperature_lag_1" in result.columns
    assert "temperature_lag_3" in result.columns

    # Check lag values are correct
    assert pd.isna(result.loc[0, "temperature_lag_1"])  # First value should be NaN
    assert result.loc[1, "temperature_lag_1"] == result.loc[0, "temperature"]
    assert result.loc[3, "temperature_lag_3"] == result.loc[0, "temperature"]


def test_create_lag_features_preserves_original(sample_data):
    """Test that lag features don't modify original columns."""
    original_temp = sample_data["temperature"].copy()
    result = create_lag_features(sample_data, ["temperature"], [1])

    pd.testing.assert_series_equal(result["temperature"], original_temp)


def test_create_lag_features_multiple_columns(sample_data):
    """Test lag features for multiple columns."""
    lags = [1, 6]
    result = create_lag_features(sample_data, ["temperature", "rainfall"], lags)

    assert "temperature_lag_1" in result.columns
    assert "temperature_lag_6" in result.columns
    assert "rainfall_lag_1" in result.columns
    assert "rainfall_lag_6" in result.columns


# ============================================================================
# Test Rolling Statistics
# ============================================================================


def test_create_rolling_features_basic(sample_data):
    """Test rolling statistics calculations."""
    windows = [3]
    result = create_rolling_features(sample_data, ["temperature"], windows)

    # Check rolling columns exist
    assert "temperature_rolling_mean_3" in result.columns
    assert "temperature_rolling_std_3" in result.columns

    # Check rolling mean calculation
    # For first 3 values, rolling mean should be their average
    expected_mean = sample_data["temperature"].iloc[:3].mean()
    assert np.isclose(result.loc[2, "temperature_rolling_mean_3"], expected_mean)


def test_create_rolling_features_multiple_windows(sample_data):
    """Test rolling features with multiple window sizes."""
    windows = [3, 6]
    result = create_rolling_features(sample_data, ["temperature"], windows)

    assert "temperature_rolling_mean_3" in result.columns
    assert "temperature_rolling_mean_6" in result.columns
    assert "temperature_rolling_std_3" in result.columns
    assert "temperature_rolling_std_6" in result.columns


def test_create_rolling_features_std_calculation(sample_data):
    """Test rolling standard deviation is calculated correctly."""
    windows = [3]
    result = create_rolling_features(sample_data, ["temperature"], windows)

    # Check std calculation for first 3 values
    expected_std = sample_data["temperature"].iloc[:3].std()
    assert np.isclose(result.loc[2, "temperature_rolling_std_3"], expected_std)


# ============================================================================
# Test Interaction Features
# ============================================================================


def test_create_interaction_features_enso_rainfall(sample_data):
    """Test ENSO × rainfall interaction features."""
    result = create_interaction_features(sample_data)

    # Check that interaction columns were created
    interaction_cols = [col for col in result.columns if "_x_" in col and "oni" in col and "rainfall" in col]
    assert len(interaction_cols) > 0

    # Verify interaction calculation
    for col in interaction_cols:
        parts = col.split("_x_")
        if len(parts) == 2:
            col1, col2 = parts
            if col1 in result.columns and col2 in result.columns:
                expected = result[col1] * result[col2]
                pd.testing.assert_series_equal(result[col], expected, check_names=False)


def test_create_interaction_features_iod_ndvi(sample_data):
    """Test IOD × NDVI interaction features."""
    result = create_interaction_features(sample_data)

    # Check that IOD × NDVI interactions were created
    interaction_cols = [col for col in result.columns if "_x_" in col and "iod" in col and "ndvi" in col]
    assert len(interaction_cols) > 0


# ============================================================================
# Test Missing Value Handling
# ============================================================================


def test_handle_missing_values_forward_fill(sample_data_with_missing):
    """Test forward-fill imputation."""
    result = handle_missing_values(sample_data_with_missing, max_gap=2)

    # Check that single missing value was filled
    assert not pd.isna(result.loc[15, "rainfall"])

    # Check that gap of 3 was partially filled (max_gap=2)
    assert not pd.isna(result.loc[5, "temperature"])  # First in gap, filled
    assert not pd.isna(result.loc[6, "temperature"])  # Second in gap, filled
    assert pd.isna(result.loc[7, "temperature"])  # Third in gap, not filled (exceeds max_gap)


def test_handle_missing_values_preserves_non_missing(sample_data_with_missing):
    """Test that non-missing values are preserved."""
    original_values = sample_data_with_missing.loc[0:4, "temperature"].copy()
    result = handle_missing_values(sample_data_with_missing, max_gap=2)

    pd.testing.assert_series_equal(result.loc[0:4, "temperature"], original_values)


# ============================================================================
# Test Normalization
# ============================================================================


def test_normalize_features_basic(sample_data):
    """Test feature normalization produces correct statistics."""
    result, scaler_params = normalize_features(sample_data)

    # Check that temperature was normalized
    assert "temperature" in scaler_params
    assert "mean" in scaler_params["temperature"]
    assert "std" in scaler_params["temperature"]

    # Check that normalized values have mean ≈ 0 and std ≈ 1
    assert np.isclose(result["temperature"].mean(), 0, atol=1e-10)
    assert np.isclose(result["temperature"].std(), 1, atol=1e-10)


def test_normalize_features_excludes_year_month(sample_data):
    """Test that year and month are not normalized."""
    result, scaler_params = normalize_features(sample_data)

    # Year and month should not be in scaler params
    assert "year" not in scaler_params
    assert "month" not in scaler_params

    # Year and month should be unchanged
    pd.testing.assert_series_equal(result["year"], sample_data["year"])
    pd.testing.assert_series_equal(result["month"], sample_data["month"])


def test_normalize_features_custom_exclude(sample_data):
    """Test normalization with custom exclude list."""
    result, scaler_params = normalize_features(sample_data, exclude_cols=["year", "month", "temperature"])

    # Temperature should not be normalized
    assert "temperature" not in scaler_params
    pd.testing.assert_series_equal(result["temperature"], sample_data["temperature"])

    # Other columns should be normalized
    assert "rainfall" in scaler_params


# ============================================================================
# Test Temporal Data Splitting
# ============================================================================


def test_split_temporal_data_maintains_order(sample_data):
    """Test that temporal split maintains chronological order."""
    train, val, test = split_temporal_data(sample_data, train_pct=0.5, val_pct=0.25)

    # Check that splits are in chronological order
    assert train["year"].max() <= val["year"].min()
    assert val["year"].max() <= test["year"].max()


def test_split_temporal_data_correct_sizes(sample_data):
    """Test that split sizes match specified percentages."""
    train, val, test = split_temporal_data(sample_data, train_pct=0.7, val_pct=0.15)

    total_samples = len(sample_data)

    # Check that splits sum to total
    assert len(train) + len(val) + len(test) == total_samples

    # Check that train is approximately 70%
    assert abs(len(train) / total_samples - 0.7) < 0.1

    # Check that val is approximately 15%
    assert abs(len(val) / total_samples - 0.15) < 0.1


def test_split_temporal_data_no_overlap(sample_data):
    """Test that splits have no overlapping samples."""
    train, val, test = split_temporal_data(sample_data, train_pct=0.6, val_pct=0.2)

    # Check no index overlap
    train_indices = set(train.index)
    val_indices = set(val.index)
    test_indices = set(test.index)

    assert len(train_indices & val_indices) == 0
    assert len(train_indices & test_indices) == 0
    assert len(val_indices & test_indices) == 0


def test_split_temporal_data_covers_all_samples(sample_data):
    """Test that splits cover all original samples."""
    train, val, test = split_temporal_data(sample_data, train_pct=0.6, val_pct=0.2)

    total_split_samples = len(train) + len(val) + len(test)
    assert total_split_samples == len(sample_data)


# ============================================================================
# Integration Tests
# ============================================================================


def test_preprocessing_pipeline_integration(sample_data, tmp_path):
    """Test that preprocessing steps work together."""
    # Create lag features
    df = create_lag_features(sample_data, ["temperature"], [1])

    # Create rolling features
    df = create_rolling_features(df, ["temperature"], [3])

    # Create interactions
    df = create_interaction_features(df)

    # Handle missing values
    df = handle_missing_values(df, max_gap=2)

    # Normalize
    df, scaler_params = normalize_features(df)

    # Split
    train, val, test = split_temporal_data(df, train_pct=0.7, val_pct=0.15)

    # Verify final output
    assert len(train) > 0
    assert len(val) > 0
    assert len(test) > 0
    assert len(scaler_params) > 0
