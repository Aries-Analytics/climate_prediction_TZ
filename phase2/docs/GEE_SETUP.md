# Google Earth Engine Setup Guide

## Overview

The NDVI ingestion module can fetch real satellite data from Google Earth Engine (GEE) using the MODIS MOD13A2 dataset. This provides actual vegetation index measurements from NASA's Terra satellite.

## Prerequisites

- Python 3.7 or higher
- Google account
- Internet connection

## Installation Steps

### 1. Install Earth Engine API

```bash
pip install earthengine-api
```

### 2. Authenticate with Google Earth Engine

Run the authentication command:

```bash
earthengine authenticate
```

This will:
1. Open your web browser
2. Ask you to sign in with your Google account
3. Request permission to access Earth Engine
4. Provide an authorization code

Follow the prompts and paste the authorization code back into your terminal.

### 3. Verify Installation

Test that Earth Engine is working:

```python
import ee

try:
    ee.Initialize()
    print("✓ Google Earth Engine is ready!")
except Exception as e:
    print(f"✗ Error: {e}")
```

## Using GEE with the Pipeline

### Automatic Mode (Default)

The NDVI module automatically tries to use GEE if available:

```python
from modules.ingestion.ndvi_ingestion import fetch_ndvi_data

# Will use GEE if authenticated, otherwise falls back to synthetic data
df = fetch_ndvi_data(start_year=2020, end_year=2023)

# Check data source
print(f"Data source: {df['data_source'].iloc[0]}")
# Output: "MODIS_MOD13A2_GEE" (real data) or "climatology_based" (synthetic)
```

### Force Synthetic Data

To skip GEE and use synthetic data:

```python
df = fetch_ndvi_data(start_year=2020, end_year=2023, use_gee=False)
```

### Run Full Pipeline with GEE

```bash
# Make sure you're authenticated first
earthengine authenticate

# Run the pipeline (will use real NDVI data)
python run_pipeline.py
```

## Data Details

### MODIS MOD13A2 Dataset

- **Satellite**: NASA Terra
- **Product**: Vegetation Indices 16-Day Global 1km
- **Resolution**: 1 km spatial resolution
- **Temporal**: 16-day composite periods
- **Coverage**: Global, 2000-present
- **Processing**: Aggregated to monthly means by the pipeline

### NDVI Values

MODIS NDVI is scaled by 10,000 in the raw data. The module automatically:
1. Divides by 10,000 to get actual NDVI values
2. Clips to valid range (-1.0 to 1.0)
3. Aggregates 16-day composites to monthly means
4. Calculates spatial mean over the region

## Troubleshooting

### Authentication Errors

**Error**: `ee.ee_exception.EEException: Please authorize access to your Earth Engine account`

**Solution**:
```bash
earthengine authenticate
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'ee'`

**Solution**:
```bash
pip install earthengine-api
```

### Initialization Errors

**Error**: `HttpError 403: Earth Engine account not registered`

**Solution**:
1. Go to https://earthengine.google.com/
2. Sign up for Earth Engine access
3. Wait for approval (usually instant for non-commercial use)
4. Run `earthengine authenticate` again

### Timeout Errors

**Error**: `ee.ee_exception.EEException: Computation timed out`

**Solution**:
- Reduce the date range (fewer years)
- Reduce the geographic area
- Try again later (GEE may be busy)

### Quota Errors

**Error**: `ee.ee_exception.EEException: User memory limit exceeded`

**Solution**:
- Process smaller date ranges
- Use smaller geographic regions
- Wait and try again (quotas reset)

## Performance Considerations

### Download Times

Typical download times for Tanzania region:
- 1 year: 30-60 seconds
- 5 years: 2-5 minutes
- 10 years: 5-10 minutes
- 14 years (2010-2023): 10-15 minutes

### Caching

Use the caching utility to avoid repeated downloads:

```python
from utils.cache import get_cache
from modules.ingestion.ndvi_ingestion import fetch_ndvi_data

cache = get_cache(default_ttl_hours=168)  # 1 week cache

params = {'start_year': 2020, 'end_year': 2023}
df = cache.get('ndvi', params)

if df is None:
    df = fetch_ndvi_data(**params)
    cache.set('ndvi', params, df)
```

### Incremental Updates

Use incremental updates to fetch only new data:

```python
from utils.incremental import get_tracker
from modules.ingestion.ndvi_ingestion import fetch_ndvi_data

tracker = get_tracker()

# Get range for incremental update
start_year, start_month, end_year, end_month, is_incremental = \
    tracker.get_incremental_range('ndvi', 2010, 2023)

if start_year is not None:
    new_data = fetch_ndvi_data(start_year=start_year, end_year=end_year)
    merged_data = tracker.merge_with_existing('ndvi', new_data)
    tracker.record_update('ndvi', end_year, 12, len(new_data))
```

## Alternative: Synthetic Data

If you don't need real satellite data or can't access GEE, the module provides high-quality synthetic data:

**Advantages**:
- No authentication required
- Instant generation
- Reproducible for testing
- Reflects Tanzania's seasonal patterns

**Disadvantages**:
- Not real measurements
- No interannual variability
- No spatial detail
- No anomaly detection

**When to use synthetic**:
- Development and testing
- Demonstrations
- When GEE is unavailable
- For quick prototyping

## Data Quality

### Real MODIS Data (GEE)

✓ Actual satellite measurements  
✓ Captures real vegetation changes  
✓ Includes drought events  
✓ Spatial detail preserved  
✓ Validated by NASA  

### Synthetic Data

✓ Realistic seasonal patterns  
✓ Reproducible  
✓ Fast generation  
✗ No real anomalies  
✗ No spatial variability  

## References

- [Google Earth Engine](https://earthengine.google.com/)
- [MODIS MOD13A2 Product](https://lpdaac.usgs.gov/products/mod13a2v006/)
- [Earth Engine Python API](https://developers.google.com/earth-engine/guides/python_install)
- [MODIS NDVI User Guide](https://lpdaac.usgs.gov/documents/103/MOD13_User_Guide_V6.pdf)

## Support

For Earth Engine issues:
- [GEE Forum](https://groups.google.com/g/google-earth-engine-developers)
- [GEE Documentation](https://developers.google.com/earth-engine)

For pipeline issues:
- Check logs in `logs/pipeline_YYYY-MM-DD.log`
- Run with `--debug` flag for verbose output
- Review error messages for specific guidance
