"""
Experiment Tracking Module

This module implements experiment tracking functionality to log, compare,
and retrieve model training experiments.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import json
import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Experiment Tracking (Task 10.1)
# ============================================================================

def create_experiment_id(prefix: str = "exp") -> str:
    """
    Create a unique experiment ID.
    
    Args:
        prefix: Prefix for the experiment ID
        
    Returns:
        str: Unique experiment ID
        
    Requirements: 7.1
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_id = f"{prefix}_{timestamp}"
    
    return experiment_id


def log_experiment(experiment_id: str, experiment_data: Dict[str, Any],
                  log_file: str = "outputs/experiments/experiment_log.jsonl") -> str:
    """
    Log experiment details to a JSONL file.
    
    Args:
        experiment_id: Unique experiment identifier
        experiment_data: Dictionary containing experiment details
        log_file: Path to the experiment log file
        
    Returns:
        str: Path to the log file
        
    Requirements: 7.2
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add experiment ID and timestamp
    experiment_record = {
        'experiment_id': experiment_id,
        'timestamp': datetime.now().isoformat(),
        **experiment_data
    }
    
    # Append to JSONL file
    with open(log_file, 'a') as f:
        f.write(json.dumps(experiment_record, default=str) + '\n')
    
    logger.info(f"Logged experiment {experiment_id} to {log_file}")
    
    return str(log_file)


# ============================================================================
# Experiment Comparison (Task 10.2)
# ============================================================================

def load_experiments(log_file: str = "outputs/experiments/experiment_log.jsonl") -> pd.DataFrame:
    """
    Load all experiments from the log file.
    
    Args:
        log_file: Path to the experiment log file
        
    Returns:
        pd.DataFrame: DataFrame containing all experiments
        
    Requirements: 7.3
    """
    log_path = Path(log_file)
    
    if not log_path.exists():
        logger.warning(f"Experiment log file not found: {log_file}")
        return pd.DataFrame()
    
    # Read JSONL file
    experiments = []
    with open(log_file, 'r') as f:
        for line in f:
            if line.strip():
                experiments.append(json.loads(line))
    
    if not experiments:
        logger.warning("No experiments found in log file")
        return pd.DataFrame()
    
    df = pd.DataFrame(experiments)
    
    logger.info(f"Loaded {len(df)} experiments from {log_file}")
    
    return df


def compare_experiments(log_file: str = "outputs/experiments/experiment_log.jsonl",
                       metric: str = 'r2', ascending: bool = False) -> pd.DataFrame:
    """
    Compare experiments and rank by specified metric.
    
    Args:
        log_file: Path to the experiment log file
        metric: Metric to rank by (default: 'r2')
        ascending: Sort order (False for descending, True for ascending)
        
    Returns:
        pd.DataFrame: Ranked experiments
        
    Requirements: 7.4
    """
    df = load_experiments(log_file)
    
    if df.empty:
        return df
    
    # Try to find the metric in nested dictionaries
    metric_column = None
    
    # Check if metric exists as a direct column
    if metric in df.columns:
        metric_column = metric
    else:
        # Check in nested structures (e.g., models.random_forest.test_metrics.r2)
        for col in df.columns:
            if isinstance(df[col].iloc[0], dict):
                # Expand nested dictionary
                expanded = pd.json_normalize(df[col])
                for expanded_col in expanded.columns:
                    if metric in expanded_col:
                        # Add expanded column to dataframe
                        df[f"{col}.{expanded_col}"] = expanded[expanded_col]
                        metric_column = f"{col}.{expanded_col}"
                        break
            if metric_column:
                break
    
    if metric_column is None:
        logger.warning(f"Metric '{metric}' not found in experiments")
        return df
    
    # Sort by metric
    df_sorted = df.sort_values(metric_column, ascending=ascending)
    
    logger.info(f"Ranked {len(df_sorted)} experiments by {metric}")
    
    return df_sorted


def get_best_model(log_file: str = "outputs/experiments/experiment_log.jsonl",
                  metric: str = 'r2') -> Optional[Dict[str, Any]]:
    """
    Get the best performing model based on specified metric.
    
    Args:
        log_file: Path to the experiment log file
        metric: Metric to optimize (default: 'r2', higher is better)
        
    Returns:
        Optional[Dict[str, Any]]: Best experiment record or None
        
    Requirements: 7.5
    """
    df = compare_experiments(log_file, metric=metric, ascending=False)
    
    if df.empty:
        logger.warning("No experiments found")
        return None
    
    best_experiment = df.iloc[0].to_dict()
    
    logger.info(f"Best experiment: {best_experiment.get('experiment_id', 'unknown')}")
    
    return best_experiment


def generate_comparison_report(log_file: str = "outputs/experiments/experiment_log.jsonl",
                              output_file: str = "outputs/experiments/comparison_report.md") -> str:
    """
    Generate a comparison summary report for all experiments.
    
    Args:
        log_file: Path to the experiment log file
        output_file: Path to save the comparison report
        
    Returns:
        str: Path to the saved report
        
    Requirements: 7.5
    """
    df = load_experiments(log_file)
    
    if df.empty:
        logger.warning("No experiments to compare")
        return ""
    
    # Create output directory
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate report
    report = []
    report.append("# Experiment Comparison Report\n")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append(f"Total Experiments: {len(df)}\n")
    report.append("\n---\n\n")
    
    # Summary statistics
    report.append("## Summary Statistics\n\n")
    
    # Try to extract metrics from nested structures
    metrics_found = []
    for col in df.columns:
        if 'metrics' in col.lower() or col in ['r2', 'rmse', 'mae', 'mape']:
            if df[col].dtype in ['float64', 'int64']:
                metrics_found.append(col)
    
    if metrics_found:
        report.append("| Metric | Mean | Std | Min | Max |\n")
        report.append("|--------|------|-----|-----|-----|\n")
        
        for metric in metrics_found:
            mean_val = df[metric].mean()
            std_val = df[metric].std()
            min_val = df[metric].min()
            max_val = df[metric].max()
            report.append(f"| {metric} | {mean_val:.4f} | {std_val:.4f} | {min_val:.4f} | {max_val:.4f} |\n")
    
    report.append("\n---\n\n")
    
    # Top 5 experiments
    report.append("## Top 5 Experiments\n\n")
    
    # Try to rank by R² if available
    ranked_df = df
    if 'r2' in df.columns:
        ranked_df = df.sort_values('r2', ascending=False)
    
    report.append("| Rank | Experiment ID | Timestamp |\n")
    report.append("|------|---------------|------------|\n")
    
    for idx, row in ranked_df.head(5).iterrows():
        rank = idx + 1
        exp_id = row.get('experiment_id', 'unknown')
        timestamp = row.get('timestamp', 'unknown')
        report.append(f"| {rank} | {exp_id} | {timestamp} |\n")
    
    report.append("\n---\n\n")
    
    # All experiments table
    report.append("## All Experiments\n\n")
    report.append(f"Total: {len(df)} experiments\n\n")
    
    # Select key columns for display
    display_cols = ['experiment_id', 'timestamp']
    for col in df.columns:
        if col not in display_cols and len(display_cols) < 8:
            display_cols.append(col)
    
    # Create markdown table
    if display_cols:
        report.append("| " + " | ".join(display_cols) + " |\n")
        report.append("|" + "|".join(["---"] * len(display_cols)) + "|\n")
        
        for _, row in df.iterrows():
            values = []
            for col in display_cols:
                val = row.get(col, '')
                if isinstance(val, (dict, list)):
                    val = str(val)[:50] + "..." if len(str(val)) > 50 else str(val)
                elif isinstance(val, float):
                    val = f"{val:.4f}"
                values.append(str(val))
            report.append("| " + " | ".join(values) + " |\n")
    
    # Write report
    with open(output_file, 'w') as f:
        f.writelines(report)
    
    logger.info(f"Generated comparison report: {output_file}")
    
    return str(output_file)


# ============================================================================
# Convenience Functions
# ============================================================================

def log_training_experiment(experiment_name: str, model_results: Dict[str, Any],
                           config: Dict[str, Any], additional_info: Optional[Dict[str, Any]] = None,
                           log_file: str = "outputs/experiments/experiment_log.jsonl") -> str:
    """
    Convenience function to log a training experiment.
    
    Args:
        experiment_name: Name of the experiment
        model_results: Results from model training
        config: Configuration used for training
        additional_info: Additional information to log
        log_file: Path to the experiment log file
        
    Returns:
        str: Experiment ID
    """
    experiment_id = create_experiment_id(prefix=experiment_name)
    
    experiment_data = {
        'name': experiment_name,
        'config': config,
        'results': model_results
    }
    
    if additional_info:
        experiment_data.update(additional_info)
    
    log_experiment(experiment_id, experiment_data, log_file)
    
    return experiment_id
