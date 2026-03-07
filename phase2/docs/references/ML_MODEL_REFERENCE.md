# ML Model Reference

**Last Updated**: March 5, 2026
**Version**: 3.2
**Status**: ✅ Production Ready

---

## Overview

The Tanzania Climate Intelligence Platform employs an advanced ensemble machine learning approach combining four complementary models to predict climate variables with high accuracy. The system achieves 86.7% accuracy (R²) using XGBoost on the 6-location dataset with proper temporal gap validation (12-month gaps between train/val/test splits). Following a data leakage fix (11 rainfall-derived features removed), the pipeline now uses `utils/data_leakage_prevention.py` for systematic leakage detection instead of hardcoded patterns.

### Key Achievements

- **6-Location Dataset**: 1,872 monthly observations across 6 locations
- **83 Optimized Features**: Selected from 245 through intelligent hybrid feature selection (11 leaky rainfall-derived features removed)
- **4-Model Ensemble**: Random Forest, XGBoost, LSTM, and Weighted Ensemble
- **Temporal Validation**: 0.8566 ± 0.0575 R² (RF CV), 0.8396 ± 0.0603 R² (XGB CV, 5-fold temporal CV)
- **Temporal Validation**: Robust performance with 12-month gap between train/val/test splits
- **Uncertainty Quantification**: 95% prediction intervals for risk assessment

---

## Model Architecture

### Ensemble Approach

The system combines four complementary models to leverage their individual strengths:

```
┌─────────────────────────────────────────────────────────────┐
│                    ENSEMBLE ARCHITECTURE                     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Random Forest│  │   XGBoost    │  │     LSTM     │     │
│  │   (30%)      │  │    (40%)     │  │    (30%)     │     │
│  │              │  │              │  │              │     │
│  │ • Non-linear │  │ • Gradient   │  │ • Temporal   │     │
│  │ • Robust     │  │   boosting   │  │   patterns   │     │
│  │ • Feature    │  │ • High       │  │ • Sequential │     │
│  │   importance │  │   accuracy   │  │   learning   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │             │
│         └─────────────────┼─────────────────┘             │
│                           │                               │
│                           ▼                               │
│                  ┌─────────────────┐                      │
│                  │ Weighted Average│                      │
│                  │   Ensemble      │                      │
│                  │                 │                      │
│                  │ Final R²: 0.840 │                      │
│                  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Model Performance (6-Location Dataset)

| Model | Test R² | RMSE | MAE | Strengths |
|-------|---------|------|-----|-----------|
| **XGBoost** | **0.8666** | **0.4008** | **0.2518** | **Best by R², fast, interpretable** |
| Ensemble | 0.8402 | 0.4387 | 0.2784 | Robust generalization |
| LSTM | 0.7866 | 0.5103 | 0.3286 | Temporal dependencies |
| Random Forest | 0.7814 | 0.5131 | 0.3201 | Robust, feature importance |

**Active Model for Serving**: Primary = XGBoost (R²=0.8666, highest test R²), Fallback = LSTM (R²=0.7866)

> **Note (March 2026 Data Leakage Fix)**: 11 rainfall-derived features (precip_mm, flood_trigger, is_dry_day, consecutive_dry_days, heavy_rain_days_30day, cumulative_excess_7day, and all their lags/rolling variants) were identified as data leakage and removed. The pipeline now uses `utils/data_leakage_prevention.py` for systematic detection. Original features reduced from 279 to 245 before selection; selected features reduced from 84 to 83.

### Spatial Cross-Validation Results

**Leave-One-Location-Out (LOLO) Performance**:

| Location | R² | RMSE | Climate Zone | Performance |
|----------|-----|------|--------------|-------------|
| **Morogoro** | 0.855 | 0.356 | Tropical transition | Excellent |
| **Mbeya** | 0.855 | 0.410 | Highland | Excellent |
| **Mwanza** | 0.846 | 0.351 | Lake region | Excellent |
| **Dodoma** | 0.816 | 0.442 | Semi-arid | Strong |
| **Dar es Salaam** | 0.765 | 0.442 | Coastal | Good |
| **Arusha** | 0.737 | 0.461 | Highland | Good |

**Overall Temporal CV (5-fold, Mar 2026 Retraining with Data Leakage Fix)**:

| Model | CV R² Mean ± Std | 95% CI |
|-------|-------------------|--------|
| **Random Forest** | **0.8566 ± 0.0575** | [0.7852, 0.9281] |
| **XGBoost** | 0.8396 ± 0.0603 | [0.7647, 0.9145] |

---

## Individual Model Details

### 1. Random Forest

**Architecture**:
- 200 decision trees
- Maximum depth: 15
- Bootstrap sampling with replacement
- Feature bagging (sqrt(n_features) per split)

**Strengths**:
- Robust to outliers and missing data
- Provides feature importance rankings
- Handles non-linear relationships naturally
- Fast training and prediction

**Configuration**:
```python
RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)
```

**Feature Importance**: Top predictive features identified through Gini importance

### 2. XGBoost

**Architecture**:
- Gradient boosting with 200 estimators
- Learning rate: 0.05 (conservative for stability)
- Maximum depth: 6
- L1 (alpha=0.1) and L2 (lambda=1.0) regularization

**Strengths**:
- Strong individual model accuracy
- Excellent handling of complex interactions
- Built-in regularization prevents overfitting
- Fast training with GPU support

**Configuration**:
```python
XGBRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=6,
    alpha=0.1,
    lambda=1.0,
    random_state=42
)
```

**Feature Importance**: Gain-based importance for interpretability

### 3. LSTM Neural Network

**Architecture**:
- 2 LSTM layers: [128, 64] units
- Sequence length: 6 months
- Dropout: 0.3 for regularization
- Dense output layer with linear activation

**Strengths**:
- Captures temporal dependencies and seasonal patterns
- Learns complex sequential relationships
- Handles variable-length sequences
- Memory of long-term patterns

**Configuration**:
```python
Sequential([
    LSTM(128, return_sequences=True, dropout=0.3),
    LSTM(64, dropout=0.3),
    Dense(1, activation='linear')
])
```

**Training**: Early stopping with patience=10, validation monitoring

### 4. Weighted Ensemble

**Combination Strategy**:
- Random Forest: 30% weight
- XGBoost: 40% weight (highest individual performance)
- LSTM: 30% weight

**Benefits**:
- Reduces individual model biases
- Improves generalization across different scenarios
- Provides more reliable predictions
- Enables uncertainty quantification

**Implementation**:
```python
ensemble_prediction = (
    0.30 * rf_prediction +
    0.40 * xgb_prediction +
    0.30 * lstm_prediction
)
```

---

## Feature Engineering

### Feature Selection Process

**Original Features**: 245 (after feature engineering with atmospheric data; reduced from 279 after removing 11 leaky rainfall-derived features)
**Selected Features**: 83 (66% reduction)
**Selection Method**: Hybrid approach combining:
- Correlation analysis
- Mutual information
- Source diversity preservation
- Domain knowledge

### Feature Categories

| Category | Count | Examples |
|----------|-------|----------|
| **ERA5 (Atmospheric)** | 15 | Temperature, humidity, pressure, wind, dewpoint |
| **Vegetation (NDVI)** | 34 | NDVI, VCI, crop stress indicators, anomalies |
| **NASA POWER** | 17 | Solar radiation, PET, temperature derivatives |
| **CHIRPS (Rainfall)** | 0 | Removed (data leakage -- all rainfall-derived features excluded) |
| **Ocean Indices** | 5 | ENSO intensity, critical period indicators |
| **Other** | 12 | Soil moisture, seasonal indicators, temperature derivatives |

### Key Predictive Features

**Top 10 Features by Importance**:
1. Recent rainfall patterns (3-month rolling average)
2. ENSO indicators (Niño 3.4 index)
3. Vegetation health (NDVI lag features)
4. Temperature extremes (heat stress days)
5. Indian Ocean Dipole patterns
6. Rainfall anomalies (standardized)
7. Vegetation condition index
8. Atmospheric pressure patterns
9. Seasonal indicators
10. Location encoding

### Feature Engineering Pipeline

```python
def engineer_features(df):
    """Complete feature engineering pipeline"""
    
    # 1. Temporal features
    df = create_lag_features(df, lags=[1, 3, 6])
    df = create_rolling_features(df, windows=[3, 6])
    
    # 2. Climate interactions
    df = create_climate_interactions(df)
    df = create_ocean_interactions(df)
    
    # 3. Vegetation features
    df = create_vegetation_features(df)
    
    # 4. Anomaly detection
    df = create_anomaly_features(df)
    
    # 5. Data leakage prevention (utils/data_leakage_prevention.py)
    df = remove_leaky_features(df)  # Removes 11 rainfall-derived features

    # 6. Feature selection
    df = select_optimal_features(df, n_features=83)
    
    return df
```

---

## Training Pipeline

### Data Preparation

**Dataset Split** (with 12-month gaps between splits to prevent temporal leakage):
- **Training**: 1,122 samples, Jan 2000 -- Jul 2015
- **Validation**: 372 samples, Aug 2016 -- Sep 2021 (12-month gap after train)
- **Test**: 240 samples, Oct 2022 -- Jan 2026 (12-month gap after val)

**Preprocessing Steps**:
1. **Data Leakage Prevention**: Automatic exclusion of 11 rainfall-derived features via `utils/data_leakage_prevention.py`
2. **Feature Selection**: Intelligent selection of 83 optimal features from 245 candidates
3. **Missing Value Handling**: Median imputation after feature selection
4. **Normalization**: Z-score standardization
5. **Sequence Preparation**: 6-month sequences for LSTM

### Training Process

**Automated Pipeline** (`train_pipeline.py`):
```bash
# Complete training pipeline
python train_pipeline.py

# Specific models only
python train_pipeline.py --models rf,xgb

# Custom configuration
python train_pipeline.py --config custom_config.json
```

**Training Steps**:
1. Load and preprocess 6-location dataset
2. Apply feature engineering and selection
3. Split data temporally with gap prevention
4. Train individual models with cross-validation
5. Create weighted ensemble
6. Generate comprehensive evaluation reports
7. Save models and metadata

### Model Validation

**Temporal Cross-Validation**:
- 5-fold expanding window
- 12-month gap between train/test
- Prevents future data leakage

**Spatial Cross-Validation**:
- Leave-One-Location-Out (LOLO)
- Tests generalization to unseen locations
- Validates spatial robustness

**Performance Metrics**:
- R² (coefficient of determination)
- RMSE (root mean squared error)
- MAE (mean absolute error)
- Spatial CV statistics

---

## Uncertainty Quantification

### Prediction Intervals

The system provides 95% confidence intervals for all predictions using ensemble variance:

```python
def calculate_prediction_intervals(predictions_list, confidence=0.95):
    """Calculate prediction intervals from ensemble"""
    
    quantiles = [
        (1 - confidence) / 2,  # Lower bound
        0.5,                   # Median
        1 - (1 - confidence) / 2  # Upper bound
    ]
    
    return np.percentile(predictions_list, 
                        [q * 100 for q in quantiles], 
                        axis=0)
```

**Benefits**:
- Risk-informed decision making
- Insurance reserve planning
- Agricultural planning with uncertainty
- Model confidence assessment

### Uncertainty Sources

1. **Model Uncertainty**: Disagreement between models
2. **Data Uncertainty**: Measurement and processing errors
3. **Temporal Uncertainty**: Future climate variability
4. **Spatial Uncertainty**: Location-specific variations

---

## Model Deployment

### Model Artifacts

**Saved Models**:
```
outputs/models/
├── random_forest_climate.pkl          # Random Forest model
├── xgboost_climate.pkl               # XGBoost model
├── lstm_climate.keras                # LSTM model
├── ensemble_climate_config.json      # Ensemble configuration
├── feature_selection_results.json    # Selected features
└── scaler_params.json               # Normalization parameters
```

**Metadata Files**:
```
outputs/models/
├── random_forest_climate_metadata.json
├── xgboost_climate_metadata.json
├── lstm_climate_metadata.json
├── ensemble_climate_metadata.json
└── training_results_YYYYMMDD_HHMMSS.json
```

### Production Inference

**Single Prediction**:
```python
from models.ensemble_predictor import EnsemblePredictor

# Load trained ensemble
predictor = EnsemblePredictor.load('outputs/models/')

# Make prediction with uncertainty
prediction, lower_bound, upper_bound = predictor.predict_with_uncertainty(
    features, confidence=0.95
)

print(f"Prediction: {prediction:.2f}")
print(f"95% CI: [{lower_bound:.2f}, {upper_bound:.2f}]")
```

**Batch Predictions**:
```python
# Batch processing for multiple locations/times
predictions = predictor.predict_batch(features_batch)
```

### Model Monitoring

**Performance Tracking**:
- Prediction accuracy over time
- Model drift detection
- Feature importance stability
- Uncertainty calibration

**Retraining Triggers**:
- Performance degradation (R² < 0.75)
- Significant data drift
- New location additions
- Seasonal recalibration

---

## Evaluation and Validation

### Comprehensive Testing

**Test Coverage**: 80%+ across all model components

**Test Types**:
- **Unit Tests**: Individual model components
- **Integration Tests**: End-to-end pipeline
- **Property-Based Tests**: Model correctness properties
- **Performance Tests**: Speed and memory benchmarks

### Model Validation Framework

**Validation Checks**:
1. **Overfitting Detection**: Train vs. validation performance
2. **Feature Leakage**: Automated target-derived feature detection
3. **Temporal Consistency**: No future data in training
4. **Spatial Generalization**: LOLO cross-validation
5. **Uncertainty Calibration**: Prediction interval coverage

### Performance Benchmarks

**Baseline Comparisons**:
- Persistence model: R² = -1.03 (poor)
- Mean model: R² = 0.00 (poor)
- Linear Ridge: R² = 0.973 (strong baseline)
- **XGBoost**: R² = 0.8666 (best model after leakage fix)
- **Ensemble**: R² = 0.8402 (robust with uncertainty)

---

## Advanced Features

### Data Leakage Prevention

**Systematic Detection via `utils/data_leakage_prevention.py`**:

In March 2026, a comprehensive audit identified 11 rainfall-derived features as data leakage (precip_mm, flood_trigger, is_dry_day, consecutive_dry_days, etc.). These features were derived from the prediction target (rainfall) and artificially inflated model performance.

The pipeline now uses a dedicated module instead of hardcoded regex patterns:

```python
from utils.data_leakage_prevention import remove_leaky_features

# Removes all rainfall-derived features systematically
# 11 features removed, reducing candidates from 279 to 245
df = remove_leaky_features(df)
```

**Prevention**: Integrated into the training pipeline before feature selection. The `data_leakage_prevention` module maintains the canonical list of leaky feature patterns and is the single source of truth.

### Feature Importance Analysis

**Multi-Model Importance**:
- Random Forest: Gini importance
- XGBoost: Gain-based importance
- LSTM: Gradient-based attribution
- Ensemble: Weighted average importance

**Visualization**:
```python
def plot_feature_importance(importance_dict, top_n=20):
    """Plot feature importance across models"""
    
    # Combine importance from all models
    combined_importance = combine_importance_scores(importance_dict)
    
    # Plot top features
    plt.figure(figsize=(12, 8))
    plt.barh(range(top_n), combined_importance[:top_n])
    plt.title('Top Feature Importance (Ensemble)')
    plt.show()
```

### Hyperparameter Optimization

**Automated Tuning**:
```python
def optimize_hyperparameters(model_type, X_train, y_train):
    """Optimize hyperparameters using Bayesian optimization"""
    
    search_spaces = {
        'random_forest': {
            'n_estimators': (100, 500),
            'max_depth': (10, 30),
            'min_samples_split': (2, 20)
        },
        'xgboost': {
            'learning_rate': (0.01, 0.3),
            'max_depth': (3, 10),
            'n_estimators': (100, 1000)
        }
    }
    
    # Bayesian optimization with cross-validation
    best_params = bayesian_optimize(
        model_type, 
        search_spaces[model_type],
        X_train, y_train,
        cv=5
    )
    
    return best_params
```

---

## Performance Optimization

### Training Optimization

**Parallel Processing**:
- Multi-core training for Random Forest
- GPU acceleration for XGBoost
- Batch processing for LSTM
- Concurrent model training

**Memory Optimization**:
- Efficient data loading with Parquet
- Feature selection reduces memory usage
- Batch processing for large datasets
- Model compression for deployment

### Inference Optimization

**Fast Prediction**:
- Model caching in memory
- Batch prediction support
- Optimized feature preprocessing
- Parallel ensemble inference

**Typical Performance**:
- Single prediction: <10ms
- Batch prediction (100 samples): <100ms
- Model loading: <2 seconds
- Memory usage: <500MB

---

## Troubleshooting

### Common Issues

#### Low Model Performance
**Symptoms**: R² < 0.80, high RMSE  
**Solutions**:
1. Check data quality and completeness
2. Verify feature engineering pipeline
3. Tune hyperparameters
4. Add more relevant features
5. Increase training data

#### Overfitting
**Symptoms**: High train R², low validation R²  
**Solutions**:
1. Increase regularization
2. Reduce model complexity
3. Add more training data
4. Improve feature selection
5. Use cross-validation

#### Data Leakage
**Symptoms**: Unrealistic performance (R² > 0.95)  
**Solutions**:
1. Run leakage detection
2. Remove target-derived features
3. Verify temporal splits
4. Check feature engineering logic

#### Memory Issues
**Symptoms**: Out of memory errors  
**Solutions**:
1. Reduce batch sizes
2. Use feature selection
3. Optimize data types
4. Process in chunks

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| M001 | Model loading failed | Check file paths and permissions |
| M002 | Feature mismatch | Verify feature preprocessing |
| M003 | Prediction failed | Check input data format |
| M004 | Memory exceeded | Reduce batch size or features |
| M005 | Training timeout | Reduce model complexity |

---

## Future Enhancements

### Planned Improvements

**Model Architecture**:
- Transformer-based models for temporal patterns
- Graph neural networks for spatial relationships
- Attention mechanisms for feature importance
- Multi-task learning for related predictions

**Advanced Features**:
- Online learning for continuous updates
- Federated learning across locations
- Causal inference for climate relationships
- Explainable AI for model interpretability

**Performance**:
- Model quantization for faster inference
- Distributed training across multiple GPUs
- Real-time prediction streaming
- Edge deployment optimization

---

## Related Documentation

- **[DATA_PIPELINE_REFERENCE.md](./DATA_PIPELINE_REFERENCE.md)** - Data pipeline details
- **[TESTING_REFERENCE.md](./TESTING_REFERENCE.md)** - Testing documentation
- **[DEPLOYMENT_REFERENCE.md](./DEPLOYMENT_REFERENCE.md)** - Deployment guide
- **[feature_engineering.md](./feature_engineering.md)** - Feature engineering details
- **[UNCERTAINTY_QUANTIFICATION.md](./UNCERTAINTY_QUANTIFICATION.md)** - Uncertainty methods

---

**Document Version**: 3.2
**Last Updated**: March 5, 2026
**Status**: ✅ Production Ready
**Consolidates**: MODEL_DEVELOPMENT_GUIDE.md, feature_engineering.md, UNCERTAINTY_QUANTIFICATION.md, MODEL_IMPROVEMENT_IMPLEMENTATION_GUIDE.md, MODEL_IMPROVEMENTS_RESULTS.md, TRAIN_PIPELINE_MIGRATION.md, RETRAINING_RESULTS_SUMMARY.md, SPATIAL_CV_RESULTS_TASK_15.md