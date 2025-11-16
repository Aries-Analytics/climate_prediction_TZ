# Model Development Pipeline Guide

## Overview

The `pipelines/model_development_pipeline.py` script orchestrates the complete machine learning model development workflow for climate prediction. It automates preprocessing, training, evaluation, and experiment tracking.

## Quick Start

### Basic Usage

Train all models with default settings:

```bash
python pipelines/model_development_pipeline.py
```

### Common Use Cases

#### 1. Train specific models only

```bash
# Train only Random Forest and XGBoost
python pipelines/model_development_pipeline.py --models rf,xgb

# Train only LSTM
python pipelines/model_development_pipeline.py --models lstm
```

#### 2. Skip preprocessing (use existing features)

```bash
python pipelines/model_development_pipeline.py --skip-preprocessing
```

#### 3. Specify custom input and output

```bash
python pipelines/model_development_pipeline.py \
    --input data/my_dataset.csv \
    --output-dir results/experiment_001
```

#### 4. Named experiment with specific target

```bash
python pipelines/model_development_pipeline.py \
    --experiment-name rainfall_prediction \
    --target rainfall_mm \
    --verbose
```

#### 5. Use custom configuration

```bash
python pipelines/model_development_pipeline.py \
    --config configs/custom_hyperparameters.json
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input PATH` | Path to master dataset CSV | `outputs/processed/master_dataset.csv` |
| `--output-dir PATH` | Base output directory | `outputs` |
| `--target COLUMN` | Target variable column name | Auto-detect |
| `--skip-preprocessing` | Skip preprocessing step | False |
| `--models LIST` | Models to train (rf,xgb,lstm,ensemble,all) | `all` |
| `--experiment-name NAME` | Experiment name | Auto-generated |
| `--config PATH` | Custom config JSON file | None |
| `--verbose` | Enable verbose logging | False |

## Pipeline Workflow

The pipeline executes the following steps:

### Step 1: Preprocessing and Feature Engineering

- Loads master dataset
- Creates lag features (1, 3, 6, 12 months)
- Creates rolling statistics (3, 6 month windows)
- Creates interaction features (ENSO × Rainfall, IOD × NDVI)
- Handles missing values (forward-fill with 2-month limit)
- Normalizes features (standardization)
- Splits data temporally (70% train, 15% val, 15% test)
- Saves preprocessed datasets to CSV and Parquet

**Outputs:**
- `outputs/processed/features_train.csv`
- `outputs/processed/features_val.csv`
- `outputs/processed/features_test.csv`
- `outputs/processed/scaler_params.json`
- `outputs/processed/feature_metadata.json`

### Step 2: Model Training

Trains selected models sequentially:

#### Random Forest
- 200 trees, max depth 15
- Calculates feature importance
- Cross-validation with 5 folds

#### XGBoost
- 200 estimators, learning rate 0.05
- Early stopping on validation set
- Feature importance using gain metric

#### LSTM
- 2 layers (128, 64 units)
- 12-month sequence length
- Early stopping with patience 10

#### Ensemble
- Weighted average of RF, XGB, LSTM
- Weights: 30% RF, 40% XGB, 30% LSTM

**Outputs:**
- `outputs/models/random_forest_climate.pkl`
- `outputs/models/xgboost_climate.pkl`
- `outputs/models/lstm_climate.keras`
- `outputs/models/ensemble_climate_config.json`
- `outputs/models/*_metadata.json`

### Step 3: Evaluation

For each model:
- Calculates metrics (R², RMSE, MAE, MAPE)
- Generates prediction intervals (95% confidence)
- Creates visualizations:
  - Predictions vs Actual scatter plot
  - Residuals over time
  - Feature importance (for tree models)
- Performs seasonal analysis (if month data available)
- Performs regional analysis (if region data available)

**Outputs:**
- `outputs/evaluation/{model}_evaluation_summary.json`
- `outputs/evaluation/{model}_predictions_vs_actual.png`
- `outputs/evaluation/{model}_residuals_over_time.png`
- `outputs/evaluation/{model}_feature_importance.png`
- `outputs/evaluation/{model}_predictions_with_uncertainty.csv`

### Step 4: Experiment Tracking

- Creates unique experiment ID
- Logs all hyperparameters and metrics
- Generates comparison report across experiments

**Outputs:**
- `outputs/experiments/experiment_log.jsonl`
- `outputs/experiments/comparison_report.md`
- `outputs/experiments/training_results_{name}.json`

## Custom Configuration

Create a JSON file to override default hyperparameters:

```json
{
  "random_forest": {
    "n_estimators": 300,
    "max_depth": 20
  },
  "xgboost": {
    "learning_rate": 0.01,
    "n_estimators": 500
  },
  "lstm": {
    "units": [256, 128, 64],
    "epochs": 150
  }
}
```

Use with:
```bash
python pipelines/model_development_pipeline.py --config my_config.json
```

## Output Directory Structure

```
outputs/
├── processed/
│   ├── features_train.csv
│   ├── features_val.csv
│   ├── features_test.csv
│   ├── features_train.parquet
│   ├── features_val.parquet
│   ├── features_test.parquet
│   ├── scaler_params.json
│   └── feature_metadata.json
├── models/
│   ├── random_forest_climate.pkl
│   ├── xgboost_climate.pkl
│   ├── lstm_climate.keras
│   ├── ensemble_climate_config.json
│   └── *_metadata.json
├── evaluation/
│   ├── *_evaluation_summary.json
│   ├── *_predictions_vs_actual.png
│   ├── *_residuals_over_time.png
│   ├── *_feature_importance.png
│   └── *_predictions_with_uncertainty.csv
└── experiments/
    ├── experiment_log.jsonl
    ├── comparison_report.md
    └── training_results_*.json
```

## Interpreting Results

### Model Performance Metrics

- **R² Score**: Coefficient of determination (0-1, higher is better)
  - Target: > 0.85 for production use
  - 0.85-0.95: Good performance
  - > 0.95: Excellent performance

- **RMSE**: Root Mean Squared Error (lower is better)
  - Measures average prediction error in original units
  - Compare across models to identify best performer

- **MAE**: Mean Absolute Error (lower is better)
  - Average absolute difference between predictions and actual
  - More interpretable than RMSE

- **MAPE**: Mean Absolute Percentage Error (lower is better)
  - Percentage error, useful for comparing across scales

### Prediction Intervals

- **95% Confidence Interval**: Range where true value is expected 95% of the time
- **Coverage**: Percentage of actual values within intervals
  - Target: 90-95% for 95% intervals
  - Lower coverage indicates underestimated uncertainty
  - Higher coverage indicates overestimated uncertainty

### Feature Importance

- Shows which features contribute most to predictions
- Use to:
  - Understand model behavior
  - Identify key climate drivers
  - Simplify model by removing low-importance features

## Troubleshooting

### Issue: "Master dataset not found"

**Solution**: Ensure the master dataset exists at the specified path or use `--input` to specify correct path.

### Issue: "R² score below threshold"

**Suggestions:**
1. Add more relevant features
2. Tune hyperparameters using custom config
3. Increase model complexity (more trees, deeper networks)
4. Check data quality and handle outliers
5. Try ensemble model for better performance

### Issue: "LSTM produces NaN predictions"

**Cause**: Insufficient sequence length or data issues

**Solution:**
1. Ensure at least 12 months of data per sequence
2. Check for missing values in input data
3. Reduce sequence length in config if needed

### Issue: "Out of memory during training"

**Solution:**
1. Reduce batch size for LSTM
2. Reduce number of trees for RF/XGB
3. Use fewer features (feature selection)
4. Train models individually instead of all at once

## Best Practices

1. **Always run with experiment names** for tracking:
   ```bash
   python pipelines/model_development_pipeline.py --experiment-name baseline_v1
   ```

2. **Start with a subset of models** to iterate quickly:
   ```bash
   python pipelines/model_development_pipeline.py --models rf,xgb
   ```

3. **Use verbose mode** for debugging:
   ```bash
   python pipelines/model_development_pipeline.py --verbose
   ```

4. **Compare experiments** using the comparison report:
   ```bash
   cat outputs/experiments/comparison_report.md
   ```

5. **Version your configurations** in git for reproducibility

6. **Monitor logs** in `logs/model_development.log`

## Integration with Existing Pipeline

The model development pipeline integrates with the existing data pipeline:

```bash
# Step 1: Run data ingestion and processing
python run_pipeline.py

# Step 2: Run model development
python pipelines/model_development_pipeline.py

# Step 3: Review results
cat outputs/experiments/comparison_report.md
```

## Next Steps

After running the pipeline:

1. **Review evaluation reports** in `outputs/evaluation/`
2. **Compare experiments** using `comparison_report.md`
3. **Select best model** based on R² and domain requirements
4. **Deploy model** for predictions (see deployment guide)
5. **Monitor performance** over time and retrain as needed

## Support

For issues or questions:
1. Check logs in `logs/model_development.log`
2. Review error messages and stack traces
3. Consult the design document in `.kiro/specs/ml-model-development/design.md`
4. Check requirements in `.kiro/specs/ml-model-development/requirements.md`
