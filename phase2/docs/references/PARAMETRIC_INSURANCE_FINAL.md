# True Parametric Insurance - Final Implementation

**Date**: March 15, 2026
**Status**: 🔄 SHADOW RUN ACTIVE (Mar 7 – Jun 12, 2026 revised) — Live pilot pending late June 2026 gate
**Version**: 4.0 (Phase-Based + Horizon Tiers)

---

## Executive Summary

Implemented true parametric insurance with market-competitive rates aligned with successful African programs (Pula Zambia, KLIP Kenya, IBLI Ethiopia). The system provides multi-peril coverage (drought, flood, crop failure) at affordable rates while maintaining financial sustainability.

**Key Achievement**: Reduced sustainable premium from **$91/year** (Lump Sum Model) to **$20/year** (Phase-Based Model) without requiring heavy subsidies. This was achieved by moving from binary "all-or-nothing" payouts to weighted, phase-specific coverage.

## 1. Product Summary

- **Type**: Multi-Peril Parametric Insurance (Drought + Flood + Crop Failure)
- **Target**: Smallholder Rice Farmers (0.5 - 2 hectares)
- **Region**: Kilombero Basin (Morogoro)
- **Premium**: **$20 / season** (Affordable for smallholders)
- **Sum Insured**: Up to $90 / season (Input cost coverage)

**Platform**: HewaSense™ - Tanzania Climate Intelligence & Parametric Insurance Platform

---

## Payout Model

### Fixed Payout Rates (USD)

**FINAL CALIBRATED RATES** (Effective Jan 2026):

| Trigger Type            | Payout | Rationale                                |
| ----------------------- | ------ | ---------------------------------------- |
| **Drought**       | \$60   | Market rate aligned with Pula (~\$50-70) |
| **Flood**         | \$75   | 25% premium for higher risk              |
| **Crop Failure**  | \$90   | Critical impact, highest payout          |
| **Severe Stress** | \$45   | Supplementary coverage                   |

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
- **Per-Farmer Premium (full)**: $20/year
- **Loss Ratio**: 75% (target: 60-80%) ✅

#### Premium Scenarios and Funding Pathways

| Scenario | Subsidy Source | Subsidy % | Farmer Pays | Break-Even Farmers |
|----------|---------------|-----------|-------------|-------------------|
| **A — No subsidy** | None (self-sustaining) | 0% | **$20/year** | ~10,000 |
| **B — Donor / NGO grant** | GSMA, GIZ, USAID, WFP, etc. | ~40% | **~$12/year** | ~2,000 |
| **C — Government subsidy** | Ministry of Agriculture MOU | 50% | **$10/year** | ~2,000 |

> **Scenario A** is the honest, no-subsidy baseline; it requires large scale to be self-sustaining. **Scenario B** is the realistic near-term pathway — donor or NGO co-funding is well-documented in African agricultural insurance programmes (Pula, ACRE Africa). **Scenario C** is a 3–5 year policy horizon scenario. Tanzania's **TAIS (Tanzania Agriculture Insurance Scheme)**, launched July 2023, explicitly designates government premium subsidies as part of its mandate. UNDP Tanzania is actively developing the smart subsidy business case for TAIS (RFP issued 2024) — meaning the architecture is being designed but is not yet operationally available. This scenario must not be treated as a near-term assumption; it is a credible medium-term alignment target as TAIS matures.

> **Note on loss ratio arithmetic:** The $1,590/year aggregate payout figure above spans all six training locations. The 75% loss ratio is calibrated for the Morogoro pilot location specifically. Dividing the 6-location aggregate ($1,590) by the single-location pilot premium ($1,988) yields ~80% — a multi-location artefact, not the pilot loss ratio. The Morogoro calibration iterated thresholds against 26 years of location-specific data to reach 75%.

### Sustainability Metrics

| Metric               | Value    | Status                       |
| -------------------- | -------- | ---------------------------- |
| Loss Ratio           | 75%      | ✅ Sustainable (target <80%) |
| Premium/Payout Ratio | 1:3.1    | ✅ Adequate coverage         |
| Subsidy Requirement  | 0% (Scenario A) / ~40% donor (B) / 50% govt (C) | A=self-sustaining at scale; B=near-term realistic; C=policy goal |
| Farmer Affordability | $20 (A) / ~$12 (B) / $10 (C) | B/C ≈ 1–2 days' wages ✅; A viable at scale |

---

## Competitive Analysis

### Apples-to-Apples Comparison (0.5 hectare)

| Program               | Premium             | Max Payout     | Perils                                 | Location           |
| --------------------- | ------------------- | -------------- | -------------------------------------- | ------------------ |
| **Pula Zambia** | \$6/year            | \$25           | Drought                                | Zambia             |
| **KLIP Kenya**  | N/A                 | \$10/animal    | Drought                                | Kenya (livestock)  |
| **ACRE Kenya**  | \$8/year            | \$40           | Drought, Flood                         | Kenya              |
| HewaSense             | **\$10–\$20/year** | **\$90** | **Drought, Flood, Crop Failure** | **Tanzania** |

> HewaSense premium shown as range reflecting the three funding scenarios (A: $20 no-subsidy; B: ~$12 donor grant; C: $10 govt subsidy). See Premium Scenarios table above.

### Value Proposition

**vs Pula Zambia** (most comparable, Scenario C at $10):

- **Price**: $10 vs $6 (+67% more)
- **Payout**: $90 vs $25 (+260% more)
- **Perils**: 3 vs 1 (+200% more)
- **Value Score**: **3.6x better payout-to-price ratio**

> At Scenario A ($20/year, no subsidy): 1.5x price vs Pula with a 3.1x payout advantage — still strong value given multi-peril coverage.

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

### Iteration 3: Market-Competitive Rates (Jan 2026) ✅

```python
PAYOUT_RATES = {"drought": 60, "flood": 75, "crop": 90}
```

- **Result**: $10/year premium (competitive)
- **Status**: ✅ In production

### Iteration 4: Phase-Based Precision (Jan 23, 2026) ✅

Aligned triggers with **Rice Growth Phases** (Germination, Vegetative, Flowering, Maturity).

- **Benefit**: Removes "basis risk" — payouts match biological reality (e.g., critical flowering deficits)
- **Implementation**: Fixed rules applied to variable forecasts
- **Status**: ✅ In production

### Iteration 5: Horizon Tier Enforcement (Mar 15, 2026) ✅

Enforced primary/advisory tier split throughout backend and frontend.

- **Primary** (≤4mo, ≥75%): payout-eligible — counted in all financial exposure calculations
- **Advisory** (5-6mo, ≥50%): early warning only — never triggers payout or reserve earmarking
- **Deduplication**: MAX probability per `triggerType×month` prevents double-counting from multiple pipeline runs
- **Status**: ✅ In production (shadow run)

---

## Trigger Detection Methodology

### Two-Step Process

The system uses a **scientific, objective approach** to determine when payouts occur:

#### Step 1: Climate Variable Prediction

The primary serving model (XGBoost V4.0) forecasts actual climate variables for the next 3-6 months:

- **Rainfall** (mm): XGBoost primary model (83 features, post-leakage fix)
- **NDVI**: Vegetation health index from satellite data (MODIS)
- **Soil Moisture** (%): Planned Q2 2026 — ERA5/NASA POWER backfill required before activation

**Model Performance** (as of Mar 5, 2026 training):

- R² Score: 0.8666 (XGBoost, **only model used for live forecasts**); Ensemble: 0.840 (training reference)
- Temporal Cross-Validation: 84.6% (5-fold, no look-ahead bias)
- Forecast Horizon: 3–6 months (4 horizons: 3mo, 4mo, 5mo, 6mo)
- LSTM and Random Forest: training reference only — not used in production

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
# Reserve sizing (while forecast is outstanding): PILOT_FARMERS × probability × PAYOUT_RATES[trigger_type]
# Confirmed payout (when trigger is observed): PILOT_FARMERS × PAYOUT_RATES[trigger_type]  ← binary, all enrolled farmers
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

### Target Specifications (Updated: Mar 2026)

- **Location**: Morogoro Region, Kilombero Basin
- **Farmers**: 1,000 smallholder rice farmers (target; enrolment pending Phase 3 gate)
- **Crop**: Rice (intensive cultivation area)
- **Coverage**: ~500 hectares total (0.5 ha per farmer)
- **Current Phase**: Shadow Run ACTIVE (Mar 7 – Jun 12, 2026 revised) — technical validation, no live payouts
- **Live Pilot Timeline**: Q3 2026+ contingent on June 2026 go-live gate (Brier Score < 0.25)
- **Duration**: 12-month pilot once live

**Rationale for Kilombero Basin**:

- Major rice-producing region in Tanzania
- High climate vulnerability (floods + droughts)
- Existing farmer cooperatives for distribution
- Good data coverage for model validation

### Budget Requirements

**Per-Farmer Costs (by scenario)**:

| Scenario | Full Premium | Subsidy Source | Farmer Pays |
|----------|-------------|----------------|-------------|
| A — No subsidy | $20/year | None | $20/year |
| B — Donor/NGO | $20/year | ~40% grant | ~$12/year |
| C — Government | $20/year | 50% MOU | $10/year |

**1,000-Farmer Pilot (Morogoro)**:

- Total premiums collected: $20,000/year (full premium regardless of scenario)
- External co-funding (Scenario B): ~$8,000/year donor/NGO grant
- External co-funding (Scenario C): $10,000/year government subsidy
- Expected payouts: ~$15,900/year (historical avg scaled)
- Net sustainability: Positive with reserves across all three scenarios

> **Funding source note**: Scenario B (donor/NGO) is the recommended near-term target. Approach GSMA M4D, GIZ, USAID, WFP, or IFAD — all have active agricultural insurance co-funding programmes in East Africa.

---

## Regulatory Compliance

### TIRA (Tanzania Insurance Regulatory Authority)

**Design Compliance** (pending formal TIRA submission with evidence pack — Phase 3):

- ✅ Fixed payout schedule (disclosed upfront, transparent rates)
- ✅ Objective triggers (no loss adjustment, no claims form)
- ✅ Clear policy terms (parametric = automatic payout on threshold breach)
- ✅ No claims process required
- ⏳ Formal TIRA submission — scheduled for June 2026 with shadow run evidence pack

### Policy Documentation

**Farmer-Facing Language** (Updated for Climate Pivot):

> "Our system monitors rainfall and satellite data every day.
> If actual rainfall falls below 120mm during your crop's growing season (**drought**), you automatically receive **$60**.
> If rainfall exceeds the flood threshold during your season (**flood**), you receive **$75**.
> If satellite data confirms your crop zone is under stress (**crop failure**), you receive **$90**.
> Every enrolled farmer in the zone receives the same payout. No waiting, no claim forms — just automatic protection when the conditions are objectively confirmed."

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
- **Reserve Sizing Formula**: `PILOT_FARMERS × probability × payout_rate_per_farmer`
  - Example (drought at 52.6%): 1,000 × 0.526 × $60 = $31,560 earmarked in reserve while forecast is pending
  - This is a **financial reserve metric**, not an indicator of which farmers get paid
- **Confirmed Payout (binary)**: When observed data confirms the threshold was breached → ALL enrolled farmers in the zone receive the fixed rate. If the threshold is not breached → no payout.
  - Example (drought confirmed): 1,000 × $60 = $60,000 distributed to all enrolled Morogoro farmers
  - The zone-level index applies equally to all enrolled farmers — no individual farm assessment, no partial payouts based on probability
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
2. **Scale economies**: >500 farmers → approach break-even without subsidy (Scenario A viable)
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

### Phase 2 — Shadow Run 🔄 ACTIVE — Day 21 of 90 valid run-days (252/1,080 forecasts, 23.3%)

> **Purpose**: 90 valid-run-day forward validation (= 1,080 ForecastLog entries at 12/day). Pipeline runs daily at 06:00 EAT. No real payouts during this phase — forecasts are logged and evaluated against actual observations to build the evidence pack for reinsurers and TIRA.

**Run schedule:**

- **Nominal start**: Mar 7, 2026
- **First correct run**: Mar 9, 2026 (Mar 7 started late; Mar 8 missed — scheduler timezone bug, fixed)
- **Additional missed days**: 5 (pipeline failures post-Mar 9) — total missed: 7
- **Nominal end**: Jun 5, 2026 — extended by 7 days to compensate
- **Revised end date**: **Jun 12, 2026** (to achieve 90 valid run-days = 1,080 entries)
- **Brier Score auto-evaluation**: begins ~Jun 9 when first 3-month forecasts (issued ~Mar 9) mature

**Current state (as of Mar 15, 2026):**

- ✅ Pipeline executing daily since Mar 9 (scheduler TZ bug fixed Mar 8)
- ✅ 12 forecasts/run: drought × 4 horizons + flood × 4 horizons + heat_stress × 4 horizons
- ✅ `ForecastLog` evidence pack: `threshold_used` (0.65/0.60) + `forecast_distribution` (horizon_tier, insurance_eligible, confidence bounds) populated on every entry
- ✅ `horizon_months <= 4` guard enforced in both backend endpoints — advisory tier never enters financial exposure
- ⏳ ForecastLog entries status: all `pending` — validity windows are 3–6 months ahead; auto-evaluation begins ~Jun 9
- ✅ 90-day evidence pack compilation automated — orchestrator Stage 5 detects completion, generates `shadow_run_final_report.json` (Brier Score + NDVI proxy basis risk), sends Slack go/no-go alert. API: `GET /api/v1/evidence-pack/final-report`
- ✅ NDVI proxy basis risk automated — `basis_risk_service.py` joins `forecast_logs` × `ndvi_observations` by month; primary-tier drought/crop_failure triggers corroborated by NDVI anomaly < -0.05. API: `GET /api/v1/evidence-pack/basis-risk`

### Phase 3 — Go-Live Decision (Late June 2026) ⏳ PENDING

> Gate criteria: Brier Score < 0.25 AND Basis Risk < 30%
> Timing: shadow run completes Jun 12 → evidence pack compiled → debrief ~Jun 15–20

- ⏳ Shadow run debrief — predicted vs actual trigger alignment
- ⏳ TIRA regulatory submission with evidence pack
- ⏳ Reinsurer review
- ⏳ Go/No-Go: live payouts authorised OR shadow run extended + model retrained on 2026 data

### Phase 4 — Live Pilot (Q3 2026+, contingent on Phase 3 gate)

- ⏳ TIRA approval confirmed
- ⏳ External funding arrangement confirmed (Scenario B: donor/NGO grant ~40%, OR Scenario C: government MOU 50% — Scenario A self-sustaining at scale also viable)
- ⏳ Farmer education materials distributed (Kilombero Basin cooperatives)
- ⏳ Enrol 1,000 farmers — collect premiums ($10–$20/farmer depending on funding scenario)
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
- External funding maintained (Scenario B: donor grant renewed; Scenario C: government subsidy; Scenario A: break-even through scale)

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
**Last Updated**: March 21, 2026
**Next Review**: Late June 2026 (post 90 valid-run-day shadow run — review against Brier Score results; shadow run extended to Jun 12 to compensate for 7 missed days)

---

## Changelog

| Date         | Change                                                                                                                                                                                                                                                                                                                                                                      |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Mar 21, 2026 | Replaced single-subsidy assumption with three-scenario model (A: no subsidy/$20; B: donor ~40%/~$12; C: govt 50%/$10). Updated Premium Structure, Sustainability Metrics, Competitive Analysis, Budget Requirements, Phase 4 milestones, and success criteria to reflect scenario-aware language. |
| Mar 15, 2026 | Added Horizon Tiers section. Corrected payout formula to per-farmer fixed rate (`PILOT_FARMERS × probability × rate`). Added deduplication rule (MAX probability per trigger_type × month). Updated code locations to reflect backend + frontend enforcement. Fixed double-counting bug: advisory tier (5-6 month forecasts) no longer included in financial exposure. |
| Mar 9, 2026  | Updated Next Review date. Initial shadow run doc sweep.                                                                                                                                                                                                                                                                                                                     |
| Jan 23, 2026 | Phase-based precision iteration added.                                                                                                                                                                                                                                                                                                                                      |
| Jan 1, 2026  | Version 3.0 — market-competitive rates finalised.                                                                                                                                                                                                                                                                                                                          |
