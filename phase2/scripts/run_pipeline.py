"""
Main entry point for Phase 2 data pipeline - Tanzania Climate Prediction.

This is a convenience wrapper that delegates to the actual implementation
in pipelines/run_data_pipeline.py

Usage:
    python run_pipeline.py [--debug] [--start-year YEAR] [--end-year YEAR]

Examples:
    # Run in debug mode (dry-run with mock data)
    python run_pipeline.py --debug

    # Run for specific year range
    python run_pipeline.py --start-year 2020 --end-year 2023

    # Full production run
    python run_pipeline.py
"""

from pipelines.run_data_pipeline import run_pipeline

__all__ = ["run_pipeline"]

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tanzania Climate Prediction - Data Pipeline")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging and dry-run mode (uses mock data)")
    parser.add_argument("--start-year", type=int, default=2000, help="Start year for data ingestion (default: 2000)")
    parser.add_argument("--end-year", type=int, default=2023, help="End year for data ingestion (default: 2023)")

    args = parser.parse_args()
    run_pipeline(debug=args.debug, start_year=args.start_year, end_year=args.end_year)
