"""
Property-based tests for Incremental Ingestion Manager

**Feature: automated-forecast-pipeline, Property 5: Incremental fetch date calculation**
**Validates: Requirements 2.1, 2.2**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services.pipeline.incremental_manager import IncrementalIngestionManager, DateRange
from app.models.pipeline_execution import SourceIngestionTracking
from app.models.climate_data import ClimateData


# Strategy for generating valid dates (not too far in past/future)
dates_strategy = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date(2030, 12, 31)
)

# Strategy for source names
source_strategy = st.sampled_from(['chirps', 'nasa_power', 'era5', 'ndvi', 'ocean_indices'])


@settings(
    max_examples=20,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    source=source_strategy,
    last_date=dates_strategy,
    end_date=dates_strategy
)
def test_incremental_fetch_with_existing_data(
    db: Session,
    source: str,
    last_date: date,
    end_date: date
):
    """
    Property: For any data source with existing data, the system should query
    the most recent date and fetch only data from that date forward.

    **Validates: Requirements 2.1, 2.2**
    """
    # Ensure end_date is after last_date for meaningful test
    assume(end_date > last_date)

    # Setup: Create tracking record with last_date
    manager = IncrementalIngestionManager(db)
    tracking = SourceIngestionTracking(
        source=source,
        last_successful_date=last_date
    )
    db.add(tracking)
    db.commit()

    try:
        # Execute: Calculate fetch range
        fetch_range = manager.calculate_fetch_range(source, end_date)

        # Verify: Start date should be last_date + 1 day (accounting for min window override)
        expected_start = last_date + timedelta(days=1)
        min_window = IncrementalIngestionManager.SOURCE_MIN_WINDOW_DAYS.get(source, 0)
        if min_window > 0:
            min_start = end_date - timedelta(days=min_window)
            if expected_start > min_start:
                expected_start = min_start
        assert fetch_range.start_date == expected_start, \
            f"Expected start date {expected_start}, got {fetch_range.start_date}"
        assert fetch_range.end_date == end_date, \
            f"Expected end date {end_date}, got {fetch_range.end_date}"
    finally:
        # Cleanup — always runs so DB is clean for next example
        db.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).delete()
        db.commit()


@settings(
    max_examples=20,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    source=source_strategy,
    end_date=dates_strategy
)
def test_default_lookback_with_no_data(
    db: Session,
    source: str,
    end_date: date
):
    """
    Property: For any data source with no existing data, the system should
    fetch the default 180-day lookback period.

    **Validates: Requirements 2.2, 2.3**
    """
    manager = IncrementalIngestionManager(db)

    # Setup: Ensure no tracking record exists
    db.query(SourceIngestionTracking).filter(
        SourceIngestionTracking.source == source
    ).delete()
    db.commit()

    # Execute: Calculate fetch range
    fetch_range = manager.calculate_fetch_range(source, end_date)

    # Verify: Start date should be 180 days before end_date
    expected_start = end_date - timedelta(days=IncrementalIngestionManager.DEFAULT_LOOKBACK_DAYS)
    assert fetch_range.start_date == expected_start, \
        f"Expected start date {expected_start}, got {fetch_range.start_date}"
    assert fetch_range.end_date == end_date, \
        f"Expected end date {end_date}, got {fetch_range.end_date}"


@settings(
    max_examples=20,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    sources=st.lists(source_strategy, min_size=2, max_size=5, unique=True),
    dates=st.lists(dates_strategy, min_size=2, max_size=5)
)
def test_independent_source_tracking(
    db: Session,
    sources: list,
    dates: list
):
    """
    Property: For any set of data sources with different last-update dates,
    the system should handle each source's incremental update independently.

    **Validates: Requirements 2.5**
    """
    assume(len(sources) == len(dates))

    manager = IncrementalIngestionManager(db)
    source_date_map = {}

    # Pre-cleanup so no leftover tracking from previous examples
    for source in sources:
        db.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).delete()
    db.commit()

    try:
        for source, last_date in zip(sources, dates):
            tracking = SourceIngestionTracking(
                source=source,
                last_successful_date=last_date
            )
            db.add(tracking)
            source_date_map[source] = last_date

        db.commit()

        test_end_date = date.today()
        for source, expected_last_date in source_date_map.items():
            actual_last_date = manager.get_last_ingestion_date(source)
            assert actual_last_date == expected_last_date, \
                f"Source {source}: expected {expected_last_date}, got {actual_last_date}"

            fetch_range = manager.calculate_fetch_range(source, test_end_date)
            expected_start = expected_last_date + timedelta(days=1)
            # Account for minimum window override (ocean_indices/era5 have 90-day min)
            min_window = IncrementalIngestionManager.SOURCE_MIN_WINDOW_DAYS.get(source, 0)
            if min_window > 0:
                min_start = test_end_date - timedelta(days=min_window)
                if expected_start > min_start:
                    expected_start = min_start
            assert fetch_range.start_date == expected_start, \
                f"Source {source}: expected start {expected_start}, got {fetch_range.start_date}"
    finally:
        for source in sources:
            db.query(SourceIngestionTracking).filter(
                SourceIngestionTracking.source == source
            ).delete()
        db.commit()


@settings(
    max_examples=20,
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    source=source_strategy,
    last_date=dates_strategy
)
def test_mark_ingestion_updates_tracking(
    db: Session,
    source: str,
    last_date: date
):
    """
    Property: For any successful ingestion, marking it complete should
    update the tracking record with the new date.

    **Validates: Requirements 2.4**
    """
    manager = IncrementalIngestionManager(db)

    # Pre-cleanup
    db.query(SourceIngestionTracking).filter(
        SourceIngestionTracking.source == source
    ).delete()
    db.commit()

    try:
        manager.mark_ingestion_complete(source, last_date)

        tracking = db.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).first()

        assert tracking is not None, f"No tracking record found for {source}"
        assert tracking.last_successful_date == last_date, \
            f"Expected {last_date}, got {tracking.last_successful_date}"
    finally:
        db.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).delete()
        db.commit()
