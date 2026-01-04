# Implementation Plan: Model Performance Improvements

- [ ] 1. Implement feature selection module




  - Create `preprocessing/feature_selection.py` with correlation-based, importance-based, and hybrid selection methods
  - Implement source diversity enforcement to ensure all 5 data sources are represented
  - Implement redundancy removal for features with correlation > 0.95
  - Save selected feature lists and metadata for reproducibility
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ]* 1.1 Write property test for feature selection source diversity
  - **Property 1: Feature selection preserves source diversity**
  - **Validates: Requirements 1.3**

- [ ]* 1.2 Write property test for dimensionality reduction
  - **Property 2: Feature selection reduces dimensionality**
  - **Validates: Requirements 1.1**

- [ ]* 1.3 Write property test for correlation removal
  - **Property 11: Feature correlation removal reduces redundancy**


  - **Validates: Requirements 6.4**

- [ ] 2. Implement baseline models for comparison
  - Create `models/baseline_models.py` with PersistenceBaseline, ClimatologyBaseline, and LinearRegressionBaseline classes
  - Implement fit and predict methods for each baseline
  - Calculate R², RMSE, and MAE for each baseline model
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ]* 2.1 Write property test for baseline model simplicity
  - **Property 6: Baseline models are simpler than complex models**
  - **Validates: Requirements 4.1, 4.2, 4.3**

- [ ]* 2.2 Write unit tests for baseline models
  - Test persistence baseline returns last values correctly

  - Test climatology baseline calculates monthly means correctly
  - Test linear baseline selects correct number of features
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 3. Apply enhanced regularization to existing models



  - Modify `models/train_models.py` to add stronger regularization parameters for XGBoost (alpha >= 0.1, lambda >= 1.0)
  - Add regularization parameters for Random Forest (max_depth <= 10, min_samples_leaf >= 5)
  - Add dropout >= 0.3 and L2 regularization to LSTM model
  - Log all regularization hyperparameters for reproducibility
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [ ]* 3.1 Write property test for regularization effectiveness
  - **Property 5: Regularization reduces train-val gap**

  - **Validates: Requirements 3.4**

- [ ] 4. Implement time-series cross-validation


  - Create `evaluation/cross_validation.py` with time_series_cv_split function using expanding window strategy
  - Implement cross_validate_model function to run CV and aggregate metrics
  - Implement calculate_confidence_intervals function using t-distribution
  - Ensure minimum 5 folds with chronological ordering maintained
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 4.1 Write property test for temporal ordering
  - **Property 3: Time-series CV maintains temporal order**
  - **Validates: Requirements 2.5**

- [ ]* 4.2 Write property test for CV fold count
  - **Property 4: Cross-validation provides multiple estimates**
  - **Validates: Requirements 2.3**

- [ ]* 4.3 Write property test for confidence interval width
  - **Property 12: Confidence intervals widen with fewer samples**
  - **Validates: Requirements 2.4**

- [ ]* 4.4 Write unit tests for cross-validation
  - Test split sizes match expectations
  - Test with edge cases (small datasets)
  - Test confidence interval calculations with known distributions
  - _Requirements: 2.1, 2.2, 2.3, 2.4_



- [ ] 5. Implement improved ensemble method
  - Create `models/ensemble.py` with WeightedEnsemble class
  - Implement fit_weights method using inverse RMSE weighting
  - Implement predict method with weighted averaging
  - Implement predict_with_intervals method for uncertainty quantification
  - _Requirements: 7.1, 7.2, 7.3_

- [ ]* 5.1 Write property test for ensemble performance
  - **Property 7: Ensemble outperforms individual models**
  - **Validates: Requirements 7.4**

- [ ]* 5.2 Write property test for ensemble weights
  - **Property 8: Ensemble weights sum to one**
  - **Validates: Requirements 7.2**

- [ ]* 5.3 Write unit tests for ensemble
  - Test weight calculation sums to 1.0
  - Test weighted prediction matches manual calculation



  - Test prediction intervals contain mean prediction
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 6. Optimize feature engineering in preprocessing
  - Modify `preprocessing/preprocess.py` to reduce lag features from [1,3,6,12] to [1,3,6]
  - Limit rolling window features to 3-month windows only
  - Implement interaction feature selection for top 5 variable pairs
  - Remove highly correlated features (correlation > 0.95)
  - _Requirements: 6.1, 6.2, 6.3, 6.4_



- [ ]* 6.1 Write unit tests for optimized feature engineering
  - Test lag features are limited to [1,3,6]
  - Test rolling windows use 3-month periods
  - Test correlation removal works correctly
  - _Requirements: 6.1, 6.2, 6.4_

- [ ] 7. Implement expanded evaluation metrics
  - Modify `evaluation/evaluate.py` to calculate prediction interval coverage at 95% confidence
  - Add seasonal performance breakdown (short rains, long rains, dry season)
  - Calculate skill scores relative to climatology baseline
  - Identify and report worst-performing months
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 7.1 Write property test for prediction interval coverage
  - **Property 9: Prediction intervals have correct coverage**
  - **Validates: Requirements 5.1**

- [ ]* 7.2 Write unit tests for expanded metrics
  - Test seasonal breakdown calculations
  - Test skill score calculations
  - Test worst-month identification
  - _Requirements: 5.2, 5.3, 5.4_

- [ ] 8. Implement automated model validation pipeline



  - Create `utils/model_validation.py` with validation checks
  - Implement check for feature-to-sample ratio (flag if < 5:1)
  - Implement check for train-validation gap (flag if > 5%)
  - Implement check for test set size (flag if < 50 samples)
  - Implement baseline comparison check (flag if improvement < 10%)
  - Generate pass/fail report with actionable recommendations
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 8.1 Write property test for validation pipeline flagging
  - **Property 10: Validation pipeline flags critical issues**
  - **Validates: Requirements 10.1**

- [ ]* 8.2 Write unit tests for validation pipeline
  - Test each validation check independently
  - Test report generation with various scenarios
  - Test recommendation generation
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_


- [x] 9. Create comprehensive reporting module

  - Create `evaluation/reporting.py` for generating detailed reports
  - Implement feature selection report with scores and correlation matrix
  - Implement cross-validation report with fold-by-fold metrics
  - Implement model comparison report with baseline comparisons
  - Implement validation pipeline report with all checks
  - Generate visualizations (correlation heatmaps, performance plots)
  - _Requirements: 5.5, 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 9.1 Write unit tests for reporting module
  - Test report generation for each report type
  - Test visualization creation
  - Test academic language templates
  - _Requirements: 5.5, 9.1, 9.2, 9.3, 9.4, 9.5_


- [x] 10. Integrate all improvements into training pipeline




  - Modify `train_pipeline.py` to use feature selection before training
  - Add baseline model training and comparison
  - Add time-series cross-validation evaluation
  - Add weighted ensemble creation
  - Add automated validation checks
  - Generate comprehensive reports after training
  - _Requirements: 1.5, 4.5, 7.4, 10.5_

- [ ]* 10.1 Write integration tests for full pipeline
  - Test end-to-end pipeline with feature selection through reporting
  - Test that all components work together correctly
  - Test error handling and edge cases
  - _Requirements: 1.5, 4.5, 7.4, 10.5_

- [x] 11. Create data augmentation strategy documentation




  - Create `docs/DATA_AUGMENTATION_STRATEGY.md` documenting expansion approaches
  - Document spatial expansion strategy (multi-location training)
  - Document temporal expansion strategy (continued data collection)
  - Document sub-seasonal aggregation approach
  - Calculate target sample sizes for 10:1 sample-to-feature ratio
  - Document limitations and assumptions
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 12. Update training results with improved models






  - Run full training pipeline with all improvements applied
  - Generate new training results JSON with enhanced metrics
  - Compare new results against baseline (original 640-feature model)
  - Verify train-val gap is reduced to < 5%
  - Verify feature count is between 50-100
  - Document performance changes and improvements
  - _Requirements: 1.5, 3.4, 5.5_

- [x] 13. Update frontend dashboard with temporal leakage-free results


  - Update ModelPerformanceDashboard.tsx to display new training results
  - Add visual indicators for temporal leakage fix (12-month gaps between splits)
  - Update data split information display (Train: 294, Val: 98, Test: 75)
  - Add comparison section showing before/after temporal leakage fix
  - Update baseline comparison display with Ridge baseline (R² = 0.8707)
  - Add educational content explaining why R² dropped from 0.95+ to 0.87-0.90
  - Ensure feature-to-sample ratio display shows improved 5.55:1 ratio
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 14. Final checkpoint - Verify all improvements
  - Ensure all tests pass
  - Verify feature selection reduces features to 50-100
  - Verify regularization reduces train-val gap to < 5%
  - Verify cross-validation produces robust estimates with confidence intervals
  - Verify ensemble outperforms individual models
  - Verify validation pipeline correctly flags issues
  - Ask user if questions arise

