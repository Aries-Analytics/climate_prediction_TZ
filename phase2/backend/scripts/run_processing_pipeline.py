
import os
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.processing import (
    process_nasa_power,
    process_chirps,
    process_era5,
    process_ndvi,
    process_ocean_indices,
    merge_processed
)
from utils.logger import setup_logging, log_info, log_error

def run_pipeline():
    setup_logging()
    log_info("Starting Data Processing Pipeline...")

    # Define source files mapping
    # Note: Orchestrator now produces "_combined.csv" files containing data for all locations
    sources = {
        "NASA_POWER": "nasa_power_combined.csv",
        "CHIRPS": "chirps_combined.csv",
        "ERA5": "era5_combined.csv",
        "NDVI": "ndvi_combined.csv",
        "OCEAN_INDICES": "ocean_indices_raw.csv"  # Global data remains raw
    }
    
    # Define processing functions
    processors = {
        "NASA_POWER": process_nasa_power.process,
        "CHIRPS": process_chirps.process,
        "ERA5": process_era5.process,
        "NDVI": process_ndvi.process,
        "OCEAN_INDICES": process_ocean_indices.process
    }

    from utils.config import get_data_path
    
    for source_name, filename in sources.items():
        try:
            log_info(f"Processing {source_name}...")
            # Load raw data
            raw_path = get_data_path("raw", filename)
            
            if not raw_path.exists():
                log_error(f"Raw data file not found: {raw_path}")
                continue
                
            df = pd.read_csv(raw_path)
            log_info(f"Loaded {len(df)} records from {filename}")
            
            # Run processing
            process_func = processors.get(source_name)
            if process_func:
                process_func(df)
            else:
                log_error(f"No processor found for {source_name}")
                
        except Exception as e:
            log_error(f"Failed to process {source_name}: {e}")

    # Merge all processed data
    try:
        log_info("Merging all processed datasets...")
        merge_processed.merge_all()
        log_info("Pipeline completed successfully!")
    except Exception as e:
        log_error(f"Merge failed: {e}")

if __name__ == "__main__":
    run_pipeline()
