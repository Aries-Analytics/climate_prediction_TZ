# Feature Engineering Guide

## Overview

This document describes the feature engineering process for the Tanzania Climate Prediction project. Feature engineering transforms raw climate data into meaningful features for machine learning models.

## Current Status

**✅ UPDATED:** Processing modules now include comprehensive feature engineering! All 5 processing modules (CHIRPS, NDVI, Ocean Indices, NASA POWER, ERA5) implement insurance-focused features including:

- **148+ engineered features** across all data sources
- **20+ insurance trigger indicators** with confidence scoring
- **15+ risk scores** on standardized 0-100 scales
- **Temporal analysis** with rolling statistics and trends
- **Anomaly detection** relative to climatology
- **Early warning indicators** with 3-month lead time

See the **Implemented Features** section below for details on what's already available in the processing modules.

---

## Implemented Features (Available Now)

### CHIRPS Rainfall Processing

**Module:** `modules/processing/process_chirps.py`

**Features Available:**
- Drought indicators: SPI (30-day, 90-day), consecutive dry days, rainfall deficit
- Flood indicators: Heavy rain events, cumulative excess rainfall, flood risk score
- Rolling statistics: 7, 14, 30, 90, 180-day rainfall sums
- Anomalies: Rainfall anomaly (mm, %), percentiles
- Insurance triggers: Drought trigger, flood trigger, confidence scores

**Usage:**
```python
from modules.processing import process_chirps
processed = process_chirps.process(raw_chirps_data)
# Access features: processed['spi_30day'], processed['drought_trigger'], etc.
```

### NDVI Vegetation Processing

**Module:** `modules/processing/process_ndvi.py`

**Features Available:**
- Vegetation Condition Index (VCI): 0-100 normalized health metric
- Temporal analysis: Rolling means (30, 60, 90-day), trends, volatility
- Drought stress: Stress indicators, duration, severity (0-1 scale)
- Crop failure risk: 0-100 composite score
- Growth stages: Peak greenness, growing season, senescence
- Insurance triggers: Crop failure trigger, moderate/severe stress triggers

**Usage:**
```python
from modules.processing import process_ndvi
processed = process_ndvi.process(raw_ndvi_data)
# Access features: processed['vci'], processed['crop_failure_risk'], etc.
```

### Ocean Indices Climate Processing

**Module:** `modules/processing/process_ocean_indices.py`

**Features Available:**
- ENSO indicators: Strength, phase, persistence, trends, intensity
- IOD indicators: Strength, phase, persistence, trends, intensity
- Combined impacts: Interaction terms, conflict detection, uncertainty
- Seasonal forecasts: 3-month lead indicators, forecast confidence
- Rainfall probabilities: Above/below/normal forecasts
- Climate risk: Drought risk score, flood risk score (0-100)
- Early warnings: 3-month ahead drought/flood detection

**Usage:**
```python
from modules.processing import process_ocean_indices
processed = process_ocean_indices.process(raw_ocean_data)
# Access features: processed['enso_strength'], processed['drought_risk_score'], etc.
```

### NASA POWER Processing

**Module:** `modules/processing/process_nasa_power.py`

**Features Available:**
- Temperature indicators: Anomalies, heat stress days
- Solar radiation: Anomalies, cumulative radiation
- Agricultural indicators: Growing degree days, crop stress

### ERA5 Atmospheric Processing

**Module:** `modules/processing/process_era5.py`

**Features Available:**
- Atmospheric indicators: Pressure anomalies, wind analysis
- Moisture metrics: Humidity, atmospheric moisture
- Weather patterns: Extreme events, circulation patterns

---

## Additional Feature Engineering (Future Implementation)

This section describes additional features that can be built on top of the processed data from the modules above.

## Planned Features

### 1. Temporal Features

#### Date-based Features

```python
def extract_temporal_features(df):
    """
    Extract temporal features from date columns.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with year and month columns.
    
    Returns:
        pd.DataFrame: Dataframe with additional temporal features.
    """
    df['season'] = df['month'].map({
        12: 'short_rains', 1: 'short_rains', 2: 'short_rains',
        3: 'long_rains', 4: 'long_rains', 5: 'long_rains',
        6: 'dry', 7: 'dry', 8: 'dry', 9: 'dry',
        10: 'transition', 11: 'transition'
    })
    
    df['quarter'] = (df['month'] - 1) // 3 + 1
    df['is_rainy_season'] = df['season'].isin(['short_rains', 'long_rains'])
    
    return df
```

**Features:**
- `season`: Categorical season (short_rains, long_rains, dry, transition)
- `quarter`: Quarter of year (1-4)
- `is_rainy_season`: Boolean flag for rainy seasons

#### Lag Features

```python
def create_lag_features(df, columns, lags=[1, 2, 3]):
    """
    Create lagged features for time series prediction.
    
    Parameters:
        df (pd.DataFrame): Input dataframe sorted by time.
        columns (list): Columns to create lags for.
        lags (list): List of lag periods.
    
    Returns:
        pd.DataFrame: Dataframe with lag features.
    """
    for col in columns:
        for lag in lags:
            df[f'{col}_lag_{lag}'] = df[col].shift(lag)
    
    return df
```

**Example lag features:**
- `temperature_lag_1`: Temperature from previous month
- `rainfall_lag_3`: Rainfall from 3 months ago
- `oni_lag_6`: ENSO index from 6 months ago

#### Rolling Statistics

```python
def create_rolling_features(df, columns, windows=[3, 6, 12]):
    """
    Create rolling window statistics.
    
    Parameters:
        df (pd.DataFrame): Input dataframe sorted by time.
        columns (list): Columns to calculate rolling stats for.
        windows (list): Window sizes in months.
    
    Returns:
        pd.DataFrame: Dataframe with rolling features.
    """
    for col in columns:
        for window in windows:
            df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window).mean()
            df[f'{col}_rolling_std_{window}'] = df[col].rolling(window).std()
            df[f'{col}_rolling_min_{window}'] = df[col].rolling(window).min()
            df[f'{col}_rolling_max_{window}'] = df[col].rolling(window).max()
    
    return df
```

**Example rolling features:**
- `rainfall_rolling_mean_3`: 3-month average rainfall
- `temperature_rolling_std_6`: 6-month temperature variability
- `ndvi_rolling_max_12`: Maximum NDVI in past year

---

### 2. Climate Interaction Features

#### Temperature-Precipitation Interactions

```python
def create_climate_interactions(df):
    """
    Create interaction features between climate variables.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with climate variables.
    
    Returns:
        pd.DataFrame: Dataframe with interaction features.
    """
    # Temperature-precipitation interaction
    df['temp_precip_interaction'] = df['temperature'] * df['rainfall']
    
    # Humidity-temperature interaction
    df['humid_temp_interaction'] = df['humidity'] * df['temperature']
    
    # Drought stress indicator
    df['drought_stress'] = (df['temperature'] > df['temperature'].quantile(0.75)) & \
                           (df['rainfall'] < df['rainfall'].quantile(0.25))
    
    return df
```

**Features:**
- `temp_precip_interaction`: Combined temperature-rainfall effect
- `humid_temp_interaction`: Heat index proxy
- `drought_stress`: Boolean drought indicator

#### ENSO-IOD Interactions

```python
def create_ocean_interactions(df):
    """
    Create interaction features between ocean indices.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with ONI and IOD.
    
    Returns:
        pd.DataFrame: Dataframe with ocean interaction features.
    """
    # Combined ENSO-IOD effect
    df['enso_iod_product'] = df['oni'] * df['iod']
    
    # Favorable conditions for rainfall
    df['favorable_rainfall'] = ((df['oni'] > 0.5) & (df['iod'] > 0.4)).astype(int)
    
    # Drought risk
    df['drought_risk'] = ((df['oni'] < -0.5) & (df['iod'] < -0.4)).astype(int)
    
    return df
```

**Features:**
- `enso_iod_product`: Combined ocean index effect
- `favorable_rainfall`: Flag for conditions favoring rainfall
- `drought_risk`: Flag for drought risk conditions

---

### 3. Vegetation Features

#### NDVI-based Features

```python
def create_vegetation_features(df):
    """
    Create features from NDVI data.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with NDVI.
    
    Returns:
        pd.DataFrame: Dataframe with vegetation features.
    """
    # NDVI anomaly (deviation from mean)
    df['ndvi_anomaly'] = df['ndvi'] - df['ndvi'].mean()
    
    # NDVI change rate
    df['ndvi_change'] = df['ndvi'].diff()
    
    # Vegetation health categories
    df['vegetation_health'] = pd.cut(
        df['ndvi'],
        bins=[0, 0.2, 0.5, 0.8, 1.0],
        labels=['poor', 'moderate', 'good', 'excellent']
    )
    
    return df
```

**Features:**
- `ndvi_anomaly`: Deviation from average vegetation
- `ndvi_change`: Month-to-month vegetation change
- `vegetation_health`: Categorical health indicator

---

### 4. Anomaly Features

#### Climate Anomalies

```python
def create_anomaly_features(df, baseline_years=range(1981, 2011)):
    """
    Create anomaly features relative to baseline period.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with climate variables.
        baseline_years (range): Years to use for baseline climatology.
    
    Returns:
        pd.DataFrame: Dataframe with anomaly features.
    """
    # Calculate baseline climatology (monthly means)
    baseline = df[df['year'].isin(baseline_years)].groupby('month').mean()
    
    # Calculate anomalies
    for col in ['temperature', 'rainfall', 'ndvi']:
        if col in df.columns:
            df[f'{col}_anomaly'] = df.apply(
                lambda row: row[col] - baseline.loc[row['month'], col],
                axis=1
            )
    
    return df
```

**Features:**
- `temperature_anomaly`: Deviation from normal temperature
- `rainfall_anomaly`: Deviation from normal rainfall
- `ndvi_anomaly`: Deviation from normal vegetation

---

### 5. Derived Meteorological Features

#### Evapotranspiration Estimate

```python
def estimate_evapotranspiration(df):
    """
    Estimate potential evapotranspiration using simplified method.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with temperature and radiation.
    
    Returns:
        pd.DataFrame: Dataframe with ET estimate.
    """
    # Simplified Hargreaves equation
    df['pet'] = 0.0023 * df['solar_radiation'] * \
                (df['temperature'] + 17.8) * \
                (df['temperature_max'] - df['temperature_min']) ** 0.5
    
    return df
```

#### Water Balance

```python
def calculate_water_balance(df):
    """
    Calculate simple water balance.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with rainfall and ET.
    
    Returns:
        pd.DataFrame: Dataframe with water balance features.
    """
    df['water_balance'] = df['rainfall'] - df['pet']
    df['water_deficit'] = (df['water_balance'] < 0).astype(int)
    
    return df
```

**Features:**
- `pet`: Potential evapotranspiration
- `water_balance`: Rainfall minus ET
- `water_deficit`: Boolean water stress indicator

---

## Feature Selection

### Correlation Analysis

```python
def analyze_feature_correlations(df, target='rainfall'):
    """
    Analyze correlations between features and target.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with features.
        target (str): Target variable name.
    
    Returns:
        pd.Series: Correlations sorted by absolute value.
    """
    correlations = df.corr()[target].abs().sort_values(ascending=False)
    return correlations
```

### Feature Importance

```python
from sklearn.ensemble import RandomForestRegressor

def calculate_feature_importance(X, y):
    """
    Calculate feature importance using Random Forest.
    
    Parameters:
        X (pd.DataFrame): Feature matrix.
        y (pd.Series): Target variable.
    
    Returns:
        pd.DataFrame: Feature importance scores.
    """
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)
    
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'importance': rf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    return importance_df
```

---

## Feature Engineering Pipeline

### Complete Pipeline

```python
def engineer_features(df):
    """
    Complete feature engineering pipeline.
    
    Parameters:
        df (pd.DataFrame): Raw master dataset.
    
    Returns:
        pd.DataFrame: Dataframe with engineered features.
    """
    # 1. Temporal features
    df = extract_temporal_features(df)
    
    # 2. Lag features
    df = create_lag_features(
        df,
        columns=['temperature', 'rainfall', 'ndvi', 'oni', 'iod'],
        lags=[1, 2, 3, 6]
    )
    
    # 3. Rolling statistics
    df = create_rolling_features(
        df,
        columns=['temperature', 'rainfall', 'ndvi'],
        windows=[3, 6, 12]
    )
    
    # 4. Interaction features
    df = create_climate_interactions(df)
    df = create_ocean_interactions(df)
    
    # 5. Vegetation features
    df = create_vegetation_features(df)
    
    # 6. Anomaly features
    df = create_anomaly_features(df)
    
    # 7. Derived features
    df = estimate_evapotranspiration(df)
    df = calculate_water_balance(df)
    
    # 8. Drop rows with NaN from lag/rolling features
    df = df.dropna()
    
    return df
```

---

## Feature Categories Summary

| Category | Count | Examples |
|----------|-------|----------|
| Temporal | 5+ | season, quarter, is_rainy_season |
| Lag | 20+ | temperature_lag_1, rainfall_lag_3 |
| Rolling | 40+ | rainfall_rolling_mean_3, temp_rolling_std_6 |
| Interactions | 10+ | temp_precip_interaction, enso_iod_product |
| Vegetation | 5+ | ndvi_anomaly, vegetation_health |
| Anomalies | 10+ | temperature_anomaly, rainfall_anomaly |
| Derived | 5+ | pet, water_balance, drought_stress |

**Total:** 95+ engineered features

---

## Best Practices

### 1. Feature Scaling

```python
from sklearn.preprocessing import StandardScaler

def scale_features(X_train, X_test):
    """
    Scale features to zero mean and unit variance.
    
    Parameters:
        X_train (pd.DataFrame): Training features.
        X_test (pd.DataFrame): Test features.
    
    Returns:
        tuple: Scaled training and test features.
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled
```

### 2. Handle Missing Values

```python
def handle_missing_values(df, strategy='mean'):
    """
    Handle missing values in features.
    
    Parameters:
        df (pd.DataFrame): Input dataframe.
        strategy (str): Imputation strategy ('mean', 'median', 'forward_fill').
    
    Returns:
        pd.DataFrame: Dataframe with imputed values.
    """
    if strategy == 'mean':
        return df.fillna(df.mean())
    elif strategy == 'median':
        return df.fillna(df.median())
    elif strategy == 'forward_fill':
        return df.fillna(method='ffill')
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
```

### 3. Feature Documentation

Always document engineered features:

```python
FEATURE_DESCRIPTIONS = {
    'season': 'Categorical season based on Tanzania rainfall patterns',
    'temperature_lag_1': 'Temperature from previous month',
    'rainfall_rolling_mean_3': '3-month moving average of rainfall',
    'enso_iod_product': 'Interaction between ENSO and IOD indices',
    'ndvi_anomaly': 'Deviation from mean NDVI',
    'water_balance': 'Rainfall minus potential evapotranspiration'
}
```

---

## Integration with Pipeline

### Future Implementation

```python
# In run_pipeline.py (future enhancement)

from feature_engineering import engineer_features

def run_pipeline(debug=False):
    # ... existing ingestion and processing ...
    
    # Merge datasets
    master_df = merge_all()
    
    # Engineer features
    features_df = engineer_features(master_df)
    
    # Save engineered features
    features_df.to_csv('outputs/processed/features.csv', index=False)
    features_df.to_parquet('outputs/processed/features.parquet', index=False)
```

---

## Known Limitations

1. **Lag features**: Reduce available training samples
2. **Rolling features**: Require sufficient history
3. **Anomaly features**: Need long baseline period
4. **Missing data**: Lag/rolling features create NaN values
5. **Computational cost**: Many features increase processing time

---

## References

- Tanzania Meteorological Authority seasonal patterns
- ENSO/IOD climate impact studies for East Africa
- Standard meteorological feature engineering practices
- Time series forecasting best practices
