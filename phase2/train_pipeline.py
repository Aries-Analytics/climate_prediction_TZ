"""
End-to-End ML Training Pipeline

This script orchestrates the complete ML pipeline:
1. Preprocessing and feature engineering
2. Model training (RF, XGBoost, LSTM, Ensemble)
3. Evaluation and reporting
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse
import json
import logging
from datetime import datetime

import numpy as np
import pandas as pd
from models.train_models import train_all_models, save_training_results
from preprocessing.preprocess import preprocess_pipeline
from utils.logger import setup_logging

logger = logging.getLogger(__name__)


def main():
    """Main training pipeline execution."""
    parser = argparse.ArgumentParser(description="Tanzania Climate Prediction - ML Training Pipeline")
    parser.add_argument(
        "--input",
        type=str,
        default="outputs/processed/master_dataset.csv",
        help="Path to master dataset CSV",
    )
    parser.add_argument(
        "--output-dir", type=str, default="outputs/processed", help="Directory for preprocessed features"
    )
    parser.add_argument("--models-dir", type=str, default="outputs/models", help="Directory to save trained models")
    parser.add_argument(
        "--skip-preprocessing", action="store_true", help="Skip preprocessing if features already exist"
    )
    parser.add_argument("--train-rf", action="store_true", default=True, help="Train Random Forest")
    parser.add_argument("--train-xgb", action="store_true", default=True, help="Train XGBoost")
    parser.add_argument("--train-lstm", action="store_true", default=True, help="Train LSTM")
    parser.add_argument("--train-ensemble", action="store_true", default=True, help="Train Ensemble")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(log_level)

    logger.info("=" * 80)
    logger.info("TANZANIA CLIMATE PREDICTION - ML TRAINING PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Input data: {args.input}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Models directory: {args.models_dir}")

    # ========================================================================
    # Step 1: Preprocessing and Feature Engineering
    # ========================================================================
    if not args.skip_preprocessing:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: PREPROCESSING AND FEATURE ENGINEERING")
        logger.info("=" * 80)

        try:
            metadata = preprocess_pipeline(input_path=args.input, output_dir=args.output_dir)
            logger.info("✓ Preprocessing completed successfully")
        except Exception as e:
            logger.error(f"✗ Preprocessing failed: {e}")
            raise
    else:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: SKIPPING PREPROCESSING (using existing features)")
        logger.info("=" * 80)

    # ========================================================================
    # Step 2: Load Preprocessed Data
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: LOADING PREPROCESSED DATA")
    logger.info("=" * 80)

    try:
        train_df = pd.read_csv(f"{args.output_dir}/features_train.csv")
        val_df = pd.read_csv(f"{args.output_dir}/features_val.csv")
        test_df = pd.read_csv(f"{args.output_dir}/features_test.csv")

        logger.info(f"Train set: {train_df.shape}")
        logger.info(f"Validation set: {val_df.shape}")
        logger.info(f"Test set: {test_df.shape}")

        # Remove non-numeric columns (categorical/metadata columns)
        numeric_cols = train_df.select_dtypes(include=["number"]).columns.tolist()
        logger.info(f"Filtering to numeric columns only: {len(numeric_cols)} columns")

        # Columns to exclude (metadata, not features)
        exclude_cols = ["year", "month"]
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]

        # Separate features and target
        # Use rainfall_mm as target if available, otherwise use last numeric column
        if "rainfall_mm" in feature_cols:
            target_col = "rainfall_mm"
            feature_cols.remove("rainfall_mm")
        else:
            target_col = feature_cols[-1]
            feature_cols = feature_cols[:-1]

        logger.info(f"Target variable: {target_col}")
        logger.info(f"Feature count: {len(feature_cols)}")

        # Handle missing values before training
        logger.info("Checking for missing values...")
        missing_counts = train_df[feature_cols].isnull().sum()
        cols_with_missing = missing_counts[missing_counts > 0]
        
        if len(cols_with_missing) > 0:
            logger.warning(f"Found {len(cols_with_missing)} columns with missing values")
            
            # Drop columns that are completely NaN
            all_nan_cols = train_df[feature_cols].columns[train_df[feature_cols].isnull().all()].tolist()
            if all_nan_cols:
                logger.warning(f"Dropping {len(all_nan_cols)} columns with all NaN values: {all_nan_cols[:5]}...")
                feature_cols = [col for col in feature_cols if col not in all_nan_cols]
            
            # Fill remaining missing values with 0 (after normalization, 0 = mean)
            logger.info(f"Filling remaining missing values with 0")
        
        X_train = train_df[feature_cols].fillna(0).values
        y_train = train_df[target_col].values
        X_val = val_df[feature_cols].fillna(0).values
        y_val = val_df[target_col].values
        X_test = test_df[feature_cols].fillna(0).values
        y_test = test_df[target_col].values

        feature_names = feature_cols

        logger.info(f"Features: {len(feature_names)}")
        logger.info(f"Target variable: {target_col}")
        logger.info("✓ Data loaded successfully")

    except Exception as e:
        logger.error(f"✗ Failed to load preprocessed data: {e}")
        raise

    # ========================================================================
    # Step 3: Train Models
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: MODEL TRAINING")
    logger.info("=" * 80)

    try:
        results = train_all_models(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
            feature_names=feature_names,
            models_dir=args.models_dir,
            train_rf=args.train_rf,
            train_xgb=args.train_xgb,
            train_lstm=args.train_lstm,
            train_ensemble=args.train_ensemble,
        )

        logger.info("✓ Model training completed successfully")

    except Exception as e:
        logger.error(f"✗ Model training failed: {e}")
        raise

    # ========================================================================
    # Step 4: Save Results
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: SAVING RESULTS")
    logger.info("=" * 80)

    try:
        results_file = save_training_results(results, args.models_dir)
        logger.info(f"✓ Results saved to {results_file}")

    except Exception as e:
        logger.error(f"✗ Failed to save results: {e}")
        raise

    # ========================================================================
    # Final Summary
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
    logger.info("=" * 80)
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Models saved to: {args.models_dir}")
    logger.info(f"Results saved to: {results_file}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
