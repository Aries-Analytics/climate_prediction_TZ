"""
Tests for incremental data update utility
"""

import tempfile
from pathlib import Path

import pandas as pd
from utils.incremental import IncrementalUpdateTracker


def test_first_update():
    """Test first update with no previous metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = IncrementalUpdateTracker(metadata_dir=tmpdir)

        # First update should return full range
        start_year, start_month, end_year, end_month, is_incremental = tracker.get_incremental_range(
            "test_source", 2020, 2023
        )

        assert start_year == 2020
        assert start_month == 1
        assert end_year == 2023
        assert end_month == 12
        assert is_incremental is False


def test_incremental_update():
    """Test incremental update after initial fetch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = IncrementalUpdateTracker(metadata_dir=tmpdir)

        # Record initial update
        tracker.record_update("test_source", end_year=2021, end_month=12, rows_fetched=24)

        # Next update should be incremental
        start_year, start_month, end_year, end_month, is_incremental = tracker.get_incremental_range(
            "test_source", 2020, 2023
        )

        assert start_year == 2022
        assert start_month == 1
        assert end_year == 2023
        assert end_month == 12
        assert is_incremental is True


def test_already_up_to_date():
    """Test when data is already up to date."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = IncrementalUpdateTracker(metadata_dir=tmpdir)

        # Record update to 2023
        tracker.record_update("test_source", end_year=2023, end_month=12, rows_fetched=48)

        # Request data up to 2023 - should indicate up to date
        start_year, start_month, end_year, end_month, is_incremental = tracker.get_incremental_range(
            "test_source", 2020, 2023
        )

        assert start_year is None
        assert is_incremental is True


def test_merge_with_existing():
    """Test merging new data with existing data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = IncrementalUpdateTracker(metadata_dir=tmpdir)

        # Create existing data file
        existing_data = pd.DataFrame({"year": [2020, 2021], "month": [1, 1], "value": [100, 200]})
        data_path = Path(tmpdir) / "test_data.csv"
        existing_data.to_csv(data_path, index=False)

        # New data to merge
        new_data = pd.DataFrame({"year": [2022, 2023], "month": [1, 1], "value": [300, 400]})

        # Merge
        merged = tracker.merge_with_existing("test_source", new_data, data_path=data_path)

        assert len(merged) == 4
        assert merged["year"].tolist() == [2020, 2021, 2022, 2023]


def test_merge_removes_duplicates():
    """Test that merging removes duplicate entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = IncrementalUpdateTracker(metadata_dir=tmpdir)

        # Create existing data
        existing_data = pd.DataFrame({"year": [2020, 2021], "month": [1, 1], "value": [100, 200]})
        data_path = Path(tmpdir) / "test_data.csv"
        existing_data.to_csv(data_path, index=False)

        # New data with overlap
        new_data = pd.DataFrame({"year": [2021, 2022], "month": [1, 1], "value": [250, 300]})

        # Merge
        merged = tracker.merge_with_existing("test_source", new_data, data_path=data_path)

        assert len(merged) == 3  # Should have 2020, 2021 (updated), 2022
        assert merged[merged["year"] == 2021]["value"].iloc[0] == 250  # Should keep new value


def test_record_and_retrieve_update():
    """Test recording and retrieving update metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = IncrementalUpdateTracker(metadata_dir=tmpdir)

        # Record update
        tracker.record_update("test_source", end_year=2022, end_month=6, rows_fetched=18, params={"region": "TZ"})

        # Retrieve
        metadata = tracker.get_last_update("test_source")

        assert metadata is not None
        assert metadata["last_data_year"] == 2022
        assert metadata["last_data_month"] == 6
        assert metadata["rows_fetched"] == 18
        assert metadata["params"]["region"] == "TZ"


def test_clear_metadata():
    """Test clearing update metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = IncrementalUpdateTracker(metadata_dir=tmpdir)

        # Record updates for multiple sources
        tracker.record_update("source1", end_year=2022, end_month=12, rows_fetched=24)
        tracker.record_update("source2", end_year=2022, end_month=12, rows_fetched=24)

        # Clear specific source
        tracker.clear_metadata("source1")
        assert tracker.get_last_update("source1") is None
        assert tracker.get_last_update("source2") is not None

        # Clear all
        tracker.clear_metadata()
        assert tracker.get_last_update("source2") is None
