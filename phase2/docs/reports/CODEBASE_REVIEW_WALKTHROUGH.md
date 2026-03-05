# Codebase Review & Prediction Logic Analysis

**Date**: February 15, 2026  
**Scope**: Read-only review — no code changes made  
**Focus Areas**: Tech stack, data sources, ML pipeline correctness, and prediction logic

---

## Tech Stack Summary

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Vite, Material-UI 5, Plotly.js, Chart.js, Leaflet |
| **Backend** | Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis |
| **ML Models** | TensorFlow/Keras (LSTM), scikit-learn (Random Forest), XGBoost, Ensemble |
| **Data Sources** | CHIRPS (GEE), ERA5 (CDS API), NASA POWER, NDVI (GEE/MODIS), Ocean Indices (NOAA) |
| **Infrastructure** | Docker Compose, APScheduler |

---

## Data & ML Pipeline Review

### Data Ingestion (5 modules — all well-structured)
- **CHIRPS**: Google Earth Engine → monthly rainfall; has synthetic fallback
- **ERA5**: CDS API → temperature, humidity, wind; multi-variable extraction
- **NASA POWER**: REST API → solar radiation, temperature; robust error handling
- **NDVI**: GEE/MODIS → vegetation health; synthetic climatological fallback
- **Ocean Indices**: NOAA CPC → ENSO (ONI), IOD; text-format parsers

### Preprocessing ([preprocess.py](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/preprocessing/preprocess.py))
- Feature engineering: lag features (1,3,6,12 months), rolling windows (3,6 months), interaction features
- Location encoding via cyclical sin/cos of lat/lon
- Correlation-based removal (>0.95 threshold)
- Split: 65% train / 20% val / 15% test with 12-month temporal gaps — **correctly prevents leakage**

### Feature Selection ([feature_selection.py](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/preprocessing/feature_selection.py))
- Hybrid approach: correlation + Random Forest importance + Lasso + XGBoost
- Reduces from ~640 features to 50-100 selected features

### Training Pipeline ([train_pipeline.py](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/models/train_pipeline.py))
- Time-series cross-validation (5 folds, expanding window)
- Explicit data leakage verification step
- Location-aware splitting
- Model comparison and ensemble weighting

> [!TIP]
> The ML training pipeline is well-designed with proper temporal splitting, leakage verification, and time-series CV. No critical issues found in the training logic.

---

## Prediction Logic Review — Issues Found

### 🔴 Critical Issues

#### 1. Duplicate Class Definition in `forecast_service.py`

[forecast_service.py#L27-L33](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/app/services/forecast_service.py#L27-L33)

```python
class ForecastGenerator:          # Line 27 — first definition (empty)
    """Service for generating climate trigger forecasts"""

from app.models.location import Location  # Line 30 — import between classes

class ForecastGenerator:          # Line 32 — second definition (actual one)
    """Service for generating climate trigger forecasts"""
```

The first `ForecastGenerator` class at L27 is immediately overwritten by the second at L32. The import statement between them is misplaced. **Python will use the second definition, so it works at runtime**, but this is confusing dead code.

---

#### 2. `generate_forecasts.py` Imports Non-Existent Function

[generate_forecasts.py#L27](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/scripts/generate_forecasts.py#L27)

```python
from app.services.forecast_service import generate_climate_forecasts_all_locations
```

This function **does not exist** in `forecast_service.py`. The actual function is `generate_forecasts_all_locations`. Running this script will raise an `ImportError`.

Additionally at L58, it accesses `f.trigger_alerts` — but the `ForecastResponse` schema has no `trigger_alerts` attribute. This would raise an `AttributeError` at runtime.

---

#### 3. Undefined Variable in `seasonal_forecast_integration.py`

[seasonal_forecast_integration.py#L78](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/app/services/seasonal_forecast_integration.py#L78)

```python
except Exception as e:
    moderate_payout = simple_payout   # ← 'simple_payout' is never defined
```

If the phase-based calculation fails, the `except` block references `simple_payout` which doesn't exist in scope. This will raise a `NameError`.

The same file's `update_dashboard_data` method (L183-227) references dictionary keys like `seasonal_forecast['simple_model']`, `seasonal_forecast['phase_based_model']`, `seasonal_forecast['trigger_probabilities']`, and `seasonal_forecast['model_comparison']` — none of which are returned by `generate_seasonal_forecast()`. The function only returns keys like `drought_probability`, `flood_probability`, `phase_breakdown`, etc. This method would crash with `KeyError`.

---

#### 4. Model `predict_proba` Assumption Mismatch

[forecast_service.py#L170-171](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/app/services/forecast_service.py#L170-L171)

```python
prediction = self.model.predict_proba(features_df)[0]
probability = float(prediction[1] if len(prediction) > 1 else prediction[0])
```

This assumes `predict_proba` — a classification method. However the ML pipeline is a **regression** pipeline (predicting rainfall in mm, not binary trigger events). The trained models use `.predict()` not `.predict_proba()`:
- **LSTM**: Keras model → `model.predict()` returns continuous values
- **XGBoost/RF**: Trained as regressors → have `.predict()` not `.predict_proba()`

This call will either raise an `AttributeError` (for Keras models and regressors) or return wrong results. The fallback to `_baseline_prediction()` catches this error, meaning **predictions always use the rule-based baseline** rather than the trained ML models.

---

### 🟡 Moderate Issues

#### 5. Frontend-Backend Location ID Mismatch

[ForecastDashboard.tsx#L88-L119](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/frontend/src/pages/ForecastDashboard.tsx#L88-L119)

```typescript
// Frontend hardcodes locationId: 1 for Morogoro
const morogoroLocation = { locationId: 1, ... }

// API call uses location_id: 1
params: { days: 180, location_id: 1 }
```

But the backend consistently uses `PILOT_LOCATION_ID = 6` for Morogoro:

```python
# Backend hardcodes location_id: 6 for Morogoro
PILOT_LOCATION_ID = 6  # Morogoro, Tanzania
```

This mismatch means the frontend requests forecasts for `location_id=1` while the backend's portfolio risk, financial impact, and location risk summary endpoints all filter for `location_id=6`. **The forecasts endpoint passes through any location_id**, so the frontend will get forecasts for location 1 (whatever that is), while portfolio risk data is calculated for location 6.

---

#### 6. `should_run_forecast` Timezone-Naive Comparison

[forecast_scheduler.py#L47](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/app/services/forecast_scheduler.py#L47)

```python
days_old = (datetime.now() - latest_forecast.created_at).days
```

`datetime.now()` is timezone-naive, but `created_at` uses `DateTime(timezone=True)` with `server_default=func.now()` (timezone-aware). Subtracting these can raise a `TypeError` or produce incorrect results depending on the database driver.

Compare with `get_forecasts()` which correctly uses `datetime.now(timezone.utc)` at L358.

---

#### 7. Feature Name Mismatch Between Training and Serving

The [prepare_features](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/app/services/forecast_service.py#L67-L140) method generates 10 features:

```
avg_temp_3mo, avg_rainfall_3mo, avg_ndvi_3mo, avg_temp_6mo, avg_rainfall_6mo,
total_rainfall_3mo, total_rainfall_6mo, enso_latest, iod_latest, horizon_months
```

But the training pipeline in `preprocess.py` generates ~640 features (lag features, rolling windows, interaction terms, location encodings, etc.) reduced to ~75 by feature selection. **The feature names and count do not match.** Even if `predict_proba` worked, the model would reject the input due to shape mismatch.

---

#### 8. `_baseline_prediction` Horizon Decay Logic

[forecast_service.py#L216-218](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/app/services/forecast_service.py#L216-L218)

```python
horizon_decay = 0.6 ** (horizon_months - 3)
mean_probability = 0.15
adjusted_probability = base_probability * horizon_decay + mean_probability * (1 - horizon_decay)
```

For horizon=3: `decay = 0.6^0 = 1.0` → full base probability  
For horizon=6: `decay = 0.6^3 = 0.216` → heavy regression toward 15% mean

This means **longer horizons always regress toward 15%**, regardless of actual climate severity. While mean-reversion is conceptually reasonable, a fixed 15% mean with 0.6 decay is arbitrary and not calibrated against historical trigger rates.

---

#### 9. Payout Calculation Inconsistencies Between Frontend & Backend

The frontend's [financial projections](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/frontend/src/pages/ForecastDashboard.tsx#L359-L418) use a **50% (Advisory) threshold** and calculate payouts as:

```typescript
if (f.probability >= 0.50) {
    const affectedFarmers = PILOT_FARMERS * f.probability;
    const amount = Math.round(affectedFarmers * payoutPerFarmer);
}
```

But the backend's [portfolio-risk](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/app/api/forecasts.py#L334-L339) endpoint uses a **75% (High Risk) threshold**:

```python
high_risk_forecasts = db.query(Forecast).filter(
    Forecast.probability >= 0.75,
    ...
```

This means the financial chart on the dashboard will show **significantly higher payouts** than the portfolio risk API returns, because it includes forecasts between 50-75% that the backend excludes.

---

### 🟢 Minor Issues

#### 10. `get_kilombero_stage` Called With Inconsistent Arguments

In [climate_forecasts.py#L84](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/app/api/climate_forecasts.py#L84):
```python
stage = get_kilombero_stage(f.target_date, season_type)  # Two args
```

In [forecast_service.py#L372](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/app/services/forecast_service.py#L372):
```python
stage = get_kilombero_stage(f.target_date)  # One arg
```

The function may or may not accept an optional `season_type` parameter. If it does, the one-arg call may default to 'wet' season regardless of actual date.

#### 11. Staleness Check Uses Different Timezone Approaches

`forecast_scheduler.py` uses `datetime.now()` (naive), while `forecast_service.get_forecasts()` uses `datetime.now(timezone.utc)` (aware). The `created_at` column is timezone-aware. This inconsistency could cause comparison errors in the scheduler.

---

## Summary

| Category | Count | Severity |
|----------|-------|----------|
| Critical Runtime Errors | 4 | 🔴 Would crash at runtime |
| Logic/Data Mismatches | 5 | 🟡 Would produce incorrect results |
| Minor Inconsistencies | 2 | 🟢 Could cause subtle bugs |

> [!IMPORTANT]
> **The most significant finding is Issue #4 + #7**: The prediction logic in `forecast_service.py` cannot actually use the trained ML models because (a) it calls `predict_proba` on regression models, and (b) the serving features don't match training features. In practice, **all predictions fall through to the rule-based `_baseline_prediction` method**, which uses hardcoded heuristics rather than the trained ensemble. The ML training pipeline itself is well-built, but the bridge between trained models and production serving is broken.

> [!NOTE]
> Per your request, no code changes were made. All findings are documented for review only.
