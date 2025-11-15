# 📊 Model Evaluation Reports - Quick Access Guide

**Location:** `outputs/evaluation/`  
**Latest Run:** November 15, 2025 at 9:02 AM

---

## 📁 Latest Evaluation Reports

### 1. 📈 Visualizations (PNG Images - 300 DPI)

#### Predictions vs Actual
**File:** `outputs/evaluation/predictions_vs_actual.png`
- Scatter plot showing predicted vs actual rainfall
- Includes R² score annotation
- Perfect prediction line for reference
- **Size:** 212 KB

#### Residuals Over Time
**File:** `outputs/evaluation/residuals_over_time.png`
- Time series of prediction errors
- Shows temporal patterns in errors
- Zero error reference line
- **Size:** 300 KB

#### Feature Importance
**File:** `outputs/evaluation/feature_importance.png`
- Top 20 most important features
- Bar chart with importance scores
- Color-coded for easy reading
- **Size:** 209 KB

### 2. 📊 Data Reports

#### Evaluation Summary (JSON)
**File:** `outputs/evaluation/evaluation_summary.json`
- Complete metrics for all models
- Baseline comparison
- Improvement percentages
- Seasonal performance breakdown
- **Size:** 2.47 KB

#### Seasonal Performance (CSV)
**File:** `outputs/evaluation/seasonal_performance.csv`
- Metrics by season (Short Rains, Long Rains, Dry Season)
- Sample counts per season
- R², RMSE, MAE, MAPE for each season
- **Size:** 0.33 KB

---

## 🔍 How to View

### Option 1: Open in File Explorer
```
1. Navigate to: outputs\evaluation\
2. Double-click any .png file to view
3. Open .json files in text editor or VS Code
4. Open .csv files in Excel or text editor
```

### Option 2: Command Line
```bash
# View images (Windows)
start outputs\evaluation\predictions_vs_actual.png
start outputs\evaluation\residuals_over_time.png
start outputs\evaluation\feature_importance.png

# View JSON summary
type outputs\evaluation\evaluation_summary.json

# View CSV in Excel
start outputs\evaluation\seasonal_performance.csv
```

### Option 3: Python
```python
import json
import pandas as pd
from PIL import Image

# View evaluation summary
with open('outputs/evaluation/evaluation_summary.json') as f:
    summary = json.load(f)
    print(json.dumps(summary, indent=2))

# View seasonal performance
df = pd.read_csv('outputs/evaluation/seasonal_performance.csv')
print(df)

# View images
img = Image.open('outputs/evaluation/predictions_vs_actual.png')
img.show()
```

---

## 📋 What's in Each Report

### Evaluation Summary JSON
```json
{
  "experiment_id": "rainfall_model_20251115_090244",
  "timestamp": "2025-11-15T09:02:44",
  "model_type": "RandomForest",
  "baseline": {
    "type": "seasonal_mean",
    "test_r2": 0.816,
    "test_rmse": 34.056
  },
  "metrics": {
    "train": { "r2_score": 0.995, "rmse": 4.557, "mae": 2.793 },
    "validation": { "r2_score": 0.974, "rmse": 12.836, "mae": 8.740 },
    "test": { "r2_score": 0.983, "rmse": 10.248, "mae": 7.312 }
  },
  "improvement_over_baseline": {
    "r2_improvement": 0.167,
    "rmse_improvement": 23.808,
    "r2_improvement_pct": 20.5,
    "rmse_improvement_pct": 69.9
  },
  "seasonal_performance": [...]
}
```

### Seasonal Performance CSV
```csv
target,season,n_samples,r2_score,rmse,mae,mape
rainfall,Short Rains,12,0.987,8.82,6.67,8.45
rainfall,Long Rains,11,0.982,11.35,8.35,10.23
rainfall,Dry Season,21,0.976,10.42,7.21,15.67
```

---

## 🎯 Key Metrics to Look At

### Overall Performance
- **Test R²:** 0.983 (98.3%) ✅ Excellent!
- **Test RMSE:** 10.25 mm
- **Test MAE:** 7.31 mm

### Improvement Over Baseline
- **R² Improvement:** +20.5%
- **RMSE Improvement:** -69.9% (error reduced by 70%!)

### Seasonal Performance
- **Short Rains:** 98.7% R² (12 samples)
- **Long Rains:** 98.2% R² (11 samples)
- **Dry Season:** 97.6% R² (21 samples)

---

## 📂 Full Directory Structure

```
outputs/
├── evaluation/
│   ├── predictions_vs_actual.png          ← Scatter plot
│   ├── residuals_over_time.png            ← Time series errors
│   ├── feature_importance.png             ← Top features
│   ├── evaluation_summary.json            ← Complete metrics
│   └── seasonal_performance.csv           ← By season
│
├── models/
│   ├── baseline_seasonal_mean_*.pkl       ← Baseline model
│   ├── random_forest_*.pkl                ← RF model
│   ├── xgboost_*.pkl                      ← XGBoost model
│   └── ensemble_*.pkl                     ← Ensemble model
│
└── experiments/
    └── experiment_log.jsonl               ← All experiments
```

---

## 🚀 Quick Commands

### View All Images at Once
```bash
start outputs\evaluation\predictions_vs_actual.png
start outputs\evaluation\residuals_over_time.png
start outputs\evaluation\feature_importance.png
```

### View Summary in Terminal
```bash
python -c "import json; print(json.dumps(json.load(open('outputs/evaluation/evaluation_summary.json')), indent=2))"
```

### View Seasonal Performance
```bash
python -c "import pandas as pd; print(pd.read_csv('outputs/evaluation/seasonal_performance.csv').to_string(index=False))"
```

---

## 📊 What the Visualizations Show

### Predictions vs Actual (Scatter Plot)
- **X-axis:** Actual rainfall values
- **Y-axis:** Predicted rainfall values
- **Red dashed line:** Perfect prediction (y=x)
- **Points:** Each test sample
- **Annotation:** R², RMSE, MAE metrics

**What to look for:**
- Points close to red line = good predictions
- Tight clustering = low error
- R² close to 1.0 = excellent fit

### Residuals Over Time (Time Series)
- **X-axis:** Date/time
- **Y-axis:** Prediction error (actual - predicted)
- **Red dashed line:** Zero error
- **Blue line:** Actual errors over time

**What to look for:**
- Errors centered around zero = unbiased
- No patterns = good model
- Consistent spread = stable performance

### Feature Importance (Bar Chart)
- **Y-axis:** Feature names (top 20)
- **X-axis:** Importance score
- **Colors:** Gradient for visual appeal

**What to look for:**
- Top features = most influential
- Helps understand what drives predictions
- Useful for feature selection

---

## 💡 Tips

1. **Compare Runs:** Look at timestamps to see latest results
2. **Check Seasonal:** Ensure good performance across all seasons
3. **Monitor Residuals:** Look for patterns that indicate issues
4. **Feature Insights:** Top features show what matters most

---

## 🔗 Related Files

- **Pipeline Code:** `model_development_pipeline.py`
- **Evaluation Code:** `evaluation/evaluate.py`
- **Status Reports:** 
  - `MODELS_STATUS_FINAL.md`
  - `FINAL_MODEL_PIPELINE_REPORT.md`
  - `MODEL_DEVELOPMENT_STATUS.md`

---

**All reports are ready to view! Just navigate to `outputs/evaluation/` and open the files.** 📊✨
