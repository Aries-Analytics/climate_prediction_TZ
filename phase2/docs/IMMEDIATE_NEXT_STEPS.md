# Immediate Next Steps: Week 1 Action Plan

## 🎯 This Week's Goal
Transform Phase 2 infrastructure into Phase 3 by implementing real data processing and beginning feature engineering for insurance triggers.

---

## Day 1-2: Implement Real Processing Modules

### Task 1.1: NASA POWER Processing
**File:** `modules/processing/process_nasa_power.py`

**Current State:** Returns placeholder data  
**Target State:** Real transformations with climate indices

**Implementation:**
```python
def process(data):
    """
    Process NASA POWER data with real transformations.
    
    Transformations:
    1. Column standardization
    2. Unit conversions
    3. Derived climate indices
    4. Quality filtering
    """
    df = data.copy()
    
    # Standardize column names
    df = df.rename(columns={
        't2m': 'temp_mean_c',
        't2m_max': 'temp_max_c',
        't2m_min': 'temp_min_c',
        'prectotcorr': 'precip_mm',
        'rh2m': 'humidity_pct',
        'allsky_sfc_sw_dwn': 'solar_rad_wm2'
    })
    
    # Calculate derived indices
    df['temp_range_c'] = df['temp_max_c'] - df['temp_min_c']
    df['heat_index'] = calculate_heat_index(df['temp_mean_c'], df['humidity_pct'])
    df['growing_degree_days'] = calculate_gdd(df['temp_mean_c'], base_temp=10)
    
    # Quality filters
    df = df[df['temp_mean_c'].between(-10, 50)]  # Reasonable for Tanzania
    df = df[df['precip_mm'] >= 0]  # No negative rainfall
    
    # Validate and save
    validate_dataframe(df, expected_columns=['year', 'month', 'temp_mean_c'])
    output_path = get_output_path("processed", "nasa_power_processed.csv")
    df.to_csv(output_path, index=False)
    
    return df
```

**Deliverable:** Functional NASA POWER processing with 10+ features

---

### Task 1.2: ERA5 Processing
**File:** `modules/processing/process_era5.py`

**Implementation:**
```python
def process(data):
    """Process ERA5 data with unit conversions and derived features."""
    df = data.copy()
    
    # Unit conversions
    df['temp_2m_c'] = df['temp_2m'] - 273.15  # Kelvin to Celsius
    df['dewpoint_2m_c'] = df['dewpoint_2m'] - 273.15
    df['precip_mm'] = df['total_precip'] * 1000  # meters to mm
    df['pressure_hpa'] = df['surface_pressure'] / 100  # Pa to hPa
    
    # Calculate wind speed
    df['wind_speed_ms'] = np.sqrt(df['wind_u_10m']**2 + df['wind_v_10m']**2)
    
    # Calculate relative humidity from temp and dewpoint
    df['rel_humidity_pct'] = calculate_relative_humidity(
        df['temp_2m_c'], 
        df['dewpoint_2m_c']
    )
    
    # Evapotranspiration estimate (Penman-Monteith simplified)
    df['pet_mm'] = calculate_pet(
        df['temp_2m_c'],
        df['wind_speed_ms'],
        df['rel_humidity_pct']
    )
    
    return df
```

---

### Task 1.3: CHIRPS Processing
**File:** `modules/processing/process_chirps.py`

**Implementation:**
```python
def process(data):
    """Process CHIRPS rainfall data with drought indicators."""
    df = data.copy()
    
    # Calculate rolling statistics
    df['precip_7day'] = df.groupby('year')['rainfall_mm'].rolling(7).sum().reset_index(0, drop=True)
    df['precip_30day'] = df.groupby('year')['rainfall_mm'].rolling(30).sum().reset_index(0, drop=True)
    
    # Drought indicators
    df['consecutive_dry_days'] = calculate_consecutive_dry_days(df['rainfall_mm'])
    df['spi_30day'] = calculate_spi(df['precip_30day'])  # Standardized Precipitation Index
    
    # Flood indicators
    df['heavy_rain_event'] = (df['rainfall_mm'] > 50).astype(int)  # >50mm/day
    df['extreme_rain_event'] = (df['rainfall_mm'] > 100).astype(int)  # >100mm/day
    
    return df
```

---

## Day 3-4: Feature Engineering Pipeline

### Task 2.1: Create Feature Engineering Module
**File:** `modules/feature_engineering/engineer_features.py`

**Implementation:**
```python
def engineer_features(master_df):
    """
    Complete feature engineering pipeline for insurance triggers.
    
    Features created:
    - Temporal: lags, rolling stats, seasonal
    - Risk: drought, flood, heat stress indicators
    - Interactions: ENSO × season, temp × humidity
    - Anomalies: deviations from climatology
    """
    df = master_df.copy()
    
    # 1. Temporal features
    df = add_temporal_features(df)  # season, quarter, day_of_year
    df = add_lag_features(df, ['temp_mean_c', 'precip_mm'], lags=[1, 3, 7, 14, 30])
    df = add_rolling_features(df, ['temp_mean_c', 'precip_mm'], windows=[7, 14, 30])
    
    # 2. Risk indicators
    df = add_drought_indicators(df)  # consecutive_dry_days, spi, water_deficit
    df = add_flood_indicators(df)  # heavy_rain_days, cumulative_excess
    df = add_heat_stress_indicators(df)  # heat_wave_days, extreme_temp_days
    
    # 3. Interactions
    df = add_climate_interactions(df)  # temp × humidity, precip × evap
    df = add_enso_interactions(df)  # oni × season, iod × region
    
    # 4. Anomalies
    df = add_anomaly_features(df, baseline_years=range(1981, 2011))
    
    return df
```

---

### Task 2.2: Insurance-Specific Features
**File:** `modules/feature_engineering/insurance_features.py`

**Implementation:**
```python
def calculate_insurance_triggers(df):
    """
    Calculate insurance trigger indicators.
    
    Returns DataFrame with trigger probabilities and severity.
    """
    triggers = pd.DataFrame(index=df.index)
    
    # Drought trigger
    triggers['drought_trigger'] = (
        (df['consecutive_dry_days'] > 21) &  # 3 weeks no rain
        (df['precip_30day'] < 25)  # <25mm in 30 days
    ).astype(int)
    triggers['drought_severity'] = calculate_drought_severity(df)
    
    # Flood trigger
    triggers['flood_trigger'] = (
        (df['precip_7day'] > 150) |  # >150mm in 7 days
        (df['rainfall_mm'] > 100)  # >100mm in 1 day
    ).astype(int)
    triggers['flood_severity'] = calculate_flood_severity(df)
    
    # Heat stress trigger
    triggers['heat_trigger'] = (
        (df['temp_max_c'] > 35) &  # >35°C
        (df['heat_index'] > 40)  # Heat index >40
    ).astype(int)
    triggers['heat_severity'] = calculate_heat_severity(df)
    
    # Combined multi-peril trigger
    triggers['any_trigger'] = (
        triggers['drought_trigger'] | 
        triggers['flood_trigger'] | 
        triggers['heat_trigger']
    ).astype(int)
    
    return triggers
```

---

## Day 5: Model Enhancement Setup

### Task 3.1: Model Comparison Framework
**File:** `model_pipeline/model_comparison.py`

**Implementation:**
```python
class ModelComparison:
    """Framework for comparing multiple models."""
    
    def __init__(self):
        self.models = {}
        self.results = {}
    
    def add_model(self, name, model, params=None):
        """Add a model to comparison."""
        self.models[name] = {
            'model': model,
            'params': params or {}
        }
    
    def train_all(self, X_train, y_train):
        """Train all models."""
        for name, config in self.models.items():
            print(f"Training {name}...")
            model = config['model'](**config['params'])
            model.fit(X_train, y_train)
            self.models[name]['trained'] = model
    
    def evaluate_all(self, X_test, y_test):
        """Evaluate all models."""
        for name, config in self.models.items():
            model = config['trained']
            y_pred = model.predict(X_test)
            
            self.results[name] = {
                'mae': mean_absolute_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred),
                'mape': mean_absolute_percentage_error(y_test, y_pred)
            }
    
    def get_best_model(self, metric='r2'):
        """Get best performing model."""
        best_name = max(self.results, key=lambda x: self.results[x][metric])
        return best_name, self.models[best_name]['trained']
```

---

### Task 3.2: Add New Models
**File:** `model_pipeline/advanced_models.py`

**Models to implement:**
1. **XGBoost** - Gradient boosting for tabular data
2. **LightGBM** - Fast gradient boosting
3. **LSTM** - Time series neural network
4. **Prophet** - Facebook's time series forecasting
5. **Quantile Regression** - For uncertainty bounds

---

## Day 6-7: Testing & Validation

### Task 4.1: Integration Testing
**File:** `tests/test_phase3_integration.py`

**Tests:**
- End-to-end pipeline with real processing
- Feature engineering output validation
- Model training and prediction
- Insurance trigger calculation

### Task 4.2: Performance Benchmarking
**File:** `tests/benchmark_models.py`

**Benchmarks:**
- Compare Phase 2 vs Phase 3 accuracy
- Measure processing time improvements
- Validate feature importance
- Test on holdout data (2023)

---

## Week 1 Deliverables Checklist

- [ ] Real processing modules for all 5 data sources
- [ ] Feature engineering pipeline (50+ features)
- [ ] Insurance trigger calculation module
- [ ] Model comparison framework
- [ ] 3+ new model implementations
- [ ] Integration tests passing
- [ ] Performance benchmark report
- [ ] Updated documentation

---

## Success Criteria

### Technical
- ✅ All processing modules return real data (not placeholders)
- ✅ Feature engineering creates 50+ features
- ✅ At least one model achieves R² > 0.80
- ✅ Insurance triggers calculated correctly
- ✅ All tests passing

### Business
- ✅ Clear path to R² > 0.85 identified
- ✅ Insurance trigger logic validated with domain expert
- ✅ Computational performance acceptable (<5 min for full pipeline)

---

## Blockers & Risks

### Potential Blockers
1. **Data quality issues** → Mitigation: Robust validation, multiple sources
2. **Computational resources** → Mitigation: Cloud computing, optimization
3. **Domain knowledge gaps** → Mitigation: Consult insurance/agriculture experts

### Risk Management
- Daily standup to identify issues early
- Parallel work streams to avoid dependencies
- Fallback to simpler approaches if needed

---

## Resources Needed

### Technical
- Python packages: `xgboost`, `lightgbm`, `prophet`, `tensorflow`
- Cloud compute: AWS/GCP for model training
- Storage: ~10GB for processed data

### Human
- Data scientist: Feature engineering, model development
- Domain expert: Insurance trigger validation (2-3 hours)
- Code reviewer: Quality assurance

---

## Communication Plan

### Daily
- Morning: Team standup (15 min)
- Evening: Progress update in Slack/email

### Weekly
- Friday: Demo of week's progress
- Friday: Planning for next week

### Stakeholders
- Monday: Week 1 kickoff presentation
- Friday: Week 1 results presentation

---

## Next Week Preview (Week 2)

Focus areas:
1. Model optimization and hyperparameter tuning
2. Uncertainty quantification implementation
3. Regional model development
4. Begin trigger system architecture

---

## Questions? Contact

- **Technical Lead**: [Your Name]
- **Project Manager**: [PM Name]
- **Insurance Expert**: [Expert Name]
