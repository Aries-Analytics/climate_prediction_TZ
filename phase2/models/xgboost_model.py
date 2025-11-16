"""
XGBoost Model Implementation

This module implements an XGBoost regression model for climate prediction.

Requirements: 2.2, 2.7
"""

import logging
import time
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

try:
    import xgboost as xgb

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("XGBoost not installed. Install with: pip install xgboost")

from models.base_model import SklearnBaseModel
from models.model_config import get_model_config

logger = logging.getLogger(__name__)


class XGBoostModel(SklearnBaseModel):
    """
    XGBoost regression model for climate prediction.

    This model uses XGBoost's XGBRegressor with configurable hyperparameters,
    early stopping, and feature importance extraction.
    """

    def __init__(self, model_name: str = "xgboost", custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize XGBoost model.

        Args:
            model_name: Name identifier for the model
            custom_config: Optional custom configuration overrides

        Raises:
            ImportError: If XGBoost is not installed
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost is not installed. Install with: pip install xgboost")

        # Get configuration
        config = get_model_config("xgboost", custom_config)

        # Initialize base class
        super().__init__(model_name, "xgboost", config)

        # Initialize the XGBoost model
        self.model = xgb.XGBRegressor(
            n_estimators=config["n_estimators"],
            max_depth=config["max_depth"],
            learning_rate=config["learning_rate"],
            subsample=config["subsample"],
            colsample_bytree=config["colsample_bytree"],
            min_child_weight=config["min_child_weight"],
            gamma=config["gamma"],
            reg_alpha=config["reg_alpha"],
            reg_lambda=config["reg_lambda"],
            random_state=config["random_state"],
            n_jobs=config["n_jobs"],
            verbosity=config["verbosity"],
        )

        self.feature_importances_ = None
        self.best_iteration_ = None

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        early_stopping_rounds: int = 10,
    ) -> Dict[str, Any]:
        """
        Train the XGBoost model with optional early stopping.

        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features (optional, required for early stopping)
            y_val: Validation targets (optional, required for early stopping)
            early_stopping_rounds: Number of rounds for early stopping

        Returns:
            Dict[str, Any]: Training metrics and information
        """
        self.log_training_start(X_train.shape, y_train.shape)

        # Validate input
        self.validate_input_shape(X_train)

        # Start training
        start_time = time.time()

        # Prepare evaluation set for early stopping
        eval_set = []
        if X_val is not None and y_val is not None:
            eval_set = [(X_train, y_train), (X_val, y_val)]
            logger.info(f"Using early stopping with {early_stopping_rounds} rounds")

        # Fit the model
        if eval_set:
            # XGBoost API changed between versions - try both approaches
            try:
                # Try older XGBoost API first (< 2.0)
                self.model.fit(
                    X_train,
                    y_train,
                    eval_set=eval_set,
                    early_stopping_rounds=early_stopping_rounds,
                    verbose=False,
                )
                logger.info(f"Using XGBoost < 2.0 API with early_stopping_rounds parameter")
            except TypeError as e:
                # If that fails, try XGBoost 2.0+ API with callbacks
                if "early_stopping_rounds" in str(e) or "callbacks" in str(e):
                    try:
                        from xgboost.callback import EarlyStopping
                        
                        self.model.fit(
                            X_train,
                            y_train,
                            eval_set=eval_set,
                            callbacks=[EarlyStopping(rounds=early_stopping_rounds)],
                            verbose=False,
                        )
                        logger.info(f"Using XGBoost 2.0+ API with EarlyStopping callback")
                    except Exception as callback_error:
                        logger.warning(f"Early stopping failed: {callback_error}. Training without early stopping.")
                        self.model.fit(X_train, y_train, verbose=False)
                else:
                    raise
            
            # Get best iteration if available
            if hasattr(self.model, 'best_iteration'):
                self.best_iteration_ = self.model.best_iteration
                logger.info(f"Best iteration: {self.best_iteration_}")
        else:
            self.model.fit(X_train, y_train)

        training_time = time.time() - start_time

        # Mark as trained
        self.is_trained = True

        # Calculate training metrics
        y_train_pred = self.model.predict(X_train)
        train_metrics = self.calculate_metrics(y_train, y_train_pred)

        # Calculate validation metrics if provided
        val_metrics = {}
        if X_val is not None and y_val is not None:
            y_val_pred = self.model.predict(X_val)
            val_metrics = self.calculate_metrics(y_val, y_val_pred)
            logger.info(f"Validation metrics: {val_metrics}")

        # Store feature importances
        self.feature_importances_ = self.model.feature_importances_

        # Prepare results
        results = {
            "train_metrics": train_metrics,
            "val_metrics": val_metrics,
            "training_time": training_time,
            "n_estimators": self.model.n_estimators,
            "best_iteration": self.best_iteration_,
            "n_features": X_train.shape[1],
        }

        self.log_training_complete(training_time, train_metrics)

        return results

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Generate predictions using the trained model.

        Args:
            X: Input features

        Returns:
            np.ndarray: Predictions
        """
        self.validate_trained()
        self.validate_input_shape(X)

        predictions = self.model.predict(X)

        return predictions

    def get_feature_importance(
        self, feature_names: Optional[list] = None, importance_type: str = "gain"
    ) -> pd.DataFrame:
        """
        Get feature importance rankings using specified importance type.

        Args:
            feature_names: Optional list of feature names
            importance_type: Type of importance ('gain', 'weight', 'cover')

        Returns:
            pd.DataFrame: DataFrame with features and their importance scores
        """
        self.validate_trained()

        # Get importance scores based on type
        if importance_type == "gain":
            importances = self.model.feature_importances_
        else:
            # Get booster and extract importance
            booster = self.model.get_booster()
            importance_dict = booster.get_score(importance_type=importance_type)

            # Convert to array (handle missing features)
            n_features = len(feature_names) if feature_names else self.model.n_features_in_
            importances = np.zeros(n_features)
            for feat_idx, score in importance_dict.items():
                idx = int(feat_idx.replace("f", ""))
                if idx < n_features:
                    importances[idx] = score

        # Use provided feature names or generate default ones
        if feature_names is None:
            feature_names = self.get_feature_names()

        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(len(importances))]

        # Create DataFrame
        importance_df = (
            pd.DataFrame({"feature": feature_names, "importance": importances})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )

        return importance_df

    def save_feature_importance(
        self, save_dir: str, feature_names: Optional[list] = None, importance_type: str = "gain"
    ) -> str:
        """
        Save feature importance to CSV file.

        Args:
            save_dir: Directory to save the file
            feature_names: Optional list of feature names
            importance_type: Type of importance ('gain', 'weight', 'cover')

        Returns:
            str: Path to saved file
        """
        from pathlib import Path

        importance_df = self.get_feature_importance(feature_names, importance_type)

        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        file_path = save_path / f"{self.model_name}_feature_importance_{importance_type}.csv"
        importance_df.to_csv(file_path, index=False)

        logger.info(f"Saved feature importance ({importance_type}) to {file_path}")

        return str(file_path)
