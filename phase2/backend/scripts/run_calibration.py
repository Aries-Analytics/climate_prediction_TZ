"""
Run trigger calibration using existing processed data.

This script loads existing processed CHIRPS and NDVI data and runs the
calibration workflow to generate trigger_thresholds.yaml configuration.

If processed data doesn't exist, it will process the raw data first.
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging, log_info, log_error, log_warning
from modules.calibration.generate_config import generate_calibrated_config, load_historical_data
from modules.processing import process_chirps, process_ndvi
import logging


def process_raw_data_if_needed():
    """Process raw data if processed files don't exist."""
    chirps_processed = Path("outputs/processed/chirps_processed.csv")
    ndvi_processed = Path("outputs/processed/ndvi_processed.csv")
    
    # Check if processed files exist
    if chirps_processed.exists() and ndvi_processed.exists():
        log_info("Processed data files already exist, skipping processing")
        return
    
    log_info("Processed data not found, processing raw data...")
    
    # Process CHIRPS if needed
    if not chirps_processed.exists():
        log_info("Processing CHIRPS raw data...")
        chirps_raw = Path("data/raw/chirps_raw.csv")
        if not chirps_raw.exists():
            log_error(f"CHIRPS raw data not found: {chirps_raw}")
            raise FileNotFoundError(f"CHIRPS raw data not found: {chirps_raw}")
        
        df_chirps = pd.read_csv(chirps_raw)
        log_info(f"Loaded {len(df_chirps)} CHIRPS raw records")
        process_chirps.process(df_chirps)
        log_info("CHIRPS processing complete")
    
    # Process NDVI if needed
    if not ndvi_processed.exists():
        log_info("Processing NDVI raw data...")
        ndvi_raw = Path("data/raw/ndvi_raw.csv")
        if not ndvi_raw.exists():
            log_error(f"NDVI raw data not found: {ndvi_raw}")
            raise FileNotFoundError(f"NDVI raw data not found: {ndvi_raw}")
        
        df_ndvi = pd.read_csv(ndvi_raw)
        log_info(f"Loaded {len(df_ndvi)} NDVI raw records")
        process_ndvi.process(df_ndvi)
        log_info("NDVI processing complete")


def main():
    """Main calibration workflow."""
    setup_logging(logging.INFO)
    
    log_info("=" * 80)
    log_info("INSURANCE TRIGGER CALIBRATION WORKFLOW")
    log_info("=" * 80)
    
    try:
        # Step 1: Ensure processed data exists
        log_info("\nStep 1: Checking for processed data...")
        process_raw_data_if_needed()
        
        # Step 2: Load historical data
        log_info("\nStep 2: Loading historical data...")
        df_chirps, df_ndvi = load_historical_data()
        
        # Step 3: Run calibration and generate config
        log_info("\nStep 3: Running calibration workflow...")
        config = generate_calibrated_config(
            df_chirps,
            df_ndvi,
            output_path="configs/trigger_thresholds.yaml"
        )
        
        log_info("\n" + "=" * 80)
        log_info("CALIBRATION WORKFLOW COMPLETED SUCCESSFULLY!")
        log_info("=" * 80)
        log_info("\nGenerated files:")
        log_info("  - configs/trigger_thresholds.yaml")
        log_info("  - data/outputs/calibration/threshold_analysis_report_*.json")
        log_info("  - data/outputs/calibration/threshold_analysis_summary_*.txt")
        log_info("\nNext steps:")
        log_info("  1. Review the generated configuration file")
        log_info("  2. Review the threshold analysis report")
        log_info("  3. Proceed to task 5: Update CHIRPS processing module")
        
    except Exception as e:
        log_error(f"\nCalibration workflow failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
