# Design: Data Augmentation via Spatial-Temporal Expansion

## 1. Executive Summary

This design document outlines the technical approach to expand the Tanzania Climate Prediction training dataset from 191 samples to 1,560-2,496 samples through a hybrid spatial-temporal expansion strategy. The approach combines multi-location data collection with historical temporal extension to achieve a healthy feature-to-sample ratio of 20:1 or better.

**Strategy**: Collect data from 5-8 representative locations across Tanzania for the period 2000-2025 (312 months), resulting in 1,560-2,496 total samples.

## 2. Problem Statement

### 2.1 Current Limitations

**Insufficient Training Data**:
- Current: 191 months (2010-2025, single location)
- Training samples: 133 (after 70/15/15 split)
- Features: 35-79 (after optimization)
- Feature-to-sample ratio: 1.68:1 to 3.8:1 (unhealthy)

**Recommended Standards**:
- Minimum ratio: 10:1 (requires 350-790 samples)
- Target ratio: 15:1 (requires 525-1,185 samples)
- Optimal ratio: 20:1+ (requires 700-1,580 samples)

**Impact of Insufficient Data**:
- Overfitting risk despite regularization
- Unreliable confidence intervals
- Poor spatial/temporal generalization
- Not scientifically publishable
- Limited stakeholder trust

### 2.2 Design Goals

1. **Sample Size**: Achieve 1,560+ samples (8.2× increase)
2. **Ratio**: Achieve 20:1+ feature-to-sample ratio
3. **Generalization**: Validate spatial generalization across locations
4. **Performance**: Maintain or improve model accuracy
5. **Scientific Rigor**: Create statistically sound, publishable model
6. **Sustainability**: Enable ongoing monthly data collection

## 3. Solution Architecture

### 3.1 Hybrid Spatial-Temporal Strategy

```
Current:
┌─────────────────────────────────────┐
│ 1 Location × 191 Months = 191 Samples │
│ Feature-to-Sample Ratio: 2.5:1 ❌    │
└─────────────────────────────────────┘

Phase 1 (Recommended Minimum):
┌─────────────────────────────────────────────┐
│ 5 Locations × 312 Months = 1,560 Samples   │
│ Feature-to-Sample Ratio: 20.8:1 ✓          │
│ Timeline: 2-3 months                        │
└─────────────────────────────────────────────┘

Phase 2 (Optimal):
┌─────────────────────────────────────────────┐
│ 8 Locations × 312 Months = 2,496 Samples   │
│ Feature-to-Sample Ratio: 33.3:1 ✓          │
│ Timeline: 3-4 months                        │
└─────────────────────────────────────────────┘
```

### 3.2 Location Selection Criteria

**Geographic Diversity**:
- Represent different climate zones (coastal, highland, semi-arid, lake)
- Span latitude and longitude across Tanzania
- Include agriculturally important regions
- Minimize spatial autocorrelation (≥ 100-200 km apart)

**Data Availability**:
- Verify all 5 data sources available for 2000-2025
- Check data quality and completeness
- Ensure consistent temporal coverage

**Recommended Locations (Phase 1 - 5 Locations)**:

1. **Dodoma** (-6.1630°, 35.7516°)
   - Central Tanzania, semi-arid
   - Capital city, agricultural importance
   - Existing baseline location

2. **Dar es Salaam** (-6.7924°, 39.2083°)
   - Coastal zone, high rainfall
   - Largest city, economic importance
   - Different climate regime from central

3. **Arusha** (-3.3869°, 36.6830°)
   - Northern highlands
   - Major agricultural area (coffee, horticulture)
   - Highland climate, cooler temperatures

4. **Mwanza** (-2.5164°, 32.9175°)
   - Lake Victoria region
   - Lake influence on climate
   - Important for fisheries and agriculture

5. **Mbeya** (-8.9094°, 33.4606°)
   - Southern highlands
   - High elevation, unique microclimate
   - Tea and coffee production

**Additional Locations (Phase 2 - expand to 8)**:

6. **Tabora** (-5.0167°, 32.8000°) - Western plateau
7. **Mtwara** (-10.2762°, 40.1833°) - Southern coastal
8. **Kigoma** (-4.8778°, 29.6267°) - Western, Lake Tanganyika

### 3.3 Temporal Expansion Strategy

**Historical Extension**:
- Current: 2010-2025 (191 months)
- Extended: 2000-2025 (312 months)
- Additional: 121 months (+63% temporal data)
- Limitation: NDVI (MODIS) only available from 2000

**Justification for 2000 Start**:
- MODIS NDVI availability (limiting factor)
- 25-year period captures climate variability
- Includes multiple El Niño and La Niña events
- Balances data quantity with climate non-stationarity

## 4. Technical Architecture

### 4.1 Data Collection Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Multi-Location Data Collection          │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Location 1  │  │  Location 2  │  │  Location N  │
│   Dodoma     │  │ Dar es Salaam│  │   Mbeya...   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        ├─────────┬────────┴──────────┬───────┤
        ▼         ▼        ▼          ▼       ▼
    CHIRPS    NASA POWER  ERA5     NDVI    Ocean Indices
        │         │        │          │       │
        └─────────┴────────┴──────────┴───────┘
                           │
                ┌──────────▼──────────┐
                │  Location-Tagged    │
                │   Raw Data Store    │
                └─────────────────────┘
                           │
                ┌──────────▼──────────┐
                │    Processing &     │
                │ Feature Engineering │
                └─────────────────────┘
                           │
                ┌──────────▼──────────┐
                │   Multi-Location    │
                │  Master Dataset     │
                │  (1,560-2,496 rows) │
                └─────────────────────┘
```

### 4.2 Data Processing Pipeline

**Step 1: Location-Specific Ingestion**
```python
def collect_multi_location_data(locations, start_date, end_date):
    """
    Collect data for multiple locations.
    
    Args:
        locations: Dict of {name: {lat, lon}}
        start_date: "2000-01"
        end_date: "2025-11"
    
    Returns:
        Dict of {location_name: {source: dataframe}}
    """
    all_data = {}
    
    for location_name, coords in locations.items():
        logger.info(f"Collecting data for {location_name}")
        
        # Collect from each source
        chirps = fetch_chirps(coords['lat'], coords['lon'], start_date, end_date)
        nasa = fetch_nasa_power(coords['lat'], coords['lon'], start_date, end_date)
        era5 = fetch_era5(coords['lat'], coords['lon'], start_date, end_date)
        ndvi = fetch_ndvi(coords['lat'], coords['lon'], start_date, end_date)
        ocean = fetch_ocean_indices(start_date, end_date)  # Same for all locations
        
        # Tag with location
        for df in [chirps, nasa, era5, ndvi, ocean]:
            df['location'] = location_name
            df['latitude'] = coords['lat']
            df['longitude'] = coords['lon']
        
        all_data[location_name] = {
            'chirps': chirps,
            'nasa_power': nasa,
            'era5': era5,
            'ndvi': ndvi,
            'ocean_indices': ocean
        }
    
    return all_data
```

**Step 2: Unified Processing**
```python
def process_multi_location_data(all_location_data):
    """
    Process data from all locations using consistent pipeline.
    
    Returns:
        Combined DataFrame with all locations
    """
    processed_datasets = []
    
    for location_name, source_data in all_location_data.items():
        # Apply existing processing pipeline
        processed_chirps = process_chirps(source_data['chirps'])
        processed_nasa = process_nasa_power(source_data['nasa_power'])
        processed_era5 = process_era5(source_data['era5'])
        processed_ndvi = process_ndvi(source_data['ndvi'])
        processed_ocean = process_ocean_indices(source_data['ocean_indices'])
        
        # Merge for this location
        location_merged = merge_processed(
            processed_chirps,
            processed_nasa,
            processed_era5,
            processed_ndvi,
            processed_ocean
        )
        
        processed_datasets.append(location_merged)
    
    # Combine all locations
    combined = pd.concat(processed_datasets, axis=0, ignore_index=True)
    
    return combined
```

**Step 3: Location-Aware Feature Engineering**
```python
def engineer_features_multi_location(combined_data):
    """
    Apply feature engineering with location awareness.
    """
    # Add location encoding
    combined_data = pd.get_dummies(combined_data, columns=['location'], prefix='loc')
    
    # Apply temporal features (lags, rolling windows)
    # IMPORTANT: Group by location to prevent leakage across locations
    for location in combined_data['location'].unique():
        location_mask = combined_data['location'] == location
        location_data = combined_data[location_mask]
        
        # Apply lag features within location
        location_data = add_lag_features(location_data, lags=[1, 3, 6])
        location_data = add_rolling_features(location_data, windows=[3])
        
        combined_data.loc[location_mask] = location_data
    
    # Add interaction features
    combined_data = add_interaction_features(combined_data)
    
    return combined_data
```

### 4.3 Train/Val/Test Split Strategy

**Stratified Splitting by Location**:
```python
def stratified_split_by_location(data, train_size=0.70, val_size=0.15, test_size=0.15):
    """
    Split data ensuring each location appears in all sets.
    """
    train_dfs = []
    val_dfs = []
    test_dfs = []
    
    for location in data['location'].unique():
        location_data = data[data['location'] == location]
        
        # Temporal split within location (maintain chronological order)
        n = len(location_data)
        train_end = int(n * train_size)
        val_end = int(n * (train_size + val_size))
        
        location_data = location_data.sort_values('date')
        
        train_dfs.append(location_data.iloc[:train_end])
        val_dfs.append(location_data.iloc[train_end:val_end])
        test_dfs.append(location_data.iloc[val_end:])
    
    train = pd.concat(train_dfs, ignore_index=True)
    val = pd.concat(val_dfs, ignore_index=True)
    test = pd.concat(test_dfs, ignore_index=True)
    
    return train, val, test
```

**Expected Split Sizes (5 locations × 312 months = 1,560)**:
- Training: 1,092 samples (70%)
- Validation: 234 samples (15%)
- Test: 234 samples (15%)

**Feature-to-Sample Ratio** (with 75 features):
- Current: 133 train samples / 75 features = 1.77:1 ❌
- After expansion: 1,092 train samples / 75 features = 14.6:1 ✓

### 4.4 Model Training Strategy

**Location-Aware Cross-Validation**:
```python
def location_aware_cv(data, model, n_folds=5):
    """
    K-fold cross-validation with location stratification.
    """
    locations = data['location'].unique()
    cv_scores = []
    
    for fold in range(n_folds):
        # Rotate which locations are in validation
        val_locations = locations[fold::n_folds]
        train_data = data[~data['location'].isin(val_locations)]
        val_data = data[data['location'].isin(val_locations)]
        
        model.fit(train_data)
        score = model.evaluate(val_data)
        cv_scores.append(score)
    
    return np.mean(cv_scores), np.std(cv_scores)
```

**Leave-One-Location-Out Validation** (ultimate spatial generalization test):
```python
def leave_one_location_out(data, model):
    """
    Train on N-1 locations, test on held-out location.
    """
    locations = data['location'].unique()
    results = {}
    
    for holdout_location in locations:
        train_data = data[data['location'] != holdout_location]
        test_data = data[data['location'] == holdout_location]
        
        model.fit(train_data)
        score = model.evaluate(test_data)
        
        results[holdout_location] = score
    
    return results
```

## 5. Data Storage Design

### 5.1 File Organization

```
outputs/
└── multi_location_data/
    ├── raw/
    │   ├── dodoma/
    │   │   ├── chirps_2000_2025.csv
    │   │   ├── nasa_power_2000_2025.csv
    │   │   ├── era5_2000_2025.csv
    │   │   ├── ndvi_2000_2025.csv
    │   │   └── ocean_indices_2000_2025.csv
    │   ├── dar_es_salaam/
    │   └── ... (other locations)
    ├── processed/
    │   ├── dodoma_processed.parquet
    │   ├── dar_es_salaam_processed.parquet
    │   └── ... (other locations)
    └── combined/
        ├── master_dataset_multi_location.parquet
        ├── features_train_multi_location.parquet
        ├── features_val_multi_location.parquet
        └── features_test_multi_location.parquet
```

### 5.2 Data Schema

**Multi-Location Master Dataset**:
```python
{
    'date': datetime,           # Monthly date
    'location': str,            # Location name
    'latitude': float,          # Location coordinates
    'longitude': float,
    'elevation': float,         # Optional
    
    # CHIRPS features (processed)
    'rainfall_mm': float,
    'spi_3month': float,
    'consecutive_dry_days': int,
    'flood_trigger': bool,
    'drought_trigger': bool,
    
    # NASA POWER features
    'temperature_2m': float,
    'solar_radiation': float,
    'heat_stress_days': int,
    
    # ERA5 features
    'wind_speed': float,
    'relative_humidity': float,
    'pressure': float,
    
    # NDVI features
    'ndvi': float,
    'vci': float,
    'crop_stress_trigger': bool,
    
    # Ocean Indices (same for all locations)
    'nino34': float,
    'iod': float,
    
    # Engineered features (lags, rolling, interactions)
    'rainfall_lag_1': float,
    'rainfall_lag_3': float,
    'rainfall_rolling_3month': float,
    'enso_x_rainfall': float,
    # ... (70+ total features)
    
    # Location encoding (one-hot)
    'loc_dodoma': int,
    'loc_dar_es_salaam': int,
    # ... (one per location)
}
```

## 6. Validation Strategy

### 6.1 Multi-Level Validation

**Level 1: Data Quality Validation**
- Completeness by location
- Temporal consistency within locations
- Spatial consistency across locations
- Outlier detection and flagging

**Level 2: Model Performance Validation**
- Overall test R² ≥ 0.85
- Per-location test R² tracking
- Train-validation gap < 5%
- Cross-validation std < 0.10

**Level 3: Generalization Validation**
- Leave-one-location-out R² ≥ 0.75
- Held-out temporal period validation
- Prediction interval coverage 90-98%

**Level 4: Comparison Validation**
- Multi-location vs single-location baseline
- Feature-to-sample ratio improvement
- Confidence interval narrowing
- Overfitting reduction

### 6.2 Success Metrics

| Metric | Current | Target | Validation Method |
|--------|---------|--------|-------------------|
| Samples | 191 | 1,560+ | Count |
| Feature-to-Sample Ratio | 2.5:1 | 20:1+ | Calculate |
| Test R² | 0.95 | ≥ 0.85 | Held-out test |
| Train-Val Gap | Variable | < 5% | Compare metrics |
| Held-Out Location R² | N/A | ≥ 0.75 | Leave-one-out CV |
| CV Std | N/A | < 0.10 | K-fold CV |

## 7. Implementation Phases

### Phase 1: Minimum Viable (5 Locations, 8 weeks)

**Weeks 1-2: Planning**
- Finalize 5 locations
- Verify data availability
- Set up infrastructure

**Weeks 3-6: Data Collection**
- Collect historical data (2000-2025)
- Validate data quality
- Process and merge

**Weeks 7-8: Model Development**
- Feature engineering
- Train multi-location model
- Initial validation

**Deliverables**:
- 1,560 sample dataset
- Multi-location trained model
- Validation report

### Phase 2: Optimal (8 Locations, additional 4 weeks)

**Weeks 9-10: Expansion**
- Add 3 more locations
- Collect and process data

**Weeks 11-12: Final Model**
- Retrain with 2,496 samples
- Comprehensive validation
- Production deployment

**Deliverables**:
- 2,496 sample dataset
- Production-ready model
- Complete documentation

## 8. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Historical data quality issues | Medium | Medium | Rigorous quality checks, exclude problematic periods |
| Spatial autocorrelation | Low | Low | Select diverse locations ≥100km apart |
| Computational limitations | Medium | Low | Optimize processing, use cloud if needed |
| Location-specific overfitting | Medium | Medium | Leave-one-out validation, monitor per-location metrics |
| Data collection time | Low | Medium | Parallel collection, caching, progress tracking |

## 9. Monitoring and Maintenance

### 9.1 Ongoing Data Collection

**Monthly Updates**:
- Collect new month's data for all locations
- Append to master dataset
- Growth rate: 5 locations × 12 months/year = 60 samples/year

**Quarterly Retraining**:
- Retrain model with updated data
- Validate performance
- Update production model

### 9.2 Performance Monitoring

**Track Over Time**:
- Per-location model accuracy
- Spatial generalization metrics
- Temporal trends in performance
- Feature importance evolution

## 10. Expected Outcomes

### 10.1 Quantitative Improvements

- **Sample size**: 191 → 1,560 (8.2× increase)
- **Feature-to-sample ratio**: 2.5:1 → 20.8:1 (8.3× improvement)
- **Confidence intervals**: Narrower, more reliable
- **Generalization**: Validated across geography

### 10.2 Qualitative Improvements

- **Scientific rigor**: Publishable methodology
- **Stakeholder trust**: Robust validation
- **Operational value**: Spatial applicability
- **Future-proof**: Sustainable data growth

## 11. Conclusion

The hybrid spatial-temporal expansion strategy provides a practical, achievable path to address the fundamental sample size limitation. By collecting data from 5-8 locations across Tanzania for the period 2000-2025, we can increase the training dataset by 8-13× and achieve a healthy feature-to-sample ratio of 20-33:1, resulting in a scientifically sound, production-ready model.
