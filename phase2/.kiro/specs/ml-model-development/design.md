# Design Document: ML Model Development

## Overview

This design document outlines the architecture for a machine learning system that predicts climate variables for Tanzania using 24 years of monthly data (288 records) with 181 engineered features. The system will implement multiple model types (Random Forest, XGBoost, LSTM, Ensemble) with uncertainty quantification to support parametric insurance decisions.

### Key Design Goals

1. **High Accuracy**: Achieve R² > 0.85 for reliable insurance triggers
2. **Uncertainty Quantification**: Provide confidence intervals for risk assessment
3. **Modularity**: Separate preprocessing, training, and evaluation components
4. **Reproducibility**: Track experiments and enable model versioning
5. **Extensibility**: Easy to add new models and features

### Data Context

- **Input**: `outputs/processed/master_dataset.csv` (288 rows × 181 columns)
- **Time Range**: 2000-2023 (24 years, monthly frequency)
- **Features**: 181 engineered features from 5 data sources
- **Target Variables**: Temperature, rainfall, NDVI, insurance triggers

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ML Model System                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Feature    │───▶│    Model     │───▶│  Evaluation  │  │
│  │  Pipeline    │    │   Trainer    │    │    Engine    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Preprocessed │    │    Trained   │    │  Performance │  │
│  │   Features   │    │    Models    │    │   Reports    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Configuration & Experiment Tracking          │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
Master Dataset (CSV)
       │
       ▼
Feature Pipeline
  ├─ Load & Validate
  ├─ Create Lag Features
  ├─ Create Rolling Stats
  ├─ Handle Missing Values
  ├─ Normalize Features
  └─ Train/Val/Test Split
       │
       ▼
Model Trainer
  ├─ Random Forest
  ├─ XGBoost
  ├─ LSTM
  └─ Ensemble
       │
       ▼
Evaluation Engine
  ├─ Calculate Metrics
  ├─ Generate Plots
  ├─ Uncertainty Analysis
  └─ Save Reports
```


## Components and Interfaces

### 1. Feature Pipeline (`preprocessing/preprocess.py`)

**Purpose**: Transform raw master dataset into model-ready features

**Key Functions**:

```python
def load_and_validate_data(file_path: str) -> pd.DataFrame:
    """Load master dataset and validate structure"""
    
def create_lag_features(df: pd.DataFrame, columns: List[str], lags: List[int]) -> pd.DataFrame:
    """Create lag features for specified columns"""
    
def create_rolling_features(df: pd.DataFrame, columns: List[str], windows: List[int]) -> pd.DataFrame:
    """Create rolling mean/std features"""
    
def handle_missing_values(df: pd.DataFrame, max_gap: int = 2) -> pd.DataFrame:
    """Forward-fill missing values with gap limit"""
    
def normalize_features(df: pd.DataFrame, exclude_cols: List[str]) -> Tuple[pd.DataFrame, dict]:
    """Standardize numeric features, return scaler params"""
    
def split_temporal_data(df: pd.DataFrame, train_pct: float = 0.7, val_pct: float = 0.15) -> Tuple:
    """Split data temporally into train/val/test"""
    
def preprocess_pipeline(input_path: str, output_dir: str) -> dict:
    """Main preprocessing pipeline, returns metadata"""
```

**Inputs**:
- `outputs/processed/master_dataset.csv`

**Outputs**:
- `outputs/processed/features_train.csv`
- `outputs/processed/features_val.csv`
- `outputs/processed/features_test.csv`
- `outputs/processed/scaler_params.json`
- `outputs/processed/feature_metadata.json`

### 2. Model Configuration (`models/model_config.py`)

**Purpose**: Centralized configuration for all models

**Configuration Structure**:

```python
MODEL_CONFIG = {
    "random_forest": {
        "n_estimators": 200,
        "max_depth": 15,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "random_state": 42
    },
    "xgboost": {
        "n_estimators": 200,
        "max_depth": 8,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42
    },
    "lstm": {
        "units": [128, 64],
        "dropout": 0.2,
        "epochs": 100,
        "batch_size": 16,
        "learning_rate": 0.001
    },
    "ensemble": {
        "weights": {"rf": 0.3, "xgb": 0.4, "lstm": 0.3}
    }
}

FEATURE_CONFIG = {
    "lag_periods": [1, 3, 6, 12],
    "rolling_windows": [3, 6],
    "target_variables": ["temperature", "rainfall", "ndvi"]
}
```


### 3. Model Trainer (`models/model_trainer.py`)

**Purpose**: Train and evaluate multiple model types

**Key Classes and Functions**:

```python
class BaseModel:
    """Abstract base class for all models"""
    def train(self, X_train, y_train, X_val, y_val) -> dict:
        pass
    def predict(self, X) -> np.ndarray:
        pass
    def save(self, path: str):
        pass
    def load(self, path: str):
        pass

class RandomForestModel(BaseModel):
    """Random Forest implementation"""
    
class XGBoostModel(BaseModel):
    """XGBoost implementation"""
    
class LSTMModel(BaseModel):
    """LSTM time series model"""
    
class EnsembleModel(BaseModel):
    """Weighted ensemble of multiple models"""
    
def train_all_models(X_train, y_train, X_val, y_val, config: dict) -> dict:
    """Train all model types and return results"""
    
def cross_validate_model(model, X, y, n_folds: int = 5) -> dict:
    """Perform time series cross-validation"""
```

**Inputs**:
- Training/validation data from Feature Pipeline
- Model configuration from `model_config.py`

**Outputs**:
- `models/saved/random_forest_{timestamp}.pkl`
- `models/saved/xgboost_{timestamp}.pkl`
- `models/saved/lstm_{timestamp}.h5`
- `models/saved/ensemble_{timestamp}.pkl`
- `models/saved/model_metadata_{timestamp}.json`

### 4. Evaluation Engine (`evaluation/evaluate.py`)

**Purpose**: Comprehensive model evaluation and reporting

**Key Functions**:

```python
def calculate_metrics(y_true, y_pred) -> dict:
    """Calculate R², RMSE, MAE, MAPE"""
    
def calculate_quantile_predictions(model, X, quantiles: List[float]) -> dict:
    """Generate prediction intervals"""
    
def evaluate_by_region(model, X, y, regions) -> pd.DataFrame:
    """Performance metrics by region"""
    
def evaluate_by_season(model, X, y, months) -> pd.DataFrame:
    """Performance metrics by season"""
    
def plot_predictions_vs_actual(y_true, y_pred, save_path: str):
    """Scatter plot with R² annotation"""
    
def plot_residuals_over_time(y_true, y_pred, dates, save_path: str):
    """Time series of prediction errors"""
    
def plot_feature_importance(model, feature_names, save_path: str):
    """Bar chart of top features"""
    
def generate_evaluation_report(model, test_data, output_dir: str) -> dict:
    """Comprehensive evaluation with all metrics and plots"""
```

**Outputs**:
- `outputs/evaluation/metrics_summary.json`
- `outputs/evaluation/predictions_vs_actual.png`
- `outputs/evaluation/residuals_over_time.png`
- `outputs/evaluation/feature_importance.png`
- `outputs/evaluation/performance_by_region.csv`
- `outputs/evaluation/performance_by_season.csv`


### 5. Experiment Tracking (`models/experiment_tracker.py`)

**Purpose**: Log and compare model experiments

**Key Functions**:

```python
def create_experiment_id() -> str:
    """Generate unique experiment ID"""
    
def log_experiment(experiment_id: str, config: dict, metrics: dict, model_path: str):
    """Record experiment details"""
    
def load_experiments() -> pd.DataFrame:
    """Load all experiment logs"""
    
def compare_experiments(metric: str = "r2_score") -> pd.DataFrame:
    """Rank experiments by performance"""
    
def get_best_model(metric: str = "r2_score") -> dict:
    """Retrieve best performing model info"""
```

**Outputs**:
- `outputs/experiments/experiment_log.csv`
- `outputs/experiments/experiment_comparison.csv`

## Data Models

### Feature Dataset Schema

```python
{
    "year": int,           # 2000-2023
    "month": int,          # 1-12
    
    # Original features (181 columns from master dataset)
    "nasa_power_*": float,
    "era5_*": float,
    "chirps_*": float,
    "ndvi_*": float,
    "ocean_indices_*": float,
    
    # Engineered lag features
    "temperature_lag_1": float,
    "temperature_lag_3": float,
    "rainfall_lag_1": float,
    # ... more lags
    
    # Rolling statistics
    "temperature_rolling_mean_3": float,
    "temperature_rolling_std_3": float,
    "rainfall_rolling_mean_6": float,
    # ... more rolling stats
    
    # Target variables
    "target_temperature": float,
    "target_rainfall": float,
    "target_ndvi": float
}
```

### Model Metadata Schema

```python
{
    "model_id": str,
    "model_type": str,  # "random_forest", "xgboost", "lstm", "ensemble"
    "timestamp": str,
    "hyperparameters": dict,
    "training_time_seconds": float,
    "metrics": {
        "r2_score": float,
        "rmse": float,
        "mae": float,
        "mape": float
    },
    "feature_count": int,
    "training_samples": int,
    "validation_samples": int,
    "test_samples": int
}
```

### Experiment Log Schema

```python
{
    "experiment_id": str,
    "timestamp": str,
    "model_type": str,
    "hyperparameters": dict,
    "features_used": List[str],
    "r2_score": float,
    "rmse": float,
    "mae": float,
    "mape": float,
    "training_time": float,
    "model_path": str,
    "notes": str
}
```


## Error Handling

### Data Validation Errors

**Scenario**: Missing columns or invalid data types in master dataset

**Handling**:
- Validate schema on load
- Raise `ValueError` with specific missing columns
- Log error details to `logs/pipeline.log`
- Provide clear error message to user

### Missing Value Handling

**Scenario**: Gaps in time series data

**Handling**:
- Forward-fill up to 2 months
- If gap > 2 months, log warning and use interpolation
- Track imputation statistics in metadata
- Flag imputed values in output

### Model Training Failures

**Scenario**: Model fails to converge or encounters numerical issues

**Handling**:
- Catch exceptions during training
- Log error with stack trace
- Continue with other models
- Report failed models in summary

### Low Performance Warning

**Scenario**: Model R² < 0.85 threshold

**Handling**:
- Log warning message
- Include suggestions: "Consider adding more features, tuning hyperparameters, or using ensemble"
- Continue execution (not a fatal error)
- Highlight in evaluation report

## Testing Strategy

### Unit Tests

**Test Coverage**:

1. **Feature Pipeline Tests** (`tests/test_preprocessing.py`)
   - Test lag feature creation with known inputs
   - Test rolling statistics calculations
   - Test missing value handling edge cases
   - Test train/val/test split maintains temporal order
   - Test normalization produces mean=0, std=1

2. **Model Tests** (`tests/test_models.py`)
   - Test each model can fit and predict
   - Test model save/load functionality
   - Test ensemble combines predictions correctly
   - Test configuration loading

3. **Evaluation Tests** (`tests/test_evaluation.py`)
   - Test metric calculations with known values
   - Test quantile prediction generation
   - Test plot generation doesn't crash

### Integration Tests

**Test Scenarios**:

1. **End-to-End Pipeline** (`tests/test_ml_pipeline.py`)
   - Load master dataset
   - Run preprocessing
   - Train all models
   - Generate evaluation reports
   - Verify all output files created

2. **Experiment Tracking** (`tests/test_experiments.py`)
   - Log multiple experiments
   - Compare experiments
   - Retrieve best model

### Performance Tests

**Benchmarks**:
- Preprocessing should complete in < 30 seconds
- Random Forest training should complete in < 2 minutes
- XGBoost training should complete in < 3 minutes
- LSTM training should complete in < 10 minutes
- Evaluation should complete in < 1 minute


## Implementation Details

### Time Series Considerations

**Temporal Ordering**:
- Always split data chronologically (no random shuffling)
- Training: 2000-2016 (70% = ~201 months)
- Validation: 2017-2019 (15% = ~43 months)
- Test: 2020-2023 (15% = ~44 months)

**Cross-Validation**:
- Use TimeSeriesSplit with 5 folds
- Each fold respects temporal order
- No future data leaks into past predictions

**LSTM Sequence Preparation**:
- Create sequences of 12 months (1 year lookback)
- Predict next month's values
- Reshape data to (samples, timesteps, features)

### Feature Selection Strategy

**Initial Approach**:
- Use all 181 features from master dataset
- Add lag and rolling features (estimated +50 features)
- Total: ~230 features

**Optimization**:
- Calculate feature importance from Random Forest
- Remove features with importance < 0.001
- Retrain with reduced feature set
- Compare performance

### Hyperparameter Tuning

**Method**: Grid Search with Time Series Cross-Validation

**Random Forest Grid**:
```python
{
    "n_estimators": [100, 200, 300],
    "max_depth": [10, 15, 20],
    "min_samples_split": [2, 5, 10]
}
```

**XGBoost Grid**:
```python
{
    "n_estimators": [100, 200, 300],
    "max_depth": [6, 8, 10],
    "learning_rate": [0.01, 0.05, 0.1]
}
```

**LSTM Grid**:
```python
{
    "units": [[64, 32], [128, 64], [256, 128]],
    "dropout": [0.1, 0.2, 0.3],
    "learning_rate": [0.001, 0.0001]
}
```

### Uncertainty Quantification Implementation

**Quantile Regression for Tree Models**:
- Train separate models for 10th, 50th, 90th percentiles
- Use quantile loss function
- Ensemble predictions for final intervals

**Monte Carlo Dropout for LSTM**:
- Enable dropout during inference
- Run 100 forward passes
- Calculate mean and percentiles from distribution

**Prediction Interval Validation**:
- Check coverage: % of actual values within intervals
- Target: 80% coverage for 80% intervals
- Adjust if coverage is too low/high


## Dependencies

### Required Python Packages

```python
# Core ML libraries
scikit-learn>=1.3.0      # Random Forest, preprocessing
xgboost>=2.0.0           # XGBoost models
tensorflow>=2.13.0       # LSTM models (or pytorch>=2.0.0)

# Data manipulation
pandas>=2.0.0
numpy>=1.24.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0

# Utilities
joblib>=1.3.0            # Model serialization
pyyaml>=6.0              # Config files
```

### Existing Project Dependencies

- `utils/logger.py` - Logging functionality
- `utils/config.py` - Path management
- `utils/validation.py` - Data validation
- `outputs/processed/master_dataset.csv` - Input data

## Deployment Considerations

### Model Serving

**Option 1: Batch Predictions**
- Load model once
- Process all test data
- Save predictions to CSV
- Suitable for monthly updates

**Option 2: API Endpoint** (Future)
- Flask/FastAPI wrapper
- Load model on startup
- Accept JSON input
- Return predictions with uncertainty

### Model Versioning

**Strategy**:
- Save models with timestamp: `model_YYYYMMDD_HHMMSS.pkl`
- Keep metadata file with same timestamp
- Maintain experiment log for comparison
- Archive old models after 6 months

### Monitoring

**Metrics to Track**:
- Prediction accuracy over time (detect drift)
- Feature distributions (detect data shifts)
- Inference time (performance monitoring)
- Error rates (system health)

## Future Enhancements

### Phase 1 (Current Spec)
- Basic preprocessing and feature engineering
- 4 model types (RF, XGB, LSTM, Ensemble)
- Uncertainty quantification
- Experiment tracking

### Phase 2 (Future)
- Advanced feature selection (SHAP values)
- Automated hyperparameter optimization (Optuna)
- Model interpretability (LIME, SHAP)
- Real-time prediction API

### Phase 3 (Future)
- Multi-step ahead forecasting (3, 6, 12 months)
- Spatial models (predict multiple locations)
- Transfer learning from global climate models
- Automated retraining pipeline

## Success Criteria

### Technical Metrics
- ✅ R² > 0.85 on test set
- ✅ RMSE < 10% of target variable range
- ✅ 80% prediction interval coverage ≥ 75%
- ✅ Training completes in < 30 minutes
- ✅ All tests pass

### Deliverables
- ✅ Preprocessed feature datasets
- ✅ 4 trained models saved to disk
- ✅ Evaluation reports with visualizations
- ✅ Experiment tracking log
- ✅ Updated documentation

### Code Quality
- ✅ All functions have docstrings
- ✅ Type hints for function signatures
- ✅ Unit test coverage > 80%
- ✅ No linting errors (flake8)
- ✅ Follows project code style
