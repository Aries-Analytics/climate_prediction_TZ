"""
Model Evaluation Engine

This module implements comprehensive model evaluation including metrics calculation,
uncertainty quantification, regional/seasonal analysis, and visualization.

Requirements: 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

logger = logging.getLogger(__name__)


# ============================================================================
# Metrics Calculation (Task 9.1)
# ============================================================================

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate comprehensive regression metrics.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        Dict[str, float]: Dictionary of metrics (R², RMSE, MAE, MAPE)
        
    Requirements: 2.6, 4.3
    """
    metrics = {
        'r2': float(r2_score(y_true, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
        'mae': float(mean_absolute_error(y_true, y_pred))
    }
    
    # Calculate MAPE (avoiding division by zero)
    mask = y_true != 0
    if mask.any():
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        metrics['mape'] = float(mape)
    else:
        metrics['mape'] = None
    
    return metrics


# ============================================================================
# Uncertainty Quantification (Task 9.2)
# ============================================================================

def calculate_quantile_predictions(models: List[Any], X: np.ndarray,
                                  quantiles: List[float] = [0.1, 0.5, 0.9]) -> Dict[str, np.ndarray]:
    """
    Calculate quantile predictions for uncertainty estimation.
    
    Uses ensemble of models to estimate prediction quantiles.
    
    Args:
        models: List of trained models
        X: Input features
        quantiles: List of quantiles to calculate (default: 10th, 50th, 90th percentiles)
        
    Returns:
        Dict[str, np.ndarray]: Dictionary with quantile predictions
        
    Requirements: 3.1, 3.2
    """
    logger.info(f"Calculating quantile predictions for {len(models)} models")
    
    # Get predictions from all models
    predictions = []
    for model in models:
        pred = model.predict(X)
        predictions.append(pred)
    
    predictions = np.array(predictions)
    
    # Calculate quantiles
    quantile_preds = {}
    for q in quantiles:
        quantile_preds[f'q{int(q*100)}'] = np.quantile(predictions, q, axis=0)
    
    # Add mean prediction
    quantile_preds['mean'] = np.mean(predictions, axis=0)
    
    return quantile_preds


def calculate_prediction_intervals(y_pred: np.ndarray, y_true: np.ndarray,
                                   confidence: float = 0.95) -> Dict[str, Any]:
    """
    Calculate prediction intervals and validate coverage.
    
    Args:
        y_pred: Predicted values
        y_true: True values
        confidence: Confidence level (default: 0.95 for 95% intervals)
        
    Returns:
        Dict[str, Any]: Prediction intervals and coverage statistics
        
    Requirements: 3.2, 3.3, 3.4, 3.5
    """
    # Calculate residuals
    residuals = y_true - y_pred
    
    # Calculate standard error
    std_error = np.std(residuals)
    
    # Calculate z-score for confidence level
    from scipy import stats
    z_score = stats.norm.ppf((1 + confidence) / 2)
    
    # Calculate intervals
    margin = z_score * std_error
    lower_bound = y_pred - margin
    upper_bound = y_pred + margin
    
    # Validate coverage
    within_interval = (y_true >= lower_bound) & (y_true <= upper_bound)
    actual_coverage = np.mean(within_interval)
    
    results = {
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'margin': float(margin),
        'std_error': float(std_error),
        'confidence_level': confidence,
        'expected_coverage': confidence,
        'actual_coverage': float(actual_coverage),
        'coverage_valid': abs(actual_coverage - confidence) < 0.05  # Within 5% tolerance
    }
    
    logger.info(f"Prediction intervals: {confidence*100:.0f}% confidence")
    logger.info(f"  Expected coverage: {confidence*100:.1f}%")
    logger.info(f"  Actual coverage: {actual_coverage*100:.1f}%")
    
    return results


def save_predictions_with_uncertainty(y_true: np.ndarray, y_pred: np.ndarray,
                                     intervals: Dict[str, Any], save_path: str) -> str:
    """
    Save predictions with uncertainty estimates to CSV.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        intervals: Prediction intervals dictionary
        save_path: Path to save CSV file
        
    Returns:
        str: Path to saved file
        
    Requirements: 3.5
    """
    df = pd.DataFrame({
        'true_value': y_true,
        'prediction': y_pred,
        'lower_bound': intervals['lower_bound'],
        'upper_bound': intervals['upper_bound']
    })
    
    df.to_csv(save_path, index=False)
    logger.info(f"Saved predictions with uncertainty to {save_path}")
    
    return save_path


# ============================================================================
# Regional Performance Analysis (Task 9.3)
# ============================================================================

def evaluate_by_region(y_true: np.ndarray, y_pred: np.ndarray,
                      regions: np.ndarray) -> Dict[str, Dict[str, float]]:
    """
    Calculate performance metrics separately for each region.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        regions: Region labels for each sample
        
    Returns:
        Dict[str, Dict[str, float]]: Metrics for each region
        
    Requirements: 4.1, 4.3
    """
    logger.info("Evaluating performance by region")
    
    unique_regions = np.unique(regions)
    results = {}
    
    for region in unique_regions:
        mask = regions == region
        if mask.sum() > 0:
            region_metrics = calculate_metrics(y_true[mask], y_pred[mask])
            results[str(region)] = region_metrics
            logger.info(f"  {region}: R²={region_metrics['r2']:.4f}, "
                       f"RMSE={region_metrics['rmse']:.4f}")
    
    return results


# ============================================================================
# Seasonal Performance Analysis (Task 9.4)
# ============================================================================

def evaluate_by_season(y_true: np.ndarray, y_pred: np.ndarray,
                      months: np.ndarray) -> Dict[str, Dict[str, float]]:
    """
    Calculate performance metrics separately for each season.
    
    Seasons:
    - Short rains: October-December (months 10-12)
    - Long rains: March-May (months 3-5)
    - Dry season: June-September, January-February (months 1-2, 6-9)
    
    Args:
        y_true: True values
        y_pred: Predicted values
        months: Month numbers (1-12) for each sample
        
    Returns:
        Dict[str, Dict[str, float]]: Metrics for each season
        
    Requirements: 4.2, 4.3
    """
    logger.info("Evaluating performance by season")
    
    # Define seasons
    short_rains_mask = np.isin(months, [10, 11, 12])
    long_rains_mask = np.isin(months, [3, 4, 5])
    dry_season_mask = np.isin(months, [1, 2, 6, 7, 8, 9])
    
    results = {}
    
    # Short rains
    if short_rains_mask.sum() > 0:
        metrics = calculate_metrics(y_true[short_rains_mask], y_pred[short_rains_mask])
        results['short_rains'] = metrics
        logger.info(f"  Short rains: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.4f}")
    
    # Long rains
    if long_rains_mask.sum() > 0:
        metrics = calculate_metrics(y_true[long_rains_mask], y_pred[long_rains_mask])
        results['long_rains'] = metrics
        logger.info(f"  Long rains: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.4f}")
    
    # Dry season
    if dry_season_mask.sum() > 0:
        metrics = calculate_metrics(y_true[dry_season_mask], y_pred[dry_season_mask])
        results['dry_season'] = metrics
        logger.info(f"  Dry season: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.4f}")
    
    return results


# ============================================================================
# Visualization Functions (Task 9.5)
# ============================================================================

def plot_predictions_vs_actual(y_true: np.ndarray, y_pred: np.ndarray,
                               save_path: str, title: str = "Predictions vs Actual") -> str:
    """
    Create scatter plot comparing predicted vs actual values.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        save_path: Path to save plot
        title: Plot title
        
    Returns:
        str: Path to saved plot
        
    Requirements: 4.4, 4.5
    """
    plt.figure(figsize=(10, 8))
    
    # Scatter plot
    plt.scatter(y_true, y_pred, alpha=0.5, s=30)
    
    # Perfect prediction line
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
    
    # Calculate metrics for annotation
    metrics = calculate_metrics(y_true, y_pred)
    
    # Add metrics text
    textstr = f"R² = {metrics['r2']:.4f}\nRMSE = {metrics['rmse']:.4f}\nMAE = {metrics['mae']:.4f}"
    plt.text(0.05, 0.95, textstr, transform=plt.gca().transAxes,
            fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.xlabel('Actual Values', fontsize=12)
    plt.ylabel('Predicted Values', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved predictions vs actual plot to {save_path}")
    
    return save_path


def plot_residuals_over_time(y_true: np.ndarray, y_pred: np.ndarray,
                             time_index: Optional[np.ndarray],
                             save_path: str, title: str = "Residuals Over Time") -> str:
    """
    Create time series plot of prediction residuals.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        time_index: Time index for x-axis (optional)
        save_path: Path to save plot
        title: Plot title
        
    Returns:
        str: Path to saved plot
        
    Requirements: 4.4, 4.5
    """
    residuals = y_true - y_pred
    
    plt.figure(figsize=(14, 6))
    
    if time_index is not None:
        plt.plot(time_index, residuals, marker='o', linestyle='-', alpha=0.6, markersize=4)
    else:
        plt.plot(residuals, marker='o', linestyle='-', alpha=0.6, markersize=4)
    
    # Zero line
    plt.axhline(y=0, color='r', linestyle='--', lw=2, label='Zero Error')
    
    # Add standard deviation bands
    std_residuals = np.std(residuals)
    plt.axhline(y=std_residuals, color='orange', linestyle=':', lw=1.5, label=f'±1 Std ({std_residuals:.2f})')
    plt.axhline(y=-std_residuals, color='orange', linestyle=':', lw=1.5)
    
    plt.xlabel('Time' if time_index is not None else 'Sample Index', fontsize=12)
    plt.ylabel('Residual (Actual - Predicted)', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved residuals plot to {save_path}")
    
    return save_path


def plot_feature_importance(importance_df: pd.DataFrame, save_path: str,
                           top_n: int = 20, title: str = "Feature Importance") -> str:
    """
    Create bar chart of feature importance.
    
    Args:
        importance_df: DataFrame with 'feature' and 'importance' columns
        save_path: Path to save plot
        top_n: Number of top features to display
        title: Plot title
        
    Returns:
        str: Path to saved plot
        
    Requirements: 4.4, 4.6
    """
    plt.figure(figsize=(10, max(8, top_n * 0.4)))
    
    # Get top N features
    top_features = importance_df.head(top_n)
    
    # Create horizontal bar chart
    plt.barh(range(len(top_features)), top_features['importance'])
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Importance', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.gca().invert_yaxis()  # Highest importance at top
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved feature importance plot to {save_path}")
    
    return save_path


# ============================================================================
# Comprehensive Evaluation Report (Task 9.6)
# ============================================================================

def generate_evaluation_report(model, X_test: np.ndarray, y_test: np.ndarray,
                               feature_names: Optional[List[str]] = None,
                               months: Optional[np.ndarray] = None,
                               regions: Optional[np.ndarray] = None,
                               output_dir: str = "outputs/evaluation",
                               model_name: str = "model") -> Dict[str, Any]:
    """
    Generate comprehensive evaluation report with all metrics and visualizations.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test targets
        feature_names: Optional list of feature names
        months: Optional month numbers for seasonal analysis
        regions: Optional region labels for regional analysis
        output_dir: Directory to save outputs
        model_name: Name of the model for file naming
        
    Returns:
        Dict[str, Any]: Comprehensive evaluation results
        
    Requirements: 4.3, 4.6, 4.7
    """
    logger.info(f"Generating comprehensive evaluation report for {model_name}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get predictions
    y_pred = model.predict(X_test)
    
    # Handle NaN predictions (from LSTM padding)
    valid_mask = ~np.isnan(y_pred)
    if not valid_mask.all():
        logger.warning(f"Found {(~valid_mask).sum()} NaN predictions, using only valid predictions")
        y_test = y_test[valid_mask]
        y_pred = y_pred[valid_mask]
        if months is not None:
            months = months[valid_mask]
        if regions is not None:
            regions = regions[valid_mask]
    
    # Calculate overall metrics
    overall_metrics = calculate_metrics(y_test, y_pred)
    
    # Check R² threshold
    r2_threshold = 0.85
    if overall_metrics['r2'] < r2_threshold:
        logger.warning(f"⚠ Model R² ({overall_metrics['r2']:.4f}) is below threshold ({r2_threshold})")
        logger.warning("  Suggestions:")
        logger.warning("  - Increase model complexity or ensemble size")
        logger.warning("  - Add more relevant features")
        logger.warning("  - Tune hyperparameters")
        logger.warning("  - Check for data quality issues")
    
    # Initialize results
    results = {
        'model_name': model_name,
        'overall_metrics': overall_metrics,
        'r2_threshold': r2_threshold,
        'meets_threshold': overall_metrics['r2'] >= r2_threshold
    }
    
    # Seasonal analysis
    if months is not None:
        seasonal_metrics = evaluate_by_season(y_test, y_pred, months)
        results['seasonal_metrics'] = seasonal_metrics
    
    # Regional analysis
    if regions is not None:
        regional_metrics = evaluate_by_region(y_test, y_pred, regions)
        results['regional_metrics'] = regional_metrics
    
    # Prediction intervals
    intervals = calculate_prediction_intervals(y_pred, y_test, confidence=0.95)
    results['prediction_intervals'] = {
        'confidence_level': intervals['confidence_level'],
        'expected_coverage': intervals['expected_coverage'],
        'actual_coverage': intervals['actual_coverage'],
        'coverage_valid': intervals['coverage_valid']
    }
    
    # Save predictions with uncertainty
    pred_file = output_path / f"{model_name}_predictions_with_uncertainty.csv"
    save_predictions_with_uncertainty(y_test, y_pred, intervals, str(pred_file))
    
    # Create visualizations
    viz_files = []
    
    # 1. Predictions vs Actual
    viz_path = output_path / f"{model_name}_predictions_vs_actual.png"
    plot_predictions_vs_actual(y_test, y_pred, str(viz_path), 
                              title=f"{model_name.upper()}: Predictions vs Actual")
    viz_files.append(str(viz_path))
    
    # 2. Residuals over time
    viz_path = output_path / f"{model_name}_residuals_over_time.png"
    plot_residuals_over_time(y_test, y_pred, None, str(viz_path),
                            title=f"{model_name.upper()}: Residuals Over Time")
    viz_files.append(str(viz_path))
    
    # 3. Feature importance (if available)
    if hasattr(model, 'get_feature_importance'):
        try:
            importance_df = model.get_feature_importance(feature_names)
            viz_path = output_path / f"{model_name}_feature_importance.png"
            plot_feature_importance(importance_df, str(viz_path),
                                  title=f"{model_name.upper()}: Feature Importance")
            viz_files.append(str(viz_path))
        except Exception as e:
            logger.warning(f"Could not generate feature importance plot: {e}")
    
    results['visualization_files'] = viz_files
    
    # Save summary JSON
    summary_file = output_path / f"{model_name}_evaluation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved evaluation summary to {summary_file}")
    logger.info(f"Generated {len(viz_files)} visualization files")
    
    return results
