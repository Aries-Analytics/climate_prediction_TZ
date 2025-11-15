# Google Earth Engine Setup Instructions for NDVI Data

## Current Status

The NDVI ingestion module is configured to fetch real satellite data from Google Earth Engine (MODIS MOD13A2 dataset), but requires a Google Cloud Project to be set up.

## Setup Steps

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "tanzania-climate-insurance")
4. Click "Create"
5. Note your Project ID (e.g., "tanzania-climate-insurance-12345")

### 2. Enable Earth Engine API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Earth Engine API"
3. Click on it and click "Enable"

### 3. Register Project with Earth Engine

1. Go to [Earth Engine Code Editor](https://code.earthengine.google.com/)
2. Sign in with your Google account
3. Register your project for Earth Engine access
4. This may require filling out a form explaining your use case

### 4. Configure Local Environment

Once your project is approved:

```bash
# Set your project ID
earthengine set_project YOUR_PROJECT_ID

# Test the connection
python -c "import ee; ee.Initialize(project='YOUR_PROJECT_ID'); print('Success!')"
```

### 5. Update the Code

Update `modules/ingestion/ndvi_ingestion.py` line 47:

```python
# Replace 'ee-default-project' with your actual project ID
ee.Initialize(project='YOUR_PROJECT_ID')
```

## Alternative: Use Synthetic Data

If you don't want to set up GEE, the module automatically falls back to climatology-based synthetic NDVI data that reflects Tanzania's seasonal patterns:

```python
from modules.ingestion.ndvi_ingestion import fetch_ndvi_data

# This will use synthetic data if GEE is not available
df = fetch_ndvi_data(start_year=2020, end_year=2023, use_gee=False)
```

## Alternative: Use NASA MODIS Direct Download

Another option is to fetch MODIS data directly from NASA's servers without using GEE. This would require implementing a new data source similar to how CHIRPS data is fetched.

### NASA MODIS Data Sources:

- **LAADS DAAC**: https://ladsweb.modaps.eosdis.nasa.gov/
- **AppEEARS**: https://appeears.earthdatacloud.nasa.gov/
- **ORNL DAAC**: https://daac.ornl.gov/

These services provide MODIS data through direct download or API access without requiring a Google Cloud Project.

## Cost Considerations

- **Google Earth Engine**: Free for research and educational use
- **Google Cloud Project**: Free tier available, but may require credit card for verification
- **NASA Data**: Free for all users, no cloud project required

## Recommended Approach

For this project, I recommend:

1. **Short-term**: Use the synthetic climatology-based NDVI data (already implemented)
2. **Long-term**: Set up a Google Cloud Project for real satellite data access

The synthetic data is based on Tanzania's known seasonal patterns and provides realistic values for development and testing.
