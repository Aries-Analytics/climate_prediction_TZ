import sys
sys.path.append('/app')

from app.core.database import SessionLocal
from app.models.climate_data import ClimateData
import pandas as pd
import numpy as np

db = SessionLocal()

# Tanzania coordinates
TANZANIA_LAT = -6.369028
TANZANIA_LON = 34.888822

# Get data
query = db.query(ClimateData).filter(
    ClimateData.location_lat == TANZANIA_LAT,
    ClimateData.location_lon == TANZANIA_LON
).limit(100)

data = query.all()

print(f"Found {len(data)} records")

if data:
    # Check first few records
    for i, record in enumerate(data[:5]):
        print(f"\nRecord {i+1}:")
        print(f"  Date: {record.date}")
        print(f"  Temperature: {record.temperature_avg}")
        print(f"  Rainfall: {record.rainfall_mm}")
        print(f"  NDVI: {record.ndvi}")
        print(f"  ENSO: {record.enso_index}")
        print(f"  IOD: {record.iod_index}")
    
    # Create DataFrame
    df_data = []
    for record in data:
        df_data.append({
            'temperature': float(record.temperature_avg) if record.temperature_avg else np.nan,
            'rainfall': float(record.rainfall_mm) if record.rainfall_mm else np.nan,
            'ndvi': float(record.ndvi) if record.ndvi else np.nan,
            'enso': float(record.enso_index) if record.enso_index else np.nan,
            'iod': float(record.iod_index) if record.iod_index else np.nan
        })
    
    df = pd.DataFrame(df_data)
    
    print("\n\nDataFrame info:")
    print(df.info())
    
    print("\n\nDataFrame describe:")
    print(df.describe())
    
    print("\n\nCorrelation matrix:")
    corr = df.corr()
    print(corr)
    
    print("\n\nCorrelation matrix as list:")
    print(corr.values.tolist())

db.close()
