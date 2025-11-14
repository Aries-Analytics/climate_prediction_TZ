"""
Tests for data quality metrics
"""

import tempfile

import pandas as pd

from utils.quality_metrics import DataQualityMetrics


def test_completeness_calculation():
    """Test completeness metric calculation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_tracker = DataQualityMetrics(metrics_dir=tmpdir)
        df = pd.DataFrame({"year": [2020, 2021, 2022], "value": [100, None, 300]})
        metrics = metrics_tracker.calculate_metrics(df, "test_source")
        assert "completeness" in metrics
        assert metrics["completeness"]["total_cells"] == 6
        assert metrics["completeness"]["non_null_cells"] == 5


def test_missing_values_detection():
    """Test missing values detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_tracker = DataQualityMetrics(metrics_dir=tmpdir)
        df = pd.DataFrame({"col1": [1, 2, None, 4], "col2": [None, None, 3, 4]})
        metrics = metrics_tracker.calculate_metrics(df, "test_source")
        assert metrics["missing_values"]["col1"]["count"] == 1
        assert metrics["missing_values"]["col2"]["count"] == 2


def test_duplicate_detection():
    """Test duplicate row detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_tracker = DataQualityMetrics(metrics_dir=tmpdir)
        df = pd.DataFrame({"year": [2020, 2021, 2021, 2022], "month": [1, 1, 1, 1], "value": [100, 200, 200, 300]})
        metrics = metrics_tracker.calculate_metrics(df, "test_source")
        assert metrics["duplicates"]["total_duplicates"] == 1


def test_quality_score_calculation():
    """Test overall quality score calculation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics_tracker = DataQualityMetrics(metrics_dir=tmpdir)
        df = pd.DataFrame({"year": [2020, 2021, 2022], "month": [1, 2, 3], "value": [100, 200, 300]})
        metrics = metrics_tracker.calculate_metrics(df, "test_source", expected_columns=["year", "month", "value"])
        assert "quality_score" in metrics
        assert metrics["quality_score"] == 100.0
