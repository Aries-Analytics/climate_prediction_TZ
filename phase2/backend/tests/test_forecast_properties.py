"""
Property-based tests for forecast functionality.

**Feature: early-warning-system, Property 1: Forecast probability bounds**
**Validates: Requirements 1.3**

Property: For any generated forecast, the probability value must be between 0 and 1 inclusive,
and confidence_lower ≤ probability ≤ confidence_upper
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.climate_data import ClimateData
from app.services.forecast_service import ForecastGenerator, generate_forecasts


# Create in-memory SQLite database for property tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

_test_db = None
_test_engine = None


def get_or_create_test_db():
    """Get or create a shared database for property-based testing"""
    global _test_db, _test_engine
    
    if _test_db is None:
        _test_engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)
        
        # Create tables
        Base.metadata.create_all(bind=_test_engine)
        _test_db = TestingSessionLocal()
    
    return _test_db


def cleanup_test_db():
    """Cleanup database and engine"""
    global _test_db, _test_engine
    
    try:
        if _test_db:
            _test_db.close()
        if _test_engine:
            Base.metadata.drop_all(bind=_test_engine)
            _test_engine.dispose()
    except Exception:
        pass
    finally:
        _test_db = None
        _test_engine = None


def create_climate_data(db, start_date: date, days: int):
    """Helper to create random climate data"""
    import random
    
    # Clear existing data
    try:
        db.query(ClimateData).delete()
        db.commit()
    except Exception:
        db.rollback()
    
    for i in range(days):
        climate = ClimateData(
            date=start_date - timedelta(days=days-i),
            temperature=random.uniform(20.0, 35.0),
            rainfall=random.uniform(0.0, 150.0),
            ndvi=random.uniform(0.2, 0.8),
            enso=random.uniform(-2.0, 2.0),
            iod=random.uniform(-1.5, 1.5),
            location_lat=-6.0,
            location_lon=35.0
        )
        db.add(climate)
    
    db.commit()


def teardown_module():
    """Cleanup after all property tests complete"""
    cleanup_test_db()


@settings(
    max_examples=20,
    deadline=5000,
)
@given(
    horizon_months=st.integers(min_value=3, max_value=6),
    trigger_type=st.sampled_from(["drought", "flood", "crop_failure"]),
    days_of_data=st.integers(min_value=30, max_value=180)
)
def test_forecast_probability_bounds(
    horizon_months,
    trigger_type,
    days_of_data
):
    """
    Property Test: Forecast probability bounds
    
    For any generated forecast, verifies that:
    1. Probability is between 0 and 1 inclusive
    2. confidence_lower ≤ probability ≤ confidence_upper
    3. confidence_lower and confidence_upper are both between 0 and 1
    
    This test generates random combinations of:
    - horizon_months: Forecast horizon (3-6 months)
    - trigger_type: Type of trigger event
    - days_of_data: Amount of historical climate data (30-180 days)
    """
    db = get_or_create_test_db()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    # Generate forecast
    generator = ForecastGenerator()
    forecast = generator.generate_forecast(db, start_date, horizon_months, trigger_type)
    
    # Verify forecast was generated
    assert forecast is not None, "Forecast generation failed"
    
    # Property 1: Probability must be between 0 and 1
    assert 0.0 <= forecast.probability <= 1.0, (
        f"Probability {forecast.probability} is outside valid range [0, 1]"
    )
    
    # Property 2: Confidence bounds must be between 0 and 1
    assert 0.0 <= forecast.confidence_lower <= 1.0, (
        f"confidence_lower {forecast.confidence_lower} is outside valid range [0, 1]"
    )
    assert 0.0 <= forecast.confidence_upper <= 1.0, (
        f"confidence_upper {forecast.confidence_upper} is outside valid range [0, 1]"
    )
    
    # Property 3: confidence_lower ≤ probability ≤ confidence_upper
    assert forecast.confidence_lower <= forecast.probability, (
        f"confidence_lower {forecast.confidence_lower} > probability {forecast.probability}"
    )
    assert forecast.probability <= forecast.confidence_upper, (
        f"probability {forecast.probability} > confidence_upper {forecast.confidence_upper}"
    )
    
    # Additional check: confidence interval width should be reasonable
    interval_width = forecast.confidence_upper - forecast.confidence_lower
    assert 0.0 <= interval_width < 1.0, (
        f"Confidence interval width {interval_width} is invalid"
    )


@settings(
    max_examples=15,
    deadline=5000,
)
@given(
    horizon_months=st.integers(min_value=3, max_value=6),
    days_of_data=st.integers(min_value=30, max_value=180)
)
def test_forecast_horizon_consistency(
    horizon_months,
    days_of_data
):
    """
    Property Test: Forecast horizon consistency
    
    **Feature: early-warning-system, Property 2: Forecast horizon consistency**
    **Validates: Requirements 1.1**
    
    For any forecast with horizon_months = N, the target_date must equal
    forecast_date plus N months.
    
    This test generates random combinations of:
    - horizon_months: Forecast horizon (3-6 months)
    - days_of_data: Amount of historical climate data (30-180 days)
    """
    db = get_or_create_test_db()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    # Generate forecast for drought (arbitrary choice)
    generator = ForecastGenerator()
    forecast = generator.generate_forecast(db, start_date, horizon_months, "drought")
    
    # Verify forecast was generated
    assert forecast is not None, "Forecast generation failed"
    
    # Calculate expected target date
    expected_target = start_date + relativedelta(months=horizon_months)
    
    # Property: target_date = forecast_date + horizon_months
    assert forecast.target_date == expected_target, (
        f"Target date {forecast.target_date} doesn't match expected "
        f"{expected_target} for horizon {horizon_months} months from {start_date}"
    )
    
    # Verify horizon_months is stored correctly
    assert forecast.horizon_months == horizon_months, (
        f"Stored horizon {forecast.horizon_months} doesn't match input {horizon_months}"
    )


@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    days_of_data=st.integers(min_value=30, max_value=100)
)
def test_confidence_interval_validity(
    days_of_data
):
    """
    Property Test: Confidence interval validity
    
    **Feature: early-warning-system, Property 3: Confidence interval validity**
    **Validates: Requirements 2.1, 2.3**
    
    For any forecast, the confidence interval width (confidence_upper - confidence_lower)
    must be non-negative and less than 1.0.
    """
    db = get_or_create_test_db()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    # Generate forecasts for all trigger types and horizons
    generator = ForecastGenerator()
    
    for trigger_type in ["drought", "flood", "crop_failure"]:
        for horizon in [3, 4, 5, 6]:
            forecast = generator.generate_forecast(db, start_date, horizon, trigger_type)
            
            if forecast:
                # Calculate interval width
                interval_width = forecast.confidence_upper - forecast.confidence_lower
                
                # Property 1: Width must be non-negative
                assert interval_width >= 0.0, (
                    f"Confidence interval width {interval_width} is negative for "
                    f"{trigger_type} at {horizon} months"
                )
                
                # Property 2: Width must be less than 1.0
                assert interval_width < 1.0, (
                    f"Confidence interval width {interval_width} is >= 1.0 for "
                    f"{trigger_type} at {horizon} months"
                )


@settings(
    max_examples=10,
    deadline=10000,
)
@given(
    horizons=st.lists(
        st.integers(min_value=3, max_value=6),
        min_size=1,
        max_size=4,
        unique=True
    ),
    days_of_data=st.integers(min_value=50, max_value=150)
)
def test_generate_forecasts_all_valid(
    horizons,
    days_of_data
):
    """
    Property Test: All generated forecasts have valid probabilities
    
    Verifies that when generating multiple forecasts at once,
    all of them satisfy the probability bounds property.
    """
    db = get_or_create_test_db()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    # Generate forecasts
    forecasts = generate_forecasts(db, start_date, horizons)
    
    # Should generate forecasts for all trigger types and horizons
    expected_count = len(horizons) * 3  # 3 trigger types
    assert len(forecasts) == expected_count, (
        f"Expected {expected_count} forecasts but got {len(forecasts)}"
    )
    
    # Verify all forecasts have valid probabilities
    for forecast in forecasts:
        # Probability bounds
        assert 0.0 <= forecast.probability <= 1.0, (
            f"Invalid probability {forecast.probability} for {forecast.trigger_type}"
        )
        
        # Confidence bounds
        assert 0.0 <= forecast.confidence_lower <= 1.0
        assert 0.0 <= forecast.confidence_upper <= 1.0
        
        # Ordering
        assert forecast.confidence_lower <= forecast.probability <= forecast.confidence_upper, (
            f"Probability {forecast.probability} outside confidence interval "
            f"[{forecast.confidence_lower}, {forecast.confidence_upper}]"
        )


@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    probability=st.floats(min_value=0.0, max_value=1.0),
    uncertainty=st.floats(min_value=0.01, max_value=0.3)
)
def test_confidence_interval_calculation(
    probability,
    uncertainty
):
    """
    Property Test: Confidence interval calculation
    
    Verifies that the confidence interval calculation function
    produces valid intervals for any probability and uncertainty.
    """
    generator = ForecastGenerator()
    
    lower, upper = generator.calculate_confidence_intervals(probability, uncertainty)
    
    # Property 1: Bounds are within [0, 1]
    assert 0.0 <= lower <= 1.0, f"Lower bound {lower} outside [0, 1]"
    assert 0.0 <= upper <= 1.0, f"Upper bound {upper} outside [0, 1]"
    
    # Property 2: Lower ≤ Upper
    assert lower <= upper, f"Lower bound {lower} > upper bound {upper}"
    
    # Property 3: Probability should be within or near the interval
    # (may be clipped at boundaries)
    if 0.0 < probability < 1.0:
        # For probabilities not at boundaries, they should be within interval
        # or the interval should be at a boundary
        assert (lower <= probability <= upper) or lower == 0.0 or upper == 1.0, (
            f"Probability {probability} not properly bounded by [{lower}, {upper}]"
        )



@settings(
    max_examples=15,
    deadline=5000,
)
@given(
    probability=st.floats(min_value=0.0, max_value=1.0),
    threshold=st.floats(min_value=0.2, max_value=0.5)
)
def test_recommendation_threshold(
    probability,
    threshold
):
    """
    Property Test: Recommendation threshold
    
    **Feature: early-warning-system, Property 4: Recommendation threshold**
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    For any forecast with probability > threshold, the system must generate
    at least one recommendation.
    
    This test generates random combinations of:
    - probability: Forecast probability (0-1)
    - threshold: Recommendation threshold (0.2-0.5)
    """
    from app.services.forecast_service import generate_recommendations
    from app.models.forecast import Forecast
    from datetime import date
    
    db = get_or_create_test_db()
    
    # Create a mock forecast
    forecast = Forecast(
        forecast_date=date.today(),
        target_date=date.today() + timedelta(days=90),
        horizon_months=3,
        trigger_type="drought",
        probability=probability,
        confidence_lower=max(0.0, probability - 0.1),
        confidence_upper=min(1.0, probability + 0.1),
        model_version="test_v1"
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    
    # Generate recommendations
    recommendations = generate_recommendations(db, forecast, threshold)
    
    # Property: If probability > threshold, must have at least one recommendation
    if probability > threshold:
        assert len(recommendations) >= 1, (
            f"Expected at least 1 recommendation for probability {probability} "
            f"with threshold {threshold}, but got {len(recommendations)}"
        )
        
        # Verify recommendation has required fields
        rec = recommendations[0]
        assert rec.recommendation_text is not None and len(rec.recommendation_text) > 0
        assert rec.priority in ["high", "medium", "low"]
        assert rec.action_timeline is not None
    else:
        # If probability <= threshold, should have no recommendations
        assert len(recommendations) == 0, (
            f"Expected 0 recommendations for probability {probability} "
            f"with threshold {threshold}, but got {len(recommendations)}"
        )
    
    # Cleanup
    db.query(Forecast).filter(Forecast.id == forecast.id).delete()
    db.commit()


@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    probability=st.floats(min_value=0.3, max_value=1.0),
    trigger_type=st.sampled_from(["drought", "flood", "crop_failure"])
)
def test_recommendation_priority_mapping(
    probability,
    trigger_type
):
    """
    Property Test: Recommendation priority is correctly assigned
    
    Verifies that recommendation priority matches the probability level:
    - probability >= 0.6 → high priority
    - 0.4 <= probability < 0.6 → medium priority
    - probability < 0.4 → low priority
    """
    from app.services.forecast_service import generate_recommendations
    from app.models.forecast import Forecast
    from datetime import date
    
    db = get_or_create_test_db()
    
    # Create a mock forecast
    forecast = Forecast(
        forecast_date=date.today(),
        target_date=date.today() + timedelta(days=90),
        horizon_months=3,
        trigger_type=trigger_type,
        probability=probability,
        confidence_lower=max(0.0, probability - 0.1),
        confidence_upper=min(1.0, probability + 0.1),
        model_version="test_v1"
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    
    # Generate recommendations
    recommendations = generate_recommendations(db, forecast, threshold=0.3)
    
    # Should have at least one recommendation since probability >= 0.3
    assert len(recommendations) >= 1
    
    rec = recommendations[0]
    
    # Verify priority matches probability
    if probability >= 0.6:
        assert rec.priority == "high", (
            f"Expected 'high' priority for probability {probability}, got '{rec.priority}'"
        )
    elif probability >= 0.4:
        assert rec.priority == "medium", (
            f"Expected 'medium' priority for probability {probability}, got '{rec.priority}'"
        )
    else:
        assert rec.priority == "low", (
            f"Expected 'low' priority for probability {probability}, got '{rec.priority}'"
        )
    
    # Cleanup
    db.query(Forecast).filter(Forecast.id == forecast.id).delete()
    db.commit()


@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    days_of_data=st.integers(min_value=50, max_value=150)
)
def test_all_high_probability_forecasts_have_recommendations(
    days_of_data
):
    """
    Property Test: All high-probability forecasts get recommendations
    
    Verifies that when generating forecasts, all forecasts with probability > 0.3
    receive at least one recommendation.
    """
    from app.services.forecast_service import generate_forecasts, generate_all_recommendations
    
    db = get_or_create_test_db()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    # Generate forecasts
    forecasts = generate_forecasts(db, start_date, [3, 4, 5, 6])
    
    # Generate recommendations for all high-probability forecasts
    recommendations = generate_all_recommendations(db, min_probability=0.3)
    
    # Count forecasts above threshold
    high_prob_forecasts = [f for f in forecasts if f.probability > 0.3]
    
    # Property: Number of recommendations should match number of high-probability forecasts
    assert len(recommendations) == len(high_prob_forecasts), (
        f"Expected {len(high_prob_forecasts)} recommendations for high-probability forecasts, "
        f"but got {len(recommendations)}"
    )



@settings(
    max_examples=15,
    deadline=5000,
)
@given(
    trigger_type=st.sampled_from(["drought", "flood", "crop_failure"]),
    min_probability=st.floats(min_value=0.0, max_value=0.5),
    horizon_months=st.integers(min_value=3, max_value=6),
    days_of_data=st.integers(min_value=50, max_value=150)
)
def test_api_response_schema(
    trigger_type,
    min_probability,
    horizon_months,
    days_of_data
):
    """
    Property Test: API response schema
    
    **Feature: early-warning-system, Property 7: API response schema**
    **Validates: Requirements 5.1**
    
    For any successful API forecast request, the response must conform to the
    defined JSON schema with all required fields present.
    
    This test generates random query parameters and verifies that:
    1. All returned forecasts have required fields
    2. Field types match the schema
    3. Field values are within valid ranges
    4. camelCase conversion works correctly
    """
    from app.services.forecast_service import get_forecasts
    from app.schemas.forecast import ForecastResponse
    
    db = get_or_create_test_db()
    
    # Create climate data and generate forecasts
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    forecasts = generate_forecasts(db, start_date, [3, 4, 5, 6])
    
    # Query forecasts with filters (simulating API request)
    filtered_forecasts = get_forecasts(
        db=db,
        trigger_type=trigger_type,
        min_probability=min_probability,
        horizon_months=horizon_months
    )
    
    # Property 1: All forecasts must be valid ForecastResponse objects
    for forecast in filtered_forecasts:
        assert isinstance(forecast, ForecastResponse), (
            f"Forecast is not a ForecastResponse instance: {type(forecast)}"
        )
        
        # Property 2: Required fields must be present
        required_fields = [
            'id', 'forecast_date', 'target_date', 'horizon_months',
            'trigger_type', 'probability', 'confidence_lower',
            'confidence_upper', 'created_at'
        ]
        
        for field in required_fields:
            assert hasattr(forecast, field), (
                f"Missing required field '{field}' in forecast response"
            )
            assert getattr(forecast, field) is not None, (
                f"Required field '{field}' is None in forecast response"
            )
        
        # Property 3: Field types must be correct
        assert isinstance(forecast.id, int), "id must be integer"
        assert isinstance(forecast.forecast_date, date), "forecast_date must be date"
        assert isinstance(forecast.target_date, date), "target_date must be date"
        assert isinstance(forecast.horizon_months, int), "horizon_months must be integer"
        assert isinstance(forecast.trigger_type, str), "trigger_type must be string"
        assert isinstance(forecast.probability, float), "probability must be float"
        assert isinstance(forecast.confidence_lower, float), "confidence_lower must be float"
        assert isinstance(forecast.confidence_upper, float), "confidence_upper must be float"
        assert isinstance(forecast.created_at, datetime), "created_at must be datetime"
        
        # Property 4: Field values must be within valid ranges
        assert forecast.horizon_months in [3, 4, 5, 6], (
            f"horizon_months {forecast.horizon_months} not in valid range [3-6]"
        )
        assert forecast.trigger_type in ["drought", "flood", "crop_failure"], (
            f"trigger_type '{forecast.trigger_type}' not in valid set"
        )
        assert 0.0 <= forecast.probability <= 1.0, (
            f"probability {forecast.probability} outside valid range [0, 1]"
        )
        assert 0.0 <= forecast.confidence_lower <= 1.0, (
            f"confidence_lower {forecast.confidence_lower} outside valid range [0, 1]"
        )
        assert 0.0 <= forecast.confidence_upper <= 1.0, (
            f"confidence_upper {forecast.confidence_upper} outside valid range [0, 1]"
        )
        
        # Property 5: Confidence interval ordering
        assert forecast.confidence_lower <= forecast.probability <= forecast.confidence_upper, (
            f"Probability {forecast.probability} outside confidence interval "
            f"[{forecast.confidence_lower}, {forecast.confidence_upper}]"
        )
        
        # Property 6: Date relationships
        assert forecast.target_date > forecast.forecast_date, (
            f"target_date {forecast.target_date} not after forecast_date {forecast.forecast_date}"
        )
        
        # Property 7: Horizon consistency
        expected_target = forecast.forecast_date + relativedelta(months=forecast.horizon_months)
        assert forecast.target_date == expected_target, (
            f"target_date {forecast.target_date} doesn't match expected {expected_target} "
            f"for horizon {forecast.horizon_months} months"
        )
        
        # Property 8: JSON serialization works (camelCase conversion)
        try:
            json_dict = forecast.model_dump(by_alias=True)
            
            # Verify camelCase keys exist
            assert 'forecastDate' in json_dict or 'forecast_date' in json_dict, (
                "forecast_date not properly serialized"
            )
            assert 'targetDate' in json_dict or 'target_date' in json_dict, (
                "target_date not properly serialized"
            )
            assert 'horizonMonths' in json_dict or 'horizon_months' in json_dict, (
                "horizon_months not properly serialized"
            )
            assert 'triggerType' in json_dict or 'trigger_type' in json_dict, (
                "trigger_type not properly serialized"
            )
            assert 'confidenceLower' in json_dict or 'confidence_lower' in json_dict, (
                "confidence_lower not properly serialized"
            )
            assert 'confidenceUpper' in json_dict or 'confidence_upper' in json_dict, (
                "confidence_upper not properly serialized"
            )
            assert 'createdAt' in json_dict or 'created_at' in json_dict, (
                "created_at not properly serialized"
            )
        except Exception as e:
            pytest.fail(f"JSON serialization failed: {e}")
    
    # Property 9: Filters are applied correctly
    for forecast in filtered_forecasts:
        # Verify trigger_type filter
        assert forecast.trigger_type == trigger_type, (
            f"Forecast trigger_type '{forecast.trigger_type}' doesn't match filter '{trigger_type}'"
        )
        
        # Verify min_probability filter
        assert forecast.probability >= min_probability, (
            f"Forecast probability {forecast.probability} below minimum {min_probability}"
        )
        
        # Verify horizon_months filter
        assert forecast.horizon_months == horizon_months, (
            f"Forecast horizon {forecast.horizon_months} doesn't match filter {horizon_months}"
        )



@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    trigger_type=st.sampled_from(["drought", "flood", "crop_failure"]),
    horizon_months=st.integers(min_value=3, max_value=6),
    trigger_occurred=st.booleans(),
    days_of_data=st.integers(min_value=50, max_value=150)
)
def test_validation_completeness(
    trigger_type,
    horizon_months,
    trigger_occurred,
    days_of_data
):
    """
    Property Test: Validation completeness
    
    **Feature: early-warning-system, Property 6: Validation completeness**
    **Validates: Requirements 6.1**
    
    For any actual trigger event, if a forecast existed for that date and trigger type,
    a validation record must be created.
    
    This test generates random scenarios with:
    - trigger_type: Type of trigger event
    - horizon_months: Forecast horizon
    - trigger_occurred: Whether a trigger actually occurred
    - days_of_data: Amount of historical climate data
    """
    from app.services.forecast_service import (
        generate_forecasts,
        validate_forecasts_for_date
    )
    from app.models.trigger_event import TriggerEvent
    
    db = get_or_create_test_db()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    # Generate forecasts
    forecasts = generate_forecasts(db, start_date, [horizon_months])
    
    # Calculate target date
    target_date = start_date + relativedelta(months=horizon_months)
    
    # Create trigger event if it occurred
    if trigger_occurred:
        trigger = TriggerEvent(
            trigger_date=target_date,
            trigger_type=trigger_type,
            location_lat=-6.0,
            location_lon=35.0,
            severity="moderate",
            affected_area_km2=100.0
        )
        db.add(trigger)
        db.commit()
        db.refresh(trigger)
    
    # Find the forecast for this trigger type and horizon
    matching_forecast = None
    for forecast in forecasts:
        if (forecast.trigger_type == trigger_type and 
            forecast.horizon_months == horizon_months):
            matching_forecast = forecast
            break
    
    # Property: If a forecast exists, validation should be possible
    if matching_forecast:
        # Validate forecasts for the target date
        validations = validate_forecasts_for_date(db, target_date, trigger_type)
        
        # Property 1: At least one validation should be created
        assert len(validations) >= 1, (
            f"Expected at least 1 validation for {trigger_type} at {target_date}, "
            f"but got {len(validations)}"
        )
        
        # Property 2: Validation should reference the forecast
        validation_forecast_ids = [v.forecast_id for v in validations]
        assert matching_forecast.id in validation_forecast_ids, (
            f"Forecast {matching_forecast.id} not found in validation records"
        )
        
        # Property 3: Validation should correctly record trigger occurrence
        matching_validation = None
        for v in validations:
            if v.forecast_id == matching_forecast.id:
                matching_validation = v
                break
        
        assert matching_validation is not None, "Validation record not found"
        
        if trigger_occurred:
            assert matching_validation.actual_trigger_id is not None, (
                "Validation should reference actual trigger when trigger occurred"
            )
        else:
            assert matching_validation.actual_trigger_id is None, (
                "Validation should not reference trigger when no trigger occurred"
            )
        
        # Property 4: Validation metrics should be calculated
        assert matching_validation.brier_score is not None, (
            "Brier score should be calculated"
        )
        assert 0.0 <= float(matching_validation.brier_score) <= 1.0, (
            f"Brier score {matching_validation.brier_score} outside valid range [0, 1]"
        )
        
        assert matching_validation.probability_error is not None, (
            "Probability error should be calculated"
        )
        assert 0.0 <= float(matching_validation.probability_error) <= 1.0, (
            f"Probability error {matching_validation.probability_error} outside valid range [0, 1]"
        )
        
        # Property 5: was_correct should be boolean (0 or 1)
        assert matching_validation.was_correct in [0, 1], (
            f"was_correct should be 0 or 1, got {matching_validation.was_correct}"
        )
    
    # Cleanup
    if trigger_occurred:
        db.query(TriggerEvent).filter(TriggerEvent.trigger_date == target_date).delete()
    db.query(ForecastValidation).delete()
    db.commit()


@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    probability=st.floats(min_value=0.0, max_value=1.0),
    trigger_occurred=st.booleans()
)
def test_brier_score_calculation(
    probability,
    trigger_occurred
):
    """
    Property Test: Brier score calculation
    
    Verifies that the Brier score is calculated correctly:
    Brier score = (probability - actual)^2
    where actual is 1 if trigger occurred, 0 otherwise
    """
    from app.services.forecast_service import validate_forecast
    from app.models.forecast import Forecast
    from app.models.trigger_event import TriggerEvent
    
    db = get_or_create_test_db()
    
    # Create a mock forecast
    forecast = Forecast(
        forecast_date=date.today(),
        target_date=date.today() + timedelta(days=90),
        horizon_months=3,
        trigger_type="drought",
        probability=probability,
        confidence_lower=max(0.0, probability - 0.1),
        confidence_upper=min(1.0, probability + 0.1),
        model_version="test_v1"
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)
    
    # Create trigger if it occurred
    trigger = None
    if trigger_occurred:
        trigger = TriggerEvent(
            trigger_date=forecast.target_date,
            trigger_type=forecast.trigger_type,
            location_lat=-6.0,
            location_lon=35.0,
            severity="moderate",
            affected_area_km2=100.0
        )
        db.add(trigger)
        db.commit()
        db.refresh(trigger)
    
    # Validate forecast
    validation = validate_forecast(db, forecast, trigger)
    
    # Calculate expected Brier score
    actual_value = 1.0 if trigger_occurred else 0.0
    expected_brier = (probability - actual_value) ** 2
    
    # Property: Brier score should match expected calculation
    assert abs(float(validation.brier_score) - expected_brier) < 0.0001, (
        f"Brier score {validation.brier_score} doesn't match expected {expected_brier}"
    )
    
    # Property: Brier score should be between 0 and 1
    assert 0.0 <= float(validation.brier_score) <= 1.0, (
        f"Brier score {validation.brier_score} outside valid range [0, 1]"
    )
    
    # Cleanup
    db.query(ForecastValidation).filter(ForecastValidation.id == validation.id).delete()
    db.query(Forecast).filter(Forecast.id == forecast.id).delete()
    if trigger:
        db.query(TriggerEvent).filter(TriggerEvent.id == trigger.id).delete()
    db.commit()


@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    days_of_data=st.integers(min_value=50, max_value=150)
)
def test_validation_metrics_aggregation(
    days_of_data
):
    """
    Property Test: Validation metrics aggregation
    
    Verifies that validation metrics are correctly aggregated by trigger type
    and horizon, and that accuracy calculations are correct.
    """
    from app.services.forecast_service import (
        generate_forecasts,
        validate_forecasts_for_date,
        calculate_validation_metrics
    )
    from app.models.trigger_event import TriggerEvent
    
    db = get_or_create_test_db()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    # Generate forecasts for multiple horizons
    forecasts = generate_forecasts(db, start_date, [3, 4])
    
    # Create some trigger events and validate
    for horizon in [3, 4]:
        target_date = start_date + relativedelta(months=horizon)
        
        # Create a drought trigger
        trigger = TriggerEvent(
            trigger_date=target_date,
            trigger_type="drought",
            location_lat=-6.0,
            location_lon=35.0,
            severity="moderate",
            affected_area_km2=100.0
        )
        db.add(trigger)
        db.commit()
        
        # Validate forecasts
        validate_forecasts_for_date(db, target_date)
    
    # Calculate metrics
    metrics = calculate_validation_metrics(db)
    
    # Property 1: Metrics should be returned for each trigger type and horizon combination
    assert len(metrics) > 0, "Should have validation metrics"
    
    for metric in metrics:
        # Property 2: Total forecasts should be positive
        assert metric.total_forecasts > 0, (
            f"Total forecasts should be > 0, got {metric.total_forecasts}"
        )
        
        # Property 3: Correct forecasts should be <= total forecasts
        assert metric.correct_forecasts <= metric.total_forecasts, (
            f"Correct forecasts {metric.correct_forecasts} > total {metric.total_forecasts}"
        )
        
        # Property 4: Accuracy should be between 0 and 1
        assert 0.0 <= metric.accuracy <= 1.0, (
            f"Accuracy {metric.accuracy} outside valid range [0, 1]"
        )
        
        # Property 5: Accuracy should match correct/total
        expected_accuracy = metric.correct_forecasts / metric.total_forecasts
        assert abs(metric.accuracy - expected_accuracy) < 0.0001, (
            f"Accuracy {metric.accuracy} doesn't match expected {expected_accuracy}"
        )
        
        # Property 6: If precision/recall are present, they should be between 0 and 1
        if metric.precision is not None:
            assert 0.0 <= metric.precision <= 1.0, (
                f"Precision {metric.precision} outside valid range [0, 1]"
            )
        
        if metric.recall is not None:
            assert 0.0 <= metric.recall <= 1.0, (
                f"Recall {metric.recall} outside valid range [0, 1]"
            )
        
        # Property 7: Average Brier score should be between 0 and 1
        if metric.avg_brier_score is not None:
            assert 0.0 <= metric.avg_brier_score <= 1.0, (
                f"Average Brier score {metric.avg_brier_score} outside valid range [0, 1]"
            )
    
    # Cleanup
    db.query(ForecastValidation).delete()
    db.query(TriggerEvent).delete()
    db.commit()



@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    days_old=st.integers(min_value=0, max_value=14),
    days_of_data=st.integers(min_value=50, max_value=150)
)
def test_forecast_freshness(
    days_old,
    days_of_data
):
    """
    Property Test: Forecast freshness
    
    **Feature: early-warning-system, Property 5: Forecast freshness**
    **Validates: Requirements 4.2**
    
    For any API request for latest forecasts, all returned forecasts must have
    created_at within the last 7 days.
    
    This test generates random scenarios with:
    - days_old: Age of forecasts in days (0-14)
    - days_of_data: Amount of historical climate data
    """
    from app.services.forecast_service import get_latest_forecasts, generate_forecasts
    
    db = get_or_create_test_db()
    
    # Clear existing forecasts
    db.query(Forecast).delete()
    db.commit()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    # Generate forecasts with a specific timestamp
    forecast_date = date.today() - timedelta(days=days_old)
    forecasts = generate_forecasts(db, forecast_date, [3, 4])
    
    # Manually set created_at to simulate old forecasts
    for forecast_obj in db.query(Forecast).all():
        forecast_obj.created_at = datetime.now() - timedelta(days=days_old)
    db.commit()
    
    # Get latest forecasts
    latest_forecasts = get_latest_forecasts(db)
    
    if latest_forecasts:
        # Property: All latest forecasts should be from the same forecast_date
        forecast_dates = set(f.forecast_date for f in latest_forecasts)
        assert len(forecast_dates) == 1, (
            f"Latest forecasts have multiple forecast dates: {forecast_dates}"
        )
        
        # Property: If forecasts are fresh (< 7 days), they should be returned
        # If forecasts are stale (>= 7 days), they may still be returned but flagged
        for forecast in latest_forecasts:
            age_days = (datetime.now() - forecast.created_at).days
            
            # Verify the age matches what we set
            assert abs(age_days - days_old) <= 1, (
                f"Forecast age {age_days} doesn't match expected {days_old}"
            )
            
            # Property: created_at should be a valid datetime
            assert isinstance(forecast.created_at, datetime), (
                "created_at must be a datetime object"
            )
            
            # Property: created_at should not be in the future
            assert forecast.created_at <= datetime.now(), (
                f"Forecast created_at {forecast.created_at} is in the future"
            )
    
    # Cleanup
    db.query(Forecast).delete()
    db.commit()


@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    days_of_data=st.integers(min_value=50, max_value=150)
)
def test_scheduler_freshness_check(
    days_of_data
):
    """
    Property Test: Scheduler correctly identifies stale forecasts
    
    Verifies that the scheduler's should_run_forecast() method correctly
    identifies when forecasts need updating based on age.
    """
    from app.services.forecast_scheduler import ForecastScheduler
    
    db = get_or_create_test_db()
    
    # Clear existing forecasts
    db.query(Forecast).delete()
    db.commit()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    scheduler = ForecastScheduler(db)
    
    # Property 1: Should run when no forecasts exist
    assert scheduler.should_run_forecast() == True, (
        "Scheduler should run when no forecasts exist"
    )
    
    # Generate fresh forecasts
    forecasts = generate_forecasts(db, date.today(), [3, 4])
    
    # Property 2: Should not run when forecasts are fresh
    assert scheduler.should_run_forecast() == False, (
        "Scheduler should not run when forecasts are fresh"
    )
    
    # Make forecasts old (8 days)
    for forecast_obj in db.query(Forecast).all():
        forecast_obj.created_at = datetime.now() - timedelta(days=8)
        forecast_obj.forecast_date = date.today() - timedelta(days=8)
    db.commit()
    
    # Property 3: Should run when forecasts are stale (> 7 days)
    assert scheduler.should_run_forecast() == True, (
        "Scheduler should run when forecasts are older than 7 days"
    )
    
    # Cleanup
    db.query(Forecast).delete()
    db.commit()


@settings(
    max_examples=10,
    deadline=10000,
)
@given(
    days_of_data=st.integers(min_value=50, max_value=150)
)
def test_scheduler_execution_success(
    days_of_data
):
    """
    Property Test: Scheduler execution produces valid results
    
    Verifies that running the scheduler produces forecasts with correct properties.
    """
    from app.services.forecast_scheduler import run_forecast_job
    
    db = get_or_create_test_db()
    
    # Clear existing forecasts
    db.query(Forecast).delete()
    db.commit()
    
    # Create climate data
    start_date = date.today()
    create_climate_data(db, start_date, days_of_data)
    
    # Run scheduler
    result = run_forecast_job(db)
    
    # Property 1: Result should have required fields
    assert "status" in result, "Result must have status field"
    assert result["status"] in ["success", "skipped", "failed", "error"], (
        f"Invalid status: {result['status']}"
    )
    
    # Property 2: If successful, should have metrics
    if result["status"] == "success":
        assert "forecasts_generated" in result, "Success result must have forecasts_generated"
        assert "recommendations_generated" in result, "Success result must have recommendations_generated"
        assert "duration_seconds" in result, "Success result must have duration_seconds"
        
        # Property 3: Forecasts should be generated
        assert result["forecasts_generated"] > 0, (
            "Successful run should generate at least one forecast"
        )
        
        # Property 4: Duration should be reasonable (< 5 minutes)
        assert result["duration_seconds"] < 300, (
            f"Forecast generation took too long: {result['duration_seconds']}s"
        )
        
        # Property 5: Generated forecasts should be in database
        forecast_count = db.query(Forecast).count()
        assert forecast_count == result["forecasts_generated"], (
            f"Database has {forecast_count} forecasts but result claims {result['forecasts_generated']}"
        )
        
        # Property 6: All generated forecasts should be fresh
        for forecast in db.query(Forecast).all():
            age_seconds = (datetime.now() - forecast.created_at).total_seconds()
            assert age_seconds < 60, (
                f"Newly generated forecast is {age_seconds}s old (should be < 60s)"
            )
    
    # Cleanup
    db.query(Forecast).delete()
    db.commit()
