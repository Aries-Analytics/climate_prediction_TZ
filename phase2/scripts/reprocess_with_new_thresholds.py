"""
Reprocess CHIRPS and NDVI data with updated trigger thresholds.

This script reprocesses only the trigger calculations without re-ingesting data.
Much faster than running the full pipeline.
"""

import pandas as pd
from pathlib import Path
import sys
import time

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from modules.processing import process_chirps, process_ndvi, process_ocean_indices
from modules.processing.merge_processed import merge_all
from utils.logger import setup_logging
import logging


def main():
    """Reprocess data with new thresholds."""
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("=" * 70)
    print("REPROCESSING WITH NEW TRIGGER THRESHOLDS")
    print("=" * 70)
    
    start_time = time.time()
    
    # Load raw data
    chirps_raw_path = Path('data/raw/chirps_raw.csv')
    ndvi_raw_path = Path('data/raw/ndvi_raw.csv')
    ocean_raw_path = Path('data/raw/ocean_indices_raw.csv')
    
    if not chirps_raw_path.exists():
        logger.error(f"Raw CHIRPS data not found: {chirps_raw_path}")
        return
    
    if not ndvi_raw_path.exists():
        logger.error(f"Raw NDVI data not found: {ndvi_raw_path}")
        return
    
    logger.info("Loading raw data...")
    chirps_raw = pd.read_csv(chirps_raw_path)
    ndvi_raw = pd.read_csv(ndvi_raw_path)
    
    logger.info(f"  CHIRPS: {len(chirps_raw)} records")
    logger.info(f"  NDVI: {len(ndvi_raw)} records")
    
    # Reprocess CHIRPS with new thresholds
    logger.info("\nReprocessing CHIRPS data with new flood/drought thresholds...")
    t0 = time.time()
    process_chirps.process(chirps_raw)
    logger.info(f"  Completed in {time.time() - t0:.2f}s")
    
    # Reprocess NDVI with new thresholds
    logger.info("\nReprocessing NDVI data with new crop failure thresholds...")
    t0 = time.time()
    process_ndvi.process(ndvi_raw)
    logger.info(f"  Completed in {time.time() - t0:.2f}s")
    
    # Reprocess ocean indices (for completeness)
    if ocean_raw_path.exists():
        logger.info("\nReprocessing Ocean Indices data...")
        t0 = time.time()
        ocean_raw = pd.read_csv(ocean_raw_path)
        process_ocean_indices.process(ocean_raw)
        logger.info(f"  Completed in {time.time() - t0:.2f}s")
    
    # Regenerate master dataset
    logger.info("\nRegenerating master dataset...")
    t0 = time.time()
    merge_all()
    logger.info(f"  Completed in {time.time() - t0:.2f}s")
    
    # Verify trigger rates
    logger.info("\n" + "=" * 70)
    logger.info("VERIFICATION")
    logger.info("=" * 70)
    
    chirps_processed = pd.read_csv('outputs/processed/chirps_processed.csv')
    ndvi_processed = pd.read_csv('outputs/processed/ndvi_processed.csv')
    
    flood_rate = chirps_processed['flood_trigger'].mean()
    drought_rate = chirps_processed['drought_trigger'].mean()
    crop_rate = ndvi_processed['crop_failure_trigger'].mean()
    
    logger.info(f"\nTrigger Rates:")
    logger.info(f"  Flood: {flood_rate:.2%} (target: 5-15%)")
    logger.info(f"  Drought: {drought_rate:.2%} (target: 8-20%)")
    logger.info(f"  Crop Failure: {crop_rate:.2%} (target: 3-10%)")
    
    # Check if rates are in target ranges
    flood_ok = 0.05 <= flood_rate <= 0.15
    drought_ok = 0.08 <= drought_rate <= 0.20
    crop_ok = 0.03 <= crop_rate <= 0.10
    
    logger.info(f"\nStatus:")
    logger.info(f"  Flood: {'✓ PASS' if flood_ok else '✗ FAIL'}")
    logger.info(f"  Drought: {'✓ PASS' if drought_ok else '✗ FAIL'}")
    logger.info(f"  Crop Failure: {'✓ PASS' if crop_ok else '✗ FAIL'}")
    
    logger.info(f"\nTotal time: {time.time() - start_time:.2f}s")
    
    if flood_ok and drought_ok and crop_ok:
        logger.info("\n✓ All trigger rates within target ranges!")
    else:
        logger.warning("\n⚠ Some trigger rates outside target ranges. May need further calibration.")
    
    print("\n" + "=" * 70)
    print("REPROCESSING COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
