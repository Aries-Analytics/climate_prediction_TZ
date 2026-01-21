# Climate Index Insurance Pivot - Tasks

## Phase 1: Database Migration
- [ ] **Create ClimateForecast Model**
  - File: `backend/app/models/climate_forecast.py`
  - Attributes: `rainfall_mm`, `ndvi_value`, `season`, `horizon_days`
- [ ] **Create TriggerAlert Model**
  - File: `backend/app/models/trigger_alert.py`
  - Attributes: `alert_type`, `severity`, `threshold_value`, `action`
- [ ] **Generate Alembic Migration**
  - Command: `alembic revision --autogenerate -m "add_climate_forecasts"`
  - Verify verify `upgrade()` and `downgrade()` scripts.

## Phase 2: Threshold Logic (Backend)
- [ ] **Create Rice Threshold Config**
  - File: `backend/app/config/rice_thresholds.py`
  - Implement `KILOMBERO_WET_SEASON` map (Month -> Stage)
  - Implement `RAINFALL_THRESHOLDS` (Stage -> Min/Max mm)
- [ ] **Implement Trigger Service**
  - File: `backend/app/services/trigger_evaluator.py`
  - Function: `evaluate_rainfall_trigger(forecast, date)`
  - Logic: Determine stage, check threshold, return Alert object if breach.

## Phase 3: Integration
- [ ] **Update Forecast Generator**
  - File: `backend/scripts/generate_forecasts.py`
  - Logic: Save to `ClimateForecast` instead of `Forecast`.
  - Logic: Call `trigger_evaluator` and save `TriggerAlerts`.
- [ ] **Create API Endpoints**
  - File: `backend/app/api/climate_forecasts.py`
  - Endpoint: `GET /` (Forecast History)
  - Endpoint: `GET /alerts` (Active Triggers)

## Phase 4: Frontend Visualization
- [ ] **Create ClimateForecastChart**
  - File: `frontend/src/components/ClimateForecastChart.tsx`
  - Lib: `react-chartjs-2`
  - Feature: Line chart with dynamic threshold lines (red dashed).
- [ ] **Update Dashboard Page**
  - File: `frontend/src/pages/ForecastDashboard.tsx`
  - Replace old `PortfolioRisk` cards with new Alert list.
  - Embed `ClimateForecastChart`.

## Phase 5: Verification
- [ ] **Data Verification**
  - Run `generate_forecasts.py` and inspect DB tables.
- [ ] **Visual Verification**
  - Check Dashboard for correct "Flowering" stage identification in April.
  - Verify alerts trigger correctly for low rainfall values.
