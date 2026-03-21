# ML Model Reference

**Last Updated**: March 8, 2026
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

**Active Model for Serving**: XGBoost only (R²=0.8666, highest test R²). LSTM and Ensemble are training-reference models — **no fallback in production**. Shadow run integrity requires the primary model exclusively; fallback candidates were removed Mar 10 2026 (commit `97da796`).

> **Mar 10 2026 Update**: `load_model()` in `forecast_service.py` now enforces primary-only loading with a hard error if the primary model file is missing. Probability conversion also updated: raw model output (z-score) is now converted to trigger probability via `norm.cdf((phase_threshold - predicted_mm) / rmse_mm)` using Kilombero rice phase thresholds — replacing the physically meaningless sigmoid. See `_raw_to_probability()` in `forecast_service.py`.

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

## Inference Mechanics — How Forecasts Are Generated at Runtime

> This section describes the serving-time pipeline: how ingested data is transformed into forecast probabilities each day. This is distinct from model training (covered above) and data ingestion (covered in DATA_PIPELINE_REFERENCE.md).

---

### Step 1 — Daily Ingestion (Collect)

Every day at 06:00 EAT the pipeline fetches incremental updates from five climate sources:

| Source | Provides | Typical Cadence |
|---|---|---|
| CHIRPS | Rainfall (5km satellite grid) | Monthly +10–15 day lag |
| NASA POWER | Temperature, humidity | Daily +1–2 days |
| ERA5 | Wind, pressure, solar radiation, soil moisture | Monthly +2–3 month lag |
| NDVI | Vegetation health index | 16-day composite +5–10 days |
| Ocean Indices | ENSO, IOD (El Niño / Indian Ocean Dipole) | Monthly +10 days |

**Incremental logic:** On the first run, 180 days of history are fetched. Every subsequent run fetches only records newer than the last successful ingestion date (`SourceIngestionTracking` table). Sources returning 0 records on a given day means nothing new exists since the last fetch — this is normal, not a failure.

All records are stored in the `ClimateData` table as **monthly aggregates** at Morogoro's coordinates (lat/lon ±0.01° tolerance).

---

### Step 2 — Feature Preparation (Lookback)

At forecast time, the pipeline looks back **12 months** from today and queries all `ClimateData` records in that window for Morogoro. A minimum of **6 monthly records** is required — if fewer exist, the run is skipped rather than fabricating data (GOTCHA Law #1: no synthetic fallbacks).

From those ~12 monthly rows it engineers **83 features**: lagged values, rolling averages, seasonal signals, ENSO/IOD state, vegetation indices, and GDD-derived crop phase indicators.

> **Note on MEMORY.md:** The project memory references "7 months + `.replace(day=1)`" as the lookback. The code uses 12 months in `prepare_features()` (`forecast_service.py`) and 7 months in earlier lookback utilities. The 12-month window is the operative value at forecast generation time; the 7-month reference relates to the data availability check used upstream.

---

### Step 3 — Model Prediction (Single Run)

The XGBoost model takes the 83-feature vector and outputs a **z-score** — a normalized rainfall value relative to Morogoro's historical distribution:

```
Mean:  79.15 mm/month  (derived from 312 records, 2000-2025)
Std:   77.06 mm/month
RMSE:  33.1 mm          (test-set RMSE = 0.43 z-score × 77.06)
```

The z-score is converted back to millimetres:
```
predicted_mm = z_score × 77.06 + 79.15
```

**The model runs once per trigger type.** It produces one rainfall prediction. The four horizon outputs are derived from this single prediction, not from four separate model runs.

---

### Step 4 — Horizon Splitting and Probability Conversion

The single rainfall prediction is evaluated against four future target months (3, 4, 5, 6 months ahead). For each target month:

1. **Identify crop phase** — map target month to the Kilombero rice calendar:

```
Wet season (Jan planting → Jun harvest):
  Jan → germination  (min 50mm)
  Feb–Mar → vegetative  (min 100mm)
  Apr → flowering  (min 120mm)  ← CRITICAL, highest threshold
  May → grain_fill  (min 60mm)
  Jun → harvesting  (min 0mm, needs dry: <80mm excessive)

Dry season (Jul planting → Dec harvest):
  Jul → germination  (min 50mm)
  Aug–Sep → vegetative  (min 100mm)
  Oct → flowering  (min 120mm)  ← CRITICAL
  Nov → grain_fill  (min 60mm)
  Dec → harvesting  (min 0mm, needs dry)
```

2. **Calculate probability** using the normal distribution CDF (Cumulative Distribution Function):

**What CDF means here:** The model predicts a single rainfall value (e.g. 45mm), but that prediction carries uncertainty measured by the model's RMSE (33.1mm). The CDF answers: *"given this predicted value and this uncertainty, what is the probability that actual rainfall lands below (or above) the threshold?"* It converts a point prediction into a probability by integrating the uncertainty distribution up to the threshold.

**Why CDF is the right approach:** Instead of a binary "predicted rainfall < threshold = drought risk", the CDF quantifies *how likely* the threshold is to be breached, proportional to how close the prediction is to the threshold relative to the model's own measured error. A prediction of 45mm against a 120mm drought threshold (75mm gap, RMSE 33mm) gives a very different probability than a prediction of 115mm against the same threshold (5mm gap, same RMSE). The uncertainty is grounded in real test-set performance — not assumed.

**Example:**
```
Predicted rainfall: 45mm  |  Drought threshold: 120mm  |  RMSE: 33.1mm
CDF((120 - 45) / 33.1) = CDF(2.27) ≈ 99% drought probability

Predicted rainfall: 115mm  |  Drought threshold: 120mm  |  RMSE: 33.1mm
CDF((120 - 115) / 33.1) = CDF(0.15) ≈ 56% drought probability
```

**Formulas by trigger type:**
```
Drought:      P(actual_mm < min_threshold)  = CDF((threshold_min - predicted_mm) / RMSE)
Flood:        P(actual_mm > excessive)       = 1 - CDF((threshold_excessive - predicted_mm) / RMSE)
Crop failure: P(actual_mm < 50% of min)     = CDF((threshold_min × 0.5 - predicted_mm) / RMSE)
```

For flood the formula is inverted (`1 - CDF`) because flood asks "what is the probability actual rainfall exceeds the threshold" rather than falls below it.

3. **Assign confidence intervals:**
```
base_uncertainty = 0.15
horizon_uncertainty = 0.15 + (0.02 × (horizon_months - 3))
confidence_lower = max(0, probability - horizon_uncertainty)
confidence_upper = min(1, probability + horizon_uncertainty)
```

This produces 12 `ForecastLog` entries per run: 3 trigger types × 4 horizons.

---

### Step 5 — Horizon Tier Assignment

| Horizon | Tier | Meaning |
|---|---|---|
| 3 months | **Primary** | Insurance trigger eligible — reliable enough to earmark reserves |
| 4 months | **Primary** | Insurance trigger eligible |
| 5 months | **Advisory** | Early warning only — not a payout trigger |
| 6 months | **Advisory** | Early warning only — directional signal only |

Only **primary-tier** forecasts (≤4 months, ≥75% probability) are counted in financial exposure calculations and reserve sizing. Advisory-tier forecasts are surfaced on the dashboard but excluded from payout logic.

---

### The Full Inference Chain

```
06:00 EAT daily
    ↓
Fetch new climate records (incremental, 5 sources)
    ↓
Store as monthly aggregates → ClimateData table
    ↓
Look back 12 months → query 6–12 monthly records
    ↓
Engineer 83 features
    ↓
XGBoost: features → z-score → predicted_mm
    ↓
For each of 3 trigger types × 4 horizons:
  → target_date = today + horizon months
  → season = 'dry' if month in (7-12) else 'wet'
  → crop phase = calendar lookup (wet/dry season dict)
  → threshold = RAINFALL_THRESHOLDS[crop_phase]
  → probability = CDF calculation (trigger-type specific)
  → tier = 'primary' if horizon ≤ 4 else 'advisory'
    ↓
12 ForecastLog entries written → Evidence Pack grows
```

> **Key design point:** The model does not predict "what happens in 3 months" vs "what happens in 6 months" separately. It predicts the current climate trajectory once. The horizon granularity comes entirely from applying different crop-phase thresholds to the same prediction — the threshold and crop phase change per horizon, not the underlying model output.

---

## Future Enhancements

### Where HewaSense Sits on the ML Frontier

The current system is deliberately pragmatic — not cutting-edge research ML, but well above the baseline for smallholder parametric insurance in East Africa. Understanding where the frontier is, and what's realistically achievable at HewaSense scale, informs the improvement roadmap.

**The current frontier (what "cutting-edge" looks like for this problem):**

| Approach | Examples | What it offers |
|---|---|---|
| **Climate foundation models** | Google DeepMind GraphCast, ECMWF AIFS, Huawei Pangu-Weather | Large NNs trained on decades of global ERA5 reanalysis; GraphCast (2023) outperforms ECMWF NWP at 10-day forecasts. Training requires petabyte-scale data and million-dollar compute budgets. |
| **Calibrated ensemble forecasting** | ECMWF ENS (51 perturbed members) | Derives probabilities from ensemble *spread* rather than a single prediction + RMSE approximation. Spread varies by climate state (La Niña year ≠ neutral year uncertainty). More honest than fixed RMSE-based CDF. |
| **Deep learning downscaling** | Diffusion models, convolutional super-resolution | Takes coarse 50km ERA5 data and produces sub-kilometre resolution — would close the ERA5 (50km) vs CHIRPS (5km) spatial mismatch. |
| **Physics-informed neural networks** | PINNs, NeuralODE | Embeds atmospheric physics equations as constraints; better generalisation under climate change scenarios outside training distribution. |
| **Farm-level real-time verification** | Satellite/drone soil moisture + crop stress at field resolution | Near-real-time trigger verification; near-eliminates basis risk. |

**Why HewaSense does not need foundation models to succeed:**
The constraint limiting impact here is not model sophistication — it is getting any reliable, affordable parametric insurance to Tanzanian smallholders at all. XGBoost at R²=0.8666 with phase-aware thresholds and ENSO/IOD features is more than sufficient for the current pilot and regulatory context. The Brier Score from the shadow run will determine what actually needs improving, not theoretical benchmarks.

---

### Realistic Improvement Path (achievable at HewaSense scale)

These improvements capture most of the frontier benefit without the compute or team requirements of foundation models. They are sequenced by impact and readiness.

**Phase 1 — Post-shadow-run (Q3 2026), triggered by Brier Score results:**

- **Probability calibration (Platt scaling / isotonic regression):** If the shadow run reveals systematic over- or under-confidence in the CDF probability estimates, apply post-hoc calibration to the XGBoost outputs. ~1 week effort. Highest impact per unit of work.

- **Horizon-specific Brier Score comparison:** Evaluate whether advisory-tier (5–6mo) forecasts are materially worse than primary-tier (3–4mo). If yes, proceed to Phase 2 horizon-specific models. If comparable, the current single-run design is validated.

**Phase 2 — Scale preparation (Q4 2026 / Q1 2027):**

- **ECMWF SEAS5 seasonal forecasts as input features:** SEAS5 is a state-of-the-art seasonal forecast system specifically designed for 1–7 month horizons in Africa. Incorporating SEAS5 ensemble members as features effectively outsources the multi-step forecasting problem to ECMWF's operational system — a ~2-week integration that would materially improve longer-horizon skill without building a new model. API access is available at research pricing (~€500/yr). This is the single highest-leverage improvement available.

- **ERA5-Land (9km) replacing ERA5 (50km):** ECMWF's ERA5-Land product provides the same variables at 9km resolution. Switching the ERA5 ingestion module to ERA5-Land would close the spatial resolution gap between CHIRPS (5km) and the current 50km ERA5 variables (temperature, humidity, soil moisture). ~1 week effort.

- **SEAS5 ensemble spread as uncertainty estimate:** Replace the fixed RMSE-based CDF uncertainty with the actual spread of the SEAS5 ensemble members at each forecast point. This means the confidence intervals widen in uncertain climate states (e.g., ENSO transition years) and narrow when the signal is strong — more actuarially honest than a static ±0.15 band.

**Phase 3 — Longer-term (post-commercialisation):**

- **Ensemble forecasting (multiple XGBoost models with perturbed inputs):** Generate an internal ensemble by running the model with bootstrap-sampled feature sets. Derive probabilities from ensemble spread rather than RMSE-CDF. More expensive but produces calibrated uncertainty without depending on external APIs.
- **Deep learning downscaling:** If sub-kilometre resolution matters for Kilombero Basin sub-zones, apply convolutional or diffusion-model downscaling to ERA5 inputs.
- **Causal climate teleconnection modelling:** Replace correlation-based ENSO/IOD features with causal inference models that are more robust to distributional shift under climate change.

---

### How These Improvements Translate to the Parametric Insurance Product

Every ML improvement in this roadmap has a direct downstream effect on the insurance product — reserve sizing, premium accuracy, reinsurability, farmer protection, and basis risk. The table below maps each technical improvement to its product impact.

| Improvement | Technical Effect | Insurance Product Impact |
|---|---|---|
| **Probability calibration (Phase 1)** | Corrects systematic over/under-confidence in CDF probability estimates | Reserve sizing becomes accurate — currently reserves are sized on potentially miscalibrated probabilities. Miscalibrated upward = over-reserved (locked capital); downward = under-reserved (solvency risk). Directly improves actuarial credibility with TIRA and reinsurers. |
| **Brier Score evidence pack (Phase 1)** | Forward-validated probability calibration on real 2026 data | The single most important reinsurance artefact. A Brier Score < 0.25 on real forward data is the difference between "backtested model" and "underwriteable product." Unlocks reinsurance conversations. |
| **ECMWF SEAS5 features (Phase 2)** | Multi-month ensemble forecast skill from ECMWF's operational seasonal system incorporated as input features | Earlier trigger signals: a developing La Niña identified 5 months ahead gives farmers time to switch varieties, delay planting, or purchase additional protection. Extends reliable forecast lead time. Reinsurers gain independent signal validation — SEAS5 is a globally recognised system, not proprietary to HewaSense. |
| **SEAS5 ensemble spread as uncertainty (Phase 2)** | Dynamic confidence intervals that widen in uncertain climate states (ENSO transition years) and narrow when signal is strong | Reserve sizing becomes dynamic rather than static. In a strong La Niña year the 75% drought probability may become 88% — reserves adjust automatically, reducing the risk of being undercapitalised precisely when payouts are most likely. Premiums can be priced dynamically by season, improving long-run sustainability. |
| **ERA5-Land 9km replacing ERA5 50km (Phase 2)** | Closes the spatial resolution gap between CHIRPS (5km) and current temperature/humidity/soil moisture inputs (50km) | Reduces basis risk. The 50km ERA5 grid means the model currently reads climate conditions averaged over a ~50×50km cell. Kilombero Basin farm conditions within that cell can vary significantly. ERA5-Land at 9km better matches what farmers actually experience, reducing the gap between index trigger and farm-level outcome. |
| **Horizon-specific models (Phase 2, if triggered)** | Separate calibrated models for each forecast horizon | Enables expanding primary tier to 5 months if accuracy holds → larger trigger-eligible window → more farmer protection per premium dollar. More advance notice of trigger risk = more time to arrange reinsurance capital before a payout event. |
| **Internal ensemble forecasting (Phase 3)** | Probability estimates derived from ensemble spread rather than RMSE-CDF approximation | More honest uncertainty quantification at every climate state. Actuaries can price reinsurance more accurately. Premiums can reflect genuine seasonal risk variation rather than a fixed annual loss ratio. |
| **Causal teleconnection modelling (Phase 3)** | Climate relationships modelled causally rather than by correlation | Robustness under climate change: as historical rainfall patterns shift, correlation-based models degrade. Causal models are more stable across distributional shift — important for a 10–20 year product horizon. Makes the product defensible to regulators who ask "what happens when historical patterns change?" |

**The overall product evolution trajectory:**

- **Today (shadow run):** Proof-of-concept phase. XGBoost with CDF probabilities. Evidence pack accumulating. Not yet reinsureable on forward data alone.

- **Post-shadow-run (Q3 2026):** Brier Score available. Probability calibration applied. Evidence pack complete. First reinsurance conversations possible — product moves from "backtested" to "forward-validated."

- **SEAS5 + ERA5-Land integration (Q4 2026):** Forecast lead time extends, spatial resolution improves, reserve sizing becomes dynamic. Product is commercially competitive for TIRA pilot approval and reinsurance placement at 1,000–5,000 farmer scale.

- **Full commercial (post-commercialisation):** Internal ensemble, causal teleconnection modelling, potential farm-level verification integration. Product is defensible at 50,000+ farmer scale across multiple Tanzania basins, with dynamic premium pricing and near-zero basis risk. Comparable in design maturity to ACRE Africa or KLIP Kenya at their current stage.

> **Core principle:** Every ML improvement in this roadmap reduces one of three things — **basis risk** (the gap between index and farm reality), **reserve mispricing** (capital allocated incorrectly due to uncalibrated probabilities), or **reinsurance friction** (the evidence gap preventing external capital from underwriting the product). These are the three constraints that determine whether HewaSense reaches scale.

---

### Planned Improvements

**Horizon-Specific Forecast Models** *(data-driven decision — evaluate post-shadow-run)*:

The current design uses a single model run with phase-aware threshold interpretation across all four horizons (3, 4, 5, 6 months). ENSO/IOD features provide genuine multi-month predictive skill — Indian Ocean Dipole events have documented 3–6 month lead time on East African long rains — which makes this approach defensible. A true multi-step model would predict intermediate climate states and feed them forward as inputs to longer-horizon forecasts, better capturing the autocorrelation structure of seasonal climate.

**Decision gate:** Compare Brier Scores by horizon tier once shadow run evaluations begin (~June 2026):
- If primary-tier (3–4mo) and advisory-tier (5–6mo) Brier Scores are comparable → the single-model design is working; ENSO/IOD features carry the longer-horizon signal. No action required.
- If advisory-tier Brier Scores are materially worse → implement horizon-specific models or recursive multi-step forecasting as a targeted improvement.

The advisory tier and widening confidence intervals already communicate this uncertainty in the current product design. This enhancement should be triggered by evidence, not by theoretical concern alone.

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

**Document Version**: 3.6
**Last Updated**: March 21, 2026
**Status**: ✅ Production Ready
**Consolidates**: MODEL_DEVELOPMENT_GUIDE.md, feature_engineering.md, UNCERTAINTY_QUANTIFICATION.md, MODEL_IMPROVEMENT_IMPLEMENTATION_GUIDE.md, MODEL_IMPROVEMENTS_RESULTS.md, TRAIN_PIPELINE_MIGRATION.md, RETRAINING_RESULTS_SUMMARY.md, SPATIAL_CV_RESULTS_TASK_15.md