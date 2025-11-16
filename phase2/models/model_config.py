"""
Model Configuration Module

This module contains hyperparameter configurations for all model types,
feature engineering parameters, and configuration validation functions.

Requirements: 1.2, 1.3, 2.1, 2.2, 2.3, 5.1, 5.2, 5.3, 5.4
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Model Hyperparameter Configurations
# ============================================================================

MODEL_CONFIG = {
    "random_forest": {
        "n_estimators": 200,
        "max_depth": 15,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "max_features": "sqrt",
        "random_state": 42,
        "n_jobs": -1,
        "verbose": 0,
    },
    "xgboost": {
        "n_estimators": 200,
        "max_depth": 8,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 1,
        "gamma": 0,
        "reg_alpha": 0,
        "reg_lambda": 1,
        "random_state": 42,
        "n_jobs": -1,
        "verbosity": 0,
    },
    "lstm": {
        "units": [128, 64],
        "dropout": 0.2,
        "recurrent_dropout": 0.1,
        "activation": "tanh",
        "recurrent_activation": "sigmoid",
        "epochs": 100,
        "batch_size": 16,
        "learning_rate": 0.001,
        "patience": 10,
        "validation_split": 0.15,
        "sequence_length": 6,  # Reduced from 12 to 6 for smaller datasets
        "verbose": 1,
    },
    "ensemble": {"weights": {"rf": 0.3, "xgb": 0.4, "lstm": 0.3}, "method": "weighted_average"},
}


# ============================================================================
# Feature Engineering Parameters
# ============================================================================

FEATURE_CONFIG = {
    "lag_periods": [1, 3, 6, 12],
    "rolling_windows": [3, 6],
    "rolling_stats": ["mean", "std"],
    "interaction_features": [
        {"feature1": "enso", "feature2": "rainfall", "operation": "multiply"},
        {"feature1": "iod", "feature2": "ndvi", "operation": "multiply"},
    ],
    "target_variables": ["temperature", "rainfall", "ndvi"],
    "max_missing_gap": 2,
    "normalization_method": "standardization",
}


# ============================================================================
# Training Parameters
# ============================================================================

TRAINING_CONFIG = {
    "train_split": 0.70,
    "val_split": 0.15,
    "test_split": 0.15,
    "cross_validation_folds": 5,
    "random_state": 42,
    "shuffle": False,  # Must be False for time series
    "early_stopping": True,
    "early_stopping_patience": 10,
    "save_best_only": True,
}


# ============================================================================
# Evaluation Parameters
# ============================================================================

EVALUATION_CONFIG = {
    "metrics": ["r2_score", "rmse", "mae", "mape"],
    "quantiles": [0.1, 0.5, 0.9],
    "confidence_interval": 0.95,
    "min_r2_threshold": 0.85,
    "plot_formats": ["png"],
    "plot_dpi": 300,
}


# ============================================================================
# Paths Configuration
# ============================================================================

PATHS_CONFIG = {
    "input_data": "outputs/processed/master_dataset.csv",
    "preprocessed_dir": "outputs/processed",
    "models_dir": "models/saved",
    "evaluation_dir": "outputs/evaluation",
    "experiments_dir": "outputs/experiments",
    "logs_dir": "logs",
}


# ============================================================================
# Configuration Validation Functions
# ============================================================================


def validate_model_config(config: Dict[str, Any], model_type: str) -> bool:
    """
    Validate model configuration for a specific model type.

    Args:
        config: Model configuration dictionary
        model_type: Type of model ('random_forest', 'xgboost', 'lstm', 'ensemble')

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    if model_type not in MODEL_CONFIG:
        raise ValueError(f"Unknown model type: {model_type}. " f"Valid types: {list(MODEL_CONFIG.keys())}")

    required_keys = MODEL_CONFIG[model_type].keys()
    missing_keys = set(required_keys) - set(config.keys())

    if missing_keys:
        raise ValueError(f"Missing required configuration keys for {model_type}: {missing_keys}")

    # Model-specific validations
    if model_type == "random_forest":
        if config["n_estimators"] <= 0:
            raise ValueError("n_estimators must be positive")
        if config["max_depth"] is not None and config["max_depth"] <= 0:
            raise ValueError("max_depth must be positive or None")
        if config["min_samples_split"] < 2:
            raise ValueError("min_samples_split must be >= 2")
        if config["min_samples_leaf"] < 1:
            raise ValueError("min_samples_leaf must be >= 1")

    elif model_type == "xgboost":
        if config["n_estimators"] <= 0:
            raise ValueError("n_estimators must be positive")
        if config["max_depth"] <= 0:
            raise ValueError("max_depth must be positive")
        if not 0 < config["learning_rate"] <= 1:
            raise ValueError("learning_rate must be in (0, 1]")
        if not 0 < config["subsample"] <= 1:
            raise ValueError("subsample must be in (0, 1]")
        if not 0 < config["colsample_bytree"] <= 1:
            raise ValueError("colsample_bytree must be in (0, 1]")

    elif model_type == "lstm":
        if not isinstance(config["units"], list) or len(config["units"]) == 0:
            raise ValueError("units must be a non-empty list")
        if any(u <= 0 for u in config["units"]):
            raise ValueError("All units must be positive")
        if not 0 <= config["dropout"] < 1:
            raise ValueError("dropout must be in [0, 1)")
        if config["epochs"] <= 0:
            raise ValueError("epochs must be positive")
        if config["batch_size"] <= 0:
            raise ValueError("batch_size must be positive")
        if config["learning_rate"] <= 0:
            raise ValueError("learning_rate must be positive")
        if config["sequence_length"] <= 0:
            raise ValueError("sequence_length must be positive")

    elif model_type == "ensemble":
        weights = config["weights"]
        if not isinstance(weights, dict):
            raise ValueError("weights must be a dictionary")
        if set(weights.keys()) != {"rf", "xgb", "lstm"}:
            raise ValueError("weights must contain keys: rf, xgb, lstm")
        if not all(0 <= w <= 1 for w in weights.values()):
            raise ValueError("All weights must be in [0, 1]")
        if abs(sum(weights.values()) - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {sum(weights.values())}")

    logger.info(f"Configuration validation passed for {model_type}")
    return True


def validate_feature_config(config: Dict[str, Any]) -> bool:
    """
    Validate feature engineering configuration.

    Args:
        config: Feature configuration dictionary

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    required_keys = ["lag_periods", "rolling_windows", "target_variables"]
    missing_keys = set(required_keys) - set(config.keys())

    if missing_keys:
        raise ValueError(f"Missing required feature configuration keys: {missing_keys}")

    # Validate lag periods
    if not isinstance(config["lag_periods"], list) or len(config["lag_periods"]) == 0:
        raise ValueError("lag_periods must be a non-empty list")
    if any(lag <= 0 for lag in config["lag_periods"]):
        raise ValueError("All lag periods must be positive")

    # Validate rolling windows
    if not isinstance(config["rolling_windows"], list) or len(config["rolling_windows"]) == 0:
        raise ValueError("rolling_windows must be a non-empty list")
    if any(window <= 0 for window in config["rolling_windows"]):
        raise ValueError("All rolling windows must be positive")

    # Validate target variables
    if not isinstance(config["target_variables"], list) or len(config["target_variables"]) == 0:
        raise ValueError("target_variables must be a non-empty list")

    # Validate max missing gap
    if "max_missing_gap" in config and config["max_missing_gap"] < 0:
        raise ValueError("max_missing_gap must be non-negative")

    logger.info("Feature configuration validation passed")
    return True


def validate_training_config(config: Dict[str, Any]) -> bool:
    """
    Validate training configuration.

    Args:
        config: Training configuration dictionary

    Returns:
        bool: True if configuration is valid

    Raises:
        ValueError: If configuration is invalid
    """
    required_keys = ["train_split", "val_split", "test_split"]
    missing_keys = set(required_keys) - set(config.keys())

    if missing_keys:
        raise ValueError(f"Missing required training configuration keys: {missing_keys}")

    # Validate splits
    splits = [config["train_split"], config["val_split"], config["test_split"]]
    if any(s <= 0 or s >= 1 for s in splits):
        raise ValueError("All splits must be in (0, 1)")

    if abs(sum(splits) - 1.0) > 1e-6:
        raise ValueError(f"Splits must sum to 1.0, got {sum(splits)}")

    # Validate cross-validation folds
    if "cross_validation_folds" in config:
        if config["cross_validation_folds"] < 2:
            raise ValueError("cross_validation_folds must be >= 2")

    # Validate shuffle for time series
    if config.get("shuffle", False):
        logger.warning("shuffle is set to True. For time series data, this should be False!")

    logger.info("Training configuration validation passed")
    return True


def validate_all_configs() -> bool:
    """
    Validate all default configurations.

    Returns:
        bool: True if all configurations are valid

    Raises:
        ValueError: If any configuration is invalid
    """
    try:
        # Validate all model configs
        for model_type in MODEL_CONFIG.keys():
            validate_model_config(MODEL_CONFIG[model_type], model_type)

        # Validate feature config
        validate_feature_config(FEATURE_CONFIG)

        # Validate training config
        validate_training_config(TRAINING_CONFIG)

        logger.info("All default configurations validated successfully")
        return True

    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise


def get_model_config(model_type: str, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get model configuration with optional custom overrides.

    Args:
        model_type: Type of model ('random_forest', 'xgboost', 'lstm', 'ensemble')
        custom_config: Optional dictionary with custom configuration overrides

    Returns:
        Dict[str, Any]: Model configuration

    Raises:
        ValueError: If model_type is invalid or configuration is invalid
    """
    if model_type not in MODEL_CONFIG:
        raise ValueError(f"Unknown model type: {model_type}")

    config = MODEL_CONFIG[model_type].copy()

    if custom_config:
        config.update(custom_config)
        validate_model_config(config, model_type)

    return config


def get_feature_config(custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get feature engineering configuration with optional custom overrides.

    Args:
        custom_config: Optional dictionary with custom configuration overrides

    Returns:
        Dict[str, Any]: Feature configuration

    Raises:
        ValueError: If configuration is invalid
    """
    config = FEATURE_CONFIG.copy()

    if custom_config:
        config.update(custom_config)
        validate_feature_config(config)

    return config


def get_training_config(custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get training configuration with optional custom overrides.

    Args:
        custom_config: Optional dictionary with custom configuration overrides

    Returns:
        Dict[str, Any]: Training configuration

    Raises:
        ValueError: If configuration is invalid
    """
    config = TRAINING_CONFIG.copy()

    if custom_config:
        config.update(custom_config)
        validate_training_config(config)

    return config


# ============================================================================
# Module Initialization
# ============================================================================

# Validate all default configurations on module import
try:
    validate_all_configs()
except ValueError as e:
    logger.error(f"Default configuration validation failed: {e}")
    raise
