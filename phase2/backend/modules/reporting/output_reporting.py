"""
Output Reporting Module  Phase 2
---------------------------------
Handles final reporting, saving results, and generating summaries
after the data processing pipeline completes.
"""

import json
import logging
import os

import pandas as pd

from utils.config import get_data_path

logger = logging.getLogger(__name__)


def save_summary_report(summary_dict: dict, filename: str = "summary_report.json"):
    """
    Save pipeline summary metrics or metadata as JSON.
    """
    output_path = get_data_path("outputs", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=4)
    logger.info(f"Summary report saved: {output_path}")
    return output_path


def save_processed_data(df: pd.DataFrame, filename: str = "processed_data.csv"):
    """
    Save the final processed DataFrame to the outputs directory.
    """
    output_path = get_data_path("outputs", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved: {output_path}")
    return output_path


def generate_report_summary():
    """
    Placeholder for a more advanced reporting function that could:
    - Summarize key statistics
    - Generate plots or charts
    - Export results for dashboards
    """
    logger.info("Generating summary report... (dry run)")
    summary = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "status": "success",
        "records_processed": 0,
        "notes": "Dry run summary - replace with real metrics later",
    }

    save_summary_report(summary)
    return summary


def run_reporting_stage(processed_data=None):
    """
    Orchestrates the reporting stage after all processing modules complete.
    """
    logger.info("Running reporting stage...")

    # Example: if processed_data is a dict of DataFrames
    if processed_data:
        for name, df in processed_data.items():
            if isinstance(df, pd.DataFrame):
                save_processed_data(df, f"{name}_processed.csv")

    summary = generate_report_summary()
    logger.info("Reporting stage completed.")
    return summary
