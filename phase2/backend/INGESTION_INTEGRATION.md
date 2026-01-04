# Ingestion Module Integration with Pipeline Orchestrator

## Overview

The ingestion modules have been updated to integrate seamlessly with the automated pipeline orchestrator. Each module now provides a standardized interface that supports:

- **Database integration**: Direct storage to PostgreSQL via SQLAlchemy
- **Incremental updates**: Fetch only new data based on date ranges
- **Consistent interface**: All modules follow the same function signature
- **Error handling**: Proper rollback on failures

## Updated Modules

### 1. CHIRPS Ingestion (`modules/ingestion/chirps_ingestion.py`)

**New Function**: `ingest_chirps(db, start_date, end_date, incremental)`

- Fetches rainfall data from Google Earth Engine or synthetic sources
- Stores to `ClimateData.rainfall_mm` field
- Uses Tanzania bounding box coordinates

### 2. NASA POWER Ingestion (`modules/ingestion/nasa_power_ingestion.py`)

**New Function**: `ingest_nasa_power(db, start_date, end_date, incremental)`

- Fetches temperature and climate data from NASA POWER API
- Stores to `ClimateData.temperature_avg` field
- Uses Tanzania center point coordinates

### 3. ERA5 Ingestion (`modules/ingestion/era5_ingestion.py`)

**New Function**: `ingest_era5(db, start_date, end_date, incremental)`

- Fetches reanalysis data from Copernicus Climate Data Store
- Stores to `ClimateData.temperature_avg` field (converts Kelvin to Celsius)
- Uses Tanzania center point coordinates

### 4. NDVI Ingestion (`modules/ingestion/ndvi_ingestion.py`)

**New Function**: `ingest_ndvi(db, start_date, end_date, incremental)`

- Fetches vegetation index from MODIS via Google Earth Engine
- Stores to `ClimateData.ndvi` field
- Uses Tanzania center point coordinates

### 5. Ocean Indices Ingestion (`modules/ingestion/ocean_indices_ingestion.py`)

**New Function**: `ingest_ocean_indices(db, start_date, end_date, incremental)`

- Fetches ENSO (ONI) and IOD indices from NOAA
- Stores to `ClimateData.enso_index` and `ClimateData.iod_index` fields
- Uses Tanzania center point coordinates

## Function Signature

All ingestion functions follow this standardized interface:

```python
def ingest_<source>(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    incremental: bool = True
) -> Tuple[int, int]:
    """
    Ingest data and store to database (orchestrator-compatible interface).
    
    Parameters
    ----------
    db : Session
        SQLAlchemy database session for storing data
    start_date : datetime, optional
        Start date for data retrieval. If None, defaults to 2010-01-01
    end_date : datetime, optional
        End date for data retrieval. If None, defaults to current date
    incremental : bool, optional
        Whether to use incremental ingestion. Default is True.
        
    Returns
    -------
    Tuple[int, int]
        (records_fetched, records_stored)
    """
```

## Orchestrator Integration

The pipeline orchestrator (`backend/app/services/pipeline/orchestrator.py`) has been updated to call these functions:

```python
def _ingest_single_source(self, source: str, incremental: bool) -> tuple:
    """Ingest data from a single source"""
    
    # Determine date range
    if incremental:
        date_range = self.incremental_manager.get_date_range(source)
    else:
        start_date = datetime(2010, 1, 1)
        end_date = datetime.now()
    
    # Call appropriate ingestion module
    if source == 'chirps':
        from modules.ingestion.chirps_ingestion import ingest_chirps
        return ingest_chirps(self.db, start_date, end_date, incremental)
    
    elif source == 'nasa_power':
        from modules.ingestion.nasa_power_ingestion import ingest_nasa_power
        return ingest_nasa_power(self.db, start_date, end_date, incremental)
    
    # ... etc for other sources
```

## Data Storage Strategy

### Upsert Logic

Each ingestion function implements an upsert pattern:

1. **Check for existing record**: Query by date and location
2. **Update if exists**: Update relevant fields (e.g., rainfall, temperature)
3. **Insert if new**: Create new `ClimateData` record
4. **Commit transaction**: Commit all changes at once

### Example

```python
# Check if record exists
existing = db.query(ClimateData).filter(
    and_(
        ClimateData.date == row['date'].date(),
        ClimateData.location_lat == tanzania_lat,
        ClimateData.location_lon == tanzania_lon
    )
).first()

if existing:
    # Update existing record
    existing.rainfall_mm = float(row['rainfall_mm'])
else:
    # Create new record
    climate_record = ClimateData(
        date=row['date'].date(),
        location_lat=tanzania_lat,
        location_lon=tanzania_lon,
        rainfall_mm=float(row['rainfall_mm'])
    )
    db.add(climate_record)
```

## Error Handling

All ingestion functions implement proper error handling:

- **Per-record errors**: Logged but don't stop the entire ingestion
- **Fatal errors**: Trigger database rollback
- **Retry logic**: Handled by orchestrator's `RetryHandler`

```python
try:
    # Fetch and store data
    ...
    db.commit()
    return (records_fetched, records_stored)
    
except Exception as e:
    log_error(f"Ingestion failed: {e}")
    db.rollback()
    raise
```

## Testing

### Unit Test

Run the integration test:

```bash
cd backend
python scripts/test_ingestion_integration.py
```

This tests that all modules:
- Accept the correct parameters
- Return the correct tuple format
- Handle database operations properly

### Manual Test

Test individual modules:

```python
from datetime import datetime
from sqlalchemy.orm import Session
from modules.ingestion.chirps_ingestion import ingest_chirps

# Assuming you have a db session
records_fetched, records_stored = ingest_chirps(
    db=db_session,
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2020, 12, 31),
    incremental=False
)

print(f"Fetched: {records_fetched}, Stored: {records_stored}")
```

## Backward Compatibility

The original functions (`fetch_chirps_data`, `fetch_nasa_power_data`, etc.) remain unchanged and continue to work for standalone use. The new `ingest_*` functions are specifically for orchestrator integration.

## Next Steps

1. **Test with real data sources**: Ensure API credentials are configured
2. **Monitor performance**: Check ingestion times for large date ranges
3. **Tune incremental logic**: Adjust date range calculations in `IncrementalIngestionManager`
4. **Add data quality checks**: Integrate with `DataQualityValidator` after ingestion

## Configuration

### Environment Variables

Ensure these are set in `.env`:

```bash
# Google Earth Engine (for CHIRPS and NDVI)
GOOGLE_CLOUD_PROJECT=your-project-id

# Copernicus CDS (for ERA5)
# Configure in ~/.cdsapirc:
# url: https://cds.climate.copernicus.eu/api/v2
# key: {UID}:{API-KEY}
```

### Database

The `ClimateData` model must exist with these fields:
- `date`: Date
- `location_lat`: Numeric(10, 6)
- `location_lon`: Numeric(10, 6)
- `temperature_avg`: Numeric(5, 2)
- `rainfall_mm`: Numeric(7, 2)
- `ndvi`: Numeric(4, 3)
- `enso_index`: Numeric(5, 3)
- `iod_index`: Numeric(5, 3)

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError: No module named 'backend'`:

```python
# Add project root to Python path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

### Database Connection

Ensure the database session is properly configured:

```python
from backend.app.core.database import SessionLocal

db = SessionLocal()
try:
    # Use db
    ...
finally:
    db.close()
```

### API Authentication

- **Google Earth Engine**: Run `earthengine authenticate`
- **Copernicus CDS**: Configure `~/.cdsapirc` with your credentials
- **NASA POWER**: No authentication required (public API)
- **NOAA**: No authentication required (public data)
