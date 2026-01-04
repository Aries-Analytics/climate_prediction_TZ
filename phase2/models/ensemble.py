"""
Improved Ensemble Model Implementation

This module implements an enhanced ensemble method using weighted averaging
based on validation performance and prediction intervals using model disagreement.

Key improvements over simple averaging:
- Inverse RMSE weighting (better models get more weight)
- Prediction intervals from model disagreement
- Automatic weight optimization
- Ensemble validation

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class EnsembleWeights:
    """Container for ensemble model weights and metadata."""
    
    weights: Dict[str, float]
    validation_rmse: Dict[str, float]
    validation_r2: Dict[str, float]
    method: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'weights': self.weights,
            'validation_rmse': self.validation_rmse,
            'validation_r2': self.validation_r2,
            'method': self.method,
            'timestamp': self.timestamp.isoformat()
        }
    
    def summary(self) -> str:
        """Generate summary string."""
        summary = "\nEnsemble Weights:\n"
        summary += "-" * 40 + "\n"
        for name, weight in self.weights.items():
            rmse = self.validation_rmse.get(name, np.nan)
            r2 = self.validation_r2.get(name, np.nan)
            summary += f"  {name:15s}: {weight:.4f} (RMSE={rmse:.4f}, R²={r2:.4f})\n"
        summary += "-" * 40 + "\n"
        summary += f"Method: {self.method}\n"
        return summary


class WeightedEnsemble:
    """
    Ensemble model using inverse RMSE weighting.
    
    This ensemble combines predictions from multiple models using weights
    based on their validation performance. Better-performing models
    (lower RMSE) receive higher weights.
    """
    
    def __init__(self, models: List[Any], names: List[str], ensemble_name: str = "weighted_ensemble"):
        """
        Initialize weighted ensemble.
        
        Args:
            models: List of trained model objects (must have predict method)
            names: List of model names (same order as models)
            ensemble_name: Name for this ensemble
            
        Raises:
            ValueError: If models and names have different lengths
        """
        if len(models) != len(names):
            raise ValueError(f"Number of models ({len(models)}) must match number of names ({len(names)})")
        
        if len(models) == 0:
            raise ValueError("At least one model is required")
        
        self.models = models
        self.names = names
        self.ensemble_name = ensemble_name
        self.weights = None
        self.ensemble_weights_obj = None
        self.is_fitted = False
        
        logger.info(f"Initialized {ensemble_name} with {len(models)} models: {names}")
    
    def fit_weights(
        self,
        X_val: np.ndarray,
        y_val: np.ndarray,
        method: str = 'inverse_rmse'
    ) -> EnsembleWeights:
        """
        Calculate ensemble weights based on validation performance.
        
        Args:
            X_val: Validation features
            y_val: Validation targets
            method: Weighting method ('inverse_rmse', 'inverse_mse', 'softmax_rmse')
            
        Returns:
            EnsembleWeights object with calculated weights
            
        Raises:
            ValueError: If method is unknown or all models fail
        """
        logger.info(f"Calculating ensemble weights using method: {method}")
        logger.info(f"Validation set size: {len(X_val)}")
        
        from sklearn.metrics import mean_squared_error, r2_score
        
        # Calculate validation metrics for each model
        rmses = {}
        r2_scores = {}
        predictions = {}
        
        for model, name in zip(self.models, self.names):
            try:
                # Get predictions
                y_pred = model.predict(X_val)
                
                # Handle NaN predictions (e.g., from LSTM padding)
                valid_mask = ~np.isnan(y_pred)
                if valid_mask.sum() == 0:
                    logger.warning(f"Model {name} produced no valid predictions")
                    rmses[name] = np.inf
                    r2_scores[name] = -np.inf
                    continue
                
                y_val_clean = y_val[valid_mask]
                y_pred_clean = y_pred[valid_mask]
                
                # Calculate metrics
                rmse = np.sqrt(mean_squared_error(y_val_clean, y_pred_clean))
                r2 = r2_score(y_val_clean, y_pred_clean)
                
                rmses[name] = rmse
                r2_scores[name] = r2
                predictions[name] = y_pred
                
                logger.info(f"  {name}: RMSE={rmse:.4f}, R²={r2:.4f}")
                
            except Exception as e:
                logger.error(f"  {name}: Failed to evaluate - {e}")
                rmses[name] = np.inf
                r2_scores[name] = -np.inf
        
        # Check if we have any valid models
        valid_models = [name for name, rmse in rmses.items() if rmse < np.inf]
        if len(valid_models) == 0:
            raise ValueError("All models failed validation")
        
        # Calculate weights based on method
        if method == 'inverse_rmse':
            # Inverse RMSE weighting: w_i = (1/RMSE_i) / sum(1/RMSE_j)
            inv_rmses = np.array([1.0 / rmses[name] for name in valid_models])
            weights_array = inv_rmses / inv_rmses.sum()
            weights = dict(zip(valid_models, weights_array))
            
        elif method == 'inverse_mse':
            # Inverse MSE weighting: w_i = (1/MSE_i) / sum(1/MSE_j)
            inv_mses = np.array([1.0 / (rmses[name]**2) for name in valid_models])
            weights_array = inv_mses / inv_mses.sum()
            weights = dict(zip(valid_models, weights_array))
            
        elif method == 'softmax_rmse':
            # Softmax of negative RMSE: w_i = exp(-RMSE_i) / sum(exp(-RMSE_j))
            neg_rmses = np.array([-rmses[name] for name in valid_models])
            # Normalize to prevent overflow
            neg_rmses = neg_rmses - neg_rmses.max()
            exp_neg_rmses = np.exp(neg_rmses)
            weights_array = exp_neg_rmses / exp_neg_rmses.sum()
            weights = dict(zip(valid_models, weights_array))
            
        elif method == 'equal':
            # Equal weighting
            weight_value = 1.0 / len(valid_models)
            weights = {name: weight_value for name in valid_models}
            
        else:
            raise ValueError(f"Unknown weighting method: {method}")
        
        # Add zero weights for failed models
        for name in self.names:
            if name not in weights:
                weights[name] = 0.0
        
        # Store weights
        self.weights = weights
        self.is_fitted = True
        
        # Create weights object
        self.ensemble_weights_obj = EnsembleWeights(
            weights=weights,
            validation_rmse=rmses,
            validation_r2=r2_scores,
            method=method
        )
        
        logger.info(self.ensemble_weights_obj.summary())
        
        # Verify weights sum to 1.0
        total_weight = sum(weights.values())
        if not np.isclose(total_weight, 1.0, atol=1e-6):
            logger.warning(f"Weights sum to {total_weight:.6f}, not 1.0")
        
        return self.ensemble_weights_obj
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Generate weighted average predictions.
        
        Args:
            X: Input features
            
        Returns:
            Weighted average predictions
            
        Raises:
            ValueError: If weights haven't been fitted
        """
        if not self.is_fitted:
            raise ValueError("Weights must be fitted before prediction. Call fit_weights() first.")
        
        logger.debug(f"Generating ensemble predictions for {len(X)} samples")
        
        # Collect predictions from all models
        all_predictions = []
        active_weights = []
        
        for model, name in zip(self.models, self.names):
            weight = self.weights[name]
            
            if weight > 0:
                try:
                    pred = model.predict(X)
                    all_predictions.append(pred)
                    active_weights.append(weight)
                except Exception as e:
                    logger.error(f"Model {name} prediction failed: {e}")
        
        if len(all_predictions) == 0:
            raise ValueError("No models produced valid predictions")
        
        # Stack predictions
        predictions_array = np.array(all_predictions)  # Shape: (n_models, n_samples)
        weights_array = np.array(active_weights)
        
        # Normalize weights (in case some models failed)
        weights_array = weights_array / weights_array.sum()
        
        # Weighted average
        ensemble_pred = np.average(predictions_array, axis=0, weights=weights_array)
        
        return ensemble_pred
    
    def predict_with_intervals(
        self,
        X: np.ndarray,
        confidence: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate predictions with uncertainty intervals based on model disagreement.
        
        The uncertainty is estimated from the standard deviation of individual
        model predictions, weighted by their ensemble weights.
        
        Args:
            X: Input features
            confidence: Confidence level for intervals (default 0.95)
            
        Returns:
            Tuple of (mean_predictions, lower_bounds, upper_bounds)
            
        Raises:
            ValueError: If weights haven't been fitted
        """
        if not self.is_fitted:
            raise ValueError("Weights must be fitted before prediction. Call fit_weights() first.")
        
        logger.debug(f"Generating ensemble predictions with {confidence*100}% intervals")
        
        # Collect predictions from all models
        all_predictions = []
        active_weights = []
        
        for model, name in zip(self.models, self.names):
            weight = self.weights[name]
            
            if weight > 0:
                try:
                    pred = model.predict(X)
                    all_predictions.append(pred)
                    active_weights.append(weight)
                except Exception as e:
                    logger.error(f"Model {name} prediction failed: {e}")
        
        if len(all_predictions) == 0:
            raise ValueError("No models produced valid predictions")
        
        # Stack predictions
        predictions_array = np.array(all_predictions)  # Shape: (n_models, n_samples)
        weights_array = np.array(active_weights)
        
        # Normalize weights
        weights_array = weights_array / weights_array.sum()
        
        # Weighted mean
        mean_pred = np.average(predictions_array, axis=0, weights=weights_array)
        
        # Weighted standard deviation (model disagreement)
        # std = sqrt(sum(w_i * (x_i - mean)^2))
        variance = np.average((predictions_array - mean_pred)**2, axis=0, weights=weights_array)
        std_pred = np.sqrt(variance)
        
        # Calculate confidence intervals
        # Using normal approximation: mean ± z * std
        from scipy import stats
        z_score = stats.norm.ppf((1 + confidence) / 2)
        
        lower = mean_pred - z_score * std_pred
        upper = mean_pred + z_score * std_pred
        
        logger.debug(f"Mean uncertainty (std): {np.mean(std_pred):.4f}")
        logger.debug(f"Mean interval width: {np.mean(upper - lower):.4f}")
        
        return mean_pred, lower, upper
    
    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, Any]:
        """
        Evaluate ensemble performance on test data.
        
        Args:
            X_test: Test features
            y_test: Test targets
            
        Returns:
            Dictionary with ensemble and individual model metrics
        """
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        
        logger.info("Evaluating ensemble on test data")
        
        results = {
            'individual_models': {},
            'ensemble': {}
        }
        
        # Evaluate individual models
        for model, name in zip(self.models, self.names):
            try:
                y_pred = model.predict(X_test)
                
                # Handle NaN predictions
                valid_mask = ~np.isnan(y_pred)
                if valid_mask.sum() == 0:
                    logger.warning(f"Model {name} produced no valid predictions")
                    continue
                
                y_test_clean = y_test[valid_mask]
                y_pred_clean = y_pred[valid_mask]
                
                metrics = {
                    'r2': float(r2_score(y_test_clean, y_pred_clean)),
                    'rmse': float(np.sqrt(mean_squared_error(y_test_clean, y_pred_clean))),
                    'mae': float(mean_absolute_error(y_test_clean, y_pred_clean)),
                    'weight': self.weights[name]
                }
                
                results['individual_models'][name] = metrics
                logger.info(f"  {name}: R²={metrics['r2']:.4f}, RMSE={metrics['rmse']:.4f}, Weight={metrics['weight']:.4f}")
                
            except Exception as e:
                logger.error(f"  {name}: Evaluation failed - {e}")
        
        # Evaluate ensemble
        try:
            y_pred_ensemble = self.predict(X_test)
            
            # Handle NaN predictions
            valid_mask = ~np.isnan(y_pred_ensemble)
            y_test_clean = y_test[valid_mask]
            y_pred_clean = y_pred_ensemble[valid_mask]
            
            ensemble_metrics = {
                'r2': float(r2_score(y_test_clean, y_pred_clean)),
                'rmse': float(np.sqrt(mean_squared_error(y_test_clean, y_pred_clean))),
                'mae': float(mean_absolute_error(y_test_clean, y_pred_clean))
            }
            
            results['ensemble'] = ensemble_metrics
            logger.info(f"  Ensemble: R²={ensemble_metrics['r2']:.4f}, RMSE={ensemble_metrics['rmse']:.4f}")
            
            # Check if ensemble outperforms individual models
            individual_r2s = [m['r2'] for m in results['individual_models'].values()]
            if individual_r2s:
                best_individual_r2 = max(individual_r2s)
                if ensemble_metrics['r2'] >= best_individual_r2:
                    logger.info(f"  ✓ Ensemble outperforms best individual model (R²: {ensemble_metrics['r2']:.4f} >= {best_individual_r2:.4f})")
                else:
                    logger.warning(f"  ✗ Ensemble underperforms best individual model (R²: {ensemble_metrics['r2']:.4f} < {best_individual_r2:.4f})")
            
        except Exception as e:
            logger.error(f"  Ensemble evaluation failed: {e}")
            results['ensemble'] = {'error': str(e)}
        
        return results
    
    def save(self, save_dir: str) -> str:
        """
        Save ensemble configuration and weights.
        
        Args:
            save_dir: Directory to save configuration
            
        Returns:
            Path to saved configuration file
        """
        if not self.is_fitted:
            raise ValueError("Ensemble must be fitted before saving")
        
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        config = {
            'ensemble_name': self.ensemble_name,
            'model_names': self.names,
            'weights': self.ensemble_weights_obj.to_dict(),
            'n_models': len(self.models)
        }
        
        config_file = save_path / f"{self.ensemble_name}_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved ensemble configuration to {config_file}")
        
        return str(config_file)
    
    def load(self, config_path: str) -> None:
        """
        Load ensemble configuration and weights.
        
        Note: This only loads the configuration. Models must be loaded separately
        and passed to the constructor.
        
        Args:
            config_path: Path to configuration file
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.ensemble_name = config['ensemble_name']
        
        # Load weights
        weights_data = config['weights']
        self.weights = weights_data['weights']
        self.is_fitted = True
        
        # Recreate weights object
        self.ensemble_weights_obj = EnsembleWeights(
            weights=weights_data['weights'],
            validation_rmse=weights_data['validation_rmse'],
            validation_r2=weights_data['validation_r2'],
            method=weights_data['method'],
            timestamp=datetime.fromisoformat(weights_data['timestamp'])
        )
        
        logger.info(f"Loaded ensemble configuration from {config_path}")
        logger.info(self.ensemble_weights_obj.summary())


def create_ensemble_from_models(
    models: Dict[str, Any],
    X_val: np.ndarray,
    y_val: np.ndarray,
    method: str = 'inverse_rmse',
    ensemble_name: str = 'weighted_ensemble'
) -> WeightedEnsemble:
    """
    Convenience function to create and fit an ensemble from a dictionary of models.
    
    Args:
        models: Dictionary of {name: model} pairs
        X_val: Validation features for weight fitting
        y_val: Validation targets for weight fitting
        method: Weighting method
        ensemble_name: Name for the ensemble
        
    Returns:
        Fitted WeightedEnsemble object
    """
    model_list = list(models.values())
    name_list = list(models.keys())
    
    ensemble = WeightedEnsemble(model_list, name_list, ensemble_name)
    ensemble.fit_weights(X_val, y_val, method=method)
    
    return ensemble
