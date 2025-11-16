"""
Exploratory Data Analysis (EDA) Module

Performs comprehensive EDA on processed datasets before and after merging.

Features:
- Summary statistics
- Missing value analysis
- Distribution analysis
- Correlation analysis
- Time series patterns
- Feature importance indicators
- Data quality assessment
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from utils.logger import log_error, log_info


def perform_eda(df, dataset_name="Dataset", output_dir="outputs/eda"):
    """
    Perform comprehensive EDA on a dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset to analyze
    dataset_name : str
        Name of the dataset for reporting
    output_dir : str
        Directory to save EDA outputs

    Returns
    -------
    dict
        Dictionary containing EDA results
    """
    log_info(f"[EDA] Starting EDA for {dataset_name}...")

    if df is None or df.empty:
        log_error(f"[EDA] {dataset_name} is empty")
        return {}

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize results dictionary
    results = {
        "dataset_name": dataset_name,
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.to_dict(),
    }

    # 1. Basic Statistics
    log_info(f"[EDA] Computing basic statistics for {dataset_name}...")
    results["basic_stats"] = _compute_basic_stats(df)

    # 2. Missing Value Analysis
    log_info(f"[EDA] Analyzing missing values for {dataset_name}...")
    results["missing_values"] = _analyze_missing_values(df)

    # 3. Distribution Analysis
    log_info(f"[EDA] Analyzing distributions for {dataset_name}...")
    results["distributions"] = _analyze_distributions(df)

    # 4. Correlation Analysis
    log_info(f"[EDA] Computing correlations for {dataset_name}...")
    results["correlations"] = _analyze_correlations(df)

    # 5. Time Series Patterns (if temporal data)
    if "year" in df.columns and "month" in df.columns:
        log_info(f"[EDA] Analyzing time series patterns for {dataset_name}...")
        results["time_series"] = _analyze_time_series(df)

    # 6. Feature Statistics
    log_info(f"[EDA] Computing feature statistics for {dataset_name}...")
    results["feature_stats"] = _compute_feature_stats(df)

    # 7. Generate Visualizations
    log_info(f"[EDA] Generating visualizations for {dataset_name}...")
    _generate_visualizations(df, dataset_name, output_path)

    # 8. Generate Report
    log_info(f"[EDA] Generating report for {dataset_name}...")
    _generate_report(results, output_path, dataset_name)

    log_info(f"[EDA] EDA complete for {dataset_name}")
    log_info(f"[EDA] Results saved to: {output_path}")

    return results


def _compute_basic_stats(df):
    """Compute basic statistics for the dataset."""
    stats = {
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024**2,
        "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
        "categorical_columns": df.select_dtypes(include=["object", "category"]).columns.tolist(),
        "datetime_columns": df.select_dtypes(include=["datetime64"]).columns.tolist(),
    }

    # Summary statistics for numeric columns
    if stats["numeric_columns"]:
        stats["numeric_summary"] = df[stats["numeric_columns"]].describe().to_dict()

    return stats


def _analyze_missing_values(df):
    """Analyze missing values in the dataset."""
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100

    missing_df = pd.DataFrame({"missing_count": missing, "missing_percentage": missing_pct})

    missing_df = missing_df[missing_df["missing_count"] > 0].sort_values("missing_percentage", ascending=False)

    return {
        "total_missing": missing.sum(),
        "columns_with_missing": len(missing_df),
        "missing_by_column": missing_df.to_dict("index"),
    }


def _analyze_distributions(df):
    """Analyze distributions of numeric features."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    distributions = {}
    for col in numeric_cols:
        distributions[col] = {
            "mean": df[col].mean(),
            "median": df[col].median(),
            "std": df[col].std(),
            "min": df[col].min(),
            "max": df[col].max(),
            "skewness": df[col].skew(),
            "kurtosis": df[col].kurtosis(),
            "q25": df[col].quantile(0.25),
            "q75": df[col].quantile(0.75),
            "iqr": df[col].quantile(0.75) - df[col].quantile(0.25),
        }

    return distributions


def _analyze_correlations(df):
    """Analyze correlations between numeric features."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    if len(numeric_cols) < 2:
        return {"message": "Not enough numeric columns for correlation analysis"}

    corr_matrix = df[numeric_cols].corr()

    # Find highly correlated pairs (|r| > 0.7)
    high_corr = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            if abs(corr_matrix.iloc[i, j]) > 0.7:
                high_corr.append(
                    {
                        "feature1": corr_matrix.columns[i],
                        "feature2": corr_matrix.columns[j],
                        "correlation": corr_matrix.iloc[i, j],
                    }
                )

    return {
        "correlation_matrix": corr_matrix.to_dict(),
        "high_correlations": high_corr,
        "n_high_correlations": len(high_corr),
    }


def _analyze_time_series(df):
    """Analyze time series patterns."""
    if "year" not in df.columns or "month" not in df.columns:
        return {}

    # Create date column if not exists
    if "date" not in df.columns:
        df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

    df_sorted = df.sort_values("date")

    time_stats = {
        "start_date": df_sorted["date"].min().strftime("%Y-%m-%d"),
        "end_date": df_sorted["date"].max().strftime("%Y-%m-%d"),
        "n_months": len(df_sorted),
        "date_range_years": (df_sorted["date"].max() - df_sorted["date"].min()).days / 365.25,
    }

    # Check for gaps in time series
    date_diffs = df_sorted["date"].diff()
    expected_diff = pd.Timedelta(days=30)  # Approximately 1 month
    gaps = date_diffs[date_diffs > expected_diff * 1.5]

    time_stats["n_gaps"] = len(gaps)
    if len(gaps) > 0:
        time_stats["gaps"] = gaps.index.tolist()

    return time_stats


def _compute_feature_stats(df):
    """Compute statistics for each feature."""
    feature_stats = {}

    for col in df.columns:
        stats = {
            "dtype": str(df[col].dtype),
            "n_unique": df[col].nunique(),
            "n_missing": df[col].isnull().sum(),
            "missing_pct": (df[col].isnull().sum() / len(df)) * 100,
        }

        if df[col].dtype in [np.float64, np.int64]:
            stats["mean"] = df[col].mean()
            stats["std"] = df[col].std()
            stats["min"] = df[col].min()
            stats["max"] = df[col].max()
            stats["zeros"] = (df[col] == 0).sum()
            stats["zeros_pct"] = ((df[col] == 0).sum() / len(df)) * 100

        feature_stats[col] = stats

    return feature_stats


def _generate_visualizations(df, dataset_name, output_path):
    """Generate visualizations for the dataset."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    if len(numeric_cols) == 0:
        log_info(f"[EDA] No numeric columns to visualize for {dataset_name}")
        return

    # Set style
    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = (12, 8)

    # 1. Missing Values Heatmap
    if df.isnull().sum().sum() > 0:
        plt.figure(figsize=(12, 6))
        sns.heatmap(df.isnull(), cbar=False, yticklabels=False, cmap="viridis")
        plt.title(f"Missing Values Pattern - {dataset_name}")
        plt.tight_layout()
        plt.savefig(output_path / f"{dataset_name}_missing_values.png", dpi=300, bbox_inches="tight")
        plt.close()

    # 2. Distribution Plots (first 12 numeric features)
    n_features = min(12, len(numeric_cols))
    fig, axes = plt.subplots(4, 3, figsize=(15, 12))
    axes = axes.flatten()

    for idx, col in enumerate(numeric_cols[:n_features]):
        df[col].hist(bins=30, ax=axes[idx], edgecolor="black")
        axes[idx].set_title(f"{col}")
        axes[idx].set_xlabel("Value")
        axes[idx].set_ylabel("Frequency")

    # Hide unused subplots
    for idx in range(n_features, 12):
        axes[idx].axis("off")

    plt.suptitle(f"Feature Distributions - {dataset_name}", fontsize=16, y=1.00)
    plt.tight_layout()
    plt.savefig(output_path / f"{dataset_name}_distributions.png", dpi=300, bbox_inches="tight")
    plt.close()

    # 3. Correlation Heatmap (if enough features)
    if len(numeric_cols) >= 2:
        # Limit to first 20 features for readability
        cols_to_plot = numeric_cols[:20]
        corr_matrix = df[cols_to_plot].corr()

        plt.figure(figsize=(14, 12))
        sns.heatmap(
            corr_matrix, annot=False, cmap="coolwarm", center=0, square=True, linewidths=0.5, cbar_kws={"shrink": 0.8}
        )
        plt.title(f"Feature Correlations - {dataset_name}")
        plt.tight_layout()
        plt.savefig(output_path / f"{dataset_name}_correlations.png", dpi=300, bbox_inches="tight")
        plt.close()

    # 4. Time Series Plots (if temporal data)
    if "year" in df.columns and "month" in df.columns:
        # Create date column
        df_temp = df.copy()
        if "date" not in df_temp.columns:
            df_temp["date"] = pd.to_datetime(df_temp[["year", "month"]].assign(day=1))

        df_temp = df_temp.sort_values("date")

        # Plot first 6 numeric features over time
        n_ts_features = min(6, len(numeric_cols))
        fig, axes = plt.subplots(n_ts_features, 1, figsize=(14, 3 * n_ts_features))

        if n_ts_features == 1:
            axes = [axes]

        for idx, col in enumerate(numeric_cols[:n_ts_features]):
            axes[idx].plot(df_temp["date"], df_temp[col], linewidth=1)
            axes[idx].set_title(f"{col} over Time")
            axes[idx].set_xlabel("Date")
            axes[idx].set_ylabel(col)
            axes[idx].grid(True, alpha=0.3)

        plt.suptitle(f"Time Series - {dataset_name}", fontsize=16, y=1.00)
        plt.tight_layout()
        plt.savefig(output_path / f"{dataset_name}_timeseries.png", dpi=300, bbox_inches="tight")
        plt.close()

    log_info(f"[EDA] Visualizations saved to {output_path}")


def _generate_report(results, output_path, dataset_name):
    """Generate a text report of EDA results."""
    report_path = output_path / f"{dataset_name}_eda_report.txt"

    with open(report_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("EXPLORATORY DATA ANALYSIS REPORT\n")
        f.write(f"Dataset: {dataset_name}\n")
        f.write("=" * 80 + "\n\n")

        # Basic Statistics
        f.write("BASIC STATISTICS\n")
        f.write("-" * 80 + "\n")
        basic = results["basic_stats"]
        f.write(f"Rows: {basic['n_rows']:,}\n")
        f.write(f"Columns: {basic['n_columns']}\n")
        f.write(f"Memory Usage: {basic['memory_usage_mb']:.2f} MB\n")
        f.write(f"Numeric Columns: {len(basic['numeric_columns'])}\n")
        f.write(f"Categorical Columns: {len(basic['categorical_columns'])}\n")
        f.write(f"Datetime Columns: {len(basic['datetime_columns'])}\n\n")

        # Missing Values
        f.write("MISSING VALUES\n")
        f.write("-" * 80 + "\n")
        missing = results["missing_values"]
        f.write(f"Total Missing Values: {missing['total_missing']:,}\n")
        f.write(f"Columns with Missing Values: {missing['columns_with_missing']}\n\n")

        if missing["columns_with_missing"] > 0:
            f.write("Top 10 Columns with Missing Values:\n")
            sorted_missing = sorted(
                missing["missing_by_column"].items(), key=lambda x: x[1]["missing_percentage"], reverse=True
            )[:10]
            for col, stats in sorted_missing:
                f.write(f"  {col}: {stats['missing_count']} ({stats['missing_percentage']:.2f}%)\n")
        f.write("\n")

        # Correlations
        if "correlations" in results and "high_correlations" in results["correlations"]:
            f.write("HIGH CORRELATIONS (|r| > 0.7)\n")
            f.write("-" * 80 + "\n")
            high_corr = results["correlations"]["high_correlations"]
            f.write(f"Number of High Correlations: {len(high_corr)}\n\n")

            if high_corr:
                f.write("Top 10 Correlations:\n")
                sorted_corr = sorted(high_corr, key=lambda x: abs(x["correlation"]), reverse=True)[:10]
                for corr in sorted_corr:
                    f.write(f"  {corr['feature1']} <-> {corr['feature2']}: {corr['correlation']:.3f}\n")
            f.write("\n")

        # Time Series
        if "time_series" in results:
            f.write("TIME SERIES ANALYSIS\n")
            f.write("-" * 80 + "\n")
            ts = results["time_series"]
            f.write(f"Start Date: {ts['start_date']}\n")
            f.write(f"End Date: {ts['end_date']}\n")
            f.write(f"Number of Months: {ts['n_months']}\n")
            f.write(f"Date Range: {ts['date_range_years']:.2f} years\n")
            f.write(f"Gaps in Time Series: {ts['n_gaps']}\n\n")

        # Feature Statistics Summary
        f.write("FEATURE STATISTICS SUMMARY\n")
        f.write("-" * 80 + "\n")
        feature_stats = results["feature_stats"]

        # Count features by type
        numeric_features = [k for k, v in feature_stats.items() if "mean" in v]
        categorical_features = [k for k, v in feature_stats.items() if "mean" not in v]

        f.write(f"Numeric Features: {len(numeric_features)}\n")
        f.write(f"Categorical Features: {len(categorical_features)}\n\n")

        # Features with high missing rates
        high_missing = [(k, v["missing_pct"]) for k, v in feature_stats.items() if v["missing_pct"] > 10]
        if high_missing:
            f.write(f"Features with >10% Missing Values: {len(high_missing)}\n")
            for feat, pct in sorted(high_missing, key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"  {feat}: {pct:.2f}%\n")

        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")

    log_info(f"[EDA] Report saved to {report_path}")


def compare_datasets(df_before, df_after, output_dir="outputs/eda"):
    """
    Compare datasets before and after merging.

    Parameters
    ----------
    df_before : dict or pd.DataFrame
        Dataset(s) before merging (dict of DataFrames or single DataFrame)
    df_after : pd.DataFrame
        Dataset after merging
    output_dir : str
        Directory to save comparison outputs
    """
    log_info("[EDA] Comparing datasets before and after merging...")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    comparison = {}

    # Handle before datasets
    if isinstance(df_before, dict):
        # Multiple datasets before merging
        comparison["before"] = {"n_datasets": len(df_before), "datasets": {}}

        total_rows_before = 0
        total_cols_before = set()

        for name, df in df_before.items():
            comparison["before"]["datasets"][name] = {"shape": df.shape, "columns": list(df.columns)}
            total_rows_before += len(df)
            total_cols_before.update(df.columns)

        comparison["before"]["total_rows"] = total_rows_before
        comparison["before"]["unique_columns"] = len(total_cols_before)
    else:
        # Single dataset before merging
        comparison["before"] = {"shape": df_before.shape, "columns": list(df_before.columns)}

    # After merging
    comparison["after"] = {"shape": df_after.shape, "columns": list(df_after.columns)}

    # Comparison metrics
    if isinstance(df_before, dict):
        comparison["changes"] = {
            "row_reduction": total_rows_before - len(df_after),
            "row_reduction_pct": (
                ((total_rows_before - len(df_after)) / total_rows_before * 100) if total_rows_before > 0 else 0
            ),
            "column_increase": len(df_after.columns) - len(total_cols_before),
            "new_columns": list(set(df_after.columns) - total_cols_before),
        }

    # Generate comparison report
    report_path = output_path / "merge_comparison_report.txt"

    with open(report_path, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("DATASET MERGE COMPARISON REPORT\n")
        f.write("=" * 80 + "\n\n")

        f.write("BEFORE MERGING\n")
        f.write("-" * 80 + "\n")
        if isinstance(df_before, dict):
            f.write(f"Number of Datasets: {comparison['before']['n_datasets']}\n")
            f.write(f"Total Rows: {comparison['before']['total_rows']:,}\n")
            f.write(f"Unique Columns: {comparison['before']['unique_columns']}\n\n")

            for name, stats in comparison["before"]["datasets"].items():
                f.write(f"  {name}:\n")
                f.write(f"    Shape: {stats['shape']}\n")
                f.write(f"    Columns: {len(stats['columns'])}\n")
        else:
            f.write(f"Shape: {comparison['before']['shape']}\n")
            f.write(f"Columns: {len(comparison['before']['columns'])}\n")

        f.write("\n")
        f.write("AFTER MERGING\n")
        f.write("-" * 80 + "\n")
        f.write(f"Shape: {comparison['after']['shape']}\n")
        f.write(f"Columns: {len(comparison['after']['columns'])}\n\n")

        if "changes" in comparison:
            f.write("CHANGES\n")
            f.write("-" * 80 + "\n")
            f.write(
                f"Row Reduction: {comparison['changes']['row_reduction']:,} "
                f"({comparison['changes']['row_reduction_pct']:.2f}%)\n"
            )
            f.write(f"Column Increase: {comparison['changes']['column_increase']}\n")
            if comparison["changes"]["new_columns"]:
                f.write(f"New Columns: {len(comparison['changes']['new_columns'])}\n")

        f.write("\n")
        f.write("=" * 80 + "\n")

    log_info(f"[EDA] Comparison report saved to {report_path}")

    return comparison
