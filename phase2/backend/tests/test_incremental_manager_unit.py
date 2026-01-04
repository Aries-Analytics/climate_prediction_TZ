"""
Unit tests for Incremental Ingestion Manager edge cases

Tests specific edge cases and boundary conditions for incremental ingestion.
"""
import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services.pipeline.incremental_manager import IncrementalIngestionManager, DateRange
from app.models.pipeline_execution import SourceIngestionTracking


class TestIncrementalManagerEdgeCases:
    """Test edge cases for incremental ingestion manager"""
    
    def test_no_previous_data_default_lookback(self, db_session: Session):
        """
        Test that when no previous data exists, the system fetches 
        the default 180-day lookback period.
        
        **Validates: Requirements 2.3**
        """
        manager = IncrementalIngestionManager(db_session)
        source = "chirps"
        end_date = date(2024, 11, 26)
        
        # Ensure no tracking exists
        existing = db_session.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).first()
        if existing:
            db_session.delete(existing)
            db_session.commit()
        
        # Calculate fetch range
        fetch_range = manager.calculate_fetch_range(source, end_date)
        
        # Verify 180-day lookback
        expected_start = end_date - timedelta(days=180)
        assert fetch_range.start_date == expected_start
        assert fetch_range.end_date == end_date
        assert (fetch_range.end_date - fetch_range.start_date).days == 180
    
    def test_independent_source_tracking(self, db_session: Session):
        """
        Test that multiple sources maintain independent tracking records.
        
        **Validates: Requirements 2.5**
        """
        manager = IncrementalIngestionManager(db_session)
        
        # Set up different dates for different sources
        sources_dates = {
            'chirps': date(2024, 11, 1),
            'nasa_power': date(2024, 11, 10),
            'era5': date(2024, 11, 15),
        }
        
        # Create tracking records
        for source, last_date in sources_dates.items():
            manager.mark_ingestion_complete(source, last_date)
        
        # Verify each source has independent tracking
        for source, expected_date in sources_dates.items():
            actual_date = manager.get_last_ingestion_date(source)
            assert actual_date == expected_date, \
                f"Source {source} should have date {expected_date}, got {actual_date}"
        
        # Cleanup
        for source in sources_dates.keys():
            tracking = db_session.query(SourceIngestionTracking).filter(
                SourceIngestionTracking.source == source
            ).first()
            if tracking:
                db_session.delete(tracking)
        db_session.commit()
    
    def test_date_boundary_same_day(self, db_session: Session):
        """
        Test boundary condition when last_date equals end_date.
        Should return empty range (start > end).
        """
        manager = IncrementalIngestionManager(db_session)
        source = "chirps"
        same_date = date(2024, 11, 26)
        
        # Set up tracking with same date
        manager.mark_ingestion_complete(source, same_date)
        
        # Calculate fetch range with same end date
        fetch_range = manager.calculate_fetch_range(source, same_date)
        
        # Start should be same_date + 1, which is after end_date
        expected_start = same_date + timedelta(days=1)
        assert fetch_range.start_date == expected_start
        assert fetch_range.end_date == same_date
        assert fetch_range.start_date > fetch_range.end_date, \
            "When last_date equals end_date, start should be after end (empty range)"
        
        # Cleanup
        tracking = db_session.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).first()
        if tracking:
            db_session.delete(tracking)
        db_session.commit()
    
    def test_date_boundary_consecutive_days(self, db_session: Session):
        """
        Test boundary condition when end_date is one day after last_date.
        Should return single-day range.
        """
        manager = IncrementalIngestionManager(db_session)
        source = "nasa_power"
        last_date = date(2024, 11, 25)
        end_date = date(2024, 11, 26)
        
        # Set up tracking
        manager.mark_ingestion_complete(source, last_date)
        
        # Calculate fetch range
        fetch_range = manager.calculate_fetch_range(source, end_date)
        
        # Should fetch only the end_date (single day)
        assert fetch_range.start_date == end_date
        assert fetch_range.end_date == end_date
        assert (fetch_range.end_date - fetch_range.start_date).days == 0, \
            "Should be a single-day range"
        
        # Cleanup
        tracking = db_session.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).first()
        if tracking:
            db_session.delete(tracking)
        db_session.commit()
    
    def test_update_existing_tracking_record(self, db_session: Session):
        """
        Test that marking ingestion complete updates existing tracking record
        rather than creating a duplicate.
        """
        manager = IncrementalIngestionManager(db_session)
        source = "era5"
        first_date = date(2024, 11, 20)
        second_date = date(2024, 11, 25)
        
        # First ingestion
        manager.mark_ingestion_complete(source, first_date)
        
        # Verify first record
        tracking = db_session.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).first()
        assert tracking.last_successful_date == first_date
        
        # Second ingestion (should update, not create new)
        manager.mark_ingestion_complete(source, second_date)
        
        # Verify only one record exists and it's updated
        all_tracking = db_session.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).all()
        assert len(all_tracking) == 1, "Should only have one tracking record per source"
        assert all_tracking[0].last_successful_date == second_date
        
        # Cleanup
        db_session.delete(all_tracking[0])
        db_session.commit()
    
    def test_needs_update_staleness_threshold(self, db_session: Session):
        """
        Test staleness detection with various thresholds.
        """
        manager = IncrementalIngestionManager(db_session)
        source = "ndvi"
        
        # Test 1: Recent data (2 days old) - should not need update with 7-day threshold
        recent_date = date.today() - timedelta(days=2)
        manager.mark_ingestion_complete(source, recent_date)
        assert not manager.needs_update(source, staleness_threshold_days=7)
        
        # Test 2: Stale data (10 days old) - should need update with 7-day threshold
        stale_date = date.today() - timedelta(days=10)
        manager.mark_ingestion_complete(source, stale_date)
        assert manager.needs_update(source, staleness_threshold_days=7)
        
        # Test 3: Exactly at threshold (7 days old) - should need update
        threshold_date = date.today() - timedelta(days=7)
        manager.mark_ingestion_complete(source, threshold_date)
        assert manager.needs_update(source, staleness_threshold_days=7)
        
        # Cleanup
        tracking = db_session.query(SourceIngestionTracking).filter(
            SourceIngestionTracking.source == source
        ).first()
        if tracking:
            db_session.delete(tracking)
        db_session.commit()
    
    def test_get_all_source_status(self, db_session: Session):
        """
        Test retrieving status for all sources.
        """
        manager = IncrementalIngestionManager(db_session)
        
        # Set up some sources
        test_sources = {
            'chirps': date(2024, 11, 20),
            'nasa_power': date(2024, 11, 22),
        }
        
        for source, last_date in test_sources.items():
            manager.mark_ingestion_complete(source, last_date)
        
        # Get status
        status = manager.get_all_source_status()
        
        # Verify status includes all expected sources
        assert 'chirps' in status
        assert 'nasa_power' in status
        assert 'era5' in status  # Should be included even if no data
        
        # Verify dates for sources with data
        assert status['chirps']['last_date'] == test_sources['chirps']
        assert status['nasa_power']['last_date'] == test_sources['nasa_power']
        
        # Verify days_old calculation
        for source, last_date in test_sources.items():
            expected_days = (date.today() - last_date).days
            assert status[source]['days_old'] == expected_days
        
        # Cleanup
        for source in test_sources.keys():
            tracking = db_session.query(SourceIngestionTracking).filter(
                SourceIngestionTracking.source == source
            ).first()
            if tracking:
                db_session.delete(tracking)
        db_session.commit()


# Pytest fixtures
@pytest.fixture
def db_session(test_db):
    """Provide a database session for tests"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def test_db():
    """Set up test database"""
    # This would be configured in conftest.py
    pass
