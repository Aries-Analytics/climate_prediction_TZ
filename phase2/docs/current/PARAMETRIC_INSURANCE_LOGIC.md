# Parametric Insurance Model: Logic & Architecture

**Date**: March 15, 2026
**Last Updated**: April 2, 2026
**Status**: Core Architecture Reference

## 1. Concept Clarification
There is often confusion between "Machine Learning Models" and "Parametric Insurance Models". This document clarifies the distinction and explains how they work together in the HewaSense platform.

### The "Two-Layer" Approach
We do **not** use a single "black box" to decide insurance payouts. We use a transparent two-layer system:

1.  **Layer 1: The Predictor (Machine Learning)**
    *   **What it does**: Predicts future climate conditions (e.g., "Will it rain next month?").
    *   **Models**: Random Forest, LSTM, Ensemble.
    *   **Output**: A forecast (e.g., "35mm rainfall predicted for April 1-10").
    *   **Training**: Requires retraining on historical data to improve accuracy.

2.  **Layer 2: The Decider (Parametric Logic)**
    *   **What it does**: Determines if a payout is due based on **pre-agreed rules**.
    *   **Model**: Phase-Based Code Logic (in `phase_based_coverage.py`).
    *   **Output**: A Payout Trigger (e.g., "YES - Pay $50 because rainfall < 40mm").
    *   **Training**: **NONE**. This is a set of fixed business rules (contracts) that do not "learn".

> **Key Takeaway**: You do **not** need to retrain your ML models to change the insurance product. You simply update the rules in Layer 2.

---

## 2. Phase-Based Triggers (The New Approach)
Instead of looking at total seasonal rainfall (which masks problems), we look at **Rice Growth Phases**.

### Why this is better?
A "Seasonal Total" of 500mm looks good. But if 0mm fell during the **Flowering** phase, the crop fails. Our new model aligns poyouts with biology.

### The Phases (Kilombero Valley Calendar)

| Phase | Months | Importance | Trigger Threshold (Rainfall) |
| :--- | :--- | :--- | :--- |
| **Germination** | Jan, Jul | moderate | < 50mm / month |
| **Vegetative** | Feb-Mar, Aug-Sep | High | < 100mm / month |
| **Flowering** | **Apr, Oct** | **CRITICAL** | **< 120mm / month** |
| **Maturity** | May, Nov | Low | < 60mm / month |
| **Harvest** | Jun, Dec | Negative | > 80mm / month (Flood Risk) |

### Payout Logic Example
*   **Scenario**: It is April (Flowering Phase).
*   **ML Prediction**: LSTM predicts 90mm rainfall.
*   **Parametric Rule**: "If Rainfall < 120mm during Flowering -> Trigger Payout".
*   **Result**: 90mm < 120mm. **PAYOUT TRIGGERED**.

---

## 3. Dashboard Integration
The dashboards have been updated to reflect this logic:

*   **Trigger Events**: Displays alerts linked to specific phases (e.g., "Flowering Deficit" vs generic "Drought").
*   **Early Warnings**: prioritizes alerts based on phase criticality (Flowering alerts are top priority).
*   **Risk Management**: Calculates liability based on the active phase's max payout potential.

## 4. Horizon Tiers & Payout Eligibility (Updated Mar 15, 2026)

The platform generates forecasts at 4 horizons (3, 4, 5, 6 months ahead). Only primary-tier forecasts are payout-eligible:

| Tier | Horizons | Probability Threshold | Role |
|------|----------|-----------------------|------|
| **Primary** | 3–4 months | ≥ 75% | Payout-eligible — counted in financial exposure |
| **Advisory** | 5–6 months | ≥ 50% | Early warning only — never triggers payout |

**Why this matters for financial calculations**:
- All financial exposure metrics (map tooltip, total exposure, 6-month projection chart) include **primary tier only**
- Advisory-tier forecasts appear in Early Warning panels but are explicitly labelled and excluded from reserve calculations
- Prevents premature earmarking of reserves against uncertain long-range forecasts

### Payout Formula

```
Expected Payout = PILOT_FARMERS × probability × payout_rate_per_farmer
```

| Trigger | Rate/Farmer | Example (87.4%) |
|---------|-------------|-----------------|
| Drought | $60 | 1,000 × 0.874 × $60 = $52,440 |
| Flood | $75 | 1,000 × 0.874 × $75 = $65,550 |
| Crop Failure | $90 | 1,000 × 0.874 × $90 = $78,660 |

**Deduplication**: When multiple pipeline runs forecast the same trigger type in the same calendar month, the system uses the **MAX probability** — never sums across runs.

**Enforcement locations**:
- `backend/app/config/rice_thresholds.py` — `HORIZON_TIERS` dict + `get_horizon_tier()`
- `backend/app/api/forecasts.py` — `/forecasts/portfolio-risk` → `horizon_months <= 4`
- `backend/app/api/risk.py` — `/risk/portfolio` → `horizon_months <= 4`
- `frontend/src/pages/ForecastDashboard.tsx` — `generateFinancialProjections()` + `highestRiskForecast`

---

## 5. Operational Implication
*   **Adjusting Sensitivity**: If payouts are too frequent, lower the trigger thresholds (e.g., change 120mm to 100mm) in `rice_thresholds.py`.
*   **New Crops**: To support Maize, create a `maize_thresholds.py` and import it into the logic layer. No ML retraining required.
*   **Horizon tier changes**: Edit `HORIZON_TIERS` in `rice_thresholds.py`. The backend API filters and frontend calculations both read from the same constant.

---

## 6. Loss Ratio Disambiguation (Added April 2, 2026)

Two distinct loss ratio concepts exist in the platform. They must never be conflated:

| Metric | Formula | What it answers |
|---|---|---|
| **Actuarial Loss Ratio** | Historical paid claims ÷ Historical earned premiums | Is the $20/farmer premium sustainably priced over time? |
| **Forward Reserve Stress Ratio** | Probability-weighted expected payout ÷ 6-month premiums | If this season's forecast triggers, how stressed are current reserves? |

**Actuarial Loss Ratio: 22.6%** — derived from 10-year backtested trigger frequency. This is the basis for the $20/farmer premium (Scenario A in `PARAMETRIC_INSURANCE_FINAL.md`). Well within the industry-healthy range (<60%). Stored as `historicalLossRatio` in the `/risk/portfolio` API response.

**Forward Reserve Stress Ratio** — probability-weighted, can exceed 100% in a high-risk season. This is not a sustainability failure; it means the reserve fund (not premiums alone) would cover the payout. The reserve fund exists precisely for this purpose. Displayed in the Risk Management Dashboard as "Reserve Stress Ratio". Capped at 200% for display.

**Why reserves don't contradict sustainability:** The $150K reserve fund absorbs seasons where forward stress is elevated. The product is sustainably priced if the *actuarial* ratio is healthy over time — a single bad season at 87% forecast probability is the scenario reserves are designed for.

---

## 7. Off-Season Alert Exclusion (Added April 2, 2026)

The wet-season pilot covers **January–June only** (rainfed rice, Jan planting → Jun harvest). Months July–December are off-season — no insured crop is in the field.

The `GET /climate-forecasts/alerts` endpoint explicitly excludes forecasts where `get_kilombero_stage(target_date)` returns `'off_season'`. Without this filter, August/September drought forecasts (which can be high probability — August is Kilombero's dry season peak) would appear as active payout triggers despite having no insured crop attached.

**Why off-season drought probabilities can be high:** The XGBoost model correctly identifies that August/September are dry months in Kilombero — it is a real meteorological signal. But no wet-season crop is in the field, so no policy applies. The Executive Dashboard grid shows these cells with a grey "OFF-SEASON" badge instead of the red "TRIGGER" badge.

**Enforcement location:** `backend/app/api/climate_forecasts.py` — `get_active_alerts()`, stage check before building the alert response object.
