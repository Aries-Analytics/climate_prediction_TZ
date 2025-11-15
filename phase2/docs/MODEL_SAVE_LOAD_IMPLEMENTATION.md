# Model Save/Load Implementation

## Overview

This document describes the implementation of model save/load functionality for all ML models in the system. The implementation satisfies task 3.2 requirements:

- ✅ Use joblib for scikit-learn models
- ✅ Use native save for TensorFlow/Keras models
- ✅ Save model metadata alongside model files

## Implementation Details

### 1. Base Model Classes

#### SklearnBaseModel (models/base_model.py)

Provides save/load functionality for all scikit-learn based models using joblib:

```python
class SklearnBaseModel(BaseModel):
    def save(self, save_dir: str) -> str:
        """Save sklearn model using joblib."""
        # Saves model to: {save_dir}/{model_name}.pkl
        # Saves metadata to: {save_dir}/{model_name}_metadata.json
        
    def load(self, model_path: str) -> None:
        """Load sklearn model using joblib."""
        # Loads model from .pkl file
        # Loads metadata if available
```

**Models using this base class:**
- RandomForestModel
- XGBoostModel

#### LSTMModel (models/lstm_model.py)

Implements native Keras save/load functionality:

```python
class LSTMModel(BaseModel):
    def save(self, save_dir: str) -> str:
        """Save LSTM model using native Keras format."""
        # Saves model to: {save_dir}/{model_name}.keras
        # Saves metadata to: {save_dir}/{model_name}_metadata.json
        
    def load(self, model_path: str) -> None:
        """Load LSTM model using Keras."""
        # Loads model from .keras file
        # Loads metadata if available
        # Restores sequence_length from metadata
```

#### EnsembleModel (models/ensemble_model.py)

Saves configuration as JSON (base models saved separately):

```python
class EnsembleModel(BaseModel):
    def save(self, save_dir: str) -> str:
        """Save ensemble configuration."""
        # Saves config to: {save_dir}/{model_name}_config.json
        # Saves metadata to: {save_dir}/{model_name}_metadata.json
        
    def load(self, model_path: str) -> None:
        """Load ensemble configuration."""
        # Loads config from JSON
        # Note: Base models must be loaded separately
```

### 2. Metadata Management

All models save metadata alongside the model files using the `save_metadata()` method from BaseModel:

**Metadata includes:**
- Model name and type
- Creation and training timestamps
- Training time in seconds
- Hyperparameters/configuration
- Performance metrics (R², RMSE, MAE, MAPE)
- Feature information (names, count)
- Model-specific information

**Metadata file format:** `{model_name}_metadata.json`

Example metadata:
```json
{
  "model_name": "random_forest",
  "model_type": "random_forest",
  "created_at": "2025-11-15T07:11:01.123456",
  "trained_at": "2025-11-15T07:11:05.789012",
  "training_time_seconds": 4.665556,
  "config": {
    "n_estimators": 200,
    "max_depth": 15,
    "min_samples_split": 5
  },
  "metrics": {
    "rmse": 0.8234,
    "mae": 0.6543,
    "r2": 0.8765,
    "mape": 12.34
  },
  "feature_names": ["feature_1", "feature_2", ...],
  "n_features": 181
}
```

### 3. File Formats

| Model Type | Model File Format | Serialization Method |
|------------|------------------|---------------------|
| Random Forest | `.pkl` | joblib |
| XGBoost | `.pkl` | joblib |
| LSTM | `.keras` | TensorFlow/Keras native |
| Ensemble | `.json` | JSON (config only) |
| Metadata (all) | `.json` | JSON |

### 4. Usage Examples

#### Saving Models

```python
from models.random_forest_model import RandomForestModel

# Train model
model = RandomForestModel(model_name="my_rf_model")
model.train(X_train, y_train, X_val, y_val)

# Save model and metadata
model_path = model.save("models/saved")
# Creates:
#   models/saved/my_rf_model.pkl
#   models/saved/my_rf_model_metadata.json
```

#### Loading Models

```python
from models.random_forest_model import RandomForestModel

# Create model instance
model = RandomForestModel(model_name="my_rf_model")

# Load trained model
model.load("models/saved/my_rf_model.pkl")
# Automatically loads metadata if available

# Use model
predictions = model.predict(X_test)
```

#### Ensemble Model Save/Load

```python
from models.ensemble_model import EnsembleModel

# Save ensemble (after loading base models)
ensemble = EnsembleModel(model_name="my_ensemble")
ensemble.load_base_models(rf_model, xgb_model, lstm_model)
ensemble.save("models/saved")
# Creates:
#   models/saved/my_ensemble_config.json
#   models/saved/my_ensemble_metadata.json

# Load ensemble
new_ensemble = EnsembleModel(model_name="my_ensemble")
new_ensemble.load("models/saved/my_ensemble_config.json")
# Note: Must load base models separately
new_ensemble.load_base_models(rf_model, xgb_model, lstm_model)
```

### 5. Validation

The implementation has been verified with comprehensive tests in `verify_model_save_load.py`:

**Test Results:**
- ✅ Random Forest save/load (joblib)
- ✅ XGBoost save/load (joblib)
- ✅ LSTM save/load (Keras native)
- ✅ Ensemble save/load (JSON config)
- ✅ Metadata save/load for all models
- ✅ Predictions match before and after save/load
- ✅ Model state correctly restored

### 6. Error Handling

The implementation includes robust error handling:

- **FileNotFoundError**: Raised if model file doesn't exist during load
- **RuntimeError**: Raised if trying to save untrained model
- **Validation**: Models validate they are trained before saving
- **Metadata**: Gracefully handles missing metadata files

### 7. Requirements Mapping

| Requirement | Implementation | Status |
|------------|----------------|--------|
| 2.8 - Save trained models | All models implement save() method | ✅ |
| 2.9 - Save model metadata | Metadata saved alongside all models | ✅ |
| 6.1 - Save to models directory | Configurable save_dir parameter | ✅ |
| 6.2 - Save model metadata | Comprehensive metadata in JSON | ✅ |
| 6.5 - Validate loaded models | is_trained flag and validation | ✅ |

## Best Practices

1. **Always save metadata**: Metadata helps track model versions and performance
2. **Use timestamps**: Include timestamps in filenames for versioning
3. **Validate before use**: Check `is_trained` flag before making predictions
4. **Separate base models**: For ensemble, save base models separately
5. **Backup models**: Keep multiple versions for rollback capability

## Future Enhancements

- Model versioning system with automatic archival
- Compression for large model files
- Cloud storage integration (S3, Azure Blob)
- Model registry for tracking all saved models
- Automatic model comparison and selection
