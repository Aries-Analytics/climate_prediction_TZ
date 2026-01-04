"""
Spatial Generalization Validation - Task 15
Leave-One-Location-Out Cross-Validation (LOLO CV)

Tests if models can predict rainfall in unseen locations based on training from other locations.
Target: Held-out location R² ≥ 0.75
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import json
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns

from utils.logger import setup_logging
import logging

logger = logging.getLogger(__name__)


def load_combined_data():
    """Load and combine train, val, test datasets"""
    logger.info("Loading combined dataset...")
    
    # Load all splits
    train_df = pd.read_csv("outputs/processed/features_train.csv")
    val_df = pd.read_csv("outputs/processed/features_val.csv")
    test_df = pd.read_csv("outputs/processed/features_test.csv")
    
    # Combine
    combined_df = pd.concat([train_df, val_df, test_df], ignore_index=True)
    
    logger.info(f"Combined dataset: {len(combined_df)} samples")
    logger.info(f"Locations: {sorted(combined_df['location'].unique())}")
    
    return combined_df


def load_feature_list():
    """Load selected features from feature selection results"""
    with open("outputs/models/feature_selection_results.json", 'r') as f:
        feature_selection = json.load(f)
    
    # Handle both dict and list formats
    selected_features = feature_selection.get('selected_features', {})
    if isinstance(selected_features, dict):
        feature_cols = list(selected_features.keys())
    elif isinstance(selected_features, list):
        feature_cols = selected_features
    else:
        raise ValueError(f"Unexpected selected_features format: {type(selected_features)}")
    
    logger.info(f"Loaded {len(feature_cols)} selected features")
    
    return feature_cols


def train_model(model_name, X_train, y_train):
    """Train a single model using sklearn/xgboost directly"""
    if model_name == 'random_forest':
        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
    elif model_name == 'xgboost':
        model = xgb.XGBRegressor(
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
    else:
        raise ValueError(f"Unknown model: {model_name}")
    
    # Train
    model.fit(X_train, y_train)
    
    return model


def calculate_metrics(y_true, y_pred):
    """Calculate evaluation metrics"""
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    
    # MAPE (handle division by zero)
    mape = np.mean(np.abs((y_true - y_pred) / np.where(y_true != 0, y_true, 1))) * 100
    
    return {
        'r2': r2,
        'rmse': rmse,
        'mae': mae,
        'mape': mape,
        'n_samples': len(y_true)
    }


def spatial_cross_validation(data, feature_cols, target_col, models_to_test):
    """
    Run Leave-One-Location-Out Cross-Validation
    
    For each location:
    - Train on 4 other locations
    - Test on held-out location
    """
    locations = sorted(data['location'].unique())
    results = {}
    
    logger.info("="*80)
    logger.info("LEAVE-ONE-LOCATION-OUT CROSS-VALIDATION")
    logger.info("="*80)
    logger.info(f"Locations: {locations}")
    logger.info(f"Models: {models_to_test}")
    logger.info("")
    
    for hold_out_loc in locations:
        logger.info(f"\n{'='*80}")
        logger.info(f"FOLD: Holding out {hold_out_loc.upper()}")
        logger.info(f"{'='*80}")
        
        # Split data
        train_data = data[data['location'] != hold_out_loc].copy()
        test_data = data[data['location'] == hold_out_loc].copy()
        
        train_locs = sorted(train_data['location'].unique())
        logger.info(f"Training locations: {train_locs}")
        logger.info(f"Training samples: {len(train_data)}")
        logger.info(f"Test samples: {len(test_data)}")
        logger.info("")
        
        # Prepare data
        X_train = train_data[feature_cols].fillna(train_data[feature_cols].median()).values
        y_train = train_data[target_col].fillna(train_data[target_col].median()).values
        
        X_test = test_data[feature_cols].fillna(train_data[feature_cols].median()).values  # Use train median
        y_test = test_data[target_col].fillna(train_data[target_col].median()).values
        
        # Train and evaluate each model
        for model_name in models_to_test:
            logger.info(f"  Training {model_name}...")
            
            try:
                model = train_model(model_name, X_train, y_train)
                y_pred = model.predict(X_test)
                
                metrics = calculate_metrics(y_test, y_pred)
                
                logger.info(f"    R² = {metrics['r2']:.4f}")
                logger.info(f"    RMSE = {metrics['rmse']:.4f}")
                logger.info(f"    MAE = {metrics['mae']:.4f}")
                
                # Store results
                key = f"{model_name}_{hold_out_loc}"
                results[key] = {
                    'model': model_name,
                    'hold_out_location': hold_out_loc,
                    'train_locations': train_locs,
                    'metrics': metrics
                }
                
            except Exception as e:
                logger.error(f"  Failed for {model_name}: {e}")
                results[f"{model_name}_{hold_out_loc}"] = None
    
    return results


def aggregate_results(results):
    """Aggregate LOLO CV results by model"""
    logger.info("\n" + "="*80)
    logger.info("SPATIAL CV SUMMARY")
    logger.info("="*80)
    logger.info("")
    
    # Group by model
    model_summaries = {}
    
    for model_name in ['random_forest', 'xgboost']:
        model_results = [v for k, v in results.items() 
                        if v and v['model'] == model_name]
        
        if not model_results:
            continue
        
        r2_scores = [r['metrics']['r2'] for r in model_results]
        rmse_scores = [r['metrics']['rmse'] for r in model_results]
        mae_scores = [r['metrics']['mae'] for r in model_results]
        
        summary = {
            'model': model_name,
            'n_folds': len(model_results),
            'mean_r2': np.mean(r2_scores),
            'std_r2': np.std(r2_scores),
            'min_r2': np.min(r2_scores),
            'max_r2': np.max(r2_scores),
            'mean_rmse': np.mean(rmse_scores),
            'mean_mae': np.mean(mae_scores),
            'per_location': {r['hold_out_location']: r['metrics']['r2'] 
                           for r in model_results}
        }
        
        model_summaries[model_name] = summary
        
        logger.info(f"{model_name.upper()}:")
        logger.info(f"  Mean R² = {summary['mean_r2']:.4f} ± {summary['std_r2']:.4f}")
        logger.info(f"  95% CI = [{summary['mean_r2'] - 1.96*summary['std_r2']:.4f}, "
                   f"{summary['mean_r2'] + 1.96*summary['std_r2']:.4f}]")
        logger.info(f"  Range = [{summary['min_r2']:.4f}, {summary['max_r2']:.4f}]")
        logger.info(f"  RMSE = {summary['mean_rmse']:.4f}")
        logger.info(f"  MAE = {summary['mean_mae']:.4f}")
        logger.info("")
        
        # Per-location breakdown
        logger.info(f"  Per-location R²:")
        for loc, r2 in sorted(summary['per_location'].items()):
            status = "✓" if r2 >= 0.75 else "✗"
            logger.info(f"    {loc:20s}: {r2:.4f} {status}")
        logger.info("")
    
    return model_summaries


def create_visualization(results, output_path):
    """Create visualization of spatial CV results"""
    logger.info(f"Creating visualization: {output_path}")
    
    # Prepare data for plotting
    plot_data = []
    for key, result in results.items():
        if result:
            plot_data.append({
                'Model': result['model'].replace('_', ' ').title(),
                'Location': result['hold_out_location'],
                'R²': result['metrics']['r2']
            })
    
    df = pd.DataFrame(plot_data)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Grouped bar plot
    locations = sorted(df['Location'].unique())
    models = sorted(df['Model'].unique())
    x = np.arange(len(locations))
    width = 0.35
    
    for i, model in enumerate(models):
        model_data = df[df['Model'] == model]
        r2_values = [model_data[model_data['Location'] == loc]['R²'].values[0] 
                    for loc in locations]
        ax.bar(x + i*width, r2_values, width, label=model,
              color=['#2ecc71', '#3498db'][i])
    
    # Add target line
    ax.axhline(y=0.75, color='r', linestyle='--', label='Target (0.75)', linewidth=2)
    
    # Formatting
    ax.set_xlabel('Held-Out Location', fontsize=12, fontweight='bold')
    ax.set_ylabel('R² Score', fontsize=12, fontweight='bold')
    ax.set_title('Leave-One-Location-Out Cross-Validation Results', 
                fontsize=14, fontweight='bold')
    ax.set_xticks(x + width/2)
    ax.set_xticklabels(locations, rotation=45, ha='right')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 1.0)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info("✓ Visualization created")


def save_results(results, summaries, output_dir):
    """Save results to JSON and CSV"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results (JSON)
    results_file = output_dir / "spatial_cv_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"✓ Saved detailed results to {results_file}")
    
    # Save summary (CSV)
    summary_data = []
    for model_name, summary in summaries.items():
        for loc, r2 in summary['per_location'].items():
            summary_data.append({
                'Model': model_name,
                'Held_Out_Location': loc,
                'R2': r2,
                'Mean_R2': summary['mean_r2'],
                'Std_R2': summary['std_r2']
            })
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = output_dir / "spatial_cv_summary.csv"
    summary_df.to_csv(summary_file, index=False)
    logger.info(f"✓ Saved summary to {summary_file}")
    
    # Create visualization
    plot_file = output_dir / "spatial_cv_plot.png"
    create_visualization(results, plot_file)


def main():
    """Main execution"""
    setup_logging(logging.INFO)
    
    logger.info("="*80)
    logger.info("SPATIAL GENERALIZATION VALIDATION - TASK 15")
    logger.info("Leave-One-Location-Out Cross-Validation")
    logger.info("="*80)
    logger.info("")
    
    # Load data
    data = load_combined_data()
    feature_cols = load_feature_list()
    target_col = 'rainfall_mm'
    
    # Remove target from features if present
    if target_col in feature_cols:
        feature_cols.remove(target_col)
    
    # Models to test (excluding LSTM due to sequence requirements)
    models_to_test = ['random_forest', 'xgboost']
    
    logger.info(f"Features: {len(feature_cols)}")
    logger.info(f"Target: {target_col}")
    logger.info(f"Models: {models_to_test}")
    logger.info("")
    
    # Run spatial CV
    results = spatial_cross_validation(data, feature_cols, target_col, models_to_test)
    
    # Aggregate results
    summaries = aggregate_results(results)
    
    # Check targets
    logger.info("="*80)
    logger.info("TARGET VALIDATION")
    logger.info("="*80)
    logger.info("")
    
    for model_name, summary in summaries.items():
        logger.info(f"{model_name.upper()}:")
        
        # Check mean R² target
        if summary['mean_r2'] >= 0.75:
            logger.info(f"  ✓ Mean R² ({summary['mean_r2']:.4f}) meets target (≥0.75)")
        else:
            logger.info(f"  ✗ Mean R² ({summary['mean_r2']:.4f}) below target (≥0.75)")
        
        # Check stability target
        if summary['std_r2'] < 0.10:
            logger.info(f"  ✓ Std R² ({summary['std_r2']:.4f}) meets stability target (<0.10)")
        else:
            logger.info(f"  ✗ Std R² ({summary['std_r2']:.4f}) exceeds stability target (<0.10)")
        
        # Check minimum location
        if summary['min_r2'] >= 0.70:
            logger.info(f"  ✓ Min R² ({summary['min_r2']:.4f}) acceptable (≥0.70)")
        else:
            logger.info(f"  ⚠ Min R² ({summary['min_r2']:.4f}) below 0.70")
        
        logger.info("")
    
    # Save results
    output_dir = "outputs/evaluation/spatial_cv"
    save_results(results, summaries, output_dir)
    
    logger.info("="*80)
    logger.info("SPATIAL CV COMPLETE!")
    logger.info(f"Results saved to: {output_dir}")
    logger.info("="*80)


if __name__ == "__main__":
    main()
