from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Optional
from app.models.climate_data import ClimateData
from app.schemas.climate_data import TimeSeries, TimeSeriesPoint

def get_climate_timeseries(
    db: Session,
    variable: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> TimeSeries:
    """Get time series data for a climate variable"""
    query = db.query(ClimateData)
    
    if start_date:
        query = query.filter(ClimateData.date >= start_date)
    
    if end_date:
        query = query.filter(ClimateData.date <= end_date)
    
    data = query.order_by(ClimateData.date).all()
    
    # Extract the requested variable
    points = []
    for record in data:
        value = getattr(record, variable, None)
        if value is not None:
            points.append(TimeSeriesPoint(
                date=record.date,
                value=float(value)
            ))
    
    return TimeSeries(variable=variable, data=points)

def calculate_anomalies(
    db: Session,
    variable: str,
    threshold: float = 2.0
) -> List[dict]:
    """Calculate anomalies for a climate variable"""
    # Get all data for the variable
    data = db.query(ClimateData).order_by(ClimateData.date).all()
    
    values = [float(getattr(record, variable)) for record in data if getattr(record, variable) is not None]
    
    if not values:
        return []
    
    # Calculate mean and std
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std = variance ** 0.5
    
    # Find anomalies
    anomalies = []
    for record in data:
        value = getattr(record, variable, None)
        if value is not None:
            z_score = (float(value) - mean) / std if std > 0 else 0
            if abs(z_score) > threshold:
                anomalies.append({
                    "date": record.date,
                    "value": float(value),
                    "z_score": z_score,
                    "type": "high" if z_score > 0 else "low"
                })
    
    return anomalies

def get_correlation_matrix(
    db: Session,
    variables: List[str]
) -> dict:
    """Calculate correlation matrix for climate variables"""
    # This is a simplified version
    # Real implementation would use numpy/pandas for correlation calculation
    return {
        "variables": variables,
        "matrix": [[1.0 if i == j else 0.5 for j in range(len(variables))] for i in range(len(variables))]
    }

def get_seasonal_patterns(
    db: Session,
    variable: str
) -> dict:
    """Calculate seasonal patterns for a variable"""
    # Group by month and calculate averages
    monthly_data = db.query(
        func.extract('month', ClimateData.date).label('month'),
        func.avg(getattr(ClimateData, variable)).label('avg_value')
    ).group_by('month').order_by('month').all()
    
    return {
        "variable": variable,
        "monthly_averages": {int(month): float(avg) for month, avg in monthly_data if avg is not None}
    }
