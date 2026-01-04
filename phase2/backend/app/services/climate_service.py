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
    """Get time series data for a climate variable (all 6 Tanzania locations)"""
    # Map variable name to database column
    db_variable = _map_variable_name(variable)
    
    query = db.query(ClimateData)
    
    # Note: Removed hardcoded location filter to support all 6 locations
    # query = _filter_by_tanzania_location(query)
    
    if start_date:
        query = query.filter(ClimateData.date >= start_date)
    
    if end_date:
        query = query.filter(ClimateData.date <= end_date)
    
    data = query.order_by(ClimateData.date).all()
    
    # Group by date and aggregate across locations
    import math
    import statistics
    from collections import defaultdict
    
    grouped = defaultdict(list)
    
    for record in data:
        value = getattr(record, db_variable, None)
        if value is not None:
            try:
                float_value = float(value)
                # Skip NaN and Infinity values
                if not math.isnan(float_value) and not math.isinf(float_value):
                    grouped[record.date].append(float_value)
            except (ValueError, TypeError):
                # Skip invalid values
                continue
    
    # Calculate median, min, max for each date
    points = []
    for date_key in sorted(grouped.keys()):
        values = grouped[date_key]
        if values:  # Only add if we have data
            points.append(TimeSeriesPoint(
                date=date_key,
                median=statistics.median(values),
                min=min(values),
                max=max(values),
                value=statistics.median(values)  # For backward compatibility
            ))
    
    return TimeSeries(variable=variable, data=points)

def calculate_anomalies(
    db: Session,
    variable: str,
    threshold: float = 2.0
) -> List[dict]:
    """
    Calculate temporal anomalies for each location separately.
    
    Detects unusual weather events within each location's historical context,
    rather than comparing locations to each other (geographic differences).
    """
    from collections import defaultdict
    import math
    
    # Map variable name to database column
    db_variable = _map_variable_name(variable)
    
    # Get all data
    try:
        data = db.query(ClimateData).order_by(ClimateData.date).all()
    except Exception as e:
        print(f"Error querying data: {e}")
        return []
    
    if not data:
        return []
    
    # Group data by location
    location_data = defaultdict(list)
    for record in data:
        value = getattr(record, db_variable, None)
        if value is None:
            continue
            
        try:
            float_value = float(value)
            if math.isnan(float_value) or math.isinf(float_value):
                continue
                
            location_key = f"{record.location_lat},{record.location_lon}"
            location_data[location_key].append({
                'record': record,
                'value': float_value
            })
        except (ValueError, TypeError):
            continue
    
    # Calculate anomalies for each location
    all_anomalies = []
    
    for location_key, records in location_data.items():
        # Need enough data for meaningful statistics
        if len(records) < 10:
            continue
            
        # Calculate mean and std for THIS location only
        values = [r['value'] for r in records]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = variance ** 0.5
        
        # No variability means no anomalies
        if std == 0:
            continue
        
        # Find anomalies within this location's historical data
        for item in records:
            z_score = (item['value'] - mean) / std
            
            if abs(z_score) > threshold:
                record = item['record']
                deviation = item['value'] - mean
                
                all_anomalies.append({
                    "date": record.date.isoformat(),
                    "variable": variable,
                    "value": item['value'],
                    "expectedValue": mean,  # Location-specific mean
                    "deviation": deviation,
                    "z_score": z_score,
                    "type": "high" if z_score > 0 else "low",
                    "location": location_key,
                    "location_lat": float(record.location_lat) if record.location_lat else None,
                    "location_lon": float(record.location_lon) if record.location_lon else None
                })
    
    # Sort by absolute z-score (most extreme first)
    all_anomalies.sort(key=lambda x: abs(x['z_score']), reverse=True)
    
    # Deduplicate by date and location (safety check)
    seen = set()
    unique_anomalies = []
    for anomaly in all_anomalies:
        key = (anomaly["date"], anomaly.get("location", ""))
        if key not in seen:
            seen.add(key)
            unique_anomalies.append(anomaly)
    
    return unique_anomalies

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
    
    # Get data for all 6 Tanzania locations
    query = db.query(ClimateData)
    # Note: Removed hardcoded location filter to support all 6 locations
    
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
    
    # Group by month and calculate averages (all 6 Tanzania locations)
    query = db.query(
        func.extract('month', ClimateData.date).label('month'),
        func.avg(getattr(ClimateData, db_variable)).label('avg_value')
    )
    # Note: Removed hardcoded location filter to support all 6 locations
    monthly_data = query.group_by('month').order_by('month').all()
    
    return {
        "variable": variable,
        "monthly_averages": {int(month): float(avg) for month, avg in monthly_data if avg is not None}
    }
