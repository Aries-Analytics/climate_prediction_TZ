"""
Improved Per-Location Anomaly Detection

This optional enhancement detects TEMPORAL anomalies (unusual events within a location's history)
instead of SPATIAL anomalies (location differences).

To use this version, update the API endpoint in climate.py:
    from app.services.climate_service import calculate_anomalies_per_location
    return climate_service.calculate_anomalies_per_location(db, variable, threshold)
"""

def calculate_anomalies_per_location(
    db: Session,
    variable: str,
    threshold: float = 2.0
) -> List[dict]:
    """
    Calculate temporal anomalies for each location separately.
    
    This detects unusual events within each location's historical data,
    rather than comparing locations to each other.
    
    Example:
    - Detects: "Mbeya unusually cold for Mbeya" (temporal anomaly)
    - Ignores: "Mbeya colder than Dodoma" (expected spatial difference)
    """
    from app.models.climate_data import ClimateData
    import math
    from collections import defaultdict
    
    # Map variable name to database column
    db_variable = _map_variable_name(variable)
    
    # Get all data
    data = db.query(ClimateData).order_by(ClimateData.date).all()
    
    # Group data by location
    location_data = defaultdict(list)
    for record in data:
        value = getattr(record, db_variable, None)
        if value is not None:
            try:
                float_value = float(value)
                if not math.isnan(float_value) and not math.isinf(float_value):
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
        # Calculate mean and std for THIS location only
        values = [r['value'] for r in records]
        if len(values) < 10:  # Need enough data for meaningful statistics
            continue
            
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = variance ** 0.5
        
        if std == 0:  # No variability
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
                    "location_lat": float(record.location_lat),
                    "location_lon": float(record.location_lon)
                })
    
    # Sort by date
    all_anomalies.sort(key=lambda x: x['date'])
    
    # Deduplicate (should not be needed, but safety check)
    seen = set()
    unique_anomalies = []
    for anomaly in all_anomalies:
        key = (anomaly["date"], anomaly.get("location", ""))
        if key not in seen:
            seen.add(key)
            unique_anomalies.append(anomaly)
    
    return unique_anomalies


# Helper function for _map_variable_name (if not already in file)
def _map_variable_name(variable: str) -> str:
    """Map frontend variable names to database column names"""
    mapping = {
        'temperature': 'temperature_avg',
        'rainfall': 'rainfall_mm',
        'ndvi': 'ndvi',
        'enso': 'enso_index',
        'iod': 'iod_index'
    }
    return mapping.get(variable.lower(), variable)
