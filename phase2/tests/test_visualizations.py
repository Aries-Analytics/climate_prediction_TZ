"""
Tests for data visualization module
"""

import tempfile
from pathlib import Path

import pandas as pd

from utils.visualizations import DataVisualizer


def test_time_series_plot():
    """Test time series plot creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        visualizer = DataVisualizer(output_dir=tmpdir)

        df = pd.DataFrame({"year": [2020, 2021, 2022], "month": [1, 2, 3], "temperature": [20.5, 21.0, 22.5]})

        filepath = visualizer.plot_time_series(df, "temperature", save_name="test_timeseries.png")

        assert filepath is not None
        assert Path(filepath).exists()


def test_correlation_matrix():
    """Test correlation matrix creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        visualizer = DataVisualizer(output_dir=tmpdir)

        df = pd.DataFrame({"temp": [20, 21, 22], "humidity": [60, 65, 70], "rainfall": [100, 110, 120]})

        filepath = visualizer.plot_correlation_matrix(df, save_name="test_correlation.png")

        assert filepath is not None
        assert Path(filepath).exists()


def test_quality_metrics_dashboard():
    """Test quality metrics dashboard creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        visualizer = DataVisualizer(output_dir=tmpdir)

        metrics = {
            "source": "test_source",
            "quality_score": 85.5,
            "row_count": 100,
            "column_count": 5,
            "completeness": {"percentage": 95.0},
            "missing_values": {"col1": {"percentage": 5.0}, "col2": {"percentage": 0.0}},
            "duplicates": {"total_duplicates": 2},
            "temporal": {"year_range": {"min": 2020, "max": 2023}},
        }

        filepath = visualizer.plot_quality_metrics(metrics, save_name="test_quality.png")

        assert filepath is not None
        assert Path(filepath).exists()
