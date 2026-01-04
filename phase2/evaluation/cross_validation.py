"""
Time-Series Cross-Validation Module

This module implements walk-forward time-series cross-validation to provide
robust performance estimates that account for temporal autocorrelation.

Key features:
- Expanding window strategy (respects temporal ordering)
- Confidence interval calculations using t-distribution
- Aggregated metrics across folds
- No future data leakage

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class CrossValidationResult:
    """Container for cross-validation results and statistics."""
    
    model_name: str
    n_splits: int
    r2_mean: float
    r2_std: float
    r2_ci_lower: float
    r2_ci_upper: float
    rmse_mean: float
    rmse_std: float
    mae_mean: float
    mae_std: float
    fold_results: List[Dict[str, Any]]
    best_fold: int
    worst_fold: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'model_name': self.model_name,
            'n_splits': self.n_splits,
            'r2_mean': self.r2_mean,
            'r2_std': self.r2_std,
            'r2_ci_lower': self.r2_ci_lower,
            'r2_ci_upper': self.r2_ci_upper,
            'rmse_mean': self.rmse_mean,
            'rmse_std': self.rmse_std,
            'mae_mean': self.mae_mean,
            'mae_std': self.mae_std,
            'fold_results': self.fold_results,
            'best_fold': self.best_fold,
            'worst_fold': self.worst_fold,
            'timestamp': self.timestamp.isoformat()
        }
    
    def summary(self) -> str:
        """Generate a summary string of CV results."""
        summary = f"\n{'='*60}\n"
        summary += f"Cross-Validation Results: {self.model_name}\n"
        summary += f"{'='*60}\n"
        summary += f"Number of folds: {self.n_splits}\n"
        summary += f"\nR² Score:\n"
        summary += f"  Mean: {self.r2_mean:.4f}\n"
        summary += f"  Std:  {self.r2_std:.4f}\n"
        summary += f"  95% CI: [{self.r2_ci_lower:.4f}, {self.r2_ci_upper:.4f}]\n"
        summary += f"\nRMSE:\n"
        summary += f"  Mean: {self.rmse_mean:.4f}\n"
        summary += f"  Std:  {self.rmse_std:.4f}\n"
        summary += f"\nMAE:\n"
        summary += f"  Mean: {self.mae_mean:.4f}\n"
        summary += f"  Std:  {self.mae_std:.4f}\n"
        summary += f"\nBest fold: {self.best_fold} (R²={self.fold_results[self.best_fold]['r2']:.4f})\n"
        summary += f"Worst fold: {self.worst_fold} (R²={self.fold_results[self.worst_fold]['r2']:.4f})\n"
        summary += f"{'='*60}\n"
        return summary


def time_series_cv_split(
    n_samples: int,
    n_splits: int = 5,
    test_size: int = 29,
    gap: int = 0
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    Create time-series cross-validation splits using expanding window strategy.
    
    This ensures temporal ordering is maintained - training data always comes
    before test data, preventing future data leakage.
    
    Strategy: Expanding window
    - Split 1: Train on samples [0:train_end_1], test on [train_end_1+gap:train_end_1+gap+test_size]
    - Split 2: Train on samples [0:train_end_2], test on [train_end_2+gap:train_end_2+gap+test_size]
    - etc.
    
    Args:
        n_samples: Total number of samples in dataset
        n_splits: Number of CV folds (default 5)
        test_size: Size of each test set (default 29)
        gap: Gap between train and test sets for forecast horizon (default 0)
        
    Returns:
        List of (train_indices, test_indices) tuples
        
    Raises:
        ValueError: If dataset is too small for requested splits
    """
    logger.info(f"Creating {n_splits} time-series CV splits")
    logger.info(f"  Total samples: {n_samples}")
    logger.info(f"  Test size: {test_size}")
    logger.info(f"  Gap: {gap}")
    
    # Calculate minimum samples needed
    min_train_size = 50  # Minimum training samples
    min_samples_needed = min_train_size + gap + (n_splits * test_size)
    
    if n_samples < min_samples_needed:
        raise ValueError(
            f"Insufficient samples for {n_splits} splits. "
            f"Need at least {min_samples_needed}, got {n_samples}. "
            f"Try reducing n_splits or test_size."
        )
    
    splits = []
    
    # Calculate the size of each fold's test set end position
    # We work backwards from the end to ensure we use all data
    total_test_samples = n_splits * test_size
    available_for_training = n_samples - total_test_samples - (n_splits * gap)
    
    if available_for_training < min_train_size:
        raise ValueError(
            f"Not enough samples for training. "
            f"Available: {available_for_training}, minimum: {min_train_size}"
        )
    
    # Calculate train end positions for expanding window
    train_increment = available_for_training // n_splits
    
    for i in range(n_splits):
        # Expanding window: each fold gets more training data
        train_end = min_train_size + (i * train_increment)
        test_start = train_end + gap
        test_end = test_start + test_size
        
        # Ensure we don't exceed dataset bounds
        if test_end > n_samples:
            test_end = n_samples
            test_start = test_end - test_size
        
        train_indices = np.arange(0, train_end)
        test_indices = np.arange(test_start, test_end)
        
        splits.append((train_indices, test_indices))
        
        logger.info(
            f"  Fold {i+1}: Train[0:{train_end}] ({len(train_indices)} samples), "
            f"Test[{test_start}:{test_end}] ({len(test_indices)} samples)"
        )
    
    return splits


def calculate_confidence_intervals(
    scores: List[float],
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence intervals for CV scores using t-distribution.
    
    Uses t-distribution instead of normal distribution because sample sizes
    are typically small (n_splits = 5).
    
    Args:
        scores: List of metric scores from CV folds
        confidence: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    n = len(scores)
    mean = np.mean(scores)
    std = np.std(scores, ddof=1)  # Sample standard deviation
    
    # Use t-distribution for small sample sizes
    t_value = stats.t.ppf((1 + confidence) / 2, df=n-1)
    margin_of_error = t_value * (std / np.sqrt(n))
    
    lower = mean - margin_of_error
    upper = mean + margin_of_error
    
    return lower, upper


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate regression metrics.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        Dictionary of metrics
    """
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    
    # Handle NaN values
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) == 0:
        return {
            'r2': np.nan,
            'rmse': np.nan,
            'mae': np.nan,
            'mape': np.nan
        }
    
    r2 = r2_score(y_true_clean, y_pred_clean)
    rmse = np.sqrt(mean_squared_error(y_true_clean, y_pred_clean))
    mae = mean_absolute_error(y_true_clean, y_pred_clean)
    
    # MAPE (handle division by zero)
    mape = np.mean(np.abs((y_true_clean - y_pred_clean) / (y_true_clean + 1e-10))) * 100
    
    return {
        'r2': float(r2),
        'rmse': float(rmse),
        'mae': float(mae),
        'mape': float(mape)
    }


def cross_validate_model(
    model_class: Any,
    X: np.ndarray,
    y: np.ndarray,
    cv_splits: List[Tuple[np.ndarray, np.ndarray]],
    model_name: str = "model",
    **model_params
) -> CrossValidationResult:
    """
    Perform cross-validation and return aggregated metrics.
    
    Args:
        model_class: Model class to instantiate (must have fit/predict methods)
        X: Feature matrix
        y: Target variable
        cv_splits: List of (train_indices, test_indices) from time_series_cv_split
        model_name: Name for the model
        **model_params: Parameters to pass to model constructor
        
    Returns:
        CrossValidationResult object with aggregated metrics
    """
    logger.info(f"Starting cross-validation for {model_name}")
    logger.info(f"  Number of folds: {len(cv_splits)}")
    
    fold_results = []
    r2_scores = []
    rmse_scores = []
    mae_scores = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(cv_splits):
        logger.info(f"\n  Fold {fold_idx + 1}/{len(cv_splits)}")
        
        # Split data
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Initialize and train model
        model = model_class(**model_params)
        
        try:
            # Train model (handle different API signatures)
            if hasattr(model, 'train'):
                model.train(X_train, y_train)
            else:
                model.fit(X_train, y_train)
            
            # Predict
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            metrics = calculate_metrics(y_test, y_pred)
            
            # Store results
            fold_results.append({
                'fold': fold_idx,
                'train_size': len(train_idx),
                'test_size': len(test_idx),
                **metrics
            })
            
            r2_scores.append(metrics['r2'])
            rmse_scores.append(metrics['rmse'])
            mae_scores.append(metrics['mae'])
            
            logger.info(f"    R²: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}")
            
        except Exception as e:
            logger.error(f"    Fold {fold_idx + 1} failed: {e}")
            fold_results.append({
                'fold': fold_idx,
                'train_size': len(train_idx),
                'test_size': len(test_idx),
                'error': str(e),
                'r2': np.nan,
                'rmse': np.nan,
                'mae': np.nan,
                'mape': np.nan
            })
            r2_scores.append(np.nan)
            rmse_scores.append(np.nan)
            mae_scores.append(np.nan)
    
    # Remove NaN scores for statistics
    r2_scores_clean = [s for s in r2_scores if not np.isnan(s)]
    rmse_scores_clean = [s for s in rmse_scores if not np.isnan(s)]
    mae_scores_clean = [s for s in mae_scores if not np.isnan(s)]
    
    if len(r2_scores_clean) == 0:
        raise ValueError("All folds failed during cross-validation")
    
    # Calculate aggregated statistics
    r2_mean = np.mean(r2_scores_clean)
    r2_std = np.std(r2_scores_clean, ddof=1)
    r2_ci_lower, r2_ci_upper = calculate_confidence_intervals(r2_scores_clean)
    
    rmse_mean = np.mean(rmse_scores_clean)
    rmse_std = np.std(rmse_scores_clean, ddof=1)
    
    mae_mean = np.mean(mae_scores_clean)
    mae_std = np.std(mae_scores_clean, ddof=1)
    
    # Find best and worst folds
    best_fold = int(np.argmax(r2_scores_clean))
    worst_fold = int(np.argmin(r2_scores_clean))
    
    # Create result object
    result = CrossValidationResult(
        model_name=model_name,
        n_splits=len(cv_splits),
        r2_mean=r2_mean,
        r2_std=r2_std,
        r2_ci_lower=r2_ci_lower,
        r2_ci_upper=r2_ci_upper,
        rmse_mean=rmse_mean,
        rmse_std=rmse_std,
        mae_mean=mae_mean,
        mae_std=mae_std,
        fold_results=fold_results,
        best_fold=best_fold,
        worst_fold=worst_fold
    )
    
    logger.info(result.summary())
    
    return result


def cross_validate_sklearn_model(
    model,
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    test_size: int = 29,
    gap: int = 0,
    model_name: str = "sklearn_model"
) -> CrossValidationResult:
    """
    Convenience function for cross-validating sklearn-compatible models.
    
    Args:
        model: Sklearn-compatible model instance (with fit/predict)
        X: Feature matrix
        y: Target variable
        n_splits: Number of CV folds
        test_size: Size of each test set
        model_name: Name for the model
        
    Returns:
        CrossValidationResult object
    """
    # Create CV splits
    cv_splits = time_series_cv_split(
        n_samples=len(X),
        n_splits=n_splits,
        test_size=test_size,
        gap=gap
    )
    
    # Run CV
    fold_results = []
    r2_scores = []
    rmse_scores = []
    mae_scores = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(cv_splits):
        logger.info(f"  Fold {fold_idx + 1}/{n_splits}")
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Clone model to avoid state issues
        from sklearn.base import clone
        model_fold = clone(model)
        
        # Train and predict
        model_fold.fit(X_train, y_train)
        y_pred = model_fold.predict(X_test)
        
        # Calculate metrics
        metrics = calculate_metrics(y_test, y_pred)
        
        fold_results.append({
            'fold': fold_idx,
            'train_size': len(train_idx),
            'test_size': len(test_idx),
            **metrics
        })
        
        r2_scores.append(metrics['r2'])
        rmse_scores.append(metrics['rmse'])
        mae_scores.append(metrics['mae'])
        
        logger.info(f"    R²: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.4f}")
    
    # Calculate statistics
    r2_mean = np.mean(r2_scores)
    r2_std = np.std(r2_scores, ddof=1)
    r2_ci_lower, r2_ci_upper = calculate_confidence_intervals(r2_scores)
    
    rmse_mean = np.mean(rmse_scores)
    rmse_std = np.std(rmse_scores, ddof=1)
    
    mae_mean = np.mean(mae_scores)
    mae_std = np.std(mae_scores, ddof=1)
    
    best_fold = int(np.argmax(r2_scores))
    worst_fold = int(np.argmin(r2_scores))
    
    result = CrossValidationResult(
        model_name=model_name,
        n_splits=n_splits,
        r2_mean=r2_mean,
        r2_std=r2_std,
        r2_ci_lower=r2_ci_lower,
        r2_ci_upper=r2_ci_upper,
        rmse_mean=rmse_mean,
        rmse_std=rmse_std,
        mae_mean=mae_mean,
        mae_std=mae_std,
        fold_results=fold_results,
        best_fold=best_fold,
        worst_fold=worst_fold
    )
    
    logger.info(result.summary())
    
    return result


def compare_cv_results(results: List[CrossValidationResult]) -> pd.DataFrame:
    """
    Compare cross-validation results from multiple models.
    
    Args:
        results: List of CrossValidationResult objects
        
    Returns:
        DataFrame with comparison metrics
    """
    comparison_data = []
    
    for result in results:
        comparison_data.append({
            'Model': result.model_name,
            'R² Mean': result.r2_mean,
            'R² Std': result.r2_std,
            'R² CI Lower': result.r2_ci_lower,
            'R² CI Upper': result.r2_ci_upper,
            'RMSE Mean': result.rmse_mean,
            'RMSE Std': result.rmse_std,
            'MAE Mean': result.mae_mean,
            'MAE Std': result.mae_std,
            'N Splits': result.n_splits
        })
    
    df = pd.DataFrame(comparison_data)
    df = df.sort_values('R² Mean', ascending=False).reset_index(drop=True)
    
    return df
