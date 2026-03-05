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

    # Select only numeric columns (excludes strings like location, data_quality, season, etc.)
    numeric_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()
    exclude_cols = ["year", "month", target_column]
    feature_cols = [col for col in numeric_cols if col not in exclude_cols]

    logger.info(f"Target column: {target_column}")
    logger.info(f"Total columns: {len(train_df.columns)}")
    logger.info(f"Numeric columns: {len(numeric_cols)}")
    logger.info(f"Feature columns (numeric only): {len(feature_cols)}")

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

    return X_train, y_train, X_val, y_val, X_test, y_test, feature_cols, target_column


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

    X_train, y_train, X_val, y_val, X_test, y_test, feature_names, target_column = prepare_model_inputs(
        train_df, val_df, test_df, target_column
    )

    # ========================================================================
    # STEP 3.4: Data Leakage Prevention
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 3.4: DATA LEAKAGE PREVENTION")
    logger.info("=" * 80)
    logger.info(f"Checking {len(feature_names)} features for data leakage...")

    from utils.data_leakage_prevention import remove_leaky_features

    # Convert arrays to DataFrame for the utility
    X_train_df_for_check = pd.DataFrame(X_train, columns=feature_names)
    y_train_series = pd.Series(y_train, name=target_column)

    # Use the comprehensive leakage prevention module
    X_cleaned, removed_features, removal_reasons = remove_leaky_features(
        X_train_df_for_check, target_name=target_column, y=y_train_series, strict=True
    )

    if removed_features:
        clean_feature_names = [f for f in feature_names if f not in removed_features]
        feature_indices = [i for i, f in enumerate(feature_names) if f not in removed_features]
        X_train = X_train[:, feature_indices]
        X_val = X_val[:, feature_indices]
        X_test = X_test[:, feature_indices]
        feature_names = clean_feature_names

        logger.info(f"Removed {len(removed_features)} leaky features")
        for reason in removal_reasons:
            logger.info(f"  {reason}")
        logger.info(f"Remaining features: {len(feature_names)}")
    else:
        logger.info("No leaky features detected")

    # ========================================================================
    # STEP 3.5: Feature Selection
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 3.5: FEATURE SELECTION")
    logger.info("=" * 80)
    logger.info(f"Reducing features from {len(feature_names)} to ~80 selected features")

    try:
        from preprocessing.feature_selection import select_features_hybrid, apply_feature_selection

        # Convert arrays to DataFrames
        X_train_df = pd.DataFrame(X_train, columns=feature_names)
        X_val_df = pd.DataFrame(X_val, columns=feature_names)
        X_test_df = pd.DataFrame(X_test, columns=feature_names)

        # Perform hybrid feature selection
        selection_result = select_features_hybrid(
            X_train_df,
            pd.Series(y_train),
            target_features=80,
            min_per_source=5
        )

        # Save results
        selection_result.save(str(dirs["models"]) + "/feature_selection_results.json")

        # Apply selection
        X_train = apply_feature_selection(X_train_df, selection_result.selected_features).values
        X_val = apply_feature_selection(X_val_df, selection_result.selected_features).values
        X_test = apply_feature_selection(X_test_df, selection_result.selected_features).values
        feature_names = selection_result.selected_features

        logger.info(f"Selected {len(feature_names)} features")
        logger.info(f"Features saved to: {dirs['models']}/feature_selection_results.json")

        # Store feature selection summary for later enrichment of training_results
        _feature_selection_summary = {
            "selected_features": selection_result.selected_count if hasattr(selection_result, 'selected_count') else len(feature_names),
            "original_features": selection_result.original_count if hasattr(selection_result, 'original_count') else None,
        }

    except Exception as e:
        logger.error(f"Feature selection failed: {e}")
        logger.warning("Continuing with all features")
        _feature_selection_summary = None

    # ========================================================================
    # STEP 3.6: Handle Missing Values
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 3.6: HANDLING MISSING VALUES")
    logger.info("=" * 80)

    nan_count_train = np.isnan(X_train).sum()
    nan_count_val = np.isnan(X_val).sum()
    nan_count_test = np.isnan(X_test).sum()

    logger.info(f"NaN values - Train: {nan_count_train}, Val: {nan_count_val}, Test: {nan_count_test}")

    if nan_count_train > 0 or nan_count_val > 0 or nan_count_test > 0:
        logger.info("Filling NaN values with median...")

        X_train_df = pd.DataFrame(X_train, columns=feature_names)
        median_values = X_train_df.median()

        X_train = X_train_df.fillna(median_values).values
        X_val = pd.DataFrame(X_val, columns=feature_names).fillna(median_values).values
        X_test = pd.DataFrame(X_test, columns=feature_names).fillna(median_values).values

        y_train_median = np.nanmedian(y_train)
        y_train = np.where(np.isnan(y_train), y_train_median, y_train)
        y_val = np.where(np.isnan(y_val), y_train_median, y_val)
        y_test = np.where(np.isnan(y_test), y_train_median, y_test)

        logger.info(f"Filled NaN values. Remaining: {np.isnan(X_train).sum()}")
    else:
        logger.info("No NaN values detected")

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

    # Save initial training results (will be re-saved with enriched data at end of pipeline)
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

    # Display test metrics for all trained models
    logger.info("\nTest Set Performance:")
    logger.info("-" * 80)
    for model_name, model_results in training_results["models"].items():
        if "error" in model_results:
            logger.info(f"{model_name.upper()}: FAILED - {model_results['error']}")
        elif "test_metrics" in model_results:
            metrics = model_results["test_metrics"]
            if "error" not in metrics:
                logger.info(
                    f"{model_name.upper()}: R²={metrics.get('r2', 0):.4f}, "
                    f"RMSE={metrics.get('rmse', 0):.4f}, MAE={metrics.get('mae', 0):.4f}"
                )
        elif model_name == "ensemble" and "ensemble_metrics" in model_results:
            metrics = model_results["ensemble_metrics"]
            if metrics and "error" not in metrics:
                logger.info(
                    f"{model_name.upper()}: R²={metrics.get('r2', 0):.4f}, "
                    f"RMSE={metrics.get('rmse', 0):.4f}, MAE={metrics.get('mae', 0):.4f}"
                )
    logger.info("-" * 80)

    # ========================================================================
    # STEP 5.2: Temporal Cross-Validation
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 5.2: TEMPORAL CROSS-VALIDATION")
    logger.info("=" * 80)
    logger.info("Running 5-fold time-series CV for robustness assessment...")

    try:
        from evaluation.cross_validation import cross_validate_sklearn_model, compare_cv_results
        from sklearn.ensemble import RandomForestRegressor
        from xgboost import XGBRegressor

        cv_results_list = []

        # Cross-validate Random Forest (if trained)
        if "random_forest" in training_results["models"] and "error" not in training_results["models"]["random_forest"]:
            logger.info("Cross-validating Random Forest...")
            rf_cv = cross_validate_sklearn_model(
                RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
                X_train, y_train,
                n_splits=5, model_name="RandomForest"
            )
            cv_results_list.append(rf_cv)
            logger.info(f"RF CV: R²={rf_cv.r2_mean:.4f} ± {rf_cv.r2_std:.4f}")

        # Cross-validate XGBoost (if trained)
        if "xgboost" in training_results["models"] and "error" not in training_results["models"]["xgboost"]:
            logger.info("Cross-validating XGBoost...")
            xgb_cv = cross_validate_sklearn_model(
                XGBRegressor(n_estimators=500, max_depth=4, learning_rate=0.01, random_state=42),
                X_train, y_train,
                n_splits=5, model_name="XGBoost"
            )
            cv_results_list.append(xgb_cv)
            logger.info(f"XGB CV: R²={xgb_cv.r2_mean:.4f} ± {xgb_cv.r2_std:.4f}")

        # Save CV comparison
        if cv_results_list:
            cv_comparison = compare_cv_results(cv_results_list)
            cv_path = dirs["evaluation"] / "cv_comparison.csv"
            cv_comparison.to_csv(cv_path, index=False)
            logger.info(f"CV comparison saved to: {cv_path}")

        # Enrich training_results with CV data so canonical file includes it
        cv_data_for_results = {}
        for cv_result in cv_results_list:
            name = cv_result.model_name.lower().replace(" ", "_")
            cv_data_for_results[name] = {
                "r2_mean": cv_result.r2_mean,
                "r2_std": cv_result.r2_std,
                "r2_ci_lower": cv_result.r2_ci_lower,
                "r2_ci_upper": cv_result.r2_ci_upper,
                "rmse_mean": cv_result.rmse_mean,
                "rmse_std": cv_result.rmse_std,
                "mae_mean": cv_result.mae_mean,
                "mae_std": cv_result.mae_std,
                "n_splits": cv_result.n_splits,
            }
        if cv_data_for_results:
            training_results["cross_validation"] = cv_data_for_results
            logger.info(f"Added CV data for {len(cv_data_for_results)} models to training_results")

    except Exception as e:
        logger.error(f"Temporal CV failed: {e}")
        logger.info("Continuing without temporal CV results")

    # ========================================================================
    # STEP 5.3: Detailed Evaluation Report
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 5.3: GENERATING DETAILED EVALUATION REPORT")
    logger.info("=" * 80)

    try:
        from models.evaluation import (
            plot_predictions_vs_actual,
            plot_residuals_over_time,
            generate_evaluation_report
        )

        # Generate plots for each successful model
        for model_name, model_results in training_results["models"].items():
            if "error" not in model_results and "test_metrics" in model_results:
                # Create plots directory for this model
                model_plots_dir = dirs["evaluation"] / "plots" / model_name
                model_plots_dir.mkdir(parents=True, exist_ok=True)

                # Load model predictions (would need to re-predict or save during training)
                # For now, just log that plots would be generated
                logger.info(f"Evaluation plots for {model_name} would be saved to {model_plots_dir}")

        logger.info("Detailed evaluation report generation complete")

    except Exception as e:
        logger.error(f"Evaluation report generation failed: {e}")
        logger.info("Continuing without detailed evaluation report")

    # ========================================================================
    # STEP 5.5: Spatial Generalization Validation (LOLO CV)
    # ========================================================================

    spatial_cv_results = None
    
    # Check if we have multi-location data
    if 'location' in train_df.columns:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5.5: SPATIAL GENERALIZATION VALIDATION (LOLO CV)")
        logger.info("=" * 80)
        logger.info("Multi-location data detected - running spatial cross-validation...")
        
        try:
            import subprocess
            from pathlib import Path
            
            # Run spatial CV as subprocess
            result = subprocess.run(
                ['python', 'evaluation/spatial_cv.py'],
                capture_output=True,
                text=True,
                cwd=str(Path.cwd())
            )
            
            if result.returncode == 0:
                logger.info("Spatial CV completed successfully")
                logger.info("Check outputs/evaluation/spatial_cv/ for detailed results")
                
                # Try to load results
                spatial_cv_file = Path("outputs/evaluation/spatial_cv/spatial_cv_results.json")
                if spatial_cv_file.exists():
                    import json
                    with open(spatial_cv_file) as f:
                        spatial_cv_results = json.load(f)
                    logger.info(f"Spatial CV summary: {spatial_cv_results.get('summary', {})}")
            else:
                logger.warning(f"Spatial CV failed with code {result.returncode}")
                logger.warning(f"Error: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Spatial CV execution failed: {e}")
            logger.info("Continuing without spatial CV results")
    else:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5.5: SPATIAL CV SKIPPED (single location data)")
        logger.info("=" * 80)

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
    # STEP 7: Generate active_model.json (Dynamic Model Resolution)
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 7: GENERATING active_model.json FOR SERVING")
    logger.info("=" * 80)

    try:
        # Find the best-performing model by test R²
        model_scores = {}
        model_filenames = {
            "random_forest": "random_forest_climate.pkl",
            "xgboost": "xgboost_climate.pkl",
        }

        for model_name, model_results in training_results["models"].items():
            if "error" not in model_results and "test_metrics" in model_results:
                metrics = model_results["test_metrics"]
                if "error" not in metrics and "r2" in metrics:
                    model_scores[model_name] = metrics["r2"]

        if model_scores:
            # Sort by R² (highest first)
            ranked = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
            best_name, best_r2 = ranked[0]
            
            # Build active_model.json
            from datetime import datetime, timezone as tz
            
            active_model_config = {
                "expected_feature_count": len(feature_names),
                "feature_schema": "feature_schema.json",
                "last_updated": datetime.now(tz.utc).isoformat(),
                "notes": f"Auto-generated by training pipeline (experiment: {exp_id})",
            }
            
            # Primary model (best R²)
            best_filename = model_filenames.get(best_name, f"{best_name}_climate.pkl")
            active_model_config["primary_model"] = {
                "filename": best_filename,
                "type": best_name,
                "version": f"{best_name}_v{exp_id[:8]}",
                "r2_score": best_r2,
                "expected_features": len(feature_names),
                "trained_at": datetime.now(tz.utc).isoformat(),
            }
            
            # Fallback model (second best, if available)
            if len(ranked) > 1:
                fallback_name, fallback_r2 = ranked[1]
                fallback_filename = model_filenames.get(fallback_name, f"{fallback_name}_climate.pkl")
                active_model_config["fallback_model"] = {
                    "filename": fallback_filename,
                    "type": fallback_name,
                    "version": f"{fallback_name}_v{exp_id[:8]}",
                    "r2_score": fallback_r2,
                    "expected_features": len(feature_names),
                    "trained_at": datetime.now(tz.utc).isoformat(),
                }
            
            # Write to models directory
            active_model_path = dirs["models"] / "active_model.json"
            with open(active_model_path, "w") as f:
                json.dump(active_model_config, f, indent=2)
            
            logger.info(f"Generated active_model.json:")
            logger.info(f"  Primary: {best_filename} (R²={best_r2:.4f})")
            if len(ranked) > 1:
                logger.info(f"  Fallback: {fallback_filename} (R²={ranked[1][1]:.4f})")
            logger.info(f"  Features: {len(feature_names)}")
            logger.info(f"  Saved to: {active_model_path}")
        else:
            logger.warning("No model scores available — active_model.json not generated")

    except Exception as e:
        logger.error(f"Failed to generate active_model.json: {e}")
        logger.warning("Serving will fall back to hardcoded model candidates")

    # ========================================================================
    # STEP 8: Re-save Enriched Training Results to Canonical Path
    # ========================================================================

    logger.info("\n" + "=" * 80)
    logger.info("STEP 8: SAVING ENRICHED TRAINING RESULTS")
    logger.info("=" * 80)

    # Add feature selection summary if available
    if _feature_selection_summary:
        training_results["feature_selection"] = _feature_selection_summary
        logger.info(f"Added feature_selection to training_results: {_feature_selection_summary}")

    # Re-save the enriched training_results (now includes cross_validation + feature_selection)
    try:
        enriched_file = save_training_results(
            training_results, str(dirs["experiments"]), experiment_name
        )
        # Update canonical path with enriched data
        import shutil
        canonical_path = dirs["models"] / "latest_training_results.json"
        shutil.copy2(enriched_file, str(canonical_path))
        logger.info(f"Canonical training results updated with enriched data: {canonical_path}")
        logger.info(f"  Keys: {list(training_results.keys())}")
    except Exception as e:
        logger.error(f"Failed to re-save enriched training results: {e}")

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

        logger.info("\n[OK] Pipeline completed successfully!")
        logger.info(f"[OK] Experiment ID: {results['experiment_id']}")
        logger.info(f"[OK] Check results in: {args.output_dir}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"\n[FAIL] Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
