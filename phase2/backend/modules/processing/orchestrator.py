"""
Data Processing Orchestrator
Coordinates processing of all data sources for all locations and merges results.

Usage:
    python modules/processing/orchestrator.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import yaml

from modules.processing.merge_processed import merge_all

# Import processing modules
from modules.processing.process_chirps import process as process_chirps
from modules.processing.process_era5 import process as process_era5
from modules.processing.process_nasa_power import process as process_nasa_power
from modules.processing.process_ndvi import process as process_ndvi
from modules.processing.process_ocean_indices import process as process_ocean_indices
from utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


def load_locations_config() -> Dict:
    """Load locations configuration from YAML file"""
    config_path = Path("configs/locations_config.yaml")

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    return config


def process_source(source_name: str, locations: List[str]) -> Dict:
    """
    Process a single data source for all locations.

    Args:
        source_name: Name of the source (chirps, nasa_power, era5, ndvi, ocean_indices)
        locations: List of location names

    Returns:
        Dictionary with processing results
    """
    logger.info(f"{'='*80}")
    logger.info(f"Processing {source_name.upper()}")
    logger.info(f"{'='*80}")

    result = {"source": source_name, "status": "pending", "locations_processed": [], "errors": []}

    try:
        # Handle ocean_indices special case FIRST (different file path)
        if source_name == "ocean_indices":
            raw_data_path = Path("data/raw/ocean_indices_raw.csv")

            if not raw_data_path.exists():
                raise FileNotFoundError(f"Raw data not found: {raw_data_path}")

            logger.info(f"Loading raw data from {raw_data_path}...")
            data = pd.read_csv(raw_data_path)
            logger.info(f"Loaded {len(data)} ocean indices records")
            processed_data = process_ocean_indices(data)
            result["status"] = "success"
            result["locations_processed"] = ["global"]

        else:
            # Load the combined raw data for other sources
            raw_data_path = Path(f"data/raw/{source_name}_combined.csv")

            if not raw_data_path.exists():
                raise FileNotFoundError(f"Raw data not found: {raw_data_path}")

            logger.info(f"Loading raw data from {raw_data_path}...")
            data = pd.read_csv(raw_data_path)
            logger.info(f"Loaded {len(data)} records")

            # Process based on source type
            if source_name == "chirps":
                processed_data = process_chirps(data)
                result["status"] = "success"
                result["locations_processed"] = locations

            elif source_name == "nasa_power":
                processed_data = process_nasa_power(data)
                result["status"] = "success"
                result["locations_processed"] = locations

            elif source_name == "era5":
                processed_data = process_era5(data)
                result["status"] = "success"
                result["locations_processed"] = locations

            elif source_name == "ndvi":
                processed_data = process_ndvi(data)
                result["status"] = "success"
                result["locations_processed"] = locations

            else:
                raise ValueError(f"Unknown source: {source_name}")

        logger.info(f"✓ {source_name.upper()}: Processing complete - {len(processed_data)} records")

    except Exception as e:
        logger.error(f"✗ {source_name.upper()}: Processing failed - {e}")
        result["status"] = "failed"
        result["errors"].append(str(e))

    return result


def run_processing_pipeline(sources: Optional[List[str]] = None, skip_merge: bool = False) -> Dict:
    """
    Run the complete processing pipeline.

    Args:
        sources: List of sources to process. If None, processes all.
        skip_merge: If True, skips the merge step (useful for debugging)

    Returns:
        Dictionary with pipeline results
    """
    logger.info("=" * 80)
    logger.info("DATA PROCESSING PIPELINE")
    logger.info("=" * 80)
    logger.info("")

    # Load configuration
    try:
        config = load_locations_config()
        locations = list(config["locations"].keys())
        logger.info(f"Loaded configuration: {len(locations)} locations")
        logger.info(f"Locations: {', '.join(locations)}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return {"status": "failed", "error": str(e)}

    # Define processing order (ocean_indices first as it's global)
    all_sources = ["ocean_indices", "chirps", "nasa_power", "era5", "ndvi"]

    # Use specified sources or all
    sources_to_process = sources if sources else all_sources

    logger.info(f"\nProcessing {len(sources_to_process)} data sources:")
    for source in sources_to_process:
        logger.info(f"  - {source}")
    logger.info("")

    # Process each source
    results = []
    start_time = datetime.now()

    for source in sources_to_process:
        source_result = process_source(source, locations)
        results.append(source_result)
        logger.info("")

    # Merge processed data
    if not skip_merge:
        logger.info("=" * 80)
        logger.info("MERGING PROCESSED DATA")
        logger.info("=" * 80)

        try:
            merge_all()
            logger.info("✓ Merge complete")
            merge_status = "success"
        except Exception as e:
            logger.error(f"✗ Merge failed: {e}")
            merge_status = "failed"
    else:
        logger.info("Skipping merge step (skip_merge=True)")
        merge_status = "skipped"

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("")
    logger.info("=" * 80)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 80)

    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")

    logger.info(f"Total Sources: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"Merge Status: {merge_status}")
    logger.info("")

    # Detailed results
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        logger.info(f"{status_icon} {result['source']:20s} | {result['status']}")
        if result["errors"]:
            for error in result["errors"]:
                logger.info(f"    Error: {error}")

    logger.info("")

    # Final status
    pipeline_status = {
        "status": (
            "success" if failed == 0 and merge_status == "success" else "partial" if failed < len(results) else "failed"
        ),
        "total_sources": len(results),
        "successful": successful,
        "failed": failed,
        "merge_status": merge_status,
        "duration_seconds": duration,
        "results": results,
    }

    if pipeline_status["status"] == "success":
        logger.info("🎉 Processing pipeline completed successfully!")
    elif pipeline_status["status"] == "partial":
        logger.info("⚠️  Processing pipeline completed with some errors")
    else:
        logger.info("❌ Processing pipeline failed")

    logger.info("=" * 80)

    return pipeline_status


def main():
    """Main entry point"""
    setup_logging()

    # Run complete pipeline
    result = run_processing_pipeline()

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
