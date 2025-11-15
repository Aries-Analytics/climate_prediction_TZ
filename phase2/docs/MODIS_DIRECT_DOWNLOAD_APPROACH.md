# MODIS NDVI Direct Download Approach

## Overview

Instead of using Google Earth Engine (which requires a Google Cloud Project), we can download MODIS NDVI data directly from NASA's data servers, similar to how we fetch CHIRPS rainfall data.

## How It Works

### 1. Data Source: NASA LAADS DAAC

**LAADS DAAC** (Level-1 and Atmosphere Archive & Distribution System Distributed Active Archive Center) provides direct HTTP access to MODIS data.

**URL Pattern:**
```
https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD13A2/{YEAR}/{DAY_OF_YEAR}/
```

**Example File:**
```
MOD13A2.A2023001.h21v09.061.2023018142849.hdf
```

### 2. File Format

- **Format**: HDF (Hierarchical Data Format)
- **Product**: MOD13A2 (MODIS/Terra Vegetation Indices 16-Day L3 Global 1km)
- **Temporal Resolution**: 16-day composite
- **Spatial Resolution**: 1km
- **Coverage**: Global, tiled system

### 3. Tile System

MODIS uses a sinusoidal grid system. Tanzania is covered by these tiles:
- **h21v09** (northern Tanzania)
- **h21v10** (southern Tanzania)
- **h22v09** (eastern Tanzania - includes Zanzibar)

### 4. Download Process

```python
def fetch_modis_ndvi_direct(start_year, end_year, bounds):
    """
    1. For each year:
       - Calculate which 16-day periods to download (e.g., day 1, 17, 33, ...)
       
    2. For each period:
       - Construct URL for each tile covering Tanzania
       - Download HDF file (~10-20 MB per tile)
       
    3. Process each file:
       - Open HDF file with rasterio or gdal
       - Extract NDVI layer
       - Subset to Tanzania bounding box
       - Calculate spatial mean
       
    4. Aggregate:
       - Combine 16-day values into monthly means
       - Return DataFrame with year, month, ndvi
    """
```

### 5. Implementation Steps

#### Step 1: Determine Tiles for Tanzania
```python
# Tanzania bounding box
TANZANIA_BOUNDS = {
    "lat_min": -11.75,
    "lat_max": -0.99,
    "lon_min": 29.34,
    "lon_max": 40.44,
}

# MODIS tiles covering Tanzania
TANZANIA_TILES = ["h21v09", "h21v10", "h22v09"]
```

#### Step 2: Construct Download URLs
```python
def get_modis_url(year, day_of_year, tile):
    """
    Construct URL for MODIS file.
    
    Example:
    https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD13A2/2023/001/
    """
    base_url = "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/MOD13A2"
    return f"{base_url}/{year}/{day_of_year:03d}/"
```

#### Step 3: Download and Process
```python
import requests
from osgeo import gdal
import numpy as np

def download_and_process_tile(url, bounds):
    """
    1. Download HDF file
    2. Open with GDAL
    3. Extract NDVI subdataset
    4. Subset to bounding box
    5. Calculate mean NDVI
    """
    # Download
    response = requests.get(url)
    
    # Save temporarily
    with tempfile.NamedTemporaryFile(suffix='.hdf', delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
    
    # Open with GDAL
    dataset = gdal.Open(tmp_path)
    
    # MODIS HDF files have multiple subdatasets
    # NDVI is typically subdataset 0 or 1
    subdatasets = dataset.GetSubDatasets()
    ndvi_dataset = gdal.Open(subdatasets[0][0])  # First subdataset
    
    # Read NDVI array
    ndvi_array = ndvi_dataset.ReadAsArray()
    
    # MODIS NDVI is scaled by 10000
    ndvi_array = ndvi_array / 10000.0
    
    # Subset to Tanzania bounds (requires coordinate transformation)
    # ... (geospatial subsetting logic)
    
    # Calculate mean
    mean_ndvi = np.nanmean(ndvi_array)
    
    return mean_ndvi
```

#### Step 4: Aggregate to Monthly
```python
def aggregate_to_monthly(ndvi_records):
    """
    Convert 16-day NDVI values to monthly means.
    
    MODIS provides ~23 values per year (every 16 days)
    We aggregate these to 12 monthly values
    """
    df = pd.DataFrame(ndvi_records)
    df['date'] = pd.to_datetime(df['year'].astype(str) + df['day_of_year'].astype(str), format='%Y%j')
    df['month'] = df['date'].dt.month
    
    # Group by year and month, take mean
    monthly = df.groupby(['year', 'month'])['ndvi'].mean().reset_index()
    
    return monthly
```

## Advantages

✅ **No Google Cloud Project required** - Direct HTTP download
✅ **No authentication needed** - Public data access
✅ **Similar to CHIRPS approach** - Consistent architecture
✅ **Full control** - Process data exactly as needed
✅ **Free** - No API quotas or billing

## Disadvantages

❌ **More complex** - Need to handle HDF files, tiles, projections
❌ **Larger downloads** - ~10-20 MB per tile per 16-day period
❌ **Processing overhead** - Need GDAL/rasterio for HDF processing
❌ **Tile management** - Must download and merge multiple tiles

## Required Dependencies

```bash
pip install gdal  # or rasterio
pip install h5py  # For HDF file handling
```

## Alternative: NASA AppEEARS API

NASA also provides **AppEEARS** (Application for Extracting and Exploring Analysis Ready Samples), which is an API that:

1. You submit a request with coordinates and date range
2. NASA processes the data on their servers
3. You download a CSV with extracted values

**Advantages:**
- No need to process HDF files
- NASA handles tile merging and subsetting
- Returns CSV directly

**Disadvantages:**
- Requires NASA Earthdata account (free)
- Asynchronous (submit request, wait, download)
- May take hours for processing

## Recommended Approach

### Option A: Direct Download (More Work, More Control)
- Implement HDF processing
- Download tiles directly
- Process locally
- **Estimated effort**: 4-6 hours

### Option B: AppEEARS API (Less Work, Less Control)
- Use NASA's processing service
- Submit requests via API
- Download processed CSV
- **Estimated effort**: 2-3 hours

### Option C: Keep GEE (Best Quality, Requires Setup)
- Set up Google Cloud Project (one-time)
- Use existing implementation
- Best data quality and flexibility
- **Estimated effort**: 1-2 hours (mostly waiting for approval)

## My Recommendation

For this project, I recommend **Option C (Google Earth Engine)** because:

1. The code is already implemented and tested
2. GEE handles all the complex processing (tiles, projections, aggregation)
3. One-time setup that works forever
4. Free for research/educational use
5. Most reliable and maintained service

**However**, if you need data immediately without waiting for GCP approval, I can implement **Option B (AppEEARS API)** which would give you real MODIS data within a few hours.

## Example: AppEEARS API Flow

```python
# 1. Submit request
import requests

# Authenticate
auth = ('your_earthdata_username', 'your_earthdata_password')

# Define request
task = {
    'task_type': 'area',
    'task_name': 'Tanzania_NDVI_2023',
    'params': {
        'dates': [{'startDate': '2023-01-01', 'endDate': '2023-12-31'}],
        'layers': [{'product': 'MOD13A2.061', 'layer': 'NDVI'}],
        'coordinates': [
            [29.34, -11.75],  # Tanzania bounds
            [40.44, -11.75],
            [40.44, -0.99],
            [29.34, -0.99],
            [29.34, -11.75]
        ]
    }
}

# Submit
response = requests.post(
    'https://appeears.earthdatacloud.nasa.gov/api/task',
    json=task,
    auth=auth
)

task_id = response.json()['task_id']

# 2. Wait for processing (check status)
status_url = f'https://appeears.earthdatacloud.nasa.gov/api/status/{task_id}'

# 3. Download results when ready
download_url = f'https://appeears.earthdatacloud.nasa.gov/api/bundle/{task_id}'
```

Would you like me to implement the AppEEARS API approach to get real NDVI data without needing a Google Cloud Project?
