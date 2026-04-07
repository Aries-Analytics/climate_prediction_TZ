"""
Verify Data Leakage in Trained Models

This script checks if trained models contain features that may cause data leakage.
It loads the most recent model and analyzes its features for potential leakage.

Usage:
    python verify_data_leakage.py
"""

import os
import sys
import json
import glob
from pathlib import Path

# Add project root to Python path (scripts/verification/ is two levels below phase2/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.data_leakage_prevention import detect_target_related_features

# Use print for output since logger might not be configured
def log_info(msg):
    print(msg)

def log_warning(msg):
    print(f"⚠️  {msg}")

def log_error(msg):
    print(f"❌ {msg}")


def load_model_features():
    """Load feature names and importance scores from saved files."""
    features = []
    feature_importance = {}
    
    # Try to load from feature_selection_results.json
    feature_selection_file = "outputs/models/feature_selection_results.json"
    if os.path.exists(feature_selection_file):
        try:
            with open(feature_selection_file, 'r') as f:
                selection_results = json.load(f)
            
            features = selection_results.get('selected_features', [])
            feature_importance = selection_results.get('feature_scores', {})
            
            log_info(f"Loaded {len(features)} features from {feature_selection_file}")
        except Exception as e:
            log_error(f"Error loading feature selection results: {e}")
    
    # If no features found, try loading from CSV files
    if not features:
        # Try Random Forest importance
        rf_importance_file = "outputs/models/random_forest_climate_feature_importance.csv"
        if os.path.exists(rf_importance_file):
            try:
                import pandas as pd
                df = pd.read_csv(rf_importance_file)
                features = df['feature'].tolist()
                feature_importance = dict(zip(df['feature'], df['importance']))
                log_info(f"Loaded {len(features)} features from {rf_importance_file}")
            except Exception as e:
                log_error(f"Error loading RF importance: {e}")
        
        # Try XGBoost importance if RF not found
        if not features:
            xgb_importance_file = "outputs/models/xgboost_climate_feature_importance_gain.csv"
            if os.path.exists(xgb_importance_file):
                try:
                    import pandas as pd
                    df = pd.read_csv(xgb_importance_file)
                    features = df['feature'].tolist()
                    feature_importance = dict(zip(df['feature'], df['importance']))
                    log_info(f"Loaded {len(features)} features from {xgb_importance_file}")
                except Exception as e:
                    log_error(f"Error loading XGBoost importance: {e}")
    
    return features, feature_importance


def verify_leakage(features, feature_importance=None, target_name='rainfall_mm'):
    """
    Verify if features contain data leakage.
    
    Args:
        features: List of feature names
        feature_importance: Dict of feature importance scores (optional)
        target_name: Name of target variable
    
    Returns:
        Dict with verification results
    """
    log_info("=" * 80)
    log_info("DATA LEAKAGE VERIFICATION")
    log_info("=" * 80)
    
    # Detect leaky features
    leaky_features, safe_features = detect_target_related_features(
        features,
        target_name,
        strict=True
    )
    
    total_features = len(features)
    num_leaky = len(leaky_features)
    num_safe = len(safe_features)
    
    # Calculate percentages
    pct_leaky = (num_leaky / total_features * 100) if total_features > 0 else 0
    pct_safe = (num_safe / total_features * 100) if total_features > 0 else 0
    
    # Print summary
    log_info(f"\nTotal features: {total_features}")
    log_info(f"Leaky features: {num_leaky} ({pct_leaky:.1f}%)")
    log_info(f"Safe features: {num_safe} ({pct_safe:.1f}%)")
    
    # Print leaky features with importance if available
    if leaky_features:
        log_warning("\nLEAKY FEATURES DETECTED:")
        log_info("-" * 80)
        
        # Sort by importance if available
        if feature_importance:
            leaky_with_importance = [
                (feat, feature_importance.get(feat, 0.0))
                for feat in leaky_features
            ]
            leaky_with_importance.sort(key=lambda x: x[1], reverse=True)
            
            for i, (feat, importance) in enumerate(leaky_with_importance, 1):
                marker = "⚠️ WORST OFFENDER" if i == 1 else ""
                log_warning(f"{i:2d}. {feat:40s} (importance: {importance:.4f}) {marker}")
        else:
            for i, feat in enumerate(leaky_features, 1):
                log_warning(f"{i:2d}. {feat}")
        
        log_info("-" * 80)
        log_error(f"VALIDATION FAILED: {num_leaky} leaky features found")
        log_info("These features may be causing data leakage and inflating model performance.")
        log_info("\nRecommendation: Retrain model with leakage prevention:")
        log_info("  python train_pipeline.py --skip-preprocessing --target-features 25")
    else:
        log_info("\n✅ NO DATA LEAKAGE DETECTED")
        log_info("All features appear to be safe from obvious data leakage.")
    
    # Print safe features summary
    if safe_features:
        log_info(f"\n✓ Safe features ({num_safe}):")
        log_info("-" * 80)
        for i, feat in enumerate(safe_features[:10], 1):  # Show first 10
            importance = feature_importance.get(feat, 0.0) if feature_importance else None
            if importance is not None:
                log_info(f"{i:2d}. {feat:40s} (importance: {importance:.4f})")
            else:
                log_info(f"{i:2d}. {feat}")
        
        if len(safe_features) > 10:
            log_info(f"... and {len(safe_features) - 10} more safe features")
    
    log_info("=" * 80)
    
    return {
        'total_features': total_features,
        'leaky_features': leaky_features,
        'safe_features': safe_features,
        'num_leaky': num_leaky,
        'num_safe': num_safe,
        'pct_leaky': pct_leaky,
        'pct_safe': pct_safe,
        'has_leakage': num_leaky > 0
    }


def main():
    """Main verification function."""
    # Load features
    features, feature_importance = load_model_features()
    
    if not features:
        logger.error("Could not load features from model files.")
        logger.error("Please ensure you have trained a model first.")
        logger.error("Run: python train_pipeline.py")
        return 1
    
    # Verify leakage
    results = verify_leakage(features, feature_importance)
    
    # Return exit code based on results
    return 1 if results['has_leakage'] else 0


if __name__ == "__main__":
    exit(main())
