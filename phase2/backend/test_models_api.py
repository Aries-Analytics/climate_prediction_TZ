"""
Test script to verify the models API returns CV and feature selection data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Change to backend directory so relative paths work
os.chdir(os.path.dirname(__file__))

from app.services.model_service import _load_latest_training_results

def test_load_training_results():
    """Test loading CV and feature selection data"""
    print("Testing _load_latest_training_results()...")
    
    cv_data, feature_data = _load_latest_training_results()
    
    print("\n=== Cross-Validation Data ===")
    if cv_data:
        for model_name, cv_metrics in cv_data.items():
            print(f"\n{model_name}:")
            print(f"  R² Mean: {cv_metrics.get('r2_mean')}")
            print(f"  R² Std: {cv_metrics.get('r2_std')}")
            print(f"  R² CI: [{cv_metrics.get('r2_ci_lower')}, {cv_metrics.get('r2_ci_upper')}]")
            print(f"  RMSE Mean: {cv_metrics.get('rmse_mean')}")
            print(f"  N Splits: {cv_metrics.get('n_splits')}")
    else:
        print("  No CV data found")
    
    print("\n=== Feature Selection Data ===")
    if feature_data:
        print(f"  Selected Features: {feature_data.get('selected_features')}")
        print(f"  Original Features: {feature_data.get('original_features')}")
        print(f"  Feature-to-Sample Ratio: {feature_data.get('feature_to_sample_ratio'):.2f}:1")
    else:
        print("  No feature selection data found")
    
    print("\n✅ Test complete!")
    
    return cv_data, feature_data

if __name__ == "__main__":
    test_load_training_results()
