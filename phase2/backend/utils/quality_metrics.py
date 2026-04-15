"""
Data Quality Metrics - Phase 2
Provides comprehensive data quality assessment for climate data pipeline.
"""

import json
from datetime import datetime
from pathlib import Path

from utils.config import get_data_path
from utils.logger import log_error, log_info


class DataQualityMetrics:
    """
    Calculates and tracks data quality metrics for climate datasets.
    """

    def __init__(self, metrics_dir=None):
        """
        Initialize the quality metrics tracker.

        Args:
            metrics_dir: Directory to store metrics reports (default: data/metrics)
        """
        if metrics_dir is None:
            metrics_dir = get_data_path("metrics")
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def calculate_metrics(self, df, source_name, expected_columns=None):
        """
        Calculate comprehensive quality metrics for a dataset.

        Args:
            df: pandas DataFrame to analyze
            source_name: Name of the data source
            expected_columns: List of expected column names (optional)

        Returns:
            Dictionary containing quality metrics
        """
        metrics = {
            "source": source_name,
            "timestamp": datetime.now().isoformat(),
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
        }

        # Completeness metrics
        metrics["completeness"] = self._calculate_completeness(df)

        # Missing value metrics
        metrics["missing_values"] = self._calculate_missing_values(df)

        # Data type consistency
        metrics["data_types"] = self._check_data_types(df)

        # Temporal consistency (if year/month columns exist)
        if "year" in df.columns:
            metrics["temporal"] = self._check_temporal_consistency(df)

        # Value range checks
        metrics["value_ranges"] = self._calculate_value_ranges(df)

        # Duplicate detection
        metrics["duplicates"] = self._check_duplicates(df)

        # Expected columns check
        if expected_columns:
            metrics["schema_validation"] = self._validate_schema(df, expected_columns)

        # Overall quality score (0-100)
        metrics["quality_score"] = self._calculate_quality_score(metrics)

        return metrics

    def _calculate_completeness(self, df):
        """Calculate data completeness percentage."""
        total_cells = df.shape[0] * df.shape[1]
        non_null_cells = df.count().sum()
        completeness_pct = (non_null_cells / total_cells * 100) if total_cells > 0 else 0

        return {
            "total_cells": int(total_cells),
            "non_null_cells": int(non_null_cells),
            "percentage": round(completeness_pct, 2),
        }

    def _calculate_missing_values(self, df):
        """Calculate missing values per column."""
        missing = {}
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df) * 100) if len(df) > 0 else 0
            missing[col] = {"count": int(null_count), "percentage": round(null_pct, 2)}
        return missing

    def _check_data_types(self, df):
        """Check data types of columns."""
        return {col: str(dtype) for col, dtype in df.dtypes.items()}

    def _check_temporal_consistency(self, df):
        """Check temporal consistency of the data."""
        temporal = {}

        if "year" in df.columns:
            temporal["year_range"] = {"min": int(df["year"].min()), "max": int(df["year"].max())}
            temporal["year_gaps"] = self._find_year_gaps(df)

        if "month" in df.columns:
            temporal["month_range"] = {"min": int(df["month"].min()), "max": int(df["month"].max())}
            temporal["invalid_months"] = int(((df["month"] < 1) | (df["month"] > 12)).sum())

        return temporal

    def _find_year_gaps(self, df):
        """Find gaps in year sequence."""
        if "year" not in df.columns:
            return []

        years = sorted(df["year"].unique())
        gaps = []
        for i in range(len(years) - 1):
            if years[i + 1] - years[i] > 1:
                gaps.append(
                    {"from": int(years[i]), "to": int(years[i + 1]), "gap_size": int(years[i + 1] - years[i] - 1)}
                )
        return gaps

    def _calculate_value_ranges(self, df):
        """Calculate value ranges for numeric columns."""
        ranges = {}
        numeric_cols = df.select_dtypes(include=["number"]).columns

        for col in numeric_cols:
            if col not in ["year", "month"]:  # Skip time columns
                ranges[col] = {
                    "min": float(df[col].min()) if not df[col].isnull().all() else None,
                    "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                    "std": float(df[col].std()) if not df[col].isnull().all() else None,
                }
        return ranges

    def _check_duplicates(self, df):
        """Check for duplicate rows."""
        duplicate_count = df.duplicated().sum()
        duplicate_pct = (duplicate_count / len(df) * 100) if len(df) > 0 else 0

        # Check for duplicates based on year/month if available
        key_duplicates = 0
        if "year" in df.columns and "month" in df.columns:
            key_duplicates = df.duplicated(subset=["year", "month"]).sum()
        elif "year" in df.columns:
            key_duplicates = df.duplicated(subset=["year"]).sum()

        return {
            "total_duplicates": int(duplicate_count),
            "percentage": round(duplicate_pct, 2),
            "key_duplicates": int(key_duplicates),
        }

    def _validate_schema(self, df, expected_columns):
        """Validate that expected columns are present."""
        actual_columns = set(df.columns)
        expected_set = set(expected_columns)

        missing = list(expected_set - actual_columns)
        extra = list(actual_columns - expected_set)

        return {"missing_columns": missing, "extra_columns": extra, "is_valid": len(missing) == 0}

    def _calculate_quality_score(self, metrics):
        """
        Calculate overall quality score (0-100) based on various metrics.

        Scoring criteria:
        - Completeness: 40 points
        - No duplicates: 20 points
        - Temporal consistency: 20 points
        - Schema validation: 20 points
        """
        score = 0

        # Completeness score (40 points)
        completeness_pct = metrics["completeness"]["percentage"]
        score += (completeness_pct / 100) * 40

        # Duplicate score (20 points)
        duplicate_pct = metrics["duplicates"]["percentage"]
        score += max(0, (100 - duplicate_pct) / 100 * 20)

        # Temporal consistency score (20 points)
        if "temporal" in metrics:
            temporal_score = 20
            if "invalid_months" in metrics["temporal"] and metrics["temporal"]["invalid_months"] > 0:
                temporal_score -= 10
            if "year_gaps" in metrics["temporal"] and len(metrics["temporal"]["year_gaps"]) > 0:
                temporal_score -= 5
            score += temporal_score
        else:
            score += 20  # No temporal data to check

        # Schema validation score (20 points)
        if "schema_validation" in metrics:
            if metrics["schema_validation"]["is_valid"]:
                score += 20
            else:
                # Partial credit based on missing columns
                missing_count = len(metrics["schema_validation"]["missing_columns"])
                score += max(0, 20 - (missing_count * 5))
        else:
            score += 20  # No schema to validate

        return round(min(100, max(0, score)), 2)

    def save_metrics(self, metrics, source_name):
        """
        Save metrics to a JSON file.

        Args:
            metrics: Metrics dictionary
            source_name: Name of the data source
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source_name}_metrics_{timestamp}.json"
        filepath = self.metrics_dir / filename

        try:
            with open(filepath, "w") as f:
                json.dump(metrics, f, indent=2)
            log_info(f"Quality metrics saved: {filepath}")
        except Exception as e:
            log_error(f"Failed to save metrics: {e}")

    def generate_report(self, metrics):
        """
        Generate a human-readable quality report.

        Args:
            metrics: Metrics dictionary

        Returns:
            String containing formatted report
        """
        report = []
        report.append(f"\n{'='*60}")
        report.append(f"Data Quality Report: {metrics['source']}")
        report.append(f"{'='*60}")
        report.append(f"Timestamp: {metrics['timestamp']}")
        report.append(f"Quality Score: {metrics['quality_score']}/100")
        report.append("\nDataset Overview:")
        report.append(f"  Rows: {metrics['row_count']:,}")
        report.append(f"  Columns: {metrics['column_count']}")

        # Completeness
        comp = metrics["completeness"]
        report.append("\nCompleteness:")
        report.append(f"  {comp['percentage']:.2f}% ({comp['non_null_cells']:,}/{comp['total_cells']:,} cells)")

        # Missing values
        report.append("\nMissing Values by Column:")
        for col, info in metrics["missing_values"].items():
            if info["count"] > 0:
                report.append(f"  {col}: {info['count']} ({info['percentage']:.2f}%)")

        # Duplicates
        dup = metrics["duplicates"]
        if dup["total_duplicates"] > 0:
            report.append("\nDuplicates:")
            report.append(f"  Total: {dup['total_duplicates']} ({dup['percentage']:.2f}%)")
            if dup["key_duplicates"] > 0:
                report.append(f"  Key duplicates (year/month): {dup['key_duplicates']}")

        # Temporal consistency
        if "temporal" in metrics:
            temp = metrics["temporal"]
            report.append("\nTemporal Consistency:")
            if "year_range" in temp:
                report.append(f"  Year range: {temp['year_range']['min']}-{temp['year_range']['max']}")
            if "year_gaps" in temp and temp["year_gaps"]:
                report.append(f"  Year gaps detected: {len(temp['year_gaps'])}")
            if "invalid_months" in temp and temp["invalid_months"] > 0:
                report.append(f"  Invalid months: {temp['invalid_months']}")

        # Schema validation
        if "schema_validation" in metrics:
            schema = metrics["schema_validation"]
            report.append("\nSchema Validation:")
            report.append(f"  Valid: {schema['is_valid']}")
            if schema["missing_columns"]:
                report.append(f"  Missing columns: {', '.join(schema['missing_columns'])}")
            if schema["extra_columns"]:
                report.append(f"  Extra columns: {', '.join(schema['extra_columns'])}")

        report.append(f"{'='*60}\n")
        return "\n".join(report)


# Global metrics instance
_metrics = None


def get_quality_metrics(metrics_dir=None):
    """
    Get or create the global quality metrics instance.

    Args:
        metrics_dir: Directory to store metrics reports

    Returns:
        DataQualityMetrics instance
    """
    global _metrics
    if _metrics is None:
        _metrics = DataQualityMetrics(metrics_dir=metrics_dir)
    return _metrics
