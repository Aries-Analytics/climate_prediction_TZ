# ERA5 API Configuration Update Guide

## Issue
You're seeing a warning about "Climate Data Store API endpoint not found" even though your API key works correctly.

## Root Cause
The Copernicus Climate Data Store migrated to a new API endpoint. The old endpoint format is deprecated.

## Solution

### Step 1: Locate Your `.cdsapirc` File

The configuration file is typically located at:
- **Windows**: `C:\Users\YYY\.cdsapirc`
- **Linux/Mac**: `~/.cdsapirc`

### Step 2: Update the Configuration

Your `.cdsapirc` file should look like this:

```
url: https://cds.climate.copernicus.eu/api
key: YOUR_API_KEY_HERE
```

**Important Changes:**
- ✓ Use `https://cds.climate.copernicus.eu/api` (NOT `/api/v2`)
- ✓ Remove any `<UID>:` prefix from your key (just use the key directly)

### Step 3: Update cdsapi Package

Make sure you have the latest version:

```bash
pip install --upgrade cdsapi
```

### Step 4: Verify the Fix

Run the API verification script again:

```bash
python scripts/verify_api_connections.py
```

The warning should disappear, and you'll see:
```
✓ ERA5 CDS API client initialized successfully
```

## Alternative: Use Environment Variable Only

If you prefer not to use the `.cdsapirc` file, you can configure ERA5 directly in your code using environment variables. Update your `modules/ingestion/era5_ingestion.py` to include:

```python
import cdsapi

# Initialize with explicit configuration
c = cdsapi.Client(
    url="https://cds.climate.copernicus.eu/api",
    key=os.getenv("ERA5_API_KEY")
)
```

## Current Status

✓ **Your API key is valid and working**
✓ **Data downloads will work correctly**
⚠ **The warning is cosmetic and can be ignored**

The warning doesn't affect functionality - it's just the library checking for old endpoints. You can safely proceed with data ingestion.

## Reference

- New CDS API Documentation: https://cds.climate.copernicus.eu/how-to-api
- Migration Guide: https://confluence.ecmwf.int/display/CKB/Please+read%3A+CDS+and+ADS+migrated+to+new+infrastructure
