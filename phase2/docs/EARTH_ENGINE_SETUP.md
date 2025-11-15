# Google Earth Engine Setup Guide

## Quick Start

### 1. Install Earth Engine API
```bash
pip install earthengine-api
```

### 2. Authenticate (One-time)
```bash
earthengine authenticate
```
This opens a browser window for you to authorize access.

### 3. Set Project ID in `.env`
```bash
GOOGLE_CLOUD_PROJECT=climate-prediction-using-ml
```

### 4. Test Your Setup
```python
from modules.ingestion.chirps_ingestion import fetch_chirps_data

# Fetch real data
df = fetch_chirps_data(start_year=2022, end_year=2022)
print(f"Data source: {df['data_source'].iloc[0]}")
# Should print: "CHIRPS_GEE"
```

---

## What We Use Earth Engine For

### CHIRPS Rainfall Data
- **Dataset**: `UCSB-CHG/CHIRPS/DAILY`
- **Resolution**: ~5.5 km
- **Temporal**: Daily (aggregated to monthly)
- **Coverage**: 1981-present
- **Benefits**: No 1-2 GB file downloads per year

### MODIS NDVI Data
- **Dataset**: `MODIS/061/MOD13A2`
- **Resolution**: 1 km
- **Temporal**: 16-day composite (aggregated to monthly)
- **Coverage**: 2000-present
- **Benefits**: Pre-processed, cloud-masked vegetation indices

---

## Troubleshooting

### "Project not registered to use Earth Engine"
**Solution**: Register your project at:
```
https://console.cloud.google.com/earth-engine/configuration?project=climate-prediction-using-ml
```
- Select "Unpaid usage" for research/non-commercial
- Registration is instant

### "Credentials not found"
**Solution**: Run authentication:
```bash
earthengine authenticate --force
```

### "Failed to initialize Google Earth Engine"
**Check**:
1. Internet connection
2. Project ID in `.env` file
3. Authentication completed
4. Project registered with Earth Engine

**Fallback**: Pipeline automatically uses cached or synthetic data

---

## Data Sources

All fetched data includes a `data_source` column:

| Value | Meaning |
|-------|---------|
| `CHIRPS_GEE` | Real rainfall data from Earth Engine |
| `MODIS_MOD13A2_GEE` | Real NDVI data from Earth Engine |
| `climatology_based` | Synthetic data (fallback) |
| `dummy_fallback` | Emergency minimal data |

---

## Cost

**Free** for research and non-commercial use:
- $300 in credits for 90 days (new accounts)
- Always-free tier after credits expire
- No automatic charges

---

## Best Practices

1. **Cache data**: First fetch saves to `data/raw/*.csv` for offline use
2. **Monitor source**: Check `data_source` column in outputs
3. **Test offline**: Pipeline works with cached/synthetic data
4. **Update regularly**: Re-fetch periodically for latest data

---

## Advanced Usage

### Custom Region
```python
custom_bounds = {
    'lat_min': -8.0,
    'lat_max': -5.0,
    'lon_min': 33.0,
    'lon_max': 36.0
}
df = fetch_chirps_data(bounds=custom_bounds, start_year=2020, end_year=2023)
```

### Force Synthetic Data
```python
# Skip GEE, use synthetic data directly
df = fetch_chirps_data(use_gee=False, start_year=2020, end_year=2023)
```

### Dry Run (Testing)
```python
# Quick test with minimal data
df = fetch_chirps_data(dry_run=True)
```

---

## Resources

- [Earth Engine Documentation](https://developers.google.com/earth-engine)
- [CHIRPS Dataset](https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY)
- [MODIS NDVI Dataset](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13A2)
- [Python API Guide](https://developers.google.com/earth-engine/guides/python_install)
