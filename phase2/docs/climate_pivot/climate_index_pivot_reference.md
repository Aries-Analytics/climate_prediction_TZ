# Climate Index Insurance Pivot - Technical Reference

## Overview
This document details the transition of the HewaSense platform from a generic crop failure predictor to a robust **Climate Index Insurance** system tailored for the Kilombero Valley Rice Pilot.

## Architecture Changes

### 1. Database & Schema
*   **New Tables**:
    *   `climate_forecasts`: Stores forecasted climate variables (rainfall_mm, ndvi_value, soil_moisture_pct) along with metadata like season and confidence intervals.
    *   `trigger_alerts`: Stores actionable insurance payout triggers generated when forecasts breach specific phenological thresholds (e.g., "Drought during Flowering").
*   **Relationships**: Linked Forecasts to Locations for geospatial querying.

### 2. Backend Logic (`app/services`)
*   **Rice Phenology Config**: Defined `app/config/rice_thresholds.py` with specific growth stages for Kilombero rice:
    *   **Sowing** (Jan/Feb)
    *   **Vegetative** (Mar)
    *   **Flowering** (Apr - Critical Stage)
    *   **Harvesting** (Jun)
    *   *Includes specific rainfall requirements (min/max mm) for each stage.*
*   **Trigger Evaluator**: Implemented `TriggerEvaluator` service to automatically check forecasts against these thresholds and generate 'CRITICAL' or 'WARNING' alerts.
*   **Forecast Generation**: Updated `generate_forecasts.py` to produce 6-month rainfall forecasts using regression models instead of legacy classification models.

### 3. API Layer (`app/api`)
*   **New Endpoints** (`app/api/climate_forecasts.py`):
    *   `GET /api/climate-forecasts/?location_id=...`: Returns time-series rainfall data with dynamic threshold limits for visualization.
    *   `GET /api/climate-forecasts/alerts`: Returns active triggers requiring insurance team attention.

### 4. Frontend Visualization (`frontend`)
*   **ClimateForecastChart**: A new multi-layer chart visualizing:
    *   Predicted Rainfall (Blue Line)
    *   Critical Minimum Threshold (Red Dashed Line)
    *   Flood/Max Threshold (Orange Dashed Line)
    *   Tooltips showing relevant Phenology Stage.
*   **Dashboard Overhaul**: The Forecast Dashboard was updated to replace generic "Risk Cards" with a focused **Active Triggers** section and the new Climate Chart.

## Key Components

### Trigger Logic
Triggers are evaluated based on the deviation of forecasted rainfall from the optimal range for the specific phenological stage of the crop.

**Example:**
- **Stage**: Flowering (April)
- **Requirement**: >100mm Rainfall
- **Forecast**: 60mm
- **Result**: `CRITICAL` Alert (Drought Risk) -> Recommendation: "Deploy irrigation supplements"

### Automated Pipeline
1.  **Ingestion**: Weather data (CHIRPS/ERA5) is ingested.
2.  **Prediction**: ML Models predict rainfall for next 6 months.
3.  **Evaluation**: `TriggerEvaluator` compares prediction vs. `rice_thresholds`.
4.  **Alerting**: `TriggerAlert` records are saved to DB.
5.  **Visualization**: Frontend displays alerts and charts.

## Future Steps
*   **User Testing**: Verify the threshold levels with on-ground agronomists in Kilombero.
*   **Model Retraining**: Ingest real-time satellite data to improve the regressor accuracy.
