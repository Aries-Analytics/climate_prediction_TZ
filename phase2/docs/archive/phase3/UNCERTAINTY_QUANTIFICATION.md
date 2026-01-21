# Uncertainty Quantification for Climate Predictions

> **Scope**: This document describes uncertainty quantification for **climate variable predictions** (rainfall mm, NDVI values, soil moisture %). These predictions are then compared to fixed thresholds to determine insurance triggers. This is NOT about predicting trigger probabilities directly. See [PARAMETRIC_INSURANCE_FINAL.md](../references/PARAMETRIC_INSURANCE_FINAL.md#trigger-detection-methodology) for the complete trigger detection process.

## Overview

Uncertainty quantification provides prediction intervals (confidence bounds) around climate predictions, allowing users to understand the reliability and range of possible outcomes.

## Why It Matters

**Without Uncertainty:**
```
Prediction: "Rainfall will be 125mm next month"
Problem: How confident are we? What's the range?
```

**With Uncertainty:**
```
Prediction: "Rainfall will be 125mm (95% CI: 100-150mm)"
Benefit: Users know the prediction range and can plan accordingly
```

## Implementation

### Functions

#### 1. `calculate_quantile_predictions()`

Calculates quantile predictions from multiple model predictions or bootstrap samples.

**Usage:**
```python
from evaluation.evaluate import calculate_quantile_predictions

# Get predictions from multiple models
rf_pred = rf_model.predict(X_test)
xgb_pred = xgb_model.predict(X_test)
lstm_pred = lstm_model.predict(X_test)

# Calculate 95% prediction intervals
quantiles = calculate_quantile_predictions(
    [rf_pred, xgb_pred, lstm_pred],
    quantiles=[0.025, 0.5, 0.975]  # 2.5%, 50%, 97.5%
)

# Access results
lower_bound = quantiles['q2.5']   # Lower 95% bound
median = quantiles['q50']          # Median prediction
upper_bound = quantiles['q97.5']   # Upper 95% bound
```

**Parameters:**
- `predictions_list`: List of prediction arrays from different models/samples
- `quantiles`: List of quantiles to calculate (default: [0.025, 0.5, 0.975])

**Returns:**
- Dictionary mapping quantile names to prediction arrays

#### 2. `validate_prediction_intervals()`

Validates that prediction intervals have correct coverage.

**Usage:**
```python
from evaluation.evaluate import validate_prediction_intervals

# Validate 95% interval coverage
validation = validate_prediction_intervals(
    y_true=actual_values,
    lower_bound=quantiles['q2.5'],
    upper_bound=quantiles['q97.5'],
    confidence_level=0.95
)

print(f"Coverage: {validation['coverage']:.2%}")
print(f"Expected: {validation['expected_coverage']:.2%}")
print(f"Error: {validation['coverage_error']:+.2%}")
```

**Parameters:**
- `y_true`: Actual values
- `lower_bound`: Lower bound of prediction interval
- `upper_bound`: Upper bound of prediction interval
- `confidence_level`: Expected confidence level (default: 0.95)

**Returns:**
- Dictionary with validation metrics:
  - `coverage`: Actual proportion of values within interval
  - `expected_coverage`: Expected confidence level
  - `coverage_error`: Difference between actual and expected
  - `n_samples`: Number of samples
  - `n_within_interval`: Number of samples within interval
  - `interval_width_mean`: Average interval width
  - `interval_width_std`: Standard deviation of interval widths

## Use Cases

### 1. Ensemble Model Predictions

Combine predictions from multiple models to create uncertainty estimates:

```python
# Train multiple models
rf_model = RandomForestModel()
xgb_model = XGBoostModel()
lstm_model = LSTMModel()

# Get predictions
predictions = [
    rf_model.predict(X_test),
    xgb_model.predict(X_test),
    lstm_model.predict(X_test)
]

# Calculate uncertainty
quantiles = calculate_quantile_predictions(predictions)
```

### 2. Bootstrap Predictions

Use bootstrap resampling from a single model:

```python
# Create bootstrap predictions
bootstrap_predictions = []
for i in range(100):
    # Resample training data
    X_boot, y_boot = resample(X_train, y_train)
    
    # Train model on bootstrap sample
    model = RandomForestModel()
    model.train(X_boot, y_boot)
    
    # Get predictions
    bootstrap_predictions.append(model.predict(X_test))

# Calculate uncertainty
quantiles = calculate_quantile_predictions(bootstrap_predictions)
```

### 3. Insurance Risk Management

Use prediction intervals for financial planning:

```python
# Predict trigger probabilities with uncertainty
quantiles = calculate_quantile_predictions(predictions)

# Calculate risk scenarios
worst_case = quantiles['q97.5']  # 97.5th percentile
expected = quantiles['q50']       # Median
best_case = quantiles['q2.5']     # 2.5th percentile

# Plan reserves based on worst case
reserves_needed = calculate_reserves(worst_case)
```

### 4. Dashboard Visualization

Display prediction intervals in charts:

```python
import matplotlib.pyplot as plt

# Calculate quantiles
quantiles = calculate_quantile_predictions(predictions)

# Plot with uncertainty bands
plt.figure(figsize=(12, 6))
plt.plot(dates, quantiles['q50'], label='Prediction', color='blue')
plt.fill_between(
    dates,
    quantiles['q2.5'],
    quantiles['q97.5'],
    alpha=0.3,
    label='95% Confidence Interval',
    color='blue'
)
plt.plot(dates, y_true, label='Actual', color='red', linestyle='--')
plt.legend()
plt.title('Rainfall Predictions with Uncertainty')
plt.show()
```

## Confidence Levels

Common confidence levels and their quantiles:

| Confidence Level | Lower Quantile | Upper Quantile | Use Case |
|-----------------|----------------|----------------|----------|
| 90% | 0.05 | 0.95 | General predictions |
| 95% | 0.025 | 0.975 | Standard scientific reporting |
| 99% | 0.005 | 0.995 | High-stakes decisions |

## Interpretation

### Interval Width

**Narrow intervals** (e.g., 100-110mm):
- High confidence in prediction
- Models agree closely
- Low uncertainty

**Wide intervals** (e.g., 50-200mm):
- Low confidence in prediction
- Models disagree
- High uncertainty

### Coverage Validation

**Good coverage** (actual ≈ expected):
- 95% interval contains ~95% of actual values
- Intervals are well-calibrated
- Reliable uncertainty estimates

**Poor coverage** (actual << expected):
- Intervals too narrow
- Overconfident predictions
- Need to recalibrate

**Excessive coverage** (actual >> expected):
- Intervals too wide
- Underconfident predictions
- Can be tightened

## Best Practices

### 1. Use Multiple Models

Combine diverse models for better uncertainty estimates:
- Random Forest (tree-based)
- XGBoost (boosting)
- LSTM (neural network)

### 2. Validate Coverage

Always check that intervals have correct coverage:

```python
validation = validate_prediction_intervals(y_true, lower, upper, 0.95)
if abs(validation['coverage_error']) > 0.05:
    print("Warning: Intervals may need recalibration")
```

### 3. Choose Appropriate Confidence Level

- **90%**: General forecasting
- **95%**: Standard for scientific work
- **99%**: Critical decisions (insurance reserves)

### 4. Monitor Interval Width

Track average interval width over time:

```python
width = quantiles['q97.5'] - quantiles['q2.5']
avg_width = np.mean(width)

if avg_width > threshold:
    print("Warning: High uncertainty in predictions")
```

## Example: Complete Workflow

```python
from evaluation.evaluate import (
    calculate_quantile_predictions,
    validate_prediction_intervals
)

# 1. Train ensemble models
rf_model = RandomForestModel()
xgb_model = XGBoostModel()
lstm_model = LSTMModel()

rf_model.train(X_train, y_train)
xgb_model.train(X_train, y_train)
lstm_model.train(X_train, y_train)

# 2. Get predictions
predictions = [
    rf_model.predict(X_test),
    xgb_model.predict(X_test),
    lstm_model.predict(X_test)
]

# 3. Calculate 95% prediction intervals
quantiles = calculate_quantile_predictions(
    predictions,
    quantiles=[0.025, 0.5, 0.975]
)

# 4. Validate coverage
validation = validate_prediction_intervals(
    y_test,
    quantiles['q2.5'],
    quantiles['q97.5'],
    confidence_level=0.95
)

print(f"Coverage: {validation['coverage']:.2%}")
print(f"Average interval width: {validation['interval_width_mean']:.2f}")

# 5. Save results with uncertainty
results_df = pd.DataFrame({
    'date': test_dates,
    'prediction': quantiles['q50'],
    'lower_95': quantiles['q2.5'],
    'upper_95': quantiles['q97.5'],
    'actual': y_test
})

results_df.to_csv('predictions_with_uncertainty.csv', index=False)
```

## Testing

Comprehensive tests ensure uncertainty quantification works correctly:

**Unit Tests** (`test_evaluation.py`):
- Quantile calculation correctness
- Input validation
- Interval ordering
- Coverage validation

**Integration Tests** (`test_uncertainty_quantification_integration.py`):
- End-to-end workflow
- Multiple confidence levels
- DataFrame integration
- Edge cases

Run tests:
```bash
pytest tests/test_evaluation.py -k "quantile or interval" -v
pytest tests/test_uncertainty_quantification_integration.py -v
```

## References

- Design Document: `.kiro/specs/ml-model-development/design.md` (Requirements 3.1-3.5)
- Implementation: `evaluation/evaluate.py`
- Tests: `tests/test_evaluation.py`, `tests/test_uncertainty_quantification_integration.py`

---

**Last Updated:** November 19, 2025  
**Version:** 1.0  
**Status:** ✅ Implemented and Tested
