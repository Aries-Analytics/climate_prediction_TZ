from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Optional
from app.models.climate_data import ClimateData
from app.schemas.climate_data import TimeSeries, TimeSeriesPoint

# Tanzania coordinates (correct location for filtering)
TANZANIA_LAT = -6.369028
TANZANIA_LON = 34.888822

def _map_variable_name(variable: str) -> str:
    """Map frontend variable names to database column names"""
    variable_mapping = {
        'temperature': 'temperature_avg',
        'rainfall': 'rainfall_mm',
        'ndvi': 'ndvi',
        'enso': 'enso_index',
        'iod': 'iod_index'
    }
    return variable_mapping.get(variable, variable)

def _filter_by_tanzania_location(query):
    """Filter query to only return Tanzania records"""
    return query.filter(
        ClimateData.location_lat == TANZANIA_LAT,
        ClimateData.location_lon == TANZANIA_LON
    )

def get_climate_timeseries(
    db: Session,
    variable: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> TimeSeries:
    """Get time series data for a climate variable (Tanzania only)"""
    # Map variable name to database column
    db_variable = _map_variable_name(variable)
    
    query = db.query(ClimateData)
    
    # Filter by Tanzania location
    query = _filter_by_tanzania_location(query)
    
    if start_date:
        query = query.filter(ClimateData.date >= start_date)
    
    if end_date:
        query = query.filter(ClimateData.date <= end_date)
    
    data = query.order_by(ClimateData.date).all()
    
    # Extract the requested variable
    points = []
    for record in data:
        value = getattr(record, db_variable, None)
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
    """Calculate anomalies for a climate variable (Tanzania only)"""
    # Map variable name to database column
    db_variable = _map_variable_name(variable)
    
    # Get all data for the variable (Tanzania only)
    query = db.query(ClimateData)
    query = _filter_by_tanzania_location(query)
    data = query.order_by(ClimateData.date).all()
    
    values = [float(getattr(record, db_variable)) for record in data if getattr(record, db_variable) is not None]
    
    if not values:
        return []
    
    # Calculate mean and std
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std = variance ** 0.5
    
    # Find anomalies
    anomalies = []
    for record in data:
        value = getattr(record, db_variable, None)
        if value is not None:
            z_score = (float(value) - mean) / std if std > 0 else 0
            if abs(z_score) > threshold:
                deviation = float(value) - mean
                anomalies.append({
                    "date": record.date.isoformat(),
                    "variable": variable,
                    "value": float(value),
                    "expectedValue": mean,
                    "deviation": deviation,
                    "z_score": z_score,
                    "type": "high" if z_score > 0 else "low"
                })
    
    return anomalies

def get_correlation_matrix(
    db: Session,
    variables: List[str]
) -> dict:
    """Calculate correlation matrix for climate variables"""
    import pandas as pd
    import numpy as np
    
    # Map frontend variable names to database columns
    variable_map = {
        'temperature': 'temperature_avg',
        'rainfall': 'rainfall_mm',
        'ndvi': 'ndvi',
        'enso': 'enso_index',
        'iod': 'iod_index'
    }
    
    # Get data for Tanzania location
    query = db.query(ClimateData).filter(
        ClimateData.location_lat == TANZANIA_LAT,
        ClimateData.location_lon == TANZANIA_LON
    )
    
    # Fetch all data
    data = query.all()
    
    if not data:
        # Return identity matrix if no data
        return {
            "variables": variables,
            "matrix": [[1.0 if i == j else 0.0 for j in range(len(variables))] for i in range(len(variables))]
        }
    
    # Convert to DataFrame
    df_data = []
    for record in data:
        row = {}
        for var in variables:
            db_col = variable_map.get(var, var)
            value = getattr(record, db_col, None)
            row[var] = float(value) if value is not None else np.nan
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    # Calculate correlation matrix
    corr_matrix = df.corr().values.tolist()
    
    # Replace NaN with 0
    corr_matrix = [[0.0 if pd.isna(val) else float(val) for val in row] for row in corr_matrix]
    
    return {
        "variables": variables,
        "matrix": corr_matrix
    }

def get_seasonal_patterns(
    db: Session,
    variable: str
) -> dict:
    """Calculate seasonal patterns for a variable (Tanzania only)"""
    # Map variable name to database column
    db_variable = _map_variable_name(variable)
    
    # Group by month and calculate averages (Tanzania only)
    query = db.query(
        func.extract('month', ClimateData.date).label('month'),
        func.avg(getattr(ClimateData, db_variable)).label('avg_value')
    )
    query = query.filter(
        ClimateData.location_lat == TANZANIA_LAT,
        ClimateData.location_lon == TANZANIA_LON
    )
    monthly_data = query.group_by('month').order_by('month').all()
    
    return {
        "variable": variable,
        "monthly_averages": {int(month): float(avg) for month, avg in monthly_data if avg is not None}
    }
