"""
Evaluation Engine for Tanzania Climate Prediction Models
Provides comprehensive model evaluation including seasonal performance analysis
"""

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from utils.logger import get_logger

logger = get_logger()


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate performance metrics for regression models.

    Args:
        y_true: Actual values
        y_pred: Predicted values

    Returns:
        Dictionary containing R², RMSE, MAE, and MAPE
    """
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    # Calculate metrics
    # R² requires at least 2 samples to calculate variance
    if len(y_true) >= 2:
        r2 = r2_score(y_true, y_pred)
    else:
        r2 = None  # Use None instead of NaN for better JSON serialization
        logger.warning(f"Cannot calculate R² with only {len(y_true)} sample(s). Need at least 2 samples.")

    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)

    # Calculate MAPE (avoiding division by zero)
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100 if mask.any() else None

    return {"r2_score": r2, "rmse": rmse, "mae": mae, "mape": mape}


def calculate_quantile_predictions(
    predictions_list: list,
    quantiles: Optional[list] = None
) -> Dict[str, np.ndarray]:
    """
    Calculate quantile predictions for uncertainty quantification.
    
    This function takes predictions from multiple models or bootstrap samples
    and calculates specified quantiles to create prediction intervals.
    
    Args:
        predictions_list: List of prediction arrays from different models/samples
                         Each array should have shape (n_samples,)
        quantiles: List of quantiles to calculate (default: [0.025, 0.5, 0.975] for 95% CI)
    
    Returns:
        Dictionary mapping quantile names to prediction arrays
        Example: {'q2.5': array([...]), 'q50': array([...]), 'q97.5': array([...])}
    
    Example:
        >>> rf_pred = model_rf.predict(X_test)
        >>> xgb_pred = model_xgb.predict(X_test)
        >>> lstm_pred = model_lstm.predict(X_test)
        >>> quantiles = calculate_quantile_predictions([rf_pred, xgb_pred, lstm_pred])
        >>> # Now you have 95% prediction intervals
        >>> lower_bound = quantiles['q2.5']
        >>> median = quantiles['q50']
        >>> upper_bound = quantiles['q97.5']
    """
    if quantiles is None:
        quantiles = [0.025, 0.5, 0.975]  # 95% prediction interval + median
    
    # Validate inputs
    if not predictions_list:
        raise ValueError("predictions_list cannot be empty")
    
    if not all(isinstance(pred, np.ndarray) for pred in predictions_list):
        raise TypeError("All predictions must be numpy arrays")
    
    # Check all predictions have same length
    n_samples = len(predictions_list[0])
    if not all(len(pred) == n_samples for pred in predictions_list):
        raise ValueError("All prediction arrays must have the same length")
    
    # Stack predictions: shape (n_models, n_samples)
    predictions_array = np.stack(predictions_list, axis=0)
    
    # Calculate quantiles along model axis (axis=0)
    quantile_results = {}
    
    for q in quantiles:
        if not 0 <= q <= 1:
            raise ValueError(f"Quantile {q} must be between 0 and 1")
        
        # Calculate quantile across models for each sample
        quantile_pred = np.quantile(predictions_array, q, axis=0)
        
        # Create key name (e.g., 0.025 -> 'q2.5', 0.5 -> 'q50')
        if q == 0.5:
            key = "q50"
        else:
            key = f"q{q*100:.1f}".replace('.0', '')
        
        quantile_results[key] = quantile_pred
    
    logger.info(f"Calculated {len(quantiles)} quantiles for {n_samples} samples from {len(predictions_list)} models")
    
    return quantile_results


def validate_prediction_intervals(
    y_true: np.ndarray,
    lower_bound: np.ndarray,
    upper_bound: np.ndarray,
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Validate prediction interval coverage.
    
    Checks if the actual coverage of prediction intervals matches the expected
    confidence level. For a 95% interval, approximately 95% of true values
    should fall within the interval.
    
    Args:
        y_true: Actual values
        lower_bound: Lower bound of prediction interval
        upper_bound: Upper bound of prediction interval
        confidence_level: Expected confidence level (default: 0.95)
    
    Returns:
        Dictionary with validation metrics:
        - coverage: Actual proportion of values within interval
        - expected_coverage: Expected confidence level
        - coverage_error: Difference between actual and expected
        - n_samples: Number of samples
        - n_within_interval: Number of samples within interval
    
    Example:
        >>> quantiles = calculate_quantile_predictions([pred1, pred2, pred3])
        >>> validation = validate_prediction_intervals(
        ...     y_true, quantiles['q2.5'], quantiles['q97.5'], confidence_level=0.95
        ... )
        >>> print(f"Coverage: {validation['coverage']:.2%}")
    """
    # Validate inputs
    if len(y_true) != len(lower_bound) or len(y_true) != len(upper_bound):
        raise ValueError("All arrays must have the same length")
    
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")
    
    # Check if values fall within interval
    within_interval = (y_true >= lower_bound) & (y_true <= upper_bound)
    
    # Calculate coverage
    n_within = np.sum(within_interval)
    n_total = len(y_true)
    actual_coverage = n_within / n_total
    
    # Calculate error
    coverage_error = actual_coverage - confidence_level
    
    results = {
        "coverage": float(actual_coverage),
        "expected_coverage": float(confidence_level),
        "coverage_error": float(coverage_error),
        "n_samples": int(n_total),
        "n_within_interval": int(n_within),
        "interval_width_mean": float(np.mean(upper_bound - lower_bound)),
        "interval_width_std": float(np.std(upper_bound - lower_bound))
    }
    
    logger.info(
        f"Prediction interval validation: "
        f"Coverage={actual_coverage:.2%} (expected={confidence_level:.2%}), "
        f"Error={coverage_error:+.2%}"
    )
    
    return results


def evaluate_by_season(
    y_true: np.ndarray, y_pred: np.ndarray, dates: pd.Series, target_name: str = "target"
) -> pd.DataFrame:
    """
    Calculate performance metrics separately for each season.

    Seasons are defined for Tanzania:
    - Short rains: October-December (months 10, 11, 12)
    - Long rains: March-May (months 3, 4, 5)
    - Dry season: June-September, January-February (months 1, 2, 6, 7, 8, 9)

    Args:
        y_true: Actual values
        y_pred: Predicted values
        dates: Date series (must be datetime)
        target_name: Name of the target variable for reporting

    Returns:
        DataFrame with metrics by season
    """
    logger.info(f"Evaluating {target_name} performance by season...")

    # Convert dates to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(dates):
        dates = pd.to_datetime(dates)

    # Extract month from dates
    # Handle both Series and DatetimeIndex
    if isinstance(dates, pd.DatetimeIndex):
        months = pd.Series(dates.month, index=dates)
    else:
        months = dates.dt.month

    # Define season mapping
    def get_season(month: int) -> str:
        if month in [10, 11, 12]:
            return "Short Rains"
        elif month in [3, 4, 5]:
            return "Long Rains"
        else:  # months 1, 2, 6, 7, 8, 9
            return "Dry Season"

    # Create season labels
    seasons = months.apply(get_season)

    # Create DataFrame for analysis
    eval_df = pd.DataFrame({"actual": y_true, "predicted": y_pred, "season": seasons})

    # Calculate metrics for each season
    results = []
    for season in ["Short Rains", "Long Rains", "Dry Season"]:
        season_data = eval_df[eval_df["season"] == season]

        if len(season_data) == 0:
            logger.warning(f"No data found for season: {season}")
            continue

        if len(season_data) < 2:
            logger.warning(
                f"Only {len(season_data)} sample(s) for {season}. "
                f"R² cannot be calculated. Consider using more test data."
            )

        metrics = calculate_metrics(season_data["actual"].values, season_data["predicted"].values)

        results.append(
            {
                "season": season,
                "n_samples": len(season_data),
                "r2_score": metrics["r2_score"],
                "rmse": metrics["rmse"],
                "mae": metrics["mae"],
                "mape": metrics["mape"],
            }
        )

        # Format R² display
        r2_str = f"{metrics['r2_score']:.3f}" if metrics["r2_score"] is not None else "N/A"
        logger.info(
            f"  {season}: R²={r2_str}, RMSE={metrics['rmse']:.3f}, "
            f"MAE={metrics['mae']:.3f}, n={len(season_data)}"
        )

    # Create results DataFrame
    results_df = pd.DataFrame(results)

    # Add target name to results
    results_df.insert(0, "target", target_name)

    return results_df


def plot_predictions_vs_actual(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    save_path: str,
    target_name: str = "Target Variable",
    title: Optional[str] = None,
) -> None:
    """
    Create scatter plot comparing predicted vs actual values.

    Args:
        y_true: Actual values
        y_pred: Predicted values
        save_path: Path to save the plot
        target_name: Name of target variable for axis labels
        title: Optional custom title
    """
    from pathlib import Path

    import matplotlib.pyplot as plt

    logger.info(f"Creating predictions vs actual plot: {save_path}")

    # Calculate metrics for annotation
    metrics = calculate_metrics(y_true, y_pred)

    # Create figure
    plt.figure(figsize=(10, 8))

    # Scatter plot
    plt.scatter(y_true, y_pred, alpha=0.6, edgecolors="k", linewidth=0.5)

    # Perfect prediction line
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    plt.plot([min_val, max_val], [min_val, max_val], "r--", linewidth=2, label="Perfect Prediction")

    # Labels and title
    plt.xlabel(f"Actual {target_name}", fontsize=12)
    plt.ylabel(f"Predicted {target_name}", fontsize=12)
    if title:
        plt.title(title, fontsize=14, fontweight="bold")
    else:
        plt.title(f"Predictions vs Actual: {target_name}", fontsize=14, fontweight="bold")

    # Add metrics annotation
    textstr = f"R² = {metrics['r2_score']:.3f}\nRMSE = {metrics['rmse']:.3f}\nMAE = {metrics['mae']:.3f}"
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.8)
    plt.text(0.05, 0.95, textstr, transform=plt.gca().transAxes, fontsize=11, verticalalignment="top", bbox=props)

    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save plot
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    logger.info(f"✓ Saved plot to {save_path}")


def plot_residuals_over_time(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    dates: pd.Series,
    save_path: str,
    target_name: str = "Target Variable",
    title: Optional[str] = None,
) -> None:
    """
    Create time series plot of prediction residuals (errors).

    Args:
        y_true: Actual values
        y_pred: Predicted values
        dates: Date series for x-axis
        save_path: Path to save the plot
        target_name: Name of target variable for axis labels
        title: Optional custom title
    """
    from pathlib import Path

    import matplotlib.pyplot as plt

    logger.info(f"Creating residuals over time plot: {save_path}")

    # Calculate residuals
    residuals = y_true - y_pred

    # Convert dates to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(dates):
        dates = pd.to_datetime(dates)

    # Create figure
    plt.figure(figsize=(14, 6))

    # Plot residuals
    plt.plot(dates, residuals, marker="o", linestyle="-", linewidth=1, markersize=4, alpha=0.7)

    # Zero line
    plt.axhline(y=0, color="r", linestyle="--", linewidth=2, label="Zero Error")

    # Labels and title
    plt.xlabel("Date", fontsize=12)
    plt.ylabel(f"Residual (Actual - Predicted) {target_name}", fontsize=12)
    if title:
        plt.title(title, fontsize=14, fontweight="bold")
    else:
        plt.title(f"Prediction Residuals Over Time: {target_name}", fontsize=14, fontweight="bold")

    # Add statistics annotation
    textstr = f"Mean Error = {residuals.mean():.3f}\nStd Dev = {residuals.std():.3f}"
    props = dict(boxstyle="round", facecolor="lightblue", alpha=0.8)
    plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=11, verticalalignment="top", bbox=props)

    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save plot
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    logger.info(f"✓ Saved plot to {save_path}")


def plot_feature_importance(
    feature_names: list, importances: np.ndarray, save_path: str, top_n: int = 20, title: Optional[str] = None
) -> None:
    """
    Create horizontal bar chart of feature importances.

    Args:
        feature_names: List of feature names
        importances: Array of importance values
        save_path: Path to save the plot
        top_n: Number of top features to display
        title: Optional custom title
    """
    from pathlib import Path

    import matplotlib.pyplot as plt

    logger.info(f"Creating feature importance plot: {save_path}")

    # Create DataFrame and sort
    importance_df = pd.DataFrame({"feature": feature_names, "importance": importances}).sort_values(
        "importance", ascending=False
    )

    # Select top N features
    top_features = importance_df.head(top_n)

    # Create figure
    plt.figure(figsize=(10, max(8, top_n * 0.4)))

    # Horizontal bar chart
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_features)))
    plt.barh(range(len(top_features)), top_features["importance"], color=colors)
    plt.yticks(range(len(top_features)), top_features["feature"])

    # Labels and title
    plt.xlabel("Importance", fontsize=12)
    plt.ylabel("Feature", fontsize=12)
    if title:
        plt.title(title, fontsize=14, fontweight="bold")
    else:
        plt.title(f"Top {top_n} Feature Importances", fontsize=14, fontweight="bold")

    # Invert y-axis so most important is at top
    plt.gca().invert_yaxis()

    plt.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()

    # Save plot
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()

    logger.info(f"✓ Saved plot to {save_path}")


def generate_evaluation_report(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    dates: pd.Series,
    feature_names: list,
    output_dir: str,
    model_name: str = "model",
    target_name: str = "target",
    r2_threshold: float = 0.85,
) -> Dict:
    """
    Generate comprehensive evaluation report with all metrics and visualizations.

    Args:
        model: Trained model with predict() method
        X_test: Test features
        y_test: Test target values
        dates: Date series for test set
        feature_names: List of feature names
        output_dir: Directory to save outputs
        model_name: Name of the model for file naming
        target_name: Name of target variable
        r2_threshold: Minimum acceptable R² score

    Returns:
        Dictionary containing all evaluation metrics and file paths
    """
    import json
    from pathlib import Path

    logger.info(f"=" * 80)
    logger.info(f"Generating comprehensive evaluation report for {model_name}")
    logger.info(f"=" * 80)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate predictions
    logger.info("Generating predictions...")
    y_pred = model.predict(X_test)

    # Calculate overall metrics
    logger.info("Calculating overall metrics...")
    overall_metrics = calculate_metrics(y_test, y_pred)

    logger.info(f"Overall Performance:")
    logger.info(f"  R² Score: {overall_metrics['r2_score']:.4f}")
    logger.info(f"  RMSE:     {overall_metrics['rmse']:.4f}")
    logger.info(f"  MAE:      {overall_metrics['mae']:.4f}")
    logger.info(f"  MAPE:     {overall_metrics['mape']:.2f}%")

    # Check R² threshold
    if overall_metrics["r2_score"] < r2_threshold:
        logger.warning(f"⚠ R² score ({overall_metrics['r2_score']:.4f}) is below threshold ({r2_threshold})")
        logger.warning("  Suggestions for improvement:")
        logger.warning("  - Add more relevant features")
        logger.warning("  - Tune hyperparameters using grid search")
        logger.warning("  - Try ensemble methods combining multiple models")
        logger.warning("  - Check for data quality issues or outliers")
    else:
        logger.info(f"✓ R² score meets threshold requirement ({r2_threshold})")

    # Seasonal performance analysis
    logger.info("\nCalculating seasonal performance...")
    seasonal_metrics = evaluate_by_season(y_test, y_pred, dates, target_name)
    seasonal_csv_path = output_path / f"{model_name}_seasonal_performance.csv"
    seasonal_metrics.to_csv(seasonal_csv_path, index=False)
    logger.info(f"✓ Saved seasonal metrics to {seasonal_csv_path}")

    # Create visualizations
    logger.info("\nGenerating visualizations...")

    # 1. Predictions vs Actual
    pred_vs_actual_path = output_path / f"{model_name}_predictions_vs_actual.png"
    plot_predictions_vs_actual(
        y_test, y_pred, str(pred_vs_actual_path), target_name=target_name, title=f"{model_name}: Predictions vs Actual"
    )

    # 2. Residuals over time
    residuals_path = output_path / f"{model_name}_residuals_over_time.png"
    plot_residuals_over_time(
        y_test, y_pred, dates, str(residuals_path), target_name=target_name, title=f"{model_name}: Residuals Over Time"
    )

    # 3. Feature importance (if model supports it)
    feature_importance_path = None
    if hasattr(model, "feature_importances_"):
        feature_importance_path = output_path / f"{model_name}_feature_importance.png"
        plot_feature_importance(
            feature_names,
            model.feature_importances_,
            str(feature_importance_path),
            top_n=20,
            title=f"{model_name}: Top 20 Feature Importances",
        )
    else:
        logger.info("  Model does not support feature importance extraction")

    # Compile summary report
    logger.info("\nCompiling summary report...")

    summary = {
        "model_name": model_name,
        "target_name": target_name,
        "evaluation_timestamp": pd.Timestamp.now().isoformat(),
        "test_samples": len(y_test),
        "overall_metrics": {
            "r2_score": float(overall_metrics["r2_score"]),
            "rmse": float(overall_metrics["rmse"]),
            "mae": float(overall_metrics["mae"]),
            "mape": float(overall_metrics["mape"]),
        },
        "r2_threshold": r2_threshold,
        "meets_threshold": overall_metrics["r2_score"] >= r2_threshold,
        "seasonal_performance": seasonal_metrics.to_dict("records"),
        "output_files": {
            "seasonal_metrics_csv": str(seasonal_csv_path),
            "predictions_vs_actual_plot": str(pred_vs_actual_path),
            "residuals_plot": str(residuals_path),
            "feature_importance_plot": str(feature_importance_path) if feature_importance_path else None,
        },
    }

    # Save summary as JSON
    summary_json_path = output_path / f"{model_name}_evaluation_summary.json"
    with open(summary_json_path, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"✓ Saved evaluation summary to {summary_json_path}")

    logger.info(f"\n" + "=" * 80)
    logger.info(f"✓ Comprehensive evaluation report completed for {model_name}")
    logger.info(f"  All outputs saved to: {output_path}")
    logger.info(f"=" * 80)

    return summary


def generate_report(model, metrics):
    """Legacy function for compatibility"""
    logger.info(f"Dry-run: evaluating model {model} with metrics {metrics}")
