# Requirements Document

## Introduction

The Model Performance Dashboard currently displays Cross-Validation (CV) R² scores as the primary metric. However, the test set metrics (R², RMSE, MAE) from the final holdout test set (2019-2025, 75 samples) are the true indicators of model performance on unseen data. This feature will update the dashboard to display test set metrics as the primary performance indicators, with CV metrics as supplementary validation information.

## Glossary

- **Test Set Metrics**: Performance metrics calculated on the final holdout test set (2019-2025, 75 samples) that was never seen during training or validation
- **Cross-Validation (CV) Metrics**: Performance metrics calculated across multiple train/validation splits during model development
- **R² Score**: Coefficient of determination, measures how well the model explains variance in the data (0-1, higher is better)
- **RMSE**: Root Mean Squared Error, measures average prediction error in millimeters (lower is better)
- **MAE**: Mean Absolute Error, measures average absolute prediction error in millimeters (lower is better)
- **Dashboard**: The frontend Model Performance Dashboard component
- **Backend API**: The FastAPI service that provides model metrics data

## Requirements

### Requirement 1

**User Story:** As a data scientist, I want to see test set metrics as the primary performance indicators on the dashboard, so that I can evaluate model performance on truly unseen data.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL display test set R², RMSE, and MAE as the primary metrics for each model
2. WHEN displaying the primary metric card THEN the system SHALL show the test R² score with a label indicating it is from the test set
3. WHEN displaying error metrics THEN the system SHALL show test RMSE and test MAE values
4. WHEN showing the metrics table THEN the system SHALL display test set metrics in the main columns
5. WHEN rendering comparison charts THEN the system SHALL use test set metrics for model comparisons

### Requirement 2

**User Story:** As a data scientist, I want CV metrics to be displayed as supplementary information, so that I can understand model stability across different data splits.

#### Acceptance Criteria

1. WHEN viewing model details THEN the system SHALL display CV metrics in a separate "Cross-Validation Details" section
2. WHEN showing CV metrics THEN the system SHALL clearly label them as "Cross-Validation" metrics
3. WHEN displaying CV metrics THEN the system SHALL show mean ± standard deviation format
4. WHEN presenting CV information THEN the system SHALL include explanatory text that CV metrics are supplementary
5. WHEN the user views the dashboard THEN the system SHALL visually distinguish CV metrics from test metrics using different card styling

### Requirement 3

**User Story:** As a data scientist, I want clear explanations of why test metrics are the primary evaluation criteria, so that I can understand the scientific validity of the results.

#### Acceptance Criteria

1. WHEN viewing the dashboard THEN the system SHALL display an informational alert explaining the importance of test set metrics
2. WHEN showing metric interpretations THEN the system SHALL explain that test R² is the primary metric for final model evaluation
3. WHEN displaying performance context THEN the system SHALL include information about the test set composition (75 samples, 2019-2025)
4. WHEN presenting model comparisons THEN the system SHALL reference test set performance as the basis for comparison
5. WHEN showing the "Understanding Model Performance" section THEN the system SHALL emphasize test metrics over CV metrics

### Requirement 4

**User Story:** As a developer, I want the backend API to continue providing both test and CV metrics, so that the frontend can display comprehensive performance information.

#### Acceptance Criteria

1. WHEN the API returns model metrics THEN the system SHALL include both test metrics (r2_score, rmse, mae) and CV metrics (cv_r2_mean, cv_rmse_mean, etc.)
2. WHEN loading metrics from training results THEN the system SHALL extract test_metrics from the JSON file
3. WHEN test metrics are unavailable THEN the system SHALL fall back to validation metrics
4. WHEN the database stores metrics THEN the system SHALL maintain the current schema with r2_score, rmse, mae representing test set performance
5. WHEN the API response is serialized THEN the system SHALL use camelCase naming for frontend compatibility
