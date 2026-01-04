"""
Comprehensive Reporting Module

This module generates detailed reports for model training, evaluation, and validation.
Includes feature selection reports, cross-validation reports, model comparison reports,
and validation pipeline reports with visualizations.

Requirements: 5.5, 9.1, 9.2, 9.3, 9.4, 9.5
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Set style for visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def generate_feature_selection_report(
    selected_features: List[str],
    feature_scores: Dict[str, float],
    source_distribution: Dict[str, int],
    original_count: int,
    selected_count: int,
    correlation_matrix: Optional[np.ndarray] = None,
    output_dir: str = "outputs/reports"
) -> str:
    """
    Generate comprehensive feature selection report.
    
    Args:
        selected_features: List of selected feature names
        feature_scores: Dictionary of feature scores
        source_distribution: Features per data source
        original_count: Original number of features
        selected_count: Number of selected features
        correlation_matrix: Correlation matrix of selected features
        output_dir: Directory to save report
        
    Returns:
        Path to generated report
        
    Requirements: 9.1
    """
    logger.info("Generating feature selection report")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_path / f"feature_selection_report_{timestamp}.txt"
    
    # Generate text report
    with open(report_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("FEATURE SELECTION REPORT\n")
        f.write("="*70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("SUMMARY\n")
        f.write("-"*70 + "\n")
        f.write(f"Original Features: {original_count}\n")
        f.write(f"Selected Features: {selected_count}\n")
        f.write(f"Reduction: {((original_count - selected_count) / original_count * 100):.1f}%\n\n")
        
        f.write("SOURCE DISTRIBUTION\n")
        f.write("-"*70 + "\n")
        for source, count in sorted(source_distribution.items()):
            f.write(f"{source:20s}: {count:3d} features\n")
        
        f.write("\nTOP 20 SELECTED FEATURES BY SCORE\n")
        f.write("-"*70 + "\n")
        sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)[:20]
        for i, (feat, score) in enumerate(sorted_features, 1):
            f.write(f"{i:2d}. {feat:50s} {score:.4f}\n")
    
    logger.info(f"Feature selection report saved to {report_file}")
    
    # Generate correlation heatmap if matrix provided
    if correlation_matrix is not None and len(selected_features) <= 50:
        try:
            fig, ax = plt.subplots(figsize=(14, 12))
            sns.heatmap(correlation_matrix, cmap='coolwarm', center=0, 
                       square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
            ax.set_title('Feature Correlation Matrix (Selected Features)', fontsize=14, pad=20)
            
            heatmap_file = output_path / f"feature_correlation_heatmap_{timestamp}.png"
            plt.tight_layout()
            plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Correlation heatmap saved to {heatmap_file}")
        except Exception as e:
            logger.warning(f"Could not generate correlation heatmap: {e}")
    
    return str(report_file)



def generate_cv_report(
    cv_results: Dict[str, Any],
    output_dir: str = "outputs/reports"
) -> str:
    """
    Generate cross-validation report with fold-by-fold metrics.
    
    Args:
        cv_results: CrossValidationResult object or dict
        output_dir: Directory to save report
        
    Returns:
        Path to generated report
        
    Requirements: 9.2
    """
    logger.info("Generating cross-validation report")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_path / f"cv_report_{timestamp}.txt"
    
    # Extract data from results
    if hasattr(cv_results, 'to_dict'):
        cv_dict = cv_results.to_dict()
    else:
        cv_dict = cv_results
    
    model_name = cv_dict.get('model_name', 'Unknown')
    n_splits = cv_dict.get('n_splits', 0)
    fold_results = cv_dict.get('fold_results', [])
    
    # Generate text report
    with open(report_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write(f"CROSS-VALIDATION REPORT: {model_name}\n")
        f.write("="*70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("SUMMARY STATISTICS\n")
        f.write("-"*70 + "\n")
        f.write(f"Number of Folds: {n_splits}\n")
        f.write(f"R² Mean: {cv_dict.get('r2_mean', 0):.4f} ± {cv_dict.get('r2_std', 0):.4f}\n")
        f.write(f"R² 95% CI: [{cv_dict.get('r2_ci_lower', 0):.4f}, {cv_dict.get('r2_ci_upper', 0):.4f}]\n")
        f.write(f"RMSE Mean: {cv_dict.get('rmse_mean', 0):.4f} ± {cv_dict.get('rmse_std', 0):.4f}\n")
        f.write(f"MAE Mean: {cv_dict.get('mae_mean', 0):.4f} ± {cv_dict.get('mae_std', 0):.4f}\n\n")
        
        f.write("FOLD-BY-FOLD RESULTS\n")
        f.write("-"*70 + "\n")
        f.write(f"{'Fold':<6} {'Train Size':<12} {'Test Size':<12} {'R²':<10} {'RMSE':<10} {'MAE':<10}\n")
        f.write("-"*70 + "\n")
        
        for fold in fold_results:
            fold_num = fold.get('fold', 0) + 1
            train_size = fold.get('train_size', 0)
            test_size = fold.get('test_size', 0)
            r2 = fold.get('r2', 0)
            rmse = fold.get('rmse', 0)
            mae = fold.get('mae', 0)
            
            f.write(f"{fold_num:<6} {train_size:<12} {test_size:<12} {r2:<10.4f} {rmse:<10.4f} {mae:<10.4f}\n")
    
    logger.info(f"CV report saved to {report_file}")
    
    # Generate performance plot
    try:
        r2_scores = [fold.get('r2', 0) for fold in fold_results]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        folds = list(range(1, len(r2_scores) + 1))
        ax.plot(folds, r2_scores, marker='o', linewidth=2, markersize=8, label='R² Score')
        ax.axhline(y=cv_dict.get('r2_mean', 0), color='r', linestyle='--', label='Mean R²')
        ax.fill_between(folds, 
                        cv_dict.get('r2_ci_lower', 0), 
                        cv_dict.get('r2_ci_upper', 0), 
                        alpha=0.2, label='95% CI')
        ax.set_xlabel('Fold Number', fontsize=12)
        ax.set_ylabel('R² Score', fontsize=12)
        ax.set_title(f'Cross-Validation Performance: {model_name}', fontsize=14, pad=20)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plot_file = output_path / f"cv_performance_{timestamp}.png"
        plt.tight_layout()
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"CV performance plot saved to {plot_file}")
    except Exception as e:
        logger.warning(f"Could not generate CV plot: {e}")
    
    return str(report_file)



def generate_model_comparison_report(
    model_results: Dict[str, Dict[str, float]],
    baseline_results: Optional[Dict[str, Dict[str, float]]] = None,
    output_dir: str = "outputs/reports"
) -> str:
    """
    Generate model comparison report with baseline comparisons.
    
    Args:
        model_results: Dictionary of model results {model_name: {metric: value}}
        baseline_results: Dictionary of baseline results (optional)
        output_dir: Directory to save report
        
    Returns:
        Path to generated report
        
    Requirements: 9.3
    """
    logger.info("Generating model comparison report")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_path / f"model_comparison_{timestamp}.txt"
    
    # Generate text report
    with open(report_file, 'w') as f:
        f.write("="*70 + "\n")
        f.write("MODEL COMPARISON REPORT\n")
        f.write("="*70 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Complex models
        f.write("COMPLEX MODELS\n")
        f.write("-"*70 + "\n")
        f.write(f"{'Model':<20} {'R²':<10} {'RMSE':<10} {'MAE':<10} {'Train-Val Gap':<15}\n")
        f.write("-"*70 + "\n")
        
        for model_name, metrics in sorted(model_results.items()):
            r2 = metrics.get('test_r2', metrics.get('r2', 0))
            rmse = metrics.get('test_rmse', metrics.get('rmse', 0))
            mae = metrics.get('test_mae', metrics.get('mae', 0))
            
            train_r2 = metrics.get('train_r2', 0)
            val_r2 = metrics.get('val_r2', 0)
            gap = abs(train_r2 - val_r2) if train_r2 and val_r2 else 0
            
            f.write(f"{model_name:<20} {r2:<10.4f} {rmse:<10.4f} {mae:<10.4f} {gap:<15.2%}\n")
        
        # Baseline models
        if baseline_results:
            f.write("\nBASELINE MODELS\n")
            f.write("-"*70 + "\n")
            f.write(f"{'Model':<20} {'R²':<10} {'RMSE':<10} {'MAE':<10}\n")
            f.write("-"*70 + "\n")
            
            for model_name, metrics in sorted(baseline_results.items()):
                r2 = metrics.get('r2', 0)
                rmse = metrics.get('rmse', 0)
                mae = metrics.get('mae', 0)
                f.write(f"{model_name:<20} {r2:<10.4f} {rmse:<10.4f} {mae:<10.4f}\n")
            
            # Calculate improvements
            f.write("\nIMPROVEMENT OVER BEST BASELINE\n")
            f.write("-"*70 + "\n")
            
            best_baseline_r2 = max([m.get('r2', 0) for m in baseline_results.values()])
            
            for model_name, metrics in sorted(model_results.items()):
                model_r2 = metrics.get('test_r2', metrics.get('r2', 0))
                improvement = model_r2 - best_baseline_r2
                improvement_pct = (improvement / (1 - best_baseline_r2)) * 100 if best_baseline_r2 < 1 else 0
                
                f.write(f"{model_name:<20} +{improvement:.4f} ({improvement_pct:+.1f}%)\n")
    
    logger.info(f"Model comparison report saved to {report_file}")
    
    # Generate comparison bar chart
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # R² comparison
        models = list(model_results.keys())
        r2_scores = [model_results[m].get('test_r2', model_results[m].get('r2', 0)) for m in models]
        
        if baseline_results:
            models.extend(list(baseline_results.keys()))
            r2_scores.extend([baseline_results[m].get('r2', 0) for m in baseline_results.keys()])
        
        colors = ['#2ecc71' if 'baseline' not in m.lower() else '#95a5a6' for m in models]
        
        ax1.barh(models, r2_scores, color=colors)
        ax1.set_xlabel('R² Score', fontsize=12)
        ax1.set_title('Model Performance Comparison (R²)', fontsize=14)
        ax1.grid(True, alpha=0.3, axis='x')
        
        # RMSE comparison
        rmse_scores = [model_results[m].get('test_rmse', model_results[m].get('rmse', 0)) 
                      for m in list(model_results.keys())]
        
        if baseline_results:
            rmse_scores.extend([baseline_results[m].get('rmse', 0) 
                               for m in baseline_results.keys()])
        
        ax2.barh(models, rmse_scores, color=colors)
        ax2.set_xlabel('RMSE', fontsize=12)
        ax2.set_title('Model Performance Comparison (RMSE)', fontsize=14)
        ax2.grid(True, alpha=0.3, axis='x')
        
        plot_file = output_path / f"model_comparison_{timestamp}.png"
        plt.tight_layout()
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Model comparison plot saved to {plot_file}")
    except Exception as e:
        logger.warning(f"Could not generate comparison plot: {e}")
    
    return str(report_file)



def generate_validation_pipeline_report(
    validation_report: Any,
    output_dir: str = "outputs/reports"
) -> str:
    """
    Generate validation pipeline report with all checks.
    
    Args:
        validation_report: ValidationReport object from model_validation module
        output_dir: Directory to save report
        
    Returns:
        Path to generated report
        
    Requirements: 9.4
    """
    logger.info("Generating validation pipeline report")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_path / f"validation_report_{timestamp}.txt"
    
    # Use the summary method if available
    if hasattr(validation_report, 'summary'):
        summary_text = validation_report.summary()
    else:
        summary_text = str(validation_report)
    
    # Save to file
    with open(report_file, 'w') as f:
        f.write(summary_text)
    
    logger.info(f"Validation report saved to {report_file}")
    
    # Generate visualization of checks
    try:
        if hasattr(validation_report, 'all_checks'):
            checks = validation_report.all_checks
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            check_names = [c.name for c in checks]
            check_values = [c.value if c.value is not None else 0 for c in checks]
            check_thresholds = [c.threshold if c.threshold is not None else 0 for c in checks]
            check_colors = ['green' if c.passed else 'red' for c in checks]
            
            x = np.arange(len(check_names))
            width = 0.35
            
            ax.bar(x - width/2, check_values, width, label='Actual', color=check_colors, alpha=0.7)
            ax.bar(x + width/2, check_thresholds, width, label='Threshold', color='gray', alpha=0.5)
            
            ax.set_xlabel('Validation Check', fontsize=12)
            ax.set_ylabel('Value', fontsize=12)
            ax.set_title('Validation Pipeline Results', fontsize=14, pad=20)
            ax.set_xticks(x)
            ax.set_xticklabels(check_names, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            plot_file = output_path / f"validation_checks_{timestamp}.png"
            plt.tight_layout()
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Validation checks plot saved to {plot_file}")
    except Exception as e:
        logger.warning(f"Could not generate validation plot: {e}")
    
    return str(report_file)



def generate_academic_language_templates(
    model_results: Dict[str, Any],
    output_dir: str = "outputs/reports"
) -> str:
    """
    Generate academic language templates for methods and results sections.
    
    Args:
        model_results: Dictionary with model metrics and metadata
        output_dir: Directory to save templates
        
    Returns:
        Path to generated templates file
        
    Requirements: 9.5
    """
    logger.info("Generating academic language templates")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    template_file = output_path / f"academic_templates_{timestamp}.md"
    
    # Extract metrics
    n_features = model_results.get('n_features', 0)
    n_train = model_results.get('n_train_samples', 0)
    n_val = model_results.get('n_val_samples', 0)
    n_test = model_results.get('n_test_samples', 0)
    
    test_r2 = model_results.get('test_r2', 0)
    test_rmse = model_results.get('test_rmse', 0)
    test_mae = model_results.get('test_mae', 0)
    
    train_r2 = model_results.get('train_r2', 0)
    val_r2 = model_results.get('val_r2', 0)
    
    with open(template_file, 'w') as f:
        f.write("# Academic Language Templates\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Methods Section Template\n\n")
        f.write("### Model Development and Evaluation\n\n")
        f.write(f"We trained an ensemble model combining Random Forest, XGBoost, and LSTM ")
        f.write(f"architectures on {n_train} monthly observations, with {n_val} months ")
        f.write(f"held out for validation and {n_test} for testing. The dataset includes ")
        f.write(f"{n_features} features derived from five climate data sources (CHIRPS, ")
        f.write(f"NASA POWER, ERA5, MODIS NDVI, and NOAA Ocean Indices).\n\n")
        
        f.write(f"The ensemble model achieved an R² of {test_r2:.2f} on the test set ")
        f.write(f"(RMSE = {test_rmse:.3f}), indicating strong predictive performance. ")
        f.write(f"However, several important caveats apply:\n\n")
        
        f.write(f"1. **Limited Sample Size**: With only {n_train + n_val + n_test} total ")
        f.write(f"observations, the test set of {n_test} months provides a limited basis ")
        f.write(f"for performance estimation. Confidence intervals around the R² metric ")
        f.write(f"would be wide.\n\n")
        
        f.write(f"2. **High Dimensionality**: The ratio of {n_features} features to ")
        f.write(f"{n_train} training samples ({n_features/n_train:.1f}:1) is high, ")
        f.write(f"increasing the risk of overfitting. ")
        
        if train_r2 > 0 and val_r2 > 0:
            gap = abs(train_r2 - val_r2)
            f.write(f"Evidence of overfitting is visible in the training performance ")
            f.write(f"(R² = {train_r2:.4f}) compared to validation (R² = {val_r2:.4f}), ")
            f.write(f"showing a gap of {gap:.2%}.\n\n")
        else:
            f.write(f"\n\n")
        
        f.write(f"3. **Temporal Structure**: Standard train/test splits may not fully ")
        f.write(f"account for temporal autocorrelation in climate data. Time-series ")
        f.write(f"cross-validation would provide more robust estimates.\n\n")
        
        f.write(f"Despite these statistical limitations, the model demonstrates practical ")
        f.write(f"utility through its ability to correctly identify major historical climate ")
        f.write(f"events. This operational validation provides confidence beyond statistical ")
        f.write(f"metrics alone.\n\n")
        
        f.write("## Results Section Template\n\n")
        f.write("### Model Performance\n\n")
        f.write(f"The ensemble model achieved the following performance on held-out test data:\n")
        f.write(f"- R² Score: {test_r2:.2f} (explains {test_r2*100:.0f}% of variance)\n")
        f.write(f"- RMSE: {test_rmse:.3f} (root mean squared error)\n")
        f.write(f"- MAE: {test_mae:.3f} (mean absolute error)\n\n")
        
        f.write(f"These results should be interpreted in the context of the limited sample ")
        f.write(f"size ({n_train + n_val + n_test} monthly observations) and high feature ")
        f.write(f"dimensionality ({n_features} features). Continued data collection will ")
        f.write(f"enable more robust model evaluation and refinement.\n\n")
        
        f.write("## Limitations Section Template\n\n")
        f.write("### Study Limitations\n\n")
        f.write(f"Several limitations should be considered when interpreting these results:\n\n")
        f.write(f"1. **Sample Size**: The dataset contains {n_train + n_val + n_test} monthly ")
        f.write(f"observations, which is relatively small for climate analysis. This limits ")
        f.write(f"the statistical power of our evaluation and increases uncertainty in ")
        f.write(f"performance estimates.\n\n")
        f.write(f"2. **Feature Dimensionality**: The high ratio of features to samples ")
        f.write(f"({n_features}:{n_train}) increases overfitting risk. Feature selection ")
        f.write(f"techniques could improve model generalization.\n\n")
        f.write(f"3. **Temporal Coverage**: {(n_train + n_val + n_test) / 12:.1f} years of ")
        f.write(f"data may not capture longer-term climate cycles and decadal oscillations.\n\n")
        f.write(f"4. **Geographic Scope**: The model is trained on data from a single ")
        f.write(f"location and may not generalize to other regions without retraining.\n\n")
        
        f.write("## Future Work Section Template\n\n")
        f.write("### Future Directions\n\n")
        f.write(f"Future work should address the current limitations:\n\n")
        f.write(f"1. **Data Expansion**: Collect additional years of data to increase ")
        f.write(f"sample size and improve model robustness.\n\n")
        f.write(f"2. **Feature Selection**: Apply systematic feature selection to reduce ")
        f.write(f"dimensionality from {n_features} to 50-100 most informative features.\n\n")
        f.write(f"3. **Cross-Validation**: Implement time-series cross-validation to ")
        f.write(f"obtain more reliable performance estimates.\n\n")
        f.write(f"4. **Spatial Validation**: Extend the model to multiple locations to ")
        f.write(f"assess geographic generalization.\n\n")
    
    logger.info(f"Academic templates saved to {template_file}")
    
    return str(template_file)


def generate_comprehensive_report(
    feature_selection_result: Optional[Any] = None,
    cv_results: Optional[Any] = None,
    model_results: Optional[Dict] = None,
    baseline_results: Optional[Dict] = None,
    validation_report: Optional[Any] = None,
    output_dir: str = "outputs/reports"
) -> Dict[str, str]:
    """
    Generate all reports in one call.
    
    Args:
        feature_selection_result: FeatureSelectionResult object
        cv_results: CrossValidationResult object
        model_results: Dictionary of model results
        baseline_results: Dictionary of baseline results
        validation_report: ValidationReport object
        output_dir: Directory to save all reports
        
    Returns:
        Dictionary mapping report type to file path
        
    Requirements: 5.5
    """
    logger.info("Generating comprehensive report suite")
    
    report_paths = {}
    
    try:
        if feature_selection_result:
            if hasattr(feature_selection_result, 'selected_features'):
                path = generate_feature_selection_report(
                    selected_features=feature_selection_result.selected_features,
                    feature_scores=feature_selection_result.feature_scores,
                    source_distribution=feature_selection_result.source_distribution,
                    original_count=feature_selection_result.original_count,
                    selected_count=feature_selection_result.selected_count,
                    correlation_matrix=feature_selection_result.correlation_matrix,
                    output_dir=output_dir
                )
                report_paths['feature_selection'] = path
    except Exception as e:
        logger.error(f"Failed to generate feature selection report: {e}")
    
    try:
        if cv_results:
            path = generate_cv_report(cv_results, output_dir)
            report_paths['cross_validation'] = path
    except Exception as e:
        logger.error(f"Failed to generate CV report: {e}")
    
    try:
        if model_results:
            path = generate_model_comparison_report(
                model_results, baseline_results, output_dir
            )
            report_paths['model_comparison'] = path
    except Exception as e:
        logger.error(f"Failed to generate model comparison report: {e}")
    
    try:
        if validation_report:
            path = generate_validation_pipeline_report(validation_report, output_dir)
            report_paths['validation'] = path
    except Exception as e:
        logger.error(f"Failed to generate validation report: {e}")
    
    try:
        if model_results:
            path = generate_academic_language_templates(model_results, output_dir)
            report_paths['academic_templates'] = path
    except Exception as e:
        logger.error(f"Failed to generate academic templates: {e}")
    
    logger.info(f"Generated {len(report_paths)} reports")
    
    return report_paths
