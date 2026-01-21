"""
Verification script for model save/load functionality.

This script tests that all models can be saved and loaded correctly.
"""

import shutil
import tempfile
from pathlib import Path

import numpy as np
from models.ensemble_model import EnsembleModel
from models.lstm_model import LSTMModel

# Import models
from models.random_forest_model import RandomForestModel
from models.xgboost_model import XGBoostModel


def test_sklearn_model_save_load():
    """Test Random Forest save/load (uses joblib)."""
    print("\n=== Testing Random Forest (sklearn/joblib) ===")

    # Create synthetic data
    np.random.seed(42)
    X_train = np.random.randn(100, 10)
    y_train = np.random.randn(100)
    X_test = np.random.randn(20, 10)

    # Create and train model
    model = RandomForestModel(model_name="test_rf")
    model.train(X_train, y_train)

    # Make predictions before saving
    pred_before = model.predict(X_test)

    # Save model
    temp_dir = tempfile.mkdtemp()
    try:
        model_path = model.save(temp_dir)
        print(f"✓ Model saved to: {model_path}")

        # Check files exist
        assert Path(model_path).exists(), "Model file not found"
        metadata_path = Path(temp_dir) / "test_rf_metadata.json"
        assert metadata_path.exists(), "Metadata file not found"
        print(f"✓ Metadata saved to: {metadata_path}")

        # Load model
        new_model = RandomForestModel(model_name="test_rf")
        new_model.load(model_path)
        print("✓ Model loaded successfully")

        # Make predictions after loading
        pred_after = new_model.predict(X_test)

        # Verify predictions match
        assert np.allclose(pred_before, pred_after), "Predictions don't match!"
        print("✓ Predictions match after load")

        # Verify metadata
        assert new_model.is_trained, "Model not marked as trained"
        assert new_model.metadata is not None, "Metadata not loaded"
        print("✓ Model state restored correctly")

        print("✓ Random Forest save/load test PASSED")

    finally:
        shutil.rmtree(temp_dir)


def test_xgboost_model_save_load():
    """Test XGBoost save/load (uses joblib)."""
    print("\n=== Testing XGBoost (sklearn/joblib) ===")

    # Create synthetic data
    np.random.seed(42)
    X_train = np.random.randn(100, 10)
    y_train = np.random.randn(100)
    X_test = np.random.randn(20, 10)

    # Create and train model
    model = XGBoostModel(model_name="test_xgb")
    model.train(X_train, y_train)

    # Make predictions before saving
    pred_before = model.predict(X_test)

    # Save model
    temp_dir = tempfile.mkdtemp()
    try:
        model_path = model.save(temp_dir)
        print(f"✓ Model saved to: {model_path}")

        # Check files exist
        assert Path(model_path).exists(), "Model file not found"
        metadata_path = Path(temp_dir) / "test_xgb_metadata.json"
        assert metadata_path.exists(), "Metadata file not found"
        print(f"✓ Metadata saved to: {metadata_path}")

        # Load model
        new_model = XGBoostModel(model_name="test_xgb")
        new_model.load(model_path)
        print("✓ Model loaded successfully")

        # Make predictions after loading
        pred_after = new_model.predict(X_test)

        # Verify predictions match
        assert np.allclose(pred_before, pred_after), "Predictions don't match!"
        print("✓ Predictions match after load")

        # Verify metadata
        assert new_model.is_trained, "Model not marked as trained"
        assert new_model.metadata is not None, "Metadata not loaded"
        print("✓ Model state restored correctly")

        print("✓ XGBoost save/load test PASSED")

    finally:
        shutil.rmtree(temp_dir)


def test_lstm_model_save_load():
    """Test LSTM save/load (uses native Keras format)."""
    print("\n=== Testing LSTM (TensorFlow/Keras) ===")

    # Create synthetic data (need more samples for LSTM sequence length)
    np.random.seed(42)
    X_train = np.random.randn(100, 10)
    y_train = np.random.randn(100)
    X_test = np.random.randn(30, 10)
    y_test = np.random.randn(30)

    # Create and train model
    model = LSTMModel(model_name="test_lstm")
    model.train(X_train, y_train, X_val=X_test, y_val=y_test)

    # Make predictions before saving
    pred_before = model.predict(X_test)

    # Save model
    temp_dir = tempfile.mkdtemp()
    try:
        model_path = model.save(temp_dir)
        print(f"✓ Model saved to: {model_path}")

        # Check files exist
        assert Path(model_path).exists(), "Model file not found"
        metadata_path = Path(temp_dir) / "test_lstm_metadata.json"
        assert metadata_path.exists(), "Metadata file not found"
        print(f"✓ Metadata saved to: {metadata_path}")

        # Load model
        new_model = LSTMModel(model_name="test_lstm")
        new_model.load(model_path)
        print("✓ Model loaded successfully")

        # Make predictions after loading
        pred_after = new_model.predict(X_test)

        # Verify predictions match (allowing for small numerical differences)
        assert np.allclose(pred_before, pred_after, equal_nan=True), "Predictions don't match!"
        print("✓ Predictions match after load")

        # Verify metadata
        assert new_model.is_trained, "Model not marked as trained"
        assert new_model.metadata is not None, "Metadata not loaded"
        print("✓ Model state restored correctly")

        print("✓ LSTM save/load test PASSED")

    finally:
        shutil.rmtree(temp_dir)


def test_ensemble_model_save_load():
    """Test Ensemble save/load (saves config only)."""
    print("\n=== Testing Ensemble Model ===")

    # Create synthetic data
    np.random.seed(42)
    X_train = np.random.randn(100, 10)
    y_train = np.random.randn(100)

    # Create and train base models
    rf_model = RandomForestModel(model_name="test_rf_ensemble")
    rf_model.train(X_train, y_train)

    xgb_model = XGBoostModel(model_name="test_xgb_ensemble")
    xgb_model.train(X_train, y_train)

    lstm_model = LSTMModel(model_name="test_lstm_ensemble")
    lstm_model.train(X_train, y_train)

    # Create ensemble
    ensemble = EnsembleModel(model_name="test_ensemble")
    ensemble.load_base_models(rf_model, xgb_model, lstm_model)

    # Save ensemble config
    temp_dir = tempfile.mkdtemp()
    try:
        config_path = ensemble.save(temp_dir)
        print(f"✓ Ensemble config saved to: {config_path}")

        # Check files exist
        assert Path(config_path).exists(), "Config file not found"
        metadata_path = Path(temp_dir) / "test_ensemble_metadata.json"
        assert metadata_path.exists(), "Metadata file not found"
        print(f"✓ Metadata saved to: {metadata_path}")

        # Load ensemble config
        new_ensemble = EnsembleModel(model_name="test_ensemble")
        new_ensemble.load(config_path)
        print("✓ Ensemble config loaded successfully")

        # Verify weights
        assert new_ensemble.weights == ensemble.weights, "Weights don't match!"
        print("✓ Ensemble configuration restored correctly")

        print("✓ Ensemble save/load test PASSED")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("=" * 60)
    print("Model Save/Load Verification")
    print("=" * 60)

    try:
        test_sklearn_model_save_load()
        test_xgboost_model_save_load()
        test_lstm_model_save_load()
        test_ensemble_model_save_load()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("  ✓ Random Forest: Uses joblib for sklearn models")
        print("  ✓ XGBoost: Uses joblib for sklearn models")
        print("  ✓ LSTM: Uses native Keras .keras format")
        print("  ✓ Ensemble: Saves configuration as JSON")
        print("  ✓ All models save metadata alongside model files")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
