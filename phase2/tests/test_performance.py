"""
Tests for performance optimization module
"""

import tempfile
import time

import pandas as pd

from utils.performance import DataFrameOptimizer, PerformanceBenchmark, PerformanceMonitor, timer


def test_performance_monitor():
    """Test performance monitoring."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = PerformanceMonitor(metrics_file=f"{tmpdir}/metrics.csv")

        monitor.record_metric("test_op", 1.5, memory_used=100, rows_processed=1000)
        monitor.save_metrics()

        summary = monitor.get_summary()
        assert summary["total_operations"] == 1


def test_timer_decorator():
    """Test timer decorator."""

    @timer
    def slow_function():
        time.sleep(0.1)
        return "done"

    result = slow_function()
    assert result == "done"


def test_dataframe_optimizer():
    """Test DataFrame optimization."""
    df = pd.DataFrame(
        {"int_col": [1, 2, 3, 4, 5], "float_col": [1.0, 2.0, 3.0, 4.0, 5.0], "cat_col": ["A", "A", "B", "B", "A"]}
    )

    optimized_df, savings = DataFrameOptimizer.optimize_dtypes(df.copy())

    assert "savings_mb" in savings
    assert optimized_df["cat_col"].dtype.name == "category"


def test_benchmark_operation():
    """Test operation benchmarking."""

    def simple_func():
        time.sleep(0.01)  # Small delay to ensure measurable time
        return sum(range(100))

    results = PerformanceBenchmark.benchmark_operation(simple_func, iterations=5)

    assert results["iterations"] == 5
    assert "avg_duration" in results
    assert results["avg_duration"] >= 0
