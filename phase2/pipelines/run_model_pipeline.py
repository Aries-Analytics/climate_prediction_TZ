"""
Comprehensive Model Development Pipeline - Tanzania Climate Prediction

This script orchestrates the complete ML model development workflow:
1. Preprocessing and feature engineering
2. Model training (RF, XGBoost, LSTM, Ensemble)
3. Model evaluation
4. Experiment tracking

Requirements: All requirements (1.1-7.5)
"""

import sys
import io
import argparse
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Ensure UTF-8 encoding for console output (Windows compatibility)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from evaluation.evaluate import (
    calculate_metrics,
    evaluate_by_season,
    plot_predictions_vs_actual,
    plot_residuals_over_time,
    plot_feature_importance
)

# Import model classes
try:
    from models.random_forest_model import RandomForestModel
    from models.xgboost_model import XGBoostModel
    from models.lstm_model import LSTMModel
    from models.ensemble_model import EnsembleModel
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import model classes: {e}")
    print("Falling back to basic sklearn RandomForest only")
    MODELS_AVAILABLE = False

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
    
    # Append experiment to log
    with open(log_file, 'a') as f:
        json.dump({
            'experiment_id': experiment_id,
            'timestamp': datetime.now().isoformat(),
            **results
        }, f)
        f.write('\n')
    
    logger.info(f"✓ Logged experiment to {log_file}")


def main():
    """Main pipeline execution function."""
    
    print("=" * 80)
    print("ML MODEL DEVELOPMENT PIPELINE - Tanzania Climate Prediction")
    print("=" * 80)
    
    # Create output directories
    output_dir = Path("outputs")
    models_dir = output_dir / "models"
    evaluation_dir = output_dir / "evaluation"
    experiments_dir = output_dir / "experiments"
    
    models_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    experiments_dir.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # Step 1: Load Data
    # ========================================================================
    print("\n[1/4] Loading dataset...")
    
    try:
        # Always use master_dataset.csv (full 288 rows, 2000-2023)
        df = pd.read_csv("outputs/processed/master_dataset.csv")
        print(f"✓ Loaded master_dataset.csv")
        print(f"✓ Dataset shape: {df.shape}")
        
        # Create date column from year and month
        if 'date' not in df.columns and 'year' in df.columns and 'month' in df.columns:
            df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        df = df.sort_values('date').reset_index(drop=True)
        
        # Define features and target
        # Get all numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Exclude date, year, month, and any target columns
        exclude_cols = ['year', 'month', 'drought_risk', 'flood_risk', 'rainfall_next_month']
        
        # Determine target column
        if 'rainfall_next_month' in df.columns:
            target_col = 'rainfall_next_month'
        elif 'rainfall_mm' in df.columns:
            target_col = 'rainfall_mm'
        else:
            # Use first numeric column as target
            target_col = [col for col in numeric_cols if col not in exclude_cols][0]
        
        # Feature columns are all numeric columns except target and excluded columns
        feature_cols = [col for col in numeric_cols if col not in exclude_cols + [target_col]]
        
        print(f"✓ Using {len(feature_cols)} features")
        print(f"✓ Target variable: {target_col}")
        
        # Split data chronologically (70% train, 15% val, 15% test)
        n = len(df)
        train_idx = int(n * 0.70)
        val_idx = int(n * 0.85)
        
        train_df = df.iloc[:train_idx].copy()
        val_df = df.iloc[train_idx:val_idx].copy()
        test_df = df.iloc[val_idx:].copy()
        
        print(f"✓ Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")
        
        # Prepare arrays (fill NaN values)
        X_train = train_df[feature_cols].fillna(0).values
        y_train = train_df[target_col].fillna(train_df[target_col].mean()).values
        X_val = val_df[feature_cols].fillna(0).values
        y_val = val_df[target_col].fillna(val_df[target_col].mean()).values
        X_test = test_df[feature_cols].fillna(0).values
        y_test = test_df[target_col].fillna(test_df[target_col].mean()).values
        test_dates = test_df['date']
        
        print(f"✓ Data prepared (NaN values filled)")
        print(f"  Target range: [{y_train.min():.2f}, {y_train.max():.2f}]")
        
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return 1
    
    # ========================================================================
    # Step 2: Train Baseline Model
    # ========================================================================
    print("\n[2/5] Training Baseline Model (Seasonal Mean)...")
    
    try:
        # Create baseline: predict seasonal mean for each month
        # Calculate mean rainfall for each month from training data
        train_df_with_target = train_df.copy()
        train_df_with_target['target'] = y_train
        
        seasonal_means = train_df_with_target.groupby('month')['target'].mean().to_dict()
        
        # Baseline predictions
        y_pred_baseline_train = np.array([seasonal_means.get(m, y_train.mean()) for m in train_df['month']])
        y_pred_baseline_val = np.array([seasonal_means.get(m, y_train.mean()) for m in val_df['month']])
        y_pred_baseline_test = np.array([seasonal_means.get(m, y_train.mean()) for m in test_df['month']])
        
        # Calculate baseline metrics
        baseline_train_metrics = calculate_metrics(y_train, y_pred_baseline_train)
        baseline_val_metrics = calculate_metrics(y_val, y_pred_baseline_val)
        baseline_test_metrics = calculate_metrics(y_test, y_pred_baseline_test)
        
        print(f"✓ Baseline Model (Seasonal Mean) Performance:")
        print(f"  Train R² = {baseline_train_metrics['r2_score']:.3f}, RMSE = {baseline_train_metrics['rmse']:.3f}")
        print(f"  Val   R² = {baseline_val_metrics['r2_score']:.3f}, RMSE = {baseline_val_metrics['rmse']:.3f}")
        print(f"  Test  R² = {baseline_test_metrics['r2_score']:.3f}, RMSE = {baseline_test_metrics['rmse']:.3f}")
        
        # Save baseline model
        baseline_model = {'type': 'seasonal_mean', 'seasonal_means': seasonal_means}
        baseline_path = models_dir / f"baseline_seasonal_mean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        joblib.dump(baseline_model, baseline_path)
        print(f"✓ Saved baseline model to {baseline_path}")
        
    except Exception as e:
        print(f"✗ Baseline training failed: {e}")
        return 1
    
    # ========================================================================
    # Step 3: Train All Models
    # ========================================================================
    print("\n[3/5] Training all models...")
    
    models_results = {}
    trained_models = {}
    
    # 3.1: Random Forest
    print("\n  [3.1] Training Random Forest...")
    try:
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        rf_model.fit(X_train, y_train)
        
        # Predictions
        rf_pred_test = rf_model.predict(X_test)
        rf_metrics = calculate_metrics(y_test, rf_pred_test)
        
        models_results['RandomForest'] = {
            'model': rf_model,
            'predictions': rf_pred_test,
            'metrics': rf_metrics,
            'path': models_dir / f"random_forest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        }
        trained_models['RandomForest'] = rf_model
        
        joblib.dump(rf_model, models_results['RandomForest']['path'])
        
        print(f"    ✓ RF Test R² = {rf_metrics['r2_score']:.3f}, RMSE = {rf_metrics['rmse']:.3f}")
        
    except Exception as e:
        print(f"    ✗ Random Forest failed: {e}")
        models_results['RandomForest'] = None
    
    # 3.2: XGBoost
    print("\n  [3.2] Training XGBoost...")
    try:
        import xgboost as xgb
        
        xgb_model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        # XGBoost 3.x uses different API for early stopping
        xgb_model.fit(X_train, y_train, 
                     eval_set=[(X_val, y_val)],
                     verbose=False)
        
        # Predictions
        xgb_pred_test = xgb_model.predict(X_test)
        xgb_metrics = calculate_metrics(y_test, xgb_pred_test)
        
        models_results['XGBoost'] = {
            'model': xgb_model,
            'predictions': xgb_pred_test,
            'metrics': xgb_metrics,
            'path': models_dir / f"xgboost_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        }
        trained_models['XGBoost'] = xgb_model
        
        joblib.dump(xgb_model, models_results['XGBoost']['path'])
        
        print(f"    ✓ XGB Test R² = {xgb_metrics['r2_score']:.3f}, RMSE = {xgb_metrics['rmse']:.3f}")
        
    except ImportError:
        print("    ⚠ XGBoost not installed (pip install xgboost)")
        models_results['XGBoost'] = None
    except Exception as e:
        print(f"    ✗ XGBoost failed: {e}")
        models_results['XGBoost'] = None
    
    # 3.3: LSTM (using proper LSTMModel class)
    print("\n  [3.3] Training LSTM...")
    try:
        from models.lstm_model import LSTMModel
        
        # Initialize LSTM model with custom config
        lstm_model = LSTMModel(
            model_name="lstm_rainfall",
            custom_config={
                'sequence_length': 12,  # 12-month lookback
                'units': [64, 32],       # Two LSTM layers
                'dropout': 0.2,
                'epochs': 50,
                'batch_size': 16,
                'patience': 10,
                'verbose': 0
            }
        )
        
        # Train LSTM
        lstm_results = lstm_model.train(X_train, y_train, X_val, y_val)
        
        # Get predictions (will have NaN padding for first sequence_length-1 samples)
        lstm_pred_test = lstm_model.predict(X_test)
        
        # Calculate metrics only on valid predictions (skip NaN padding)
        lstm_valid_mask = ~np.isnan(lstm_pred_test)
        if lstm_valid_mask.sum() > 0:
            lstm_metrics = calculate_metrics(y_test[lstm_valid_mask], lstm_pred_test[lstm_valid_mask])
            
            models_results['LSTM'] = {
                'model': lstm_model,
                'predictions': lstm_pred_test,
                'metrics': lstm_metrics,
                'path': models_dir / f"lstm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            trained_models['LSTM'] = lstm_model
            
            # Save model
            lstm_model.save(str(models_results['LSTM']['path']))
            
            print(f"    ✓ LSTM Test R² = {lstm_metrics['r2_score']:.3f}, RMSE = {lstm_metrics['rmse']:.3f}")
            print(f"    ✓ Valid predictions: {lstm_valid_mask.sum()}/{len(y_test)} (first {12-1} samples are NaN padding)")
        else:
            raise ValueError("No valid LSTM predictions generated")
            
    except ImportError as e:
        print(f"    ⚠ TensorFlow not installed: {e}")
        print("    Install with: pip install tensorflow")
        models_results['LSTM'] = None
    except Exception as e:
        print(f"    ✗ LSTM failed: {e}")
        import traceback
        print(f"    Details: {traceback.format_exc()}")
        models_results['LSTM'] = None
    
    # 3.4: Ensemble (smart - only include models better than baseline)
    print("\n  [3.4] Creating Ensemble...")
    try:
        # Only include models that perform better than baseline
        good_models = []
        for model_name, result in models_results.items():
            if result is not None:
                # Check if model beats baseline
                if result['metrics']['r2_score'] > baseline_test_metrics['r2_score']:
                    good_models.append(model_name)
        
        if len(good_models) >= 2:
            print(f"    Using {len(good_models)} models: {', '.join(good_models)}")
            
            # Collect predictions from good models only
            ensemble_preds = []
            for model_name in good_models:
                ensemble_preds.append(models_results[model_name]['predictions'])
            
            # Stack predictions (shape: n_models x n_samples)
            ensemble_preds = np.array(ensemble_preds)
            
            # Handle NaN values (from LSTM padding) using nanmean
            # For samples where all models have predictions, use average
            # For samples with NaN (LSTM padding), use average of available models
            ensemble_pred_test = np.nanmean(ensemble_preds, axis=0)
            
            # Calculate metrics only on samples where we have predictions
            valid_mask = ~np.isnan(ensemble_pred_test)
            if valid_mask.sum() > 0:
                ensemble_metrics = calculate_metrics(y_test[valid_mask], ensemble_pred_test[valid_mask])
            else:
                raise ValueError("No valid ensemble predictions")
            
            # Equal weights for good models
            equal_weights = [1.0 / len(good_models)] * len(good_models)
            
            models_results['Ensemble'] = {
                'model': None,  # Ensemble is just a combination
                'predictions': ensemble_pred_test,
                'metrics': ensemble_metrics,
                'components': good_models,
                'weights': dict(zip(good_models, equal_weights))
            }
        elif len(good_models) == 1:
            print(f"    ⚠ Only 1 model beats baseline ({good_models[0]}), skipping ensemble")
            models_results['Ensemble'] = None
        else:
            print(f"    ⚠ No models beat baseline, skipping ensemble")
            models_results['Ensemble'] = None
            
    except Exception as e:
        print(f"    ✗ Ensemble failed: {e}")
        import traceback
        print(f"    Details: {traceback.format_exc()}")
        models_results['Ensemble'] = None
    
    # Summary comparison
    print("\n✓ Model Training Complete - Performance Summary:")
    print(f"\n  {'Model':<15} {'Test R²':<10} {'RMSE':<10} {'vs Baseline':<15}")
    print(f"  {'-'*50}")
    print(f"  {'Baseline':<15} {baseline_test_metrics['r2_score']:<10.3f} {baseline_test_metrics['rmse']:<10.2f} {'---':<15}")
    
    best_model_name = None
    best_r2 = baseline_test_metrics['r2_score']
    
    for model_name, result in models_results.items():
        if result is not None:
            r2 = result['metrics']['r2_score']
            rmse = result['metrics']['rmse']
            improvement = r2 - baseline_test_metrics['r2_score']
            
            print(f"  {model_name:<15} {r2:<10.3f} {rmse:<10.2f} {improvement:+.3f} ({improvement/max(abs(baseline_test_metrics['r2_score']), 0.001)*100:+.1f}%)")
            
            if r2 > best_r2:
                best_r2 = r2
                best_model_name = model_name
    
    if best_model_name:
        print(f"\n  🏆 Best Model: {best_model_name} (R² = {best_r2:.3f})")
    else:
        print(f"\n  ⚠ All models performed worse than baseline!")
    
    # Use best model for evaluation (or RF if none better)
    if best_model_name and models_results[best_model_name]:
        best_result = models_results[best_model_name]
        model = best_result['model']
        y_pred_test = best_result['predictions']
        test_metrics = best_result['metrics']
        model_path = best_result.get('path', models_dir / f"best_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl")
    elif models_results.get('RandomForest'):
        best_model_name = 'RandomForest'
        best_result = models_results['RandomForest']
        model = best_result['model']
        y_pred_test = best_result['predictions']
        test_metrics = best_result['metrics']
        model_path = best_result['path']
    else:
        print("\n✗ No models trained successfully!")
        return 1
    
    # ========================================================================
    # Step 4: Evaluation
    # ========================================================================
    print("\n[4/5] Generating evaluation reports...")
    
    try:
        # Seasonal performance analysis
        print("\n  Analyzing seasonal performance...")
        seasonal_results = evaluate_by_season(
            y_true=y_test,
            y_pred=y_pred_test,
            dates=test_dates,
            target_name="rainfall"
        )
        
        seasonal_path = evaluation_dir / "seasonal_performance.csv"
        seasonal_results.to_csv(seasonal_path, index=False)
        print(f"  ✓ Saved seasonal analysis to {seasonal_path}")
        
        # Predictions vs Actual plot
        print("\n  Creating predictions vs actual plot...")
        plot_predictions_vs_actual(
            y_true=y_test,
            y_pred=y_pred_test,
            save_path=str(evaluation_dir / "predictions_vs_actual.png"),
            target_name="Rainfall (mm)",
            title="Rainfall Predictions vs Actual Values"
        )
        
        # Residuals over time plot
        print("  Creating residuals over time plot...")
        plot_residuals_over_time(
            y_true=y_test,
            y_pred=y_pred_test,
            dates=test_dates,
            save_path=str(evaluation_dir / "residuals_over_time.png"),
            target_name="Rainfall (mm)",
            title="Prediction Residuals Over Time"
        )
        
        # Feature importance plot
        print("  Creating feature importance plot...")
        plot_feature_importance(
            feature_names=feature_cols,
            importances=model.feature_importances_,
            save_path=str(evaluation_dir / "feature_importance.png"),
            top_n=20,
            title="Top 20 Feature Importances"
        )
        
        print(f"\n✓ All evaluation reports saved to {evaluation_dir}/")
        
    except Exception as e:
        print(f"✗ Evaluation failed: {e}")
        return 1
    
    # ========================================================================
    # Step 5: Experiment Tracking
    # ========================================================================
    print("\n[5/5] Logging experiment...")
    
    try:
        experiment_id = create_experiment_id("rainfall_model")
        
        # Log all models
        all_models_data = {}
        for model_name, result in models_results.items():
            if result is not None:
                all_models_data[model_name] = {
                    'test_r2': result['metrics']['r2_score'],
                    'test_rmse': result['metrics']['rmse'],
                    'test_mae': result['metrics']['mae'],
                    'improvement_over_baseline': result['metrics']['r2_score'] - baseline_test_metrics['r2_score']
                }
        
        experiment_data = {
            'best_model': best_model_name,
            'n_features': len(feature_cols),
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'test_samples': len(X_test),
            'baseline_test_r2': baseline_test_metrics['r2_score'],
            'baseline_test_rmse': baseline_test_metrics['rmse'],
            'best_test_r2': test_metrics['r2_score'],
            'best_test_rmse': test_metrics['rmse'],
            'best_test_mae': test_metrics['mae'],
            'r2_improvement_over_baseline': test_metrics['r2_score'] - baseline_test_metrics['r2_score'],
            'rmse_improvement_over_baseline': baseline_test_metrics['rmse'] - test_metrics['rmse'],
            'all_models': all_models_data,
            'baseline_path': str(baseline_path)
        }
        
        log_experiment(experiment_id, experiment_data, output_dir)
        print(f"✓ Logged experiment: {experiment_id}")
        
        # Save summary report
        # Compile all models' results
        all_models_summary = {}
        for model_name, result in models_results.items():
            if result is not None:
                all_models_summary[model_name] = {
                    'test_r2': result['metrics']['r2_score'],
                    'test_rmse': result['metrics']['rmse'],
                    'test_mae': result['metrics']['mae'],
                    'improvement_over_baseline': {
                        'r2': result['metrics']['r2_score'] - baseline_test_metrics['r2_score'],
                        'rmse': baseline_test_metrics['rmse'] - result['metrics']['rmse']
                    }
                }
        
        summary = {
            'experiment_id': experiment_id,
            'timestamp': datetime.now().isoformat(),
            'best_model': best_model_name,
            'baseline': {
                'type': 'seasonal_mean',
                'test_r2': baseline_test_metrics['r2_score'],
                'test_rmse': baseline_test_metrics['rmse'],
                'test_mae': baseline_test_metrics['mae']
            },
            'all_models': all_models_summary,
            'best_model_metrics': {
                'test': test_metrics
            },
            'improvement_over_baseline': {
                'r2_improvement': test_metrics['r2_score'] - baseline_test_metrics['r2_score'],
                'rmse_improvement': baseline_test_metrics['rmse'] - test_metrics['rmse'],
                'r2_improvement_pct': (test_metrics['r2_score'] - baseline_test_metrics['r2_score']) / max(abs(baseline_test_metrics['r2_score']), 0.001) * 100,
                'rmse_improvement_pct': (baseline_test_metrics['rmse'] - test_metrics['rmse']) / baseline_test_metrics['rmse'] * 100
            },
            'seasonal_performance': seasonal_results.to_dict('records')
        }
        
        summary_path = evaluation_dir / "evaluation_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✓ Saved evaluation summary to {summary_path}")
        
    except Exception as e:
        print(f"⚠ Experiment tracking failed: {e}")
        # Don't fail the pipeline for tracking errors
    
    # ========================================================================
    # Pipeline Complete
    # ========================================================================
    print("\n" + "=" * 80)
    print("✓ PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nOutputs saved to:")
    print(f"  Models: {models_dir}/")
    print(f"  Evaluation: {evaluation_dir}/")
    print(f"  Experiments: {experiments_dir}/")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
