"""
Comprehensive Model Evaluation Script

This script generates evaluation reports and visualizations for all trained models.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import json
import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from evaluation.evaluate import (
    calculate_metrics,
    evaluate_by_season,
    plot_predictions_vs_actual,
    plot_residuals_over_time,
)
from models.train_models import load_trained_models
from utils.logger import setup_logging

logger = logging.getLogger(__name__)


def create_model_comparison_plot(results_dict, save_path):
    """Create bar chart comparing model performance."""
    logger.info("Creating model comparison plot...")
    
    models = []
    r2_scores = []
    rmse_scores = []
    mae_scores = []
    
    # Handle both old and new result structures
    if 'models' in results_dict:
        # New structure: results_dict['models'][model_name]
        results_to_plot = results_dict['models']
    else:
        # Old structure: results_dict[model_name]
        results_to_plot = results_dict
    
    for model_name, metrics in results_to_plot.items():
        if metrics:
            # Handle both 'r2' and 'r2_score' keys
            r2_key = 'r2_score' if 'r2_score' in metrics else 'r2'
            if r2_key in metrics:
                models.append(model_name.upper())
                r2_scores.append(metrics[r2_key])
                rmse_scores.append(metrics['rmse'])
                mae_scores.append(metrics['mae'])
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # R² scores
    axes[0].bar(models, r2_scores, color=['#2ecc71', '#3498db', '#e74c3c', '#9b59b6'][:len(models)])
    axes[0].set_ylabel('R² Score', fontsize=12)
    axes[0].set_title('R² Score by Model', fontsize=14, fontweight='bold')
    axes[0].axhline(y=0.85, color='r', linestyle='--', label='Target (0.85)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # RMSE
    axes[1].bar(models, rmse_scores, color=['#2ecc71', '#3498db', '#e74c3c', '#9b59b6'][:len(models)])
    axes[1].set_ylabel('RMSE', fontsize=12)
    axes[1].set_title('RMSE by Model', fontsize=14, fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    # MAE
    axes[2].bar(models, mae_scores, color=['#2ecc71', '#3498db', '#e74c3c', '#9b59b6'][:len(models)])
    axes[2].set_ylabel('MAE', fontsize=12)
    axes[2].set_title('MAE by Model', fontsize=14, fontweight='bold')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✓ Saved model comparison plot to {save_path}")


def create_feature_importance_plot(importance_file, save_path, top_n=20):
    """Create feature importance plot."""
    logger.info(f"Creating feature importance plot from {importance_file}...")
    
    if not Path(importance_file).exists():
        logger.warning(f"Feature importance file not found: {importance_file}")
        return
    
    df = pd.read_csv(importance_file)
    df_top = df.head(top_n)
    
    plt.figure(figsize=(10, 8))
    plt.barh(range(len(df_top)), df_top['importance'], color='steelblue')
    plt.yticks(range(len(df_top)), df_top['feature'])
    plt.xlabel('Importance', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.title(f'Top {top_n} Most Important Features', fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✓ Saved feature importance plot to {save_path}")


def generate_evaluation_summary(results_dict, save_path):
    """Generate JSON summary of evaluation results."""
    logger.info("Generating evaluation summary...")
    
    summary = {
        "evaluation_date": pd.Timestamp.now().isoformat(),
        "models": results_dict,
        "best_model": max(results_dict.items(), key=lambda x: x[1].get('r2', 0) if x[1] else 0)[0],
        "target_achieved": any(m.get('r2', 0) >= 0.85 for m in results_dict.values() if m)
    }
    
    with open(save_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"✓ Saved evaluation summary to {save_path}")


def main():
    """Main evaluation execution."""
    setup_logging(logging.INFO)
    
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE MODEL EVALUATION")
    logger.info("=" * 80)
    
    # Create output directory structure
    eval_base = Path("outputs/evaluation")
    eval_base.mkdir(parents=True, exist_ok=True)
    
    # Use latest/ for current evaluation
    eval_dir = eval_base / "latest"
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    # Create archive directory for historical runs
    archive_dir = eval_base / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Load test data
    logger.info("\nLoading test data...")
    test_df = pd.read_csv("outputs/processed/features_test.csv")
    
    # Get feature columns (exclude year, month, and target)
    numeric_cols = test_df.select_dtypes(include=['number']).columns.tolist()
    exclude_cols = ['year', 'month']
    feature_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    # Handle target variable
    if 'rainfall_mm' in feature_cols:
        target_col = 'rainfall_mm'
        feature_cols.remove('rainfall_mm')
    else:
        target_col = feature_cols[-1]
        feature_cols = feature_cols[:-1]
    
    # Drop all-NaN columns
    all_nan_cols = test_df[feature_cols].columns[test_df[feature_cols].isnull().all()].tolist()
    if all_nan_cols:
        logger.info(f"Dropping {len(all_nan_cols)} all-NaN columns")
        feature_cols = [col for col in feature_cols if col not in all_nan_cols]
    
    X_test = test_df[feature_cols].fillna(0).values
    y_test = test_df[target_col].values
    
    # Create date column for time series plots
    test_dates = pd.to_datetime(test_df[['year', 'month']].assign(day=1))
    
    logger.info(f"Test set: {X_test.shape[0]} samples, {X_test.shape[1]} features")
    logger.info(f"Target variable: {target_col}")
    
    # Load trained models
    logger.info("\nLoading trained models...")
    try:
        models = load_trained_models("outputs/models")
        logger.info(f"Loaded {len(models)} models: {list(models.keys())}")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        return
    
    # Evaluate each model
    results = {}
    
    for model_name, model in models.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"EVALUATING {model_name.upper()}")
        logger.info(f"{'='*80}")
        
        try:
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Handle LSTM padding (NaN values)
            if hasattr(model, 'sequence_length'):
                valid_mask = ~np.isnan(y_pred)
                if valid_mask.sum() == 0:
                    logger.warning(f"{model_name}: No valid predictions")
                    continue
                y_pred_valid = y_pred[valid_mask]
                y_test_valid = y_test[valid_mask]
                dates_valid = test_dates[valid_mask]
            else:
                y_pred_valid = y_pred
                y_test_valid = y_test
                dates_valid = test_dates
            
            # Calculate metrics
            metrics = calculate_metrics(y_test_valid, y_pred_valid)
            results[model_name] = metrics
            
            logger.info(f"  R² Score: {metrics['r2_score']:.4f}")
            logger.info(f"  RMSE: {metrics['rmse']:.4f}")
            logger.info(f"  MAE: {metrics['mae']:.4f}")
            logger.info(f"  MAPE: {metrics['mape']:.2f}%")
            
            # Create predictions vs actual plot
            plot_path = eval_dir / f"{model_name}_predictions_vs_actual.png"
            plot_predictions_vs_actual(
                y_test_valid,
                y_pred_valid,
                str(plot_path),
                target_name="Rainfall (mm)",
                title=f"{model_name.upper()}: Predictions vs Actual"
            )
            
            # Create residuals plot
            residuals_path = eval_dir / f"{model_name}_residuals_over_time.png"
            plot_residuals_over_time(
                y_test_valid,
                y_pred_valid,
                dates_valid,
                str(residuals_path),
                target_name="Rainfall (mm)",
                title=f"{model_name.upper()}: Residuals Over Time"
            )
            
            # Seasonal evaluation
            try:
                seasonal_results = evaluate_by_season(
                    y_test_valid,
                    y_pred_valid,
                    dates_valid,
                    target_name="rainfall"
                )
                seasonal_path = eval_dir / f"{model_name}_seasonal_performance.csv"
                seasonal_results.to_csv(seasonal_path, index=False)
                logger.info(f"  Saved seasonal performance to {seasonal_path}")
            except Exception as e:
                logger.warning(f"  Seasonal evaluation failed: {e}")
            
        except Exception as e:
            logger.error(f"  Evaluation failed for {model_name}: {e}")
            results[model_name] = None
    
    # Create model comparison plot
    logger.info(f"\n{'='*80}")
    logger.info("CREATING COMPARISON VISUALIZATIONS")
    logger.info(f"{'='*80}")
    
    comparison_path = eval_dir / "model_comparison.png"
    create_model_comparison_plot(results, comparison_path)
    
    # Create feature importance plots
    for model_name in ['random_forest', 'xgboost']:
        importance_file = f"outputs/models/{model_name}_climate_feature_importance.csv"
        if model_name == 'xgboost':
            importance_file = f"outputs/models/{model_name}_climate_feature_importance_gain.csv"
        
        if Path(importance_file).exists():
            plot_path = eval_dir / f"{model_name}_feature_importance.png"
            create_feature_importance_plot(importance_file, plot_path)
    
    # Generate summary
    summary_path = eval_dir / "evaluation_summary.json"
    generate_evaluation_summary(results, summary_path)
    
    # Print final summary
    logger.info(f"\n{'='*80}")
    logger.info("EVALUATION COMPLETE!")
    logger.info(f"{'='*80}")
    logger.info(f"\nResults saved to: {eval_dir}")
    logger.info("\nGenerated files:")
    logger.info("  - model_comparison.png")
    logger.info("  - *_predictions_vs_actual.png (per model)")
    logger.info("  - *_residuals_over_time.png (per model)")
    logger.info("  - *_feature_importance.png (RF & XGBoost)")
    logger.info("  - *_seasonal_performance.csv (per model)")
    logger.info("  - evaluation_summary.json")
    
    logger.info(f"\n{'='*80}")
    logger.info("BEST MODEL PERFORMANCE")
    logger.info(f"{'='*80}")
    best_model = max(results.items(), key=lambda x: x[1].get('r2_score', 0) if x[1] else 0)
    logger.info(f"Best Model: {best_model[0].upper()}")
    logger.info(f"  R² Score: {best_model[1]['r2_score']:.4f}")
    logger.info(f"  RMSE: {best_model[1]['rmse']:.4f}")
    logger.info(f"  MAE: {best_model[1]['mae']:.4f}")
    
    if best_model[1]['r2_score'] >= 0.85:
        logger.info("\n🎯 TARGET ACHIEVED: R² ≥ 0.85!")
    else:
        logger.info(f"\n⚠️  Target not achieved. Gap: {0.85 - best_model[1]['r2_score']:.4f}")
    
    logger.info(f"{'='*80}\n")


if __name__ == "__main__":
    main()
