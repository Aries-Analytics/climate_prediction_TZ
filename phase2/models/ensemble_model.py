"""
Ensemble Model Implementation

This module implements an ensemble model that combines predictions from
Random Forest, XGBoost, and LSTM models using weighted averaging.

Requirements: 2.4
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from models.base_model import BaseModel
from models.model_config import get_model_config

logger = logging.getLogger(__name__)


class EnsembleModel(BaseModel):
    """
    Ensemble model combining Random Forest, XGBoost, and LSTM predictions.
    
    This model loads trained base models and combines their predictions
    using weighted averaging with configurable weights.
    """
    
    def __init__(self, model_name: str = "ensemble", 
                 custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Ensemble model.
        
        Args:
            model_name: Name identifier for the model
            custom_config: Optional custom configuration overrides
        """
        # Get configuration
        config = get_model_config("ensemble", custom_config)
        
        # Initialize base class
        super().__init__(model_name, "ensemble", config)
        
        self.weights = config['weights']
        self.method = config.get('method', 'weighted_average')
        
        # Base models
        self.rf_model = None
        self.xgb_model = None
        self.lstm_model = None
        
        # Validate weights
        self._validate_weights()
    
    def _validate_weights(self) -> None:
        """Validate that weights sum to 1.0."""
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
        
        logger.info(f"Ensemble weights: RF={self.weights['rf']:.2f}, "
                   f"XGB={self.weights['xgb']:.2f}, LSTM={self.weights['lstm']:.2f}")
    
    def load_base_models(self, rf_model, xgb_model, lstm_model) -> None:
        """
        Load trained base models.
        
        Args:
            rf_model: Trained Random Forest model
            xgb_model: Trained XGBoost model
            lstm_model: Trained LSTM model
        """
        # Validate models are trained
        if not rf_model.is_trained:
            raise ValueError("Random Forest model is not trained")
        if not xgb_model.is_trained:
            raise ValueError("XGBoost model is not trained")
        if not lstm_model.is_trained:
            raise ValueError("LSTM model is not trained")
        
        self.rf_model = rf_model
        self.xgb_model = xgb_model
        self.lstm_model = lstm_model
        
        self.is_trained = True
        
        logger.info("Loaded base models:")
        logger.info(f"  - Random Forest: {rf_model.model_name}")
        logger.info(f"  - XGBoost: {xgb_model.model_name}")
        logger.info(f"  - LSTM: {lstm_model.model_name}")
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None, 
              y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Train method for ensemble (not used - base models are trained separately).
        
        This method is required by the BaseModel interface but ensemble models
        don't train directly. Instead, they combine predictions from pre-trained models.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            
        Returns:
            Dict[str, Any]: Empty dict (ensemble doesn't train)
        """
        logger.warning("Ensemble model doesn't train directly. "
                      "Train base models separately and load them using load_base_models().")
        return {}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Generate ensemble predictions using weighted averaging.
        
        Args:
            X: Input features
            
        Returns:
            np.ndarray: Ensemble predictions
        """
        self.validate_trained()
        
        if self.rf_model is None or self.xgb_model is None or self.lstm_model is None:
            raise RuntimeError("Base models not loaded. Call load_base_models() first.")
        
        # Get predictions from each model
        rf_pred = self.rf_model.predict(X)
        xgb_pred = self.xgb_model.predict(X)
        lstm_pred = self.lstm_model.predict(X)
        
        # Handle LSTM predictions (may have NaN padding at the beginning)
        # Use RF/XGB predictions for padded values
        lstm_valid_mask = ~np.isnan(lstm_pred)
        
        if self.method == 'weighted_average':
            # Initialize with zeros
            ensemble_pred = np.zeros_like(rf_pred)
            
            # For samples where LSTM has valid predictions
            valid_indices = np.where(lstm_valid_mask)[0]
            if len(valid_indices) > 0:
                ensemble_pred[valid_indices] = (
                    self.weights['rf'] * rf_pred[valid_indices] +
                    self.weights['xgb'] * xgb_pred[valid_indices] +
                    self.weights['lstm'] * lstm_pred[valid_indices]
                )
            
            # For samples where LSTM has NaN (beginning of sequence)
            invalid_indices = np.where(~lstm_valid_mask)[0]
            if len(invalid_indices) > 0:
                # Use only RF and XGB, renormalize weights
                rf_weight_norm = self.weights['rf'] / (self.weights['rf'] + self.weights['xgb'])
                xgb_weight_norm = self.weights['xgb'] / (self.weights['rf'] + self.weights['xgb'])
                
                ensemble_pred[invalid_indices] = (
                    rf_weight_norm * rf_pred[invalid_indices] +
                    xgb_weight_norm * xgb_pred[invalid_indices]
                )
                
                logger.debug(f"Used RF+XGB only for {len(invalid_indices)} samples "
                           f"(LSTM sequence padding)")
        
        else:
            raise ValueError(f"Unknown ensemble method: {self.method}")
        
        return ensemble_pred
    
    def get_individual_predictions(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Get predictions from each individual model.
        
        Args:
            X: Input features
            
        Returns:
            Dict[str, np.ndarray]: Dictionary with predictions from each model
        """
        self.validate_trained()
        
        if self.rf_model is None or self.xgb_model is None or self.lstm_model is None:
            raise RuntimeError("Base models not loaded. Call load_base_models() first.")
        
        return {
            'rf': self.rf_model.predict(X),
            'xgb': self.xgb_model.predict(X),
            'lstm': self.lstm_model.predict(X),
            'ensemble': self.predict(X)
        }
    
    def evaluate_ensemble(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Dict[str, float]]:
        """
        Evaluate ensemble and individual models.
        
        Args:
            X: Input features
            y: True targets
            
        Returns:
            Dict[str, Dict[str, float]]: Metrics for each model
        """
        predictions = self.get_individual_predictions(X)
        
        results = {}
        for model_name, y_pred in predictions.items():
            # Handle NaN values in predictions (from LSTM padding)
            valid_mask = ~np.isnan(y_pred)
            if valid_mask.sum() > 0:
                metrics = self.calculate_metrics(y[valid_mask], y_pred[valid_mask])
                results[model_name] = metrics
            else:
                results[model_name] = {'error': 'No valid predictions'}
        
        logger.info("Ensemble evaluation:")
        for model_name, metrics in results.items():
            if 'error' not in metrics:
                logger.info(f"  {model_name.upper()}: R²={metrics['r2']:.4f}, "
                          f"RMSE={metrics['rmse']:.4f}, MAE={metrics['mae']:.4f}")
        
        return results
    
    def save(self, save_dir: str) -> str:
        """
        Save ensemble configuration and metadata.
        
        Note: Base models should be saved separately.
        
        Args:
            save_dir: Directory to save the ensemble config
            
        Returns:
            str: Path to saved config
        """
        import json
        
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save ensemble configuration
        config_file = save_path / f"{self.model_name}_config.json"
        
        config_data = {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'weights': self.weights,
            'method': self.method,
            'base_models': {
                'rf': self.rf_model.model_name if self.rf_model else None,
                'xgb': self.xgb_model.model_name if self.xgb_model else None,
                'lstm': self.lstm_model.model_name if self.lstm_model else None
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logger.info(f"Saved ensemble config to {config_file}")
        
        # Save metadata
        self.save_metadata(save_dir)
        
        return str(config_file)
    
    def load(self, model_path: str) -> None:
        """
        Load ensemble configuration.
        
        Note: Base models must be loaded separately using load_base_models().
        
        Args:
            model_path: Path to the saved ensemble config
        """
        import json
        
        model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Ensemble config not found: {model_path}")
        
        # Load configuration
        with open(model_path, 'r') as f:
            config_data = json.load(f)
        
        self.weights = config_data['weights']
        self.method = config_data.get('method', 'weighted_average')
        
        logger.info(f"Loaded ensemble config from {model_path}")
        logger.info(f"Weights: {self.weights}")
        logger.info("Note: Load base models separately using load_base_models()")
        
        # Load metadata if available
        metadata_file = model_path.parent / f"{self.model_name}_metadata.json"
        if metadata_file.exists():
            self.load_metadata(str(metadata_file))
