"""
Unit tests for ML models.

Tests model training, prediction, save/load, and ensemble functionality.
"""

import numpy as np
import pytest
from models.ensemble_model import EnsembleModel
from models.lstm_model import LSTMModel
from models.random_forest_model import RandomForestModel
from models.xgboost_model import XGBoostModel


@pytest.fixture
def sample_training_data():
    """Create sample training data."""
    np.random.seed(42)
    n_samples = 100
    n_features = 10

    X_train = np.random.randn(n_samples, n_features)
    y_train = np.random.randn(n_samples)

    X_val = np.random.randn(30, n_features)
    y_val = np.random.randn(30)

    return X_train, y_train, X_val, y_val


@pytest.fixture
def sample_test_data():
    """Create sample test data."""
    np.random.seed(42)
    n_samples = 20
    n_features = 10

    X_test = np.random.randn(n_samples, n_features)
    y_test = np.random.randn(n_samples)

    return X_test, y_test


# ============================================================================
# Test Random Forest Model
# ============================================================================


def test_random_forest_initialization():
    """Test Random Forest model initialization."""
    model = RandomForestModel()

    assert model.model_name == "random_forest"
    assert model.model_type == "random_forest"
    assert not model.is_trained


def test_random_forest_train_and_predict(sample_training_data):
    """Test Random Forest can fit and predict."""
    X_train, y_train, X_val, y_val = sample_training_data

    model = RandomForestModel()
    results = model.train(X_train, y_train, X_val, y_val)

    # Check training completed
    assert model.is_trained
    assert "train_metrics" in results
    assert "val_metrics" in results

    # Check can predict
    predictions = model.predict(X_train[:10])
    assert len(predictions) == 10
    assert predictions.dtype == np.float64


def test_random_forest_save_load(sample_training_data, tmp_path):
    """Test Random Forest save/load functionality."""
    X_train, y_train, _, _ = sample_training_data

    # Train model
    model = RandomForestModel()
    model.train(X_train, y_train)

    # Make predictions before saving
    pred_before = model.predict(X_train[:5])

    # Save model
    save_path = model.save(str(tmp_path))
    assert save_path.endswith(".pkl")

    # Load model
    loaded_model = RandomForestModel()
    loaded_model.load(save_path)

    # Make predictions after loading
    pred_after = loaded_model.predict(X_train[:5])

    # Predictions should be identical
    np.testing.assert_array_almost_equal(pred_before, pred_after)


def test_random_forest_feature_importance(sample_training_data):
    """Test feature importance extraction."""
    X_train, y_train, _, _ = sample_training_data

    model = RandomForestModel()
    model.train(X_train, y_train)

    # Get feature importance
    importance_df = model.get_feature_importance()

    assert len(importance_df) == X_train.shape[1]
    assert "feature" in importance_df.columns
    assert "importance" in importance_df.columns
    assert importance_df["importance"].sum() > 0


# ============================================================================
# Test XGBoost Model
# ============================================================================


def test_xgboost_initialization():
    """Test XGBoost model initialization."""
    model = XGBoostModel()

    assert model.model_name == "xgboost"
    assert model.model_type == "xgboost"
    assert not model.is_trained


def test_xgboost_train_and_predict(sample_training_data):
    """Test XGBoost can fit and predict."""
    X_train, y_train, X_val, y_val = sample_training_data

    model = XGBoostModel()
    results = model.train(X_train, y_train, X_val, y_val)

    # Check training completed
    assert model.is_trained
    assert "train_metrics" in results

    # Check can predict
    predictions = model.predict(X_train[:10])
    assert len(predictions) == 10


def test_xgboost_save_load(sample_training_data, tmp_path):
    """Test XGBoost save/load functionality."""
    X_train, y_train, _, _ = sample_training_data

    # Train model
    model = XGBoostModel()
    model.train(X_train, y_train)

    # Make predictions before saving
    pred_before = model.predict(X_train[:5])

    # Save model
    save_path = model.save(str(tmp_path))

    # Load model
    loaded_model = XGBoostModel()
    loaded_model.load(save_path)

    # Make predictions after loading
    pred_after = loaded_model.predict(X_train[:5])

    # Predictions should be identical
    np.testing.assert_array_almost_equal(pred_before, pred_after)


# ============================================================================
# Test LSTM Model
# ============================================================================


def test_lstm_initialization():
    """Test LSTM model initialization."""
    model = LSTMModel()

    assert model.model_name == "lstm"
    assert model.model_type == "lstm"
    assert not model.is_trained


def test_lstm_train_and_predict(sample_training_data):
    """Test LSTM can fit and predict."""
    X_train, y_train, X_val, y_val = sample_training_data

    # LSTM needs more samples for sequence length
    if len(X_train) < 20:
        pytest.skip("Not enough samples for LSTM")

    model = LSTMModel()
    results = model.train(X_train, y_train, X_val, y_val)

    # Check training completed
    assert model.is_trained
    assert "train_metrics" in results

    # Check can predict
    predictions = model.predict(X_train)
    assert len(predictions) == len(X_train)


def test_lstm_save_load(sample_training_data, tmp_path):
    """Test LSTM save/load functionality."""
    X_train, y_train, _, _ = sample_training_data

    if len(X_train) < 20:
        pytest.skip("Not enough samples for LSTM")

    # Train model
    model = LSTMModel()
    model.train(X_train, y_train)

    # Save model
    save_path = model.save(str(tmp_path))

    # Load model
    loaded_model = LSTMModel()
    loaded_model.load(save_path)

    # Check model is loaded
    assert loaded_model.is_trained


# ============================================================================
# Test Ensemble Model
# ============================================================================


def test_ensemble_initialization():
    """Test Ensemble model initialization."""
    model = EnsembleModel()

    assert model.model_name == "ensemble"
    assert model.model_type == "ensemble"
    assert not model.is_trained


def test_ensemble_combines_predictions_correctly(sample_training_data):
    """Test ensemble combines predictions with correct weights."""
    X_train, y_train, X_val, y_val = sample_training_data

    # Train base models
    rf_model = RandomForestModel(model_name="rf_test")
    rf_model.train(X_train, y_train)

    xgb_model = XGBoostModel(model_name="xgb_test")
    xgb_model.train(X_train, y_train)

    lstm_model = LSTMModel(model_name="lstm_test")
    lstm_model.train(X_train, y_train)

    # Create ensemble with known weights
    ensemble = EnsembleModel(custom_config={"weights": {"rf": 0.3, "xgb": 0.4, "lstm": 0.3}})

    ensemble.load_base_models(rf_model, xgb_model, lstm_model)

    # Get predictions (use more samples for LSTM sequence requirements)
    X_test = X_train[:20]  # LSTM needs at least 6 samples for sequence length
    rf_pred = rf_model.predict(X_test)
    xgb_pred = xgb_model.predict(X_test)
    lstm_pred = lstm_model.predict(X_test)
    ensemble_pred = ensemble.predict(X_test)

    # Calculate expected ensemble prediction
    # Handle LSTM NaN values
    valid_mask = ~np.isnan(lstm_pred)
    expected = np.zeros_like(rf_pred)

    for i in range(len(X_test)):
        if valid_mask[i]:
            expected[i] = 0.3 * rf_pred[i] + 0.4 * xgb_pred[i] + 0.3 * lstm_pred[i]
        else:
            # Use only RF and XGB with renormalized weights
            expected[i] = (0.3 / 0.7) * rf_pred[i] + (0.4 / 0.7) * xgb_pred[i]

    # Check ensemble predictions match expected
    np.testing.assert_array_almost_equal(ensemble_pred, expected, decimal=5)


def test_ensemble_save_load(sample_training_data, tmp_path):
    """Test ensemble save/load functionality."""
    X_train, y_train, _, _ = sample_training_data

    # Train base models
    rf_model = RandomForestModel()
    rf_model.train(X_train, y_train)

    xgb_model = XGBoostModel()
    xgb_model.train(X_train, y_train)

    lstm_model = LSTMModel()
    lstm_model.train(X_train, y_train)

    # Create and save ensemble
    ensemble = EnsembleModel()
    ensemble.load_base_models(rf_model, xgb_model, lstm_model)

    save_path = ensemble.save(str(tmp_path))

    # Load ensemble config
    loaded_ensemble = EnsembleModel()
    loaded_ensemble.load(save_path)

    # Check weights are preserved
    assert loaded_ensemble.weights == ensemble.weights


def test_ensemble_requires_trained_models(sample_training_data):
    """Test ensemble requires trained base models."""
    X_train, y_train, _, _ = sample_training_data

    # Create untrained models
    rf_model = RandomForestModel()
    xgb_model = XGBoostModel()
    lstm_model = LSTMModel()

    ensemble = EnsembleModel()

    # Should raise error when loading untrained models
    with pytest.raises(ValueError, match="not trained"):
        ensemble.load_base_models(rf_model, xgb_model, lstm_model)
