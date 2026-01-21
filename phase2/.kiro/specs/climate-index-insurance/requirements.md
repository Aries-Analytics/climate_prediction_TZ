# Climate Index Insurance Pivot - Requirements

## 1. Functional Requirements

### 1.1 Climate Data Management
- **REQ-1**: System MUST store forecasted values for Rainfall, NDVI, and Soil Moisture.
- **REQ-2**: System MUST support multiple forecast horizons (30, 60, 90 days).
- **REQ-3**: System MUST associate forecasts with specific Locations.

### 1.2 Threshold Evaluation
- **REQ-4**: System MUST verify the calendar month of a forecast target date.
- **REQ-5**: System MUST look up the correct rice phenology stage for that month (e.g., April = Flowering).
- **REQ-6**: System MUST compare forecasted values against stage-specific thresholds.
- **REQ-7**: System MUST support distinct configurations for "Wet Season" and "Dry Season".

### 1.3 Alert Generation
- **REQ-8**: System MUST generate a `TriggerAlert` when a threshold is breached.
- **REQ-9**: Alerts MUST capture the severity ('warning' vs 'critical').
  - *Critical*: < 70% of minimum required rainfall.
  - *Warning*: < 90% of minimum required rainfall.
- **REQ-10**: Alerts MUST include actionable recommendations (e.g., "Prepare supplemental irrigation").

### 1.4 API & Reporting
- **REQ-11**: API MUST provide time-series data including forecast value AND threshold line for visualization.
- **REQ-12**: API MUST provide a summary of active alerts for a given location.

## 2. Non-Functional Requirements

### 2.1 Accuracy & Reliability
- **NFR-1**: Trigger logic must be deterministic (Same forecast + Same config = Same Alert).
- **NFR-2**: Calendar thresholds must be based on verified agricultural research for Morogoro/Kilombero.

### 2.2 Performance
- **NFR-3**: Threshold evaluation must occur within 200ms of forecast generation.
- **NFR-4**: Dashboard chart data must load within 1s.

### 2.3 Usability
- **NFR-5**: Alerts must be presented in clear, non-technical language for insurance officers.
- **NFR-6**: Visualizations must clearly distinguish between "Safe Zone" and "Risk Zone".

## 3. Assumptions & Constraints
- **ASS-1**: ML models provide `rainfall_mm` predictions.
- **ASS-2**: All 6 pilot locations are in the Morogoro region (Kilombero Valley).
- **ASS-3**: Primary crop is Rice.
