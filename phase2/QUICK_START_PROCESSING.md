# Quick Start Guide - Processing Modules

## Running the Demos

### 1. CHIRPS Rainfall Processing Demo
```bash
python demo_chirps_synthetic.py
```
**Shows:** Drought indicators, flood indicators, insurance triggers

---

### 2. NDVI Vegetation Processing Demo
```bash
python demo_ndvi_synthetic.py
```
**Shows:** Vegetation health (VCI), crop failure risk, stress indicators

---

### 3. Ocean Indices Climate Processing Demo
```bash
python demo_ocean_indices_synthetic.py
```
**Shows:** ENSO/IOD phases, rainfall probabilities, climate risk, early warnings

---

## Using the Processing Modules

### Basic Usage

```python
from modules.processing import process_chirps, process_ndvi, process_ocean_indices
import pandas as pd

# Load raw data
chirps_raw = pd.read_csv('data/raw/chirps_raw.csv')
ndvi_raw = pd.read_csv('data/raw/ndvi_raw.csv')
ocean_raw = pd.read_csv('data/raw/ocean_indices_raw.csv')

# Process data
chirps_processed = process_chirps.process(chirps_raw)
ndvi_processed = process_ndvi.process(ndvi_raw)
ocean_processed = process_ocean_indices.process(ocean_raw)

# Access features
print(f"CHIRPS features: {chirps_processed.columns.tolist()}")
print(f"NDVI features: {ndvi_processed.columns.tolist()}")
print(f"Ocean features: {ocean_processed.columns.tolist()}")
```

---

## Key Features by Module

### CHIRPS (Rainfall)
- `drought_trigger` - Insurance trigger for drought (0/1)
- `flood_trigger` - Insurance trigger for flood (0/1)
- `drought_severity` - Drought severity score (0-1)
- `flood_risk_score` - Flood risk score (0-100)
- `spi_30day` - Standardized Precipitation Index
- `consecutive_dry_days` - Consecutive days with <1mm rain

### NDVI (Vegetation)
- `crop_failure_trigger` - Insurance trigger for crop failure (0/1)
- `crop_failure_risk` - Crop failure risk score (0-100)
- `vci` - Vegetation Condition Index (0-100)
- `drought_stress_severity` - Drought stress severity (0-1)
- `stress_duration` - Consecutive stressed periods
- `vegetation_vigor` - Vegetation vigor score (0-100)

### Ocean Indices (Climate)
- `climate_drought_trigger` - Climate-based drought trigger (0/1)
- `climate_flood_trigger` - Climate-based flood trigger (0/1)
- `drought_risk_score` - Drought risk from climate (0-100)
- `flood_risk_score` - Flood risk from climate (0-100)
- `prob_below_normal_rainfall` - Drought probability (0-1)
- `prob_above_normal_rainfall` - Flood probability (0-1)
- `early_warning_drought` - 3-month ahead drought warning (0/1)
- `early_warning_flood` - 3-month ahead flood warning (0/1)

---

## Insurance Trigger Examples

### Drought Insurance Payout Logic
```python
# Combine multiple drought signals
drought_payout = (
    (chirps_processed['drought_trigger'] == 1) |
    (ndvi_processed['crop_failure_trigger'] == 1) |
    (ocean_processed['climate_drought_trigger'] == 1)
)

# Calculate payout amount based on severity
payout_amount = (
    chirps_processed['drought_severity'] * 0.4 +
    ndvi_processed['trigger_severity'] * 0.4 +
    ocean_processed['trigger_severity'] * 0.2
) * max_payout

# Apply confidence threshold
high_confidence = (
    chirps_processed['drought_trigger_confidence'] > 0.7
)

final_payout = payout_amount * drought_payout * high_confidence
```

### Flood Insurance Payout Logic
```python
# Combine flood signals
flood_payout = (
    (chirps_processed['flood_trigger'] == 1) |
    (ocean_processed['climate_flood_trigger'] == 1)
)

# Calculate payout amount
payout_amount = (
    chirps_processed['flood_risk_score'] / 100 * 0.7 +
    ocean_processed['flood_risk_score'] / 100 * 0.3
) * max_payout

# Apply confidence threshold
high_confidence = (
    chirps_processed['flood_trigger_confidence'] > 0.7
)

final_payout = payout_amount * flood_payout * high_confidence
```

### Early Warning System
```python
# 3-month ahead drought warning
early_drought_warning = (
    ocean_processed['early_warning_drought'] == 1
)

# Send alert to farmers
if early_drought_warning.any():
    print("⚠️ Drought risk detected 3 months ahead")
    print("Recommended actions:")
    print("  - Plant drought-resistant crops")
    print("  - Prepare water conservation measures")
    print("  - Consider crop insurance")
```

---

## Output Files

All processed data is saved to `data/processed/`:
- `chirps_processed.csv` - Rainfall features
- `ndvi_processed.csv` - Vegetation features
- `ocean_indices_processed.csv` - Climate features
- `nasa_power_processed.csv` - Temperature/solar features
- `era5_processed.csv` - Atmospheric features

---

## Feature Categories

### 1. Temporal Statistics
Rolling means, sums, trends, changes
- Example: `rainfall_30day`, `ndvi_trend_30day`

### 2. Anomalies
Deviations from climatological normal
- Example: `rainfall_anomaly_mm`, `ndvi_anomaly_std`

### 3. Risk Scores (0-100)
Composite risk indicators
- Example: `drought_risk_score`, `crop_failure_risk`

### 4. Insurance Triggers (0/1)
Binary flags for insurance payouts
- Example: `drought_trigger`, `crop_failure_trigger`

### 5. Confidence Scores (0-1)
Trigger confidence for payout decisions
- Example: `drought_trigger_confidence`

### 6. Classifications
Categorical indicators
- Example: `enso_strength`, `vci_class`, `drought_severity`

---

## Common Workflows

### 1. Daily Monitoring
```python
# Load latest processed data
latest_data = pd.read_csv('data/processed/chirps_processed.csv')
latest_data = latest_data.sort_values('date').tail(1)

# Check for active triggers
if latest_data['drought_trigger'].iloc[0] == 1:
    print("🚨 DROUGHT TRIGGER ACTIVE")
    print(f"Confidence: {latest_data['drought_trigger_confidence'].iloc[0]:.2f}")
    print(f"Severity: {latest_data['drought_severity'].iloc[0]:.2f}")
```

### 2. Risk Assessment
```python
# Calculate overall risk
overall_risk = pd.DataFrame({
    'drought_risk': chirps_processed['drought_severity'],
    'crop_risk': ndvi_processed['crop_failure_risk'] / 100,
    'climate_risk': ocean_processed['drought_risk_score'] / 100
})

# Weighted average
overall_risk['combined'] = (
    overall_risk['drought_risk'] * 0.4 +
    overall_risk['crop_risk'] * 0.4 +
    overall_risk['climate_risk'] * 0.2
)

# Identify high-risk periods
high_risk_periods = overall_risk[overall_risk['combined'] > 0.7]
```

### 3. Seasonal Forecasting
```python
# Get short rains season forecast
short_rains = ocean_processed[ocean_processed['is_short_rains'] == 1]

# Check rainfall probability
avg_prob_below_normal = short_rains['prob_below_normal_rainfall'].mean()

if avg_prob_below_normal > 0.6:
    print("⚠️ High drought probability for short rains season")
    print(f"Probability: {avg_prob_below_normal:.1%}")
```

---

## Troubleshooting

### Issue: Module import errors
```bash
# Solution: Ensure you're in the project root directory
cd /path/to/phase2
python demo_chirps_synthetic.py
```

### Issue: Missing data directories
```bash
# Solution: Create required directories
mkdir -p data/raw data/processed data/cache logs
```

### Issue: Missing dependencies
```bash
# Solution: Install requirements
pip install -r requirements.txt
```

---

## Performance Tips

### 1. Use Parquet for Large Datasets
```python
# Save as Parquet (faster, smaller)
processed_data.to_parquet('data/processed/chirps_processed.parquet')

# Load Parquet
processed_data = pd.read_parquet('data/processed/chirps_processed.parquet')
```

### 2. Process in Chunks
```python
# For very large datasets
chunk_size = 10000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    processed_chunk = process_chirps.process(chunk)
    # Save or append chunk
```

### 3. Use Caching
```python
from utils.cache import cache_data

# Cache processed results
@cache_data(ttl=86400)  # 24 hours
def get_processed_data(date):
    raw_data = load_raw_data(date)
    return process_chirps.process(raw_data)
```

---

## Documentation

- **Full Documentation:** `docs/PROCESSING_MODULES_COMPLETE.md`
- **Implementation Status:** `docs/IMPLEMENTATION_STATUS.md`
- **Pipeline Overview:** `docs/pipeline_overview.md`
- **Data Dictionary:** `docs/data_dictionary.md`

---

## Support

For issues or questions:
1. Check the documentation in `docs/`
2. Review demo scripts for examples
3. Check module docstrings: `help(process_chirps.process)`
4. Review error logs in `logs/`

---

**Last Updated:** November 14, 2024  
**Version:** 1.0  
**Status:** Production Ready
