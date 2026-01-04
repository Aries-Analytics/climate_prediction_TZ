from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, datetime
from typing import List, Optional
import csv
import io
from app.models.trigger_event import TriggerEvent
from app.models.model_prediction import ModelPrediction
from app.schemas.trigger_event import (
    TriggerEventResponse,
    TriggerForecast,
    EarlyWarning,
    TimelineEvent
)

# Tanzania coordinates (correct location for filtering)
TANZANIA_LAT = -6.369028
TANZANIA_LON = 34.888822

def _filter_by_tanzania_location(query):
    """Filter query to only return Tanzania records"""
    return query.filter(
        TriggerEvent.location_lat == TANZANIA_LAT,
        TriggerEvent.location_lon == TANZANIA_LON
    )

def get_trigger_events(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    trigger_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[TriggerEventResponse]:
    """Get trigger events with optional filters (Tanzania only)"""
    from decimal import Decimal
    import math
    
    query = db.query(TriggerEvent)
    
    # Note: Removed hardcoded location filter to support all 6 locations
    # query = _filter_by_tanzania_location(query)
    
    if start_date:
        query = query.filter(TriggerEvent.date >= start_date)
    
    if end_date:
        query = query.filter(TriggerEvent.date <= end_date)
    
    if trigger_type:
        query = query.filter(TriggerEvent.trigger_type == trigger_type)
    
    # Order by ID for stable, predictable pagination
    events = query.order_by(TriggerEvent.id.asc()).offset(skip).limit(limit).all()
    
    # Clean NaN values before validation
    cleaned_events = []
    for event in events:
        # Convert NaN to None for numeric fields
        if event.severity is not None and (isinstance(event.severity, float) and math.isnan(event.severity) or 
                                           isinstance(event.severity, Decimal) and not event.severity.is_finite()):
            event.severity = None
        if event.confidence is not None and (isinstance(event.confidence, float) and math.isnan(event.confidence) or 
                                             isinstance(event.confidence, Decimal) and not event.confidence.is_finite()):
            event.confidence = None
        if event.payout_amount is not None and (isinstance(event.payout_amount, float) and math.isnan(event.payout_amount) or 
                                                isinstance(event.payout_amount, Decimal) and not event.payout_amount.is_finite()):
            event.payout_amount = None
        if event.location_lat is not None and (isinstance(event.location_lat, float) and math.isnan(event.location_lat) or 
                                               isinstance(event.location_lat, Decimal) and not event.location_lat.is_finite()):
            event.location_lat = None
        if event.location_lon is not None and (isinstance(event.location_lon, float) and math.isnan(event.location_lon) or 
                                               isinstance(event.location_lon, Decimal) and not event.location_lon.is_finite()):
            event.location_lon = None
        
        cleaned_events.append(TriggerEventResponse.model_validate(event))
    
    return cleaned_events

def get_trigger_timeline(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[TimelineEvent]:
    """Get timeline view of trigger events grouped by date and type (Tanzania only)"""
    query = db.query(
        TriggerEvent.date,
        TriggerEvent.trigger_type,
        func.count(TriggerEvent.id).label('count'),
        func.sum(TriggerEvent.payout_amount).label('total_payout')
    )
    
    # Note: Removed hardcoded location filter to support all 6 locations
    # query = query.filter(
    #     TriggerEvent.location_lat == TANZANIA_LAT,
    #     TriggerEvent.location_lon == TANZANIA_LON
    # )
    
    if start_date:
        query = query.filter(TriggerEvent.date >= start_date)
    
    if end_date:
        query = query.filter(TriggerEvent.date <= end_date)
    
    results = query.group_by(
        TriggerEvent.date,
        TriggerEvent.trigger_type
    ).order_by(TriggerEvent.date.desc(), TriggerEvent.trigger_type).all()
    
    timeline = []
    for event_date, trigger_type, count, total_payout in results:
        timeline.append(TimelineEvent(
            date=event_date,
            trigger_type=trigger_type,
            count=count,
            total_payout=float(total_payout or 0)
        ))
    
    return timeline

def forecast_trigger_probabilities(
    db: Session,
    months_ahead: int = 3
) -> List[TriggerForecast]:
    """Generate trigger probability forecasts from ML predictions"""
    # This would typically load from model predictions
    # For now, we'll query the model_predictions table
    
    today = date.today()
    
    # Get predictions for future dates
    predictions = db.query(ModelPrediction).filter(
        ModelPrediction.target_date > today
    ).order_by(ModelPrediction.target_date, ModelPrediction.id).limit(months_ahead * 30).all()
    
    forecasts = []
    
    # Group predictions and calculate trigger probabilities
    # This is a simplified version - real implementation would use ML model outputs
    for pred in predictions:
        if pred.predicted_value and pred.confidence_lower and pred.confidence_upper:
            # Simple heuristic: higher predicted values = higher trigger probability
            probability = min(float(pred.predicted_value) / 100.0, 1.0)
            
            forecasts.append(TriggerForecast(
                target_date=pred.target_date,
                trigger_type="drought",  # Would be determined by model
                probability=probability,
                confidence_lower=float(pred.confidence_lower),
                confidence_upper=float(pred.confidence_upper)
            ))
    
    return forecasts

def generate_early_warnings(
    db: Session,
    threshold: float = 0.7
) -> List[EarlyWarning]:
    """Generate early warning alerts based on trigger forecasts"""
    forecasts = forecast_trigger_probabilities(db, months_ahead=6)
    
    warnings = []
    
    for forecast in forecasts:
        if forecast.probability >= threshold:
            # Determine severity
            if forecast.probability >= 0.9:
                severity = "high"
            elif forecast.probability >= 0.8:
                severity = "medium"
            else:
                severity = "low"
            
            # Generate message
            message = f"High probability ({forecast.probability:.1%}) of {forecast.trigger_type} trigger on {forecast.target_date}"
            
            # Recommended action
            if severity == "high":
                action = "Immediate review required. Consider activating contingency plans."
            elif severity == "medium":
                action = "Monitor closely. Prepare contingency measures."
            else:
                action = "Continue monitoring. No immediate action required."
            
            warnings.append(EarlyWarning(
                alert_type=forecast.trigger_type,
                severity=severity,
                message=message,
                trigger_probability=forecast.probability,
                target_date=forecast.target_date,
                recommended_action=action
            ))
    
    return warnings

def export_triggers_csv(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    trigger_type: Optional[str] = None
) -> bytes:
    """Export trigger events to CSV format"""
    events = get_trigger_events(
        db,
        start_date=start_date,
        end_date=end_date,
        trigger_type=trigger_type,
        skip=0,
        limit=10000  # Large limit for export
    )
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Date', 'Trigger Type', 'Confidence', 'Severity',
        'Payout Amount', 'Latitude', 'Longitude', 'Created At'
    ])
    
    # Write data
    for event in events:
        writer.writerow([
            event.id,
            event.date,
            event.trigger_type,
            event.confidence,
            event.severity,
            event.payout_amount,
            event.location_lat,
            event.location_lon,
            event.created_at
        ])
    
    # Get CSV content as bytes
    csv_content = output.getvalue()
    return csv_content.encode('utf-8')

def get_trigger_statistics(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> dict:
    """Calculate statistics for trigger events (Tanzania only)"""
    query = db.query(TriggerEvent)
    
    # Note: Removed hardcoded location filter to support all 6 locations
    # query = _filter_by_tanzania_location(query)
    
    if start_date:
        query = query.filter(TriggerEvent.date >= start_date)
    
    if end_date:
        query = query.filter(TriggerEvent.date <= end_date)
    
    total_count = query.count()
    total_payout = query.with_entities(func.sum(TriggerEvent.payout_amount)).scalar() or 0
    
    # Note: Removed hardcoded location filter to support all 6 locations
    type_counts = db.query(
        TriggerEvent.trigger_type,
        func.count(TriggerEvent.id).label('count')
    )
    
    if start_date:
        type_counts = type_counts.filter(TriggerEvent.date >= start_date)
    if end_date:
        type_counts = type_counts.filter(TriggerEvent.date <= end_date)
    
    type_counts = type_counts.group_by(TriggerEvent.trigger_type).all()
    
    # Convert to dict for easy access
    counts_by_type = {trigger_type: count for trigger_type, count in type_counts}
    
    # Total time periods: 6 locations * 312 months (2000-2025) = 1872
    # This is the denominator for calculating trigger rates
    TOTAL_TIME_PERIODS = 1872
    
    # Calculate rates as percentage of total time periods
    rates = {
        trigger_type: round(count / TOTAL_TIME_PERIODS * 100, 1)
        for trigger_type, count in counts_by_type.items()
    }
    
    return {
        'total_count': total_count,
        'total_payout': float(total_payout),
        'total_periods': TOTAL_TIME_PERIODS,
        'by_type': counts_by_type,
        'rates': rates  # Percentage of time periods with each trigger type
    }
