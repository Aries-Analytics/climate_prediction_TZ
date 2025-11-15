# ERA5 Data Fetch Plan

## Status: ⚠️ API Migration Required

**Date:** November 14, 2025  
**Issue:** CDS API has migrated to new system  
**Action Required:** Update CDS API credentials for new system

## Proposed Dataset Configuration

### Temporal Coverage
- **Start Year:** 2010
- **End Year:** 2023
- **Duration:** 14 years (same as NASA POWER)
- **Resolution:** Monthly averaged reanalysis data
- **Total Records:** 168 (14 years × 12 months)

### Spatial Coverage
- **Region:** Tanzania Bounding Box
- **North:** -0.99°
- **South:** -11.75°
- **West:** 29.34°
- **East:** 40.44°
- **Processing:** Spatial mean over region
- **Resolution:** 0.25° × 0.25° (~28km grid)

### Climate Variables (6 variables)

1. **2m_temperature** - Temperature at 2 Meters (K)
   - Mean monthly temperature
   - Convert to Celsius: K - 273.15

2. **2m_dewpoint_temperature** - Dewpoint Temperature at 2 Meters (K)
   - Indicates moisture content of air
   - Used to calculate relative humidity

3. **total_precipitation** - Total Precipitation (m)
   - Total monthly precipitation
   - Convert to mm: m × 1000

4. **surface_pressure** - Surface Pressure (Pa)
   - Mean monthly surface pressure
   - Indicates atmospheric conditions

5. **10m_u_component_of_wind** - U-Component of Wind at 10m (m/s)
   - East-west wind component
   - Positive = eastward

6. **10m_v_component_of_wind** - V-Component of Wind at 10m (m/s)
   - North-south wind component
   - Positive = northward

## Expected Dataset Characteristics

### File Information
- **NetCDF File:** `data/raw/era5_raw.nc` (~5-10 MB)
- **CSV File:** `data/raw/era5_raw.csv` (~20-30 KB)
- **Format:** NetCDF4 (download), CSV (processed)
- **Encoding:** UTF-8

### Data Structure
```
Columns (8):
- year (int64): Year of observation
- month (int64): Month of observation (1-12)
- temp_2m (float64): Mean temperature (K)
- dewpoint_2m (float64): Mean dewpoint temperature (K)
- total_precip (float64): Total precipitation (m)
- surface_pressure (float64): Mean surface pressure (Pa)
- wind_u_10m (float64): Mean U-component of wind (m/s)
- wind_v_10m (float64): Mean V-component of wind (m/s)

Shape: (168 rows, 8 columns)
```

## Reasoning for Dataset Size

### 1. Time Range (2010-2023)
**Why same as NASA POWER?**
- ✅ Ensures temporal alignment for data merging
- ✅ Consistent baseline period across all data sources
- ✅ Captures recent climate trends
- ✅ Sufficient data for ML models (168 samples)

**Benefits:**
- Easy to merge with NASA POWER data (same time index)
- Consistent climatological baseline
- Recent enough for current climate patterns

### 2. Monthly Resolution
**Why monthly instead of hourly/daily?**
- ✅ Reduces data volume dramatically (from ~122,000 hourly to 168 monthly)
- ✅ Matches NASA POWER temporal resolution
- ✅ Sufficient for climate prediction (not weather forecasting)
- ✅ Standard for climate reanalysis applications

**Trade-offs:**
- Hourly ERA5 data available but:
  - ~122,000 records vs 168 records
  - NetCDF files would be 100s of MB vs 5-10 MB
  - Much longer download and processing times
  - Climate models typically use monthly data

### 3. Spatial Mean (Tanzania Region)
**Why area average instead of grid?**
- ✅ Single value per time step (country-level analysis)
- ✅ Smaller file sizes (168 records vs 168 × grid_points)
- ✅ Faster processing and analysis
- ✅ Matches NASA POWER single-point approach

**Trade-offs:**
- Full grid would provide spatial variability but:
  - Much larger datasets (168 × ~400 grid points = 67,200 records)
  - Longer download times (100s of MB)
  - More complex processing
  - For country-level predictions, spatial mean is sufficient

### 4. Six Climate Variables
**Why these specific variables?**
- ✅ **Temperature & Dewpoint:** Complementary to NASA POWER temperature data
- ✅ **Precipitation:** Cross-validation with CHIRPS rainfall data
- ✅ **Surface Pressure:** Atmospheric conditions, weather patterns
- ✅ **Wind Components:** Air circulation, moisture transport

**Complementarity with NASA POWER:**
- NASA POWER: Solar radiation, humidity
- ERA5: Wind, pressure, dewpoint
- Together: Comprehensive atmospheric state

## Comparison with NASA POWER

| Aspect | NASA POWER | ERA5 |
|--------|------------|------|
| **Source** | Satellite + Models | Reanalysis (Models + Obs) |
| **Resolution** | 0.5° (~55km) | 0.25° (~28km) |
| **Variables** | Solar, Temp, Precip, Humidity | Temp, Precip, Wind, Pressure |
| **Coverage** | 1981-present | 1940-present |
| **Update** | Near real-time | ~5 days delay |
| **Strength** | Solar radiation data | Comprehensive atmospheric state |

## CDS API Migration Issue

### Problem
The Copernicus Climate Data Store (CDS) has migrated to a new API system. The old API endpoints (v2) are no longer functional.

### Error Message
```
404 Client Error: Not Found for url: 
https://cds.climate.copernicus.eu/api/v2/retrieve/v1/processes/reanalysis-era5-single-levels-monthly-means
```

### Solution Required

1. **Register for New CDS Account:**
   - Visit: https://cds.climate.copernicus.eu/
   - Create new account or migrate existing account
   - Accept new Terms & Conditions

2. **Get New API Key:**
   - Login to new CDS portal
   - Navigate to user profile
   - Copy new API key (format changed - no UID prefix)

3. **Update Configuration:**
   ```
   url: https://cds.climate.copernicus.eu/api
   key: <your-new-api-key>
   ```

4. **Update cdsapi Package:**
   ```bash
   pip install --upgrade cdsapi
   ```

### Alternative: Use Dry-Run Mode

For testing and development, use dry-run mode:
```python
from modules.ingestion.era5_ingestion import fetch_era5_data

# Returns placeholder data without API call
df = fetch_era5_data(dry_run=True)
```

## Expected Performance

Once API access is restored:

- **Request Time:** 2-5 minutes (CDS queue processing)
- **Download Size:** 5-10 MB (NetCDF compressed)
- **Processing Time:** 10-30 seconds (NetCDF to CSV)
- **Total Time:** 3-6 minutes

## Next Steps

### Immediate (Using Dry-Run)
1. ✅ Continue pipeline development with dry-run mode
2. ✅ Test data processing modules
3. ✅ Develop merging logic with other data sources

### When API Access Restored
1. Update CDS API credentials
2. Fetch real ERA5 data (2010-2023)
3. Validate data quality
4. Process and merge with other datasets

## Workaround: Use Existing ERA5 Data

If ERA5 data is critical and API access cannot be restored quickly:

### Option 1: Download Manually
1. Visit CDS web interface: https://cds.climate.copernicus.eu/
2. Navigate to ERA5 monthly averaged data
3. Select variables, region, and time range
4. Download NetCDF file manually
5. Place in `data/raw/era5_raw.nc`
6. Run processing script

### Option 2: Use Alternative Source
- **ECMWF Public Datasets:** https://www.ecmwf.int/en/forecasts/datasets
- **Google Earth Engine:** ERA5 available through GEE
- **AWS Open Data:** ERA5 on AWS S3

### Option 3: Skip ERA5 for Now
- Continue with NASA POWER, CHIRPS, NDVI, and Ocean Indices
- ERA5 provides complementary data but is not critical
- Can add ERA5 data later when API access is restored

## Data Quality Expectations

Once fetched, ERA5 data should have:

- **Completeness:** 100% (no missing months)
- **Consistency:** Continuous time series
- **Validity:** All values within physical ranges
  - Temperature: 250-320 K (−23 to 47°C)
  - Precipitation: 0-0.5 m/month (0-500mm)
  - Pressure: 80,000-105,000 Pa
  - Wind: -20 to 20 m/s

## References

- **ERA5 Documentation:** https://confluence.ecmwf.int/display/CKB/ERA5
- **CDS API Documentation:** https://cds.climate.copernicus.eu/how-to-api
- **ERA5 Data Description:** https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means
- **Migration Guide:** https://confluence.ecmwf.int/display/CKB/New+CDS+migration+guide

---

**Generated:** November 14, 2025  
**Pipeline:** Tanzania Climate Prediction - Phase 2  
**Module:** `modules/ingestion/era5_ingestion.py`  
**Status:** Awaiting CDS API access restoration
