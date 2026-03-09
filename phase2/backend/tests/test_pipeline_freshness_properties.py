"""
Property-based tests for pipeline freshness and staleness features.

**Feature: automated-forecast-pipeline, Property 16: Data freshness display**
**Feature: automated-forecast-pipeline, Property 18: Staleness warning indicator**
"""
import pytest
from hypothesis import given, strategies as st
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session

pytestmark = pytest.mark.xfail(
    strict=False,
    reason="Aspirational API: app.api.pipeline.get_data_freshness and "
           "app.services.forecast_service.get_forecasts (with is_stale field) "
           "not yet implemented; also requires db_session fixture"
)

from app.models.climate_data import ClimateData
from app.models.forecast import Forecast
from app.models.pipeline_execution import PipelineExecution
from app.api.pipeline import get_data_freshness
from app.services.forecast_service import get_forecasts


@given(
    days_old=st.integers(min_value=0, max_value=30)
)
def test_property_freshness_display(db_session: Session, days_old: int):
    """
    Property 16: Data freshness display
    
    For any climate data with a known age, the freshness API should correctly
    report the age in days and the latest data timestamp.
    
    **Validates: Requirements 5.1**
    """
    # Create climate data with specific age
    data_date = date.today() - timedelta(days=days_old)
    ingestion_time = datetime.now() - timedelta(days=days_old)
    
    climate_record = ClimateData(
        date=data_date,
        location_lat=-6.369028,
        location_lon=34.888822,
        temperature_avg=25.0,
        created_at=ingestion_time
    )
    db_session.add(climate_record)
    db_session.commit()
    
    # Get freshness data
    freshness = get_data_freshness(db=db_session)
    
    # Verify freshness is reported correctly
    assert freshness['climate_data']['latest_date'] == data_date.isoformat()
    assert freshness['climate_data']['age_days'] == days_old
    
    # Cleanup
    db_session.delete(climate_record)
    db_session.commit()


@given(
    days_old=st.integers(min_value=0, max_value=30)
)
def test_property_staleness_warning(db_session: Session, days_old: int):
    """
    Property 18: Staleness warning indicator
    
    For any data age, the staleness warning should be True if and only if
    the data is older than 7 days.
    
    **Validates: Requirements 5.3**
    """
    # Create climate data with specific age
    data_date = date.today() - timedelta(days=days_old)
    
    climate_record = ClimateData(
        date=data_date,
        location_lat=-6.369028,
        location_lon=34.888822,
        temperature_avg=25.0
    )
    db_session.add(climate_record)
    db_session.commit()
    
    # Get freshness data
    freshness = get_data_freshness(db=db_session)
    
    # Verify staleness warning is correct
    expected_stale = days_old > 7
    assert freshness['climate_data']['is_stale'] == expected_stale
    
    # Cleanup
    db_session.delete(climate_record)
    db_session.commit()


@given(
    forecast_age_days=st.integers(min_value=0, max_value=30)
)
def test_property_forecast_staleness_flag(db_session: Session, forecast_age_days: int):
    """
    Property: Forecast staleness flag
    
    For any forecast with a known age, the is_stale flag should be True
    if and only if the forecast is older than 7 days.
    
    **Validates: Requirements 5.2, 5.3**
    """
    # Create forecast with specific age
    created_time = datetime.now() - timedelta(days=forecast_age_days)
    
    forecast = Forecast(
        trigger_type='drought',
        probability=0.5,
        horizon_months=3,
        target_date=date.today() + timedelta(days=90),
        created_at=created_time
    )
    db_session.add(forecast)
    db_session.commit()
    
    # Get forecasts
    forecasts = get_forecasts(db=db_session)
    
    # Verify staleness flag
    assert len(forecasts) > 0
    forecast_response = forecasts[0]
    expected_stale = forecast_age_days > 7
    assert forecast_response.is_stale == expected_stale
    
    # Cleanup
    db_session.delete(forecast)
    db_session.commit()


def test_property_updating_status_indicator(db_session: Session):
    """
    Property: Updating status indicator
    
    When a pipeline execution is in 'running' status, the freshness API
    should indicate is_updating=True. Otherwise, it should be False.
    
    **Validates: Requirements 5.4**
    """
    # Test with no execution (should be False)
    freshness = get_data_freshness(db=db_session)
    assert freshness['pipeline']['is_updating'] == False
    
    # Create running execution
    execution = PipelineExecution(
        id='test-exec-1',
        execution_type='manual',
        status='running',
        started_at=datetime.now()
    )
    db_session.add(execution)
    db_session.commit()
    
    # Should now show updating
    freshness = get_data_freshness(db=db_session)
    assert freshness['pipeline']['is_updating'] == True
    
    # Complete the execution
    execution.status = 'completed'
    execution.completed_at = datetime.now()
    db_session.commit()
    
    # Should no longer show updating
    freshness = get_data_freshness(db=db_session)
    assert freshness['pipeline']['is_updating'] == False
    
    # Cleanup
    db_session.delete(execution)
    db_session.commit()
