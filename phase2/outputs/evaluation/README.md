# Model Evaluation Results

This folder contains evaluation results for the Tanzania Climate Prediction ML models.

## 📁 Folder Structure

```
outputs/evaluation/
├── latest/                    # Most recent evaluation results
│   ├── model_comparison.png   # Bar charts comparing all models
│   ├── evaluation_summary.json # Complete metrics summary
│   ├── *_predictions_vs_actual.png  # Per-model prediction plots
│   ├── *_residuals_over_time.png    # Per-model error plots
│   ├── *_feature_importance.png     # Feature importance (RF & XGB)
│   └── *_seasonal_performance.csv   # Performance by season
│
├── archive/                   # Historical evaluation runs
│   ├── 2025-11-17_HHMMSS/    # Timestamped folders
│   └── ...
│
└── README.md                  # This file
```

## 🎯 Quick Start

**View latest results:**
```powershell
# Open model comparison
start outputs/evaluation/latest/model_comparison.png

# View summary
cat outputs/evaluation/latest/evaluation_summary.json
```

## 📊 Key Files

### Model Comparison
- `model_comparison.png` - Side-by-side bar charts of R², RMSE, and MAE for all models

### Per-Model Visualizations
- `rf_predictions_vs_actual.png` - Random Forest predictions vs actual values
- `xgb_predictions_vs_actual.png` - XGBoost predictions vs actual values
- `lstm_predictions_vs_actual.png` - LSTM predictions vs actual values
- `ensemble_predictions_vs_actual.png` - Ensemble predictions vs actual values

### Error Analysis
- `*_residuals_over_time.png` - Time series of prediction errors for each model

### Feature Importance
- `random_forest_feature_importance.png` - Top 20 most important features (RF)
- `xgboost_feature_importance.png` - Top 20 most important features (XGBoost)

### Performance Metrics
- `evaluation_summary.json` - Complete metrics for all models
- `*_seasonal_performance.csv` - Performance breakdown by season (Short Rains, Long Rains, Dry Season)

## 🔄 Workflow

1. **Run Evaluation**: `python run_evaluation.py`
   - Results automatically saved to `latest/`
   - Previous `latest/` moved to `archive/` with timestamp

2. **Compare Runs**: Check `archive/` folders to compare different model versions

3. **Archive Management**: Old archives can be manually deleted to save space

## 📈 Current Best Model

Check `evaluation_summary.json` for the `best_model` field and `target_achieved` status.

**Target**: R² ≥ 0.85

## 🗂️ Archive Policy

- **Keep**: Last 5-10 evaluation runs for comparison
- **Delete**: Older runs after confirming no regression
- **Backup**: Important milestone evaluations (e.g., production models)

## 📝 Notes

- All plots are saved at 300 DPI for publication quality
- Seasonal performance may show `null` R² for seasons with < 2 samples
- MAPE can be high when actual values are close to zero
