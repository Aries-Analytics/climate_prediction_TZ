"""
Incremental Data Update Utility - Phase 2
Tracks last update timestamps and enables fetching only new data since last update.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from utils.config import get_data_path
from utils.logger import log_error, log_info


class IncrementalUpdateTracker:
    """
    Tracks last update timestamps for data sources to enable incremental updates.
    Stores metadata about the last successful data fetch for each source.
    """

    def __init__(self, metadata_dir=None):
        """
        Initialize the tracker.

        Args:
            metadata_dir: Directory to store metadata files (default: data/metadata)
        """
        if metadata_dir is None:
            metadata_dir = get_data_path("metadata")
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def _get_metadata_path(self, source):
        """Get metadata file path for a data source."""
        return self.metadata_dir / f"{source}_update.json"

    def get_last_update(self, source):
        """
        Get the last update information for a data source.

        Args:
            source: Data source name (e.g., 'nasa_power', 'era5')

        Returns:
            Dictionary with last update info, or None if never updated
        """
        metadata_path = self._get_metadata_path(source)

        if not metadata_path.exists():
            log_info(f"No previous update found for {source}")
            return None

        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            return metadata
        except Exception as e:
            log_error(f"Failed to load update metadata for {source}: {e}")
            return None

    def record_update(self, source, end_year, end_month=12, rows_fetched=0, params=None):
        """
        Record a successful data update.

        Args:
            source: Data source name
            end_year: Last year of data fetched
            end_month: Last month of data fetched (default: 12)
            rows_fetched: Number of rows fetched in this update
            params: Additional parameters used for the fetch
        """
        metadata = {
            "source": source,
            "last_update_timestamp": datetime.now(timezone.utc).isoformat(),
            "last_data_year": end_year,
            "last_data_month": end_month,
            "rows_fetched": rows_fetched,
            "params": params or {},
        }

        metadata_path = self._get_metadata_path(source)

        try:
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            log_info(f"Recorded update for {source}: {end_year}-{end_month:02d}, {rows_fetched} rows")
        except Exception as e:
            log_error(f"Failed to record update metadata for {source}: {e}")

    def get_incremental_range(self, source, requested_start_year, requested_end_year):
        """
        Calculate the date range for incremental update.

        Args:
            source: Data source name
            requested_start_year: User-requested start year
            requested_end_year: User-requested end year

        Returns:
            Tuple of (start_year, start_month, end_year, end_month, is_incremental)
            is_incremental is True if this is an incremental update, False for full fetch
        """
        last_update = self.get_last_update(source)

        if last_update is None:
            # No previous update - fetch full range
            log_info(f"Full fetch for {source}: {requested_start_year}-{requested_end_year}")
            return requested_start_year, 1, requested_end_year, 12, False

        last_year = last_update.get("last_data_year")
        last_month = last_update.get("last_data_month", 12)

        # Calculate next month after last update
        if last_month == 12:
            start_year = last_year + 1
            start_month = 1
        else:
            start_year = last_year
            start_month = last_month + 1

        # Check if we need to fetch anything
        if start_year > requested_end_year:
            log_info(f"Data for {source} is already up to date (last: {last_year}-{last_month:02d})")
            return None, None, None, None, True

        log_info(
            f"Incremental fetch for {source}: {start_year}-{start_month:02d} to {requested_end_year}-12 "
            f"(last update: {last_year}-{last_month:02d})"
        )
        return start_year, start_month, requested_end_year, 12, True

    def merge_with_existing(self, source, new_data, data_path=None):
        """
        Merge new incremental data with existing data.

        Args:
            source: Data source name
            new_data: New DataFrame to merge
            data_path: Path to existing data file (default: data/raw/{source}_raw.csv)

        Returns:
            Merged DataFrame
        """
        if data_path is None:
            data_path = get_data_path("raw", f"{source}_raw.csv")

        data_path = Path(data_path)

        if not data_path.exists():
            log_info(f"No existing data for {source}, using new data only")
            return new_data

        try:
            # Load existing data
            existing_data = pd.read_csv(data_path)
            log_info(f"Loaded {len(existing_data)} existing rows for {source}")

            # Concatenate and remove duplicates
            merged = pd.concat([existing_data, new_data], ignore_index=True)

            # Remove duplicates based on year and month (if present)
            if "year" in merged.columns and "month" in merged.columns:
                merged = merged.drop_duplicates(subset=["year", "month"], keep="last")
            elif "year" in merged.columns:
                merged = merged.drop_duplicates(subset=["year"], keep="last")

            # Sort by year and month
            if "year" in merged.columns:
                sort_cols = ["year"]
                if "month" in merged.columns:
                    sort_cols.append("month")
                merged = merged.sort_values(sort_cols).reset_index(drop=True)

            log_info(f"Merged data for {source}: {len(merged)} total rows ({len(new_data)} new)")
            return merged

        except Exception as e:
            log_error(f"Failed to merge data for {source}: {e}")
            log_info("Using new data only")
            return new_data

    def clear_metadata(self, source=None):
        """
        Clear update metadata.

        Args:
            source: If specified, clear only this source. If None, clear all.
        """
        if source:
            metadata_path = self._get_metadata_path(source)
            if metadata_path.exists():
                metadata_path.unlink()
                log_info(f"Cleared update metadata for {source}")
        else:
            count = 0
            for file in self.metadata_dir.glob("*_update.json"):
                file.unlink()
                count += 1
            log_info(f"Cleared all {count} update metadata files")


# Global tracker instance
_tracker = None


def get_tracker(metadata_dir=None):
    """
    Get or create the global incremental update tracker.

    Args:
        metadata_dir: Directory to store metadata files

    Returns:
        IncrementalUpdateTracker instance
    """
    global _tracker
    if _tracker is None:
        _tracker = IncrementalUpdateTracker(metadata_dir=metadata_dir)
    return _tracker
