"""
Fetch Real Data - Test Script

Fetches real data from available sources (no API keys required):
1. CHIRPS - Rainfall data
2. Ocean Indices - ENSO/IOD data
3. NASA POWER - Temperature/solar data

Then runs the full processing pipeline.
"""

import logging
import time

from utils.logger import log_error, log_info, setup_logging

# Import feature engineering
from feature_engineering.engineer_features import build_features

# Import ingestion modules
from modules.ingestion import chirps_ingestion, nasa_power_ingestion, ocean_indices_ingestion

# Import processing modules
from modules.processing import process_chirps, process_nasa_power, process_ocean_indices

# Import merge module
from modules.processing.merge_processed import merge_all


def main():
    """Fetch real data and run processing pipeline."""

    setup_logging(logging.INFO)
    log_info("=" * 80)
    log_info("FETCHING REAL DATA - Test Run")
    log_info("=" * 80)

    # Use a smaller date range for testing (last 2 years)
    start_year = 2022
    end_year = 2023

    log_info(f"Date range: {start_year}-{end_year}")
    log_info("")

    # Track what we successfully fetch
    fetched_data = {}
    processed_data = {}

    # ========================================
    # 1. OCEAN INDICES (fastest, smallest)
    # ========================================
    log_info("=" * 80)
    log_info("1. FETCHING OCEAN INDICES DATA")
    log_info("=" * 80)
    try:
        t0 = time.time()
        ocean_raw = ocean_indices_ingestion.fetch_data(dry_run=False, start_year=start_year, end_year=end_year)
        elapsed = time.time() - t0

        if ocean_raw is not None and not ocean_raw.empty:
            log_info(f"✅ Ocean Indices fetched: {len(ocean_raw)} records in {elapsed:.1f}s")
            fetched_data["ocean_indices"] = ocean_raw

            # Process immediately
            log_info("Processing Ocean Indices...")
            ocean_processed = process_ocean_indices.process(ocean_raw)
            processed_data["ocean_indices"] = ocean_processed
            log_info(f"✅ Ocean Indices processed: {ocean_processed.shape}")
        else:
            log_error("❌ Ocean Indices fetch returned empty data")
    except Exception as e:
        log_error(f"❌ Ocean Indices fetch failed: {e}")

    log_info("")

    # ========================================
    # 2. NASA POWER
    # ========================================
    log_info("=" * 80)
    log_info("2. FETCHING NASA POWER DATA")
    log_info("=" * 80)
    try:
        t0 = time.time()
        nasa_raw = nasa_power_ingestion.fetch_data(dry_run=False, start_year=start_year, end_year=end_year)
        elapsed = time.time() - t0

        if nasa_raw is not None and not nasa_raw.empty:
            log_info(f"✅ NASA POWER fetched: {len(nasa_raw)} records in {elapsed:.1f}s")
            fetched_data["nasa_power"] = nasa_raw

            # Process immediately
            log_info("Processing NASA POWER...")
            nasa_processed = process_nasa_power.process(nasa_raw)
            processed_data["nasa_power"] = nasa_processed
            log_info(f"✅ NASA POWER processed: {nasa_processed.shape}")
        else:
            log_error("❌ NASA POWER fetch returned empty data")
    except Exception as e:
        log_error(f"❌ NASA POWER fetch failed: {e}")

    log_info("")

    # ========================================
    # 3. CHIRPS (largest, may take time)
    # ========================================
    log_info("=" * 80)
    log_info("3. FETCHING CHIRPS DATA")
    log_info("=" * 80)
    log_info("⚠️  Note: CHIRPS downloads NetCDF files, may take several minutes...")
    try:
        t0 = time.time()
        chirps_raw = chirps_ingestion.fetch_data(dry_run=False, start_year=start_year, end_year=end_year)
        elapsed = time.time() - t0

        if chirps_raw is not None and not chirps_raw.empty:
            log_info(f"✅ CHIRPS fetched: {len(chirps_raw)} records in {elapsed:.1f}s")
            fetched_data["chirps"] = chirps_raw

            # Process immediately
            log_info("Processing CHIRPS...")
            chirps_processed = process_chirps.process(chirps_raw)
            processed_data["chirps"] = chirps_processed
            log_info(f"✅ CHIRPS processed: {chirps_processed.shape}")
        else:
            log_error("❌ CHIRPS fetch returned empty data")
    except Exception as e:
        log_error(f"❌ CHIRPS fetch failed: {e}")
        log_info("Note: CHIRPS may fail due to server issues or file availability")

    log_info("")

    # ========================================
    # SUMMARY
    # ========================================
    log_info("=" * 80)
    log_info("FETCH SUMMARY")
    log_info("=" * 80)
    log_info(f"Successfully fetched: {len(fetched_data)}/3 data sources")
    log_info(f"Successfully processed: {len(processed_data)}/3 data sources")

    for source in ["ocean_indices", "nasa_power", "chirps"]:
        if source in fetched_data:
            log_info(f"  ✅ {source}: {len(fetched_data[source])} records")
        else:
            log_info(f"  ❌ {source}: Failed to fetch")

    log_info("")

    # ========================================
    # MERGE AND FEATURE ENGINEERING
    # ========================================
    if len(processed_data) >= 2:
        log_info("=" * 80)
        log_info("MERGING PROCESSED DATA")
        log_info("=" * 80)

        try:
            # Merge all processed data
            # merge_all() automatically discovers and merges all processed files
            merged_df = merge_all()

            log_info(f"✅ Merged dataset: {merged_df.shape}")
            log_info(f"   Columns: {len(merged_df.columns)}")
            log_info("")

            # Feature engineering
            log_info("=" * 80)
            log_info("FEATURE ENGINEERING")
            log_info("=" * 80)

            final_df = build_features(merged_df)
            log_info(f"✅ Final dataset: {final_df.shape}")
            log_info("")

            # Display sample
            log_info("=" * 80)
            log_info("SAMPLE DATA (first 5 rows)")
            log_info("=" * 80)
            print(final_df.head())
            log_info("")

            # Display available features
            log_info("=" * 80)
            log_info("AVAILABLE FEATURES")
            log_info("=" * 80)
            log_info(f"Total features: {len(final_df.columns)}")
            log_info("")
            log_info("Feature list:")
            for i, col in enumerate(final_df.columns, 1):
                log_info(f"  {i}. {col}")

        except Exception as e:
            log_error(f"❌ Merge/Feature engineering failed: {e}")
            import traceback

            log_error(traceback.format_exc())
    else:
        log_error("❌ Not enough data sources to merge (need at least 2)")

    log_info("")
    log_info("=" * 80)
    log_info("✅ REAL DATA FETCH COMPLETE")
    log_info("=" * 80)


if __name__ == "__main__":
    main()
