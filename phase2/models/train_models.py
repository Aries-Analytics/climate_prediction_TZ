"""
Model Training Orchestration

This module orchestrates the training of all models (RF, XGBoost, LSTM, Ensemble)
and manages the training workflow.

Requirements: 2.6, 2.8, 2.9, 2.10
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json
import time
from datetime import datetime
import logging

from models.random_forest_model import RandomForestModel
from models.xgboost_model import XGBoostModel
from models.lstm_model import LSTMModel
from models.ensemble_model import EnsembleModel

logger = logging.getLogger(__name__)


def train_all_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_names: Optional[List[str]] = None,
    models_dir: str = "outputs/models",
    train_rf: bool = True,
    train_xgb: bool = True,
    train_lstm: bool = True,
    train_ensemble: bool = True
) -> Dict[str, Any]:
    """
    Train all models sequentially and return results.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_val: Validation features
        y_val: Validation targets
        X_test: Test features
        y_test: Test targets
        feature_names: Optional list of feature names
        models_dir: Directory to save trained models
        train_rf: Whether to train Random Forest
        train_xgb: Whether to train XGBoost
        train_lstm: Whether to train LSTM
        train_ensemble: Whether to train Ensemble
        
    Returns:
        Dict[str, Any]: Training results for all models
    """
    logger.info("=" * 80)
    logger.info("STARTING MODEL TRAINING ORCHESTRATION")
    logger.info("=" * 80)
    
    # Create models directory
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)
    
    # Store results
    results = {
        'training_start_time': datetime.now().isoformat(),
        'data_shapes': {
            'train': X_train.shape,
            'val': X_val.shape,
            'test': X_test.shape
        },
        'models': {}
    }
    
    trained_models = {}
    
    # ========================================================================
    # Train Random Forest
    # ========================================================================
    if train_rf:
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING RANDOM FOREST MODEL")
        logger.info("=" * 80)
        
        try:
            rf_model = RandomForestModel(model_name="random_forest_climate")
            
            if feature_names:
                rf_model.set_feature_names(feature_names)
            
            # Train
            rf_results = rf_model.train(X_train, y_train, X_val, y_val)
            
            # Test evaluation
            y_test_pred = rf_model.predict(X_test)
            test_metrics = rf_model.calculate_metrics(y_test, y_test_pred)
            rf_results['test_metrics'] = test_metrics
            
            # Save model
            rf_model.save(models_dir)
            
            # Save feature importance
            if feature_names:
                rf_model.save_feature_importance(models_dir, feature_names)
            
            results['models']['random_forest'] = rf_results
            trained_models['rf'] = rf_model
            
            logger.info(f"✓ Random Forest training complete")
            logger.info(f"  Test R²: {test_metrics['r2']:.4f}")
            logger.info(f"  Test RMSE: {test_metrics['rmse']:.4f}")
            
        except Exception as e:
            logger.error(f"✗ Random Forest training failed: {e}")
            results['models']['random_forest'] = {'error': str(e)}
    
    # ========================================================================
    # Train XGBoost
    # ========================================================================
    if train_xgb:
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING XGBOOST MODEL")
        logger.info("=" * 80)
        
        try:
            xgb_model = XGBoostModel(model_name="xgboost_climate")
            
            if feature_names:
                xgb_model.set_feature_names(feature_names)
            
            # Train with early stopping
            xgb_results = xgb_model.train(X_train, y_train, X_val, y_val, early_stopping_rounds=10)
            
            # Test evaluation
            y_test_pred = xgb_model.predict(X_test)
            test_metrics = xgb_model.calculate_metrics(y_test, y_test_pred)
            xgb_results['test_metrics'] = test_metrics
            
            # Save model
            xgb_model.save(models_dir)
            
            # Save feature importance
            if feature_names:
                xgb_model.save_feature_importance(models_dir, feature_names, importance_type='gain')
            
            results['models']['xgboost'] = xgb_results
            trained_models['xgb'] = xgb_model
            
            logger.info(f"✓ XGBoost training complete")
            logger.info(f"  Test R²: {test_metrics['r2']:.4f}")
            logger.info(f"  Test RMSE: {test_metrics['rmse']:.4f}")
            
        except Exception as e:
            logger.error(f"✗ XGBoost training failed: {e}")
            results['models']['xgboost'] = {'error': str(e)}
    
    # ========================================================================
    # Train LSTM
    # ========================================================================
    if train_lstm:
        logger.info("\n" + "=" * 80)
        logger.info("TRAINING LSTM MODEL")
        logger.info("=" * 80)
        
        try:
            lstm_model = LSTMModel(model_name="lstm_climate")
            
            if feature_names:
                lstm_model.set_feature_names(feature_names)
            
            # Train with early stopping
            lstm_results = lstm_model.train(X_train, y_train, X_val, y_val)
            
            # Test evaluation
            y_test_pred = lstm_model.predict(X_test)
            # Only evaluate on valid predictions (exclude NaN padding)
            valid_mask = ~np.isnan(y_test_pred)
            if valid_mask.sum() > 0:
                test_metrics = lstm_model.calculate_metrics(y_test[valid_mask], y_test_pred[valid_mask])
                lstm_results['test_metrics'] = test_metrics
                
                logger.info(f"✓ LSTM training complete")
                logger.info(f"  Test R²: {test_metrics['r2']:.4f}")
                logger.info(f"  Test RMSE: {test_metrics['rmse']:.4f}")
            else:
                logger.warning("LSTM produced no valid predictions on test set")
                lstm_results['test_metrics'] = {'error': 'No valid predictions'}
            
            # Save model
            lstm_model.save(models_dir)
            
            results['models']['lstm'] = lstm_results
            trained_models['lstm'] = lstm_model
            
        except Exception as e:
            logger.error(f"✗ LSTM training failed: {e}")
            results['models']['lstm'] = {'error': str(e)}
    
    # ========================================================================
    # Train Ensemble
    # ========================================================================
    if train_ensemble and len(trained_models) >= 3:
        logger.info("\n" + "=" * 80)
        logger.info("CREATING ENSEMBLE MODEL")
        logger.info("=" * 80)
        
        try:
            ensemble_model = EnsembleModel(model_name="ensemble_climate")
            
            # Load base models
            ensemble_model.load_base_models(
                trained_models['rf'],
                trained_models['xgb'],
                trained_models['lstm']
            )
            
            # Evaluate ensemble on test set
            ensemble_results_dict = ensemble_model.evaluate_ensemble(X_test, y_test)
            
            # Save ensemble config
            ensemble_model.save(models_dir)
            
            results['models']['ensemble'] = {
                'individual_results': ensemble_results_dict,
                'ensemble_metrics': ensemble_results_dict.get('ensemble', {})
            }
            
            if 'ensemble' in ensemble_results_dict:
                metrics = ensemble_results_dict['ensemble']
                logger.info(f"✓ Ensemble model complete")
                logger.info(f"  Test R²: {metrics['r2']:.4f}")
                logger.info(f"  Test RMSE: {metrics['rmse']:.4f}")
            
        except Exception as e:
            logger.error(f"✗ Ensemble creation failed: {e}")
            results['models']['ensemble'] = {'error': str(e)}
    
    elif train_ensemble:
        logger.warning("Skipping ensemble - not all base models were trained successfully")
    
    # ========================================================================
    # Summary
    # ========================================================================
    results['training_end_time'] = datetime.now().isoformat()
    
    logger.info("\n" + "=" * 80)
    logger.info("MODEL TRAINING SUMMARY")
    logger.info("=" * 80)
    
    for model_name, model_results in results['models'].items():
        if 'error' in model_results:
            logger.info(f"{model_name.upper()}: FAILED - {model_results['error']}")
        elif 'test_metrics' in model_results:
            metrics = model_results['test_metrics']
            if 'error' not in metrics:
                logger.info(f"{model_name.upper()}: R²={metrics['r2']:.4f}, "
                          f"RMSE={metrics['rmse']:.4f}, MAE={metrics['mae']:.4f}")
        elif model_name == 'ensemble' and 'ensemble_metrics' in model_results:
            metrics = model_results['ensemble_metrics']
            if 'error' not in metrics:
                logger.info(f"{model_name.upper()}: R²={metrics['r2']:.4f}, "
                          f"RMSE={metrics['rmse']:.4f}, MAE={metrics['mae']:.4f}")
    
    logger.info("=" * 80)
    
    return results


def save_training_results(results: Dict[str, Any], save_dir: str, 
                          experiment_name: Optional[str] = None) -> str:
    """
    Save training results and metadata to JSON file.
    
    Args:
        results: Training results dictionary
        save_dir: Directory to save results
        experiment_name: Optional experiment name
        
    Returns:
        str: Path to saved results file
    """
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    if experiment_name:
        filename = f"training_results_{experiment_name}.json"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_results_{timestamp}.json"
    
    results_file = save_path / filename
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, tuple):
            return list(obj)
        return obj
    
    # Save results
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=convert_types)
    
    logger.info(f"Saved training results to {results_file}")
    
    return str(results_file)


def load_trained_models(models_dir: str) -> Dict[str, Any]:
    """
    Load all trained models from directory.
    
    Args:
        models_dir: Directory containing saved models
        
    Returns:
        Dict[str, Any]: Dictionary of loaded models
    """
    models_path = Path(models_dir)
    
    if not models_path.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")
    
    loaded_models = {}
    
    # Load Random Forest
    rf_path = models_path / "random_forest_climate.pkl"
    if rf_path.exists():
        rf_model = RandomForestModel(model_name="random_forest_climate")
        rf_model.load(str(rf_path))
        loaded_models['rf'] = rf_model
        logger.info(f"Loaded Random Forest model from {rf_path}")
    
    # Load XGBoost
    xgb_path = models_path / "xgboost_climate.pkl"
    if xgb_path.exists():
        xgb_model = XGBoostModel(model_name="xgboost_climate")
        xgb_model.load(str(xgb_path))
        loaded_models['xgb'] = xgb_model
        logger.info(f"Loaded XGBoost model from {xgb_path}")
    
    # Load LSTM
    lstm_path = models_path / "lstm_climate.keras"
    if lstm_path.exists():
        lstm_model = LSTMModel(model_name="lstm_climate")
        lstm_model.load(str(lstm_path))
        loaded_models['lstm'] = lstm_model
        logger.info(f"Loaded LSTM model from {lstm_path}")
    
    # Load Ensemble
    ensemble_path = models_path / "ensemble_climate_config.json"
    if ensemble_path.exists() and len(loaded_models) >= 3:
        ensemble_model = EnsembleModel(model_name="ensemble_climate")
        ensemble_model.load(str(ensemble_path))
        ensemble_model.load_base_models(
            loaded_models['rf'],
            loaded_models['xgb'],
            loaded_models['lstm']
        )
        loaded_models['ensemble'] = ensemble_model
        logger.info(f"Loaded Ensemble model from {ensemble_path}")
    
    logger.info(f"Loaded {len(loaded_models)} models")
    
    return loaded_models
