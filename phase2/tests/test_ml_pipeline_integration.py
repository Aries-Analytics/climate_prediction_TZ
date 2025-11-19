"""
Integration tests for ML pipeline.

Tests end-to-end pipeline execution and output file generation.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_master_dataset(tmp_path):
    """Create a sample master dataset for testing."""
    np.random.seed(42)
    n_samples = 50  # Small dataset for fast testing

    data = {
        "year": [2020] * 25 + [2021] * 25,
        "month": list(range(1, 13)) * 4 + list(range(1, 3)),  # 12*4 + 2 = 50
        "temperature": np.random.uniform(20, 35, n_samples),
        "rainfall": np.random.uniform(0, 200, n_samples),
        "ndvi": np.random.uniform(0.2, 0.8, n_samples),
        "oni": np.random.uniform(-2, 2, n_samples),
        "iod": np.random.uniform(-1, 1, n_samples),
        "humidity": np.random.uniform(40, 90, n_samples),
        "solar_radiation": np.random.uniform(100, 300, n_samples),
    }

    df = pd.DataFrame(data)

    # Save to CSV
    dataset_path = tmp_path / "master_dataset.csv"
    df.to_csv(dataset_path, index=False)

    return str(dataset_path)


def test_preprocessing_pipeline_end_to_end(sample_master_dataset, tmp_path):
    """Test complete preprocessing pipeline execution."""
    from preprocessing.preprocess import preprocess_pipeline

    output_dir = tmp_path / "processed"

    # Run preprocessing pipeline
    metadata = preprocess_pipeline(
        input_path=sample_master_dataset, output_dir=str(output_dir), lag_periods=[1, 3], rolling_windows=[3]
    )

    # Check metadata
    assert "initial_shape" in metadata
    assert "final_shape" in metadata
    assert "features_added" in metadata

    # Check output files exist
    assert (output_dir / "features_train.csv").exists()
    assert (output_dir / "features_val.csv").exists()
    assert (output_dir / "features_test.csv").exists()
    assert (output_dir / "features_train.parquet").exists()
    assert (output_dir / "scaler_params.json").exists()
    assert (output_dir / "feature_metadata.json").exists()

    # Load and verify train data
    train_df = pd.read_csv(output_dir / "features_train.csv")
    assert len(train_df) > 0
    assert "year" in train_df.columns
    assert "month" in train_df.columns

    # Verify features were added
    assert train_df.shape[1] > metadata["initial_shape"][1]


def test_model_training_pipeline_end_to_end(sample_master_dataset, tmp_path):
    """Test complete model training pipeline."""
    from evaluation.evaluate import calculate_metrics
    from models.random_forest_model import RandomForestModel
    from preprocessing.preprocess import preprocess_pipeline

    # Step 1: Preprocess data
    processed_dir = tmp_path / "processed"
    preprocess_pipeline(
        input_path=sample_master_dataset, output_dir=str(processed_dir), lag_periods=[1], rolling_windows=[3]
    )

    # Step 2: Load preprocessed data
    train_df = pd.read_csv(processed_dir / "features_train.csv")
    test_df = pd.read_csv(processed_dir / "features_test.csv")

    # Prepare features and target
    exclude_cols = ["year", "month"]
    feature_cols = [col for col in train_df.columns if col not in exclude_cols]

    # Use first numeric column as target
    target_col = "temperature"
    feature_cols = [col for col in feature_cols if col != target_col]

    X_train = train_df[feature_cols].fillna(0).values
    y_train = train_df[target_col].fillna(0).values

    X_test = test_df[feature_cols].fillna(0).values
    y_test = test_df[target_col].fillna(0).values

    # Step 3: Train model
    model = RandomForestModel(custom_config={"n_estimators": 10})  # Small for speed
    results = model.train(X_train, y_train)

    assert model.is_trained
    assert "train_metrics" in results

    # Step 4: Make predictions
    y_pred = model.predict(X_test)
    assert len(y_pred) == len(y_test)

    # Step 5: Evaluate
    metrics = calculate_metrics(y_test, y_pred)
    assert "r2_score" in metrics
    assert "rmse" in metrics

    # Step 6: Save model
    model_dir = tmp_path / "models"
    save_path = model.save(str(model_dir))
    assert Path(save_path).exists()

    # Step 7: Load model
    loaded_model = RandomForestModel()
    loaded_model.load(save_path)
    assert loaded_model.is_trained

    # Step 8: Verify loaded model predictions match
    y_pred_loaded = loaded_model.predict(X_test)
    np.testing.assert_array_almost_equal(y_pred, y_pred_loaded)


def test_output_files_have_correct_structure(sample_master_dataset, tmp_path):
    """Test that all output files have correct structure."""
    from preprocessing.preprocess import preprocess_pipeline

    output_dir = tmp_path / "processed"

    # Run pipeline
    preprocess_pipeline(input_path=sample_master_dataset, output_dir=str(output_dir))

    # Check CSV files
    for filename in ["features_train.csv", "features_val.csv", "features_test.csv"]:
        df = pd.read_csv(output_dir / filename)
        assert "year" in df.columns
        assert "month" in df.columns
        assert len(df) > 0

    # Check scaler params
    with open(output_dir / "scaler_params.json", "r") as f:
        scaler_params = json.load(f)
        assert isinstance(scaler_params, dict)
        assert len(scaler_params) > 0

    # Check metadata
    with open(output_dir / "feature_metadata.json", "r") as f:
        metadata = json.load(f)
        assert "initial_shape" in metadata
        assert "final_shape" in metadata
        assert "train_samples" in metadata


def test_pipeline_handles_small_dataset(tmp_path):
    """Test pipeline works with minimal dataset."""
    # Create very small dataset
    data = {
        "year": [2020] * 12,
        "month": list(range(1, 13)),
        "temperature": np.random.uniform(20, 30, 12),
        "rainfall": np.random.uniform(0, 100, 12),
    }

    df = pd.DataFrame(data)
    dataset_path = tmp_path / "small_dataset.csv"
    df.to_csv(dataset_path, index=False)

    # Run preprocessing
    from preprocessing.preprocess import preprocess_pipeline

    output_dir = tmp_path / "processed"

    metadata = preprocess_pipeline(
        input_path=str(dataset_path), output_dir=str(output_dir), lag_periods=[1], rolling_windows=[3]
    )

    # Should complete without errors
    assert metadata is not None
    assert (output_dir / "features_train.csv").exists()
