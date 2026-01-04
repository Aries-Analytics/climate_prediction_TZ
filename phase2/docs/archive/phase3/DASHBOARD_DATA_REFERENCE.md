# Dashboard Data Reference Guide

## Quick Reference: What Data Goes Where

### 📊 Executive Dashboard

**File:** `outputs/processed/master_dataset.csv` (73 rows including header)

**Key Columns:**
```python
# Trigger Rates
- drought_trigger (0/1)
- flood_trigger (0/1)  
- crop_failure_trigger (0/1)
- drought_trigger_confidence (0-1)
- flood_trigger_confidence (0-1)
- crop_failure_trigger_confidence (0-1)

# Severity
- trigger_severity_left (drought/flood severity)
- trigger_severity_right (crop failure severity)
- drought_severity
- flood_risk_score_left

# Sustainability Metrics
- rainfall_anomaly_pct
- ndvi_anomaly_pct
- overall_climate_risk
- climate_risk_class (low/moderate/high/critical)
```

**Calculations:**
```python
# Trigger Rate = (Number of triggers / Total months) * 100
drought_rate = (drought_trigger.sum() / len(df)) * 100
flood_rate = (flood_trigger.sum() / len(df)) * 100
crop_failure_rate = (crop_failure_trigger.sum() / len(df)) * 100

# Loss Ratio = Total Payouts / Total Premiums
# (Requires business logic - not in dataset)
```

---

### 🤖 Model Performance Dashboard

**File:** `outputs/models/training_results_20251121_195517.json`

**Structure:**
```json
{
  "random_forest": {
    "test_metrics": {
      "r2": 0.8499,
      "rmse": 0.3951,
      "mae": 0.3686,
      "mape": 28.15
    }
  },
  "xgboost": {...},
  "lstm": {...},
  "ensemble": {...}
}
```

**Feature Importance Files:**
- `outputs/models/random_forest_climate_feature_importance.csv`
- `outputs/models/xgboost_climate_feature_importance_gain.csv`

**Top Features to Display:**
```
1. rainfall_mm_lag_1
2. rainfall_30day
3. ndvi_30day_mean
4. oni (ENSO index)
5. temp_mean_c
... (top 20)
```

---

### ⚠️ Triggers Dashboard

**Files:**
- `outputs/processed/chirps_processed.csv` (drought/flood)
- `outputs/processed/ndvi_processed.csv` (crop failure)

**Drought Triggers:**
```python
# From chirps_processed.csv
- drought_trigger (boolean)
- drought_trigger_confidence (0-1)
- spi_30day (< -1.5 = severe drought)
- spi_90day
- drought_severity
- drought_duration_months
- rainfall_deficit_mm
- rainfall_deficit_pct
```

**Flood Triggers:**
```python
# From chirps_processed.csv
- flood_trigger (boolean)
- flood_trigger_confidence (0-1)
- flood_risk_score
- heavy_rain_event
- extreme_rain_event
- very_extreme_rain_event
- excess_rainfall_mm
- cumulative_excess_7day
```

**Crop Failure Triggers:**
```python
# From ndvi_processed.csv
- crop_failure_trigger (boolean)
- crop_failure_trigger_confidence (0-1)
- crop_failure_risk (0-100)
- crop_failure_risk_class (low/moderate/high/critical)
- vci (Vegetation Condition Index)
- vci_class
- is_stressed
- is_severe_stress
- drought_stress_severity
```

**Timeline Visualization:**
```python
# Group by year-month
df.groupby(['year', 'month']).agg({
    'drought_trigger': 'max',
    'flood_trigger': 'max',
    'crop_failure_trigger': 'max'
})
```

---

### 🌍 Climate Insights Dashboard

**File:** `outputs/processed/master_dataset.csv`

**Time Series Variables:**

**Rainfall:**
```python
- rainfall_mm (monthly total)
- rainfall_7day
- rainfall_14day
- rainfall_30day
- rainfall_90day
- rainfall_180day
- rainfall_clim_mean (climatology)
- rainfall_anomaly_mm (actual - climatology)
- rainfall_anomaly_pct
- rainfall_percentile
```

**Temperature:**
```python
- temp_mean_c
- temp_max_c
- temp_min_c
- temp_2m_c (ERA5)
- temp_range_c
- heat_index_c
```

**Vegetation:**
```python
- ndvi (Normalized Difference Vegetation Index)
- ndvi_30day_mean
- ndvi_60day_mean
- ndvi_90day_mean
- vci (Vegetation Condition Index, 0-100)
- ndvi_anomaly
- ndvi_anomaly_pct
- ndvi_percentile
```

**Climate Indices:**
```python
- oni (Oceanic Niño Index, ENSO indicator)
- enso_phase (el_nino/la_nina/neutral)
- iod (Indian Ocean Dipole)
- iod_phase (positive/negative/neutral)
- enso_impact_score
- iod_impact_score
- combined_impact_score
```

**Anomaly Detection:**
```python
# Flag anomalies where:
is_rainfall_anomaly = abs(rainfall_anomaly_std) > 2
is_ndvi_anomaly = abs(ndvi_anomaly_std) > 2
is_severe_drought = spi_30day < -1.5
is_extreme_wet = spi_30day > 1.5
```

**Correlation Matrix:**
```python
variables = [
    'rainfall_mm', 'ndvi', 'temp_mean_c', 
    'oni', 'iod', 'humidity_pct'
]
correlation_matrix = df[variables].corr()
```

**Seasonal Patterns:**
```python
# Seasons
- is_short_rains (Oct-Dec)
- is_long_rains (Mar-May)
- season (wet/dry)

# Overlay climatology
plt.plot(df['rainfall_mm'], label='Actual')
plt.plot(df['rainfall_clim_mean'], label='Climatology', linestyle='--')
```

---

### 🛡️ Risk Management Dashboard

**File:** `outputs/processed/ocean_indices_processed.csv`

**Forecast Probabilities:**
```python
- prob_above_normal_rainfall (0-1)
- prob_below_normal_rainfall (0-1)
- prob_normal_rainfall (0-1)
- drought_probability (0-1)
- flood_probability (0-1)
```

**Risk Scores:**
```python
- drought_risk_score (0-100)
- flood_risk_score (0-100)
- overall_climate_risk (0-100)
- climate_risk_class (low/moderate/high/critical)
```

**Early Warnings:**
```python
- early_warning_drought (boolean)
- early_warning_flood (boolean)
- climate_drought_trigger (boolean)
- climate_flood_trigger (boolean)
- climate_drought_trigger_confidence (0-1)
- climate_flood_trigger_confidence (0-1)
```

**Scenario Analysis:**
```python
# El Niño Scenario
el_nino_months = df[df['is_el_nino'] == 1]
avg_rainfall_el_nino = el_nino_months['rainfall_mm'].mean()

# La Niña Scenario
la_nina_months = df[df['is_la_nina'] == 1]
avg_rainfall_la_nina = la_nina_months['rainfall_mm'].mean()

# Positive IOD
pos_iod_months = df[df['is_positive_iod'] == 1]
avg_rainfall_pos_iod = pos_iod_months['rainfall_mm'].mean()

# Negative IOD
neg_iod_months = df[df['is_negative_iod'] == 1]
avg_rainfall_neg_iod = neg_iod_months['rainfall_mm'].mean()
```

**Portfolio Metrics:**
```python
# Calculate from trigger events
total_triggers = (
    df['drought_trigger'].sum() + 
    df['flood_trigger'].sum() + 
    df['crop_failure_trigger'].sum()
)

# Distribution
trigger_distribution = {
    'Drought': df['drought_trigger'].sum(),
    'Flood': df['flood_trigger'].sum(),
    'Crop Failure': df['crop_failure_trigger'].sum()
}

# By season
seasonal_triggers = df.groupby('season').agg({
    'drought_trigger': 'sum',
    'flood_trigger': 'sum',
    'crop_failure_trigger': 'sum'
})
```

---

## 🎨 Visualization Examples

### Time Series Chart (Plotly)
```javascript
{
  x: df['year'] + '-' + df['month'],  // "2018-1", "2018-2", ...
  y: df['rainfall_mm'],
  type: 'scatter',
  mode: 'lines+markers',
  name: 'Rainfall'
}
```

### Anomaly Highlighting
```javascript
{
  x: df['year'] + '-' + df['month'],
  y: df['rainfall_mm'],
  marker: {
    color: df['rainfall_anomaly_std'].map(val => 
      Math.abs(val) > 2 ? 'red' : 'blue'
    )
  }
}
```

### Trigger Timeline
```javascript
{
  x: df['year'] + '-' + df['month'],
  y: ['Drought', 'Flood', 'Crop Failure'],
  z: [
    df['drought_trigger'],
    df['flood_trigger'],
    df['crop_failure_trigger']
  ],
  type: 'heatmap',
  colorscale: 'RdYlGn'
}
```

### Model Comparison Bar Chart
```javascript
{
  x: ['Random Forest', 'XGBoost', 'LSTM', 'Ensemble'],
  y: [0.8499, 0.8511, 0.9022, 0.8649],
  type: 'bar',
  name: 'R² Score'
}
```

---

## 📦 Data Loading for Backend

### PostgreSQL Schema

**climate_data table:**
```sql
CREATE TABLE climate_data (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    rainfall_mm FLOAT,
    temp_mean_c FLOAT,
    ndvi FLOAT,
    oni FLOAT,
    iod FLOAT,
    drought_trigger BOOLEAN,
    flood_trigger BOOLEAN,
    crop_failure_trigger BOOLEAN,
    -- ... (all 176 columns from master_dataset.csv)
    created_at TIMESTAMP DEFAULT NOW()
);
```

**trigger_events table:**
```sql
CREATE TABLE trigger_events (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    event_type VARCHAR(50) NOT NULL,  -- 'drought', 'flood', 'crop_failure'
    severity VARCHAR(20),  -- 'low', 'moderate', 'high', 'critical'
    confidence FLOAT,
    location VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**model_metrics table:**
```sql
CREATE TABLE model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    r2_score FLOAT,
    rmse FLOAT,
    mae FLOAT,
    mape FLOAT,
    training_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Loading Script Example

```python
import pandas as pd
from sqlalchemy import create_engine

# Load master dataset
df = pd.read_csv('outputs/processed/master_dataset.csv')

# Connect to PostgreSQL
engine = create_engine('postgresql://user:pass@localhost:5432/climate_db')

# Load data
df.to_sql('climate_data', engine, if_exists='replace', index=False)

# Load trigger events
triggers = []
for idx, row in df.iterrows():
    if row['drought_trigger']:
        triggers.append({
            'event_date': f"{row['year']}-{row['month']:02d}-01",
            'event_type': 'drought',
            'severity': row.get('drought_severity', 'unknown'),
            'confidence': row.get('drought_trigger_confidence', 0)
        })
    # ... repeat for flood and crop failure

pd.DataFrame(triggers).to_sql('trigger_events', engine, if_exists='replace', index=False)
```

---

## 🔍 Quick Data Checks

### Verify Data Loaded Correctly

```python
import pandas as pd

# Load master dataset
df = pd.read_csv('outputs/processed/master_dataset.csv')

print(f"✓ Rows: {len(df)}")  # Should be 72
print(f"✓ Columns: {len(df.columns)}")  # Should be 176
print(f"✓ Date range: {df['year'].min()}-{df['month'].min()} to {df['year'].max()}-{df['month'].max()}")
print(f"✓ Missing values: {df.isnull().sum().sum()}")

# Check trigger counts
print(f"\n✓ Drought triggers: {df['drought_trigger'].sum()}")
print(f"✓ Flood triggers: {df['flood_trigger'].sum()}")
print(f"✓ Crop failure triggers: {df['crop_failure_trigger'].sum()}")

# Check data quality
print(f"\n✓ Rainfall range: {df['rainfall_mm'].min():.2f} - {df['rainfall_mm'].max():.2f} mm")
print(f"✓ NDVI range: {df['ndvi'].min():.3f} - {df['ndvi'].max():.3f}")
print(f"✓ Temperature range: {df['temp_mean_c'].min():.2f} - {df['temp_mean_c'].max():.2f} °C")
```

---

## 📚 Column Reference

### Complete Column List by Category

**Time:**
- year, month

**Weather (NASA POWER + ERA5):**
- temp_mean_c, temp_max_c, temp_min_c, temp_2m_c
- precip_mm, rainfall_mm
- humidity_pct, rel_humidity_pct
- solar_rad_wm2
- wind_speed_ms, wind_direction_deg
- pressure_hpa, surface_pressure
- dewpoint_2m_c, dewpoint_depression_c
- heat_index_c, vpd_kpa
- pet_mm (potential evapotranspiration)

**Rainfall Analysis (CHIRPS):**
- rainfall_7day, rainfall_14day, rainfall_30day, rainfall_90day, rainfall_180day
- rainfall_clim_mean, rainfall_clim_std
- rainfall_anomaly_mm, rainfall_anomaly_pct, rainfall_anomaly_std
- rainfall_percentile
- rainfall_deficit_mm, rainfall_deficit_pct
- excess_rainfall_mm, cumulative_excess_7day

**Drought Indicators:**
- spi_30day, spi_90day (Standardized Precipitation Index)
- is_dry_day, consecutive_dry_days
- drought_severity, is_drought_month, drought_duration_months
- drought_trigger, drought_trigger_confidence

**Flood Indicators:**
- heavy_rain_event, extreme_rain_event, very_extreme_rain_event
- heavy_rain_days_7day, heavy_rain_days_30day
- flood_risk_score, flood_trigger, flood_trigger_confidence

**Vegetation (NDVI):**
- ndvi, ndvi_30day_mean, ndvi_60day_mean, ndvi_90day_mean
- ndvi_trend_30day, ndvi_volatility_30day
- ndvi_change_mom, ndvi_change_yoy
- ndvi_clim_mean, ndvi_clim_std, ndvi_clim_min, ndvi_clim_max
- ndvi_anomaly, ndvi_anomaly_pct, ndvi_anomaly_std
- ndvi_percentile, ndvi_deficit_from_max, ndvi_deficit_pct
- vci (Vegetation Condition Index), vci_class, vci_30day_mean

**Vegetation Health:**
- vegetation_vigor
- is_stressed, stress_duration
- is_severe_stress, severe_stress_duration
- drought_stress_severity
- is_recovering, is_peak_greenness
- is_growing_season, is_senescence, is_critical_period

**Crop Failure:**
- crop_failure_risk, crop_failure_risk_class
- crop_failure_trigger, crop_failure_trigger_confidence
- moderate_stress_trigger, severe_stress_trigger

**Climate Indices (Ocean):**
- oni (Oceanic Niño Index)
- enso_phase (el_nino/la_nina/neutral)
- enso_strength, enso_impact_score, enso_intensity
- enso_trend_3month, enso_persistence, enso_phase_change
- is_el_nino, is_la_nina, is_strong_el_nino, is_strong_la_nina

**IOD (Indian Ocean Dipole):**
- iod, iod_phase, iod_strength, iod_impact_score, iod_intensity
- iod_trend_3month, iod_persistence, iod_phase_change
- is_positive_iod, is_negative_iod
- is_strong_positive_iod, is_strong_negative_iod

**Combined Climate:**
- combined_impact_score, enso_iod_product
- favorable_rainfall_climate
- drought_risk_climate, flood_risk_climate
- conflicting_signals, climate_uncertainty, combined_intensity

**Seasonal:**
- is_short_rains, is_long_rains, season

**Forecasts:**
- enso_3month_ahead, enso_seasonal_impact
- iod_3month_ahead, iod_seasonal_impact
- forecast_confidence
- short_rains_forecast, long_rains_forecast
- prob_above_normal_rainfall, prob_below_normal_rainfall, prob_normal_rainfall
- drought_probability, flood_probability

**Risk Scores:**
- drought_risk_score, flood_risk_score_right
- overall_climate_risk, climate_risk_class
- early_warning_drought, early_warning_flood
- climate_drought_trigger, climate_flood_trigger
- climate_drought_trigger_confidence, climate_flood_trigger_confidence
- any_climate_trigger, trigger_severity

**Metadata:**
- latitude, longitude
- lat_min_left, lat_max_left, lon_min_left, lon_max_left
- lat_min_right, lat_max_right, lon_min_right, lon_max_right
- data_source_left, data_source_right
- data_quality
- _provenance_files

---

**Last Updated:** November 21, 2025  
**Data Version:** 2.0  
**Total Columns:** 176 in master_dataset.csv, 662 in features_train.csv
