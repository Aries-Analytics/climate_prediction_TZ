"""
Random Forest Model Implementation

This module implements a Random Forest regression model for climate prediction.

Requirements: 2.1, 2.5, 2.7
"""

import logging
import time
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from models.base_model import SklearnBaseModel
from models.model_config import get_model_config
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score

logger = logging.getLogger(__name__)


class RandomForestModel(SklearnBaseModel):
    """
    Random Forest regression model for climate prediction.

    This model uses scikit-learn's RandomForestRegressor with configurable
    hyperparameters and supports cross-validation for time series data.
    """

    def __init__(self, model_name: str = "random_forest", custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize Random Forest model.

        Args:
            model_name: Name identifier for the model
            custom_config: Optional custom configuration overrides
        """
        # Get configuration
        config = get_model_config("random_forest", custom_config)

        # Initialize base class
        super().__init__(model_name, "random_forest", config)

        # Initialize the sklearn model
        self.model = RandomForestRegressor(
            n_estimators=config["n_estimators"],
            max_depth=config["max_depth"],
            min_samples_split=config["min_samples_split"],
            min_samples_leaf=config["min_samples_leaf"],
            max_features=config["max_features"],
            random_state=config["random_state"],
            n_jobs=config["n_jobs"],
            verbose=config["verbose"],
        )

        self.feature_importances_ = None

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Train the Random Forest model.

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

        # Start training
        start_time = time.time()

        # Fit the model
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

    def cross_validate(self, X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> Dict[str, Any]:
        """
        Perform time series cross-validation.

        Args:
            X: Features
            y: Targets
            n_splits: Number of cross-validation folds

        Returns:
            Dict[str, Any]: Cross-validation results
        """
        logger.info(f"Performing {n_splits}-fold time series cross-validation")

        # Use TimeSeriesSplit for temporal data
        tscv = TimeSeriesSplit(n_splits=n_splits)

        # Calculate cross-validation scores
        cv_scores = cross_val_score(self.model, X, y, cv=tscv, scoring="r2", n_jobs=self.config["n_jobs"])

        # Calculate additional metrics manually
        rmse_scores = []
        mae_scores = []

        for train_idx, val_idx in tscv.split(X):
            X_train_cv, X_val_cv = X[train_idx], X[val_idx]
            y_train_cv, y_val_cv = y[train_idx], y[val_idx]

            # Fit and predict
            self.model.fit(X_train_cv, y_train_cv)
            y_pred_cv = self.model.predict(X_val_cv)

            # Calculate metrics
            metrics = self.calculate_metrics(y_val_cv, y_pred_cv)
            rmse_scores.append(metrics["rmse"])
            mae_scores.append(metrics["mae"])

        results = {
            "r2_scores": cv_scores.tolist(),
            "r2_mean": float(cv_scores.mean()),
            "r2_std": float(cv_scores.std()),
            "rmse_mean": float(np.mean(rmse_scores)),
            "rmse_std": float(np.std(rmse_scores)),
            "mae_mean": float(np.mean(mae_scores)),
            "mae_std": float(np.std(mae_scores)),
            "n_splits": n_splits,
        }

        logger.info(f"Cross-validation R² mean: {results['r2_mean']:.4f} (+/- {results['r2_std']:.4f})")
        logger.info(f"Cross-validation RMSE mean: {results['rmse_mean']:.4f} (+/- {results['rmse_std']:.4f})")

        return results

    def get_feature_importance(self, feature_names: Optional[list] = None) -> pd.DataFrame:
        """
        Get feature importance rankings.

        Args:
            feature_names: Optional list of feature names

        Returns:
            pd.DataFrame: DataFrame with features and their importance scores
        """
        self.validate_trained()

        if self.feature_importances_ is None:
            raise ValueError("Feature importances not available")

        # Use provided feature names or generate default ones
        if feature_names is None:
            feature_names = self.get_feature_names()

        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(len(self.feature_importances_))]

        # Create DataFrame
        importance_df = (
            pd.DataFrame({"feature": feature_names, "importance": self.feature_importances_})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )

        return importance_df

    def save_feature_importance(self, save_dir: str, feature_names: Optional[list] = None) -> str:
        """
        Save feature importance to CSV file.

        Args:
            save_dir: Directory to save the file
            feature_names: Optional list of feature names

        Returns:
            str: Path to saved file
        """
        from pathlib import Path

        importance_df = self.get_feature_importance(feature_names)

        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        file_path = save_path / f"{self.model_name}_feature_importance.csv"
        importance_df.to_csv(file_path, index=False)

        logger.info(f"Saved feature importance to {file_path}")

        return str(file_path)
