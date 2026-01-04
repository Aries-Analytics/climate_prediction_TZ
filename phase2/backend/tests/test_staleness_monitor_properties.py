"""
Property-based tests for Staleness Monitor

**Feature: automated-forecast-pipeline, Property 8: Staleness detection and alerting**
**Validates: Requirements 3.2, 3.3**
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta, date
from unittest.mock import patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.pipeline.staleness_monitor import StalenessMonitor
from app.models.climate_data import ClimateData
from app.models.forecast import Forecast


@settings(
    max_examples=20,
    deadline=5000,
)
@given(
    data_age_days=st.integers(min_value=0, max_value=30),
    forecast_age_days=st.integers(min_value=0, max_value=30)
)
@pytest.mark.asyncio
async def test_staleness_detection_and_alerting(
    db: Session,
    data_age_days: int,
    forecast_age_days: int
):
    """
    Property Test: Staleness detection and alerting
    
    **Feature: automated-forecast-pipeline, Property 8**
    **Validates: Requirements 3.2, 3.3**
    
    For any data age, the system should detect staleness when data or forecasts
    exceed the 7-day threshold and send appropriate alerts.
    """
    monitor = StalenessMonitor(db)
    
    # Create climate data with specific age
    data_date = date.today() - timedelta(days=data_age_days)
    climate_data = ClimateData(
        date=data_date,
        location_lat=-6.369028,
        location_lon=34.888822,
        temperature_avg=25.0
    )
    db.add(climate_data)
    
    # Create forecast with specific age
    forecast_time = datetime.now() - timedelta(days=forecast_age_days)
    forecast = Forecast(
        trigger_type='drought',
        probability=0.5,
        horizon_months=3,
        target_date=date.today() + timedelta(days=90),
        created_at=forecast_time
    )
    db.add(forecast)
    db.commit()
    
    alert_sent = False
    alert_data = {}
    
    async def capture_alert(*args, **kwargs):
        nonlocal alert_sent, alert_data
        alert_sent = True
        alert_data = {
            'data_age': kwargs.get('data_age_days'),
            'forecast_age': kwargs.get('forecast_age_days')
        }
    
    try:
        with patch('app.services.pipeline.alerts.AlertService.send_staleness_alert', side_effect=capture_alert):
            # Check staleness
            result = await monitor.check_staleness()
            
            # Property 1: Should detect data staleness correctly
            data_is_stale = data_age_days > 7
            assert result['data_stale'] == data_is_stale, (
                f"Expected data_stale={data_is_stale} for age {data_age_days} days, "
                f"got {result['data_stale']}"
            )
            
            # Property 2: Should detect forecast staleness correctly
            forecast_is_stale = forecast_age_days > 7
            assert result['forecast_stale'] == forecast_is_stale, (
                f"Expected forecast_stale={forecast_is_stale} for age {forecast_age_days} days, "
                f"got {result['forecast_stale']}"
            )
            
            # Property 3: Should report correct ages
            assert result['data_age_days'] == data_age_days, (
                f"Expected data age {data_age_days}, got {result['data_age_days']}"
            )
            assert result['forecast_age_days'] == forecast_age_days, (
                f"Expected forecast age {forecast_age_days}, got {result['forecast_age_days']}"
            )
            
            # Property 4: Should send alert if either is stale
            if data_is_stale or forecast_is_stale:
                assert alert_sent, (
                    f"Alert should be sent when data_age={data_age_days} or "
                    f"forecast_age={forecast_age_days} exceeds 7 days"
                )
                assert alert_data['data_age'] == data_age_days
                assert alert_data['forecast_age'] == forecast_age_days
            else:
                assert not alert_sent, (
                    f"Alert should not be sent when both ages are <= 7 days"
                )
            
    finally:
        # Cleanup
        db.delete(climate_data)
        db.delete(forecast)
        db.commit()


@settings(
    max_examples=15,
    deadline=5000,
)
@given(
    threshold_days=st.integers(min_value=1, max_value=14),
    data_age_days=st.integers(min_value=0, max_value=20)
)
@pytest.mark.asyncio
async def test_configurable_staleness_threshold(
    db: Session,
    threshold_days: int,
    data_age_days: int
):
    """
    Property Test: Configurable staleness threshold
    
    For any configured threshold, the staleness detection should use
    that threshold instead of the default 7 days.
    
    **Validates: Requirements 3.2**
    """
    monitor = StalenessMonitor(db, staleness_threshold_days=threshold_days)
    
    # Create climate data
    data_date = date.today() - timedelta(days=data_age_days)
    climate_data = ClimateData(
        date=data_date,
        location_lat=-6.369028,
        location_lon=34.888822,
        temperature_avg=25.0
    )
    db.add(climate_data)
    db.commit()
    
    try:
        result = await monitor.check_staleness()
        
        # Property: Staleness should be based on configured threshold
        expected_stale = data_age_days > threshold_days
        assert result['data_stale'] == expected_stale, (
            f"With threshold {threshold_days} and age {data_age_days}, "
            f"expected stale={expected_stale}, got {result['data_stale']}"
        )
        
    finally:
        db.delete(climate_data)
        db.commit()


@pytest.mark.asyncio
async def test_staleness_with_no_data(db: Session):
    """
    Property Test: Staleness detection with no data
    
    When no data exists, the system should report staleness appropriately.
    
    **Validates: Requirements 3.2, 3.3**
    """
    monitor = StalenessMonitor(db)
    
    # Ensure no data exists
    db.query(ClimateData).delete()
    db.query(Forecast).delete()
    db.commit()
    
    result = await monitor.check_staleness()
    
    # Property 1: Should handle missing data gracefully
    assert 'data_stale' in result
    assert 'forecast_stale' in result
    
    # Property 2: Missing data should be considered stale
    assert result['data_stale'] == True, "Missing data should be considered stale"
    assert result['forecast_stale'] == True, "Missing forecasts should be considered stale"


@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    check_interval_minutes=st.integers(min_value=1, max_value=60)
)
@pytest.mark.asyncio
async def test_periodic_staleness_checks(
    db: Session,
    check_interval_minutes: int
):
    """
    Property Test: Periodic staleness checks
    
    For any check interval, the monitor should perform checks at the
    configured frequency.
    
    **Validates: Requirements 3.2**
    """
    monitor = StalenessMonitor(db, check_interval_minutes=check_interval_minutes)
    
    # Property: Check interval should be configurable
    assert monitor.check_interval_minutes == check_interval_minutes, (
        f"Expected interval {check_interval_minutes}, got {monitor.check_interval_minutes}"
    )


# Pytest fixtures
@pytest.fixture
def db(test_db):
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
    pass
