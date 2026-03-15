# True Parametric Insurance - Final Implementation

**Date**: January 1, 2026
**Status**: ✅ PILOT-READY
**Version**: 3.0 (Market-Competitive)

---

## Executive Summary

Implemented true parametric insurance with market-competitive rates aligned with successful African programs (Pula Zambia, KLIP Kenya, IBLI Ethiopia). The system provides multi-peril coverage (drought, flood, crop failure) at affordable rates while maintaining financial sustainability.

**Key Achievement**: Reduced sustainable premium from **$91/year** (Lump Sum Model) to **$20/year** (Phase-Based Model) without requiring heavy subsidies. This was achieved by moving from binary "all-or-nothing" payouts to weighted, phase-specific coverage.

## 1. Product Summary

- **Type**: Hybrid Parametric Insurance (Drought + Flood)
- **Target**: Smallholder Rice Farmers (0.5 - 2 hectares)
- **Region**: Kilombero Basin (Morogoro)
- **Premium**: **$20 / season** (Affordable for smallholders)
- **Sum Insured**: Up to $90 / season (Input cost coverage)

**Platform**: HewaSense™ - Tanzania Climate Intelligence & Parametric Insurance Platform

---

## Payout Model

### Fixed Payout Rates (USD)

**FINAL CALIBRATED RATES** (Effective Jan 2026):

| Trigger Type            | Payout                                        | Rationale                       |
| ----------------------- | --------------------------------------------- | ------------------------------- |
| **Drought**       | $60 | Market rate aligned with Pula (~$50-70) |                                 |
| **Flood**         | $75                                           | 25% premium for higher risk     |
| **Crop Failure**  | $90                                           | Critical impact, highest payout |
| **Severe Stress** | $45                                           | Supplementary coverage          |

**Coverage**: 0.5 hectare per farmer (typical smallholder size)

### Historical Performance (2000-2025)

- **Total Events**: 610 over 26 years
- **Drought**: 224 events (12.0% trigger rate)
- **Flood**: 175 events (9.3% trigger rate)
- **Crop Failure**: 117 events (6.2% trigger rate)
- **Severe Stress**: 94 events (5.0% trigger rate)

---

## Financial Sustainability

### 26-Year Historical Analysis

**Total Payouts**: $41,325
**Average Payout**: $68/event
**Annual Payouts**: $1,590/year (avg 23.5 events/year)

### Premium Structure (100-farmer pilot)

- **Annual Premium Total**: $1,988
- **Per-Farmer Premium**: $20/year
- **With 50% Government Subsidy**: **$10/year**
- **Loss Ratio**: 75% (target: 60-80%) ✅

### Sustainability Metrics

| Metric               | Value    | Status                       |
| -------------------- | -------- | ---------------------------- |
| Loss Ratio           | 75%      | ✅ Sustainable (target <80%) |
| Premium/Payout Ratio | 1:3.1    | ✅ Adequate coverage         |
| Subsidy Requirement  | 50%      | ✅ Manageable for government |
| Farmer Affordability | $10/year | ✅ ~2 days' wages            |

---

## Competitive Analysis

### Apples-to-Apples Comparison (0.5 hectare)

| Program               | Premium                            | Max Payout           | Perils             | Location          |
| --------------------- | ---------------------------------- | -------------------- | ------------------ | ----------------- |
| **Pula Zambia** | $6/year | $25                      | 1 (drought)          | Zambia             |                   |
| **KLIP Kenya**  | N/A                                | $10/animal           | 1 (drought)        | Kenya (livestock) |
| **ACRE Kenya**  | $8/year | $40                      | 1-2 (D/F)            | Kenya              |                   |
| **TCI (Ours)**  | **$10/year** | **$90** | **3 (D/F/CF)** | **Tanzania** |                   |

### Value Proposition

**vs Pula Zambia** (most comparable):

- **Price**: $10 vs $6 (+67% more)
- **Payout**: $90 vs $25 (+260% more)
- **Perils**: 3 vs 1 (+200% more)
- **Value Score**: **3.6x better payout-to-price ratio**

---

## Evolution History

### Iteration 1: Variable Model (Rejected)

```python
payout = base_payout * (0.5 + severity) * confidence
```

- **Problem**: Semi-parametric, not regulatory compliant
- **Result**: $271 avg payout (too variable)
- **Status**: ❌ Rejected

### Iteration 2: Fixed Premium Model (Rejected)

```python
PAYOUT_RATES = {"drought": 400, "flood": 500, "crop": 600}
```

- **Problem**: 11x more expensive than competitors
- **Result**: $66/year premium (unaffordable)
- **Status**: ❌ Rejected

### Iteration 3: Market-Competitive (Final) ✅

```python
PAYOUT_RATES = {"drought": 60, "flood": 75, "crop": 90}
```

- **Result**: $10/year premium (competitive)
- **Status**: ✅ **PILOT-READY**

### Iteration 4: Phase-Based Precision (Jan 23, 2026) ✅

Aligned triggers with **Rice Growth Phases** (Germination, Vegetative, Flowering, Maturity).

- **Benefit**: Removes "basis risk" by ensuring payouts match biological reality (e.g., critical flowering deficits).
- **Implementation**: Fixed rules applied to variable forecasts.

---

## Trigger Detection Methodology

### Two-Step Process

The system uses a **scientific, objective approach** to determine when payouts occur:

#### Step 1: Climate Variable Prediction

Machine learning models forecast actual climate variables for the next 3-6 months:

- **Rainfall** (mm): Predicted using ensemble regression models (Random Forest, Gradient Boosting, XGBoost)
- **NDVI**: Vegetation health index from satellite data
- **Soil Moisture** (%): Predicted from ERA5 climate data

**Model Performance**:

- R² Score: 0.8666 (XGBoost, primary serving model); Ensemble: 0.840
- Spatial Cross-Validation: 84.6% accuracy (XGBoost temporal CV)
- 6-month forecasting horizon

#### Step 2: Threshold Comparison

Forecasted climate values are compared to calibrated thresholds:

**Drought Detection**:

```
IF predicted_rainfall < 120mm for 30 days (SPI-30 < -0.60)
THEN trigger = "drought" → Payout = $60
```

**Flood Detection**:

```
IF predicted_daily_rainfall > 258mm AND 7-day_rainfall > 1,169mm
THEN trigger = "flood" → Payout = $75
```

**Crop Failure Detection**:

```
IF predicted_NDVI < -1.56σ OR predicted_VCI < 3.33
THEN trigger = "crop_failure" → Payout = $90
```

#### Step 3: Phase-Based Logic (The "Decider")

**Crucial Distinction**: The insurance payout is determined by a **Phase-Based Logic Layer** that sits on TOP of the ML forecasts.

* **ML Models** (Step 1): Predict rainfall/NDVI.
* **Phase Logic** (Step 3): Checks if the prediction breaches the threshold for the *specific biological phase* (e.g., Flowering).

> **Note**: You do NOT need to retrain ML models to adjust these rules. The logic is parametric (rule-based).

### Why This Approach?

**Regulatory Compliance**: Thresholds are fixed, transparent, and disclosed upfront (true parametric insurance)

**Scientific Rigor**: Climate variables are objective, measurable, and verifiable

**No Claims Process**: Payout is automatic when threshold is breached—no loss adjustment, no disputes

**Farmer-Friendly**: Simple to understand: "If rainfall forecast shows less than 120mm, you get $60"

---

## Implementation Details

### Code Locations

**Payout Rates (backend)**:

```python
# backend/app/api/forecasts.py (also mirrored in frontend)
PAYOUT_RATES = {
    "drought": 60,
    "flood": 75,
    "crop_failure": 90,
}
PILOT_FARMERS = 1000
# Expected payout = PILOT_FARMERS × probability × PAYOUT_RATES[trigger_type]
```

**Horizon tier enforcement**:

- `backend/app/config/rice_thresholds.py` — `HORIZON_TIERS = {3:"primary", 4:"primary", 5:"advisory", 6:"advisory"}` + `get_horizon_tier()`
- `backend/app/api/forecasts.py` — `/forecasts/portfolio-risk` filters `horizon_months <= 4`
- `backend/app/api/risk.py` — `/risk/portfolio` filters `horizon_months <= 4`
- `frontend/src/pages/ForecastDashboard.tsx` — `generateFinancialProjections()` + `highestRiskForecast` both enforce `horizonMonths <= 4 && probability >= 0.75`
- `frontend/src/components/FinancialForecastChart.tsx` — subtitle and annotation label reflect primary/advisory split

**Configuration**:

```python
USE_TIERED_PAYOUTS = False  # True parametric (fixed rates, not tiered)
```

---

## Pilot Deployment Parameters

### Target Specifications (Updated: Jan 2026)

- **Location**: Morogoro Region, Kilombero Basin
- **Farmers**: 1,000 smallholder rice farmers
- **Crop**: Rice (intensive cultivation area)
- **Coverage**: ~500 hectares total (0.5 ha per farmer)
- **Timeline**: Q1 2026 launch
- **Duration**: 12-month pilot

**Rationale for Kilombero Basin**:

- Major rice-producing region in Tanzania
- High climate vulnerability (floods + droughts)
- Existing farmer cooperatives for distribution
- Good data coverage for model validation

### Budget Requirements

**Per-Farmer Costs**:

- Premium: $20/year
- Government subsidy (50%): $10/farmer
- Total farmer cost: $10/year

**1,000-Farmer Pilot (Morogoro)**:

- Total premiums: $20,000/year
- Government subsidy: $10,000/year
- Expected payouts: ~$15,900/year (historical avg scaled)
- Net sustainability: Positive with reserves

---

## Regulatory Compliance

### TIRA (Tanzania Insurance Regulatory Authority)

✅ **Parametric Insurance Standards Met**:

- Fixed payout schedule (disclosed upfront)
- Objective triggers (no loss adjustment)
- Clear policy terms
- No claims process required

### Policy Documentation

**Farmer-Facing Language** (Updated for Climate Pivot):

> "Our weather prediction system forecasts rainfall for the next 6 months.
> If the forecast shows **drought conditions** (less than 120mm rainfall for 30 days), you automatically receive **$60**.
> If the forecast shows **flood risk** (more than 258mm in one day + heavy weekly rain), you receive **$75**.
> If satellite data shows **crop stress** (vegetation health below normal), you receive **$90**.
> No waiting, no claims forms—just automatic protection."

**Legal Contract**: Fixed payout amounts based on objective climate forecasts exceeding/falling below predetermined thresholds. No loss adjustment required.

---

## Technical Validation

### Data Quality

- **Historical Period**: 26 years (2000-2025)
- **Locations**: 6 (Arusha, Dar es Salaam, Dodoma, Mbeya, Mwanza, Morogoro)
- **Records**: 1,872 monthly observations
- **Trigger Events**: 610 (32.6% of records)

### Threshold Calibration (Climate Variables)

- **Drought Threshold**: Forecasted rainfall < 120mm/30days (SPI-30 < -0.60) → 12.0% historical trigger rate
- **Flood Threshold**: Forecasted daily >258mm AND 7-day >1,169mm → 9.3% historical trigger rate
- **Crop Failure Threshold**: Forecasted VCI <3.33 OR NDVI <-1.56σ → 6.2% historical trigger rate

*These thresholds were calibrated using 26 years of historical data (2000-2025) to achieve sustainable trigger rates.*

### Climate Prediction Model Performance

- **Rainfall Forecast R²**: 0.8666 (XGBoost, primary serving model; Ensemble: 0.840)
- **Temporal Cross-Validation**: 84.6% (validated across 5 temporal CV folds)
- **Forecast Horizon**: 3-6 months ahead
- **Data Leakage**: Prevented and validated ✅

*The ML model predicts climate variables (rainfall, NDVI), which are then compared to the calibrated thresholds above to determine if a trigger/payout occurs.*

### Horizon Tiers (Enforced in Code)

| Tier               | Horizon     | Threshold          | Status                                           |
| ------------------ | ----------- | ------------------ | ------------------------------------------------ |
| **Primary**  | ≤ 4 months | ≥ 75% probability | Payout-eligible — counted in financial exposure |
| **Advisory** | 5–6 months | ≥ 50% probability | Early warning only — never triggers payout      |

**Why Advisory Never Triggers**: 5-6 month forecasts carry higher uncertainty. Labelling them advisory prevents premature reserve earmarking while still surfacing emerging risk to operations teams.

### Portfolio Risk Monitoring Logic

- **"Farmers at Risk" Metric**: Policyholders in locations where **primary-tier** (horizon ≤ 4 months) forecast probability ≥ **75%** (Severe Risk).
- **Rationale**: The 75% threshold ensures reserves are only earmarked for high-confidence, near-certain payout events (≥1-in-4 year severity), aligning with TIRA-compliant parametric insurance practice.
- **Expected Payout Formula**: `PILOT_FARMERS × probability × payout_rate_per_farmer`
  - Example (drought at 52.6%): 1,000 × 0.526 × $60 = $31,560
  - Affected farmers = total farmers × probability (not a binary all-or-nothing count)
- **Deduplication Rule**: When multiple pipeline runs target the same calendar month, the system takes **MAX probability per trigger_type × month**. This prevents double-counting if two runs both forecast drought in September.
- **Code enforcement**:
  - Backend `/api/forecasts/portfolio-risk`: `Forecast.horizon_months <= 4` filter applied before aggregation
  - Backend `/api/risk/portfolio`: same `horizon_months <= 4` guard
  - Frontend `generateFinancialProjections()`: deduplicates by `triggerType|monthName` (MAX probability), primary tier only
  - Frontend `locationRisk` (map tooltip): uses `portfolioRisk.expectedPayouts` from backend — not re-accumulated on the client

---

## Risk Analysis

### Downside Risks

1. **Higher-than-expected trigger rates**: 75% loss ratio leaves only 5% buffer

   - **Mitigation**: 26-year calibration provides confidence
2. **Climate change acceleration**: Historical rates may not hold

   - **Mitigation**: Annual recalibration process
3. **Farmer uptake lower than expected**: Fixed costs diluted

   - **Mitigation**: Start with 100-farmer minimum

### Upside Opportunities

1. **Lower trigger rates**: 75% loss ratio → profits for sustainability
2. **Scale economies**: >500 farmers → reduce subsidy need
3. **Multi-peril value**: Attracts more farmers than single-peril competitors

---

## Milestone Tracker (Updated: March 15, 2026)

### Phase 1 — Technical Foundation (Complete)

1. ✅ ML pipeline deployed — XGBoost V4.0 (R²=0.8666, 83 clean features, zero data leakage)
2. ✅ Dashboard live — 5 views (Early Warning, Executive Snapshot, Climate Insights, Historical Validation, Evidence Pack)
3. ✅ Automated daily ingestion — CHIRPS, NASA POWER, ERA5, NDVI, Ocean Indices
4. ✅ Parametric trigger logic validated — calibrated thresholds in `configs/trigger_thresholds.yaml`
5. ✅ Payout calculation validated — per-farmer fixed rates, primary-tier only, deduplication enforced (Mar 15)
6. ✅ JWT auth, health checks, Slack alerts operational

### Phase 2 — Shadow Run (Mar 7 – Jun 5, 2026) 🔄 ACTIVE — Day 9 of 90

> **Purpose**: 90-day forward validation. Pipeline runs daily at 06:00 EAT. No real payouts during this phase — forecasts are logged and evaluated against actual observations to build the evidence pack for reinsurers and TIRA.

**Current state (as of Mar 15, 2026):**

- ✅ Pipeline executing daily since Mar 9 (Mar 7–8 missed due to scheduler timezone bug — fixed)
- ✅ 12 forecasts/run: drought × 4 horizons + flood × 4 horizons + heat_stress × 4 horizons
- ✅ `ForecastLog` evidence pack: `threshold_used` (0.65/0.60) + `forecast_distribution` (horizon_tier, insurance_eligible, confidence bounds) populated on every entry
- ✅ `horizon_months <= 4` guard enforced in both backend endpoints — advisory tier never enters financial exposure
- ⏳ ForecastLog entries status: all `pending` — validity windows are 3–6 months ahead; auto-evaluation begins ~Jun 8
- ⏳ 90-day evidence pack compilation (metrics.json + logs_export.csv + model_compliance_statement.txt)

### Phase 3 — Go-Live Decision (June 2026) ⏳ PENDING

> Gate criteria: Brier Score < 0.25 AND Basis Risk < 30%

- ⏳ Shadow run debrief — predicted vs actual trigger alignment
- ⏳ TIRA regulatory submission with evidence pack
- ⏳ Reinsurer review
- ⏳ Go/No-Go: live payouts authorised OR shadow run extended + model retrained on 2026 data

### Phase 4 — Live Pilot (Q3 2026+, contingent on Phase 3 gate)

- ⏳ TIRA approval confirmed
- ⏳ Government subsidy MOU signed (50% commitment)
- ⏳ Farmer education materials distributed (Kilombero Basin cooperatives)
- ⏳ Enrol 1,000 farmers — collect premiums ($10/farmer after subsidy)
- ⏳ First live payout issued within 5–7 days of confirmed primary-tier trigger
- ⏳ Measure farmer satisfaction + calculate actual loss ratio
- ⏳ Prepare scale-up plan for 2027

### Phase 5 — Q2 2026 Technical Enhancements (Parallel Track)

- ⏳ Soil moisture dual-index trigger: backfill ERA5 2020–2025 → retrain → calibrate (1–2 weeks)
- ⏳ Kilombero Basin geographic sub-zones: ingest North/Central/South coordinates → add Location records

---

## Success Criteria

### Shadow Run (Jun 2026 gate)

- Brier Score < 0.25 on evaluated forecasts
- Basis risk < 30% (predicted vs actual trigger alignment)
- ≥90 consecutive daily pipeline runs with no data-integrity failures
- Zero forecasts from non-primary model (XGBoost V4.0 only)

### Live Pilot Financial

- Loss ratio stays 50–85%
- 70%+ farmers renew for Year 2
- Government subsidy maintained at 50%

### Live Pilot Operational

- Payout delays < 7 days from confirmed primary-tier trigger
- Zero disputed payouts (parametric = automatic, objective threshold)
- Dashboard uptime > 99%

### Impact

- Farmers protected from climate shocks in Kilombero Basin
- Evidence pack accepted by reinsurer as operational reliability proof
- Model replicable for national scale-up post-2026

---

## References

- [Insurance Trigger Recalibration](./INSURANCE_TRIGGER_RECALIBRATION_SUMMARY.md)
- [6-Location Expansion](./6_LOCATION_EXPANSION_SUMMARY.md)
- [Pula Zambia Case Study](https://www.pula-advisors.com)
- [KLIP Kenya Program](https://www.ilri.org/research/projects/kenya-livestock-insurance-programme-klip)

---

**Document Owner**: Climate Prediction & Insurance Team
**Last Updated**: March 15, 2026
**Next Review**: June 2026 (post 90-day shadow run — review against Brier Score results)

---

## Changelog

| Date         | Change                                                                                                                                                                                                                                                                                                                                                                      |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Mar 15, 2026 | Added Horizon Tiers section. Corrected payout formula to per-farmer fixed rate (`PILOT_FARMERS × probability × rate`). Added deduplication rule (MAX probability per trigger_type × month). Updated code locations to reflect backend + frontend enforcement. Fixed double-counting bug: advisory tier (5-6 month forecasts) no longer included in financial exposure. |
| Mar 9, 2026  | Updated Next Review date. Initial shadow run doc sweep.                                                                                                                                                                                                                                                                                                                     |
| Jan 23, 2026 | Phase-based precision iteration added.                                                                                                                                                                                                                                                                                                                                      |
| Jan 1, 2026  | Version 3.0 — market-competitive rates finalised.                                                                                                                                                                                                                                                                                                                          |
