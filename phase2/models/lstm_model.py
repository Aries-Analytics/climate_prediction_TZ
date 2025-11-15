"""
LSTM Model Implementation

This module implements an LSTM neural network model for time series climate prediction.

Requirements: 2.3
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
import time
import logging
from pathlib import Path

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("TensorFlow not installed. Install with: pip install tensorflow")

from models.base_model import BaseModel
from models.model_config import get_model_config

logger = logging.getLogger(__name__)


class LSTMModel(BaseModel):
    """
    LSTM neural network model for time series climate prediction.
    
    This model uses TensorFlow/Keras LSTM layers with configurable architecture,
    sequence preparation, and early stopping.
    """
    
    def __init__(self, model_name: str = "lstm", 
                 custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize LSTM model.
        
        Args:
            model_name: Name identifier for the model
            custom_config: Optional custom configuration overrides
            
        Raises:
            ImportError: If TensorFlow is not installed
        """
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is not installed. Install with: pip install tensorflow")
        
        # Get configuration
        config = get_model_config("lstm", custom_config)
        
        # Initialize base class
        super().__init__(model_name, "lstm", config)
        
        self.sequence_length = config['sequence_length']
        self.model = None
        self.history = None
    
    def _build_model(self, n_features: int) -> None:
        """
        Build the LSTM model architecture.
        
        Args:
            n_features: Number of input features
        """
        model = Sequential(name=self.model_name)
        
        units = self.config['units']
        dropout = self.config['dropout']
        recurrent_dropout = self.config['recurrent_dropout']
        
        # Add LSTM layers
        for i, n_units in enumerate(units):
            return_sequences = (i < len(units) - 1)  # Return sequences for all but last layer
            
            model.add(LSTM(
                units=n_units,
                activation=self.config['activation'],
                recurrent_activation=self.config['recurrent_activation'],
                dropout=dropout,
                recurrent_dropout=recurrent_dropout,
                return_sequences=return_sequences,
                input_shape=(self.sequence_length, n_features) if i == 0 else None,
                name=f'lstm_{i+1}'
            ))
        
        # Output layer
        model.add(Dense(1, name='output'))
        
        # Compile model
        optimizer = keras.optimizers.Adam(learning_rate=self.config['learning_rate'])
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        self.model = model
        
        logger.info(f"Built LSTM model with architecture:")
        logger.info(f"  Sequence length: {self.sequence_length}")
        logger.info(f"  LSTM units: {units}")
        logger.info(f"  Dropout: {dropout}")
        logger.info(f"  Total parameters: {model.count_params():,}")
    
    def prepare_sequences(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> Tuple:
        """
        Prepare sequences for LSTM input.
        
        Args:
            X: Input features (samples, features)
            y: Target values (optional)
            
        Returns:
            Tuple: (X_sequences, y_sequences) or just X_sequences if y is None
        """
        n_samples = len(X)
        n_features = X.shape[1]
        
        # Calculate number of sequences
        n_sequences = n_samples - self.sequence_length + 1
        
        if n_sequences <= 0:
            raise ValueError(f"Not enough samples ({n_samples}) for sequence length {self.sequence_length}")
        
        # Create sequences
        X_sequences = np.zeros((n_sequences, self.sequence_length, n_features))
        
        for i in range(n_sequences):
            X_sequences[i] = X[i:i + self.sequence_length]
        
        if y is not None:
            # Target is the value at the end of each sequence
            y_sequences = y[self.sequence_length - 1:]
            return X_sequences, y_sequences
        
        return X_sequences
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None, 
              y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Train the LSTM model with early stopping.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional)
            y_val: Validation targets (optional)
            
        Returns:
            Dict[str, Any]: Training metrics and information
        """
        self.log_training_start(X_train.shape, y_train.shape)
        
        # Validate input
        self.validate_input_shape(X_train)
        
        # Prepare sequences
        logger.info("Preparing sequences for LSTM...")
        X_train_seq, y_train_seq = self.prepare_sequences(X_train, y_train)
        logger.info(f"Training sequences shape: {X_train_seq.shape}")
        
        validation_data = None
        if X_val is not None and y_val is not None:
            X_val_seq, y_val_seq = self.prepare_sequences(X_val, y_val)
            validation_data = (X_val_seq, y_val_seq)
            logger.info(f"Validation sequences shape: {X_val_seq.shape}")
        
        # Build model if not already built
        if self.model is None:
            self._build_model(X_train.shape[1])
        
        # Prepare callbacks
        callbacks = []
        
        # Early stopping
        if self.config.get('patience'):
            early_stop = EarlyStopping(
                monitor='val_loss' if validation_data else 'loss',
                patience=self.config['patience'],
                restore_best_weights=True,
                verbose=1
            )
            callbacks.append(early_stop)
        
        # Start training
        start_time = time.time()
        
        # Fit the model
        self.history = self.model.fit(
            X_train_seq, y_train_seq,
            validation_data=validation_data,
            epochs=self.config['epochs'],
            batch_size=self.config['batch_size'],
            callbacks=callbacks,
            verbose=self.config['verbose']
        )
        
        training_time = time.time() - start_time
        
        # Mark as trained
        self.is_trained = True
        
        # Calculate training metrics (handle NaN padding from sequences)
        y_train_pred = self.predict(X_train)
        valid_mask = ~np.isnan(y_train_pred)
        train_metrics = self.calculate_metrics(y_train[valid_mask], y_train_pred[valid_mask])
        
        # Calculate validation metrics if provided
        val_metrics = {}
        if X_val is not None and y_val is not None:
            y_val_pred = self.predict(X_val)
            valid_mask_val = ~np.isnan(y_val_pred)
            val_metrics = self.calculate_metrics(y_val[valid_mask_val], y_val_pred[valid_mask_val])
            logger.info(f"Validation metrics: {val_metrics}")
        
        # Prepare results
        results = {
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'training_time': training_time,
            'epochs_trained': len(self.history.history['loss']),
            'final_train_loss': float(self.history.history['loss'][-1]),
            'final_val_loss': float(self.history.history['val_loss'][-1]) if validation_data else None,
            'n_features': X_train.shape[1],
            'sequence_length': self.sequence_length
        }
        
        self.log_training_complete(training_time, train_metrics)
        
        return results
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Generate predictions using the trained model.
        
        Handles sequence reshaping for inference and returns predictions
        in the original scale.
        
        Args:
            X: Input features
            
        Returns:
            np.ndarray: Predictions
        """
        self.validate_trained()
        self.validate_input_shape(X)
        
        # Prepare sequences
        X_seq = self.prepare_sequences(X)
        
        # Predict
        predictions_seq = self.model.predict(X_seq, verbose=0)
        
        # Flatten predictions
        predictions = predictions_seq.flatten()
        
        # Pad predictions to match original length
        # (first sequence_length-1 samples don't have predictions)
        padding = np.full(self.sequence_length - 1, np.nan)
        predictions_full = np.concatenate([padding, predictions])
        
        return predictions_full
    
    def save(self, save_dir: str) -> str:
        """
        Save the trained LSTM model.
        
        Args:
            save_dir: Directory to save the model
            
        Returns:
            str: Path to the saved model
        """
        self.validate_trained()
        
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save model in native Keras format
        model_file = save_path / f"{self.model_name}.keras"
        self.model.save(model_file)
        logger.info(f"Saved model to {model_file}")
        
        # Save metadata
        self.save_metadata(save_dir)
        
        return str(model_file)
    
    def load(self, model_path: str) -> None:
        """
        Load a trained LSTM model.
        
        Args:
            model_path: Path to the saved model
        """
        model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Load model
        self.model = keras.models.load_model(model_path)
        self.is_trained = True
        logger.info(f"Loaded model from {model_path}")
        
        # Load metadata if available
        metadata_file = model_path.parent / f"{self.model_name}_metadata.json"
        if metadata_file.exists():
            self.load_metadata(str(metadata_file))
            # Restore sequence_length from metadata
            if 'config' in self.metadata and 'sequence_length' in self.metadata['config']:
                self.sequence_length = self.metadata['config']['sequence_length']
