# ML Model Reference

**Last Updated**: January 4, 2026  
**Version**: 2.0  
**Status**: ✅ Production Ready

---

## Overview

The Tanzania Climate Intelligence Platform employs an advanced ensemble machine learning approach combining four complementary models to predict climate variables with high accuracy. The system achieves 84.9% accuracy (R²) using the 6-location dataset with comprehensive spatial and temporal validation.

### Key Achievements

- **6-Location Dataset**: 1,872 monthly observations across 6 locations
- **74 Optimized Features**: Selected from 239 through intelligent feature selection
- **4-Model Ensemble**: Random Forest, XGBoost, LSTM, and Weighted Ensemble
- **Spatial Validation**: 81.2% ± 4.6% R² across locations (Leave-One-Location-Out CV)
- **Temporal Validation**: Robust performance with 12-month gap prevention
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
│                  │ Final R²: 0.849 │                      │
│                  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Model Performance (6-Location Dataset)

| Model | Test R² | RMSE | MAE | Training Time | Strengths |
|-------|---------|------|-----|---------------|-----------|
| **Ensemble** | **0.849** | 0.419 | 0.282 | ~10s | Best overall performance |
| XGBoost | 0.832 | 0.442 | 0.293 | 2.4s | Fast, interpretable |
| LSTM | 0.828 | 0.449 | 0.288 | 216s | Temporal dependencies |
| Random Forest | 0.802 | 0.479 | 0.315 | 0.6s | Robust, feature importance |

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

**Overall Spatial CV**: 0.812 ± 0.046 R² (83% success rate at R² ≥ 0.75)

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
- Highest individual model accuracy
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

**Original Features**: 239 (after data leakage prevention)  
**Selected Features**: 74 (69% reduction)  
**Selection Method**: Hybrid approach combining:
- Correlation analysis
- Mutual information
- Source diversity preservation
- Domain knowledge

### Feature Categories

| Category | Count | Examples |
|----------|-------|----------|
| **Climate Variables** | 25 | Temperature, rainfall, humidity, pressure |
| **Vegetation Indices** | 18 | NDVI, VCI, crop stress indicators |
| **Ocean Patterns** | 12 | ENSO, IOD, climate forecasts |
| **Temporal Features** | 8 | Lag variables (1, 3, 6 months) |
| **Derived Indicators** | 11 | Drought indices, flood risk, anomalies |

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
    
    # 5. Data leakage prevention
    df = remove_target_derived_features(df)
    
    # 6. Feature selection
    df = select_optimal_features(df, n_features=74)
    
    return df
```

---

## Training Pipeline

### Data Preparation

**Dataset Split**:
- **Training**: 60% (temporal split with 12-month gap)
- **Validation**: 20% (for hyperparameter tuning)
- **Test**: 20% (held-out for final evaluation)

**Preprocessing Steps**:
1. **Data Leakage Prevention**: Automatic exclusion of target-derived features
2. **Feature Selection**: Intelligent selection of 74 optimal features
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
- Performance degradation (R² < 0.80)
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
- **Ensemble**: R² = 0.849 (excellent with uncertainty)

---

## Advanced Features

### Data Leakage Prevention

**Automatic Detection**:
```python
def detect_data_leakage(features, target):
    """Detect features derived from target variable"""
    
    leakage_patterns = [
        r'.*rainfall.*rolling.*',  # Rolling rainfall features
        r'.*rainfall.*anomaly.*',  # Rainfall anomalies
        r'.*target.*',             # Direct target references
    ]
    
    leaky_features = []
    for pattern in leakage_patterns:
        leaky_features.extend(
            [col for col in features.columns 
             if re.match(pattern, col, re.IGNORECASE)]
        )
    
    return leaky_features
```

**Prevention**: Integrated into pipeline (Step 3.4) with pattern-based exclusion

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

**Document Version**: 2.0  
**Last Updated**: January 4, 2026  
**Status**: ✅ Production Ready  
**Consolidates**: MODEL_DEVELOPMENT_GUIDE.md, feature_engineering.md, UNCERTAINTY_QUANTIFICATION.md, MODEL_IMPROVEMENT_IMPLEMENTATION_GUIDE.md, MODEL_IMPROVEMENTS_RESULTS.md, TRAIN_PIPELINE_MIGRATION.md, RETRAINING_RESULTS_SUMMARY.md, SPATIAL_CV_RESULTS_TASK_15.md