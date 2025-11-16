"""
Performance Optimization Module - Phase 2
Provides tools for profiling, monitoring, and optimizing pipeline performance.
"""

import functools
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from utils.config import get_data_path
from utils.logger import log_info


class PerformanceMonitor:
    """
    Monitors and tracks performance metrics for pipeline operations.
    """

    def __init__(self, metrics_file=None):
        """
        Initialize the performance monitor.

        Args:
            metrics_file: Path to store performance metrics (default: data/performance_metrics.csv)
        """
        if metrics_file is None:
            metrics_file = get_data_path("performance_metrics.csv")
        self.metrics_file = Path(metrics_file)
        self.metrics = []

    def record_metric(self, operation, duration, memory_used=None, rows_processed=None, **kwargs):
        """
        Record a performance metric.

        Args:
            operation: Name of the operation
            duration: Duration in seconds
            memory_used: Memory used in MB (optional)
            rows_processed: Number of rows processed (optional)
            **kwargs: Additional metrics
        """
        metric = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_seconds": round(duration, 3),
            "memory_mb": memory_used,
            "rows_processed": rows_processed,
        }
        metric.update(kwargs)
        self.metrics.append(metric)

    def save_metrics(self):
        """Save metrics to CSV file."""
        if self.metrics:
            df = pd.DataFrame(self.metrics)
            self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

            # Append to existing file if it exists
            if self.metrics_file.exists():
                existing_df = pd.read_csv(self.metrics_file)
                df = pd.concat([existing_df, df], ignore_index=True)

            df.to_csv(self.metrics_file, index=False)
            log_info(f"Saved {len(self.metrics)} performance metrics to {self.metrics_file}")
            self.metrics = []

    def get_summary(self, operation=None):
        """
        Get performance summary statistics.

        Args:
            operation: Filter by specific operation (optional)

        Returns:
            Dictionary with summary statistics
        """
        if not self.metrics_file.exists():
            return {}

        df = pd.read_csv(self.metrics_file)

        if operation:
            df = df[df["operation"] == operation]

        if df.empty:
            return {}

        summary = {
            "total_operations": len(df),
            "avg_duration": df["duration_seconds"].mean(),
            "min_duration": df["duration_seconds"].min(),
            "max_duration": df["duration_seconds"].max(),
            "total_duration": df["duration_seconds"].sum(),
        }

        if "rows_processed" in df.columns:
            total_rows = df["rows_processed"].sum()
            if total_rows > 0:
                summary["total_rows"] = int(total_rows)
                summary["avg_throughput"] = total_rows / df["duration_seconds"].sum()

        return summary


def timer(func):
    """
    Decorator to time function execution.

    Usage:
        @timer
        def my_function():
            pass
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        log_info(f"{func.__name__} completed in {duration:.3f} seconds")
        return result

    return wrapper


def profile_function(monitor, operation_name=None):
    """
    Decorator to profile function execution and record metrics.

    Args:
        monitor: PerformanceMonitor instance
        operation_name: Name for the operation (defaults to function name)

    Usage:
        @profile_function(monitor, "data_fetch")
        def fetch_data():
            pass
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            start_time = time.time()

            result = func(*args, **kwargs)

            duration = time.time() - start_time

            # Try to get row count if result is a DataFrame
            rows = None
            if isinstance(result, pd.DataFrame):
                rows = len(result)

            monitor.record_metric(op_name, duration, rows_processed=rows)

            return result

        return wrapper

    return decorator


class DataFrameOptimizer:
    """
    Provides optimization utilities for pandas DataFrames.
    """

    @staticmethod
    def optimize_dtypes(df):
        """
        Optimize DataFrame dtypes to reduce memory usage.

        Args:
            df: pandas DataFrame

        Returns:
            Optimized DataFrame and memory savings info
        """
        initial_memory = df.memory_usage(deep=True).sum() / 1024**2  # MB

        # Optimize numeric columns
        for col in df.select_dtypes(include=["int"]).columns:
            df[col] = pd.to_numeric(df[col], downcast="integer")

        for col in df.select_dtypes(include=["float"]).columns:
            df[col] = pd.to_numeric(df[col], downcast="float")

        # Optimize object columns to category if beneficial
        for col in df.select_dtypes(include=["object"]).columns:
            num_unique = df[col].nunique()
            num_total = len(df[col])
            if num_unique / num_total < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype("category")

        final_memory = df.memory_usage(deep=True).sum() / 1024**2  # MB
        savings = initial_memory - final_memory
        savings_pct = (savings / initial_memory * 100) if initial_memory > 0 else 0

        log_info(f"Memory optimized: {initial_memory:.2f}MB -> {final_memory:.2f}MB (saved {savings_pct:.1f}%)")

        return df, {
            "initial_mb": initial_memory,
            "final_mb": final_memory,
            "savings_mb": savings,
            "savings_pct": savings_pct,
        }

    @staticmethod
    def chunk_processor(filepath, chunk_size=10000, process_func=None):
        """
        Process large CSV files in chunks to reduce memory usage.

        Args:
            filepath: Path to CSV file
            chunk_size: Number of rows per chunk
            process_func: Function to apply to each chunk (optional)

        Yields:
            Processed chunks
        """
        for chunk in pd.read_csv(filepath, chunksize=chunk_size):
            if process_func:
                chunk = process_func(chunk)
            yield chunk


class PerformanceBenchmark:
    """
    Benchmarking utilities for comparing performance.
    """

    @staticmethod
    def benchmark_operation(func, iterations=10, *args, **kwargs):
        """
        Benchmark an operation by running it multiple times.

        Args:
            func: Function to benchmark
            iterations: Number of iterations
            *args, **kwargs: Arguments to pass to function

        Returns:
            Dictionary with benchmark results
        """
        durations = []

        for i in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            duration = time.time() - start_time
            durations.append(duration)

        return {
            "iterations": iterations,
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_duration": sum(durations),
        }


# Global performance monitor
_monitor = None


def get_performance_monitor(metrics_file=None):
    """
    Get or create the global performance monitor instance.

    Args:
        metrics_file: Path to store performance metrics

    Returns:
        PerformanceMonitor instance
    """
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor(metrics_file=metrics_file)
    return _monitor
