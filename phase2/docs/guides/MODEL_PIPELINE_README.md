# ML Model Development Pipeline

## Overview

This comprehensive pipeline orchestrates the complete machine learning workflow for Tanzania Climate Prediction:

1. **Data Loading** - Loads and prepares the master dataset
2. **Model Training** - Trains Random Forest regression model
3. **Evaluation** - Generates comprehensive evaluation reports
4. **Experiment Tracking** - Logs experiments for comparison

## Usage

### Basic Usage

```bash
python model_development_pipeline.py
```

This will:
- Load data from `outputs/processed/master_dataset.csv`
- Train a Random Forest model
- Generate evaluation reports in `outputs/evaluation/`
- Save trained model to `outputs/models/`
- Log experiment to `outputs/experiments/`

## Pipeline Stages

### Stage 1: Data Loading
- Loads master dataset
- Creates date column from year/month
- Selects numeric features only
- Splits data chronologically (70% train, 15% val, 15% test)
- Handles missing values

### Stage 2: Model Training
- Trains Random Forest Regressor
- Calculates metrics (R², RMSE, MAE, MAPE)
- Checks R² threshold (0.85)
- Saves trained model with timestamp

### Stage 3: Evaluation
- **Seasonal Performance Analysis**: Metrics by season (Short Rains, Long Rains, Dry Season)
- **Predictions vs Actual Plot**: Scatter plot with R² annotation
- **Residuals Over Time**: Time series of prediction errors
- **Feature Importance**: Top 20 most important features

### Stage 4: Experiment Tracking
- Creates unique experiment ID
- Logs all metrics and configuration
- Saves evaluation summary as JSON

## Outputs

### Models Directory (`outputs/models/`)
- `random_forest_YYYYMMDD_HHMMSS.pkl` - Trained model

### Evaluation Directory (`outputs/evaluation/`)
- `seasonal_performance.csv` - Metrics by season
- `predictions_vs_actual.png` - Scatter plot
- `residuals_over_time.png` - Time series plot
- `feature_importance.png` - Feature importance chart
- `evaluation_summary.json` - Complete evaluation summary

### Experiments Directory (`outputs/experiments/`)
- `experiment_log.jsonl` - All experiment logs (one per line)

## Requirements

The pipeline uses the following evaluation functions from `evaluation/evaluate.py`:
- `calculate_metrics()` - Calculate R², RMSE, MAE, MAPE
- `evaluate_by_season()` - Seasonal performance analysis
- `plot_predictions_vs_actual()` - Scatter plot visualization
- `plot_residuals_over_time()` - Time series visualization
- `plot_feature_importance()` - Feature importance visualization

## Performance Thresholds

- **Target R²**: > 0.85
- **Warning**: If test R² < 0.85, suggests improvements

## Notes

- The pipeline automatically handles missing values by filling with mean
- Only numeric features are used for training
- Data is split chronologically to prevent data leakage
- All visualizations are saved at 300 DPI for publication quality

## Future Enhancements

- Add XGBoost and LSTM models
- Implement ensemble model
- Add hyperparameter tuning
- Add regional performance analysis
- Add uncertainty quantification
