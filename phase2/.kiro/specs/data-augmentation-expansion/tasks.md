# Implementation Plan: Data Augmentation via Spatial-Temporal Expansion

## Overview

Expand training dataset from 191 samples to 1,560-2,496 samples through multi-location data collection across Tanzania (5-8 locations) combined with historical temporal extension (2000-2025).

**Target**: Achieve 20:1+ feature-to-sample ratio for scientifically sound, publication-ready model.

---

## Phase 1: Planning and Preparation (Weeks 1-2)

### 1. Location Selection and Verification

- [ ] 1.1 Select 5 representative locations for Phase 1
  - Document location names, coordinates, elevation, climate zone
  - Ensure geographic diversity (coastal, highland, semi-arid, lake)
  - Minimum 100-200 km separation to reduce spatial autocorrelation
  - _Requirements: FR-2.1.1, FR-2.1.2_

- [ ] 1.2 Verify CHIRPS data availability for all 5 locations (2000-2025)
  - Test API/download for each location
  - Document any data gaps or quality issues
  - Estimate download size and time
  - _Requirements: FR-2.2.1_

- [ ] 1.3 Verify NASA POWER data availability for all 5 locations (2000-2025)
  - Test API for each location
  - Document any missing variables or time periods
  - _Requirements: FR-2.2.2_

- [ ] 1.4 Verify ERA5 data availability for all 5 locations (2000-2025)
  - Test CDS API for each location
  - Check authentication and quota limits
  - _Requirements: FR-2.2.3_

- [ ] 1.5 Verify NDVI (MODIS) data availability for all 5 locations (2000-2025)
  - Confirm MODIS limitation (2000 onwards)
  - Test Google Earth Engine or AppEEARS access
  - Document spatial resolution and temporal frequency
  - _Requirements: FR-2.2.4_

- [ ] 1.6 Verify Ocean Indices availability (2000-2025)
  - Same for all locations (global indices)
  - Confirm monthly resolution
  - _Requirements: FR-2.2.5_

- [ ] 1.7 Create data availability report
  - Summarize findings for all locations and sources
  - Identify any gaps or quality concerns
  - Flag any locations that should be excluded
  - _Requirements: FR-2.5.1, FR-2.5.3_

### 2. Infrastructure Setup

- [ ] 2.1 Provision storage for expanded dataset
  - Estimate size: 191 months × 5 locations × 5 sources ≈ 5-10 GB
  - Set up directory structure for multi-location data
  - Configure Parquet storage for efficient compression
  - _Requirements: TR-3.1.1, TR-3.1.2_

- [ ] 2.2 Create location configuration file
  - Define `locations_config.yaml` with coordinates and metadata
  - Include validation rules for locations
  - _Requirements: FR-2.1.4_

```yaml
# locations_config.yaml example
locations:
  dodoma:
    latitude: -6.1630
    longitude: 35.7516
    elevation: 1120
    climate_zone: "semi-arid"
    region: "central"
  dar_es_salaam:
    latitude: -6.7924
    longitude: 39.2083
    elevation: 14
    climate_zone: "coastal"
    region: "eastern"
  # ... other locations
```

- [ ] 2.3 Set up progress tracking and logging
  - Create logging system for multi-location collection
  - Implement progress bars for long downloads
  - Set up error handling and retry logic
  - _Requirements: TR-3.1.5_

---

## Phase 2: Data Collection (Weeks 3-6)

### 3. Extend Ingestion Modules for Multi-Location

- [ ] 3.1 Modify CHIRPS ingestion to accept location parameters
  - Update `modules/ingestion/chirps_ingestion.py`
  - Add lat/lon parameters to fetch functions
  - Tag data with location identifier
  - Test with 1 location before scaling
  - _Requirements: FR-2.1.5_

- [ ] 3.2 Modify NASA POWER ingestion for multi-location
  - Update `modules/ingestion/nasa_power_ingestion.py`
  - Add lat/lon parameters
  - Tag data with location identifier
  - _Requirements: FR-2.1.6_

- [ ] 3.3 Modify ERA5 ingestion for multi-location
  - Update `modules/ingestion/era5_ingestion.py`
  - Add lat/lon parameters
  - Handle CDS API rate limits gracefully
  - _Requirements: FR-2.1.7_

- [ ] 3.4 Modify NDVI ingestion for multi-location
  - Update `modules/ingestion/ndvi_ingestion.py`
  - Add lat/lon parameters
  - Verify MODIS temporal coverage (2000-2025)
  - _Requirements: FR-2.1.8_

- [ ] 3.5 Confirm Ocean Indices remain location-independent
  - No changes needed (same for all locations)
  - Add location tag during merging
  - _Requirements: FR-2.1.9_

### 4. Implement Multi-Location Data Collection Orchestrator

- [ ] 4.1 Create batch collection script
  - Create `scripts/collect_multi_location_data.py`
  - Load locations from config file
  - Iterate through all locations
  - Implement parallel collection where possible
  - _Requirements: FR-2.1.10_

- [ ] 4.2 Implement caching to avoid re-downloading
  - Check if location data already exists
  - Skip download if cached and valid
  - _Requirements: TR-3.1.6_

- [ ] 4.3 Add comprehensive error handling
  - Continue if single location fails
  - Log failures and retry with exponential backoff
  - Generate error report at end
  - _Requirements: FR-2.2.9_

### 5. Collect Historical Data (2000-2025)

- [ ] 5.1 Run data collection for Location 1 (Dodoma - baseline)
  - Collect all 5 sources for 2000-2025
  - Validate data quality
  - Fix any issues before scaling
  - _Requirements: FR-2.2.1-FR-2.2.5_

- [ ] 5.2 Run data collection for remaining 4 locations
  - Dar es Salaam
  - Arusha
  - Mwanza
  - Mbeya
  - Monitor progress and handle any failures
  - _Requirements: FR-2.2.1-FR-2.2.5_

- [ ] 5.3 Validate data completeness for all locations
  - Check all 5 locations have all 5 sources
  - Check temporal coverage (2000-2025)
  - Document any gaps or missing data
  - _Requirements: TR-3.2.2, TR-3.2.5_

---

## Phase 3: Data Processing (Weeks 7-8)

### 6. Data Quality Validation

- [ ] 6.1 Implement historical data quality checks
  - Compare 2000-2009 statistics to 2010-2025
  - Flag systematic biases or anomalies
  - Identify outliers beyond 5 standard deviations
  - _Requirements: FR-2.2.6, FR-2.2.8_

- [ ] 6.2 Validate spatial consistency across locations
  - Check rainfall distributions are reasonable
  - Verify temperature gradients (coastal vs highland)
  - Flag any suspicious location-specific patterns
  - _Requirements: TR-3.2.3_

- [ ] 6.3 Generate data quality report
  - Completeness by location and source
  - Temporal consistency metrics
  - Spatial consistency metrics
  - Outlier summary
  - _Requirements: FR-2.5.3, TR-3.2.4, TR-3.2.6_

### 7. Multi-Location Data Processing

- [ ] 7.1 Update processing modules to preserve location tags
  - Modify `modules/processing/process_chirps.py`
  - Modify `modules/processing/process_nasa_power.py`
  - Modify `modules/processing/process_era5.py`
  - Modify `modules/processing/process_ndvi.py`
  - Modify `modules/processing/process_ocean_indices.py`
  - Ensure location field propagates through processing
  - _Requirements: FR-2.3.2_

- [ ] 7.2 Create location-specific processing orchestrator
  - Process data for each location independently
  - Apply consistent feature engineering pipeline
  - Store processed data with location tags
  - _Requirements: FR-2.1.12_

- [ ] 7.3 Process all 5 locations through pipeline
  - Run processing for Dodoma
  - Run processing for Dar es Salaam
  - Run processing for Arusha
  - Run processing for Mwanza
  - Run processing for Mbeya
  - _Requirements: FR-2.1.12_

### 8. Multi-Location Data Merging

- [ ] 8.1 Update merge module for multi-location support
  - Modify `modules/processing/merge_processed.py`
  - Combine data from all locations
  - Preserve location identifiers
  - Sort by date and location
  - _Requirements: FR-2.3.1, FR-2.3.2_

- [ ] 8.2 Create combined master dataset
  - Merge all 5 locations into single DataFrame
  - Expected size: 5 locations × 312 months = 1,560 rows
  - Verify row count matches expectation
  - Save as `master_dataset_multi_location.parquet`
  - _Requirements: FR-2.3.5_

- [ ] 8.3 Validate merged dataset structure
  - Check all locations present
  - Check temporal coverage for each location
  - Verify feature consistency across locations
  - _Requirements: FR-2.3.9_

---

## Phase 4: Feature Engineering (Week 8)

### 9. Location-Aware Feature Engineering

- [ ] 9.1 Add location encoding features
  - Create one-hot encoding for location variable
  - Add location embedding as alternative (optional)
  - Document which approach is used
  - _Requirements: FR-2.3.7_

- [ ] 9.2 Implement location-grouped temporal features
  - Modify `preprocessing/preprocess.py`
  - Group by location before creating lag features
  - Prevent temporal leakage across locations
  - Implement lags: [1, 3, 6] months
  - _Requirements: FR-2.3.8_

- [ ] 9.3 Implement location-grouped rolling features
  - Group by location before rolling windows
  - Implement rolling windows: [3] months
  - Prevent leakage across location boundaries
  - _Requirements: FR-2.3.8_

- [ ] 9.4 Add interaction features
  - ENSO × Rainfall
  - IOD × NDVI
  - Temperature × NDVI
  - Select top 5 interactions based on mutual information
  - _Requirements: FR-2.3.7_

- [ ] 9.5 Validate feature distributions across locations
  - Check feature means and std devs by location
  - Identify location-specific outliers
  - Document feature statistics
  - _Requirements: FR-2.3.9_

### 10. Feature Selection (Optional - if using reduced features)

- [ ] 10.1 Apply feature selection to expanded dataset
  - Use correlation-based selection
  - Use mutual information selection
  - Ensure source diversity (all 5 sources represented)
  - Target: 50-100 features
  - _Requirements: Model performance requirements_

- [ ] 10.2 Document selected features
  - List final feature set
  - Document selection criteria
  - Show source distribution
  - _Requirements: FR-2.5.7_

---

## Phase 5: Model Training and Validation (Weeks 9-12)

### 11. Train/Val/Test Split Strategy

- [ ] 11.1 Implement stratified split by location
  - Create `utils/multi_location_split.py`
  - Split within each location (70/15/15)
  - Combine splits across locations
  - Maintain temporal ordering within locations
  - _Requirements: FR-2.3.3, FR-2.3.4, TR-3.3.1, TR-3.3.2_

- [ ] 11.2 Create train/val/test datasets
  - Expected train size: 1,092 samples (70%)
  - Expected val size: 234 samples (15%)
  - Expected test size: 234 samples (15%)
  - Verify location distribution in each split
  - _Requirements: TR-3.3.2_

- [ ] 11.3 Save split datasets
  - `features_train_multi_location.parquet`
  - `features_val_multi_location.parquet`
  - `features_test_multi_location.parquet`
  - Include location metadata
  - _Requirements: FR-2.3.5_

### 12. Single-Location Baseline for Comparison

- [ ] 12.1 Train baseline model on original single-location data
  - Use current 191-sample dataset (Dodoma only)
  - Train all 4 models (RF, XGBoost, LSTM, Ensemble)
  - Record all performance metrics
  - Save as baseline for comparison
  - _Requirements: FR-2.4.5_

- [ ] 12.2 Document baseline performance
  - Test R², RMSE, MAE
  - Train-val gap
  - Feature-to-sample ratio
  - Confidence interval widths
  - _Requirements: FR-2.4.5_

### 13. Multi-Location Model Training

- [ ] 13.1 Train Random Forest on multi-location data
  - Update `models/random_forest_model.py` if needed
  - Train on 1,092 samples
  - Record training time
  - _Requirements: FR-2.4.1, FR-2.4.2_

- [ ] 13.2 Train XGBoost on multi-location data
  - Update `models/xgboost_model.py` if needed
  - May require less regularization with more data
  - _Requirements: FR-2.4.1, FR-2.4.2_

- [ ] 13.3 Train LSTM on multi-location data
  - Update `models/lstm_model.py` if needed
  - May benefit from larger batch sizes
  - _Requirements: FR-2.4.1, FR-2.4.2_

- [ ] 13.4 Train Ensemble on multi-location data
  - Combine predictions from all models
  - Optimize ensemble weights
  - _Requirements: FR-2.4.1, FR-2.4.2_

### 14. Performance Evaluation

- [ ] 14.1 Calculate standard metrics on test set
  - R², RMSE, MAE, MAPE for all models
  - Compare to single-location baseline
  - _Requirements: FR-2.4.5, FR-2.4.9_

- [ ] 14.2 Calculate feature-to-sample ratio
  - Training samples / feature count
  - Verify ≥ 10:1 (minimum), target 20:1+
  - _Requirements: FR-2.4.6, PR-4.1.3_

- [ ] 14.3 Calculate train-validation gap
  - Compare train R² to validation R²
  - Verify gap < 5%
  - _Requirements: FR-2.4.7, PR-4.2.3_

- [ ] 14.4 Analyze per-location performance
  - Calculate test R² for each location separately
  - Identify any problem locations
  - _Requirements: TR-3.3.4_

### 15. Spatial Generalization Validation

- [ ] 15.1 Implement leave-one-location-out cross-validation
  - Create `evaluation/spatial_cv.py`
  - Train on 4 locations, test on held-out location
  - Repeat for all 5 locations
  - _Requirements: FR-2.4.4, TR-3.3.3_

- [ ] 15.2 Run LOLO CV for all models
  - Test spatial generalization capability
  - Target: held-out location R² ≥ 0.75
  - _Requirements: FR-2.4.4, PR-4.2.2_

- [ ] 15.3 Implement k-fold location-stratified CV
  - 5-fold CV with location stratification
  - Calculate mean and std of performance
  - Target: std < 0.10
  - _Requirements: TR-3.3.3, PR-4.2.4_

### 16. Uncertainty Quantification

- [ ] 16.1 Calculate prediction intervals on multi-location model
  - Use ensemble variance for uncertainty
  - Calculate 95% prediction intervals
  - _Requirements: PR-4.2.5_

- [ ] 16.2 Validate prediction interval coverage
  - Check if 90-98% of test points fall within intervals
  - Compare interval widths to single-location baseline
  - Expect narrower intervals with more data
  - _Requirements: PR-4.2.5_

---

## Phase 6: Documentation and Reporting (Week 12)

### 17. Performance Comparison Report

- [ ] 17.1 Create comprehensive comparison report
  - Create `docs/MULTI_LOCATION_RESULTS.md`
  - Compare single-location vs multi-location models
  - Include all metrics, visualizations, insights
  - _Requirements: FR-2.5.5_

- [ ] 17.2 Generate before/after visualizations
  - Sample size comparison
  - Feature-to-sample ratio improvement
  - Performance metric comparisons
  - Confidence interval width comparison
  - _Requirements: FR-2.5.8_

- [ ] 17.3 Document location-specific performance
  - Performance by location
  - Spatial generalization results
  - Identify any location-specific patterns
  - _Requirements: FR-2.5.6_

### 18. Data Documentation

- [ ] 18.1 Document all selected locations
  - Coordinates, elevation, climate zone
  - Data availability and quality notes
  - _Requirements: FR-2.5.1_

- [ ] 18.2 Document data collection process
  - Collection date ranges
  - Any issues encountered
  - Data gaps and how they were handled
  - _Requirements: FR-2.5.2, FR-2.5.3_

- [ ] 18.3 Create data provenance records
  - Source URLs and API versions
  - Collection timestamps
  - Processing versions
  - _Requirements: FR-2.5.4_

### 19. Statistical Validation Documentation

- [ ] 19.1 Document statistical improvements
  - Feature-to-sample ratio improvement
  - Train-val gap reduction
  - Confidence interval narrowing
  - Cross-validation stability
  - _Requirements: FR-2.5.7_

- [ ] 19.2 Document scientific rigor improvements
  - Publishability assessment
  - Statistical power analysis
  - Generalization evidence
  - _Requirements: Acceptance criteria_

---

## Phase 7: Production Integration (Week 12+)

### 20. Model Deployment

- [ ] 20.1 Save multi-location models for production
  - Save all 4 trained models
  - Include location encoding requirements
  - Document model usage
  - _Requirements: Acceptance criteria_

- [ ] 20.2 Update prediction pipeline for multi-location inference
  - Modify prediction scripts to handle location parameter
  - Add location encoding logic
  - Test predictions for all 5 locations
  - _Requirements: FR-2.4.1_

- [ ] 20.3 Update dashboard to show spatial predictions
  - Add location selector
  - Display predictions for each location
  - Show spatial generalization metrics
  - _Requirements: Optional enhancement_

### 21. Automated Monthly Updates (Optional)

- [ ] 21.1 Set up automated monthly data collection
  - Collect new month's data for all 5 locations
  - Append to existing dataset
  - Growth: 60 samples/year (5 locations × 12 months)
  - _Requirements: Sustainability goal_

- [ ] 21.2 Implement quarterly model retraining
  - Schedule retraining every 3 months
  - Validate performance after retraining
  - Update production model
  - _Requirements: Sustainability goal_

---

## Phase 8: Expansion to 8 Locations (Weeks 13-16) - OPTIONAL

### 22. Additional Location Selection

- [ ] 22.1 Select 3 additional locations
  - Tabora (Western plateau)
  - Mtwara (Southern coastal)
  - Kigoma (Western, Lake Tanganyika)
  - Document coordinates and characteristics
  - _Requirements: Phase 2 target_

- [ ] 22.2 Collect data for additional 3 locations
  - Repeat collection process (2000-2025)
  - Validate data quality
  - _Requirements: Phase 2 target_

### 23. Retrain with 8 Locations

- [ ] 23.1 Process and merge data from 8 locations
  - Expected size: 8 locations × 312 months = 2,496 samples
  - Training samples: 1,747 (70%)
  - _Requirements: PR-4.1.2_

- [ ] 23.2 Retrain all models with expanded dataset
  - Feature-to-sample ratio: 33.3:1 (with 75 features)
  - Optimize hyperparameters if needed
  - _Requirements: PR-4.1.2, TR-3.3.5_

- [ ] 23.3 Validate final model performance
  - Verify all performance targets met
  - Document improvements over 5-location model
  - _Requirements: Acceptance criteria_

---

## Final Checkpoint: Acceptance Criteria Verification

### 24. Data Collection Verification

- [ ] 24.1 Verify data collected for 5-8 locations
  - All 5 sources available for each location
  - Temporal coverage 2000-2025 (312 months)
  - Data quality meets standards (≥90% completeness)
  - Total samples: 1,560-2,496
  - _Requirements: Acceptance 8.1_

### 25. Model Performance Verification

- [ ] 25.1 Verify feature-to-sample ratio achieved
  - For 5 locations: 1,092 train / 75 features = 14.6:1 ✓
  - For 8 locations: 1,747 train / 75 features = 23.3:1 ✓
  - Minimum 10:1 achieved ✓
  - _Requirements: Acceptance 8.2_

- [ ] 25.2 Verify model performance maintained
  - Test R² ≥ 0.85
  - Held-out location R² ≥ 0.75
  - Train-val gap < 5%
  - Model scientifically sound
  - _Requirements: Acceptance 8.2_

### 26. Documentation Verification

- [ ] 26.1 Verify all documentation complete
  - Locations documented
  - Data collection process documented
  - Performance comparison report generated
  - Validation results documented
  - _Requirements: Acceptance 8.3_

### 27. Production Readiness Verification

- [ ] 27.1 Verify production readiness
  - Multi-location model trained and validated
  - Automated data collection set up (optional)
  - Model ready for operational deployment
  - Team trained on multi-location workflow
  - _Requirements: Acceptance 8.4_

---

## Success Metrics Summary

**Sample Size**:
- Current: 191 samples
- Phase 1 Target: 1,560 samples (8.2× increase) ✓
- Phase 2 Target: 2,496 samples (13.1× increase) ✓

**Feature-to-Sample Ratio** (with 75 features):
- Current: 2.5:1 ❌
- Phase 1: 20.8:1 ✓
- Phase 2: 33.3:1 ✓

**Model Performance**:
- Test R²: ≥ 0.85 (maintain)
- Held-out location R²: ≥ 0.75
- Train-val gap: < 5%
- CV std: < 0.10

**Scientific Rigor**:
- Publishable methodology ✓
- Robust spatial generalization ✓
- Narrow confidence intervals ✓
- Statistical soundness ✓
