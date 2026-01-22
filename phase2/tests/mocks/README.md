# Mock API Usage Guide

## Overview

This directory contains mock implementations of all external climate data APIs used in the pipeline. Mocks enable fast, reliable integration testing without making actual network calls.

## Available Mocks

### 1. **CHIRPS Rainfall Data** (`mock_chirps.py`)
- **Simulates**: Google Earth Engine CHIRPS daily rainfall dataset
- **Key Features**:
  - Realistic bimodal Tanzania rainfall pattern (March-May and Oct-Dec peaks)
  - Multi-location support for all calibrated locations
  - ENSO influence on interannual variability
  - Extreme events (droughts and floods)

**Usage:**
```python
from tests.mocks import get_mock_chirps

# Single location
mock_api = get_mock_chirps()
df = mock_api.get_data(start_year=2015, end_year=2020)

# Multiple locations
mock_api = get_mock_chirps(multi_location=True)
df = mock_api.get_data_all_locations(start_year=2015, end_year=2020)
```

### 2. **NASA POWER Climate Data** (`mock_nasa_power.py`)
- **Simulates**: NASA POWER HTTP API for temperature, humidity, solar radiation
- **Key Features**:
  - Realistic seasonal temperature patterns
  - Humidity inverse correlation with dry seasons
  - Solar radiation with cloud cover effects
  - Rate limiting simulation

**Usage:**
```python
from tests.mocks import get_mock_nasa_power

mock_api = get_mock_nasa_power()
df = mock_api.get_data(
    latitude=-6.369,
    longitude=34.889,
    start_year=2015,
    end_year=2020,
    parameters=["T2M", "RH2M", "ALLSKY_SFC_SW_DWN"]
)
```

### 3. **ERA5 Reanalysis Data** (`mock_era5.py`)
- **Simulates**: Copernicus CDS API for ERA5 reanalysis
- **Key Features**:
  - Temperature, wind, and pressure variables
  - Monthly aggregation
  - Realistic atmospheric patterns

**Usage:**
```python
from tests.mocks import get_mock_era5

mock_api = get_mock_era5()
df = mock_api.get_data(
    start_year=2015,
    end_year=2020,
    variables=["temperature_2m", "u_wind_10m", "surface_pressure"]
)
```

### 4. **NDVI Vegetation Index** (`mock_ndvi.py`)
- **Simulates**: Google Earth Engine MODIS and AVHRR NDVI
- **Key Features**:
  - Seasonal vegetation cycles (greening during rainy seasons)
  - Automatic MODIS (2000+) vs AVHRR (1985-1999) selection
  - Cloud cover simulation (missing data)
  - Slight greening trend over time

**Usage:**
```python
from tests.mocks import get_mock_ndvi

mock_api = get_mock_ndvi()
df = mock_api.get_data(start_year=2015, end_year=2020)
```

### 5. **Ocean Indices (ENSO/IOD)** (`mock_ocean_indices.py`)
- **Simulates**: NOAA ONI and IOD data
- **Key Features**:
  - Realistic ENSO cycles (~3-7 year periodicity)
  - IOD patterns with seasonal modulation
  - Automatic ENSO phase classification (El Niño, La Niña, Neutral)

**Usage:**
```python
from tests.mocks import get_mock_ocean_indices

mock_api = get_mock_ocean_indices()
df = mock_api.get_data(start_year=2015, end_year=2020)

# Get only ONI or IOD
oni_df = mock_api.get_oni_data(2015, 2020)
iod_df = mock_api.get_iod_data(2015, 2020)
```

## Testing Error Scenarios

All mocks support error simulation:

```python
# Simulate API failures
mock_api = get_mock_chirps(fail_rate=0.1)  # 10% failure rate

# Simulate slow responses
mock_api = get_mock_nasa_power(slow_response=True)

# Simulate rate limiting (NASA POWER only)
mock_api = get_mock_nasa_power(rate_limit=True)
```

## Using Mocks in Integration Tests

Example integration test:

```python
import pytest
from tests.mocks import get_mock_chirps
from modules.ingestion.chirps_ingestion import fetch_chirps_data

def test_chirps_ingestion_with_mock(monkeypatch):
    """Test CHIRPS ingestion using mocked API."""
    
    # Create mock
    mock_api = get_mock_chirps()
    
    # Patch the actual API call
    monkeypatch.setattr(
        "modules.ingestion.chirps_ingestion._fetch_gee_chirps",
        lambda *args, **kwargs: mock_api.get_data(*args, **kwargs)
    )
    
    # Run ingestion
    df = fetch_chirps_data(start_year=2015, end_year=2020)
    
    # Assert
    assert not df.empty
    assert "rainfall_mm" in df.columns
    assert df["rainfall_mm"].min() >= 0  # No negative rainfall
```

## Mock Data Characteristics

### Data Quality
- **Missing Data**: 0.5-3% missing values (realistic simulation)
- **Noise**: Autocorrelated noise for temporal persistence
- **Extreme Events**: Occasional droughts/floods in rainfall data

### Statistical Properties
- **Seasonal Patterns**: Accurate monthly/seasonal cycles
- **Interannual Variability**: ENSO and IOD influences
- **Spatial Variation**: Location-specific patterns for multi-location mocks
- **Autocorrelation**: Day-to-day and month-to-month persistence

## Benefits of Using Mocks

✅ **Speed**: Tests run in milliseconds instead of minutes  
✅ **Reliability**: No dependency on external API uptime  
✅ **Reproducibility**: Same input always produces same output (if random seed set)  
✅ **Cost**: No API usage charges  
✅ **Control**: Test error scenarios easily  
✅ **Offline**: Works without internet connection

## When to Use Real APIs vs Mocks

**Use Mocks For:**
- Unit and integration tests
- CI/CD pipelines
- Development and debugging
- Testing error handling

**Use Real APIs For:**
- Final validation before deployment
- Verifying API changes haven't broken integration
- Collecting actual production data

## Extending Mocks

To add a new mock API:

1. Create `mock_new_api.py` inheriting from `BaseMockAPI`
2. Implement `get_data()` method
3. Use `MockDataGenerator` utilities for realistic patterns
4. Add to `__init__.py` exports
5. Write tests in `test_mock_new_api.py`

## Troubleshooting

**Issue**: Mock data doesn't match real API structure  
**Solution**: Check real API response format and update `MockResponseBuilder`

**Issue**: Tests fail with mock but pass with real API  
**Solution**: Mock may be missing edge cases - review real API behavior

**Issue**: Mock data is unrealistic  
**Solution**: Adjust statistical parameters in mock implementation

---

**Last Updated**: January 2026  
**Maintainer**: Tanzania Climate Prediction Team
