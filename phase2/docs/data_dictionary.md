# Data Dictionary

## Overview

This document describes the data schemas for all datasets in the Tanzania Climate Prediction pipeline.

## Raw Data Schemas

### NASA POWER Raw Data

**File:** `data/raw/nasa_power_raw.csv`

| Column | Type | Unit | Description | Range |
|--------|------|------|-------------|-------|
| year | int | - | Year of observation | 2010-2023 |
| month | int | - | Month of observation | 1-12 |
| latitude | float | degrees | Latitude coordinate | -90 to 90 |
| longitude | float | degrees | Longitude coordinate | -180 to 180 |
| t2m | float | °C | Mean temperature at 2m | -50 to 50 |
| t2m_max | float | °C | Maximum temperature at 2m | -50 to 50 |
| t2m_min | float | °C | Minimum temperature at 2m | -50 to 50 |
| prectotcorr | float | mm | Total monthly precipitation | 0 to 1000+ |
| rh2m | float | % | Relative humidity at 2m | 0 to 100 |
| allsky_sfc_sw_dwn | float | W/m² | Solar radiation | 0 to 400 |

**Missing Values:** Represented as `None` or `NaN`

**Source:** NASA POWER API (https://power.larc.nasa.gov/)

---

### ERA5 Raw Data

**File:** `data/raw/era5_raw.csv`

| Column | Type | Unit | Description | Range |
|--------|------|------|-------------|-------|
| year | int | - | Year of observation | 2010-2023 |
| month | int | - | Month of observation | 1-12 |
| temp_2m | float | K | Temperature at 2m | 200 to 350 |
| dewpoint_2m | float | K | Dewpoint temperature at 2m | 200 to 350 |
| total_precip | float | m | Total precipitation | 0 to 1+ |
| surface_pressure | float | Pa | Surface pressure | 50000 to 110000 |
| wind_u_10m | float | m/s | U-component of wind at 10m | -50 to 50 |
| wind_v_10m | float | m/s | V-component of wind at 10m | -50 to 50 |

**Notes:**
- Temperature in Kelvin (convert to Celsius: K - 273.15)
- Precipitation in meters (convert to mm: m × 1000)
- Spatial mean over Tanzania region

**Source:** Copernicus ERA5 Reanalysis

---

### CHIRPS Raw Data

**File:** `data/raw/chirps_raw.csv`

| Column | Type | Unit | Description | Range |
|--------|------|------|-------------|-------|
| year | int | - | Year of observation | 2010-2023 |
| month | int | - | Month of observation | 1-12 |
| rainfall_mm | float | mm | Mean monthly rainfall | 0 to 1000+ |
| lat_min | float | degrees | Minimum latitude of region | -11.75 |
| lat_max | float | degrees | Maximum latitude of region | -0.99 |
| lon_min | float | degrees | Minimum longitude of region | 29.34 |
| lon_max | float | degrees | Maximum longitude of region | 40.44 |

**Notes:**
- Spatial mean over Tanzania bounding box
- Daily data aggregated to monthly totals

**Source:** UCSB Climate Hazards Center CHIRPS v2.0

---

### NDVI Raw Data

**File:** `data/raw/ndvi_raw.csv`

| Column | Type | Unit | Description | Range |
|--------|------|------|-------------|-------|
| year | int | - | Year of observation | 2010-2023 |
| month | int | - | Month of observation | 1-12 |
| ndvi | float | - | Normalized Difference Vegetation Index | 0.0 to 1.0 |
| lat_min | float | degrees | Minimum latitude of region | -11.75 |
| lat_max | float | degrees | Maximum latitude of region | -0.99 |
| lon_min | float | degrees | Minimum longitude of region | 29.34 |
| lon_max | float | degrees | Maximum longitude of region | 40.44 |
| data_source | string | - | Data source identifier | "climatology_based" |

**NDVI Interpretation:**
- 0.0-0.1: Bare soil, rock, sand
- 0.1-0.2: Sparse vegetation
- 0.2-0.5: Grassland, crops
- 0.5-0.8: Dense vegetation, forests
- 0.8-1.0: Very dense vegetation

**Data Sources:**

1. **MODIS MOD13A2 via Google Earth Engine** (Primary):
   - Real satellite measurements from NASA Terra
   - 1 km resolution, 16-day composites
   - Aggregated to monthly means
   - Requires GEE authentication
   - data_source: "MODIS_MOD13A2_GEE"

2. **Synthetic Climatology** (Fallback):
   - Used when GEE is unavailable or not authenticated
   - Based on Tanzania's seasonal patterns
   - Reproducible for testing
   - data_source: "climatology_based"

**Setup:** See `docs/GEE_SETUP.md` for Google Earth Engine authentication

**Source:** Google Earth Engine (MODIS) or Synthetic

---

### Ocean Indices Raw Data

**File:** `data/raw/ocean_indices_raw.csv`

| Column | Type | Unit | Description | Range |
|--------|------|------|-------------|-------|
| year | int | - | Year of observation | 2010-2023 |
| month | int | - | Month of observation | 1-12 |
| oni | float | °C | Oceanic Niño Index | -3.0 to 3.0 |
| enso_phase | string | - | ENSO phase classification | "El Niño", "La Niña", "Neutral" |
| iod | float | °C | Indian Ocean Dipole index | -2.0 to 2.0 |

**ENSO Phase Classification:**
- ONI ≥ 0.5: El Niño
- ONI ≤ -0.5: La Niña
- -0.5 < ONI < 0.5: Neutral

**IOD Interpretation:**
- Positive (> 0.4): Increased East African rainfall
- Neutral (-0.4 to 0.4): Normal conditions
- Negative (< -0.4): Decreased East African rainfall

**Source:** NOAA Climate Prediction Center (ONI), NOAA PSL (IOD)

---

## Processed Data Schemas

### NASA POWER Processed

**File:** `outputs/processed/nasa_power_processed.csv`

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| latitude | float | degrees | Latitude coordinate |
| longitude | float | degrees | Longitude coordinate |
| temperature_c | float | °C | Temperature |
| solar_radiation_wm2 | float | W/m² | Solar radiation |

**Note:** Current implementation returns placeholder data

---

### ERA5 Processed

**File:** `outputs/processed/era5_processed.csv`

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| latitude | float | degrees | Latitude coordinate |
| longitude | float | degrees | Longitude coordinate |
| temperature_c | float | °C | Temperature |
| humidity_percent | float | % | Humidity |

**Note:** Current implementation returns placeholder data

---

### CHIRPS Processed

**File:** `outputs/processed/chirps_processed.csv`

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| latitude | float | degrees | Latitude coordinate |
| longitude | float | degrees | Longitude coordinate |
| rainfall_mm | float | mm | Rainfall |

**Note:** Current implementation returns placeholder data

---

### NDVI Processed

**File:** `outputs/processed/ndvi_processed.csv`

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| latitude | float | degrees | Latitude coordinate |
| longitude | float | degrees | Longitude coordinate |
| ndvi | float | - | NDVI value |

**Note:** Current implementation returns placeholder data

---

### Ocean Indices Processed

**File:** `outputs/processed/ocean_indices_processed.csv`

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| year | int | - | Year |
| month | string | - | Month name |
| enso_index | float | °C | ENSO index |
| iod_index | float | °C | IOD index |

**Note:** Current implementation returns placeholder data

---

## Master Dataset Schema

**Files:** 
- `outputs/processed/master_dataset.csv`
- `outputs/processed/master_dataset.parquet`

The master dataset combines all processed datasets. The exact schema depends on the merging strategy used:

### Common Columns

| Column | Type | Description |
|--------|------|-------------|
| _provenance_files | string | Comma-separated list of source files |

### Additional Columns

Varies based on merge strategy and available data sources. May include:
- year, month (if year-based merge)
- latitude, longitude (if geo-based merge)
- All columns from processed datasets (with suffixes if conflicts)

### Merge Strategies

1. **Year-based merge:**
   - Outer join on 'year' column
   - Columns from different sources may have suffixes (_left, _right)

2. **Geo-based merge:**
   - Outer join on ['latitude', 'longitude']
   - Preserves spatial relationships

3. **Concatenation:**
   - Rows concatenated with _source_file column
   - Used when no common keys exist

---

## Data Quality Notes

### Missing Values

- Represented as `None`, `NaN`, or empty strings
- NASA POWER: -999 flag converted to None
- IOD: -999 flag filtered out
- CHIRPS: Continues with available years if some fail

### Temporal Coverage

- Default range: 2010-2023
- Configurable via `start_year` and `end_year` parameters
- Some sources may have gaps or limited coverage

### Spatial Coverage

- Tanzania bounding box:
  - Latitude: -11.75 to -0.99
  - Longitude: 29.34 to 40.44
- NASA POWER: Point data (center of Tanzania)
- ERA5, CHIRPS, NDVI: Spatial mean over region

### Data Frequency

- All datasets aggregated to monthly resolution
- Original frequencies:
  - NASA POWER: Daily → Monthly
  - ERA5: Monthly (pre-aggregated)
  - CHIRPS: Daily → Monthly
  - NDVI: Monthly
  - Ocean Indices: Monthly

---

## Units and Conversions

### Temperature

- NASA POWER: °C (native)
- ERA5: K (convert: K - 273.15 = °C)

### Precipitation

- NASA POWER: mm/day → mm/month (sum)
- ERA5: m (convert: m × 1000 = mm)
- CHIRPS: mm (native)

### Wind

- ERA5: m/s (native)
- Wind speed: √(u² + v²)

### Pressure

- ERA5: Pa (convert: Pa / 100 = hPa or mb)

---

## Data Validation Rules

### Required Checks

1. **Structure**: Must be pandas DataFrame
2. **Non-empty**: Must have at least one row
3. **Columns**: Must have expected columns (if specified)
4. **Types**: Numeric columns must be numeric

### Warning Conditions

- Missing values present
- Outliers detected (future enhancement)
- Unexpected column names

### Failure Conditions

- Not a DataFrame
- Empty DataFrame
- Missing required columns
- All values are null

---

## Example Data Samples

### NASA POWER Raw (first 3 rows)

```csv
year,month,latitude,longitude,t2m,t2m_max,t2m_min,prectotcorr,rh2m,allsky_sfc_sw_dwn
2010,1,-6.369028,34.888822,24.12,29.45,19.23,145.2,72.3,215.4
2010,2,-6.369028,34.888822,24.56,29.87,19.67,132.8,71.8,223.1
2010,3,-6.369028,34.888822,24.89,30.12,20.01,178.5,73.5,218.7
```

### Ocean Indices Raw (first 3 rows)

```csv
year,month,oni,enso_phase,iod
2010,1,1.23,El Niño,0.45
2010,2,1.05,El Niño,0.38
2010,3,0.78,El Niño,0.22
```

### Master Dataset (example structure)

```csv
year,latitude,longitude,temperature_c,rainfall_mm,ndvi,oni,iod,_provenance_files
2020,-6.37,34.89,25.3,145.2,0.68,0.34,0.12,"nasa_power_processed.csv,chirps_processed.csv,ndvi_processed.csv,ocean_indices_processed.csv"
```
