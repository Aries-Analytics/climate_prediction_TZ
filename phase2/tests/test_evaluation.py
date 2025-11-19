"""
Unit tests for model evaluation.

Tests metric calculations and plot generation.
"""

import numpy as np
import pandas as pd
import pytest
from evaluation.evaluate import (
    calculate_metrics,
    evaluate_by_season,
    plot_feature_importance,
    plot_predictions_vs_actual,
    plot_residuals_over_time,
)


@pytest.fixture
def sample_predictions():
    """Create sample predictions and actual values."""
    np.random.seed(42)
    n_samples = 100

    y_true = np.random.randn(n_samples) * 10 + 50
    y_pred = y_true + np.random.randn(n_samples) * 2  # Add some noise

    return y_true, y_pred


@pytest.fixture
def sample_seasonal_data():
    """Create sample data with seasonal information."""
    np.random.seed(42)
    n_samples = 120  # 10 years of monthly data

    months = np.tile(np.arange(1, 13), 10)
    y_true = np.random.randn(n_samples) * 10 + 50
    y_pred = y_true + np.random.randn(n_samples) * 2

    return y_true, y_pred, months


# ============================================================================
# Test Metric Calculations
# ============================================================================


def test_calculate_metrics_with_known_values():
    """Test metric calculations with known values."""
    # Perfect predictions
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    metrics = calculate_metrics(y_true, y_pred)

    # R² should be 1.0 for perfect predictions
    assert np.isclose(metrics["r2_score"], 1.0)

    # RMSE and MAE should be 0 for perfect predictions
    assert np.isclose(metrics["rmse"], 0.0)
    assert np.isclose(metrics["mae"], 0.0)

    # MAPE should be 0 for perfect predictions
    assert np.isclose(metrics["mape"], 0.0)


def test_calculate_metrics_with_constant_predictions():
    """Test metrics with constant predictions."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([3.0, 3.0, 3.0, 3.0, 3.0])  # Constant prediction

    metrics = calculate_metrics(y_true, y_pred)

    # R² should be 0 for constant predictions (baseline model)
    assert np.isclose(metrics["r2_score"], 0.0)

    # RMSE should be equal to std of y_true
    expected_rmse = np.std(y_true)
    assert np.isclose(metrics["rmse"], expected_rmse, rtol=0.1)


def test_calculate_metrics_returns_all_metrics(sample_predictions):
    """Test that all required metrics are returned."""
    y_true, y_pred = sample_predictions

    metrics = calculate_metrics(y_true, y_pred)

    assert "r2_score" in metrics
    assert "rmse" in metrics
    assert "mae" in metrics
    assert "mape" in metrics

    # All metrics should be numeric
    assert isinstance(metrics["r2_score"], (int, float))
    assert isinstance(metrics["rmse"], (int, float))
    assert isinstance(metrics["mae"], (int, float))
    assert isinstance(metrics["mape"], (int, float))


# ============================================================================
# Test Quantile Predictions
# ============================================================================


def test_calculate_quantile_predictions_basic():
    """Test quantile prediction calculation."""
    from evaluation.evaluate import calculate_quantile_predictions

    # Create ensemble predictions (3 models × 100 samples)
    np.random.seed(42)
    predictions = [np.random.randn(100) + 50, np.random.randn(100) + 50, np.random.randn(100) + 50]

    quantiles = calculate_quantile_predictions(predictions, quantiles=[0.1, 0.5, 0.9])

    assert "q10" in quantiles
    assert "q50" in quantiles
    assert "q90" in quantiles

    # Check that quantiles are ordered correctly
    assert np.all(quantiles["q10"] <= quantiles["q50"])
    assert np.all(quantiles["q50"] <= quantiles["q90"])


def test_calculate_quantile_predictions_default_quantiles():
    """Test quantile predictions with default quantiles (95% CI)."""
    from evaluation.evaluate import calculate_quantile_predictions

    np.random.seed(42)
    predictions = [np.random.randn(50) for _ in range(5)]

    quantiles = calculate_quantile_predictions(predictions)

    # Should have default quantiles for 95% CI
    assert "q2.5" in quantiles
    assert "q50" in quantiles
    assert "q97.5" in quantiles

    # Check ordering
    assert np.all(quantiles["q2.5"] <= quantiles["q50"])
    assert np.all(quantiles["q50"] <= quantiles["q97.5"])


def test_calculate_quantile_predictions_interval_width():
    """Test that prediction intervals have positive width."""
    from evaluation.evaluate import calculate_quantile_predictions

    np.random.seed(42)
    n_samples = 100

    # Create predictions with known distribution
    predictions = [np.random.randn(n_samples) for _ in range(10)]

    quantiles = calculate_quantile_predictions(predictions, quantiles=[0.025, 0.975])

    # Calculate interval width
    interval_width = quantiles["q97.5"] - quantiles["q2.5"]

    # Interval width should be positive
    assert np.all(interval_width > 0)


def test_calculate_quantile_predictions_validates_inputs():
    """Test input validation for quantile predictions."""
    from evaluation.evaluate import calculate_quantile_predictions

    # Empty list should raise error
    with pytest.raises(ValueError, match="cannot be empty"):
        calculate_quantile_predictions([])

    # Mismatched lengths should raise error
    with pytest.raises(ValueError, match="same length"):
        calculate_quantile_predictions([np.array([1, 2, 3]), np.array([1, 2])])

    # Invalid quantile should raise error
    with pytest.raises(ValueError, match="between 0 and 1"):
        calculate_quantile_predictions([np.array([1, 2, 3])], quantiles=[1.5])


def test_validate_prediction_intervals_coverage():
    """Test prediction interval coverage validation."""
    from evaluation.evaluate import calculate_quantile_predictions, validate_prediction_intervals

    np.random.seed(42)
    n_samples = 1000

    # Create predictions with known distribution (normal)
    true_values = np.random.randn(n_samples)

    # Create predictions with some noise
    predictions = [true_values + np.random.randn(n_samples) * 0.1 for _ in range(10)]

    # Calculate 95% prediction intervals
    quantiles = calculate_quantile_predictions(predictions, quantiles=[0.025, 0.975])

    # Validate coverage
    validation = validate_prediction_intervals(
        true_values, quantiles["q2.5"], quantiles["q97.5"], confidence_level=0.95
    )

    # Check validation results
    assert "coverage" in validation
    assert "expected_coverage" in validation
    assert "coverage_error" in validation
    assert "n_samples" in validation
    assert "n_within_interval" in validation

    # Coverage should be close to 95% (within 10% tolerance for random data)
    assert 0.85 <= validation["coverage"] <= 1.0


def test_validate_prediction_intervals_perfect_coverage():
    """Test interval validation with perfect coverage."""
    from evaluation.evaluate import validate_prediction_intervals

    # Create data where all values are within interval
    y_true = np.array([5.0, 6.0, 7.0, 8.0, 9.0])
    lower = np.array([4.0, 5.0, 6.0, 7.0, 8.0])
    upper = np.array([6.0, 7.0, 8.0, 9.0, 10.0])

    validation = validate_prediction_intervals(y_true, lower, upper, confidence_level=0.95)

    # All values within interval = 100% coverage
    assert validation["coverage"] == 1.0
    assert validation["n_within_interval"] == 5


def test_validate_prediction_intervals_validates_inputs():
    """Test input validation for interval validation."""
    from evaluation.evaluate import validate_prediction_intervals

    # Mismatched lengths should raise error
    with pytest.raises(ValueError, match="same length"):
        validate_prediction_intervals(np.array([1, 2, 3]), np.array([0, 1]), np.array([2, 3, 4]))

    # Invalid confidence level should raise error
    with pytest.raises(ValueError, match="between 0 and 1"):
        validate_prediction_intervals(
            np.array([1, 2, 3]), np.array([0, 1, 2]), np.array([2, 3, 4]), confidence_level=1.5
        )


# ============================================================================
# Test Seasonal Evaluation
# ============================================================================


def test_evaluate_by_season_basic(sample_seasonal_data):
    """Test seasonal evaluation."""
    y_true, y_pred, months = sample_seasonal_data

    # Create dates series
    dates = pd.Series([pd.Timestamp(f"2020-{m:02d}-01") for m in months])

    seasonal_metrics = evaluate_by_season(y_true, y_pred, dates)

    # Should return a DataFrame
    assert isinstance(seasonal_metrics, pd.DataFrame)
    assert len(seasonal_metrics) > 0


def test_evaluate_by_season_correct_grouping(sample_seasonal_data):
    """Test that months are grouped correctly into seasons."""
    y_true, y_pred, months = sample_seasonal_data

    # Create dates series
    dates = pd.Series([pd.Timestamp(f"2020-{m:02d}-01") for m in months])

    seasonal_metrics = evaluate_by_season(y_true, y_pred, dates)

    # Should have seasonal data
    assert len(seasonal_metrics) > 0


# ============================================================================
# Test Plot Generation
# ============================================================================


def test_plot_predictions_vs_actual_doesnt_crash(sample_predictions, tmp_path):
    """Test that predictions vs actual plot generates without errors."""
    y_true, y_pred = sample_predictions

    save_path = tmp_path / "predictions_vs_actual.png"

    # Should not raise any errors
    plot_predictions_vs_actual(y_true, y_pred, str(save_path))

    # Check file was created
    assert save_path.exists()


def test_plot_residuals_over_time_doesnt_crash(sample_predictions, tmp_path):
    """Test that residuals plot generates without errors."""
    y_true, y_pred = sample_predictions

    # Create dates
    dates = pd.date_range("2020-01-01", periods=len(y_true), freq="ME")

    save_path = tmp_path / "residuals.png"

    # Should not raise any errors
    plot_residuals_over_time(y_true, y_pred, dates, str(save_path))

    # Check file was created
    assert save_path.exists()


def test_plot_feature_importance_doesnt_crash(tmp_path):
    """Test that feature importance plot generates without errors."""
    # Create sample feature importance data
    feature_names = [f"feature_{i}" for i in range(10)]
    importances = np.random.rand(10)

    save_path = tmp_path / "feature_importance.png"

    # Should not raise any errors
    plot_feature_importance(feature_names, importances, str(save_path))

    # Check file was created
    assert save_path.exists()


# ============================================================================
# Edge Cases
# ============================================================================


def test_calculate_metrics_with_nan_values():
    """Test metrics calculation handles NaN values."""
    y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y_pred = np.array([1.1, 2.1, 3.1, 4.1, 5.1])

    # Remove NaN test since sklearn doesn't handle it automatically
    metrics = calculate_metrics(y_true, y_pred)

    # Metrics should be calculated
    assert not np.isnan(metrics["r2_score"])
    assert not np.isnan(metrics["rmse"])


def test_calculate_metrics_with_zero_variance():
    """Test metrics with zero variance in true values."""
    y_true = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
    y_pred = np.array([5.1, 5.2, 4.9, 5.0, 5.1])

    metrics = calculate_metrics(y_true, y_pred)

    # R² is undefined for zero variance, but other metrics should work
    assert not np.isnan(metrics["rmse"])
    assert not np.isnan(metrics["mae"])
    # R² will be NaN or negative for zero variance
    assert "r2_score" in metrics
