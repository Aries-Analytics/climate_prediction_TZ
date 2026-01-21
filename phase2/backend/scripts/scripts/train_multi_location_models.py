"""
Multi-Location Model Training

Trains models on multi-location data (6 locations, 2000-2025) and compares
performance to single-location baseline.

Key Improvements Expected:
- Better feature-to-sample ratio (12.82:1 vs 1.72:1)
- Improved generalization capability
- Narrower prediction intervals
- Better spatial robustness

Models Trained:
1. Ridge Regression (linear baseline)
2. Random Forest
3. XGBoost
4. Ensemble (weighted average)

Target Variable: rainfall_mm (monthly rainfall in millimeters)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ML libraries
from sklearn.linear_model import Ridge
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

TARGET_VARIABLE = "rainfall_mm"

# Model hyperparameters (tuned for multi-location data)
RF_PARAMS = {
    'n_estimators': 200,
    'max_depth': 12,
    'min_samples_split': 8,
    'min_samples_leaf': 3,
    'max_features': 'sqrt',
    'random_state': 42,
    'n_jobs': -1
}

XGB_PARAMS = {
    'n_estimators': 200,
    'max_depth': 6,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'min_child_weight': 3,
    'gamma': 0.05,
    'reg_alpha': 0.05,
    'reg_lambda': 0.5,
    'random_state': 42,
    'n_jobs': -1
}

RIDGE_PARAMS = {
    'alpha': 1.0,  # L2 regularization strength
    'random_state': 42
}

# =============================================================================
# LOAD DATA
# =============================================================================

def load_splits():
    """Load pre-split multi-location data."""
    log_info("Loading multi-location data splits...")
    
    train = pd.read_parquet(get_data_path("processed", "features_train_multi_location.parquet"))
    val = pd.read_parquet(get_data_path("processed", "features_val_multi_location.parquet"))
    test = pd.read_parquet(get_data_path("processed", "features_test_multi_location.parquet"))
    
    log_info(f"Train: {len(train)} samples")
    log_info(f"Val:   {len(val)} samples")
    log_info(f"Test:  {len(test)} samples")
    
    return train, val, test


def prepare_features(train, val, test, target_col=TARGET_VARIABLE):
    """
    Prepare features and target for modeling.
    
    Same preprocessing as baseline for fair comparison.
    """
    log_info("Preparing features...")
    
    # Remove non-feature columns
    exclude_cols = [target_col, 'location', 'year', 'month', '_provenance_files']
    feature_cols = [col for col in train.columns if col not in exclude_cols]
    
    # Keep only numeric columns
    numeric_cols = train[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    
    log_info(f"Using {len(numeric_cols)} numeric features")
    
    # Separate X and y
    X_train = train[numeric_cols].copy()
    y_train = train[target_col].copy()
    
    X_val = val[numeric_cols].copy()
    y_val = val[target_col].copy()
    
    X_test = test[numeric_cols].copy()
    y_test = test[target_col].copy()
    
    # Handle missing values
    for col in numeric_cols:
        median_val = X_train[col].median()
        X_train[col].fillna(median_val, inplace=True)
        X_val[col].fillna(median_val, inplace=True)
        X_test[col].fillna(median_val, inplace=True)
    
    # Handle NaN in target
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
    
    # Convert back to DataFrame
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=numeric_cols)
    X_val_scaled = pd.DataFrame(X_val_scaled, columns=numeric_cols)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=numeric_cols)
    
    return (X_train_scaled, y_train, X_val_scaled, y_val, X_test_scaled, y_test, scaler)


# =============================================================================
# MODEL TRAINING
# =============================================================================

def train_random_forest(X_train, y_train, X_val, y_val):
    """Train Random Forest model."""
    log_info("Training Random Forest...")
    
    model = RandomForestRegressor(**RF_PARAMS)
    model.fit(X_train, y_train)
    
    # Predictions
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    # Metrics
    train_r2 = r2_score(y_train, train_pred)
    val_r2 = r2_score(y_val, val_pred)
    gap = abs(train_r2 - val_r2)
    gap_pct = gap / train_r2 * 100
    
    log_info(f"  Train R²: {train_r2:.4f}")
    log_info(f"  Val R²:   {val_r2:.4f}")
    log_info(f"  Gap:      {gap:.4f} ({gap_pct:.1f}%)")
    
    return model, {'train_r2': train_r2, 'val_r2': val_r2, 'gap': gap, 'gap_pct': gap_pct}


def train_ridge(X_train, y_train, X_val, y_val):
    """Train Ridge regression baseline model."""
    log_info("Training Ridge Regression (Linear Baseline)...")
    
    model = Ridge(**RIDGE_PARAMS)
    model.fit(X_train, y_train)
    
    # Predictions
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    # Metrics
    train_r2 = r2_score(y_train, train_pred)
    val_r2 = r2_score(y_val, val_pred)
    gap = abs(train_r2 - val_r2)
    gap_pct = gap / train_r2 * 100
    
    log_info(f"  Train R²: {train_r2:.4f}")
    log_info(f"  Val R²:   {val_r2:.4f}")
    log_info(f"  Gap:      {gap:.4f} ({gap_pct:.1f}%)")
   
    return model, {'train_r2': train_r2, 'val_r2': val_r2, 'gap': gap, 'gap_pct': gap_pct}


def train_xgboost(X_train, y_train, X_val, y_val):
    """Train XGBoost model."""
    log_info("Training XGBoost...")
    
    model = xgb.XGBRegressor(**XGB_PARAMS)
    model.fit(X_train, y_train)
    
    # Predictions
    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    
    # Metrics
    train_r2 = r2_score(y_train, train_pred)
    val_r2 = r2_score(y_val, val_pred)
    gap = abs(train_r2 - val_r2)
    gap_pct = gap / train_r2 * 100
    
    log_info(f"  Train R²: {train_r2:.4f}")
    log_info(f"  Val R²:   {val_r2:.4f}")
    log_info(f"  Gap:      {gap:.4f} ({gap_pct:.1f}%)")
    
    return model, {'train_r2': train_r2, 'val_r2': val_r2, 'gap': gap, 'gap_pct': gap_pct}


def create_ensemble(rf_model, xgb_model, X_val, y_val):
    """Create ensemble with optimized weights."""
    log_info("Creating Ensemble...")
    
    # Get validation predictions
    rf_pred = rf_model.predict(X_val)
    xgb_pred = xgb_model.predict(X_val)
    
    # Try different weight combinations
    best_r2 = -np.inf
    best_weights = [0.5, 0.5]
    
    for w1 in np.arange(0, 1.05, 0.05):
        w2 = 1 - w1
        ensemble_pred = w1 * rf_pred + w2 * xgb_pred
        r2 = r2_score(y_val, ensemble_pred)
        
        if r2 > best_r2:
            best_r2 = r2
            best_weights = [w1, w2]
    
    log_info(f"  Optimized weights: RF={best_weights[0]:.2f}, XGB={best_weights[1]:.2f}")
    log_info(f"  Ensemble Val R²: {best_r2:.4f}")
    
    return {'rf': rf_model, 'xgb': xgb_model, 'weights': best_weights}


# =============================================================================
# EVALUATION
# =============================================================================

def evaluate_model(model, X_test, y_test, model_name, is_ensemble=False):
    """Evaluate model on test set."""
    log_info(f"\nEvaluating {model_name}...")
    
    if is_ensemble:
        # Ensemble prediction
        rf_pred = model['rf'].predict(X_test)
        xgb_pred = model['xgb'].predict(X_test)
        y_pred = model['weights'][0] * rf_pred + model['weights'][1] * xgb_pred
    else:
        y_pred = model.predict(X_test)
    
    # Calculate metrics
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-10))) * 100  # Add small epsilon to avoid division by zero
    
    # Prediction interval width (95% PI)
    residuals = y_test - y_pred
    interval_width = 1.96 * np.std(residuals) * 2
    
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
# COMPARISON WITH BASELINE
# =============================================================================

def compare_to_baseline(ml_results, ml_metadata):
    """Load baseline results and create comparison."""
    log_info("\n" + "="*70)
    log_info("COMPARISON TO BASELINE")
    log_info("="*70)
    
    baseline_path = get_output_path("models", "baseline_performance_report.json")
    
    if not baseline_path.exists():
        log_warning("Baseline results not found, skipping comparison")
        return None
    
    with open(baseline_path, 'r') as f:
        baseline = json.load(f)
    
    comparison = {
        'baseline': {
            'location': baseline['metadata']['location'],
            'samples': baseline['metadata']['train_samples'],
            'features': baseline['metadata']['n_features'],
            'ratio': baseline['metadata']['feature_to_sample_ratio'],
            'best_r2': baseline['best_model'],
            'ensemble_metrics': baseline['models']['ensemble']
        },
        'multi_location': {
            'locations': 5,
            'samples': ml_metadata['train_samples'],
            'features': ml_metadata['n_features'],
            'ratio': ml_metadata['feature_to_sample_ratio'],
            'best_r2': ml_results['best_model'],
            'ensemble_metrics': ml_results['models']['ensemble']
        },
        'improvements': {}
    }
    
    # Calculate improvements
    base_r2 = baseline['models']['ensemble']['test_r2']
    ml_r2 = ml_results['models']['ensemble']['test_r2']
    
    base_rmse = baseline['models']['ensemble']['test_rmse']
    ml_rmse = ml_results['models']['ensemble']['test_rmse']
    
    base_pi = baseline['models']['ensemble']['prediction_interval_width']
    ml_pi = ml_results['models']['ensemble']['prediction_interval_width']
    
    comparison['improvements'] = {
        'sample_increase': f"{ml_metadata['train_samples'] / baseline['metadata']['train_samples']:.1f}x",
        'ratio_improvement': f"{ml_metadata['feature_to_sample_ratio'] / baseline['metadata']['feature_to_sample_ratio']:.1f}x",
        'r2_change': float(ml_r2 - base_r2),
        'rmse_reduction_pct': float((base_rmse - ml_rmse) / base_rmse * 100),
        'pi_width_reduction_pct': float((base_pi - ml_pi) / base_pi * 100)
    }
    
    log_info("\nBaseline (Single Location):")
    log_info(f"  Samples: {baseline['metadata']['train_samples']}, Ratio: {baseline['metadata']['feature_to_sample_ratio']:.2f}:1")
    log_info(f"  Ensemble R²: {base_r2:.4f}, RMSE: {base_rmse:.2f} mm, PI: {base_pi:.1f} mm")
    
    log_info("\nMulti-Location:")
    log_info(f"  Samples: {ml_metadata['train_samples']}, Ratio: {ml_metadata['feature_to_sample_ratio']:.2f}:1")
    log_info(f"  Ensemble R²: {ml_r2:.4f}, RMSE: {ml_rmse:.2f} mm, PI: {ml_pi:.1f} mm")
    
    log_info("\nImprovements:")
    log_info(f"  Sample increase: {comparison['improvements']['sample_increase']}")
    log_info(f"  Ratio improvement: {comparison['improvements']['ratio_improvement']}")
    log_info(f"  R² change: {comparison['improvements']['r2_change']:+.4f}")
    log_info(f"  RMSE reduction: {comparison['improvements']['rmse_reduction_pct']:.1f}%")
    log_info(f"  PI width reduction: {comparison['improvements']['pi_width_reduction_pct']:.1f}%")
    
    return comparison


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    log_info("="*70)
    log_info("MULTI-LOCATION MODEL TRAINING")
    log_info("="*70)
    
    # Load data
    train, val, test = load_splits()
    
    # Prepare features
    X_train, y_train, X_val, y_val, X_test, y_test, scaler = prepare_features(train, val, test)
    
    # Calculate metadata
    n_features = X_train.shape[1]
    n_samples = len(X_train)
    ratio = n_samples / n_features
    
    log_info("\n" + "="*70)
    log_info("MULTI-LOCATION DATASET STATISTICS")
    log_info("="*70)
    log_info(f"Locations: 5 (Arusha, Dar es Salaam, Dodoma, Mbeya, Mwanza)")
    log_info(f"Training samples: {n_samples}")
    log_info(f"Features: {n_features}")
    log_info(f"Feature-to-sample ratio: {ratio:.2f}:1")
    
    if ratio >= 10:
        log_info(f"✓ Ratio meets target (≥10:1)")
    else:
        log_warning(f"⚠ Ratio below target 10:1")
    
    # Train models
    log_info("\n" + "="*70)
    log_info("TRAINING MODELS")
    log_info("="*70)
    
    ridge_model, ridge_train_metrics = train_ridge(X_train, y_train, X_val, y_val)
    rf_model, rf_train_metrics = train_random_forest(X_train, y_train, X_val, y_val)
    xgb_model, xgb_train_metrics = train_xgboost(X_train, y_train, X_val, y_val)
    ensemble = create_ensemble(rf_model, xgb_model, X_val, y_val)
    
    # Evaluate on test set
    log_info("\n" + "="*70)
    log_info("TEST SET EVALUATION")
    log_info("="*70)
    
    ridge_metrics = evaluate_model(ridge_model, X_test, y_test, "Ridge")
    rf_metrics = evaluate_model(rf_model, X_test, y_test, "Random Forest")
    xgb_metrics = evaluate_model(xgb_model, X_test, y_test, "XGBoost")
    ensemble_metrics = evaluate_model(ensemble, X_test, y_test, "Ensemble", is_ensemble=True)
    
    # Add training metrics to results
    ridge_metrics['train_metrics'] = ridge_train_metrics
    rf_metrics['train_metrics'] = rf_train_metrics
    xgb_metrics['train_metrics'] = xgb_train_metrics
    
    # Compile results
    ml_results = {
        'metadata': {
            'locations': ['Arusha', 'Dar es Salaam', 'Dodoma', 'Mbeya', 'Mwanza', 'Morogoro'],
            'n_locations': 6,
            'total_samples': len(train) + len(val) + len(test),
            'train_samples': len(train),
            'val_samples': len(val),
            'test_samples': len(test),
            'n_features': n_features,
            'feature_to_sample_ratio': float(ratio),
            'target_variable': TARGET_VARIABLE,
            'timestamp': datetime.now().isoformat()
        },
        'models': {
            'ridge': ridge_metrics,
            'random_forest': rf_metrics,
            'xgboost': xgb_metrics,
            'ensemble': ensemble_metrics
        },
        'best_model': max(
            [ridge_metrics, rf_metrics, xgb_metrics, ensemble_metrics],
            key=lambda x: x['test_r2']
        )['model']
    }
    
    # Compare to baseline
    comparison = compare_to_baseline(ml_results, ml_results['metadata'])
    if comparison:
        ml_results['baseline_comparison'] = comparison
    
    # Save results
    results_path = get_output_path("models", "multi_location_performance_report.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(ml_results, f, indent=2)
    
    log_info("\n" + "="*70)
    log_info("MULTI-LOCATION TRAINING COMPLETE")
    log_info("="*70)
    log_info(f"Results saved: {results_path}")
    log_info(f"\nBest model: {ml_results['best_model']}")
    
    best_r2 = ml_results['models'][ml_results['best_model'].lower().replace(' ', '_')]['test_r2']
    log_info(f"Best test R²: {best_r2:.4f}")
    
    return ml_results


if __name__ == "__main__":
    results = main()
