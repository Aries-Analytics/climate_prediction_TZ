"""
Model Development Pipeline

This script orchestrates the complete ML model development workflow:
1. Preprocessing and feature engineering
2. Training multiple models (RF, XGBoost, LSTM, Ensemble)
3. Comprehensive evaluation with visualizations
4. Experiment tracking and logging

Requirements: All requirements from ML Model Development spec

Usage:
    python model_development_pipeline.py [options]

Options:
    --input PATH          Path to master dataset (default: outputs/processed/master_dataset.csv)
    --output-dir PATH     Output directory (default: outputs)
    --target COLUMN       Target variable column name (default: auto-detect)
    --skip-preprocessing  Skip preprocessing if features already exist
    --models MODEL1,MODEL2  Comma-separated list of models to train (default: all)
                           Options: rf, xgb, lstm, ensemble, all
    --experiment-name NAME  Name for this experiment (default: auto-generated)
    --config PATH         Path to custom config JSON file (optional)
    --verbose            Enable verbose logging
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import preprocessing
from preprocessing.preprocess import preprocess_pipeline

# Import model training
from models.train_models import train_all_models, save_training_results

# Import evaluation
from models.evaluation import generate_evaluation_report

# Import experiment tracking
from models.experiment_tracking import (
    create_experiment_id,
    log_experiment,
    generate_comparison_report,
)

# Import configuration
from models.model_config import (
    MODEL_CONFIG,
    FEATURE_CONFIG,
    TRAINING_CONFIG,
    PATHS_CONFIG,
    get_model_config,
    get_feature_config,
    get_training_config,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/model_development.log", mode="a"),
    ],
)

logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================


def setup_directories(output_dir: str) -> Dict[str, Path]:
    """
    Create necessary output directories.

    Args:
        output_dir: Base output directory

    Returns:
        Dict[str, Path]: Dictionary of directory paths
    """
    base_path = Path(output_dir)

    dirs = {
        "base": base_path,
        "processed": base_path / "processed",
        "models": base_path / "models",
        "evaluation": base_path / "evaluation",
        "experiments": base_path / "experiments",
        "logs": Path("logs"),
    }

    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Created output directories in {output_dir}")

    return dirs


def load_preprocessed_data(
    processed_dir: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load preprocessed train/val/test datasets.

    Args:
        processed_dir: Directory containing preprocessed data

    Returns:
        tuple: (train_df, val_df, test_df)
    """
    logger.info(f"Loading preprocessed data from {processed_dir}")

    processed_path = Path(processed_dir)

    train_df = pd.read_csv(processed_path / "features_train.csv")
    val_df = pd.read_csv(processed_path / "features_val.csv")
    test_df = pd.read_csv(processed_path / "features_test.csv")

    logger.info(f"Loaded train: {train_df.shape}, val: {val_df.shape}, test: {test_df.shape}")

    return train_df, val_df, test_df


def prepare_model_inputs(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_column: Optional[str] = None,
) -> tuple:
    """
    Prepare X and y arrays for model training.

    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
        test_df: Test DataFrame
        target_column: Name of target column (if None, auto-detect)

    Returns:
        tuple: (X_train, y_train, X_val, y_val, X_test, y_test, feature_names)
    """
    logger.info("Preparing model inputs...")

    # Identify target column
    if target_column is None:
        # Auto-detect: look for common target variable names
        possible_targets = [
            "target",
            "temperature",
            "rainfall",
            "precip",
            "ndvi",
        ]

        for col in possible_targets:
            matching_cols = [c for c in train_df.columns if col in c.lower()]
            if matching_cols:
                target_column = matching_cols[0]
                logger.info(f"Auto-detected target column: {target_column}")
                break

        if target_column is None:
            # Use last numeric column as target
            numeric_cols = train_df.select_dtypes(include=[np.number]).columns
            target_column = numeric_cols[-1]
            logger.warning(f"Could not auto-detect target, using last numeric column: {target_column}")

    # Verify target exists
    if target_column not in train_df.columns:
        raise ValueError(f"Target column '{target_column}' not found in data")

    # Exclude non-feature columns
    exclude_cols = ["year", "month", target_column]
    feature_cols = [col for col in train_df.columns if col not in exclude_cols]

    logger.info(f"Target column: {target_column}")
    logger.info(f"Number of features: {len(feature_cols)}")

    # Prepare arrays
    X_train = train_df[feature_cols].values
    y_train = train_df[target_column].values

    X_val = val_df[feature_cols].values
    y_val = val_df[target_column].values

    X_test = test_df[feature_cols].values
    y_test = test_df[target_column].values

    logger.info(f"X_train shape: {X_train.shape}")
    logger.info(f"X_val shape: {X_val.shape}")
    logger.info(f"X_test shape: {X_test.shape}")

    return X_train, y_train, X_val, y_val, X_test, y_test, feature_cols


def parse_model_list(models_str: str) -> Dict[str, bool]:
    """
    Parse comma-separated model list into training flags.

    Args:
        models_str: Comma-separated model names (e.g., "rf,xgb" or "all")

    Returns:
        Dict[str, bool]: Dictionary of model training flags
    """
    models_str = models_str.lower().strip()

    if models_str == "all":
        return {
            "train_rf": True,
            "train_xgb": True,
            "train_lstm": True,
            "train_ensemble": True,
        }

    model_map = {
        "rf": "train_rf",
        "random_forest": "train_rf",
        "xgb": "train_xgb",
        "xgboost": "train_xgb",
        "lstm": "train_lstm",
        "ensemble": "train_ensemble",
    }

    flags = {
        "train_rf": False,
        "train_xgb": False,
        "train_lstm": False,
        "train_ensemble": False,
    }

    for model in models_str.split(","):
        model = model.strip()
        if model in model_map:
            flags[model_map[model]] = True
        else:
            logger.warning(f"Unknown model: {model}, skipping")

    return flags


# ============================================================================
# Main Pipeline Function
# ============================================================================


def run_model_development_pipeline(
    input_path: str,
    output_dir: str = "outputs",
    target_column: Optional[str] = None,
    skip_preprocessing: bool = False,
    models_to_train: str = "all",
    experiment_name: Optional[str] = None,
    config_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the complete model development pipeline.

    Args:
        input_path: Path to master dataset CSV
        output_dir: Base output directory
        target_column: Target variable column name
        skip_preprocessing: Skip preprocessing if features already exist
        models_to_train: Comma-separated list of models or "all"
        experiment_name: Name for this experiment
        config_path: Path to custom config JSON

    Returns:
        Dict[str, Any]: Pipeline results including all metrics and paths
    """
    pipeline_start_time = time.time()

    logger.info("=" * 80)
    logger.info("STARTING MODEL DEVELOPMENT PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Models: {models_to_train}")
    logger.info(f"Experiment: {experiment_name or 'auto-generated'}")
    logger.info("=" * 80)

    # Setup directories
    dirs = setup_directories(output_dir)

    # Load custom config if provided
    custom_config = None
    if config_path:
        logger.info(f"Loading custom configuration from {config_path}")
        with open(config_path, "r") as f:
            custom_config = json.load(f)

    # Parse model training flags
    model_flags = parse_model_list(models_to_train)
    logger.info(f"Training flags: {model_flags}")

    # ========================================================================
    # STEP 1: Preprocessing and Feature Engineering
    # ========================================================================

    if not skip_preprocessing:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: PREPROCESSING AND FEATURE ENGINEERING")
        logger.info("=" * 80)

        preprocessing_metadata = preprocess_pipeline(
            input_path=input_path,
            output_dir=str(dirs["processed"]),
            lag_periods=FEATURE_CONFIG["lag_periods"],
            rolling_windows=FEATURE_CONFIG["rolling_windows"],
        )

        logger.info("Preprocessing completed successfully")
    else:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: SKIPPING PREPROCESSING (using existing features)")
        logger.info("=" * 80)
        preprocessing_metadata = {"skipped": True}

    # ========================================================================
    # STEP 2: Load Preprocessed Data
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: LOADING PREPROCESSED DATA")
    logger.info("=" * 80)

    train_df, val_df, test_df = load_preprocessed_data(str(dirs["processed"]))

    # ========================================================================
    # STEP 3: Prepare Model Inputs
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: PREPARING MODEL INPUTS")
    logger.info("=" * 80)

    X_train, y_train, X_val, y_val, X_test, y_test, feature_names = prepare_model_inputs(
        train_df, val_df, test_df, target_column
    )

    # ========================================================================
    # STEP 4: Train Models
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: TRAINING MODELS")
    logger.info("=" * 80)

    training_results = train_all_models(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        feature_names=feature_names,
        models_dir=str(dirs["models"]),
        **model_flags,
    )

    # Save training results
    results_file = save_training_results(
        training_results, str(dirs["experiments"]), experiment_name
    )

    logger.info(f"Training results saved to {results_file}")

    # ========================================================================
    # STEP 5: Comprehensive Evaluation
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 5: COMPREHENSIVE EVALUATION")
    logger.info("=" * 80)

    # Note: Detailed evaluation is already done in train_all_models
    # This step could add additional cross-model comparisons

    logger.info("Evaluation completed (see training results for details)")

    # ========================================================================
    # STEP 6: Experiment Tracking
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 6: EXPERIMENT TRACKING")
    logger.info("=" * 80)

    # Create experiment ID
    if experiment_name:
        exp_id = create_experiment_id(prefix=experiment_name)
    else:
        exp_id = create_experiment_id(prefix="ml_pipeline")

    # Prepare experiment data
    experiment_data = {
        "name": experiment_name or "ml_pipeline",
        "input_path": input_path,
        "target_column": target_column,
        "models_trained": [k.replace("train_", "") for k, v in model_flags.items() if v],
        "preprocessing_metadata": preprocessing_metadata,
        "training_results": training_results,
        "config": {
            "model_config": MODEL_CONFIG,
            "feature_config": FEATURE_CONFIG,
            "training_config": TRAINING_CONFIG,
        },
    }

    # Log experiment
    log_file = str(dirs["experiments"] / "experiment_log.jsonl")
    log_experiment(exp_id, experiment_data, log_file)

    # Generate comparison report
    comparison_report = generate_comparison_report(
        log_file=log_file,
        output_file=str(dirs["experiments"] / "comparison_report.md"),
    )

    logger.info(f"Experiment logged: {exp_id}")
    logger.info(f"Comparison report: {comparison_report}")

    # ========================================================================
    # Pipeline Summary
    # ========================================================================

    pipeline_end_time = time.time()
    pipeline_duration = pipeline_end_time - pipeline_start_time

    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"Experiment ID: {exp_id}")
    logger.info(f"Total duration: {pipeline_duration:.2f} seconds ({pipeline_duration/60:.2f} minutes)")
    logger.info(f"Results saved to: {output_dir}")
    logger.info("=" * 80)

    # Return comprehensive results
    return {
        "experiment_id": exp_id,
        "duration_seconds": pipeline_duration,
        "preprocessing_metadata": preprocessing_metadata,
        "training_results": training_results,
        "output_directories": {k: str(v) for k, v in dirs.items()},
        "results_file": results_file,
        "comparison_report": comparison_report,
    }


# ============================================================================
# Command-Line Interface
# ============================================================================


def main():
    """Main entry point for command-line execution."""
    parser = argparse.ArgumentParser(
        description="ML Model Development Pipeline for Climate Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--input",
        type=str,
        default="outputs/processed/master_dataset.csv",
        help="Path to master dataset CSV file",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Base output directory for all results",
    )

    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target variable column name (auto-detect if not specified)",
    )

    parser.add_argument(
        "--skip-preprocessing",
        action="store_true",
        help="Skip preprocessing if features already exist",
    )

    parser.add_argument(
        "--models",
        type=str,
        default="all",
        help="Comma-separated list of models to train (rf,xgb,lstm,ensemble) or 'all'",
    )

    parser.add_argument(
        "--experiment-name",
        type=str,
        default=None,
        help="Name for this experiment (auto-generated if not specified)",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom configuration JSON file",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run pipeline
    try:
        results = run_model_development_pipeline(
            input_path=args.input,
            output_dir=args.output_dir,
            target_column=args.target,
            skip_preprocessing=args.skip_preprocessing,
            models_to_train=args.models,
            experiment_name=args.experiment_name,
            config_path=args.config,
        )

        logger.info("\n✓ Pipeline completed successfully!")
        logger.info(f"✓ Experiment ID: {results['experiment_id']}")
        logger.info(f"✓ Check results in: {args.output_dir}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"\n✗ Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
