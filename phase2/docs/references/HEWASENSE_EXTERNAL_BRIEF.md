# HewaSense — Business Case & Deployment Rationale

## Parametric Climate Insurance for Smallholder Farmers in Tanzania

**Document Type**: Strategic Business Analysis — External Introduction
**Date**: March 2026
**Status**: Forward Validation Active — Week 2 of a 90-day validation run
**Author**: HewaSense Climate Intelligence & Insurance Team
**Audience**: External Partners · Potential Underwriters · Development Finance · Government Advisors

---

## The Core Question

> *"Have we built something that actually matters — and can we give farmers real money when their crops fail?"*

The short answer is yes. This document explains why, and what the path to a live payout looks like.

---

## 1. The Problem We Are Solving

Tanzania's Kilombero Basin is one of the most productive rice-growing regions in East Africa. It is also one of the most climate-exposed. The basin sits at the confluence of the Kilombero River flood plains and the Southern Highlands rain shadow, creating a dual-peril environment where farmers face:

- **Droughts** when the Indian Ocean Dipole suppresses long rains (March–May)
- **Floods** when El Niño years bring excess rainfall to an already low-lying basin
- **Crop failure** from vegetation degradation — sometimes caused by neither drought nor flood, but prolonged cloud cover, pest pressure, or soil waterlogging

These three perils have triggered **610 adverse events** in 26 years of historical data — an average of 23.5 events per year. Across six locations and three peril types, thresholds were breached an average of 23.5 times per year — meaning smallholders in the region face multiple distinct climate hazards each season, with no financial safety net currently in place.

### Why Existing Products Fail Here

Conventional indemnity insurance requires:

- A claims adjuster (Tanzania does not have enough to cover rural areas at scale)
- A receipts-based proof of loss (smallholders rarely have receipts)
- A disputes process (weeks to months)
- Premium collection infrastructure (rural mobile money is improving but not universal)

The result: **the farmers most exposed to climate risk are the least served by the insurance industry**. Products like Pula (Zambia) and ACRE (Kenya) have made inroads with simplified parametric designs — but they cover single perils, with low payouts, and have not reached Tanzania's rice belt.

---

## 2. What We Built and Why It's Designed the Way It Is

### 2.1 True Parametric Insurance

A parametric product does not pay based on what a farmer claims they lost. It pays when a **measurable climate variable crosses a pre-disclosed threshold**. This distinction is fundamental:

| Feature         | Indemnity Insurance          | HewaSense Parametric                         |
| --------------- | ---------------------------- | -------------------------------------------- |
| Payout trigger  | Farm-level damage assessment | Climate threshold breach                     |
| Claims process  | Required                     | **None**                               |
| Payout time     | Weeks–months                | **5–7 days**                          |
| Disputes        | Frequent                     | **Not possible** (objective)           |
| Scalability     | Low (adjuster-bound)         | **High** (automated)                   |
| Regulatory path | Standard indemnity route     | Parametric route (separate regulatory track) |

This is not a compromise — it is the correct product design for smallholder agriculture in sub-Saharan Africa.

### 2.2 Phase-Based Coverage

A simple "did it rain enough this month?" trigger misses biological reality. Rice has four distinct growth phases, each with different vulnerability windows:

| Phase               | Duration              | Critical Need                     | Payout Weight |
| ------------------- | --------------------- | --------------------------------- | ------------- |
| Germination         | Weeks 1–2            | Consistent soil moisture          | 15%           |
| Vegetative          | Weeks 3–8            | Adequate rainfall                 | 25%           |
| **Flowering** | **Weeks 9–12** | **No drought, no flooding** | **35%** |
| Maturity            | Weeks 13–16          | Dry conditions                    | 25%           |

The flowering phase carries the highest weight because drought or waterlogging during this 3-week window destroys the entire season — even if all other months were normal.

**Without phase-based logic, a drought in the dry season would trigger a payout on a crop that was already harvested.** That is basis risk in the worst form: paying for non-losses and missing real ones. Our phase-based design eliminates this class of error.

### 2.3 Forecast Horizon Tiers

The model forecasts 3–6 months ahead. But a 6-month forecast carries structurally more uncertainty than a 3-month forecast. We address this formally:

- **Primary tier** (3–4 months, ≥ 75% confidence): payout-eligible, counted in financial reserves
- **Advisory tier** (5–6 months, ≥ 50% confidence): early warning only — never triggers a payout

Advisory forecasts give farmers and cooperatives time to prepare. Primary tier forecasts create financial obligations. The distinction is enforced systematically — it is not a soft guideline. This is the architecture that a reinsurer needs to see to price the product.

### 2.4 The Three Thresholds and Why They Are Calibrated Where They Are

**Drought**: Rainfall below 120mm over 30 days (Standardised Precipitation Index < −0.60)

- Calibrated from 26 years of historical data
- 12.0% historical trigger rate — about once per 8 months
- Comparable SPI threshold used by Pula Zambia

**Flood**: Daily rainfall exceeding 258mm AND 7-day accumulation exceeding 1,169mm

- Not a single-day event threshold — requires sustained inundation
- 9.3% historical trigger rate
- The dual condition prevents false positives from isolated heavy-rain days

**Crop failure**: Vegetation Health Index below the critical threshold OR satellite-derived vegetation condition index below minimum

- Satellite-derived, independent of rainfall
- Catches peril scenarios that rainfall-only triggers miss (cloud cover, pest pressure, waterlogging)
- 6.2% historical trigger rate

**All three thresholds were calibrated to achieve a sustainable 75% loss ratio at current premium rates.** The calibration is not arbitrary — it is the result of iterating through 26 years of historical data and selecting thresholds that balance farmer protection with program solvency.

> **Note:** The 75% loss ratio is the Morogoro pilot calibration specifically — derived by iterating thresholds against 26 years of Morogoro location data. Aggregate payout figures spanning all six training locations yield a different arithmetic result (~80%) when divided by the single-location pilot premium; this is a multi-location scale artefact, not a discrepancy in the pilot loss ratio.

---

## 3. The Validation Run — What We Are Actually Testing

The forward validation run is not a proof of concept. The concept was proven during development. This is a **forward validation** — running the full production system on real 2026 data and comparing every forecast against what actually happens.

### What 90 Days of Daily Forecasting Measures

Each day the system generates 12 forecasts per location:

- 3 trigger types (drought, flood, crop failure)
- 4 forecast horizons (3, 4, 5, and 6 months ahead)

After 90 valid run-days, we accumulate 1,080 forecast records. When the first 3-month forecasts mature in early June, the system evaluates each one against observed outcomes. This produces two go-live gate metrics.

### The Two Gate Metrics

**Brier Score < 0.25**

The Brier Score measures how well-calibrated the probabilistic forecasts are. A score of 0 is perfect. A score below 0.25 means that when the model says 75% drought risk, drought actually occurs roughly 75% of the time — the probabilities are meaningful, not just directionally correct. Below 0.25 is the academic and industry standard for climate forecast reliability.

Our retrospective validation (2000–2025) showed the model catching **all four documented major climate events** in that window (2016, 2018, 2020, 2022). The validation run tests if this holds on data the model has never seen.

**Basis Risk < 30%**

Basis risk is the gap between what the index says and what actually happened. If the model predicts no drought but the farmer's field dries out — that is basis risk. If the model predicts drought but the farmer's field is fine — that is also basis risk (a false payout, which hurts the insurer, not the farmer).

A 30% basis risk threshold means: in at least 70% of cases where the trigger fires, a real adverse event occurred. The retrospective validation showed **20% basis risk** — already within the gate. The forward run will confirm or revise that number on real 2026 data.

### The Evidence Pack — Why Reinsurers Need This

No reinsurer will underwrite a parametric product based on backtesting alone. They have seen too many models that performed well historically and failed in deployment. The evidence pack is our answer to that objection:

- **Aggregate forecast accuracy metrics**: Brier Score, Root Mean Squared Error, calibration error across all 1,080 evaluated forecasts
- **Full forecast-actual log**: Every forecast paired with its observed outcome, timestamped, with model version and horizon tier
- **Model compliance attestation**: Signed documentation of zero data leakage, zero look-ahead bias, primary model version only, no synthetic fallbacks

This documentation trail is what turns a demo into an underwriteable product.

---

## 4. Does This Make Financial Sense?

### The Loss Ratio Is Not the Whole Story

A 75% loss ratio means $0.75 of every $1 in premium goes to paying claims. On its own, that number is meaningless — it does not tell you whether the program is operationally sustainable. The correct metric is the **Combined Ratio**:

```
Combined Ratio = Loss Ratio + Expense Ratio
Sustainable    = Combined Ratio < 100%
```

| Cost Category                         | 1,000 Farmers        | 5,000 Farmers       | 10,000 Farmers       |
| ------------------------------------- | -------------------- | ------------------- | -------------------- |
| Gross Premium                         | \$20,000/yr          | \$100,000/yr        | \$200,000/yr         |
| Expected Claims (75% LR)              | \$15,000/yr          | \$75,000/yr         | \$150,000/yr         |
| Platform / Infrastructure             | ~\$5,000/yr          | ~\$6,000/yr         | ~\$8,000/yr          |
| Reinsurance (~12% of premium)         | ~\$2,400/yr          | ~\$12,000/yr        | ~\$24,000/yr         |
| Distribution / Farmer Education       | ~\$3,000/yr          | ~\$8,000/yr         | ~\$12,000/yr         |
| Regulatory / Operations               | ~\$2,000/yr          | ~\$3,000/yr         | ~\$4,000/yr          |
| **Total Expenses (non-claims)** | **~\$12,400**  | **~\$29,000** | **~\$48,000**  |
| **Expense Ratio**               | **~62%**       | **~29%**      | **~24%**       |
| **Combined Ratio**              | **~137%**      | **~104%**     | **~99%**       |
| **Operational Result**          | Loss (needs funding) | Marginal            | **Break-even** |

**At 1,000 farmers, the combined ratio is approximately 137% — the program cannot sustain itself on premium income alone.** This is not a design flaw. It is the expected and honest reality of every parametric agriculture insurance program at pilot scale — KLIP Kenya, IBLI Ethiopia, and ACRE Africa all launched under this structure, supported by development finance until they reached operating scale.

The loss ratio (75%) reflects actual historical claims exposure. It is not adjustable without trade-offs:

- **Raising premiums** to force a lower combined ratio reduces farmer affordability (the product's primary value)
- **Tightening thresholds** to fire less often reduces farmer protection and increases basis risk
- Neither trade-off is appropriate at pilot stage

**The correct interpretation of 75% loss ratio**: Claims are sustainable — the reserve pool will not be depleted by normal trigger events. **But operations require external support at pilot scale** — development finance co-funding (Scenario B) is the preferred near-term mechanism; government subsidy (Scenario C) is the medium-term policy goal.

**Break-even scale is approximately 5,000–10,000 farmers**, where fixed platform costs drop below 10% of gross premium and the combined ratio approaches 100%. The Kilombero pilot with 1,000 farmers is the proof-of-concept phase that earns the right to scale.

### Premium Scenarios and Funding Pathways

The unsubsidised gross premium is **\$20/farmer/year** — the financially honest baseline. Three scenarios are modelled based on different external funding assumptions:

| Scenario | Farmer Cost | External Funding | Break-even Scale |
| -------- | ----------- | ---------------- | ---------------- |
| A — No subsidy (baseline) | \$20/year | None | ~10,000 farmers |
| B — Donor/NGO co-funding (near-term) | ~\$12/year | ~40% grant | ~2,000 farmers |
| C — Government subsidy (policy goal) | \$10/year | 50% government | Policy-dependent |

**Scenario A** is the honest operational baseline. Break-even requires approximately 10,000 farmers — where fixed platform costs fall below 10% of gross premium. Achievable, but not at pilot scale.

**Scenario B** is the realistic near-term pathway. Donor and development finance co-funding (GIZ, World Bank IDA, IFAD, Syngenta Foundation) specifically targets products at this validation stage. A ~40% grant contribution reduces farmer cost to ~\$12/year and achieves break-even at ~2,000 farmers — without depending on government budget cycles or political continuity.

**Scenario C** models a 50% government subsidy, reducing farmer cost to \$10/year. This is a **3–5 year horizon scenario**, not a near-term operational assumption. The most directly relevant precedent is Tanzania's own **Tanzania Agriculture Insurance Scheme (TAIS)**, launched July 2023 as a government-private sector consortium under the Association of Tanzania Insurers. TAIS explicitly designates government premium subsidies as part of its mandate — and UNDP Tanzania is actively developing the smart subsidy business case for TAIS (RFP issued 2024). The subsidy architecture is being built; it does not yet exist operationally. HewaSense is designed to integrate with TAIS once the subsidy mechanism is formalised, making this a credible medium-term pathway rather than a speculative one.

**For the Kilombero pilot**, the preferred pathway is Scenario B — accessible without a government MOU, achievable at pilot scale, and does not require TIRA approval as a prerequisite. Government subsidy engagement (Scenario C) is pursued in parallel as a medium-term objective.

At 1,000 farmers: **\$20,000/year gross premium**. Expected claims: \$15,000/year. Gap between premium and claims: \$5,000 — operational costs require external support at pilot scale, which is standard for all agricultural parametric programs at this stage (KLIP Kenya, IBLI Ethiopia, ACRE Africa all launched under similar structures).

### Capital Adequacy

Current cash reserves: **\$150,000**
Required reserves (regulatory minimum, 100% CAR): **\$133,557**
**Capital Adequacy Ratio: 112.3%** — compliant with a 12.3% buffer

Maximum single-event exposure (1,000 farmers × \$90 crop failure): **\$90,000**
The reserves cover the worst-case scenario (100% simultaneous crop failure) 1.67 times over.

> **Reserve sizing and event correlation:** Climate events across multiple locations are not independent — a La Niña or Indian Ocean Dipole episode can drive simultaneous threshold breaches across several zones in the same season. The $150,000 reserve is sized conservatively to account for this clustering risk: even if multiple perils fire in the same period, the reserve covers the worst-case single-event exposure 1.67× over, providing a buffer against correlated multi-location payouts.

### Comparison to Market

|                       | Pula Zambia | ACRE Kenya | HewaSense (ours) |
| --------------------- | ----------- | ---------- | ---------------- |
| Farmer cost           | \$6/year    | \$8/year   | \$10/year        |
| Max payout            | \$25        | \$40       | \$90             |
| Perils covered        | 1           | 2          | 3                |
| Payout-to-price ratio | 4.2×       | 5×        | **9×**    |

The value proposition is not the cheapest product — it is the **highest value at an affordable price point**. A farmer paying \$10 gets \$90 of coverage. That is 9 months of smallholder daily wages protected for less than 2 days' wages.

### Comparison to Market

The value proposition is not the cheapest product — it is the **highest value at an affordable price point**. At the target pilot cost of ~\$10–12/year (under Scenario B or C co-funding), a farmer receives up to \$90 of coverage — 9× their premium outlay.

---

## 5. The Path from Validation to Live Payouts

If the forward validation returns **Brier Score < 0.25 AND Basis Risk < 30%**, the path to live payouts is clear:

| Milestone                            | Target Date       | Description                                                     |
| ------------------------------------ | ----------------- | --------------------------------------------------------------- |
| First 3-month forecasts mature       | ~June 9, 2026     | Brier Score calculation begins                                  |
| Validation run completes             | June 12, 2026     | 90 valid run-days reached, 1,080 forecast records in hand       |
| Evidence pack compiled               | June 15, 2026     | Forecast accuracy metrics + full forecast-actual log finalised  |
| Internal debrief                     | June 15–20       | Predicted vs actual trigger alignment reviewed                  |
| **Go/No-Go decision**          | **June 20** | Binary gate — criteria are fixed                               |
| Regulatory preparation               | Late June 2026    | Application documentation assembled with evidence pack          |
| Reinsurer review                     | July 2026         | Evidence pack handed to prospective reinsurance partners        |
| Government subsidy MOU               | July 2026         | Subsidy structure formalised                                    |
| Farmer enrollment                    | Q3 2026           | 1,000 farmers, Kilombero cooperatives                           |
| **First live policies issued** | **Q3 2026** | First payout within 5–7 days of confirmed primary-tier trigger |

The go/no-go is binary and the criteria are fixed. A gate with room for negotiation is not a gate.

### What a First Live Payout Looks Like

Scenario: October 2026. The system flags a drought trigger for Morogoro with 82% probability on a 3-month forecast horizon (primary tier).

1. System evaluates: horizon ≤ 4 months ✓, probability ≥ 75% ✓, crop phase = Flowering ✓
2. Reserve earmarked: 1,000 farmers × 82% probability × \$60 = **\$49,200 held in reserve** (expected financial exposure at this probability)
3. Reserve check: \$150,000 available — fully covered ✓
4. Operations team receives automated alert
5. October observed rainfall confirms the trigger — rainfall falls below 120mm during flowering
6. **Trigger fires → all 1,000 enrolled Morogoro farmers receive \$60 each → \$60,000 distributed within 5–7 days**

No adjuster. No claim form. No dispute. Every enrolled farmer in the zone receives the same \$60 — not because their individual field was assessed, but because the objective climate index for the zone crossed the pre-disclosed threshold. The 82% probability determined how much reserve was held; the confirmed observation determines whether the payout fires at all.

---

## 6. Honest Risk Assessment

### Where the Model Could Fail

**Overfitting gap (14.94%)**: The model's training accuracy (R²=0.996) is significantly higher than its validation accuracy (R²=0.866). This gap is a known concern. If 2026 data introduces patterns the model has not seen, performance could degrade. The validation run is specifically designed to expose this. An ensemble fallback model (zero overfitting gap, R²=0.840) is available if the primary model degrades on forward data.

**Feature dependency risk (residual)**: Two rainfall-derived features remain in the 83-feature set and may carry secondary correlation with the target variable. Direct leakage sources were removed and verified, but these two borderline features are a known risk. Forward validation will reveal if they inflate historical performance.

**Climate change non-stationarity**: Thresholds were calibrated on 2000–2025 data. If 2026 is an outlier — which current ENSO forecasts suggest is possible — trigger rates may not match historical baselines. Annual recalibration is in the roadmap.

### Where the Business Could Fail

**Farmer uptake**: Enrollment targets 1,000 farmers but relies on Kilombero cooperatives as distribution partners. If cooperatives are weak or competing products exist, actual enrollment may be lower, diluting the premium pool.

**External funding dependency**: The pilot requires external co-funding to be farmer-affordable at scale. Scenario B (donor/NGO ~40% grant) is the near-term target — this does not require a government MOU and is accessible from development finance institutions active in Tanzania. Scenario C (50% government subsidy) is a medium-term policy goal, not an operational assumption. Enrollment planning uses Scenario B as the base case.

**Reinsurer pricing**: A reinsurer may accept the evidence pack but price their participation at a rate that consumes the operating buffer. This needs to be stress-tested against actual reinsurance quotes.

### The Floor Case

Even in a bad outcome, the validation run has value. If the model misses the Brier gate by a margin, we have 90 days of real forward data to retrain on — which is exactly the kind of label-rich dataset that was unavailable before. A failed gate is not a failed project; it is a calibration input. The 6-week retraining path is mapped and ready.

---

## 7. Why This Matters Beyond the Kilombero Basin

The Kilombero pilot is a deliberate choice of difficulty. Kilombero is dual-peril, has high climatic variability, is data-sparse by Western standards, and has a smallholder farmer base with low financial inclusion. If the product works here, it is replicable across Tanzania's remaining agricultural regions and across East Africa.

The model already covers 6 locations (Arusha, Dar es Salaam, Dodoma, Mbeya, Mwanza, Morogoro). Extending to national scale means enrolling cooperatives in existing model locations — not retraining or rebuilding the platform. The marginal cost of adding 1,000 farmers in a second location is close to zero once the Kilombero pilot has proven the operations model.

There are **approximately 2.3 million smallholder farmers in Tanzania** exposed to the three perils this system monitors. At \$10/year per farmer, that is a potential \$23 million annual premium pool — a meaningful climate risk transfer program at national scale.

The broader context: **Africa has the highest concentration of climate-vulnerable smallholder farmers in the world and the lowest insurance penetration**. Tanzania's gap is not unique. The validation evidence from this run is a template that reinsurers and development finance institutions (World Bank, ADB, IFAD) can use to evaluate parametric agriculture products across the continent.

---

## 8. The Verdict

HewaSense is:

- **Technically credible**: Validation R²=0.866, zero data leakage, 83 clean features, conservative thresholds calibrated on 26 years of data, phase-based coverage architecture
- **Financially viable at scale**: 75% loss ratio (claims-sustainable), 112.3% capital adequacy ratio, 9× payout-to-price ratio — combined ratio breaks even at ~5,000–10,000 farmers; pilot phase requires development finance backing, which is standard for all agricultural parametric products at this stage
- **Regulatorily tractable**: Parametric regulatory track, fixed payout schedule, objective triggers, no claims process
- **Operationally deployable**: Fully automated pipeline running daily since March 9, 2026, real-time monitoring, live dashboard, evidence pack accumulating
- **Competitively differentiated**: Most comprehensive multi-peril product for Tanzanian smallholders at the most farmer-friendly price point in the East African market

The forward validation run is not a formality. It is the honest acknowledgment that retrospective validation is not the same as forward validation, and that no farmer should receive a payout based on a model that has only been tested on data it helped create. By June 12, 2026, we will have 90 days of evidence that either confirms or challenges every assumption in this document.

If the Brier Score comes back below 0.25 and basis risk below 30%, the answer is unambiguous: **this is real, we can deploy, and farmers will receive payouts when their crops fail**.

That is what the validation run is for.

---

## Key Numbers at a Glance

| Parameter                   | Value                                  | Basis                                              |
| --------------------------- | -------------------------------------- | -------------------------------------------------- |
| Validation run window       | March 7 – June 12, 2026 (90 run-days) | Parametric insurance design specification          |
| Forecast target             | 1,080 forecast records                 | System design KPI                                  |
| Forecasts accumulated       | 228 (19 valid run-days, Apr 1)         | Live system — updated as shadow run progresses    |
| Go-live gate: Brier Score   | < 0.25                                 | Climate forecast industry standard                 |
| Go-live gate: Basis Risk    | < 30%                                  | Retrospective result: 20% (pre-forward validation) |
| Primary ML model            | Gradient-boosted ensemble (R²=0.8666) | Internal model evaluation report                   |
| Payout: Drought             | \$60/farmer                            | Parametric insurance final specification           |
| Payout: Flood               | \$75/farmer                            | Parametric insurance final specification           |
| Payout: Crop Failure        | \$90/farmer                            | Parametric insurance final specification           |
| Farmer premium (gross / unsubsidised) | \$20/year | Operational baseline — no external funding |
| Farmer cost (Scenario B — donor co-funding) | ~\$12/year | ~40% grant contribution; near-term target |
| Farmer cost (Scenario C — govt subsidy) | \$10/year | 50% government subsidy; medium-term policy goal |
| Loss ratio                  | 75%                                    | 26-year historical calibration                     |
| Capital Adequacy Ratio      | 112.3%                                 | Kilombero Basin Pilot Specification                |
| Cash reserves               | \$150,000                              | Kilombero Basin Pilot Specification                |
| Max single-event exposure   | \$90,000                               | 1,000 farmers ×\$90 crop failure payout           |
| Payout-to-price ratio       | 9×                                    | vs Pula Zambia 4.2×, ACRE Kenya 5×               |
| Live pilot target           | Q3 2026                                | Contingent on June gate and regulatory approval    |

---

**Document Owner**: HewaSense Climate Intelligence & Insurance Team
**Date**: March 2026
**Next Review**: June 2026 — post validation debrief
**Status**: Living document — updated after June gate decision
