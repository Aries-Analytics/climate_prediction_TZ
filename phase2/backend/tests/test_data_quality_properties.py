"""
Property-based tests for Data Quality Validator

**Feature: automated-forecast-pipeline, Property 29: Required field validation**
**Feature: automated-forecast-pipeline, Property 30: Anomaly detection**
**Feature: automated-forecast-pipeline, Property 31: Data gap detection**
**Validates: Requirements 8.1, 8.2, 8.3**
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services.pipeline.data_quality_validator import DataQualityValidator, ValidationResult
from app.models.climate_data import ClimateData
from app.models.pipeline_execution import DataQualityMetrics


@settings(
    max_examples=30,
    deadline=5000,
)
@given(
    has_date=st.booleans(),
    has_temperature=st.booleans(),
    has_rainfall=st.booleans(),
    has_ndvi=st.booleans()
)
def test_required_field_validation(
    db: Session,
    has_date: bool,
    has_temperature: bool,
    has_rainfall: bool,
    has_ndvi: bool
):
    """
    Property Test: Required field validation
    
    **Feature: automated-forecast-pipeline, Property 29**
    **Validates: Requirements 8.1**
    
    For any climate data record, the system should validate that required
    fields (date and at least one climate variable) are present.
    """
    validator = DataQualityValidator(db)
    
    # Create test data with optional fields
    data = {
        'location_lat': -6.369028,
        'location_lon': 34.888822,
    }
    
    if has_date:
        data['date'] = date.today()
    if has_temperature:
        data['temperature_avg'] = 25.0
    if has_rainfall:
        data['rainfall'] = 50.0
    if has_ndvi:
        data['ndvi'] = 0.5
    
    # Validate
    result = validator.validate_required_fields(data)
    
    # Property 1: Date is required
    if not has_date:
        assert not result.is_valid, "Validation should fail without date"
        assert 'date' in result.errors, "Error should mention missing date"
    
    # Property 2: At least one climate variable is required
    has_climate_var = has_temperature or has_rainfall or has_ndvi
    if has_date and not has_climate_var:
        assert not result.is_valid, "Validation should fail without climate variables"
        assert any('climate' in err.lower() or 'variable' in err.lower() 
                   for err in result.errors), "Error should mention missing climate variables"
    
    # Property 3: Valid data should pass
    if has_date and has_climate_var:
        assert result.is_valid, (
            f"Validation should pass with date and climate variables, "
            f"but got errors: {result.errors}"
        )


@settings(
    max_examples=30,
    deadline=5000,
)
@given(
    temperature=st.one_of(
        st.floats(min_value=-50, max_value=60),  # Valid range
        st.floats(min_value=-100, max_value=-51),  # Too cold
        st.floats(min_value=61, max_value=100)  # Too hot
    ),
    rainfall=st.one_of(
        st.floats(min_value=0, max_value=500),  # Valid range
        st.floats(min_value=-10, max_value=-0.1),  # Negative (invalid)
        st.floats(min_value=501, max_value=1000)  # Too high
    ),
    ndvi=st.one_of(
        st.floats(min_value=-1.0, max_value=1.0),  # Valid range
        st.floats(min_value=-2.0, max_value=-1.1),  # Too low
        st.floats(min_value=1.1, max_value=2.0)  # Too high
    )
)
def test_anomaly_detection(
    db: Session,
    temperature: float,
    rainfall: float,
    ndvi: float
):
    """
    Property Test: Anomaly detection
    
    **Feature: automated-forecast-pipeline, Property 30**
    **Validates: Requirements 8.2**
    
    For any climate data values, the system should detect anomalies
    (values outside expected ranges).
    """
    validator = DataQualityValidator(db)
    
    data = {
        'date': date.today(),
        'location_lat': -6.369028,
        'location_lon': 34.888822,
        'temperature_avg': temperature,
        'rainfall': rainfall,
        'ndvi': ndvi
    }
    
    result = validator.validate_value_ranges(data)
    
    # Property 1: Temperature should be in valid range (-50 to 60°C)
    temp_valid = -50 <= temperature <= 60
    if not temp_valid:
        assert not result.is_valid, (
            f"Should detect temperature anomaly: {temperature}°C"
        )
        assert any('temperature' in err.lower() for err in result.errors), (
            "Error should mention temperature anomaly"
        )
    
    # Property 2: Rainfall should be non-negative and reasonable (0 to 500mm)
    rainfall_valid = 0 <= rainfall <= 500
    if not rainfall_valid:
        assert not result.is_valid, (
            f"Should detect rainfall anomaly: {rainfall}mm"
        )
        assert any('rainfall' in err.lower() for err in result.errors), (
            "Error should mention rainfall anomaly"
        )
    
    # Property 3: NDVI should be in valid range (-1 to 1)
    ndvi_valid = -1.0 <= ndvi <= 1.0
    if not ndvi_valid:
        assert not result.is_valid, (
            f"Should detect NDVI anomaly: {ndvi}"
        )
        assert any('ndvi' in err.lower() for err in result.errors), (
            "Error should mention NDVI anomaly"
        )
    
    # Property 4: All valid values should pass
    if temp_valid and rainfall_valid and ndvi_valid:
        assert result.is_valid, (
            f"All values in valid range should pass: "
            f"temp={temperature}, rain={rainfall}, ndvi={ndvi}, "
            f"errors={result.errors}"
        )


@settings(
    max_examples=20,
    deadline=5000,
)
@given(
    start_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2024, 12, 31)),
    gap_days=st.integers(min_value=1, max_value=30),
    records_before_gap=st.integers(min_value=1, max_value=10),
    records_after_gap=st.integers(min_value=1, max_value=10)
)
def test_data_gap_detection(
    db: Session,
    start_date: date,
    gap_days: int,
    records_before_gap: int,
    records_after_gap: int
):
    """
    Property Test: Data gap detection
    
    **Feature: automated-forecast-pipeline, Property 31**
    **Validates: Requirements 8.3**
    
    For any time series of climate data, the system should detect gaps
    (missing date ranges) in the data.
    """
    validator = DataQualityValidator(db)
    
    # Create records before gap
    for i in range(records_before_gap):
        record_date = start_date + timedelta(days=i)
        climate_data = ClimateData(
            date=record_date,
            location_lat=-6.369028,
            location_lon=34.888822,
            temperature_avg=25.0
        )
        db.add(climate_data)
    
    # Create gap (no records for gap_days)
    gap_start = start_date + timedelta(days=records_before_gap)
    gap_end = gap_start + timedelta(days=gap_days)
    
    # Create records after gap
    for i in range(records_after_gap):
        record_date = gap_end + timedelta(days=i + 1)
        climate_data = ClimateData(
            date=record_date,
            location_lat=-6.369028,
            location_lon=34.888822,
            temperature_avg=25.0
        )
        db.add(climate_data)
    
    db.commit()
    
    try:
        # Detect gaps
        end_date = gap_end + timedelta(days=records_after_gap)
        result = validator.detect_data_gaps(
            start_date=start_date,
            end_date=end_date,
            source='test_source'
        )
        
        # Property 1: Should detect the gap
        assert not result.is_valid, (
            f"Should detect gap of {gap_days} days between {gap_start} and {gap_end}"
        )
        
        # Property 2: Should report gap details
        assert len(result.gaps) > 0, "Should report at least one gap"
        
        # Property 3: Gap should include the missing date range
        detected_gap = result.gaps[0]
        assert detected_gap['start_date'] >= gap_start, (
            f"Gap start should be >= {gap_start}, got {detected_gap['start_date']}"
        )
        assert detected_gap['end_date'] <= gap_end, (
            f"Gap end should be <= {gap_end}, got {detected_gap['end_date']}"
        )
        
        # Property 4: Gap size should be reported
        assert detected_gap['days_missing'] >= gap_days, (
            f"Should report at least {gap_days} missing days, "
            f"got {detected_gap['days_missing']}"
        )
        
    finally:
        # Cleanup
        db.query(ClimateData).filter(
            ClimateData.date >= start_date,
            ClimateData.date <= end_date
        ).delete()
        db.commit()


@settings(
    max_examples=15,
    deadline=5000,
)
@given(
    validation_failures=st.integers(min_value=0, max_value=10),
    anomalies_detected=st.integers(min_value=0, max_value=10),
    gaps_found=st.integers(min_value=0, max_value=5)
)
def test_quality_metrics_storage(
    db: Session,
    validation_failures: int,
    anomalies_detected: int,
    gaps_found: int
):
    """
    Property Test: Quality metrics storage
    
    For any validation results, the system should store quality metrics
    in the database for tracking and analysis.
    
    **Validates: Requirements 8.5**
    """
    validator = DataQualityValidator(db)
    
    # Create validation result
    result = ValidationResult(
        is_valid=validation_failures == 0 and anomalies_detected == 0 and gaps_found == 0,
        errors=[f"Error {i}" for i in range(validation_failures)],
        warnings=[f"Warning {i}" for i in range(anomalies_detected)],
        gaps=[{'days_missing': 1} for _ in range(gaps_found)]
    )
    
    # Store metrics
    metrics = validator.store_quality_metrics(
        source='test_source',
        result=result
    )
    
    try:
        # Property 1: Metrics should be stored in database
        stored_metrics = db.query(DataQualityMetrics).filter(
            DataQualityMetrics.id == metrics.id
        ).first()
        
        assert stored_metrics is not None, "Metrics should be stored in database"
        
        # Property 2: Metrics should record validation status
        expected_valid = (validation_failures == 0 and anomalies_detected == 0 and gaps_found == 0)
        assert stored_metrics.is_valid == expected_valid, (
            f"Expected is_valid={expected_valid}, got {stored_metrics.is_valid}"
        )
        
        # Property 3: Metrics should record counts
        assert stored_metrics.validation_failures == validation_failures, (
            f"Expected {validation_failures} failures, got {stored_metrics.validation_failures}"
        )
        assert stored_metrics.anomalies_detected == anomalies_detected, (
            f"Expected {anomalies_detected} anomalies, got {stored_metrics.anomalies_detected}"
        )
        assert stored_metrics.gaps_found == gaps_found, (
            f"Expected {gaps_found} gaps, got {stored_metrics.gaps_found}"
        )
        
        # Property 4: Metrics should have timestamp
        assert stored_metrics.checked_at is not None, (
            "Metrics should have timestamp"
        )
        
    finally:
        # Cleanup
        db.delete(stored_metrics)
        db.commit()


@pytest.mark.asyncio
async def test_quality_check_alerts(db: Session):
    """
    Property Test: Quality check alerts
    
    When quality checks fail, the system should send alerts with
    details about the failures.
    
    **Validates: Requirements 8.4**
    """
    from unittest.mock import patch, AsyncMock
    
    validator = DataQualityValidator(db)
    
    # Create invalid data
    data = {
        'date': date.today(),
        'location_lat': -6.369028,
        'location_lon': 34.888822,
        'temperature_avg': 100.0,  # Anomaly
        'rainfall': -10.0  # Invalid
    }
    
    alert_sent = False
    alert_details = {}
    
    async def capture_alert(*args, **kwargs):
        nonlocal alert_sent, alert_details
        alert_sent = True
        alert_details = kwargs
    
    with patch('app.services.pipeline.alerts.AlertService.send_data_quality_alert', side_effect=capture_alert):
        result = validator.validate_value_ranges(data)
        
        if not result.is_valid:
            await validator.send_quality_alert(result, source='test_source')
        
        # Property: Alert should be sent for quality failures
        assert alert_sent, "Alert should be sent when quality checks fail"
        assert 'failed_checks' in alert_details, "Alert should include failed checks"
        assert 'affected_sources' in alert_details, "Alert should include affected sources"


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
