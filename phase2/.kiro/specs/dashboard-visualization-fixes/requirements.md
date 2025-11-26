# Requirements Document

## Introduction

This document specifies requirements for fixing visualization and data display issues in the climate prediction dashboard. The system currently has three main issues: (1) NDVI, ENSO Index, and IOD Index appear as flat lines when plotted with other climate variables due to scale differences, (2) the ensemble model shows R² score of 0.0000 instead of the actual value, and (3) charts lack educational tooltips to help users understand the data.

## Glossary

- **NDVI**: Normalized Difference Vegetation Index - a measure of vegetation health ranging from 0 (no vegetation) to 1 (dense vegetation)
- **ENSO Index**: El Niño-Southern Oscillation index (ONI) - measures ocean temperature anomalies affecting rainfall patterns, typically ranging from -2 to +2
- **IOD Index**: Indian Ocean Dipole index - influences East African rainfall patterns, typically ranging from -2 to +2
- **R² Score**: Coefficient of determination - measures how well a model explains variance in predictions, ranging from 0 to 1
- **Ensemble Model**: A machine learning model that combines predictions from multiple models (Random Forest, XGBoost, LSTM)
- **Dashboard**: The web-based interface displaying climate data, model performance, and trigger events
- **Chart**: A visual representation of data using Plotly library
- **Tooltip**: Contextual information displayed when hovering over chart elements

## Requirements

### Requirement 1

**User Story:** As a dashboard user, I want to see NDVI, ENSO Index, and IOD Index values clearly on charts, so that I can analyze vegetation and ocean climate patterns alongside other variables.

#### Acceptance Criteria

1. WHEN a user selects NDVI, ENSO Index, or IOD Index along with other climate variables THEN the system SHALL display each variable on its own y-axis scale to prevent flat-line visualization
2. WHEN multiple variables with different scales are plotted THEN the system SHALL use secondary y-axes for variables with smaller value ranges
3. WHEN NDVI is plotted THEN the system SHALL display values on a scale from 0 to 1 with appropriate precision
4. WHEN ENSO or IOD indices are plotted THEN the system SHALL display values on a scale from -2 to +2 with appropriate precision
5. WHEN variables are displayed on multiple y-axes THEN the system SHALL clearly label each axis with the variable name and units

### Requirement 2

**User Story:** As a data scientist, I want to see the correct R² score for the ensemble model, so that I can accurately evaluate its performance against other models.

#### Acceptance Criteria

1. WHEN the ensemble model metrics are loaded into the database THEN the system SHALL store the actual R² score value from the training results
2. WHEN the Model Performance Dashboard displays ensemble model metrics THEN the system SHALL show the correct R² score value
3. WHEN model metrics are missing or invalid THEN the system SHALL display "N/A" instead of 0.0000
4. WHEN the ensemble model is selected THEN the system SHALL display all performance metrics (R², RMSE, MAE, MAPE) with correct values

### Requirement 3

**User Story:** As a dashboard user, I want to see educational tooltips on chart elements, so that I can understand what the data represents and how to interpret it.

#### Acceptance Criteria

1. WHEN a user hovers over a data point on any chart THEN the system SHALL display a tooltip with the date, value, and variable name
2. WHEN a user hovers over NDVI data points THEN the system SHALL display a tooltip explaining that NDVI measures vegetation health
3. WHEN a user hovers over ENSO Index data points THEN the system SHALL display a tooltip explaining El Niño-Southern Oscillation and its impact on rainfall
4. WHEN a user hovers over IOD Index data points THEN the system SHALL display a tooltip explaining Indian Ocean Dipole and its influence on East African rainfall
5. WHEN a user hovers over trigger event markers THEN the system SHALL display a tooltip with event type, date, severity, confidence, and payout amount
6. WHEN tooltips are displayed THEN the system SHALL format numerical values with appropriate precision and units

### Requirement 4

**User Story:** As a system administrator, I want the data loading scripts to correctly extract and store ensemble model metrics, so that the dashboard displays accurate performance data.

#### Acceptance Criteria

1. WHEN the load_model_metrics script reads training_results.json THEN the system SHALL extract ensemble model metrics from the correct JSON structure
2. WHEN ensemble model metrics are extracted THEN the system SHALL validate that R² score is between 0 and 1
3. WHEN model metrics are loaded THEN the system SHALL log the values being inserted for verification
4. WHEN the ensemble model already exists in the database THEN the system SHALL update its metrics with new values
