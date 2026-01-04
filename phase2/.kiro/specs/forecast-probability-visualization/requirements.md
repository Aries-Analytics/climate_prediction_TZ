# Requirements Document

## Introduction

The forecast probability visualization dashboard is displaying incorrect data due to API response format mismatches and insufficient forecast data. Users are seeing "NaNmo" instead of proper month labels, missing chart lines, and limited forecast coverage (only 3 months visible instead of the expected 3-6 month range).

## Glossary

- **Forecast Dashboard**: Frontend React component displaying climate trigger probability forecasts
- **API Response**: JSON data returned from backend forecast endpoints
- **Horizon**: Number of months ahead that a forecast predicts (3-6 months)
- **Chart Trace**: A single line or marker series in the Plotly visualization
- **Snake Case**: Variable naming convention using underscores (e.g., `horizon_months`)
- **Camel Case**: Variable naming convention using capital letters (e.g., `horizonMonths`)

## Requirements

### Requirement 1

**User Story:** As a dashboard user, I want to see properly formatted forecast horizon labels, so that I can understand the time range of predictions

#### Acceptance Criteria

1. WHEN the forecast API returns data THEN the system SHALL transform snake_case field names to camelCase for frontend consumption
2. WHEN displaying forecast horizons THEN the system SHALL show "3mo", "4mo", "5mo", "6mo" instead of "NaNmo"
3. WHEN the API response contains `horizon_months` THEN the frontend SHALL correctly access it as `horizonMonths`
4. WHEN rendering forecast cards THEN the system SHALL display valid numeric horizon values

### Requirement 2

**User Story:** As a dashboard user, I want to see continuous forecast lines on the chart, so that I can visualize probability trends over time

#### Acceptance Criteria

1. WHEN multiple forecasts exist for the same trigger type and horizon THEN the system SHALL connect them with lines
2. WHEN only one forecast exists for a series THEN the system SHALL display markers only
3. WHEN forecast data is sparse THEN the system SHALL NOT connect gaps with lines
4. WHEN rendering the chart THEN the system SHALL group forecasts by trigger type and horizon correctly

### Requirement 3

**User Story:** As a dashboard user, I want to see forecasts covering the full 3-6 month range, so that I can plan for both near-term and longer-term risks

#### Acceptance Criteria

1. WHEN generating forecasts THEN the system SHALL create predictions for all horizons (3, 4, 5, 6 months)
2. WHEN displaying the chart THEN the system SHALL show target dates spanning at least 3-6 months from today
3. WHEN forecasts are stale THEN the system SHALL indicate they need regeneration
4. WHEN the user views the dashboard THEN the system SHALL display all available forecast horizons

### Requirement 4

**User Story:** As a system administrator, I want the API to return consistent data formats, so that frontend integration is reliable

#### Acceptance Criteria

1. WHEN the forecast API returns data THEN the system SHALL use consistent field naming (camelCase for JSON responses)
2. WHEN Pydantic schemas serialize data THEN the system SHALL configure alias generation for camelCase output
3. WHEN the frontend receives API responses THEN the system SHALL NOT require manual field name transformation
4. WHEN adding new forecast fields THEN the system SHALL automatically apply camelCase conversion

### Requirement 5

**User Story:** As a dashboard user, I want to see multiple forecast dates on the chart, so that I can compare how predictions evolve over time

#### Acceptance Criteria

1. WHEN forecasts are generated daily THEN the system SHALL retain historical forecast data
2. WHEN displaying the chart THEN the system SHALL show forecasts from multiple generation dates
3. WHEN forecast data accumulates THEN the system SHALL maintain at least 30 days of forecast history
4. WHEN the chart renders THEN the system SHALL display temporal evolution of probability estimates
