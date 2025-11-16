"""
Tests for data caching utility
"""

import tempfile

import pandas as pd
from utils.cache import DataCache


def test_cache_basic_operations():
    """Test basic cache set and get operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DataCache(cache_dir=tmpdir, default_ttl_hours=1)

        # Create test data
        df = pd.DataFrame({"year": [2020, 2021], "value": [100, 200]})
        params = {"start_year": 2020, "end_year": 2021}

        # Cache miss on first attempt
        result = cache.get("test_source", params)
        assert result is None

        # Store data in cache
        cache.set("test_source", params, df)

        # Cache hit on second attempt
        result = cache.get("test_source", params)
        assert result is not None
        assert len(result) == 2
        assert list(result.columns) == ["year", "value"]


def test_cache_expiration():
    """Test that cache expires after TTL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DataCache(cache_dir=tmpdir, default_ttl_hours=0.0001)  # Very short TTL

        df = pd.DataFrame({"year": [2020], "value": [100]})
        params = {"start_year": 2020}

        # Store and immediately retrieve
        cache.set("test_source", params, df)
        result = cache.get("test_source", params)
        assert result is not None

        # Wait for expiration (TTL is very short)
        import time

        time.sleep(1)

        # Should be expired now
        result = cache.get("test_source", params, ttl_hours=0.0001)
        assert result is None


def test_cache_different_params():
    """Test that different parameters create different cache entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DataCache(cache_dir=tmpdir)

        df1 = pd.DataFrame({"year": [2020], "value": [100]})
        df2 = pd.DataFrame({"year": [2021], "value": [200]})

        params1 = {"start_year": 2020}
        params2 = {"start_year": 2021}

        # Store two different datasets
        cache.set("test_source", params1, df1)
        cache.set("test_source", params2, df2)

        # Retrieve should get correct data for each
        result1 = cache.get("test_source", params1)
        result2 = cache.get("test_source", params2)

        assert result1 is not None
        assert result2 is not None
        assert result1["year"].iloc[0] == 2020
        assert result2["year"].iloc[0] == 2021


def test_cache_clear():
    """Test cache clearing functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DataCache(cache_dir=tmpdir)

        df = pd.DataFrame({"year": [2020], "value": [100]})
        params = {"start_year": 2020}

        # Store data
        cache.set("test_source", params, df)
        assert cache.get("test_source", params) is not None

        # Clear cache
        cache.clear("test_source")

        # Should be gone
        assert cache.get("test_source", params) is None


def test_cache_info():
    """Test cache information retrieval."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DataCache(cache_dir=tmpdir)

        df = pd.DataFrame({"year": [2020, 2021], "value": [100, 200]})
        params = {"start_year": 2020}

        # Store data
        cache.set("test_source", params, df)

        # Get cache info
        info = cache.get_cache_info()
        assert len(info) == 1
        assert info[0]["source"] == "test_source"
        assert info[0]["rows"] == 2
        assert "age_hours" in info[0]
