"""
Data Ingestion Orchestrator - Phase 2
Master script to coordinate data collection from all sources for all configured locations.
"""

import os
import sys
import yaml
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from modules.ingestion.nasa_power_ingestion import fetch_nasa_power_data
from modules.ingestion.chirps_ingestion import fetch_chirps_data
from modules.ingestion.era5_ingestion import fetch_era5_data
from modules.ingestion.ndvi_ingestion import fetch_ndvi_data
from modules.ingestion.ocean_indices_ingestion import fetch_ocean_indices_data

from utils.logger import log_info, log_error, log_warning, get_logger, setup_logging

# Initialize logger
logger = get_logger("ingestion_orchestrator")


def load_locations_config() -> dict:
    """Load locations from config file"""
    config_path = Path(__file__).resolve().parents[2] / "configs" / "locations_config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def process_location_source(location_name: str, loc_data: dict, source: str, start_year: int, end_year: int) -> tuple:
    """
    Process a single data source for a specific location.
    Returns: (result_dict, dataframe_or_none)
    """
    log_info(f"[{location_name}] Starting ingestion for {source} ({start_year}-{end_year})")
    
    lat = loc_data['latitude']
    lon = loc_data['longitude']
    
    # Define bounds for CHIRPS/NDVI (approximate 0.5 deg box around point)
    bounds = {
        "lat_min": lat - 0.25,
        "lat_max": lat + 0.25,
        "lon_min": lon - 0.25,
        "lon_max": lon + 0.25
    }
    
    try:
        df = None
        count = 0
        if source == "NASA_POWER":
            df = fetch_nasa_power_data(
                latitude=lat,
                longitude=lon,
                start_year=start_year,
                end_year=end_year
            )
            
        elif source == "CHIRPS":
            df = fetch_chirps_data(
                start_year=start_year,
                end_year=end_year,
                bounds=bounds,
                use_gee=True
            )
            
        elif source == "ERA5":
            df = fetch_era5_data(
                latitude=lat,
                longitude=lon,
                start_year=start_year,
                end_year=end_year
            )
            
        elif source == "NDVI":
            df = fetch_ndvi_data(
                start_year=start_year,
                end_year=end_year,
                bounds=bounds,
                use_gee=True
            )
            
        else:
            raise ValueError(f"Unknown source: {source}")
            
        if df is not None:
            count = len(df)
            log_info(f"[{location_name}] {source}: Successfully fetched {count} records")
            
            # Add location metadata to DataFrame if not present
            if 'location' not in df.columns:
                df['location'] = location_name
            df['location_lat'] = lat
            df['location_lon'] = lon
        
        result = {
            "location": location_name,
            "source": source,
            "status": "SUCCESS",
            "records": count
        }
        return result, df
        
    except Exception as e:
        log_error(f"[{location_name}] {source} Failed: {str(e)}")
        result = {
            "location": location_name,
            "source": source,
            "status": "FAILED",
            "error": str(e)
        }
        return result, None


def run_orchestrator(sources: Optional[List[str]] = None, parallel: bool = False):
    """
    Main orchestration loop.
    
    Args:
        sources: List of sources to ingest. If None, runs all.
        parallel: If True, runs locations in parallel.
    """
    setup_logging()
    
    config = load_locations_config()
    locations = config['locations']
    
    # Time period from config
    start_year = config.get('time_period', {}).get('start_year', 2000)
    end_year = config.get('time_period', {}).get('end_year', 2025)
    
    if sources is None:
        sources = ["NASA_POWER", "CHIRPS", "ERA5", "NDVI", "OCEAN_INDICES"]
    
    log_info(f"Starting Phase 2 Ingestion for {len(locations)} locations from {start_year} to {end_year}")
    
    results = []
    
    # Container for accumulating dataframes: {source: [df1, df2, ...]}
    collected_data = {s: [] for s in sources if s != "OCEAN_INDICES"}
    
    # 1. Global Data (Ocean Indices) - Run once
    if "OCEAN_INDICES" in sources:
        try:
            log_info("Fetching Global Ocean Indices...")
            df = fetch_ocean_indices_data(start_year=start_year, end_year=end_year)
            log_info(f"Ocean Indices: Fetched {len(df)} records")
            # Save Global Data Immediately
            from utils.config import get_data_path
            path = get_data_path("raw", "ocean_indices_raw.csv")
            df.to_csv(path, index=False)
            
            results.append({"location": "GLOBAL", "source": "OCEAN_INDICES", "status": "SUCCESS", "records": len(df)})
        except Exception as e:
            log_error(f"Ocean Indices Failed: {e}")
            results.append({"location": "GLOBAL", "source": "OCEAN_INDICES", "status": "FAILED", "error": str(e)})

    # Filter sources to location-specific ones
    loc_sources = [s for s in sources if s != "OCEAN_INDICES"]
    
    if parallel:
        # Parallel execution using ThreadPool
        with ThreadPoolExecutor(max_workers=3) as executor:  # Reduced workers to avoid API limits
            futures = []
            for loc_name, loc_data in locations.items():
                for source in loc_sources:
                    futures.append(
                        executor.submit(
                            process_location_source, 
                            loc_data['name'], 
                            loc_data, 
                            source, 
                            start_year, 
                            end_year
                        )
                    )
            
            for future in as_completed(futures):
                res, df = future.result()
                results.append(res)
                if df is not None:
                    collected_data[res['source']].append(df)
    else:
        # Sequential execution
        for loc_name, loc_data in locations.items():
            for source in loc_sources:
                res, df = process_location_source(
                    loc_data['name'], 
                    loc_data, 
                    source, 
                    start_year, 
                    end_year
                )
                results.append(res)
                if df is not None:
                    collected_data[source].append(df)
    
    # ---------------------------------------------------------
    # Save Combined Data
    # ---------------------------------------------------------
    log_info("Saving combined datasets...")
    from utils.config import get_data_path
    import pandas as pd
    
    for source, dfs in collected_data.items():
        if dfs:
            try:
                combined_df = pd.concat(dfs, ignore_index=True)
                filename = f"{source.lower()}_combined.csv"
                out_path = get_data_path("raw", filename)
                combined_df.to_csv(out_path, index=False)
                log_info(f"Saved combined {source} data to {out_path} ({len(combined_df)} records)")
            except Exception as e:
                log_error(f"Failed to save combined data for {source}: {e}")
        else:
            log_warning(f"No data collected for {source}")

    # Summary
    log_info("="*50)
    log_info("Ingestion Summary")
    log_info("="*50)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    log_info(f"Total Tasks: {len(results)}")
    log_info(f"Successful: {success_count}")
    log_info(f"Failed: {len(results) - success_count}")
    
    for r in results:
        status_icon = "✅" if r['status'] == 'SUCCESS' else "❌"
        location = r.get('location', 'UNKNOWN')
        source = r.get('source', 'UNKNOWN')
        details = f"{r.get('records', 0)} records" if r['status'] == 'SUCCESS' else f"Error: {r.get('error', 'Unknown')}"
        print(f"{status_icon} {location:<15} | {source:<15} | {details}")


if __name__ == "__main__":
    # Example usage: python modules/ingestion/orchestrator.py
    run_orchestrator(parallel=False)
