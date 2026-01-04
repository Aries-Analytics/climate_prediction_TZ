"""
Baseline Models for Climate Prediction

This module provides simple baseline models to benchmark against complex ML models.
Baselines help demonstrate the value added by sophisticated approaches.

Baseline models included:
1. Persistence Baseline - Last value carried forward
2. Climatology Baseline - Historical monthly averages
3. Linear Regression Baseline - Simple linear model with top features

These baselines typically achieve:
- Persistence: R² = 0.3-0.5
- Climatology: R² = 0.4-0.6
- Linear: R² = 0.6-0.75

Complex models should exceed R² = 0.80 to demonstrate value.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import logging

logger = logging.getLogger(__name__)


class PersistenceBaseline:
    """
    Persistence baseline model - predicts last observed value.
    
    This is the simplest baseline: "tomorrow will be like today".
    Effective for slowly-changing variables with high autocorrelation.
    """
    
    def __init__(self):
        self.name = "Persistence"
        self.last_values = None
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        Store last values from training data.
        
        Args:
            X: Feature matrix (not used, but kept for API consistency)
            y: Target values
        """
        self.last_values = y[-1] if len(y) > 0 else 0.0
        logger.info(f"Persistence baseline fitted with last value: {self.last_values:.4f}")
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using last observed value.
        
        Args:
            X: Feature matrix (shape determines prediction length)
            
        Returns:
            Array of predictions (all equal to last value)
        """
        n_samples = X.shape[0] if len(X.shape) > 1 else len(X)
        predictions = np.full(n_samples, self.last_values)
        return predictions
    
    def get_params(self) -> Dict[str, Any]:
        """Return model parameters."""
        return {
            'model': 'Persistence',
            'last_value': float(self.last_values) if self.last_values is not None else None
        }


class ClimatologyBaseline:
    """
    Climatology baseline model - predicts historical monthly averages.
    
    Uses long-term monthly means: "January is typically like this".
    Accounts for seasonal patterns but not year-to-year variations.
    """
    
    def __init__(self):
        self.name = "Climatology"
        self.monthly_means = {}
        self.overall_mean = None
    
    def fit(self, X: np.ndarray, y: np.ndarray, months: np.ndarray):
        """
        Calculate historical monthly averages.
        
        Args:
            X: Feature matrix (not used, but kept for API consistency)
            y: Target values
            months: Month numbers (1-12) for each sample
        """
        if len(y) != len(months):
            raise ValueError("Length of y and months must match")
        
        # Calculate mean for each month
        for month in range(1, 13):
            mask = months == month
            if np.any(mask):
                self.monthly_means[month] = np.mean(y[mask])
            else:
                # If no data for this month, use overall mean
                self.monthly_means[month] = np.mean(y)
        
        self.overall_mean = np.mean(y)
        
        logger.info(f"Climatology baseline fitted with {len(self.monthly_means)} monthly means")
        logger.info(f"Overall mean: {self.overall_mean:.4f}")
        
        return self
    
    def predict(self, X: np.ndarray, months: np.ndarray) -> np.ndarray:
        """
        Predict using monthly climatology.
        
        Args:
            X: Feature matrix (not used, but kept for API consistency)
            months: Month numbers (1-12) for predictions
            
        Returns:
            Array of predictions based on monthly means
        """
        if self.monthly_means is None or len(self.monthly_means) == 0:
            raise ValueError("Model must be fitted before prediction")
        
        predictions = np.array([
            self.monthly_means.get(month, self.overall_mean)
            for month in months
        ])
        
        return predictions
    
    def get_params(self) -> Dict[str, Any]:
        """Return model parameters."""
        return {
            'model': 'Climatology',
            'monthly_means': {int(k): float(v) for k, v in self.monthly_means.items()},
            'overall_mean': float(self.overall_mean) if self.overall_mean is not None else None
        }


class LinearRegressionBaseline:
    """
    Linear regression baseline with top features.
    
    Uses simple linear model with limited features selected by correlation.
    Represents a basic statistical approach without complex interactions.
    """
    
    def __init__(self, n_features: int = 20, alpha: float = 1.0):
        """
        Initialize linear regression baseline.
        
        Args:
            n_features: Number of top features to use (default 20)
            alpha: Regularization strength for Ridge regression (default 1.0)
        """
        self.name = "Linear Regression"
        self.n_features = n_features
        self.alpha = alpha
        self.model = Ridge(alpha=alpha, random_state=42)
        self.selected_features = None
        self.feature_names = None
    
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[list] = None):
        """
        Fit linear model with top correlated features.
        
        Args:
            X: Feature matrix
            y: Target values
            feature_names: Optional list of feature names
        """
        self.feature_names = feature_names
        
        # Select top features by correlation with target
        correlations = []
        for i in range(X.shape[1]):
            corr = np.corrcoef(X[:, i], y)[0, 1]
            correlations.append(abs(corr) if not np.isnan(corr) else 0.0)
        
        # Get indices of top features
        top_indices = np.argsort(correlations)[-self.n_features:]
        self.selected_features = top_indices
        
        # Fit model on selected features
        X_selected = X[:, top_indices]
        self.model.fit(X_selected, y)
        
        logger.info(f"Linear baseline fitted with {self.n_features} features")
        if feature_names:
            selected_names = [feature_names[i] for i in top_indices]
            logger.info(f"Top features: {selected_names[:5]}...")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using linear model.
        
        Args:
            X: Feature matrix
            
        Returns:
            Array of predictions
        """
        if self.selected_features is None:
            raise ValueError("Model must be fitted before prediction")
        
        X_selected = X[:, self.selected_features]
        predictions = self.model.predict(X_selected)
        
        return predictions
    
    def get_params(self) -> Dict[str, Any]:
        """Return model parameters."""
        params = {
            'model': 'Linear Regression',
            'n_features': self.n_features,
            'alpha': self.alpha,
            'selected_feature_indices': self.selected_features.tolist() if self.selected_features is not None else None
        }
        
        if self.feature_names and self.selected_features is not None:
            params['selected_feature_names'] = [
                self.feature_names[i] for i in self.selected_features
            ]
        
        return params


def evaluate_baseline(
    model,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    months_train: Optional[np.ndarray] = None,
    months_test: Optional[np.ndarray] = None,
    feature_names: Optional[list] = None
) -> Dict[str, float]:
    """
    Evaluate a baseline model and return metrics.
    
    Args:
        model: Baseline model instance
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        months_train: Month numbers for training (for Climatology)
        months_test: Month numbers for testing (for Climatology)
        feature_names: Feature names (for Linear)
        
    Returns:
        Dictionary with R², RMSE, MAE metrics
    """
    # Fit model
    if isinstance(model, ClimatologyBaseline):
        if months_train is None:
            raise ValueError("Climatology baseline requires month information")
        model.fit(X_train, y_train, months_train)
    elif isinstance(model, LinearRegressionBaseline):
        model.fit(X_train, y_train, feature_names)
    else:
        model.fit(X_train, y_train)
    
    # Make predictions
    if isinstance(model, ClimatologyBaseline):
        if months_test is None:
            raise ValueError("Climatology baseline requires month information for prediction")
        y_pred = model.predict(X_test, months_test)
    else:
        y_pred = model.predict(X_test)
    
    # Calculate metrics
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    
    # Calculate MAPE (handle division by zero)
    mape = np.mean(np.abs((y_test - y_pred) / np.where(y_test != 0, y_test, 1))) * 100
    
    metrics = {
        'model': model.name,
        'r2': float(r2),
        'rmse': float(rmse),
        'mae': float(mae),
        'mape': float(mape)
    }
    
    logger.info(f"{model.name} - R²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}")
    
    return metrics


def compare_baselines(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    months_train: Optional[np.ndarray] = None,
    months_test: Optional[np.ndarray] = None,
    feature_names: Optional[list] = None
) -> Dict[str, Dict[str, float]]:
    """
    Compare all baseline models.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        months_train: Month numbers for training
        months_test: Month numbers for testing
        feature_names: Feature names
        
    Returns:
        Dictionary mapping model names to their metrics
    """
    logger.info("=" * 60)
    logger.info("Evaluating baseline models")
    logger.info("=" * 60)
    
    results = {}
    
    # Persistence baseline
    persistence = PersistenceBaseline()
    results['persistence'] = evaluate_baseline(
        persistence, X_train, y_train, X_test, y_test
    )
    
    # Climatology baseline
    if months_train is not None and months_test is not None:
        climatology = ClimatologyBaseline()
        results['climatology'] = evaluate_baseline(
            climatology, X_train, y_train, X_test, y_test,
            months_train, months_test
        )
    else:
        logger.warning("Skipping Climatology baseline - no month information provided")
    
    # Linear regression baseline
    linear = LinearRegressionBaseline(n_features=20)
    results['linear'] = evaluate_baseline(
        linear, X_train, y_train, X_test, y_test,
        feature_names=feature_names
    )
    
    logger.info("=" * 60)
    logger.info("Baseline comparison complete")
    logger.info("=" * 60)
    
    return results


def calculate_improvement(
    model_r2: float,
    baseline_r2: float
) -> float:
    """
    Calculate percentage improvement over baseline.
    
    Uses formula: (model_r2 - baseline_r2) / (1 - baseline_r2) * 100
    This represents how much of the remaining unexplained variance is captured.
    
    Args:
        model_r2: R² score of complex model
        baseline_r2: R² score of baseline model
        
    Returns:
        Percentage improvement
    """
    if baseline_r2 >= 1.0:
        return 0.0
    
    improvement = (model_r2 - baseline_r2) / (1 - baseline_r2) * 100
    return improvement


def generate_baseline_report(
    baseline_results: Dict[str, Dict[str, float]],
    model_results: Dict[str, float]
) -> str:
    """
    Generate a formatted report comparing baselines to complex model.
    
    Args:
        baseline_results: Dictionary of baseline model results
        model_results: Results from complex model
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 70)
    report.append("BASELINE MODEL COMPARISON REPORT")
    report.append("=" * 70)
    report.append("")
    
    # Table header
    report.append(f"{'Model':<20} {'R²':>10} {'RMSE':>10} {'MAE':>10} {'MAPE':>10}")
    report.append("-" * 70)
    
    # Baseline results
    for model_name, metrics in baseline_results.items():
        report.append(
            f"{metrics['model']:<20} "
            f"{metrics['r2']:>10.4f} "
            f"{metrics['rmse']:>10.4f} "
            f"{metrics['mae']:>10.4f} "
            f"{metrics['mape']:>10.2f}%"
        )
    
    # Complex model results
    if model_results:
        report.append("-" * 70)
        report.append(
            f"{'Complex Model':<20} "
            f"{model_results.get('r2', 0):>10.4f} "
            f"{model_results.get('rmse', 0):>10.4f} "
            f"{model_results.get('mae', 0):>10.4f} "
            f"{model_results.get('mape', 0):>10.2f}%"
        )
    
    report.append("=" * 70)
    report.append("")
    
    # Improvement analysis
    if model_results:
        report.append("IMPROVEMENT OVER BASELINES")
        report.append("-" * 70)
        
        model_r2 = model_results.get('r2', 0)
        for model_name, metrics in baseline_results.items():
            improvement = calculate_improvement(model_r2, metrics['r2'])
            report.append(
                f"vs {metrics['model']:<18}: "
                f"{improvement:>6.1f}% improvement "
                f"(Δ R² = {model_r2 - metrics['r2']:>6.4f})"
            )
        
        report.append("=" * 70)
    
    return "\n".join(report)
