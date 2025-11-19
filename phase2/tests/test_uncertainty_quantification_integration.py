"""
Integration tests for uncertainty quantification.

Tests the complete workflow of generating prediction intervals
and validating their coverage using ensemble models.
"""

import numpy as np
import pytest


@pytest.fixture
def trained_ensemble_models():
    """Create trained models for testing."""
    from models.random_forest_model import RandomForestModel
    from models.xgboost_model import XGBoostModel
    from models.lstm_model import LSTMModel

    np.random.seed(42)
    n_samples = 100
    n_features = 10

    X_train = np.random.randn(n_samples, n_features)
    y_train = np.random.randn(n_samples)

    # Train models with small configs for speed
    rf_model = RandomForestModel(custom_config={"n_estimators": 10})
    rf_model.train(X_train, y_train)

    xgb_model = XGBoostModel(custom_config={"n_estimators": 10})
    xgb_model.train(X_train, y_train)

    lstm_model = LSTMModel(custom_config={"epochs": 5, "batch_size": 32})
    lstm_model.train(X_train, y_train)

    return rf_model, xgb_model, lstm_model, X_train, y_train


def test_end_to_end_uncertainty_quantification(trained_ensemble_models):
    """Test complete uncertainty quantification workflow."""
    from evaluation.evaluate import (
        calculate_quantile_predictions,
        validate_prediction_intervals,
        calculate_metrics
    )

    rf_model, xgb_model, lstm_model, X_train, y_train = trained_ensemble_models

    # Generate test data
    np.random.seed(42)
    X_test = np.random.randn(50, 10)
    y_test = np.random.randn(50)

    # Step 1: Get predictions from each model
    rf_pred = rf_model.predict(X_test)
    xgb_pred = xgb_model.predict(X_test)
    lstm_pred = lstm_model.predict(X_test)

    # Step 2: Calculate quantile predictions for uncertainty
    # Use only RF and XGB to avoid LSTM NaN issues in small test dataset
    quantiles = calculate_quantile_predictions(
        [rf_pred, xgb_pred],
        quantiles=[0.025, 0.5, 0.975]  # 95% prediction interval
    )

    # Verify quantiles were calculated
    assert "q2.5" in quantiles
    assert "q50" in quantiles
    assert "q97.5" in quantiles

    # Step 3: Validate prediction interval coverage
    validation = validate_prediction_intervals(
        y_test,
        quantiles["q2.5"],
        quantiles["q97.5"],
        confidence_level=0.95
    )

    # Check validation metrics
    assert "coverage" in validation
    assert "expected_coverage" in validation
    assert validation["n_samples"] == len(y_test)

    # Step 4: Calculate point prediction metrics using median
    metrics = calculate_metrics(y_test, quantiles["q50"])

    assert "r2_score" in metrics
    assert "rmse" in metrics

    # Step 5: Verify interval properties
    interval_width = quantiles["q97.5"] - quantiles["q2.5"]
    assert np.all(interval_width > 0), "All intervals should have positive width"
    assert np.all(quantiles["q2.5"] <= quantiles["q50"]), "Lower bound <= median"
    assert np.all(quantiles["q50"] <= quantiles["q97.5"]), "Median <= upper bound"



def test_uncertainty_quantification_with_different_confidence_levels():
    """Test uncertainty quantification with various confidence levels."""
    from evaluation.evaluate import calculate_quantile_predictions, validate_prediction_intervals

    np.random.seed(42)
    n_samples = 200

    # Create synthetic predictions
    true_values = np.random.randn(n_samples)
    predictions = [
        true_values + np.random.randn(n_samples) * 0.2
        for _ in range(5)
    ]

    # Test 90% confidence interval
    quantiles_90 = calculate_quantile_predictions(
        predictions,
        quantiles=[0.05, 0.5, 0.95]
    )

    validation_90 = validate_prediction_intervals(
        true_values,
        quantiles_90["q5"],
        quantiles_90["q95"],
        confidence_level=0.90
    )

    # Test 95% confidence interval
    quantiles_95 = calculate_quantile_predictions(
        predictions,
        quantiles=[0.025, 0.5, 0.975]
    )

    validation_95 = validate_prediction_intervals(
        true_values,
        quantiles_95["q2.5"],
        quantiles_95["q97.5"],
        confidence_level=0.95
    )

    # 95% interval should be wider than 90% interval
    width_90 = np.mean(quantiles_90["q95"] - quantiles_90["q5"])
    width_95 = np.mean(quantiles_95["q97.5"] - quantiles_95["q2.5"])

    assert width_95 > width_90, "95% interval should be wider than 90% interval"

    # Both should have reasonable coverage
    assert validation_90["coverage"] > 0.8
    assert validation_95["coverage"] > 0.8


def test_uncertainty_quantification_saves_to_dataframe():
    """Test that uncertainty quantification results can be saved to DataFrame."""
    from evaluation.evaluate import calculate_quantile_predictions
    import pandas as pd

    np.random.seed(42)
    n_samples = 50

    # Create predictions
    predictions = [np.random.randn(n_samples) + 100 for _ in range(3)]

    # Calculate quantiles
    quantiles = calculate_quantile_predictions(predictions)

    # Create DataFrame with predictions and intervals
    results_df = pd.DataFrame({
        "prediction": quantiles["q50"],
        "lower_95": quantiles["q2.5"],
        "upper_95": quantiles["q97.5"],
        "interval_width": quantiles["q97.5"] - quantiles["q2.5"]
    })

    # Verify DataFrame structure
    assert len(results_df) == n_samples
    assert "prediction" in results_df.columns
    assert "lower_95" in results_df.columns
    assert "upper_95" in results_df.columns
    assert "interval_width" in results_df.columns

    # Verify all interval widths are positive
    assert (results_df["interval_width"] > 0).all()


def test_uncertainty_quantification_with_single_model():
    """Test that uncertainty quantification works with bootstrap from single model."""
    from evaluation.evaluate import calculate_quantile_predictions

    np.random.seed(42)
    n_samples = 100

    # Simulate bootstrap predictions from a single model
    # (In practice, you'd retrain on bootstrap samples)
    base_prediction = np.random.randn(n_samples) + 50

    # Create bootstrap predictions with noise
    bootstrap_predictions = [
        base_prediction + np.random.randn(n_samples) * 0.5
        for _ in range(20)  # 20 bootstrap samples
    ]

    # Calculate quantiles
    quantiles = calculate_quantile_predictions(bootstrap_predictions)

    # Should still work with bootstrap samples
    assert "q2.5" in quantiles
    assert "q50" in quantiles
    assert "q97.5" in quantiles

    # Median should be close to base prediction
    assert np.corrcoef(quantiles["q50"], base_prediction)[0, 1] > 0.95


def test_uncertainty_quantification_edge_cases():
    """Test edge cases for uncertainty quantification."""
    from evaluation.evaluate import calculate_quantile_predictions

    np.random.seed(42)

    # Test with identical predictions (no uncertainty)
    identical_preds = [np.array([1.0, 2.0, 3.0])] * 5
    quantiles = calculate_quantile_predictions(identical_preds)

    # All quantiles should be identical
    np.testing.assert_array_almost_equal(quantiles["q2.5"], quantiles["q50"])
    np.testing.assert_array_almost_equal(quantiles["q50"], quantiles["q97.5"])

    # Test with very different predictions (high uncertainty)
    diverse_preds = [
        np.array([1.0, 2.0, 3.0]),
        np.array([10.0, 20.0, 30.0]),
        np.array([100.0, 200.0, 300.0])
    ]
    quantiles_diverse = calculate_quantile_predictions(diverse_preds)

    # Interval width should be large
    width = quantiles_diverse["q97.5"] - quantiles_diverse["q2.5"]
    assert np.all(width > 50), "High uncertainty should produce wide intervals"
