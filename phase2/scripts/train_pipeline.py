"""
End-to-End ML Training Pipeline with Model Performance Improvements

This script orchestrates the complete ML pipeline with improvements:
1. Preprocessing with optimized feature engineering
2. Feature selection (640 → 50-100 features)
3. Baseline model training for comparison
4. Advanced model training (RF, XGBoost, LSTM) with enhanced regularization
5. Improved weighted ensemble
6. Time-series cross-validation
7. Automated model validation
8. Comprehensive reporting

Requirements: 1.5, 4.5, 7.4, 10.5
"""

import sys
from pathlib import Path

# Add project root to Python path (scripts/ is one level below phase2/)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse
import json
import logging
from datetime import datetime

import numpy as np
import pandas as pd

# Import existing modules
from models.train_models import train_all_models, save_training_results
from preprocessing.preprocess import preprocess_pipeline
from utils.logger import setup_logging

# Import new improvement modules
from preprocessing.feature_selection import select_features_hybrid, apply_feature_selection
from evaluation.cross_validation import cross_validate_sklearn_model, compare_cv_results
from utils.model_validation import validate_model, save_validation_report

logger = logging.getLogger(__name__)


def train_baseline_models(X_train, y_train, X_test, y_test):
    """
    Train simple baseline models for comparison.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        
    Returns:
        Dict with baseline results
    """
    from sklearn.linear_model import Ridge
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    
    logger.info("Training baseline models...")
    
    baselines = {}
    
    # 1. Persistence baseline (last value)
    logger.info("  - Persistence baseline (last value carried forward)")
    persistence_pred = np.full_like(y_test, y_train[-1])
    baselines['persistence'] = {
        'r2': r2_score(y_test, persistence_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, persistence_pred)),
        'mae': mean_absolute_error(y_test, persistence_pred)
    }
    logger.info(f"    R²: {baselines['persistence']['r2']:.4f}")
    
    # 2. Mean baseline (historical mean)
    logger.info("  - Mean baseline (historical average)")
    mean_pred = np.full_like(y_test, y_train.mean())
    baselines['mean'] = {
        'r2': r2_score(y_test, mean_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, mean_pred)),
        'mae': mean_absolute_error(y_test, mean_pred)
    }
    logger.info(f"    R²: {baselines['mean']['r2']:.4f}")
    
    # 3. Linear regression baseline
    logger.info("  - Linear regression baseline (Ridge with top 20 features)")
    # Select top 20 features by correlation
    correlations = [abs(np.corrcoef(X_train[:, i], y_train)[0, 1]) for i in range(X_train.shape[1])]
    top_indices = np.argsort(correlations)[-20:]
    
    ridge = Ridge(alpha=1.0, random_state=42)
    ridge.fit(X_train[:, top_indices], y_train)
    ridge_pred = ridge.predict(X_test[:, top_indices])
    
    baselines['linear'] = {
        'r2': r2_score(y_test, ridge_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, ridge_pred)),
        'mae': mean_absolute_error(y_test, ridge_pred)
    }
    logger.info(f"    R²: {baselines['linear']['r2']:.4f}")
    
    # Find best baseline
    best_baseline = max(baselines.items(), key=lambda x: x[1]['r2'])
    logger.info(f"\n  Best baseline: {best_baseline[0]} (R² = {best_baseline[1]['r2']:.4f})")
    
    return baselines


def main():
    """Main training pipeline execution."""
    parser = argparse.ArgumentParser(
        description="Tanzania Climate Prediction - ML Training Pipeline"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="outputs/processed/master_dataset.csv",
        help="Path to master dataset CSV",
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="outputs/processed", 
        help="Directory for preprocessed features"
    )
    parser.add_argument(
        "--models-dir", 
        type=str, 
        default="outputs/models", 
        help="Directory to save trained models"
    )
    parser.add_argument(
        "--skip-preprocessing", 
        action="store_true", 
        help="Skip preprocessing if features already exist"
    )
    parser.add_argument(
        "--skip-feature-selection",
        action="store_true",
        help="Skip feature selection step"
    )
    parser.add_argument(
        "--skip-cv",
        action="store_true",
        help="Skip cross-validation (faster training)"
    )
    parser.add_argument(
        "--target-features",
        type=int,
        default=25,
        help="Target number of features after selection (default: 25 for 5:1 ratio)"
    )
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
    logger.info(f"Improvements enabled:")
    logger.info(f"  - Optimized feature engineering (reduced lags and windows)")
    logger.info(f"  - Feature selection (target: {args.target_features} features)")
    logger.info(f"  - Enhanced regularization")
    logger.info(f"  - Baseline model comparison")
    logger.info(f"  - Automated validation checks")
    if not args.skip_cv:
        logger.info(f"  - Time-series cross-validation")

    # ========================================================================
    # Step 1: Preprocessing with Optimized Feature Engineering
    # ========================================================================
    if not args.skip_preprocessing:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: PREPROCESSING WITH OPTIMIZED FEATURE ENGINEERING")
        logger.info("=" * 80)
        logger.info("Using optimized parameters:")
        logger.info("  - Lag periods: [1, 3, 6] (reduced from [1,3,6,12])")
        logger.info("  - Rolling windows: [3] (reduced from [3,6])")
        logger.info("  - Correlation removal: threshold 0.95")

        try:
            metadata = preprocess_pipeline(
                input_path=args.input, 
                output_dir=args.output_dir,
                lag_periods=[1, 3, 6],  # Optimized
                rolling_windows=[3]  # Optimized
            )
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

        # Prepare features and target
        numeric_cols = train_df.select_dtypes(include=["number"]).columns.tolist()
        exclude_cols = ["year", "month"]
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]

        # Determine target
        if "rainfall_mm" in feature_cols:
            target_col = "rainfall_mm"
            feature_cols.remove("rainfall_mm")
        else:
            target_col = feature_cols[-1]
            feature_cols = feature_cols[:-1]

        logger.info(f"Target variable: {target_col}")
        logger.info(f"Initial feature count: {len(feature_cols)}")

        # Handle missing values
        all_nan_cols = train_df[feature_cols].columns[train_df[feature_cols].isnull().all()].tolist()
        if all_nan_cols:
            logger.warning(f"Dropping {len(all_nan_cols)} all-NaN columns")
            feature_cols = [col for col in feature_cols if col not in all_nan_cols]

        # Fill NaN in features with median from training set
        X_train_full = train_df[feature_cols].fillna(train_df[feature_cols].median())
        X_val_full = val_df[feature_cols].fillna(train_df[feature_cols].median())
        X_test_full = test_df[feature_cols].fillna(train_df[feature_cols].median())
        
        # Fill NaN in target with median from training set
        target_median = train_df[target_col].median()
        if pd.isna(target_median):
            logger.warning(f"Target variable '{target_col}' has all NaN values in training set!")
            target_median = 0.0
        
        y_train = train_df[target_col].fillna(target_median).values
        y_val = val_df[target_col].fillna(target_median).values
        y_test = test_df[target_col].fillna(target_median).values
        
        logger.info(f"NaN handling: Filled {train_df[feature_cols].isnull().sum().sum()} feature NaNs with median")
        logger.info(f"NaN handling: Filled {train_df[target_col].isnull().sum()} target NaNs with median ({target_median:.2f})")

        logger.info("✓ Data loaded successfully")
        
        # ========================================================================
        # Step 2.5: Data Leakage Prevention
        # ========================================================================
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2.5: DATA LEAKAGE PREVENTION")
        logger.info("=" * 80)
        
        from utils.data_leakage_prevention import remove_leaky_features
        
        # Remove features that may cause data leakage
        X_train_clean, removed_features, removal_reasons = remove_leaky_features(
            X_train_full,
            target_name=target_col,
            y=pd.Series(y_train),
            strict=True,
            correlation_threshold=0.95
        )
        
        # Apply same removal to val and test sets
        X_val_full = X_val_full[X_train_clean.columns]
        X_test_full = X_test_full[X_train_clean.columns]
        X_train_full = X_train_clean
        
        logger.info(f"Removed {len(removed_features)} potentially leaky features")
        if removed_features:
            logger.info(f"Examples: {removed_features[:5]}")
        
        # Update feature_cols list
        feature_cols = X_train_full.columns.tolist()
        logger.info(f"Features after leakage prevention: {len(feature_cols)}")
        logger.info("✓ Leakage prevention completed")

    except Exception as e:
        logger.error(f"✗ Failed to load preprocessed data: {e}")
        raise

    # ========================================================================
    # Step 3: Feature Selection
    # ========================================================================
    if not args.skip_feature_selection:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: FEATURE SELECTION")
        logger.info("=" * 80)
        logger.info(f"Reducing features from {len(feature_cols)} to ~{args.target_features}")

        try:
            # Perform hybrid feature selection
            selection_result = select_features_hybrid(
                X_train_full,
                pd.Series(y_train),
                target_features=args.target_features,
                min_per_source=5
            )

            # Save feature selection results
            selection_result.save(f"{args.models_dir}/feature_selection_results.json")

            # Apply selection to all datasets
            X_train_selected = apply_feature_selection(X_train_full, selection_result.selected_features)
            X_val_selected = apply_feature_selection(X_val_full, selection_result.selected_features)
            X_test_selected = apply_feature_selection(X_test_full, selection_result.selected_features)
            
            # Get actual feature names (may be filtered if some were missing)
            feature_names = list(X_train_selected.columns)
            
            # Convert to numpy arrays
            X_train = X_train_selected.values
            X_val = X_val_selected.values
            X_test = X_test_selected.values

            logger.info(f"✓ Feature selection complete: {len(feature_names)} features selected")
            logger.info(f"  Source distribution: {selection_result.source_distribution}")

        except Exception as e:
            logger.error(f"✗ Feature selection failed: {e}")
            logger.warning("Continuing with all features...")
            X_train = X_train_full.values
            X_val = X_val_full.values
            X_test = X_test_full.values
            feature_names = feature_cols
    else:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: SKIPPING FEATURE SELECTION")
        logger.info("=" * 80)
        X_train = X_train_full.values
        X_val = X_val_full.values
        X_test = X_test_full.values
        feature_names = feature_cols

    logger.info(f"Final feature count: {len(feature_names)}")
    logger.info(f"Training samples: {len(X_train)}")
    logger.info(f"Feature-to-sample ratio: {len(X_train)/len(feature_names):.2f}:1")

    # ========================================================================
    # Step 4: Train Baseline Models
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: BASELINE MODEL TRAINING")
    logger.info("=" * 80)

    try:
        baselines = train_baseline_models(X_train, y_train, X_test, y_test)
        best_baseline_r2 = max(b['r2'] for b in baselines.values())
        logger.info("✓ Baseline models trained successfully")
    except Exception as e:
        logger.error(f"✗ Baseline training failed: {e}")
        baselines = {}
        best_baseline_r2 = None

    # ========================================================================
    # Step 5: Train Advanced Models with Enhanced Regularization
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 5: ADVANCED MODEL TRAINING (Enhanced Regularization)")
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
            train_rf=True,
            train_xgb=True,
            train_lstm=True,
            train_ensemble=True,
        )

        logger.info("✓ Model training completed successfully")

    except Exception as e:
        logger.error(f"✗ Model training failed: {e}")
        raise

    # ========================================================================
    # Step 5.5: Cross-Validation (if not skipped)
    # ========================================================================
    cv_results = {}
    if not args.skip_cv:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5.5: TIME-SERIES CROSS-VALIDATION")
        logger.info("=" * 80)
        logger.info("Running 5-fold time-series cross-validation for robust estimates...")
        
        try:
            from sklearn.ensemble import RandomForestRegressor
            import xgboost as xgb
            
            # Use ONLY training data for CV to avoid data leakage
            # CV should never see validation or test data
            X_cv = X_train
            y_cv = y_train
            
            logger.info(f"CV dataset: {len(X_cv)} samples, {X_cv.shape[1]} features")
            logger.info(f"Note: Using only training data for CV to prevent data leakage")
            
            # Cross-validate Random Forest
            logger.info("\n  Cross-validating Random Forest...")
            rf_model = RandomForestRegressor(
                n_estimators=200,
                max_depth=10,
                min_samples_split=10,
                min_samples_leaf=5,
                max_features='sqrt',
                random_state=42,
                n_jobs=-1
            )
            cv_rf = cross_validate_sklearn_model(
                rf_model, X_cv, y_cv,
                n_splits=5, test_size=20,
                gap=12,  # 12-month gap to prevent temporal leakage (matches train/val/test splits)
                model_name="Random Forest"
            )
            cv_results['random_forest'] = cv_rf.to_dict()
            logger.info(f"  ✓ RF CV R²: {cv_rf.r2_mean:.4f} ± {cv_rf.r2_std:.4f} (95% CI: [{cv_rf.r2_ci_lower:.4f}, {cv_rf.r2_ci_upper:.4f}])")
            
            # Cross-validate XGBoost
            logger.info("\n  Cross-validating XGBoost...")
            xgb_model = xgb.XGBRegressor(
                n_estimators=500,
                max_depth=4,
                learning_rate=0.01,
                subsample=0.8,
                colsample_bytree=0.8,
                min_child_weight=5,
                gamma=0.1,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=-1,
                verbosity=0
            )
            cv_xgb = cross_validate_sklearn_model(
                xgb_model, X_cv, y_cv,
                n_splits=5, test_size=20,
                gap=12,  # 12-month gap to prevent temporal leakage (matches train/val/test splits)
                model_name="XGBoost"
            )
            cv_results['xgboost'] = cv_xgb.to_dict()
            logger.info(f"  ✓ XGB CV R²: {cv_xgb.r2_mean:.4f} ± {cv_xgb.r2_std:.4f} (95% CI: [{cv_xgb.r2_ci_lower:.4f}, {cv_xgb.r2_ci_upper:.4f}])")
            
            # Cross-validate LSTM
            logger.info("\n  Cross-validating LSTM...")
            from models.lstm_model import LSTMModel
            from evaluation.cross_validation import time_series_cv_split, calculate_metrics, CrossValidationResult, calculate_confidence_intervals
            
            # Create CV splits with gap to prevent temporal leakage
            cv_splits = time_series_cv_split(
                n_samples=len(X_cv),
                n_splits=5,
                test_size=20,
                gap=12  # 12-month gap between train and test (matches train/val/test splits)
            )
            
            # Run LSTM CV manually (LSTM requires sequence preparation)
            fold_results = []
            r2_scores = []
            rmse_scores = []
            mae_scores = []
            
            for fold_idx, (train_idx, test_idx) in enumerate(cv_splits):
                logger.info(f"    Fold {fold_idx + 1}/5")
                
                X_train_fold, X_test_fold = X_cv[train_idx], X_cv[test_idx]
                y_train_fold, y_test_fold = y_cv[train_idx], y_cv[test_idx]
                
                try:
                    # Initialize LSTM model
                    lstm_fold = LSTMModel(model_name=f"lstm_cv_fold_{fold_idx}")
                    
                    # Train (LSTM.train() doesn't accept verbose parameter, it uses config)
                    lstm_fold.train(X_train_fold, y_train_fold)
                    
                    # Predict
                    y_pred_fold = lstm_fold.predict(X_test_fold)
                    
                    # Calculate metrics
                    metrics = calculate_metrics(y_test_fold, y_pred_fold)
                    
                    fold_results.append({
                        'fold': fold_idx,
                        'train_size': len(train_idx),
                        'test_size': len(test_idx),
                        **metrics
                    })
                    
                    r2_scores.append(metrics['r2'])
                    rmse_scores.append(metrics['rmse'])
                    mae_scores.append(metrics['mae'])
                    
                    logger.info(f"      R²: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.4f}")
                    
                except Exception as e:
                    logger.warning(f"      Fold {fold_idx + 1} failed: {e}")
                    fold_results.append({
                        'fold': fold_idx,
                        'train_size': len(train_idx),
                        'test_size': len(test_idx),
                        'error': str(e),
                        'r2': np.nan,
                        'rmse': np.nan,
                        'mae': np.nan,
                        'mape': np.nan
                    })
            
            # Calculate LSTM CV statistics
            r2_scores_clean = [s for s in r2_scores if not np.isnan(s)]
            if len(r2_scores_clean) > 0:
                r2_mean = np.mean(r2_scores_clean)
                r2_std = np.std(r2_scores_clean, ddof=1)
                r2_ci_lower, r2_ci_upper = calculate_confidence_intervals(r2_scores_clean)
                
                rmse_scores_clean = [s for s in rmse_scores if not np.isnan(s)]
                rmse_mean = np.mean(rmse_scores_clean)
                rmse_std = np.std(rmse_scores_clean, ddof=1)
                
                mae_scores_clean = [s for s in mae_scores if not np.isnan(s)]
                mae_mean = np.mean(mae_scores_clean)
                mae_std = np.std(mae_scores_clean, ddof=1)
                
                best_fold = int(np.argmax(r2_scores_clean))
                worst_fold = int(np.argmin(r2_scores_clean))
                
                cv_lstm = CrossValidationResult(
                    model_name="LSTM",
                    n_splits=5,
                    r2_mean=r2_mean,
                    r2_std=r2_std,
                    r2_ci_lower=r2_ci_lower,
                    r2_ci_upper=r2_ci_upper,
                    rmse_mean=rmse_mean,
                    rmse_std=rmse_std,
                    mae_mean=mae_mean,
                    mae_std=mae_std,
                    fold_results=fold_results,
                    best_fold=best_fold,
                    worst_fold=worst_fold
                )
                
                cv_results['lstm'] = cv_lstm.to_dict()
                logger.info(f"  ✓ LSTM CV R²: {cv_lstm.r2_mean:.4f} ± {cv_lstm.r2_std:.4f} (95% CI: [{cv_lstm.r2_ci_lower:.4f}, {cv_lstm.r2_ci_upper:.4f}])")
            else:
                logger.warning("  ✗ LSTM CV failed for all folds")
            
            # Cross-validate Ensemble (combine predictions from RF, XGBoost, LSTM)
            logger.info("\n  Cross-validating Ensemble...")
            
            # Check if we have CV results for all three models
            if 'random_forest' in cv_results and 'xgboost' in cv_results and 'lstm' in cv_results:
                ensemble_fold_results = []
                ensemble_r2_scores = []
                ensemble_rmse_scores = []
                ensemble_mae_scores = []
                
                # Ensemble weights
                weights = {'rf': 0.3, 'xgb': 0.4, 'lstm': 0.3}
                
                # Get fold results from each model
                rf_folds = cv_results['random_forest']['fold_results']
                xgb_folds = cv_results['xgboost']['fold_results']
                lstm_folds = cv_results['lstm']['fold_results']
                
                # For each fold, we need to recalculate ensemble predictions
                # Since we don't have the actual predictions stored, we'll need to re-run the models
                for fold_idx, (train_idx, test_idx) in enumerate(cv_splits):
                    logger.info(f"    Fold {fold_idx + 1}/5")
                    
                    X_train_fold, X_test_fold = X_cv[train_idx], X_cv[test_idx]
                    y_train_fold, y_test_fold = y_cv[train_idx], y_cv[test_idx]
                    
                    try:
                        # Train all three models on this fold
                        from sklearn.base import clone
                        
                        # RF predictions
                        rf_fold = clone(rf_model)
                        rf_fold.fit(X_train_fold, y_train_fold)
                        rf_pred = rf_fold.predict(X_test_fold)
                        
                        # XGBoost predictions
                        xgb_fold = clone(xgb_model)
                        xgb_fold.fit(X_train_fold, y_train_fold)
                        xgb_pred = xgb_fold.predict(X_test_fold)
                        
                        # LSTM predictions
                        lstm_fold = LSTMModel(model_name=f"lstm_ensemble_cv_fold_{fold_idx}")
                        lstm_fold.train(X_train_fold, y_train_fold)
                        lstm_pred = lstm_fold.predict(X_test_fold)
                        
                        # Combine predictions using ensemble weights
                        ensemble_pred = (weights['rf'] * rf_pred + 
                                       weights['xgb'] * xgb_pred + 
                                       weights['lstm'] * lstm_pred)
                        
                        # Calculate metrics for ensemble
                        metrics = calculate_metrics(y_test_fold, ensemble_pred)
                        
                        ensemble_fold_results.append({
                            'fold': fold_idx,
                            'train_size': len(train_idx),
                            'test_size': len(test_idx),
                            **metrics
                        })
                        
                        ensemble_r2_scores.append(metrics['r2'])
                        ensemble_rmse_scores.append(metrics['rmse'])
                        ensemble_mae_scores.append(metrics['mae'])
                        
                        logger.info(f"      R²: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.4f}")
                        
                    except Exception as e:
                        logger.warning(f"      Fold {fold_idx + 1} failed: {e}")
                        ensemble_fold_results.append({
                            'fold': fold_idx,
                            'train_size': len(train_idx),
                            'test_size': len(test_idx),
                            'error': str(e),
                            'r2': np.nan,
                            'rmse': np.nan,
                            'mae': np.nan,
                            'mape': np.nan
                        })
                
                # Calculate ensemble CV statistics
                ensemble_r2_clean = [s for s in ensemble_r2_scores if not np.isnan(s)]
                if len(ensemble_r2_clean) > 0:
                    ens_r2_mean = np.mean(ensemble_r2_clean)
                    ens_r2_std = np.std(ensemble_r2_clean, ddof=1)
                    ens_r2_ci_lower, ens_r2_ci_upper = calculate_confidence_intervals(ensemble_r2_clean)
                    
                    ensemble_rmse_clean = [s for s in ensemble_rmse_scores if not np.isnan(s)]
                    ens_rmse_mean = np.mean(ensemble_rmse_clean)
                    ens_rmse_std = np.std(ensemble_rmse_clean, ddof=1)
                    
                    ensemble_mae_clean = [s for s in ensemble_mae_scores if not np.isnan(s)]
                    ens_mae_mean = np.mean(ensemble_mae_clean)
                    ens_mae_std = np.std(ensemble_mae_clean, ddof=1)
                    
                    ens_best_fold = int(np.argmax(ensemble_r2_clean))
                    ens_worst_fold = int(np.argmin(ensemble_r2_clean))
                    
                    cv_ensemble = CrossValidationResult(
                        model_name="Ensemble",
                        n_splits=5,
                        r2_mean=ens_r2_mean,
                        r2_std=ens_r2_std,
                        r2_ci_lower=ens_r2_ci_lower,
                        r2_ci_upper=ens_r2_ci_upper,
                        rmse_mean=ens_rmse_mean,
                        rmse_std=ens_rmse_std,
                        mae_mean=ens_mae_mean,
                        mae_std=ens_mae_std,
                        fold_results=ensemble_fold_results,
                        best_fold=ens_best_fold,
                        worst_fold=ens_worst_fold
                    )
                    
                    cv_results['ensemble'] = cv_ensemble.to_dict()
                    logger.info(f"  ✓ Ensemble CV R²: {cv_ensemble.r2_mean:.4f} ± {cv_ensemble.r2_std:.4f} (95% CI: [{cv_ensemble.r2_ci_lower:.4f}, {cv_ensemble.r2_ci_upper:.4f}])")
                else:
                    logger.warning("  ✗ Ensemble CV failed for all folds")
            else:
                logger.warning("  ✗ Skipping Ensemble CV (missing individual model CV results)")
            
            # Save CV results
            import json
            with open(f"{args.models_dir}/cross_validation_results.json", 'w') as f:
                json.dump(cv_results, f, indent=2)
            
            logger.info("\n✓ Cross-validation completed")
            logger.info(f"  Results saved to {args.models_dir}/cross_validation_results.json")
            
        except Exception as e:
            logger.error(f"✗ Cross-validation failed: {e}")
            logger.warning("Continuing without CV results...")
            cv_results = {}
    else:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5.5: SKIPPING CROSS-VALIDATION")
        logger.info("=" * 80)

    # ========================================================================
    # Step 6: Automated Model Validation
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 6: AUTOMATED MODEL VALIDATION")
    logger.info("=" * 80)

    validation_reports = {}
    
    for model_name in ['random_forest', 'xgboost', 'lstm', 'ensemble']:
        if model_name in results['models'] and 'error' not in results['models'][model_name]:
            model_results = results['models'][model_name]
            
            # Extract metrics
            train_r2 = model_results.get('train_metrics', {}).get('r2', 0)
            val_r2 = model_results.get('val_metrics', {}).get('r2', 0)
            test_r2 = model_results.get('test_metrics', model_results.get('ensemble_metrics', {})).get('r2', 0)
            
            # Run validation
            report = validate_model(
                model_name=model_name,
                n_features=len(feature_names),
                n_train_samples=len(X_train),
                n_test_samples=len(X_test),
                train_r2=train_r2,
                val_r2=val_r2,
                test_r2=test_r2,
                baseline_r2=best_baseline_r2
            )
            
            validation_reports[model_name] = report
            
            # Save individual report
            save_validation_report(
                report,
                f"{args.models_dir}/validation_{model_name}.json"
            )
            
            # Print summary
            logger.info(f"\n{model_name.upper()} Validation:")
            logger.info(f"  Status: {report.overall_status.value.upper()}")
            logger.info(f"  Checks passed: {len(report.checks_passed)}")
            logger.info(f"  Warnings: {len(report.checks_warning)}")
            logger.info(f"  Failed: {len(report.checks_failed)}")

    logger.info("✓ Model validation completed")

    # ========================================================================
    # Step 7: Save Results
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("STEP 7: SAVING RESULTS")
    logger.info("=" * 80)

    try:
        # Add baseline, CV, and validation info to results
        results['baselines'] = baselines
        results['cross_validation'] = cv_results if cv_results else None
        results['feature_selection'] = {
            'original_features': len(feature_cols) if not args.skip_feature_selection else len(feature_names),
            'selected_features': len(feature_names),
            'reduction_pct': (1 - len(feature_names)/len(feature_cols)) * 100 if not args.skip_feature_selection else 0
        }
        results['validation_summary'] = {
            model_name: {
                'status': report.overall_status.value,
                'checks_passed': len(report.checks_passed),
                'checks_failed': len(report.checks_failed)
            }
            for model_name, report in validation_reports.items()
        }

        results_file = save_training_results(results, args.models_dir)
        logger.info(f"✓ Results saved to {results_file}")

    except Exception as e:
        logger.error(f"✗ Failed to save results: {e}")
        raise

    # ========================================================================
    # Final Summary
    # ========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("TRAINING PIPELINE COMPLETE")
    logger.info("=" * 80)
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"\nKey Improvements Applied:")
    logger.info(f"  ✓ Optimized feature engineering")
    logger.info(f"  ✓ Feature selection: {len(feature_cols)} → {len(feature_names)} features")
    logger.info(f"  ✓ Enhanced regularization")
    logger.info(f"  ✓ Baseline comparison")
    logger.info(f"  ✓ Automated validation")
    
    logger.info(f"\nBest Model Performance:")
    best_model = max(
        [(name, res.get('test_metrics', res.get('ensemble_metrics', {})).get('r2', 0))
         for name, res in results['models'].items() if 'error' not in res],
        key=lambda x: x[1]
    )
    logger.info(f"  Model: {best_model[0]}")
    logger.info(f"  Test R²: {best_model[1]:.4f}")
    if best_baseline_r2:
        logger.info(f"  Improvement over baseline: +{(best_model[1] - best_baseline_r2):.2%}")
    
    # Report CV results if available
    if cv_results:
        logger.info(f"\nCross-Validation Results (More Reliable):")
        for model_name, cv_result in cv_results.items():
            logger.info(f"  {model_name.upper()}:")
            logger.info(f"    R²: {cv_result['r2_mean']:.4f} ± {cv_result['r2_std']:.4f}")
            logger.info(f"    95% CI: [{cv_result['r2_ci_lower']:.4f}, {cv_result['r2_ci_upper']:.4f}]")
            logger.info(f"    RMSE: {cv_result['rmse_mean']:.4f} ± {cv_result['rmse_std']:.4f}")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
