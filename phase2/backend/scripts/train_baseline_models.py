"""
Baseline Model Training - Single Location

Trains models on single-location data (Dodoma, 2010-2025) to establish
performance baseline for comparison with multi-location approach.

Purpose:
- Demonstrate improvement from multi-location data augmentation
- Compare feature-to-sample ratios (2.5:1 vs 12.82:1)
- Show generalization improvements

Models Trained:
1. Random Forest
2. XGBoost
3. LSTM
4. Ensemble (weighted average)

Input: Multi-location data filtered to Dodoma only, 2010-2025
Output: Baseline model metrics and saved models
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timezone
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import xgboost as xgb

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import get_data_path, get_output_path
from utils.logger import log_info, log_warning

# =============================================================================
# CONFIGURATION
# =============================================================================

LOCATION = "Dodoma"  # Reference location for baseline
START_YEAR = 2010
END_YEAR = 2025
TARGET_VARIABLE = "rainfall_mm"

# Model hyperparameters (not heavily tuned for baseline)
RF_PARAMS = {
    'n_estimators': 100,
    'max_depth': 10,
    'min_samples_split': 5,
    'min_samples_leaf': 2,
    'random_state': 42,
    'n_jobs': -1
}

XGB_PARAMS = {
    'n_estimators': 100,
    'max_depth': 5,
    'learning_rate': 0.1,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42
}

# =============================================================================
# LOAD AND PREPARE DATA
# =============================================================================

def load_single_location_data():
    """
    Load single-location baseline data.
    
    Uses Dodoma data from 2010-2025 extracted from the multi-location dataset.
    This gives us ~191 months of data (16 years).
    """
    log_info(f"Loading baseline data: {LOCATION} ({START_YEAR}-{END_YEAR})")
    
    # Load full engineered features
    full_path = get_data_path("processed", "features_engineered_multi_location.csv")
    df = pd.read_csv(full_path)
    
    # Filter to Dodoma and time period
    mask = (
        (df['location'] == LOCATION) &
        (df['year'] >= START_YEAR) &
        (df['year'] <= END_YEAR)
    )
    baseline_df = df[mask].copy()
    
    # Sort chronologically
    baseline_df = baseline_df.sort_values(['year', 'month']).reset_index(drop=True)
    
    log_info(f"Loaded {len(baseline_df)} samples from {baseline_df['year'].min()}-{baseline_df['year'].max()}")
    
    return baseline_df


def create_baseline_splits(df):
    """
    Create time-based train/val/test splits for baseline.
    
    70/15/15 split maintaining temporal order.
    """
    log_info("Creating baseline splits (time-based 70/15/15)...")
    
    n = len(df)
    train_end = int(n * 0.70)
    val_end = train_end + int(n * 0.15)
    
    train = df.iloc[:train_end].copy()
    val = df.iloc[train_end:val_end].copy()
    test = df.iloc[val_end:].copy()
    
    log_info(f"Train: {len(train)} samples ({train['year'].min()}-{train['year'].max()})")
    log_info(f"Val:   {len(val)} samples ({val['year'].min()}-{val['year'].max()})")
    log_info(f"Test:  {len(test)} samples ({test['year'].min()}-{test['year'].max()})")
    
    return train, val, test


def prepare_features(train, val, test, target_col=TARGET_VARIABLE):
    """
    Prepare features and target for modeling.
    
    - Separate features from target
    - Remove non-numeric columns
    - Handle missing values
    - Scale features
    """
    log_info("Preparing features...")
    
    # Remove non-feature columns
    exclude_cols = [target_col, 'location', 'year', 'month', '_provenance_files']
    feature_cols = [col for col in train.columns if col not in exclude_cols]
    
    # Also exclude string/category columns
    numeric_cols = train[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    
    log_info(f"Using {len(numeric_cols)} numeric features")
    
    # Separate X and y
    X_train = train[numeric_cols].copy()
    y_train = train[target_col].copy()
    
    X_val = val[numeric_cols].copy()
    y_val = val[target_col].copy()
    
    X_test = test[numeric_cols].copy()
    y_test = test[target_col].copy()
    
    # Handle missing values (fill with median from training set)
    for col in numeric_cols:
        median_val = X_train[col].median()
        X_train[col].fillna(median_val, inplace=True)
        X_val[col].fillna(median_val, inplace=True)
        X_test[col].fillna(median_val, inplace=True)
    
    # Handle NaN in target variables
    target_median = y_train.median()
    y_train.fillna(target_median, inplace=True)
    y_val.fillna(target_median, inplace=True)
    y_test.fillna(target_median, inplace=True)
    
    log_info(f"Target variable ({target_col}) median: {target_median:.2f}")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Convert back to DataFrame for compatibility
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=numeric_cols)
    X_val_scaled = pd.DataFrame(X_val_scaled, columns=numeric_cols)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=numeric_cols)
    
    return (X_train_scaled, y_train, X_val_scaled, y_val, X_test_scaled, y_test, scaler)


# =============================================================================
# MODEL TRAINING
# =============================================================================

def train_random_forest(X_train, y_train, X_val, y_val):
    """Train Random Forest baseline model."""
    log_info("Training Random Forest...")
    
    model = RandomForestRegressor(**RF_PARAMS)
    model.fit(X_train, y_train)
    
    # Predictions
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    # Metrics
    train_r2 = r2_score(y_train, train_pred)
    val_r2 = r2_score(y_val, val_pred)
    
    log_info(f"  Train R²: {train_r2:.4f}")
    log_info(f"  Val R²:   {val_r2:.4f}")
    log_info(f"  Gap:      {abs(train_r2 - val_r2):.4f}")
    
    return model


def train_xgboost(X_train, y_train, X_val, y_val):
    """Train XGBoost baseline model."""
    log_info("Training XGBoost...")
    
    model = xgb.XGBRegressor(**XGB_PARAMS)
    model.fit(X_train, y_train)
    
    # Predictions
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    # Metrics
    train_r2 = r2_score(y_train, train_pred)
    val_r2 = r2_score(y_val, val_pred)
    
    log_info(f"  Train R²: {train_r2:.4f}")
    log_info(f"  Val R²:   {val_r2:.4f}")
    log_info(f"  Gap:      {abs(train_r2 - val_r2):.4f}")
    
    return model


def create_ensemble(rf_model, xgb_model, X_val, y_val):
    """Create simple ensemble (equal weights for baseline)."""
    log_info("Creating Ensemble...")
    
    # Get validation predictions
    rf_pred = rf_model.predict(X_val)
    xgb_pred = xgb_model.predict(X_val)
    
    # Simple average (equal weights for baseline)
    ensemble_pred = (rf_pred + xgb_pred) / 2
    
    val_r2 = r2_score(y_val, ensemble_pred)
    log_info(f"  Ensemble Val R²: {val_r2:.4f}")
    
    return {'rf': rf_model, 'xgb': xgb_model, 'weights': [0.5, 0.5]}


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_model(model, X_test, y_test, model_name, is_ensemble=False):
    """Evaluate a single model on test set."""
    log_info(f"\nEvaluating {model_name}...")
    
    if is_ensemble:
        # Ensemble prediction
        rf_pred = model['rf'].predict(X_test)
        xgb_pred = model['xgb'].predict(X_test)
        y_pred = (rf_pred + xgb_pred) / 2
    else:
        y_pred = model.predict(X_test)
    
    # Calculate metrics
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    
    # Prediction interval width (simple std-based for baseline)
    residuals = y_test - y_pred
    interval_width = 1.96 * np.std(residuals) * 2  # 95% PI width
    
    metrics = {
        'model': model_name,
        'test_r2': float(r2),
        'test_rmse': float(rmse),
        'test_mae': float(mae),
        'test_mape': float(mape),
        'prediction_interval_width': float(interval_width)
    }
    
    log_info(f"  R²:   {r2:.4f}")
    log_info(f"  RMSE: {rmse:.2f} mm")
    log_info(f"  MAE:  {mae:.2f} mm")
    log_info(f"  MAPE: {mape:.1f}%")
    log_info(f"  95% PI Width: {interval_width:.1f} mm")
    
    return metrics


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    log_info("="*70)
    log_info("BASELINE MODEL TRAINING (SINGLE LOCATION)")
    log_info("="*70)
    
    # Load data
    df = load_single_location_data()
    
    # Create splits
    train, val, test = create_baseline_splits(df)
    
    # Prepare features
    X_train, y_train, X_val, y_val, X_test, y_test, scaler = prepare_features(train, val, test)
    
    # Calculate feature-to-sample ratio
    n_features = X_train.shape[1]
    n_samples = len(X_train)
    ratio = n_samples / n_features
    
    log_info("\n" + "="*70)
    log_info("BASELINE DATASET STATISTICS")
    log_info("="*70)
    log_info(f"Location: {LOCATION}")
    log_info(f"Period: {START_YEAR}-{END_YEAR}")
    log_info(f"Training samples: {n_samples}")
    log_info(f"Features: {n_features}")
    log_info(f"Feature-to-sample ratio: {ratio:.2f}:1")
    
    if ratio < 10:
        log_warning(f"⚠ Ratio {ratio:.2f}:1 is below recommended 10:1 minimum")
    
    # Train models
    log_info("\n" + "="*70)
    log_info("TRAINING MODELS")
    log_info("="*70)
    
    rf_model = train_random_forest(X_train, y_train, X_val, y_val)
    xgb_model = train_xgboost(X_train, y_train, X_val, y_val)
    ensemble = create_ensemble(rf_model, xgb_model, X_val, y_val)
    
    # Evaluate on test set
    log_info("\n" + "="*70)
    log_info("TEST SET EVALUATION")
    log_info("="*70)
    
    rf_metrics = evaluate_model(rf_model, X_test, y_test, "Random Forest")
    xgb_metrics = evaluate_model(xgb_model, X_test, y_test, "XGBoost")
    ensemble_metrics = evaluate_model(ensemble, X_test, y_test, "Ensemble", is_ensemble=True)
    
    # Compile baseline report
    baseline_report = {
        'metadata': {
            'location': LOCATION,
            'period': f"{START_YEAR}-{END_YEAR}",
            'total_samples': len(df),
            'train_samples': len(train),
            'val_samples': len(val),
            'test_samples': len(test),
            'n_features': n_features,
            'feature_to_sample_ratio': float(ratio),
            'timestamp': datetime.now(timezone.utc).isoformat()
        },
        'models': {
            'random_forest': rf_metrics,
            'xgboost': xgb_metrics,
            'ensemble': ensemble_metrics
        },
        'best_model': max(
            [rf_metrics, xgb_metrics, ensemble_metrics],
            key=lambda x: x['test_r2']
        )['model']
    }
    
    # Save baseline report
    report_path = get_output_path("models", "baseline_performance_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(baseline_report, f, indent=2)
    
    log_info("\n" + "="*70)
    log_info("BASELINE TRAINING COMPLETE")
    log_info("="*70)
    log_info(f"Report saved: {report_path}")
    log_info(f"\nBest baseline model: {baseline_report['best_model']}")
    log_info(f"Best test R²: {baseline_report['best_model']}")
    
    return baseline_report


if __name__ == "__main__":
    report = main()
