"""
Data Caching Utility - Phase 2
Provides caching mechanism for API data to reduce redundant calls and improve performance.
"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from utils.config import get_data_path
from utils.logger import log_error, log_info


class DataCache:
    """
    Simple file-based cache for API data.
    Stores data with metadata (timestamp, parameters) to determine freshness.
    """

    def __init__(self, cache_dir=None, default_ttl_hours=24):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory to store cache files (default: data/cache)
            default_ttl_hours: Default time-to-live for cached data in hours
        """
        if cache_dir is None:
            cache_dir = get_data_path("cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = timedelta(hours=default_ttl_hours)

    def _get_cache_key(self, source, params):
        """
        Generate a unique cache key based on data source and parameters.

        Args:
            source: Data source name (e.g., 'nasa_power', 'era5')
            params: Dictionary of parameters used for the API call

        Returns:
            String cache key
        """
        # Create a deterministic hash from source and params
        param_str = json.dumps(params, sort_keys=True)
        hash_obj = hashlib.md5(f"{source}:{param_str}".encode())
        return f"{source}_{hash_obj.hexdigest()}"

    def _get_cache_paths(self, cache_key):
        """Get file paths for data and metadata."""
        data_path = self.cache_dir / f"{cache_key}.csv"
        meta_path = self.cache_dir / f"{cache_key}.meta.json"
        return data_path, meta_path

    def get(self, source, params, ttl_hours=None):
        """
        Retrieve cached data if available and fresh.

        Args:
            source: Data source name
            params: Parameters used for the API call
            ttl_hours: Time-to-live in hours (uses default if None)

        Returns:
            pandas DataFrame if cache hit and fresh, None otherwise
        """
        cache_key = self._get_cache_key(source, params)
        data_path, meta_path = self._get_cache_paths(cache_key)

        # Check if cache files exist
        if not data_path.exists() or not meta_path.exists():
            log_info(f"Cache miss for {source}")
            return None

        # Load metadata
        try:
            with open(meta_path, "r") as f:
                metadata = json.load(f)

            # Check if cache is still fresh
            cached_time = datetime.fromisoformat(metadata["timestamp"])
            ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
            age = datetime.now() - cached_time

            if age > ttl:
                log_info(f"Cache expired for {source} (age: {age}, ttl: {ttl})")
                return None

            # Load cached data
            df = pd.read_csv(data_path)
            log_info(f"Cache hit for {source} (age: {age})")
            return df

        except Exception as e:
            log_error(f"Failed to load cache for {source}: {e}")
            return None

    def set(self, source, params, data):
        """
        Store data in cache.

        Args:
            source: Data source name
            params: Parameters used for the API call
            data: pandas DataFrame to cache
        """
        cache_key = self._get_cache_key(source, params)
        data_path, meta_path = self._get_cache_paths(cache_key)

        try:
            # Save data
            data.to_csv(data_path, index=False)

            # Save metadata
            metadata = {
                "source": source,
                "params": params,
                "timestamp": datetime.now().isoformat(),
                "rows": len(data),
                "columns": list(data.columns),
            }
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)

            log_info(f"Cached {len(data)} rows for {source}")

        except Exception as e:
            log_error(f"Failed to cache data for {source}: {e}")

    def clear(self, source=None):
        """
        Clear cache files.

        Args:
            source: If specified, only clear cache for this source.
                   If None, clear all cache files.
        """
        if source:
            # Clear specific source
            pattern = f"{source}_*.csv"
            count = 0
            for file in self.cache_dir.glob(pattern):
                file.unlink()
                # Also remove metadata
                meta_file = file.with_suffix(".meta.json")
                if meta_file.exists():
                    meta_file.unlink()
                count += 1
            log_info(f"Cleared {count} cache files for {source}")
        else:
            # Clear all cache
            count = 0
            for file in self.cache_dir.glob("*"):
                file.unlink()
                count += 1
            log_info(f"Cleared all {count} cache files")

    def get_cache_info(self):
        """
        Get information about cached data.

        Returns:
            List of dictionaries with cache metadata
        """
        info = []
        for meta_file in self.cache_dir.glob("*.meta.json"):
            try:
                with open(meta_file, "r") as f:
                    metadata = json.load(f)
                    cached_time = datetime.fromisoformat(metadata["timestamp"])
                    age = datetime.now() - cached_time
                    metadata["age_hours"] = age.total_seconds() / 3600
                    info.append(metadata)
            except Exception:
                continue
        return info


# Global cache instance
_cache = None


def get_cache(cache_dir=None, default_ttl_hours=24):
    """
    Get or create the global cache instance.

    Args:
        cache_dir: Directory to store cache files
        default_ttl_hours: Default time-to-live for cached data in hours

    Returns:
        DataCache instance
    """
    global _cache
    if _cache is None:
        _cache = DataCache(cache_dir=cache_dir, default_ttl_hours=default_ttl_hours)
    return _cache
