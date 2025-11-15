"""
Main entry point for Phase 2 pipeline - Tanzania Climate Prediction.
"""

import time
import logging
import argparse
from utils.logger import setup_logging
from utils.config import validate_environment
from modules.ingestion import (
    nasa_power_ingestion,
    era5_ingestion,
    chirps_ingestion,
    ndvi_ingestion,
    ocean_indices_ingestion
)
from modules.processing import (
    process_nasa_power,
    process_era5,
    process_chirps,
    process_ndvi,
    process_ocean_indices
)
from modules.processing.merge_processed import merge_all  # <- added import

def run_pipeline(debug=False, start_year=2000, end_year=2023):
    start_time = time.time()
    setup_logging(logging.DEBUG if debug else logging.INFO)
    logger = logging.getLogger(__name__)

    # If debug flag is used we treat the run as a dry-run for ingestion
    dry_run = bool(debug)

    validate_environment()
    logger.info("Starting Phase 2 pipeline...")
    logger.info(f"Data range: {start_year}-{end_year} ({end_year - start_year + 1} years)")

    # === INGESTION ===
    stages = [
        ("NASA POWER", nasa_power_ingestion.fetch_data),
        ("ERA5", era5_ingestion.fetch_data),
        ("CHIRPS", chirps_ingestion.fetch_data),
        ("NDVI", ndvi_ingestion.fetch_data),
        ("Ocean Indices", ocean_indices_ingestion.fetch_data)
    ]

    ingested = {}
    for name, func in stages:
        t0 = time.time()
        logger.info(f"Ingesting {name} data...")
        try:
            ingested[name] = func(dry_run=dry_run, start_year=start_year, end_year=end_year)
        except TypeError:
            # backward compatibility: some fetch_data() may not accept these kwargs
            try:
                ingested[name] = func(dry_run=dry_run)
            except TypeError:
                ingested[name] = func()
        logger.info(f"{name} ingestion completed in {time.time() - t0:.2f}s")

    # === PROCESSING ===
    processing_stages = [
        ("NASA POWER", process_nasa_power.process, ingested.get("NASA POWER")),
        ("ERA5", process_era5.process, ingested.get("ERA5")),
        ("CHIRPS", process_chirps.process, ingested.get("CHIRPS")),
        ("NDVI", process_ndvi.process, ingested.get("NDVI")),
        ("Ocean Indices", process_ocean_indices.process, ingested.get("Ocean Indices"))
    ]

    for name, func, data in processing_stages:
        t0 = time.time()
        logger.info(f"Processing {name} data...")
        try:
            func(data)
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
            raise
        logger.info(f"{name} processed in {time.time() - t0:.2f}s")

    # === MERGE ALL PROCESSED DATA ===
    logger.info("Merging all processed datasets into master CSV...")
    try:
        merge_all()
        logger.info("Master CSV created successfully.")
    except Exception as e:
        logger.error(f"Error merging datasets: {e}")
        raise

    logger.info(f"Phase 2 pipeline completed successfully in {time.time() - start_time:.2f}s!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug logging (also sets dry-run for ingestion)")
    parser.add_argument("--start-year", type=int, default=2000, help="Start year for data ingestion (default: 2000)")
    parser.add_argument("--end-year", type=int, default=2023, help="End year for data ingestion (default: 2023)")
    args = parser.parse_args()
    run_pipeline(debug=args.debug, start_year=args.start_year, end_year=args.end_year)

