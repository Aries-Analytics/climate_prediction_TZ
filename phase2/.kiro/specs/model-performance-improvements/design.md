# Design Document: Model Performance Improvements

## Overview

This design addresses three critical issues in the Tanzania Climate Prediction model:
1. **Small test set** (29 samples) → Implement time-series cross-validation for robust estimates
2. **High dimensionality** (640 features / 133 samples) → Reduce to 50-100 features via selection
3. **Overfitting** (train R² = 99.999%) → Apply stronger regularization and validation

The solution focuses on practical, implementable improvements that maintain model performance while increasing scientific rigor and defensibility.

## Architecture

### Component Structure

```
preprocessing/
├── feature_selection.py          # NEW: Feature selection methods
├── preprocess.py                 # MODIFIED: Optimized feature engineering
└── validation.py                 # NEW: Data quality checks

models/
├── train_models.py               # MODIFIED: Enhanced regularization
├── baseline_models.py            # NEW: Simple baseline implementations
└── ensemble.py                   # NEW: Improved ensemble methods

evaluation/
├── evaluate.py                   # MODIFIED: Expanded metrics
├── cross_validation.py           # NEW: Time-series CV
└── reporting.py                  # NEW: Comprehensive reporting

utils/
└── model_validation.py           # NEW: Automated validation pipeline
```

## Components and Interfaces

### 1. Feature Selection Module (`preprocessing/feature_selection.py`)

**Purpose**: Reduce feature space from 640 to 50-100 features using multiple selection methods.

**Key Functions**:

```python
def select_features_correlation(
    X: pd.DataFrame, 
    y: pd.Series, 
    threshold: float = 0.1,
    max_features: int = 100
) -> List[str]:
    """
    Select features based on correlation with target.
    
    Args:
        X: Feature matrix
        y: Target variable
        threshold: Minimum absolute correlation
        max_features: Maximum features to select
        
    Returns:
        List of selected feature names
    """
    pass

def select_features_importance(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    method: str = 'random_forest',
    n_features: int = 100
) -> List[str]:
    """
    Select features using model-based importance.
    
    Methods: 'random_forest', 'xgboost', 'lasso'
    """
    pass

def select_features_hybrid(
    X: pd.DataFrame,
    y: pd.Series,
    feature_names: List[str],
    target_features: int = 75
) -> Dict[str, Any]:
    """
    Combine multiple selection methods for robust feature set.
    
    Strategy:
    1. Remove features with correlation > 0.95 (redundancy)
    2. Select top 150 by correlation with target
    3. Select top 150 by Random Forest importance
    4. Select top 150 by XGBoost importance
    5. Take intersection or union based on target count
    6. Ensure representation from all 5 data sources
    
    Returns:
        Dict with selected features, scores, and metadata
    """
    pass

def ensure_source_diversity(
    selected_features: List[str],
    all_features: List[str],
    min_per_source: int = 5
) -> List[str]:
    """
    Ensure selected features include representation from all data sources.
    
    Sources: CHIRPS, NASA_POWER, ERA5, NDVI, Ocean_Indices
    """
    pass
```

**Implementation Strategy**:
- Use correlation threshold of 0.1 with target
- Use Random Forest with 100 trees for importance
- Use XGBoost with early stopping for importance
- Take features appearing in top 150 of at least 2 methods
- Manually ensure 5-10 features from each data source

### 2. Time-Series Cross-Validation (`evaluation/cross_validation.py`)

**Purpose**: Provide robust performance estimates accounting for temporal structure.

**Key Functions**:

```python
def time_series_cv_split(
    df: pd.DataFrame,
    n_splits: int = 5,
    test_size: int = 29,
    gap: int = 0
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Create time-series cross-validation splits.
    
    Strategy: Expanding window
    - Split 1: Train on months 1-100, test on 101-129
    - Split 2: Train on months 1-130, test on 131-159
    - Split 3: Train on months 1-160, test on 161-189
    - etc.
    
    Args:
        df: DataFrame sorted by time
        n_splits: Number of CV folds
        test_size: Size of each test set
        gap: Gap between train and test (for forecast horizon)
        
    Returns:
        List of (train_indices, test_indices) tuples
    """
    pass

def cross_validate_model(
    model_class,
    X: np.ndarray,
    y: np.ndarray,
    cv_splits: List[Tuple],
    **model_params
) -> Dict[str, Any]:
    """
    Perform cross-validation and return aggregated metrics.
    
    Returns:
        {
            'r2_mean': float,
            'r2_std': float,
            'r2_scores': List[float],
            'rmse_mean': float,
            'rmse_std': float,
            'mae_mean': float,
            'mae_std': float,
            'fold_results': List[Dict]
        }
    """
    pass

def calculate_confidence_intervals(
    scores: List[float],
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence intervals for CV scores.
    
    Uses t-distribution for small sample sizes.
    """
    pass
```

**Implementation Details**:
- Use 5-fold expanding window CV
- Each fold has ~29 test samples (matching current test set)
- Report mean ± std for all metrics
- Calculate 95% confidence intervals using t-distribution
- Visualize performance across folds

### 3. Enhanced Regularization (`models/train_models.py`)

**Purpose**: Reduce overfitting through stronger model constraints.

**XGBoost Regularization**:
```python
xgb_params = {
    'max_depth': 4,              # Reduced from default 6
    'min_child_weight': 5,       # Increased from default 1
    'gamma': 0.1,                # Minimum loss reduction
    'subsample': 0.8,            # Row sampling
    'colsample_bytree': 0.8,     # Column sampling
    'reg_alpha': 0.1,            # L1 regularization
    'reg_lambda': 1.0,           # L2 regularization
    'learning_rate': 0.01,       # Slower learning
    'n_estimators': 500,         # More trees with early stopping
    'early_stopping_rounds': 50
}
```

**Random Forest Regularization**:
```python
rf_params = {
    'n_estimators': 200,
    'max_depth': 10,             # Limit tree depth
    'min_samples_split': 10,     # Require more samples to split
    'min_samples_leaf': 5,       # Require more samples in leaves
    'max_features': 'sqrt',      # Feature sampling
    'bootstrap': True,
    'oob_score': True            # Out-of-bag validation
}
```

**LSTM Regularization**:
```python
model = Sequential([
    LSTM(64, return_sequences=True, 
         kernel_regularizer=l2(0.01),
         recurrent_regularizer=l2(0.01)),
    Dropout(0.3),
    LSTM(32, kernel_regularizer=l2(0.01)),
    Dropout(0.3),
    Dense(16, activation='relu', kernel_regularizer=l2(0.01)),
    Dropout(0.2),
    Dense(1)
])
```

**Validation Strategy**:
- Monitor train vs validation gap
- If gap > 5%, increase regularization
- Use early stopping based on validation loss
- Log all hyperparameters for reproducibility

### 4. Baseline Models (`models/baseline_models.py`)

**Purpose**: Provide simple benchmarks to demonstrate model value.

**Implementations**:

```python
class PersistenceBaseline:
    """Last value carried forward."""
    def predict(self, X, last_values):
        return last_values

class ClimatologyBaseline:
    """Historical monthly averages."""
    def fit(self, X, y, months):
        self.monthly_means = {}
        for month in range(1, 13):
            mask = months == month
            self.monthly_means[month] = y[mask].mean()
    
    def predict(self, X, months):
        return np.array([self.monthly_means[m] for m in months])

class LinearRegressionBaseline:
    """Simple linear model with top features."""
    def __init__(self, n_features=20):
        self.n_features = n_features
        self.model = Ridge(alpha=1.0)
    
    def fit(self, X, y, feature_names):
        # Select top features by correlation
        correlations = [abs(np.corrcoef(X[:, i], y)[0, 1]) 
                       for i in range(X.shape[1])]
        top_indices = np.argsort(correlations)[-self.n_features:]
        self.selected_features = top_indices
        self.model.fit(X[:, top_indices], y)
    
    def predict(self, X):
        return self.model.predict(X[:, self.selected_features])
```

**Evaluation**:
- Calculate R², RMSE, MAE for each baseline
- Report improvement: `(model_r2 - baseline_r2) / (1 - baseline_r2) * 100`
- Typical expectations:
  - Persistence: R² = 0.3-0.5
  - Climatology: R² = 0.4-0.6
  - Linear: R² = 0.6-0.75
  - Our models should exceed 0.80 to be valuable

### 5. Improved Ensemble (`models/ensemble.py`)

**Purpose**: Combine models using validation-based weighting.

```python
class WeightedEnsemble:
    """Ensemble using inverse RMSE weighting."""
    
    def __init__(self, models: List, names: List[str]):
        self.models = models
        self.names = names
        self.weights = None
    
    def fit_weights(self, X_val, y_val):
        """Calculate weights based on validation performance."""
        rmses = []
        for model in self.models:
            pred = model.predict(X_val)
            rmse = np.sqrt(mean_squared_error(y_val, pred))
            rmses.append(rmse)
        
        # Inverse RMSE weighting
        inv_rmses = 1.0 / np.array(rmses)
        self.weights = inv_rmses / inv_rmses.sum()
        
        logger.info("Ensemble weights:")
        for name, weight in zip(self.names, self.weights):
            logger.info(f"  {name}: {weight:.3f}")
    
    def predict(self, X):
        """Weighted average prediction."""
        predictions = np.array([model.predict(X) for model in self.models])
        return np.average(predictions, axis=0, weights=self.weights)
    
    def predict_with_intervals(self, X, confidence=0.95):
        """Prediction with uncertainty intervals."""
        predictions = np.array([model.predict(X) for model in self.models])
        
        # Weighted mean
        mean_pred = np.average(predictions, axis=0, weights=self.weights)
        
        # Uncertainty from model disagreement
        std_pred = np.std(predictions, axis=0)
        
        # Confidence intervals (assuming normal distribution)
        z_score = 1.96  # 95% confidence
        lower = mean_pred - z_score * std_pred
        upper = mean_pred + z_score * std_pred
        
        return mean_pred, lower, upper
```

## Data Models

### Feature Selection Output

```python
@dataclass
class FeatureSelectionResult:
    selected_features: List[str]
    feature_scores: Dict[str, float]
    selection_method: str
    original_count: int
    selected_count: int
    source_distribution: Dict[str, int]  # Features per data source
    correlation_matrix: np.ndarray
    timestamp: datetime
```

### Cross-Validation Result

```python
@dataclass
class CrossValidationResult:
    model_name: str
    n_splits: int
    r2_mean: float
    r2_std: float
    r2_ci_lower: float
    r2_ci_upper: float
    rmse_mean: float
    rmse_std: float
    mae_mean: float
    mae_std: float
    fold_results: List[Dict]
    best_fold: int
    worst_fold: int
```

### Model Validation Report

```python
@dataclass
class ValidationReport:
    timestamp: datetime
    feature_to_sample_ratio: float
    train_val_gap: float
    test_set_size: int
    overfitting_severity: str  # 'low', 'medium', 'high'
    baseline_comparison: Dict[str, float]
    checks_passed: List[str]
    checks_failed: List[str]
    recommendations: List[str]
    overall_status: str  # 'pass', 'warning', 'fail'
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Feature selection preserves source diversity
*For any* feature selection result, each of the five data sources (CHIRPS, NASA POWER, ERA5, NDVI, Ocean Indices) should have at least 5 selected features
**Validates: Requirements 1.3**

### Property 2: Feature selection reduces dimensionality
*For any* feature selection execution, the number of selected features should be between 50 and 100, and less than the original feature count
**Validates: Requirements 1.1**

### Property 3: Time-series CV maintains temporal order
*For any* cross-validation split, all training indices should be less than all test indices (no future data in training)
**Validates: Requirements 2.5**

### Property 4: Cross-validation provides multiple estimates
*For any* cross-validation execution with n_splits=5, exactly 5 R² scores should be calculated and aggregated
**Validates: Requirements 2.3**

### Property 5: Regularization reduces train-val gap
*For any* model trained with enhanced regularization, the absolute difference between training R² and validation R² should be less than 0.05
**Validates: Requirements 3.4**

### Property 6: Baseline models are simpler than complex models
*For any* baseline model, it should have fewer parameters than the corresponding complex model (RF, XGBoost, LSTM)
**Validates: Requirements 4.1, 4.2, 4.3**

### Property 7: Ensemble outperforms individual models
*For any* ensemble prediction on validation data, the ensemble R² should be greater than or equal to the maximum individual model R²
**Validates: Requirements 7.4**

### Property 8: Ensemble weights sum to one
*For any* weighted ensemble, the sum of model weights should equal 1.0 (within numerical precision)
**Validates: Requirements 7.2**

### Property 9: Prediction intervals have correct coverage
*For any* set of predictions with 95% confidence intervals, approximately 95% of actual values should fall within the intervals
**Validates: Requirements 5.1**

### Property 10: Validation pipeline flags critical issues
*For any* model with feature-to-sample ratio < 5:1, the validation pipeline should flag it as a critical issue
**Validates: Requirements 10.1**

### Property 11: Feature correlation removal reduces redundancy
*For any* pair of features in the selected set, their absolute correlation should be less than 0.95
**Validates: Requirements 6.4**

### Property 12: Confidence intervals widen with fewer samples
*For any* two cross-validation results with different sample sizes, the one with fewer samples should have wider confidence intervals
**Validates: Requirements 2.4**

## Error Handling

### Feature Selection Errors

```python
class InsufficientFeaturesError(Exception):
    """Raised when feature selection produces too few features."""
    pass

class SourceDiversityError(Exception):
    """Raised when selected features don't represent all data sources."""
    pass
```

**Handling Strategy**:
- If correlation method selects < 50 features, lower threshold
- If source diversity fails, manually add top features from underrepresented sources
- Log all adjustments for transparency

### Cross-Validation Errors

```python
class InsufficientDataError(Exception):
    """Raised when dataset is too small for requested CV splits."""
    pass
```

**Handling Strategy**:
- Require minimum 100 samples for 5-fold CV
- If insufficient, reduce to 3-fold or use holdout validation
- Warn user about limited statistical power

### Model Training Errors

```python
class OverfittingDetectedError(Exception):
    """Raised when train-val gap exceeds threshold."""
    pass
```

**Handling Strategy**:
- If gap > 10%, automatically increase regularization
- Retry training with stronger constraints
- If still fails, recommend feature reduction

## Testing Strategy

### Unit Tests

**Feature Selection Tests**:
- Test correlation-based selection with known correlations
- Test importance-based selection with synthetic data
- Test source diversity enforcement
- Test redundancy removal (correlation > 0.95)

**Cross-Validation Tests**:
- Test temporal ordering (no future leakage)
- Test split sizes match expectations
- Test confidence interval calculations
- Test with edge cases (small datasets)

**Baseline Model Tests**:
- Test persistence baseline returns last values
- Test climatology baseline returns monthly means
- Test linear baseline selects correct number of features

**Ensemble Tests**:
- Test weight calculation (sum to 1.0)
- Test weighted prediction matches manual calculation
- Test prediction intervals contain mean prediction

### Integration Tests

**End-to-End Pipeline Test**:
1. Load full dataset (191 samples)
2. Perform feature selection (640 → 75 features)
3. Run 5-fold time-series CV
4. Train models with regularization
5. Compare against baselines
6. Generate ensemble predictions
7. Validate all metrics and reports

**Expected Outcomes**:
- Feature selection completes in < 60 seconds
- CV produces 5 R² scores with std < 0.1
- Regularized models have train-val gap < 5%
- Ensemble outperforms best individual model
- All validation checks pass

### Property-Based Tests

Tests will be implemented using `hypothesis` library for Python.

**Test Generators**:
- Generate random feature matrices with known properties
- Generate time-series data with temporal structure
- Generate model predictions with controlled variance

## Performance Considerations

### Computational Complexity

**Feature Selection**:
- Correlation: O(n * m) where n=samples, m=features
- Random Forest importance: O(n * m * log(n) * trees)
- Total time: ~30-60 seconds for 191 samples, 640 features

**Cross-Validation**:
- 5-fold CV with 3 models: 15 training runs
- Each run: 1-5 minutes depending on model
- Total time: 15-75 minutes
- **Optimization**: Parallelize folds using joblib

**Feature Engineering**:
- Current: Creates 640 features (slow)
- Optimized: Creates ~200 features before selection (faster)
- Reduction in lag features: 12 → 6 lags saves 50% time

### Memory Optimization

**Current Memory Usage**:
- 191 samples × 640 features × 8 bytes = ~1 MB (manageable)

**After Feature Selection**:
- 191 samples × 75 features × 8 bytes = ~0.1 MB (negligible)

**No memory concerns** for this dataset size.

## Implementation Priority

### Phase 1: Quick Wins (1-2 days)
1. Implement feature selection (correlation + importance)
2. Apply enhanced regularization to existing models
3. Implement baseline models
4. Generate comparison report

**Expected Impact**: Reduce overfitting, establish baselines

### Phase 2: Robust Validation (2-3 days)
1. Implement time-series cross-validation
2. Calculate confidence intervals
3. Implement validation pipeline
4. Generate comprehensive reports

**Expected Impact**: More reliable performance estimates

### Phase 3: Advanced Features (2-3 days)
1. Implement weighted ensemble
2. Add prediction intervals
3. Optimize feature engineering
4. Create visualization dashboard

**Expected Impact**: Better predictions, uncertainty quantification

## Validation Metrics

### Success Criteria

**Feature Selection**:
- ✓ Features reduced to 50-100
- ✓ All 5 data sources represented
- ✓ Validation R² within 5% of original

**Regularization**:
- ✓ Train-val gap < 5% for all models
- ✓ Training R² < 99% (no memorization)
- ✓ Validation R² maintained or improved

**Cross-Validation**:
- ✓ 5 folds completed successfully
- ✓ R² std < 0.1 (consistent performance)
- ✓ Confidence intervals calculated

**Baselines**:
- ✓ All 3 baselines implemented
- ✓ Complex models outperform by > 10%
- ✓ Improvement percentages calculated

**Ensemble**:
- ✓ Ensemble R² ≥ max(individual R²)
- ✓ Prediction intervals have 90-98% coverage
- ✓ Weights sum to 1.0

## Documentation Requirements

### Technical Documentation

1. **Feature Selection Report**:
   - Selected features with scores
   - Source distribution
   - Correlation matrix heatmap
   - Comparison of selection methods

2. **Cross-Validation Report**:
   - Metrics for each fold
   - Mean ± std for all metrics
   - Confidence intervals
   - Performance over time plot

3. **Model Comparison Report**:
   - Baseline vs complex models table
   - Improvement percentages
   - Train-val gaps
   - Regularization parameters

4. **Validation Pipeline Report**:
   - All checks with pass/fail status
   - Severity flags
   - Actionable recommendations
   - Overall assessment

### Academic Reporting Language

Provide templates for:
- Methods section (feature selection, CV, regularization)
- Results section (metrics with confidence intervals)
- Limitations section (sample size, overfitting risks)
- Future work section (data expansion strategies)

## Future Enhancements

### Data Expansion Strategies

**Spatial Expansion**:
- Train on multiple locations in Tanzania
- Target: 5-10 locations × 191 months = 955-1910 samples
- Improves generalization across geography

**Temporal Expansion**:
- Continue data collection (target: 20+ years)
- Target: 240+ months
- Captures longer climate cycles

**Sub-Seasonal Aggregation**:
- Use dekadal (10-day) instead of monthly
- 191 months → 573 dekads
- Increases samples 3x but may add noise

### Advanced Techniques

**Hierarchical Models**:
- Separate models for each season
- Reduces complexity per model
- May improve seasonal performance

**Transfer Learning**:
- Pre-train on global climate data
- Fine-tune on Tanzania data
- Leverages larger datasets

**Bayesian Approaches**:
- Bayesian Neural Networks for uncertainty
- Gaussian Processes for small data
- Natural uncertainty quantification

## References

### ML Best Practices

- Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The Elements of Statistical Learning*
- Bergmeir, C., & Benítez, J. M. (2012). "On the use of cross-validation for time series predictor evaluation"
- Guyon, I., & Elisseeff, A. (2003). "An introduction to variable and feature selection"

### Climate Prediction

- Funk, C., et al. (2015). "The climate hazards infrared precipitation with stations—a new environmental record for monitoring extremes"
- Nicholson, S. E. (2017). "Climate and climatic variability of rainfall over eastern Africa"

### Regularization

- Friedman, J. H. (2001). "Greedy function approximation: a gradient boosting machine"
- Breiman, L. (2001). "Random forests"
- Srivastava, N., et al. (2014). "Dropout: a simple way to prevent neural networks from overfitting"
