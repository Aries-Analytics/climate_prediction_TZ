# Climate Index Insurance Pivot - Design Document

## 1. Overview
This document outlines the design for pivoting HewaSense from a "crop failure prediction" model to a "climate index forecasting" model with parametric insurance triggers. This approach reduces basis risk and aligns with industry best practices for smallholder farmer insurance in Tanzania.

## 2. Architecture

```text
+-----------------------+       +-------------------------+
|  Climate Data Sources | ----> |  ML Forecasting Engine  |
+-----------------------+       +-----------+-------------+
                                            |
                                            v
                                 +-----------------------+
                                 |  Climate Forecast DB  |
                                 | (Rainfall / NDVI)     |
                                 +----------+------------+
                                            |
                       +--------------------+--------------------+
                       |                                         |
                       v                                         v
            +---------------------+                   +----------------------+
            | Trigger Evaluator   | <---------------- |   Threshold Config   |
            +----------+----------+                   | (Calendar/Phenology) |
                       |                              +----------------------+
                       v
            +---------------------+
            | Trigger Alerts DB   |
            +----------+----------+
                       |
                       v
            +---------------------+
            |   FastAPI Backend   |
            +----------+----------+
                       |
                       v
            +---------------------+
            | Frontend Dashboard  |
            +---------------------+
            | - Rainfall Charts   |
            | - Alert Cards       |
            +---------------------+
```

## 3. Data Models

### 3.1 ClimateForecast
Stores the raw forecasted predictions for climate variables. Replaces `Forecast` table's use of 'trigger_type'.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary Key |
| `target_date` | Date | The date being predicted |
| `horizon_days` | Integer | How far ahead the forecast is (30, 60, 90) |
| `location_id` | Integer | Foreign Key to Locations |
| `rainfall_mm` | Numeric | Predicted Daily/Monthly Rainfall |
| `ndvi_value` | Numeric | Predicted vegetation index |
| `soil_moisture`| Numeric | Predicted soil moisture % |
| `season` | String | 'wet_season' / 'dry_season' |

### 3.2 TriggerAlert
Stores actionable insurance alerts generated when forecasts breach critical thresholds.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary Key |
| `forecast_id` | Integer | Link to ClimateForecast |
| `alert_type` | String | 'rainfall_deficit', 'excessive_rain' |
| `severity` | String | 'warning', 'critical' |
| `stage` | String | 'flowering', 'germination' |
| `threshold` | Numeric | The value that was breached |
| `action` | String | Recommended farmer action |

## 4. Business Logic: Calendar-Based Thresholds

Based on Kilombero Valley rice phenology:

### Wet Season (Main Crop)
- **Period**: January - June
- **Logic**:
  - **Jan (Germination)**: Min 50mm, Optimal 100mm
  - **Feb-Mar (Vegetative)**: Min 100mm, Optimal 150mm
  - **Apr (Flowering)**: **CRITICAL** Min 120mm, Optimal 200mm
  - **May (Grain Fill)**: Min 60mm
  - **Jun (Harvest)**: Max 50mm (Needs dry weather)

### Dry Season (Irrigated)
- **Period**: July - December
- **Logic**: Similar stages shifted by 6 months.

## 5. API Design

### `GET /api/climate-forecasts/`
Returns time-series data for charting.
- **Params**: `location_id`, `horizon_days`
- **Response**: `{ dates: [], rainfall: [], thresholds: [] }`

### `GET /api/climate-forecasts/alerts`
Returns active alerts for KPI cards.
- **Params**: `location_id`, `min_severity`
- **Response**: `[{ type: 'rainfall_deficit', severity: 'critical', message: '...' }]`

## 6. Frontend Components

### ClimateForecastChart
A combination Line/Area chart:
- **Line**: Predicted Rainfall
- **Area (Red)**: Deficit zone (below threshold)
- **Annotations**: Phenology Stages (e.g., "April: Flowering")

### Alert KPI
Dynamic status card:
- **Green**: No active alerts
- **Yellow**: Warning (Approaching threshold)
- **Red**: Critical (Breached threshold - Payout likely)
