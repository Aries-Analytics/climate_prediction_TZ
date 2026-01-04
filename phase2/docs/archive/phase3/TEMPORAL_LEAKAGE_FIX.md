# Temporal Leakage Fix - Summary

**Date**: November 30, 2025  
**Issue**: Suspiciously high R² scores (0.95+) suggesting temporal leakage

---

## Problem Identified

### Original Data Split (LEAKY)
- **Train**: 343 samples (1985-01 to 2013-12)
- **Val**: 74 samples (2013-01 to 2019-12) ⚠️ **OVERLAP with train year 2013**
- **Test**: 74 samples (2019-01 to 2025-12) ⚠️ **OVERLAP with val year 2019**
- **Total**: 491 samples

### Why This Caused Leakage
1. **Year Overlap**: Validation started in 2013 while training ended in 2013
2. **Lag Features**: With 6-month lags, validation data at 2013-01 uses training data from 2012-07
3. **Strong Autocorrelation**: Recent rainfall strongly predicts current rainfall
4. **Result**: Model "sees" the future through overlapping years

---

## Solution Implemented

### Fixed Data Split (NO LEAKAGE)
- **Train**: 343 samples (1985-01 to 2013-12)
- **Gap 1**: 12 months (2014-01 to 2014-12) ✓ **BUFFER ZONE**
- **Val**: 73 samples (2015-01 to 2020-12)
- **Gap 2**: 12 months (2021-01 to 2021-12) ✓ **BUFFER ZONE**
- **Test**: 51 samples (2022-01 to 2025-12)
- **Total**: 467 samples (24 samples lost to gaps)

### Changes Made

**File**: `preprocessing/preprocess.py`

1. **Added `gap_months` parameter** to `split_temporal_data()` function
2. **Implemented temporal gaps** between train/val and val/test
3. **Added year overlap detection** to verify no leakage
4. **Default gap**: 12 months (larger than max lag of 6 months)

```python
def split_temporal_data(
    df: pd.DataFrame, 
    train_pct: float = 0.7, 
    val_pct: float = 0.15, 
    gap_months: int = 12  # NEW PARAMETER
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
```

---

## Verification

### Year Overlap Check
```
Train years: 1985-2013
Val years: 2015-2020
Test years: 2022-2025

Train-Val overlap: [] ✓ NO OVERLAP
Val-Test overlap: [] ✓ NO OVERLAP
```

### Expected Impact on R²

**Before Fix** (with leakage):
- XGBoost: R² = 0.9840
- Random Forest: R² = 0.9460
- Ridge Baseline: R² = 0.9727 (suspiciously high!)

**After Fix** (expected):
- R² should drop to 0.70-0.85 range (more realistic for rainfall prediction)
- Baseline should drop to 0.40-0.60 range
- Gap between models and baseline should increase

---

## Why This Matters

### Literature Comparison
- **Typical rainfall prediction**: R² = 0.3-0.6
- **Good NDVI prediction**: R² = 0.6-0.8
- **Excellent multi-variable climate**: R² = 0.7-0.85

### Our Previous Results
- **R² = 0.95+**: Unrealistic, suggests leakage
- **Ridge baseline = 0.97**: Major red flag

### Expected After Fix
- **R² = 0.70-0.85**: Realistic for climate prediction
- **Ridge baseline = 0.40-0.60**: More appropriate
- **Honest assessment** of model performance

---

## Next Steps

1. ✅ **Fixed temporal splits** with 12-month gaps
2. ✅ **Removed year overlap** between splits
3. ⏳ **Retraining models** with fixed splits (in progress)
4. ⏳ **Compare results** before/after fix
5. ⏳ **Update documentation** with honest performance metrics

---

## Key Takeaway

**High R² scores don't always mean good models.**

When predicting time series data:
- Always use temporal gaps between splits
- Check for year/period overlap
- Compare against simple baselines
- Be suspicious of R² > 0.90 for climate prediction

The fix ensures we're testing the model's ability to predict truly unseen future data, not just interpolating between known values.

---

**Status**: ✅ Temporal leakage fixed, retraining in progress
