"""
Comprehensive Model Development Pipeline - Tanzania Climate Prediction

This script trains ALL models end-to-end:
1. Random Forest
2. XGBoost  
3. LSTM
4. Ensemble (combining all three)

Uses the full 288-row master dataset (2000-2023)

Requirements: All requirements (1.1-7.5)
"""

import sys
import io
import warnings
warnings.filterwarnings('ignore')

# Ensure UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import time

from utils.logger import get_logger
from evaluation.evaluate import (
    calculate_metrics,
    evaluate_by_season,
    plot_predictions_vs_actual,
    plot_residuals_over_time,
    plot_feature_importance
)

logger = get_logger()

def create_experiment_id(prefix: str = "exp") -> str:
    """Generate unique experiment ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


def log_experiment(experiment_id: str, results: dict, output_dir: Path) -> None:
    """Log experiment results to JSON file."""
    experiments_dir = output_dir / "experiments"
    experiments_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = experiments_dir / "experiment_log.jsonl"
    
    with open(log_file, 'a') as f:
        json.dump({
            'experiment_id': experiment_id,
            'timestamp': datetime.now().isoformat(),
            **results
        }, f)
        f.write('\n')
    
    logger.info(f"✓ Logged experiment to {log_file}")


def train_random_forest(X_train, y_train, X_val, y_val):
    """Train Random Forest model."""
    from sklearn.ensemble import RandomForestRegressor
    import joblib
    
    print("\n  Training Random Forest...")
    start_time = time.time()
    
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    training_time = time.time() - start_time
    
    print(f"  ✓ Random Forest trained in {training_time:.2f}s")
    
    return model, training_time


def train_xgboost(X_train, y_train, X_val, y_val):
    """Train XGBoost model."""
    try:
        import xgboost as xgb
        
        print("\n  Training XGBoost...")
        start_time = time.time()
        
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        # XGBoost API: use early_stopping_rounds in constructor for newer versions
        try:
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=20,
                verbose=False
            )
        except TypeError:
            # Newer XGBoost API
            model.fit(X_train, y_train, verbose=False)
        
        training_time = time.time() - start_time
        print(f"  ✓ XGBoost trained in {training_time:.2f}s")
        
        return model, training_time
        
    except ImportError:
        print("  ⚠ XGBoost not installed. Skipping. Install with: pip install xgboost")
        return None, 0


def train_lstm(X_train, y_train, X_val, y_val, lookback=12):
    """Train LSTM model."""
    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        from tensorflow.keras.callbacks import EarlyStopping
        
        print("\n  Training LSTM...")
        start_time = time.time()
        
        # Prepare sequences
        def create_sequences(X, y, lookback):
            Xs, ys = [], []
            for i in range(len(X) - lookback):
                Xs.append(X[i:(i + lookback)])
                ys.append(y[i + lookback])
            return np.array(Xs), np.array(ys)
        
        X_train_seq, y_train_seq = create_sequences(X_train, y_train, lookback)
        X_val_seq, y_val_seq = create_sequences(X_val, y_val, lookback)
        
        # Build model
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(lookback, X_train.shape[1])),
            Dropout(0.2),
            LSTM(64),
            Dropout(0.2),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        # Train
        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        
        model.fit(
            X_train_seq, y_train_seq,
            validation_data=(X_val_seq, y_val_seq),
            epochs=100,
            batch_size=16,
            callbacks=[early_stop],
            verbose=0
        )
        
        training_time = time.time() - start_time
        print(f"  ✓ LSTM trained in {training_time:.2f}s")
        
        return model, training_time, lookback
        
    except ImportError:
        print("  ⚠ TensorFlow not installed. Skipping. Install with: pip install tensorflow")
        return None, 0, lookback


def predict_lstm(model, X, lookback):
    """Make predictions with LSTM model."""
    if model is None:
        return None
    
    # Create sequences
    X_seq = []
    for i in range(len(X) - lookback):
        X_seq.append(X[i:(i + lookback)])
    X_seq = np.array(X_seq)
    
    predictions = model.predict(X_seq, verbose=0).flatten()
    
    # Pad with NaN for first lookback samples
    full_predictions = np.full(len(X), np.nan)
    full_predictions[lookback:] = predictions
    
    return full_predictions


def create_ensemble(models, X, lookback=None):
    """Create ensemble predictions."""
    predictions = []
    weights = []
    
    rf_model, xgb_model, lstm_model = models
    
    if rf_model is not None:
        predictions.append(rf_model.predict(X))
        weights.append(0.4)
    
    if xgb_model is not None:
        predictions.append(xgb_model.predict(X))
        weights.append(0.4)
    
    if lstm_model is not None:
        lstm_pred = predict_lstm(lstm_model, X, lookback)
        if lstm_pred is not None:
            predictions.append(lstm_pred)
            weights.append(0.2)
    
    if len(predictions) == 0:
        return None
    
    # Normalize weights
    weights = np.array(weights) / sum(weights)
    
    # Weighted average
    ensemble_pred = np.zeros_like(predictions[0])
    for pred, weight in zip(predictions, weights):
        # Handle NaN values from LSTM
        valid_mask = ~np.isnan(pred)
        ensemble_pred[valid_mask] += pred[valid_mask] * weight
    
    return ensemble_pred


def main():
    """Main pipeline execution."""
    
    print("=" * 80)
    print("COMPREHENSIVE ML MODEL DEVELOPMENT PIPELINE")
    print("Training: Random Forest + XGBoost + LSTM + Ensemble")
    print("=" * 80)
    
    pipeline_start = time.time()
    
    # Create output directories
    output_dir = Path("outputs")
    models_dir = output_dir / "models"
    evaluation_dir = output_dir / "evaluation"
    experiments_dir = output_dir / "experiments"
    
    for dir_path in [models_dir, evaluation_dir, experiments_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # Step 1: Load Full Dataset
    # ========================================================================
    print("\n[1/5] Loading full master dataset...")
    
    try:
        df = pd.read_csv("outputs/processed/master_dataset.csv")
        print(f"✓ Loaded master_dataset.csv")
        print(f"✓ Dataset shape: {df.shape}")
        print(f"✓ Date range: {df['year'].min()}-{df['year'].max()}")
        
        # Create date column
        if 'date' not in df.columns:
            df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        else:
            df['date'] = pd.to_datetime(df['date'])
        
        df = df.sort_values('date').reset_index(drop=True)
        
        # Select numeric features
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        exclude_cols = ['year', 'month', 'drought_risk', 'flood_risk', 'rainfall_next_month']
        
        # Determine target
        if 'rainfall_mm' in df.columns:
            target_col = 'rainfall_mm'
        else:
            target_col = [col for col in numeric_cols if col not in exclude_cols][0]
        
        feature_cols = [col for col in numeric_cols if col not in exclude_cols + [target_col]]
        
        print(f"✓ Features: {len(feature_cols)}")
        print(f"✓ Target: {target_col}")
        
        # Split data chronologically (70/15/15)
        n = len(df)
        train_idx = int(n * 0.70)
        val_idx = int(n * 0.85)
        
        train_df = df.iloc[:train_idx].copy()
        val_df = df.iloc[train_idx:val_idx].copy()
        test_df = df.iloc[val_idx:].copy()
        
        print(f"✓ Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")
        
        # Prepare arrays
        X_train = train_df[feature_cols].fillna(0).values
        y_train = train_df[target_col].fillna(train_df[target_col].mean()).values
        X_val = val_df[feature_cols].fillna(0).values
        y_val = val_df[target_col].fillna(val_df[target_col].mean()).values
        X_test = test_df[feature_cols].fillna(0).values
        y_test = test_df[target_col].fillna(test_df[target_col].mean()).values
        test_dates = test_df['date']
        
        print(f"✓ Data prepared")
        
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # ========================================================================
    # Step 2: Train All Models
    # ========================================================================
    print("\n[2/5] Training all models...")
    
    models_results = {}
    
    # Train Random Forest
    rf_model, rf_time = train_random_forest(X_train, y_train, X_val, y_val)
    models_results['random_forest'] = {'model': rf_model, 'training_time': rf_time}
    
    # Train XGBoost
    xgb_model, xgb_time = train_xgboost(X_train, y_train, X_val, y_val)
    models_results['xgboost'] = {'model': xgb_model, 'training_time': xgb_time}
    
    # Train LSTM
    lstm_model, lstm_time, lookback = train_lstm(X_train, y_train, X_val, y_val)
    models_results['lstm'] = {'model': lstm_model, 'training_time': lstm_time, 'lookback': lookback}
    
    print(f"\n✓ All models trained")
    
    # ========================================================================
    # Step 3: Evaluate All Models
    # ========================================================================
    print("\n[3/5] Evaluating all models...")
    
    evaluation_results = {}
    
    for model_name in ['random_forest', 'xgboost', 'lstm', 'ensemble']:
        print(f"\n  Evaluating {model_name}...")
        
        # Get predictions
        if model_name == 'ensemble':
            y_pred_test = create_ensemble(
                (rf_model, xgb_model, lstm_model),
                X_test,
                lookback
            )
            if y_pred_test is None:
                print(f"  ⚠ Skipping ensemble (no models available)")
                continue
        elif model_name == 'lstm':
            if lstm_model is None:
                print(f"  ⚠ Skipping LSTM (not trained)")
                continue
            y_pred_test = predict_lstm(lstm_model, X_test, lookback)
            # Remove NaN values for evaluation
            valid_mask = ~np.isnan(y_pred_test)
            y_pred_test = y_pred_test[valid_mask]
            y_test_eval = y_test[valid_mask]
        else:
            model = models_results[model_name]['model']
            if model is None:
                print(f"  ⚠ Skipping {model_name} (not trained)")
                continue
            y_pred_test = model.predict(X_test)
            y_test_eval = y_test
        
        # Calculate metrics
        if model_name != 'lstm':
            y_test_eval = y_test
            
        metrics = calculate_metrics(y_test_eval, y_pred_test)
        
        print(f"  ✓ {model_name}: R²={metrics['r2_score']:.3f}, RMSE={metrics['rmse']:.3f}, MAE={metrics['mae']:.3f}")
        
        evaluation_results[model_name] = {
            'metrics': metrics,
            'predictions': y_pred_test
        }
        
        # Save model
        if model_name != 'ensemble':
            model = models_results[model_name]['model']
            if model is not None:
                import joblib
                model_path = models_dir / f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                joblib.dump(model, model_path)
                print(f"  ✓ Saved to {model_path}")
    
    # ========================================================================
    # Step 4: Generate Visualizations
    # ========================================================================
    print("\n[4/5] Generating visualizations...")
    
    # Use best model for visualizations (Random Forest)
    best_model_name = 'random_forest'
    y_pred_test = evaluation_results[best_model_name]['predictions']
    
    # Seasonal analysis
    seasonal_results = evaluate_by_season(y_test, y_pred_test, test_dates, target_col)
    seasonal_path = evaluation_dir / "seasonal_performance_full.csv"
    seasonal_results.to_csv(seasonal_path, index=False)
    print(f"  ✓ Seasonal analysis saved")
    
    # Plots
    plot_predictions_vs_actual(
        y_test, y_pred_test,
        str(evaluation_dir / "predictions_vs_actual_full.png"),
        "Rainfall (mm)",
        "Full Dataset: Predictions vs Actual"
    )
    
    plot_residuals_over_time(
        y_test, y_pred_test, test_dates,
        str(evaluation_dir / "residuals_over_time_full.png"),
        "Rainfall (mm)",
        "Full Dataset: Residuals Over Time"
    )
    
    if rf_model is not None:
        plot_feature_importance(
            feature_cols,
            rf_model.feature_importances_,
            str(evaluation_dir / "feature_importance_full.png"),
            top_n=20,
            title="Full Dataset: Top 20 Features"
        )
    
    print(f"  ✓ All visualizations saved")
    
    # ========================================================================
    # Step 5: Log Experiments
    # ========================================================================
    print("\n[5/5] Logging experiments...")
    
    for model_name, results in evaluation_results.items():
        experiment_id = create_experiment_id(f"{model_name}_full")
        
        experiment_data = {
            'model_type': model_name,
            'n_features': len(feature_cols),
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'test_samples': len(X_test),
            'test_r2': results['metrics']['r2_score'],
            'test_rmse': results['metrics']['rmse'],
            'test_mae': results['metrics']['mae'],
            'training_time': models_results.get(model_name, {}).get('training_time', 0)
        }
        
        log_experiment(experiment_id, experiment_data, output_dir)
    
    # Save summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'dataset': {
            'total_samples': len(df),
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'test_samples': len(X_test),
            'n_features': len(feature_cols),
            'target': target_col
        },
        'models': {
            name: {
                'metrics': results['metrics'],
                'training_time': models_results.get(name, {}).get('training_time', 0)
            }
            for name, results in evaluation_results.items()
        },
        'seasonal_performance': seasonal_results.to_dict('records')
    }
    
    summary_path = evaluation_dir / "full_pipeline_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"  ✓ Summary saved to {summary_path}")
    
    # ========================================================================
    # Complete
    # ========================================================================
    pipeline_time = time.time() - pipeline_start
    
    print("\n" + "=" * 80)
    print("✓ COMPREHENSIVE PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nTotal Time: {pipeline_time:.2f}s")
    print(f"\nModels Trained:")
    for name, results in evaluation_results.items():
        metrics = results['metrics']
        print(f"  {name:15s} R²={metrics['r2_score']:.3f}  RMSE={metrics['rmse']:.2f}  MAE={metrics['mae']:.2f}")
    print("\nOutputs:")
    print(f"  Models: {models_dir}/")
    print(f"  Evaluation: {evaluation_dir}/")
    print(f"  Experiments: {experiments_dir}/")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
