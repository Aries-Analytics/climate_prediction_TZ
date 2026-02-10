"""
Data Visualization Module - Phase 2
Provides visualization capabilities for climate data and quality metrics.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils.config import get_data_path
from utils.logger import log_error, log_info

# Set style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)


class DataVisualizer:
    """
    Creates visualizations for climate data and quality metrics.
    """

    def __init__(self, output_dir=None):
        """
        Initialize the visualizer.

        Args:
            output_dir: Directory to save plots (default: data/visualizations)
        """
        if output_dir is None:
            output_dir = get_data_path("visualizations")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_time_series(self, df, value_col, title=None, ylabel=None, save_name=None):
        """
        Create a time series plot.

        Args:
            df: DataFrame with 'year' and optionally 'month' columns
            value_col: Column name to plot
            title: Plot title
            ylabel: Y-axis label
            save_name: Filename to save plot (optional)

        Returns:
            Path to saved plot or None
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 6))

            # Create time index
            if "month" in df.columns:
                df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
                x = df["date"]
                xlabel = "Date"
            else:
                x = df["year"]
                xlabel = "Year"

            ax.plot(x, df[value_col], marker="o", linewidth=2, markersize=4)
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel or value_col, fontsize=12)
            ax.set_title(title or f"{value_col} Over Time", fontsize=14, fontweight="bold")
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            if save_name:
                filepath = self.output_dir / save_name
                plt.savefig(filepath, dpi=300, bbox_inches="tight")
                log_info(f"Time series plot saved: {filepath}")
                plt.close()
                return filepath

            return None

        except Exception as e:
            log_error(f"Failed to create time series plot: {e}")
            plt.close()
            return None

    def plot_multiple_series(self, df, value_cols, title=None, save_name=None):
        """
        Plot multiple time series on the same chart.

        Args:
            df: DataFrame with time and value columns
            value_cols: List of column names to plot
            title: Plot title
            save_name: Filename to save plot (optional)

        Returns:
            Path to saved plot or None
        """
        try:
            fig, ax = plt.subplots(figsize=(14, 7))

            # Create time index
            if "month" in df.columns:
                df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
                x = df["date"]
            else:
                x = df["year"]

            for col in value_cols:
                if col in df.columns:
                    ax.plot(x, df[col], marker="o", label=col, linewidth=2, markersize=3)

            ax.set_xlabel("Date" if "month" in df.columns else "Year", fontsize=12)
            ax.set_ylabel("Value", fontsize=12)
            ax.set_title(title or "Multiple Time Series", fontsize=14, fontweight="bold")
            ax.legend(loc="best", fontsize=10)
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            if save_name:
                filepath = self.output_dir / save_name
                plt.savefig(filepath, dpi=300, bbox_inches="tight")
                log_info(f"Multiple series plot saved: {filepath}")
                plt.close()
                return filepath

            return None

        except Exception as e:
            log_error(f"Failed to create multiple series plot: {e}")
            plt.close()
            return None

    def plot_quality_metrics(self, metrics, save_name=None):
        """
        Create a quality metrics dashboard.

        Args:
            metrics: Quality metrics dictionary
            save_name: Filename to save plot (optional)

        Returns:
            Path to saved plot or None
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle(f"Data Quality Dashboard: {metrics['source']}", fontsize=16, fontweight="bold")

            # 1. Quality Score Gauge
            ax = axes[0, 0]
            score = metrics["quality_score"]
            colors = ["red" if score < 50 else "orange" if score < 75 else "green"]
            ax.barh([0], [score], color=colors, height=0.5)
            ax.set_xlim(0, 100)
            ax.set_ylim(-0.5, 0.5)
            ax.set_xlabel("Score", fontsize=11)
            ax.set_title(f"Overall Quality Score: {score}/100", fontsize=12, fontweight="bold")
            ax.set_yticks([])

            # 2. Completeness by Column
            ax = axes[0, 1]
            missing = metrics["missing_values"]
            cols = list(missing.keys())[:10]  # Top 10 columns
            percentages = [100 - missing[col]["percentage"] for col in cols]
            ax.barh(cols, percentages, color="steelblue")
            ax.set_xlabel("Completeness (%)", fontsize=11)
            ax.set_title("Data Completeness by Column", fontsize=12, fontweight="bold")
            ax.set_xlim(0, 100)

            # 3. Temporal Coverage
            ax = axes[1, 0]
            if "temporal" in metrics and "year_range" in metrics["temporal"]:
                year_range = metrics["temporal"]["year_range"]
                years = list(range(year_range["min"], year_range["max"] + 1))
                ax.plot(years, [1] * len(years), marker="o", linestyle="-", linewidth=2)
                ax.set_xlabel("Year", fontsize=11)
                ax.set_title(
                    f"Temporal Coverage: {year_range['min']}-{year_range['max']}", fontsize=12, fontweight="bold"
                )
                ax.set_yticks([])
            else:
                ax.text(0.5, 0.5, "No temporal data", ha="center", va="center", fontsize=12)
                ax.set_xticks([])
                ax.set_yticks([])

            # 4. Summary Statistics
            ax = axes[1, 1]
            summary_text = f"Total Rows: {metrics['row_count']:,}\n"
            summary_text += f"Total Columns: {metrics['column_count']}\n"
            summary_text += f"Completeness: {metrics['completeness']['percentage']:.1f}%\n"
            summary_text += f"Duplicates: {metrics['duplicates']['total_duplicates']}\n"
            if "temporal" in metrics and "year_gaps" in metrics["temporal"]:
                summary_text += f"Year Gaps: {len(metrics['temporal']['year_gaps'])}"

            ax.text(0.1, 0.5, summary_text, fontsize=12, verticalalignment="center", family="monospace")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            ax.set_title("Summary Statistics", fontsize=12, fontweight="bold")

            plt.tight_layout()

            if save_name:
                filepath = self.output_dir / save_name
                plt.savefig(filepath, dpi=300, bbox_inches="tight")
                log_info(f"Quality metrics dashboard saved: {filepath}")
                plt.close()
                return filepath

            return None

        except Exception as e:
            log_error(f"Failed to create quality metrics plot: {e}")
            plt.close()
            return None

    def plot_correlation_matrix(self, df, save_name=None):
        """
        Create a correlation matrix heatmap.

        Args:
            df: DataFrame with numeric columns
            save_name: Filename to save plot (optional)

        Returns:
            Path to saved plot or None
        """
        try:
            # Select only numeric columns
            numeric_df = df.select_dtypes(include=["number"])

            # Remove time columns
            time_cols = ["year", "month", "day"]
            numeric_df = numeric_df.drop(columns=[col for col in time_cols if col in numeric_df.columns])

            if numeric_df.empty or len(numeric_df.columns) < 2:
                log_info("Not enough numeric columns for correlation matrix")
                return None

            fig, ax = plt.subplots(figsize=(10, 8))
            corr = numeric_df.corr()

            sns.heatmap(
                corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True, ax=ax, cbar_kws={"shrink": 0.8}
            )

            ax.set_title("Correlation Matrix", fontsize=14, fontweight="bold")
            plt.tight_layout()

            if save_name:
                filepath = self.output_dir / save_name
                plt.savefig(filepath, dpi=300, bbox_inches="tight")
                log_info(f"Correlation matrix saved: {filepath}")
                plt.close()
                return filepath

            return None

        except Exception as e:
            log_error(f"Failed to create correlation matrix: {e}")
            plt.close()
            return None

    def plot_distribution(self, df, column, title=None, save_name=None):
        """
        Create a distribution plot (histogram + KDE).

        Args:
            df: DataFrame
            column: Column name to plot
            title: Plot title
            save_name: Filename to save plot (optional)

        Returns:
            Path to saved plot or None
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            sns.histplot(data=df, x=column, kde=True, ax=ax, color="steelblue")

            ax.set_xlabel(column, fontsize=12)
            ax.set_ylabel("Frequency", fontsize=12)
            ax.set_title(title or f"Distribution of {column}", fontsize=14, fontweight="bold")

            plt.tight_layout()

            if save_name:
                filepath = self.output_dir / save_name
                plt.savefig(filepath, dpi=300, bbox_inches="tight")
                log_info(f"Distribution plot saved: {filepath}")
                plt.close()
                return filepath

            return None

        except Exception as e:
            log_error(f"Failed to create distribution plot: {e}")
            plt.close()
            return None


# Global visualizer instance
_visualizer = None


def get_visualizer(output_dir=None):
    """
    Get or create the global visualizer instance.

    Args:
        output_dir: Directory to save plots

    Returns:
        DataVisualizer instance
    """
    global _visualizer
    if _visualizer is None:
        _visualizer = DataVisualizer(output_dir=output_dir)
    return _visualizer
