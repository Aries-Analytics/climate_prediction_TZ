# NDVI/MODIS Data Access Guide

## Current Setup: Google Earth Engine (Recommended)

Your NDVI ingestion currently uses **Google Earth Engine (GEE)**, which is the recommended approach because:

✓ **Easier authentication** - One-time setup, no credentials in code  
✓ **Pre-processed data** - Analysis-ready, cloud-masked, quality-controlled  
✓ **Faster access** - Server-side processing, no large file downloads  
✓ **Better for time-series** - Optimized for temporal analysis  

### Google Earth Engine Setup

1. **Install the package:**
   ```bash
   pip install earthengine-api
   ```

2. **Authenticate (one-time):**
   ```bash
   earthengine authenticate
   ```
   This opens a browser where you:
   - Sign in with your Google account
   - Authorize Earth Engine access
   - Copy the authorization code back to terminal

3. **Set your project ID in `.env`:**
   ```
   GOOGLE_CLOUD_PROJECT=climate-prediction-using-ml
   ```

4. **Test the connection:**
   ```python
   import ee
   ee.Initialize(project='climate-prediction-using-ml')
   print("✓ Google Earth Engine connected!")
   ```

### What GEE Provides

- **Dataset**: MODIS/061/MOD13A2 (Terra Vegetation Indices)
- **Resolution**: 1 km spatial, 16-day temporal
- **Coverage**: Global, 2000-present
- **Processing**: Automatically aggregated to monthly means
- **Quality**: Cloud-masked and quality-filtered

---

## Alternative: Direct MODIS Downloads (Not Currently Used)

If you ever need to download raw MODIS files directly (not recommended for most use cases), here's how:

### NASA Earthdata Login

Your NASA Earthdata credentials are:
- **Username**: Your Earthdata username
- **Password**: Your Earthdata password
- **Registration**: https://urs.earthdata.nasa.gov/

### Adding Credentials to .env

If you want to enable direct MODIS downloads in the future:

```bash
# In your .env file
EARTHDATA_USERNAME=your_actual_username
EARTHDATA_PASSWORD=your_actual_password
```

### Direct Download Example (Python)

```python
import requests
from requests.auth import HTTPBasicAuth

# Your Earthdata credentials
username = os.getenv("EARTHDATA_USERNAME")
password = os.getenv("EARTHDATA_PASSWORD")

# Example: Download a MODIS file
url = "https://e4ftl01.cr.usgs.gov/MOLT/MOD13A2.061/2023.01.01/MOD13A2.A2023001.h21v09.061.2023010123456.hdf"

response = requests.get(
    url,
    auth=HTTPBasicAuth(username, password),
    stream=True
)

if response.status_code == 200:
    with open("modis_file.hdf", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("✓ File downloaded")
else:
    print(f"✗ Download failed: {response.status_code}")
```

### Why Direct Downloads Are More Complex

- **Large files**: HDF format, 10-50 MB per tile per date
- **Tile system**: Need to download multiple tiles for Tanzania (h21v09, h21v10, h22v09, h22v10)
- **Processing required**: Must mosaic tiles, reproject, extract NDVI band
- **Storage intensive**: Hundreds of GB for multi-year datasets
- **Slower**: Download + processing time vs instant GEE access

---

## Comparison: GEE vs Direct Downloads

| Feature | Google Earth Engine | Direct MODIS Downloads |
|---------|-------------------|----------------------|
| **Setup** | One-time auth | Earthdata credentials |
| **Data Access** | Instant, server-side | Download large files |
| **Processing** | Pre-processed | Manual processing needed |
| **Storage** | None (cloud-based) | Hundreds of GB locally |
| **Speed** | Fast (seconds) | Slow (hours for multi-year) |
| **Complexity** | Low | High |
| **Best For** | Time-series analysis | Custom processing pipelines |

---

## Current Implementation Status

✓ **Google Earth Engine**: Configured and working  
✓ **MODIS MOD13A2**: Using latest version (061)  
✓ **Tanzania Coverage**: Full country bounding box  
✓ **Temporal Range**: 2010-2023 (configurable)  
✓ **Fallback**: Synthetic climatological data if GEE unavailable  

---

## Troubleshooting

### "Google Earth Engine not initialized"

**Solution:**
```bash
earthengine authenticate
```

### "Project not found"

**Solution:** Check your `.env` file has:
```
GOOGLE_CLOUD_PROJECT=climate-prediction-using-ml
```

### "Quota exceeded"

**Solution:** GEE has usage limits. For large requests:
- Reduce date range
- Process in smaller chunks
- Wait 24 hours for quota reset

### Want to use Earthdata credentials?

**Current status:** Not needed! Your code uses GEE, which is better for your use case.

**If you still want to add them:**
1. Uncomment the lines in `.env`:
   ```
   EARTHDATA_USERNAME=your_username
   EARTHDATA_PASSWORD=your_password
   ```
2. Replace with your actual Earthdata credentials
3. Modify `ndvi_ingestion.py` to use direct downloads (not recommended)

---

## Recommendations

1. **Keep using Google Earth Engine** - It's working well for your needs
2. **Don't add Earthdata credentials** - Not needed for current implementation
3. **Only use direct downloads if:**
   - You need specific MODIS products not on GEE
   - You need raw, unprocessed data
   - You have custom processing requirements

Your current setup is optimal for climate prediction and time-series analysis!
