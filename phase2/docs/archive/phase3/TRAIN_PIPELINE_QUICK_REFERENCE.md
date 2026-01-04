# Enhanced Training Pipeline - Quick Reference

**File**: `train_pipeline.py`  
**Status**: ✅ Production-Ready  
**Last Updated**: November 28, 2025

---

## Quick Start

```bash
# Recommended: Run with all improvements
python train_pipeline.py
```

---

## Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Path to master dataset | `data/processed/merged_data_2010_2025.csv` |
| `--output-dir` | Preprocessed features directory | `outputs/processed` |
| `--models-dir` | Trained models directory | `outputs/models` |
| `--skip-preprocessing` | Skip preprocessing step | `False` |
| `--skip-feature-selection` | Skip feature selection | `False` |
| `--skip-cv` | Skip cross-validation | `False` |
| `--target-features` | Number of features to select | `75` |
| `--debug` | Enable debug logging | `False` |

---

## Common Commands

```bash
# Full pipeline (recommended)
python train_pipeline.py

# Skip preprocessing (features already exist)
python train_pipeline.py --skip-preprocessing

# Custom feature count
python train_pipeline.py --target-features 100

# Fast mode (skip CV)
python train_pipeline.py --skip-cv

# Debug mode
python train_pipeline.py --debug
```

---

## Pipeline Steps

1. **Preprocessing** - Optimized feature engineering (lag, rolling, interactions)
2. **Data Loading** - Load train/val/test splits
3. **Feature Selection** - Hybrid selection (640 → 75 features)
4. **Baseline Training** - Persistence, mean, linear baselines
5. **Model Training** - RF, XGBoost, LSTM, Ensemble
6. **Validation** - Automated checks for overfitting, performance
7. **Results** - Save models, metrics, validation reports

---

## Output Files

### Feature Selection
- `outputs/models/feature_selection_results.json` - Selected features and distribution

### Models
- `outputs/models/random_forest_climate.pkl`
- `outputs/models/xgboost_climate.pkl`
- `outputs/models/lstm_climate.keras`
- `outputs/models/ensemble_climate_config.json`

### Validation
- `outputs/models/validation_random_forest.json`
- `outputs/models/validation_xgboost.json`
- `outputs/models/validation_lstm.json`
- `outputs/models/validation_ensemble.json`

### Results
- `outputs/models/training_results_YYYYMMDD_HHMMSS.json` - Complete results with baselines

---

## Key Improvements

| Feature | Benefit |
|---------|---------|
| Feature Selection | Reduces overfitting, improves generalization |
| Baseline Models | Validates model adds value |
| Enhanced Regularization | Prevents memorization |
| Automated Validation | Catches issues early |
| Honest Metrics | Scientifically defensible |

---

## Interpreting Output

### Console Output

```
STEP 3: FEATURE SELECTION
Reducing features from 640 to ~75
✓ Feature selection complete: 75 features selected
  Source distribution: {'chirps': 15, 'nasa_power': 15, ...}

STEP 4: BASELINE MODEL TRAINING
  - Persistence baseline (last value carried forward)
    R²: 0.3245
  - Mean baseline (historical average)
    R²: 0.2891
  - Linear regression baseline (Ridge with top 20 features)
    R²: 0.4567
  Best baseline: linear (R² = 0.4567)

STEP 6: AUTOMATED MODEL VALIDATION
ENSEMBLE Validation:
  Status: PASS
  Checks passed: 5
  Warnings: 0
  Failed: 0

Best Model Performance:
  Model: ensemble
  Test R²: 0.6234
  Improvement over baseline: +36.45%
```

### Validation Status

- **PASS** ✅ - All checks passed, model is production-ready
- **WARNING** ⚠️ - Some checks failed, review before deployment
- **FAIL** ❌ - Critical issues, do not deploy

---

## Validation Checks

| Check | Threshold | Purpose |
|-------|-----------|---------|
| Feature-to-sample ratio | > 1.5:1 | Sufficient data |
| Overfitting gap | < 0.15 | No memorization |
| Baseline improvement | Test R² > Baseline R² | Model adds value |
| Reasonable performance | Test R² > 0.3 | Useful predictions |
| Sufficient test data | > 20 samples | Reliable metrics |

---

## Troubleshooting

### Issue: Feature selection failed

**Solution**: Pipeline continues with all features
```bash
# Check logs for details
python train_pipeline.py --debug
```

### Issue: Model worse than baseline

**Solution**: Model not adding value, try:
- Collect more data
- Adjust feature selection: `--target-features 100`
- Review feature engineering

### Issue: Validation checks failed

**Solution**: Review validation report
```bash
cat outputs/models/validation_ensemble.json
```

### Issue: Out of memory

**Solution**: Reduce features or skip CV
```bash
python train_pipeline.py --target-features 50 --skip-cv
```

---

## Best Practices

### ✅ Do

- Run full pipeline with all improvements
- Review validation reports before deployment
- Compare against baselines
- Check feature selection results
- Use debug mode for troubleshooting

### ❌ Don't

- Use `train_pipeline_old_deprecated.py`
- Skip feature selection without good reason
- Deploy models that fail validation
- Ignore baseline comparison
- Trust unrealistic metrics (R² > 0.95)

---

## Performance Expectations

### Realistic Metrics

| Metric | Good | Excellent | Suspicious |
|--------|------|-----------|------------|
| Test R² | 0.5-0.7 | 0.7-0.85 | > 0.95 |
| Train-Test Gap | < 0.10 | < 0.05 | > 0.20 |
| vs Baseline | +10-30% | +30-50% | +100% |

### Runtime

| Configuration | Time | Use Case |
|---------------|------|----------|
| Full pipeline | ~5-10 min | Production training |
| Skip CV | ~3-5 min | Quick iteration |
| Skip preprocessing | ~2-3 min | Retraining only |

---

## Related Documentation

- **[MODEL_IMPROVEMENT_IMPLEMENTATION_GUIDE.md](MODEL_IMPROVEMENT_IMPLEMENTATION_GUIDE.md)** - Complete guide
- **[TRAIN_PIPELINE_MIGRATION.md](TRAIN_PIPELINE_MIGRATION.md)** - Migration notice
- **[MODEL_PERFORMANCE_CRITICAL_ANALYSIS.md](MODEL_PERFORMANCE_CRITICAL_ANALYSIS.md)** - Issue analysis

---

## Support

Questions? Check:
1. Validation reports: `outputs/models/validation_*.json`
2. Training logs: Console output
3. Implementation guide: `docs/MODEL_IMPROVEMENT_IMPLEMENTATION_GUIDE.md`

---

**Remember**: Lower, honest metrics are better than high, misleading ones. Trust the validation checks!
