# Processing Features Summary

## Quick Reference Guide

This document provides a quick reference to all features created by the processing modules. Use this as a lookup guide when working with processed data.

---

## CHIRPS Rainfall Features

**File:** `data/processed/chirps_processed.csv`  
**Module:** `modules/processing/process_chirps.py`  
**Total Features:** 40+

### Rolling Statistics
| Feature | Description | Range |
|---------|-------------|-------|
| `rainfall_7day` | 7-day cumulative rainfall | 0+ mm |
| `rainfall_14day` | 14-day cumulative rainfall | 0+ mm |
| `rainfall_30day` | 30-day cumulative rainfall | 0+ mm |
| `rainfall_90day` | 90-day cumulative rainfall | 0+ mm |
| `rainfall_180day` | 180-day cumulative rainfall | 0+ mm |

### Drought Indicators
| Feature | Description | Range |
|---------|-------------|-------|
| `consecutive_dry_days` | Days with <1mm rain | 0+ days |
| `spi_30day` | Standardized Precipitation Index (30-day) | -3 to +3 |
| `spi_90day` | Standardized Precipitation Index (90-day) | -3 to +3 |
| `rainfall_deficit_mm` | Deficit from climatology | mm |
| `rainfall_deficit_pct` | Deficit percentage | % |
| `drought_severity` | Drought severity score | 0-1 |
| `drought_duration_months` | Consecutive drought months | 0+ months |

### Flood Indicators
| Feature | Description | Range |
|---------|-------------|-------|
| `heavy_rain_event` | >50mm in a day | 0/1 |
| `extreme_rain_event` | >100mm in a day | 0/1 |
| `very_extreme_rain_event` | >150mm in a day | 0/1 |
| `heavy_rain_days_7day` | Heavy rain days in 7 days | 0-7 |
| `heavy_rain_days_30day` | Heavy rain days in 30 days | 0-30 |
| `excess_rainfall_mm` | Rainfall above 95th percentile | 0+ mm |
| `cumulative_excess_7day` | 7-day cumulative excess | 0+ mm |
| `flood_risk_score` | Flood risk composite | 0-100 |

### Anomalies
| Feature | Description | Range |
|---------|-------------|-------|
| `rainfall_anomaly_mm` | Deviation from climatology | mm |
| `rainfall_anomaly_pct` | Percentage deviation | % |
| `rainfall_anomaly_std` | Standardized anomaly | z-score |
| `rainfall_percentile` | Percentile rank | 0-100 |

### Insurance Triggers
| Feature | Description | Range |
|---------|-------------|-------|
| `drought_trigger` | Drought insurance trigger | 0/1 |
| `flood_trigger` | Flood insurance trigger | 0/1 |
| `drought_trigger_confidence` | Trigger confidence | 0-1 |
| `flood_trigger_confidence` | Trigger confidence | 0-1 |
| `any_trigger` | Any trigger active | 0/1 |
| `trigger_severity` | Payout severity | 0-1 |

---

## NDVI Vegetation Features

**File:** `data/processed/ndvi_processed.csv`  
**Module:** `modules/processing/process_ndvi.py`  
**Total Features:** 46+

### Temporal Statistics
| Feature | Description | Range |
|---------|-------------|-------|
| `ndvi_30day_mean` | 30-day rolling mean | -1 to 1 |
| `ndvi_60day_mean` | 60-day rolling mean | -1 to 1 |
| `ndvi_90day_mean` | 90-day rolling mean | -1 to 1 |
| `ndvi_trend_30day` | 30-day linear trend | slope |
| `ndvi_volatility_30day` | 30-day standard deviation | 0+ |
| `ndvi_change_mom` | Month-to-month change | Δ NDVI |
| `ndvi_change_yoy` | Year-over-year change | Δ NDVI |

### Anomalies
| Feature | Description | Range |
|---------|-------------|-------|
| `ndvi_anomaly` | Deviation from climatology | NDVI units |
| `ndvi_anomaly_pct` | Percentage deviation | % |
| `ndvi_anomaly_std` | Standardized anomaly | z-score |
| `ndvi_percentile` | Percentile rank | 0-100 |
| `ndvi_deficit_from_max` | Deficit from peak | NDVI units |
| `ndvi_deficit_pct` | Deficit percentage | % |

### Vegetation Condition Index
| Feature | Description | Range |
|---------|-------------|-------|
| `vci` | Vegetation Condition Index | 0-100 |
| `vci_class` | VCI classification | categorical |
| `vci_30day_mean` | 30-day rolling VCI | 0-100 |

### Drought Stress
| Feature | Description | Range |
|---------|-------------|-------|
| `vegetation_vigor` | Vegetation vigor score | 0-100 |
| `is_stressed` | Stress indicator | 0/1 |
| `stress_duration` | Consecutive stressed periods | 0+ |
| `is_severe_stress` | Severe stress indicator | 0/1 |
| `severe_stress_duration` | Severe stress duration | 0+ |
| `drought_stress_severity` | Stress severity | 0-1 |
| `is_recovering` | Recovery indicator | 0/1 |

### Growth Stages
| Feature | Description | Range |
|---------|-------------|-------|
| `is_peak_greenness` | Peak greenness indicator | 0/1 |
| `is_growing_season` | Growing season indicator | 0/1 |
| `is_senescence` | Senescence indicator | 0/1 |
| `is_critical_period` | Critical growth period | 0/1 |

### Crop Failure Risk
| Feature | Description | Range |
|---------|-------------|-------|
| `crop_failure_risk` | Crop failure risk score | 0-100 |
| `crop_failure_risk_class` | Risk classification | categorical |

### Insurance Triggers
| Feature | Description | Range |
|---------|-------------|-------|
| `crop_failure_trigger` | Crop failure trigger | 0/1 |
| `crop_failure_trigger_confidence` | Trigger confidence | 0-1 |
| `moderate_stress_trigger` | Moderate stress trigger | 0/1 |
| `severe_stress_trigger` | Severe stress trigger | 0/1 |
| `trigger_severity` | Payout severity | 0-1 |
| `days_since_trigger` | Days since last trigger | 0+ |

---

## Ocean Indices Climate Features

**File:** `data/processed/ocean_indices_processed.csv`  
**Module:** `modules/processing/process_ocean_indices.py`  
**Total Features:** 60+

### ENSO Indicators
| Feature | Description | Range |
|---------|-------------|-------|
| `enso_strength` | ENSO strength classification | categorical |
| `enso_phase` | Numeric ENSO phase | -2 to 2 |
| `enso_impact_score` | Impact score for East Africa | -1 to 1 |
| `enso_trend_3month` | 3-month change | Δ ONI |
| `enso_persistence` | Months in current phase | 0+ |
| `enso_phase_change` | Phase transition indicator | 0/1 |
| `is_el_nino` | El Niño indicator | 0/1 |
| `is_la_nina` | La Niña indicator | 0/1 |
| `is_strong_el_nino` | Strong El Niño | 0/1 |
| `is_strong_la_nina` | Strong La Niña | 0/1 |
| `enso_intensity` | ENSO intensity | 0+ |

### IOD Indicators
| Feature | Description | Range |
|---------|-------------|-------|
| `iod_strength` | IOD strength classification | categorical |
| `iod_phase` | Numeric IOD phase | -2 to 2 |
| `iod_impact_score` | Impact score for East Africa | -1 to 1 |
| `iod_trend_3month` | 3-month change | Δ IOD |
| `iod_persistence` | Months in current phase | 0+ |
| `iod_phase_change` | Phase transition indicator | 0/1 |
| `is_positive_iod` | Positive IOD indicator | 0/1 |
| `is_negative_iod` | Negative IOD indicator | 0/1 |
| `is_strong_positive_iod` | Strong positive IOD | 0/1 |
| `is_strong_negative_iod` | Strong negative IOD | 0/1 |
| `iod_intensity` | IOD intensity | 0+ |

### Combined Climate Impacts
| Feature | Description | Range |
|---------|-------------|-------|
| `combined_impact_score` | Weighted ENSO+IOD impact | -1 to 1 |
| `enso_iod_product` | Interaction term | product |
| `favorable_rainfall_climate` | Favorable conditions | 0/1 |
| `drought_risk_climate` | Drought risk conditions | 0/1 |
| `flood_risk_climate` | Flood risk conditions | 0/1 |
| `conflicting_signals` | Conflicting ENSO/IOD | 0/1 |
| `climate_uncertainty` | Uncertainty score | 0-1 |
| `combined_intensity` | Maximum intensity | 0+ |

### Seasonal Forecasts
| Feature | Description | Range |
|---------|-------------|-------|
| `is_short_rains` | Short rains season | 0/1 |
| `is_long_rains` | Long rains season | 0/1 |
| `enso_3month_ahead` | 3-month lead ENSO | ONI |
| `iod_3month_ahead` | 3-month lead IOD | IOD |
| `enso_seasonal_impact` | ENSO seasonal impact | score |
| `iod_seasonal_impact` | IOD seasonal impact | score |
| `forecast_confidence` | Forecast confidence | 0-1 |
| `short_rains_forecast` | Short rains forecast | score |
| `long_rains_forecast` | Long rains forecast | score |

### Rainfall Probabilities
| Feature | Description | Range |
|---------|-------------|-------|
| `prob_above_normal_rainfall` | Above-normal probability | 0-1 |
| `prob_below_normal_rainfall` | Below-normal probability | 0-1 |
| `prob_normal_rainfall` | Normal probability | 0-1 |
| `drought_probability` | Drought probability | 0-1 |
| `flood_probability` | Flood probability | 0-1 |

### Climate Risk
| Feature | Description | Range |
|---------|-------------|-------|
| `drought_risk_score` | Drought risk score | 0-100 |
| `flood_risk_score` | Flood risk score | 0-100 |
| `overall_climate_risk` | Overall climate risk | 0-100 |
| `climate_risk_class` | Risk classification | categorical |
| `early_warning_drought` | 3-month drought warning | 0/1 |
| `early_warning_flood` | 3-month flood warning | 0/1 |

### Insurance Triggers
| Feature | Description | Range |
|---------|-------------|-------|
| `climate_drought_trigger` | Climate drought trigger | 0/1 |
| `climate_flood_trigger` | Climate flood trigger | 0/1 |
| `climate_drought_trigger_confidence` | Trigger confidence | 0-1 |
| `climate_flood_trigger_confidence` | Trigger confidence | 0-1 |
| `any_climate_trigger` | Any trigger active | 0/1 |
| `trigger_severity` | Payout severity | 0-1 |

---

## NASA POWER Features

**File:** `data/processed/nasa_power_processed.csv`  
**Module:** `modules/processing/process_nasa_power.py`  
**Total Features:** 20+

### Temperature Indicators
- Temperature anomalies (deviation from climatology)
- Heat stress days (days above critical thresholds)
- Growing degree days (accumulated heat units)
- Extreme temperature events

### Solar Radiation
- Solar radiation anomalies
- Cumulative solar radiation

### Agricultural Indicators
- Crop stress indicators
- Optimal growing conditions

---

## ERA5 Atmospheric Features

**File:** `data/processed/era5_processed.csv`  
**Module:** `modules/processing/process_era5.py`  
**Total Features:** 20+

### Atmospheric Indicators
- Pressure anomalies
- Wind speed analysis
- Moisture metrics
- Atmospheric stability

### Weather Patterns
- Extreme weather events
- Atmospheric circulation patterns

---

## Feature Categories Summary

### By Type

| Category | Count | Description |
|----------|-------|-------------|
| Temporal Statistics | 30+ | Rolling means, trends, changes |
| Anomalies | 25+ | Deviations from climatology |
| Risk Scores | 15+ | Composite risk indicators (0-100) |
| Insurance Triggers | 20+ | Binary trigger flags (0/1) |
| Confidence Scores | 10+ | Trigger confidence (0-1) |
| Classifications | 15+ | Categorical indicators |
| Specialized Indices | 43+ | SPI, VCI, ENSO, IOD, etc. |

### By Data Source

| Source | Features | Key Indicators |
|--------|----------|----------------|
| CHIRPS | 40+ | SPI, drought/flood triggers |
| NDVI | 46+ | VCI, crop failure risk |
| Ocean Indices | 60+ | ENSO/IOD, climate forecasts |
| NASA POWER | 20+ | Temperature, solar radiation |
| ERA5 | 20+ | Atmospheric indicators |
| **Total** | **186+** | **Comprehensive coverage** |

---

## Usage Examples

### Accessing Features

```python
import pandas as pd

# Load processed data
chirps = pd.read_csv('data/processed/chirps_processed.csv')
ndvi = pd.read_csv('data/processed/ndvi_processed.csv')
ocean = pd.read_csv('data/processed/ocean_indices_processed.csv')

# Access specific features
drought_events = chirps[chirps['drought_trigger'] == 1]
high_crop_risk = ndvi[ndvi['crop_failure_risk'] > 75]
el_nino_periods = ocean[ocean['is_el_nino'] == 1]
```

### Combining Features

```python
# Merge all processed data
from modules.processing import merge_processed

merged = merge_processed.merge_all_processed()

# Create composite risk score
merged['total_risk'] = (
    merged['drought_severity'] * 0.3 +
    merged['crop_failure_risk'] / 100 * 0.4 +
    merged['drought_risk_score'] / 100 * 0.3
)
```

### Insurance Payout Logic

```python
# Drought payout
drought_payout = (
    (chirps['drought_trigger'] == 1) |
    (ndvi['crop_failure_trigger'] == 1) |
    (ocean['climate_drought_trigger'] == 1)
)

# Calculate payout amount
payout_severity = np.maximum(
    chirps['drought_severity'],
    ndvi['trigger_severity'],
    ocean['trigger_severity']
)

payout_amount = payout_severity * max_payout * drought_payout
```

---

## Feature Interpretation Guide

### Risk Scores (0-100)

| Range | Interpretation | Action |
|-------|----------------|--------|
| 0-25 | Low risk | Normal monitoring |
| 25-50 | Moderate risk | Increased monitoring |
| 50-75 | High risk | Alert farmers, prepare |
| 75-100 | Extreme risk | Activate insurance triggers |

### Confidence Scores (0-1)

| Range | Interpretation | Reliability |
|-------|----------------|-------------|
| 0.0-0.3 | Low confidence | Uncertain signal |
| 0.3-0.7 | Moderate confidence | Mixed signals |
| 0.7-1.0 | High confidence | Strong agreement |

### Severity Scores (0-1)

| Range | Interpretation | Payout |
|-------|----------------|--------|
| 0.0-0.25 | Mild | 0-25% of max |
| 0.25-0.5 | Moderate | 25-50% of max |
| 0.5-0.75 | Severe | 50-75% of max |
| 0.75-1.0 | Extreme | 75-100% of max |

### SPI Values

| Range | Interpretation | Category |
|-------|----------------|----------|
| > 2.0 | Extremely wet | Flood risk |
| 1.5 to 2.0 | Very wet | Above normal |
| 1.0 to 1.5 | Moderately wet | Above normal |
| -1.0 to 1.0 | Near normal | Normal |
| -1.5 to -1.0 | Moderately dry | Below normal |
| -2.0 to -1.5 | Severely dry | Drought |
| < -2.0 | Extremely dry | Severe drought |

### VCI Values

| Range | Interpretation | Vegetation Health |
|-------|----------------|-------------------|
| > 50 | Normal to good | Healthy |
| 35-50 | Moderate stress | Stressed |
| 20-35 | Severe stress | Very stressed |
| < 20 | Extreme stress | Crop failure likely |

---

## Documentation

For detailed information about each module:
- **CHIRPS:** See `modules/processing/process_chirps.py` docstrings
- **NDVI:** See `modules/processing/process_ndvi.py` docstrings
- **Ocean Indices:** See `modules/processing/process_ocean_indices.py` docstrings
- **Complete Guide:** See `docs/PROCESSING_MODULES_COMPLETE.md`

---

**Last Updated:** November 14, 2024  
**Version:** 1.0  
**Status:** Production Ready
