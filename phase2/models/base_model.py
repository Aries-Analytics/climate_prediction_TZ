"""
Base Model Abstract Class

This module defines the abstract base class for all ML models in the system.
It provides a common interface and shared utilities for model training, prediction,
saving, and loading.

Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3, 6.4
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd
import joblib
import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """
    Abstract base class for all ML models.
    
    This class defines the interface that all models must implement and provides
    common utilities for model management.
    
    Attributes:
        model_name: Name of the model
        model_type: Type of model (e.g., 'random_forest', 'xgboost', 'lstm')
        config: Model configuration dictionary
        model: The underlying model object
        is_trained: Whether the model has been trained
        metadata: Dictionary containing model metadata
    """
    
    def __init__(self, model_name: str, model_type: str, config: Dict[str, Any]):
        """
        Initialize the base model.
        
        Args:
            model_name: Name identifier for the model
            model_type: Type of model
            config: Configuration dictionary with hyperparameters
        """
        self.model_name = model_name
        self.model_type = model_type
        self.config = config
        self.model = None
        self.is_trained = False
        self.metadata = {
            'model_name': model_name,
            'model_type': model_type,
            'created_at': datetime.now().isoformat(),
            'trained_at': None,
            'training_time_seconds': None,
            'config': config,
            'metrics': {},
            'feature_names': None,
            'n_features': None
        }
        
        logger.info(f"Initialized {model_type} model: {model_name}")
    
    @abstractmethod
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None, 
              y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Train the model on the provided data.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            
        Returns:
            Dict[str, Any]: Training metrics and information
        """
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Generate predictions for the input data.
        
        Args:
            X: Input features
            
        Returns:
            np.ndarray: Predictions
        """
        pass
    
    @abstractmethod
    def save(self, save_dir: str) -> str:
        """
        Save the trained model to disk.
        
        Args:
            save_dir: Directory to save the model
            
        Returns:
            str: Path to the saved model
        """
        pass
    
    @abstractmethod
    def load(self, model_path: str) -> None:
        """
        Load a trained model from disk.
        
        Args:
            model_path: Path to the saved model
        """
        pass
    
    # Common utility methods
    
    def validate_trained(self) -> None:
        """
        Validate that the model has been trained.
        
        Raises:
            RuntimeError: If model has not been trained
        """
        if not self.is_trained:
            raise RuntimeError(f"Model {self.model_name} has not been trained yet. "
                             "Call train() before making predictions.")
    
    def validate_input_shape(self, X: np.ndarray, expected_features: Optional[int] = None) -> None:
        """
        Validate input data shape.
        
        Args:
            X: Input data
            expected_features: Expected number of features (optional)
            
        Raises:
            ValueError: If input shape is invalid
        """
        if len(X.shape) != 2:
            raise ValueError(f"Expected 2D array, got shape {X.shape}")
        
        if expected_features is not None and X.shape[1] != expected_features:
            raise ValueError(f"Expected {expected_features} features, got {X.shape[1]}")
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """
        Update model metadata.
        
        Args:
            updates: Dictionary of metadata updates
        """
        self.metadata.update(updates)
        logger.debug(f"Updated metadata for {self.model_name}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get model metadata.
        
        Returns:
            Dict[str, Any]: Model metadata
        """
        return self.metadata.copy()
    
    def save_metadata(self, save_dir: str) -> str:
        """
        Save model metadata to JSON file.
        
        Args:
            save_dir: Directory to save metadata
            
        Returns:
            str: Path to saved metadata file
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        metadata_file = save_path / f"{self.model_name}_metadata.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
        
        logger.info(f"Saved metadata to {metadata_file}")
        return str(metadata_file)
    
    def load_metadata(self, metadata_path: str) -> None:
        """
        Load model metadata from JSON file.
        
        Args:
            metadata_path: Path to metadata file
        """
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        logger.info(f"Loaded metadata from {metadata_path}")
    
    def set_feature_names(self, feature_names: list) -> None:
        """
        Set feature names for the model.
        
        Args:
            feature_names: List of feature names
        """
        self.metadata['feature_names'] = feature_names
        self.metadata['n_features'] = len(feature_names)
        logger.debug(f"Set {len(feature_names)} feature names")
    
    def get_feature_names(self) -> Optional[list]:
        """
        Get feature names.
        
        Returns:
            Optional[list]: List of feature names or None
        """
        return self.metadata.get('feature_names')
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calculate common regression metrics.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dict[str, float]: Dictionary of metrics
        """
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        metrics = {
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'r2': float(r2_score(y_true, y_pred))
        }
        
        # Calculate MAPE (avoiding division by zero)
        mask = y_true != 0
        if mask.any():
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            metrics['mape'] = float(mape)
        else:
            metrics['mape'] = None
        
        return metrics
    
    def log_training_start(self, X_train_shape: Tuple, y_train_shape: Tuple) -> None:
        """
        Log training start information.
        
        Args:
            X_train_shape: Shape of training features
            y_train_shape: Shape of training targets
        """
        logger.info(f"Starting training for {self.model_name}")
        logger.info(f"Training data shape: X={X_train_shape}, y={y_train_shape}")
        logger.info(f"Model config: {self.config}")
    
    def log_training_complete(self, training_time: float, metrics: Dict[str, float]) -> None:
        """
        Log training completion information.
        
        Args:
            training_time: Training time in seconds
            metrics: Training metrics
        """
        logger.info(f"Training completed for {self.model_name}")
        logger.info(f"Training time: {training_time:.2f} seconds")
        logger.info(f"Training metrics: {metrics}")
        
        # Update metadata
        self.metadata['trained_at'] = datetime.now().isoformat()
        self.metadata['training_time_seconds'] = training_time
        self.metadata['metrics'] = metrics
    
    def __repr__(self) -> str:
        """String representation of the model."""
        status = "trained" if self.is_trained else "untrained"
        return f"{self.__class__.__name__}(name='{self.model_name}', type='{self.model_type}', status='{status}')"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.model_type.upper()} Model: {self.model_name} ({'trained' if self.is_trained else 'untrained'})"


class SklearnBaseModel(BaseModel):
    """
    Base class for scikit-learn based models.
    
    Provides common save/load functionality for sklearn models using joblib.
    """
    
    def save(self, save_dir: str) -> str:
        """
        Save sklearn model using joblib.
        
        Args:
            save_dir: Directory to save the model
            
        Returns:
            str: Path to the saved model
        """
        self.validate_trained()
        
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_file = save_path / f"{self.model_name}.pkl"
        joblib.dump(self.model, model_file)
        logger.info(f"Saved model to {model_file}")
        
        # Save metadata
        self.save_metadata(save_dir)
        
        return str(model_file)
    
    def load(self, model_path: str) -> None:
        """
        Load sklearn model using joblib.
        
        Args:
            model_path: Path to the saved model
        """
        model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load model
        self.model = joblib.load(model_path)
        self.is_trained = True
        logger.info(f"Loaded model from {model_path}")
        
        # Load metadata if available
        metadata_file = model_path.parent / f"{self.model_name}_metadata.json"
        if metadata_file.exists():
            self.load_metadata(str(metadata_file))
