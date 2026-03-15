# Parametric Insurance Model: Logic & Architecture

**Date**: March 15, 2026
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
