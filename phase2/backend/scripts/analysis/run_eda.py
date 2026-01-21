"""
Run Exploratory Data Analysis (EDA) on processed datasets.

This script performs EDA on:
1. Individual processed datasets (before merging)
2. Merged dataset (after merging)
3. Comparison between before and after merging
"""

import logging
from pathlib import Path

import pandas as pd
from utils.eda import compare_datasets, perform_eda
from utils.logger import log_info, setup_logging


def main():
    """Run EDA on all processed datasets."""
    setup_logging(logging.INFO)
    log_info("=" * 80)
    log_info("EXPLORATORY DATA ANALYSIS")
    log_info("=" * 80)

    # Define paths (check both locations)
    processed_dir = Path("outputs/processed")
    if not processed_dir.exists():
        processed_dir = Path("data/processed")

    # Check if processed data exists
    if not processed_dir.exists():
        log_info("No processed data found. Please run the pipeline first.")
        log_info("Run: python run_pipeline.py --debug")
        return

    log_info(f"Using processed data from: {processed_dir}")

    # Load individual processed datasets
    datasets_before = {}

    dataset_files = [
        "chirps_processed.csv",
        "ndvi_processed.csv",
        "ocean_indices_processed.csv",
        "nasa_power_processed.csv",
        "era5_processed.csv",
    ]

    log_info("\n" + "=" * 80)
    log_info("PART 1: EDA ON INDIVIDUAL DATASETS (BEFORE MERGING)")
    log_info("=" * 80 + "\n")

    for filename in dataset_files:
        filepath = processed_dir / filename
        if filepath.exists():
            dataset_name = filename.replace("_processed.csv", "").upper()
            log_info(f"\nLoading {dataset_name}...")
            df = pd.read_csv(filepath)
            datasets_before[dataset_name] = df

            # Perform EDA
            perform_eda(df, dataset_name=dataset_name, output_dir="outputs/eda/before_merge")
        else:
            log_info(f"File not found: {filename}")

    # Load merged dataset (check both possible names)
    merged_file = processed_dir / "master_dataset.csv"
    if not merged_file.exists():
        merged_file = processed_dir / "merged_data.csv"

    if merged_file.exists():
        log_info("\n" + "=" * 80)
        log_info("PART 2: EDA ON MERGED DATASET (AFTER MERGING)")
        log_info("=" * 80 + "\n")

        log_info("Loading merged dataset...")
        df_merged = pd.read_csv(merged_file)

        # Perform EDA on merged dataset
        perform_eda(df_merged, dataset_name="MERGED", output_dir="outputs/eda/after_merge")

        # Compare before and after
        if datasets_before:
            log_info("\n" + "=" * 80)
            log_info("PART 3: COMPARISON (BEFORE vs AFTER MERGING)")
            log_info("=" * 80 + "\n")

            compare_datasets(datasets_before, df_merged, output_dir="outputs/eda")
    else:
        log_info("\nMerged dataset not found. Skipping merged dataset EDA.")

    log_info("\n" + "=" * 80)
    log_info("EDA COMPLETE")
    log_info("=" * 80)
    log_info("\nResults saved to: outputs/eda/")
    log_info("  - before_merge/: EDA for individual datasets")
    log_info("  - after_merge/: EDA for merged dataset")
    log_info("  - merge_comparison_report.txt: Comparison report")


if __name__ == "__main__":
    main()
