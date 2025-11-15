"""
Model Development Pipeline - Tanzania Climate Prediction
Trains multiple models for drought/flood prediction and rainfall forecasting
"""

import sys
import io

# Ensure UTF-8 encoding for console output (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, TimeSeriesSplit, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, roc_curve,
    confusion_matrix, classification_report, mean_squared_error, mean_absolute_error, r2_score
)
import joblib

# Create output directories
MODEL_DIR = Path("outputs/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
VIZ_DIR = Path("outputs/visualizations/models")
VIZ_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("MODEL DEVELOPMENT PIPELINE - Tanzania Climate Prediction")
print("=" * 80)

# Load master dataset
print("\n[1/8] Loading master dataset...")
df = pd.read_csv("outputs/processed/master_dataset.csv")
print(f"✓ Loaded dataset with shape: {df.shape}")
print(f"  Columns: {list(df.columns)}")
print(f"  Date range: {df['date'].min()} to {df['date'].max()}")

# Prepare data
print("\n[2/8] Preparing data for modeling...")
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Define features and targets
feature_cols = [col for col in df.columns if col not in ['date', 'drought_risk', 'flood_risk', 'rainfall_next_month']]
print(f"✓ Using {len(feature_cols)} features")

# Split data chronologically (80% train, 20% test)
split_idx = int(len(df) * 0.8)
train_df = df.iloc[:split_idx].copy()
test_df = df.iloc[split_idx:].copy()
print(f"✓ Train set: {len(train_df)} samples | Test set: {len(test_df)} samples")

# ============================================================================
# MODEL 1: DROUGHT RISK CLASSIFICATION
# ============================================================================
print("\n[3/8] Training Drought Risk Classification Model...")

X_train_drought = train_df[feature_cols].fillna(0)
y_train_drought = train_df['drought_risk']
X_test_drought = test_df[feature_cols].fillna(0)
y_test_drought = test_df['drought_risk']

# Scale features
scaler_drought = StandardScaler()
X_train_drought_scaled = scaler_drought.fit_transform(X_train_drought)
X_test_drought_scaled = scaler_drought.transform(X_test_drought)

# Train Random Forest Classifier
rf_drought = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
rf_drought.fit(X_train_drought_scaled, y_train_drought)

# Predictions
y_pred_drought = rf_drought.predict(X_test_drought_scaled)
y_pred_proba_drought = rf_drought.predict_proba(X_test_drought_scaled)[:, 1]

# Evaluate
accuracy_drought = accuracy_score(y_test_drought, y_pred_drought)
precision_drought = precision_score(y_test_drought, y_pred_drought, zero_division=0)
recall_drought = recall_score(y_test_drought, y_pred_drought, zero_division=0)
f1_drought = f1_score(y_test_drought, y_pred_drought, zero_division=0)

print(f"✓ Drought Model Performance:")
print(f"  Accuracy:  {accuracy_drought:.3f}")
print(f"  Precision: {precision_drought:.3f}")
print(f"  Recall:    {recall_drought:.3f}")
print(f"  F1-Score:  {f1_drought:.3f}")

# Save model
joblib.dump(rf_drought, MODEL_DIR / "drought_classifier.pkl")
joblib.dump(scaler_drought, MODEL_DIR / "drought_scaler.pkl")
print(f"✓ Saved model to {MODEL_DIR / 'drought_classifier.pkl'}")

# ============================================================================
# MODEL 2: FLOOD RISK CLASSIFICATION
# ============================================================================
print("\n[4/8] Training Flood Risk Classification Model...")

X_train_flood = train_df[feature_cols].fillna(0)
y_train_flood = train_df['flood_risk']
X_test_flood = test_df[feature_cols].fillna(0)
y_test_flood = test_df['flood_risk']

# Scale features
scaler_flood = StandardScaler()
X_train_flood_scaled = scaler_flood.fit_transform(X_train_flood)
X_test_flood_scaled = scaler_flood.transform(X_test_flood)

# Train Random Forest Classifier
rf_flood = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
rf_flood.fit(X_train_flood_scaled, y_train_flood)

# Predictions
y_pred_flood = rf_flood.predict(X_test_flood_scaled)
y_pred_proba_flood = rf_flood.predict_proba(X_test_flood_scaled)[:, 1]

# Evaluate
accuracy_flood = accuracy_score(y_test_flood, y_pred_flood)
precision_flood = precision_score(y_test_flood, y_pred_flood, zero_division=0)
recall_flood = recall_score(y_test_flood, y_pred_flood, zero_division=0)
f1_flood = f1_score(y_test_flood, y_pred_flood, zero_division=0)

print(f"✓ Flood Model Performance:")
print(f"  Accuracy:  {accuracy_flood:.3f}")
print(f"  Precision: {precision_flood:.3f}")
print(f"  Recall:    {recall_flood:.3f}")
print(f"  F1-Score:  {f1_flood:.3f}")

# Save model
joblib.dump(rf_flood, MODEL_DIR / "flood_classifier.pkl")
joblib.dump(scaler_flood, MODEL_DIR / "flood_scaler.pkl")
print(f"✓ Saved model to {MODEL_DIR / 'flood_classifier.pkl'}")

# ============================================================================
# MODEL 3: RAINFALL FORECASTING (REGRESSION)
# ============================================================================
print("\n[5/8] Training Rainfall Forecasting Model...")

X_train_rainfall = train_df[feature_cols].fillna(0)
y_train_rainfall = train_df['rainfall_next_month']
X_test_rainfall = test_df[feature_cols].fillna(0)
y_test_rainfall = test_df['rainfall_next_month']

# Scale features
scaler_rainfall = StandardScaler()
X_train_rainfall_scaled = scaler_rainfall.fit_transform(X_train_rainfall)
X_test_rainfall_scaled = scaler_rainfall.transform(X_test_rainfall)

# Train Random Forest Regressor
rf_rainfall = RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    random_state=42,
    n_jobs=-1
)
rf_rainfall.fit(X_train_rainfall_scaled, y_train_rainfall)

# Predictions
y_pred_rainfall = rf_rainfall.predict(X_test_rainfall_scaled)

# Evaluate
rmse_rainfall = np.sqrt(mean_squared_error(y_test_rainfall, y_pred_rainfall))
mae_rainfall = mean_absolute_error(y_test_rainfall, y_pred_rainfall)
r2_rainfall = r2_score(y_test_rainfall, y_pred_rainfall)

print(f"✓ Rainfall Model Performance:")
print(f"  RMSE: {rmse_rainfall:.3f} mm")
print(f"  MAE:  {mae_rainfall:.3f} mm")
print(f"  R2:   {r2_rainfall:.3f}")

# Save model
joblib.dump(rf_rainfall, MODEL_DIR / "rainfall_regressor.pkl")
joblib.dump(scaler_rainfall, MODEL_DIR / "rainfall_scaler.pkl")
print(f"✓ Saved model to {MODEL_DIR / 'rainfall_regressor.pkl'}")

# ============================================================================
# FEATURE IMPORTANCE ANALYSIS
# ============================================================================
print("\n[6/8] Analyzing feature importance...")

# Get feature importance from drought model
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf_drought.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 10 Most Important Features:")
for idx, row in feature_importance.head(10).iterrows():
    print(f"  {row['feature']:<30} {row['importance']:.4f}")

# Save feature importance
feature_importance.to_csv(MODEL_DIR / "feature_importance.csv", index=False)

# ============================================================================
# VISUALIZATIONS
# ============================================================================
print("\n[7/8] Creating visualizations...")

# 1. Confusion Matrix for Drought
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

cm_drought = confusion_matrix(y_test_drought, y_pred_drought)
sns.heatmap(cm_drought, annot=True, fmt='d', cmap='Blues', ax=axes[0])
axes[0].set_title('Drought Risk - Confusion Matrix')
axes[0].set_xlabel('Predicted')
axes[0].set_ylabel('Actual')

# 2. Confusion Matrix for Flood
cm_flood = confusion_matrix(y_test_flood, y_pred_flood)
sns.heatmap(cm_flood, annot=True, fmt='d', cmap='Oranges', ax=axes[1])
axes[1].set_title('Flood Risk - Confusion Matrix')
axes[1].set_xlabel('Predicted')
axes[1].set_ylabel('Actual')

plt.tight_layout()
plt.savefig(VIZ_DIR / "confusion_matrices.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Saved confusion matrices to {VIZ_DIR / 'confusion_matrices.png'}")

# 3. Feature Importance Plot
plt.figure(figsize=(10, 8))
top_features = feature_importance.head(15)
plt.barh(range(len(top_features)), top_features['importance'])
plt.yticks(range(len(top_features)), top_features['feature'])
plt.xlabel('Importance')
plt.title('Top 15 Feature Importance (Drought Model)')
plt.tight_layout()
plt.savefig(VIZ_DIR / "feature_importance.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Saved feature importance to {VIZ_DIR / 'feature_importance.png'}")

# 4. Rainfall Prediction vs Actual
plt.figure(figsize=(12, 6))
plt.plot(y_test_rainfall.values[:100], label='Actual', marker='o', alpha=0.7)
plt.plot(y_pred_rainfall[:100], label='Predicted', marker='s', alpha=0.7)
plt.xlabel('Sample Index')
plt.ylabel('Rainfall (mm)')
plt.title('Rainfall Forecast: Actual vs Predicted (First 100 Test Samples)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(VIZ_DIR / "rainfall_predictions.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Saved rainfall predictions to {VIZ_DIR / 'rainfall_predictions.png'}")

# ============================================================================
# SUMMARY REPORT
# ============================================================================
print("\n[8/8] Generating summary report...")

summary = f"""
{'=' * 80}
MODEL DEVELOPMENT SUMMARY - Tanzania Climate Prediction
{'=' * 80}

DATASET INFORMATION:
- Total samples: {len(df):,}
- Training samples: {len(train_df):,}
- Testing samples: {len(test_df):,}
- Number of features: {len(feature_cols)}
- Date range: {df['date'].min()} to {df['date'].max()}

DROUGHT RISK CLASSIFICATION:
- Model: Random Forest Classifier
- Accuracy:  {accuracy_drought:.3f}
- Precision: {precision_drought:.3f}
- Recall:    {recall_drought:.3f}
- F1-Score:  {f1_drought:.3f}

FLOOD RISK CLASSIFICATION:
- Model: Random Forest Classifier
- Accuracy:  {accuracy_flood:.3f}
- Precision: {precision_flood:.3f}
- Recall:    {recall_flood:.3f}
- F1-Score:  {f1_flood:.3f}

RAINFALL FORECASTING:
- Model: Random Forest Regressor
- RMSE: {rmse_rainfall:.3f} mm
- MAE:  {mae_rainfall:.3f} mm
- R²:   {r2_rainfall:.3f}

TOP 5 MOST IMPORTANT FEATURES:
"""

for idx, row in feature_importance.head(5).iterrows():
    summary += f"  {idx+1}. {row['feature']:<30} ({row['importance']:.4f})\n"

summary += f"""
SAVED MODELS:
- {MODEL_DIR / 'drought_classifier.pkl'}
- {MODEL_DIR / 'flood_classifier.pkl'}
- {MODEL_DIR / 'rainfall_regressor.pkl'}

SAVED VISUALIZATIONS:
- {VIZ_DIR / 'confusion_matrices.png'}
- {VIZ_DIR / 'feature_importance.png'}
- {VIZ_DIR / 'rainfall_predictions.png'}

{'=' * 80}
"""

print(summary)

# Save summary to file
with open(MODEL_DIR / "model_summary.txt", "w", encoding='utf-8') as f:
    f.write(summary)

print(f"\n✓ Model development pipeline completed successfully!")
print(f"✓ All outputs saved to {MODEL_DIR} and {VIZ_DIR}")
print("=" * 80)
