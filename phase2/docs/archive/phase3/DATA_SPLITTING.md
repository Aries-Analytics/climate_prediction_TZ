# Multi-Location Data Splitting Documentation

## Overview

This document describes the train/validation/test data splitting strategy implemented for the multi-location climate prediction model.

**Date**: 2025-12-29  
**Task**: Phase 5, Task 11 - Train/Val/Test Split Strategy

---

## Splitting Strategy

### Approach

**Time-Based Stratified Splitting** was implemented to ensure realistic forecasting validation while maintaining location balance.

### Split Ratios

- **Training**: 70% (First 70% of timeline per location)
- **Validation**: 15% (Next 15% of timeline per location)
- **Test**: 15% (Last 15% of timeline per location)

### Key Principles

1. **Temporal Ordering**: Chronological order maintained within each location
2. **No Temporal Leakage**: Test data is strictly after validation, validation after training
3. **Location Stratification**: Equal representation from each location in each split
4. **Realistic Forecasting**: Models tested on future data (2022-2025)

---

## Split Results

### Aggregate Statistics

| Split | Samples | Percentage | Time Period |
|-------|---------|------------|-------------|
| **Train** | 1,090 | 69.9% | 2000-2018 |
| **Validation** | 230 | 14.7% | 2018-2021 |
| **Test** | 240 | 15.4% | 2022-2025 |
| **Total** | 1,560 | 100% | 2000-2025 |

### Per-Location Distribution

All 5 locations have identical distribution:

| Location | Train | Validation | Test | Total |
|----------|-------|------------|------|-------|
| Arusha | 218 | 46 | 48 | 312 |
| Dar es Salaam | 218 | 46 | 48 | 312 |
| Dodoma | 218 | 46 | 48 | 312 |
| Mbeya | 218 | 46 | 48 | 312 |
| Mwanza | 218 | 46 | 48 | 312 |
| **Total** | **1,090** | **230** | **240** | **1,560** |

**Perfect Balance**: Each location contributes exactly 20% to each split (218/1090 ≈ 20%)

---

## Temporal Coverage

### Training Set (2000-2018)
- **Years**: 19 years
- **Months**: 228 months
- **Per Location**: 218 months each (18 years, 2 months)
- **Purpose**: Learn historical climate patterns

### Validation Set (2018-2021)
- **Years**: ~3 years (overlaps with 2018)
- **Months**: 46 months
- **Per Location**: 46 months each
- **Purpose**: Hyperparameter tuning and early stopping

### Test Set (2022-2025)
- **Years**: 4 years  
- **Months**: 48 months
- **Per Location**: 48 months each
- **Purpose**: Final model evaluation on recent data

---

## Feature-to-Sample Ratio

**Calculation**:
- Training samples: 1,090
- Features: 85
- **Ratio: 12.82:1** ✓

**Status**: Exceeds minimum target of 10:1 for statistical soundness

---

## Validation Checks

### ✓ No Data Overlap
- Verified no sample appears in multiple splits
- Used (year, month, location) tuples as unique identifiers
- Zero overlap detected between train/val, train/test, val/test

### ✓ Complete Coverage
- All 1,560 samples accounted for
- No samples missing or duplicated

### ✓ Location Balance
- Each location equally represented in all splits
- 20% from each location in each split

### ✓ Temporal Ordering
- All samples chronologically ordered within each location
- No time-series shuffling

### ✓ Feature Consistency
- All splits have identical 87 columns
- Same feature set across train/val/test

---

## Files Generated

### Data Files

All files saved to: `data/processed/`

1. **`features_train_multi_location.parquet`** (primary format)
   - 1,090 samples × 87 features
   - Compressed format for efficient loading

2. **`features_val_multi_location.parquet`**
   - 230 samples × 87 features

3. **`features_test_multi_location.parquet`**
   - 240 samples × 87 features

4. **`features_train_multi_location.csv`** (for inspection)
   - Same as parquet, human-readable format

5. **`features_val_multi_location.csv`**

6. **`features_test_multi_location.csv`**

### Metadata Files

7. **`split_statistics.json`**
   - Complete split statistics per location
   - Temporal periods for each split
   - Aggregate counts and ratios

---

## Implementation Details

### Script

**Location**: `scripts/split_multi_location_data.py`

### Algorithm

```python
for each location:
    1. Sort data chronologically (year, month)
    2. Calculate split indices:
       - train_end = 70% of location samples
       - val_end = train_end + 15% of location samples
    3. Split:
       - train = samples[0:train_end]
       - val = samples[train_end:val_end]
       - test = samples[val_end:]

Combine all locations for each split
```

### Key Code

```python
# Time-based splitting per location
loc_df = df[df['location'] == location].sort_values(['year', 'month'])
n_samples = len(loc_df)

train_end = int(n_samples * 0.70)
val_end = train_end + int(n_samples * 0.15)

train_loc = loc_df.iloc[:train_end]
val_loc = loc_df.iloc[train_end:val_end]
test_loc = loc_df.iloc[val_end:]
```

---

## Advantages of Time-Based Splitting

### 1. Realistic Evaluation ✓
- Tests model's ability to predict future climate
- Mimics operational forecasting scenario
- No "cheating" by training on future data

### 2. No Temporal Leakage ✓
- Test data strictly after validation
- Validation data strictly after training
- Preserves temporal causality

### 3. Climate Pattern Learning ✓
- Training set (2000-2018) captures diverse climate states
- Includes multiple ENSO cycles, IOD events
- Robust to inter-annual variability

### 4. Recent Data Testing ✓
- Test set (2022-2025) includes recent climate
- Validates performance on current conditions
- Relevant for near-term forecasting

---

## Limitations & Considerations

### Climate Variability
- Test set (2022-2025) may not capture full climate variability
- Specific climate states in test period may differ from training
- **Mitigation**: Cross-validation (k-fold, LOLO) provides additional validation

### Sample Size
- Test set has only 240 samples
- Smaller than ideal for robust statistical inference
- **Mitigation**: Use cross-validation for more stable estimates

### Temporal Autocorrelation
- Climate data has strong temporal autocorrelation
- Adjacent months are not independent
- **Mitigation**: Acknowledged in model evaluation and interpretation

---

## Next Steps

With splits created, ready to proceed to:

1. **Task 12**: Train baseline models on single-location data (Dodoma only)
2. **Task 13**: Train multi-location models (RF, XGBoost, LSTM, Ensemble)
3. **Task 14**: Evaluate performance and compare to baseline
4. **Task 15**: Spatial generalization validation (LOLO-CV)
5. **Task 16**: Uncertainty quantification

---

## References

### Related Files
- Feature engineering: `scripts/engineer_multi_location_features.py`
- Next step (baseline): `scripts/train_baseline_models.py` (to be created)

### Related Documentation
- Feature engineering: `docs/MULTI_LOCATION_FEATURE_ENGINEERING.md` (to be created)
- Model training: `docs/MULTI_LOCATION_MODEL_TRAINING.md` (to be created)
