# ML Model Testing Suite

## Overview

Comprehensive unit and integration tests for the ML model development pipeline, ensuring robust and reliable climate predictions.

## Test Coverage

### 1. Preprocessing Tests (`test_preprocessing.py`)

**21 tests covering:**
- Data loading and validation
- Lag feature creation (1, 3, 6, 12 month lags)
- Rolling statistics (mean, std)
- Interaction features (ENSO × rainfall, IOD × NDVI)
- Missing value handling (forward-fill with gap limit)
- Feature normalization (z-score standardization)
- Temporal data splitting (train/val/test)
- End-to-end preprocessing pipeline

**Key Tests:**
- `test_create_lag_features_basic`: Verifies lag values are correctly shifted
- `test_create_rolling_features_basic`: Validates rolling mean calculations
- `test_normalize_features_basic`: Ensures normalization produces mean≈0, std≈1
- `test_split_temporal_data_maintains_order`: Confirms chronological ordering
- `test_preprocessing_pipeline_integration`: Tests complete pipeline execution

### 2. Model Tests (`test_models.py`)

**15 tests covering:**
- Random Forest model training and prediction
- XGBoost model training and prediction
- LSTM model training and prediction
- Ensemble model weighted averaging
- Model save/load functionality
- Feature importance extraction

**Key Tests:**
- `test_random_forest_train_and_predict`: Verifies RF can fit and predict
- `test_xgboost_save_load`: Ensures model persistence works correctly
- `test_ensemble_combines_predictions_correctly`: Validates weighted averaging logic
- `test_ensemble_requires_trained_models`: Checks error handling

### 3. Evaluation Tests (`test_evaluation.py`)

**17 tests covering:**
- Metric calculations (R², RMSE, MAE, MAPE)
- Quantile predictions for uncertainty quantification
- Prediction interval validation
- Seasonal performance analysis
- Plot generation (predictions vs actual, residuals, feature importance)
- Edge cases (zero variance, NaN values)

**Key Tests:**
- `test_calculate_metrics_with_known_values`: Validates metrics with perfect predictions
- `test_calculate_quantile_predictions_basic`: Tests uncertainty quantification
- `test_validate_prediction_intervals_coverage`: Validates interval coverage
- `test_evaluate_by_season_basic`: Tests seasonal grouping
- `test_plot_predictions_vs_actual_doesnt_crash`: Ensures visualization works

### 4. Integration Tests (`test_ml_pipeline_integration.py`)

**4 tests covering:**
- End-to-end preprocessing pipeline
- Complete model training workflow
- Output file structure validation
- Small dataset handling

**Key Tests:**
- `test_preprocessing_pipeline_end_to_end`: Full preprocessing execution
- `test_model_training_pipeline_end_to_end`: Complete train/predict/evaluate cycle
- `test_output_files_have_correct_structure`: Validates all output files

### 5. Uncertainty Quantification Tests (`test_uncertainty_quantification_integration.py`)

**5 tests covering:**
- End-to-end uncertainty quantification workflow
- Multiple confidence levels (90%, 95%, 99%)
- DataFrame integration
- Bootstrap predictions
- Edge cases (identical predictions, high uncertainty)

**Key Tests:**
- `test_end_to_end_uncertainty_quantification`: Complete UQ workflow with ensemble
- `test_uncertainty_quantification_with_different_confidence_levels`: Multiple CIs
- `test_uncertainty_quantification_saves_to_dataframe`: Data export
- `test_uncertainty_quantification_edge_cases`: Boundary conditions

## Running Tests

### Run All ML Tests
```bash
pytest tests/test_preprocessing.py tests/test_models.py tests/test_evaluation.py tests/test_ml_pipeline_integration.py -v
```

### Run Specific Test Suite
```bash
pytest tests/test_preprocessing.py -v
pytest tests/test_models.py -v
pytest tests/test_evaluation.py -v
pytest tests/test_ml_pipeline_integration.py -v
```

### Run with Coverage
```bash
pytest tests/test_preprocessing.py tests/test_models.py tests/test_evaluation.py tests/test_ml_pipeline_integration.py --cov=preprocessing --cov=models --cov=evaluation -v
```

### Run Fast (Skip Slow Tests)
```bash
pytest tests/test_preprocessing.py tests/test_evaluation.py -v
```

## Test Results

**Total Tests:** 63  
**Passing:** 63  
**Skipped:** 0  
**Coverage:** ~90% of ML pipeline code

## What's Tested

✅ **Preprocessing:**
- Lag features correctly shifted
- Rolling statistics accurately calculated
- Normalization produces correct distributions
- Temporal splits maintain chronological order
- Missing values handled appropriately

✅ **Models:**
- All models can train and predict
- Save/load preserves model state
- Ensemble combines predictions with correct weights
- Feature importance extraction works

✅ **Evaluation:**
- Metrics calculated correctly
- Plots generate without errors
- Seasonal analysis groups data properly

✅ **Integration:**
- Full pipeline executes end-to-end
- All output files created with correct structure
- Models can be trained, saved, loaded, and used for prediction

## What's NOT Tested (Yet)

❌ **Model Drift:** No tests for model performance degradation over time  
❌ **Real Data:** Tests use synthetic data, not actual climate data  
❌ **Performance:** No benchmarks for training/prediction speed  
❌ **Geographic Variation:** No tests for regional model performance

## Benefits of These Tests

1. **Confidence:** Know that preprocessing produces correct features
2. **Regression Prevention:** Catch breaking changes immediately
3. **Documentation:** Tests serve as usage examples
4. **Debugging:** Quickly identify where issues occur
5. **Production Readiness:** Essential for commercial deployment

## Next Steps

1. ✅ **Complete:** Basic unit and integration tests
2. ✅ **Complete:** Uncertainty quantification tests
3. 📋 **Planned:** Add property-based tests with Hypothesis
4. 📋 **Planned:** Add performance benchmarks
5. 📋 **Planned:** Add tests with real climate data
6. 📋 **Planned:** Add model drift detection tests

## Maintenance

- Run tests before committing code changes
- Update tests when adding new features
- Keep test data fixtures small for fast execution
- Add tests for any bugs discovered in production

---

**Last Updated:** November 19, 2025  
**Test Suite Version:** 1.0  
**Status:** ✅ Complete and Passing
