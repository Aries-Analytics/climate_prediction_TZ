# Data Ingestion Fallback Strategy

## Overview

Our data ingestion modules implement a robust 4-tier fallback strategy to ensure the pipeline can always run, even when external data sources are unavailable.

## Fallback Hierarchy

### Tier 1: Real Satellite Data (Primary)
**Source**: Google Earth Engine
- **CHIRPS**: `UCSB-CHG/CHIRPS/DAILY` - Daily rainfall data
- **NDVI**: `MODIS/061/MOD13A2` - 16-day vegetation indices

**Advantages**:
- Real satellite observations
- High quality, analysis-ready data
- No large file downloads
- Server-side processing

**Requirements**:
- `earthengine-api` package installed
- Authenticated with `earthengine authenticate`
- Project registered with Earth Engine
- Internet connection

**When it fails**:
- GEE not installed or authenticated
- Network issues
- API rate limits exceeded
- Project not registered

---

### Tier 2: Cached Data (Secondary)
**Source**: Previously fetched real data stored locally
- **CHIRPS**: `data/raw/chirps_raw.csv`
- **NDVI**: `data/raw/ndvi_raw.csv`

**Advantages**:
- Fast (no network required)
- Real data from previous successful fetch
- Works offline

**Behavior**:
- Checks if cached file exists
- Validates date range coverage
- Uses cached data if it covers requested years
- Falls through if missing years

**When it fails**:
- No cached file exists
- Cached data doesn't cover requested date range
- File is corrupted

---

### Tier 3: Synthetic Climatological Data (Tertiary)
**Source**: Generated based on Tanzania's climate patterns
- **CHIRPS**: Realistic rainfall with seasonal patterns
- **NDVI**: Vegetation patterns following bimodal rainfall

**Advantages**:
- Always available
- Realistic patterns for Tanzania
- Reproducible (seeded random generation)
- Good for testing and development

**Characteristics**:
- Reflects Tanzania's bimodal rainfall (MAM & OND)
- Includes seasonal variations
- Contains some extreme events (droughts, floods)
- Saved to separate files (`*_synthetic.csv`)

**When to use**:
- Development and testing
- GEE unavailable
- No cached data available
- Offline work

---

### Tier 4: Minimal Dummy Data (Last Resort)
**Source**: Hardcoded minimal values

**Characteristics**:
- Single data point per dataset
- Just enough to prevent pipeline crashes
- Clearly marked as `dummy_fallback`

**When it's used**:
- All other strategies failed
- Synthetic data generation failed
- Emergency fallback only

**Warning**: This data is NOT suitable for analysis, only for keeping the pipeline running.

---

## Implementation Details

### CHIRPS Rainfall

```python
# Tier 1: Real data from GEE
df = fetch_chirps_data(start_year=2020, end_year=2023, use_gee=True)

# Tier 2: Cached data (automatic fallback)
# Checks: data/raw/chirps_raw.csv

# Tier 3: Synthetic data
# Saves to: data/raw/chirps_synthetic.csv

# Tier 4: Dummy data (last resort)
# Returns single data point
```

### NDVI Vegetation Index

```python
# Tier 1: Real MODIS data from GEE
df = fetch_ndvi_data(start_year=2020, end_year=2023, use_gee=True)

# Tier 2: Cached data (automatic fallback)
# Checks: data/raw/ndvi_raw.csv

# Tier 3: Synthetic data
# Saves to: data/raw/ndvi_synthetic.csv

# Tier 4: Dummy data (last resort)
# Returns single data point
```

---

## Data Source Identification

All data includes a `data_source` column to track origin:

| Source | Value | Description |
|--------|-------|-------------|
| Real GEE | `CHIRPS_GEE` or `MODIS_MOD13A2_GEE` | Real satellite data |
| Cached | Same as original source | From previous fetch |
| Synthetic | `climatology_based` | Generated realistic patterns |
| Dummy | `dummy_fallback` | Emergency minimal data |
| Dry Run | `dry_run` | Testing mode |

---

## Best Practices

### For Production
1. Always use Tier 1 (real GEE data) when possible
2. Keep cached data for offline work
3. Monitor `data_source` column in outputs
4. Alert if falling back to synthetic data

### For Development
1. Use `dry_run=True` for quick testing
2. Synthetic data is fine for algorithm development
3. Test with real data before deployment
4. Document which data source was used

### For Testing
1. Use `dry_run=True` for unit tests
2. Test each fallback tier independently
3. Verify pipeline works with all data sources
4. Check `data_source` column in assertions

---

## Monitoring Data Quality

Check which data source is being used:

```python
df = fetch_chirps_data(start_year=2020, end_year=2023)

# Check data source
print(f"Data source: {df['data_source'].iloc[0]}")

# Verify data quality
if df['data_source'].iloc[0] == 'CHIRPS_GEE':
    print("✓ Using real satellite data")
elif df['data_source'].iloc[0] == 'climatology_based':
    print("⚠ Using synthetic data - consider re-fetching with GEE")
elif df['data_source'].iloc[0] == 'dummy_fallback':
    print("✗ Using dummy data - NOT suitable for analysis!")
```

---

## Troubleshooting

### "Failed to fetch from Google Earth Engine"
1. Check internet connection
2. Verify authentication: `earthengine authenticate`
3. Check project registration
4. Pipeline will use cached or synthetic data

### "Cached data missing years"
- Cached data exists but doesn't cover requested range
- Pipeline will generate synthetic data
- Re-fetch with GEE to update cache

### "Using synthetic data"
- This is normal if GEE is unavailable
- Good for development, not for production analysis
- Set up GEE for real data

### "Returning minimal dummy data"
- Emergency fallback only
- Check logs for underlying errors
- Fix GEE setup or data generation issues

---

## Configuration

Control fallback behavior:

```python
# Force GEE (fail if unavailable)
df = fetch_chirps_data(use_gee=True)

# Skip GEE, use synthetic directly
df = fetch_chirps_data(use_gee=False)

# Quick testing mode
df = fetch_chirps_data(dry_run=True)
```

---

## Summary

The 4-tier fallback strategy ensures:
- ✓ Pipeline always runs
- ✓ Best available data is used
- ✓ Graceful degradation
- ✓ Clear data provenance
- ✓ Suitable for development and production
