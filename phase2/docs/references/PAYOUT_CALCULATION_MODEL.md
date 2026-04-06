# Insurance Payout Calculation Model — Production Reference

**Date:** March 15, 2026
**Version:** 2.0 (Production — all fixes implemented)
**Context:** Morogoro Rice Pilot (1,000 farmers, Kilombero Basin)
**Status:** ✅ Implemented & Deployed — Shadow Run ACTIVE (Mar 7 – Jun 12, 2026)

---

## Overview

This document describes the **implemented and deployed** payout calculation model for the HewaSense parametric insurance pilot. All formula bugs documented in v1.0 (January 2026) have been resolved. This document supersedes the original problem-analysis draft.

---

## Two-Stage Payout Mechanism

Payout logic operates in two distinct stages. These must not be conflated.

### Stage 1 — Reserve Sizing (During Forecast Period)

```
Expected Exposure = PILOT_FARMERS × probability × rate_per_farmer
```

**Purpose:** Financial reserve management. Used to earmark capital against future liability while a forecast is outstanding.

**Where:**
- `PILOT_FARMERS = 1,000` (Kilombero Basin smallholder rice farmers)
- `probability` = XGBoost trigger probability for that horizon/trigger combination
- `rate_per_farmer` = fixed rate from pilot specification (see table below)

**Example — Drought forecast at 87.4% probability:**
```
Expected Exposure = 1,000 × 0.874 × $60 = $52,440 earmarked in reserve
```

This does NOT mean 874 farmers receive $60. It means $52,440 is held as the probability-weighted liability while the forecast is pending confirmation.

### Stage 2 — Confirmed Payout (When Trigger Is Observed)

```
Confirmed Payout = PILOT_FARMERS × rate_per_farmer   (if trigger fires)
Confirmed Payout = $0                                  (if trigger does not fire)
```

**The trigger is binary.** When observed climate data confirms that the threshold was breached (e.g., actual rainfall < 120mm during the covered period):

- **ALL enrolled farmers in the zone receive the fixed rate**
- No individual farm assessment is made
- No distinction is drawn between farmers whose fields were more or less affected

**Example — Drought trigger confirmed:**
```
Confirmed Payout = 1,000 × $60 = $60,000 distributed to all enrolled farmers
```

**Design rationale (Option A):** Zone-level index + binary trigger is the correct design for smallholder parametric insurance. The index is objective and pre-disclosed. The payout is equal across all enrolled farmers in the zone. This eliminates all basis risk from individual assessment — which is exactly what a claims process would introduce. A farmer pays $10 because the zone covers them equally, not because their individual loss was measured.

### Summary

| Stage | Formula | Purpose |
|---|---|---|
| Reserve sizing (forecast) | `PILOT_FARMERS × probability × rate` | Capital earmarked while forecast is pending |
| Confirmed payout (observed) | `PILOT_FARMERS × rate` if trigger fires, else $0 | Actual farmer payment on threshold breach |

---

## Payout Rates (Pilot Specification)

| Trigger Type | Rate per Farmer | Max Pool (1,000 farmers) |
|---|---|---|
| Drought | $60 | $60,000 |
| Flood | $75 | $75,000 |
| Crop Failure | $90 | $90,000 |

**Source:** `KILOMBERO_BASIN_PILOT_SPECIFICATION.md`

---

## Horizon Tier Enforcement (CRITICAL)

Payout eligibility is gated by horizon tier. This is enforced in code — advisory-tier forecasts **never** appear in financial exposure calculations.

| Tier | Horizon | Probability Gate | Payout Eligible |
|---|---|---|---|
| **Primary** | 3–4 months ahead | ≥ 75% | ✅ YES |
| **Advisory** | 5–6 months ahead | ≥ 50% | ❌ NO — early warning only |

**Code enforcement locations:**
- `backend/app/api/forecasts.py` — `portfolio-risk` endpoint filters `Forecast.horizon_months <= 4`
- `backend/app/api/risk.py` — `/api/risk/portfolio` same filter
- `frontend/src/pages/ForecastDashboard.tsx` — `generateFinancialProjections()` only processes primary-tier rows

---

## Multi-Run Deduplication Rule

When multiple pipeline runs target the same calendar month, payouts are deduplicated by **MAX probability** per `triggerType × calendar month`. Runs are never summed.

```
// Correct (implemented in generateFinancialProjections())
monthKey = `${triggerType}|${monthName}`
bucket[monthKey] = MAX(bucket[monthKey], probability)  // keep highest only

// Wrong (old behavior — fixed Mar 15, 2026)
bucket[monthKey] += probability  // double-counted across runs
```

**Why this matters:** Two pipeline runs both targeting September 2026 drought at 87.4% would have produced `$52,440 + $52,440 = $104,880` (2× correct). The dedup rule ensures it stays `$52,440`.

---

## Single Source of Truth for Payouts

All payout figures across the dashboard originate from one backend call:

```
GET /api/risk/portfolio  →  portfolioRisk.expectedPayouts
```

Frontend components **never** re-accumulate payouts from the raw `forecasts` array. Any component needing the expected payout total reads `portfolioRisk.expectedPayouts` directly.

**Applies to:**
- Portfolio Risk Overview panel
- Geographic Payout & Risk Distribution map tooltip
- Financial Forecast chart annotations

---

## Complete Payout Calculation Pipeline

```
XGBoost V4.0 (R²=0.8666, 83 features)
        ↓
Phase-Based Thresholds (50-80mm, conservative)
        ↓
Horizon Tier Gate (≤4 months = primary / 5-6 months = advisory)
        ↓
Confidence Gating (≥75% for primary / ≥50% for advisory)
        ↓
Deduplication (MAX probability per triggerType × calendar month)
        ↓
Payout Formula: PILOT_FARMERS × probability × rate_per_farmer
        ↓
Financial Exposure — PRIMARY TIER ONLY
```

---

## Threshold Reference

| Threshold Name | Value | Purpose |
|---|---|---|
| `MONITORING_THRESHOLD` | 30% | Internal monitoring only |
| `ADVISORY_THRESHOLD` | 50% | Advisory-tier trigger gate (5-6mo) |
| `WARNING_THRESHOLD` | 65% | Pre-alert warnings |
| `HIGH_RISK_THRESHOLD` | 75% | Primary-tier payout gate (3-4mo) |

---

## Capital Adequacy Validation

Using the correct formula (per-farmer model):

| Scenario | Calculation | Result |
|---|---|---|
| 100% crop failure | 1,000 × 1.0 × $90 | $90,000 max exposure |
| 87.4% drought | 1,000 × 0.874 × $60 | $52,440 |
| 75% flood | 1,000 × 0.75 × $75 | $56,250 |

**Pilot reserves:** $150,000
**Required reserves (100% CAR):** $90,000 (worst-case single event)
**Capital Adequacy Ratio:** 150,000 / 90,000 = **167% ✅ TIRA compliant**

---

## TIRA Compliance

| Requirement | Status |
|---|---|
| Fixed payout schedule ($60/$75/$90 per farmer) | ✅ Implemented |
| Objective triggers (rainfall thresholds) | ✅ Implemented |
| Transparent terms (disclosed upfront) | ✅ Documented |
| No loss adjustment (automatic payout) | ✅ Designed |
| Parametric guidelines (TIRA 2023) | ✅ Design-compliant — formal submission subject to mid-2026 Go/No-Go decision |

---

## Code Locations

| Constant / Function | File | Notes |
|---|---|---|
| `PAYOUT_RATES` | `backend/app/api/forecasts.py` | `{"drought": 60, "flood": 75, "crop_failure": 90}` |
| `PILOT_FARMERS` | `backend/app/api/forecasts.py` | `1000` |
| `horizon_months <= 4` filter | `backend/app/api/forecasts.py`, `backend/app/api/risk.py` | Advisory tier exclusion |
| `generateFinancialProjections()` | `frontend/src/pages/ForecastDashboard.tsx` | MAX-dedup + primary-only |
| `portfolioRisk.expectedPayouts` | `frontend/src/pages/ForecastDashboard.tsx` | Single source of truth for map tooltip |
| Horizon tier config | `backend/app/config/rice_thresholds.py` | `HORIZON_TIERS`, `get_horizon_tier()` |

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| 1.0 | Jan 19, 2026 | Initial problem analysis — identified $50,000 PAYOUT_UNIT bug, wrong formula |
| 2.0 | Mar 15, 2026 | **Supersedes v1.0.** All bugs fixed and deployed. Rewritten as production reference: correct formula, horizon tier enforcement, dedup rule, single source of truth, TIRA compliance table, code locations |

---

**References:**
- `docs/references/KILOMBERO_BASIN_PILOT_SPECIFICATION.md`
- `docs/references/PARAMETRIC_INSURANCE_FINAL.md`
- `docs/current/PARAMETRIC_INSURANCE_LOGIC.md` — Section 4: Horizon Tiers & Payout Eligibility
- `backend/app/config/rice_thresholds.py` — `HORIZON_TIERS`
- TIRA Parametric Insurance Guidelines 2023
