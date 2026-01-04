"""
Performance Analysis Script - Tasks 14.3-14.4
Calculates train-validation gap and per-location performance
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from models.train_models import load_trained_models

print("="*80)
print("TASK 14.3: TRAIN-VALIDATION GAP ANALYSIS")
print("="*80)
print()

# Load training results
results_file = "outputs/models/training_results_20251229_171138.json"
with open(results_file, 'r') as f:
    results = json.load(f)

# Calculate gaps
print("Train-Validation Gap (Target: <5%)")
print("-" * 50)

gaps = {}
model_keys = {
    'random_forest': 'Random Forest',
    'xgboost': 'XGBoost',
    'lstm': 'LSTM',
    'ensemble': 'Ensemble'
}

for model_name, display_name in model_keys.items():
    model_results = results['models'].get(model_name, {})
    if not model_results:
        print(f"{display_name:15s}: No results found")
        continue
        
    train_r2 = model_results['metrics']['train']['r2']
    val_r2 = model_results['metrics']['validation']['r2']
    gap = abs(train_r2 - val_r2)
    gaps[model_name] = gap
    
    status = "✓ PASS" if gap < 0.05 else "✗ FAIL"
    print(f"{display_name:15s}: Train={train_r2:.4f}, Val={val_r2:.4f}, Gap={gap:.4f} {status}")

print()
print(f"Average Gap: {np.mean(list(gaps.values())):.4f}")
print(f"Max Gap: {max(gaps.values()):.4f} ({[k for k, v in gaps.items() if v == max(gaps.values())][0]})")
print()

# Summary
all_pass = all(g < 0.05 for g in gaps.values())
if all_pass:
    print("✓ ALL MODELS PASS: Train-val gap < 5%")
else:
    print("⚠ SOME MODELS FAIL: Train-val gap ≥ 5%")

print()
print("="*80)
print("TASK 14.4: PER-LOCATION PERFORMANCE ANALYSIS")
print("="*80)
print()

# Load test data with location column
test_df = pd.read_csv("outputs/processed/features_test.csv")

if 'location' not in test_df.columns:
    print("ERROR: No location column in test data!")
    sys.exit(1)

# Load feature selection results
with open("outputs/models/feature_selection_results.json", 'r') as f:
    feature_selection = json.load(f)
feature_cols = list(feature_selection['selected_features'].keys())

# Remove target from features if present
target_col = 'rainfall_mm'
if target_col in feature_cols:
    feature_cols.remove(target_col)

# Load models
models = load_trained_models("outputs/models")

print(f"Locations in test set: {sorted(test_df['location'].unique())}")
print(f"Total test samples: {len(test_df)}")
print()

# Calculate per-location performance for each model
location_performance = {}

for loc in sorted(test_df['location'].unique()):
    loc_df = test_df[test_df['location'] == loc]
    
    # Prepare data
    X_loc = loc_df[feature_cols].fillna(loc_df[feature_cols].median()).values
    y_loc = loc_df[target_col].fillna(loc_df[target_col].median()).values
    
    print(f"\n{loc.upper()} ({len(loc_df)} samples)")
    print("-" * 50)
    
    location_performance[loc] = {}
    
    for model_name, model in models.items():
        try:
            y_pred = model.predict(X_loc)
            
            # Handle LSTM NaN padding
            if hasattr(model, 'sequence_length'):
                valid_mask = ~np.isnan(y_pred)
                if valid_mask.sum() > 0:
                    y_pred = y_pred[valid_mask]
                    y_loc_valid = y_loc[valid_mask]
                else:
                    print(f"  {model_name:12s}: No valid predictions")
                    continue
            else:
                y_loc_valid = y_loc
            
            r2 = r2_score(y_loc_valid, y_pred)
            rmse = np.sqrt(mean_squared_error(y_loc_valid, y_pred))
            mae = mean_absolute_error(y_loc_valid, y_pred)
            
            location_performance[loc][model_name] = {
                'r2': r2,
                'rmse': rmse,
                'mae': mae,
                'samples': len(y_loc_valid)
            }
            
            print(f"  {model_name:12s}: R²={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f}")
            
        except Exception as e:
            print(f"  {model_name:12s}: ERROR - {e}")
            location_performance[loc][model_name] = None

# Summary statistics
print()
print("="*80)
print("LOCATION PERFORMANCE SUMMARY")
print("="*80)
print()

for model_name in ['rf', 'xgb', 'lstm', 'ensemble']:
    r2_scores = [perf[model_name]['r2'] for perf in location_performance.values() 
                 if model_name in perf and perf[model_name] is not None]
    
    if r2_scores:
        print(f"{model_name.upper():12s}: Mean R²={np.mean(r2_scores):.4f}, "
              f"Std={np.std(r2_scores):.4f}, "
              f"Min={min(r2_scores):.4f}, Max={max(r2_scores):.4f}")

# Identify problem locations
print()
print("Problem Locations (R² < 0.75):")
print("-" * 50)
problem_found = False
for loc, perf in location_performance.items():
    for model_name, metrics in perf.items():
        if metrics and metrics['r2'] < 0.75:
            print(f"  {loc} - {model_name}: R²={metrics['r2']:.4f}")
            problem_found = True

if not problem_found:
    print("  ✓ No problem locations found!")

# Save results
output_file = "outputs/evaluation/latest/per_location_performance.json"
with open(output_file, 'w') as f:
    json.dump({
        'train_val_gaps': gaps,
        'location_performance': location_performance
    }, f, indent=2)

print()
print(f"✓ Results saved to {output_file}")
