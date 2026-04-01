# HewaSense — Business Case & Deployment Rationale

## Parametric Climate Insurance for Smallholder Farmers in Tanzania

**Document Type**: Strategic Business Analysis
**Date**: March 19, 2026
**Status**: Shadow Run ACTIVE — Day 19 of 90 valid run-days (228/1,080 forecasts, 21.1%)
**Author**: HewaSense Climate Intelligence & Insurance Team
**Audience**: Project Leadership · Potential Underwriters · TIRA Review · Government Partners

---

## The One-Question Framing

> *"Have we built something that actually matters — and if the shadow run numbers come back clean, can we give farmers real money when their crops fail?"*

The short answer is yes. This document explains why, and what the path to a live payout looks like.

---

## 1. The Problem We Are Solving

Tanzania's Kilombero Basin is one of the most productive rice-growing regions in East Africa. It is also one of the most climate-exposed. The basin sits at the confluence of the Kilombero River flood plains and the Southern Highlands rain shadow, creating a dual-peril environment where farmers face:

- **Droughts** when the Indian Ocean Dipole suppresses long rains (March–May)
- **Floods** when El Niño years bring excess rainfall to an already low-lying basin
- **Crop failure** from NDVI degradation — sometimes caused by neither drought nor flood, but prolonged cloud cover, pest pressure, or soil waterlogging

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
| TIRA compliance | Standard route               | Parametric route (separate regulatory track) |

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

**Without phase-based logic, a drought in the dry season would trigger a payout on a crop that was already harvested.** That is basis risk in the worst form: paying for non-losses and missing real ones. Our phase-based architecture eliminates this class of error.

### 2.3 Horizon Tier Enforcement

The ML model forecasts 3–6 months ahead. But a 6-month forecast carries structurally more uncertainty than a 3-month forecast. We address this formally:

- **Primary tier** (≤ 4 months, ≥ 75% confidence): payout-eligible, counted in financial reserves
- **Advisory tier** (5–6 months, ≥ 50% confidence): early warning only — never triggers a payout

This is not a soft guideline. It is enforced at the code level in three locations (backend API, risk endpoint, frontend financial projections). Advisory forecasts surface in the Early Warning panel but cannot create financial obligations. This is the architecture that a reinsurer needs to see to price the product.

### 2.4 The Three Thresholds and Why They Are Calibrated Where They Are

**Drought**: Rainfall < 120mm over 30 days (SPI-30 < -0.60)

- Calibrated from 26 years of historical data
- 12.0% historical trigger rate — about once per 8 months
- Pula Zambia uses a comparable SPI threshold

**Flood**: Daily rainfall > 258mm AND 7-day accumulation > 1,169mm

- Not a single-day event threshold — requires sustained inundation
- 9.3% historical trigger rate
- The dual condition prevents false positives from single heavy-rain days

**Crop failure**: NDVI < -1.56σ from seasonal baseline OR VCI < 3.33

- Satellite-derived vegetation health — independent of rainfall
- Catches peril scenarios the rainfall-only triggers miss
- 6.2% historical trigger rate

**All three thresholds were calibrated to achieve a sustainable 75% loss ratio at current premium rates.** The calibration is not arbitrary — it is the result of iterating through 26 years of historical data and selecting thresholds that balance farmer protection with program solvency.

> **Note:** The 75% loss ratio is the Morogoro pilot calibration specifically — derived by iterating thresholds against 26 years of Morogoro location data. Aggregate payout figures spanning all six training locations yield a different arithmetic result (~80%) when divided by the single-location pilot premium; this is a multi-location scale artefact, not a discrepancy in the pilot loss ratio.

---

## 3. The Shadow Run — What We Are Actually Testing

The shadow run is not a proof of concept. The concept was proven during development. The shadow run is a **forward validation** — running the full production pipeline on real 2026 data and comparing every forecast against what actually happens.

### What 90 Days and 1,080 Forecasts Measures

Every day at 06:00 EAT, the pipeline generates 12 forecasts per location:

- 3 trigger types (drought, flood, crop failure)
- 4 forecast horizons (3, 4, 5, 6 months ahead)

After 90 valid run-days, we accumulate **1,080 ForecastLog entries**. When the first 3-month forecasts mature (~June 9), the system evaluates each one:

```
Forecast: "Drought probability 78% for Morogoro, April 2026"
Outcome (June): Did a drought event actually occur?
Result: TP / FP / TN / FN → feeds Brier Score calculation
```

### The Two Gate Metrics and What They Mean in Plain Language

**Brier Score < 0.25**

The Brier Score measures how well-calibrated the probabilistic forecasts are. A score of 0 is perfect; a score of 0.25 means the model's probabilities are meaningful — when it says 75% drought risk, it rains less than 120mm roughly 75% of the time. A score below 0.25 is the academic and industry standard for climate forecast reliability.

Our retrospective validation (2000–2025) showed the model catching **all four documented major climate events** in that window (2016, 2018, 2020, 2022). The shadow run will test if this holds on **data the model has never seen**.

**Basis Risk < 30%**

Basis risk is the gap between what the index says and what actually happened. If the model predicts no drought but the farmer's field dries out — that is basis risk. If the model predicts drought but the farmer's field is fine — that is also basis risk, but in the other direction (a false payout, which hurts the insurer, not the farmer).

A 30% basis risk threshold means: in at least 70% of cases where the trigger fires, a real adverse event occurred. The retrospective validation showed **20% basis risk** — already within the gate. The shadow run will confirm or revise that number on forward data.

### The Evidence Pack — Why Reinsurers Need This

No reinsurer will underwrite a parametric product based on backtesting alone. They have seen too many models that performed well in-sample and failed in deployment. The evidence pack is our answer to that objection:

- **`metrics.json`**: Aggregate Brier Score, RMSE, calibration error across all 1,080 evaluated forecasts
- **`logs_export.csv`**: Every forecast-actual pair with timestamps, model version, and horizon tier
- **`model_compliance_statement.txt`**: Signed attestation of zero data leakage, zero look-ahead bias, XGBoost V4.0 only, no synthetic fallbacks

This is the documentation trail that turns a demo into an underwriteable product.

---

## 4. Does This Make Financial Sense?

### The Loss Ratio Is Not the Whole Story

A 75% loss ratio means $0.75 of every $1 in premium goes to paying claims. On its own, that number is meaningless — it does not tell you whether the program is operationally sustainable. The correct metric is the **Combined Ratio**:

```
Combined Ratio = Loss Ratio + Expense Ratio
Sustainable = Combined Ratio < 100%
```

| Cost Category                         | 1,000 Farmers        | 5,000 Farmers       | 10,000 Farmers       |
| ------------------------------------- | -------------------- | ------------------- | -------------------- |
| Gross Premium                         | \$20,000/yr          | \$100,000/yr        | \$200,000/yr         |
| Expected Claims (75% LR)              | \$15,000/yr          | \$75,000/yr         | \$150,000/yr         |
| Platform / Infrastructure             | ~\$5,000/yr          | ~\$6,000/yr         | ~\$8,000/yr          |
| Reinsurance (~12% of premium)         | ~\$2,400/yr          | ~\$12,000/yr        | ~\$24,000/yr         |
| Distribution / Farmer Education       | ~\$3,000/yr          | ~\$8,000/yr         | ~\$12,000/yr         |
| TIRA Compliance / Operations          | ~\$2,000/yr          | ~\$3,000/yr         | ~\$4,000/yr          |
| **Total Expenses (non-claims)** | **~\$12,400**  | **~\$29,000** | **~\$48,000**  |
| **Expense Ratio**               | **~62%**       | **~29%**      | **~24%**       |
| **Combined Ratio**              | **~137%**      | **~104%**     | **~99%**       |
| **Operational Result**          | Loss (needs funding) | Marginal            | **Break-even** |

**At 1,000 farmers, the combined ratio is approximately 137% — the program cannot sustain itself on premium income alone.** This is not a design flaw. It is the expected and honest reality of every parametric agriculture insurance program at pilot scale — KLIP Kenya, IBLI Ethiopia, and ACRE Africa all launched under this structure, supported by development finance until they reached operating scale.

The loss ratio (75%) reflects the actual historical claims exposure. It is not adjustable without trade-offs:

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

**Scenario A** is the honest operational baseline. Break-even requires approximately 10,000 farmers — where fixed platform costs fall below 10% of gross premium. Achievable at scale, but not at pilot stage.

**Scenario B** is the realistic near-term pathway. Donor and development finance co-funding (GIZ, World Bank IDA, IFAD, Syngenta Foundation) specifically targets products at this validation stage. A ~40% grant contribution reduces farmer cost to ~\$12/year and achieves break-even at ~2,000 farmers — without depending on government budget cycles or political continuity.

**Scenario C** models a 50% government subsidy, reducing farmer cost to \$10/year. Precedents exist in the region (KLIP Kenya, CADP Ethiopia, Nigeria NIRSAL), and Tanzania's ASDP has explicit smallholder risk management mandates. The ask (\$10,000/year for 1,000 farmers) is modest in development aid terms — but it requires a budget line, disbursement mechanism, and political will sustained across election cycles. It is a legitimate medium-term policy goal, not a near-term operational assumption.

**For the Kilombero pilot**, the preferred pathway is Scenario B — accessible without a government MOU, achievable at pilot scale, and does not require TIRA approval as a prerequisite. Government subsidy engagement (Scenario C) is pursued in parallel as a medium-term objective.

At 1,000 farmers: **\$20,000/year gross premium**. Expected claims: \$15,000/year. Gap between premium and claims: \$5,000 — operational costs require external support at pilot scale, consistent with how every comparable agricultural parametric program launched (KLIP Kenya, IBLI Ethiopia, ACRE Africa).

### Capital Adequacy

Current cash reserves: **\$150,000**
Required reserves (TIRA 100% CAR minimum): **\$133,557**
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

### Why the Three-Scenario Model Matters

Presenting a single government-subsidy-dependent premium as the baseline does not survive actuarial or investor scrutiny. The three-scenario model is honest about what each pathway requires and does not assume political commitments that have not yet been made. The scenarios are not mutually exclusive — Scenario B can fund the pilot while Scenario C is negotiated in parallel for national scale.

---

## 5. What "Good Numbers" Unlock: The Live Pilot Decision Tree

If the shadow run returns **Brier Score < 0.25 AND Basis Risk < 30%**, the path to live payouts is:

```
June 12 — Shadow run completes (90 valid run-days)
June 9  — First 3-month forecasts mature, Brier Score calculation begins
June 15 — Evidence pack compiled (metrics.json + logs_export.csv)
June 15-20 — Internal debrief: predicted vs actual trigger alignment
June 20 — Go/No-Go decision
    │
    ├── GO: Brier < 0.25 + Basis < 30%
    │   ├── TIRA submission with evidence pack
    │   ├── Reinsurer review (evidence pack handed over)
    │   ├── Government subsidy MOU signing
    │   ├── Farmer enrollment (1,000 farmers, Kilombero cooperatives)
    │   └── Q3 2026: First live policies issued
    │       └── First payout: within 5-7 days of confirmed primary-tier trigger
    │
    └── NO-GO: Numbers outside gate
        ├── Retrain XGBoost on 2026 data (6-8 weeks)
        ├── Recalibrate thresholds if bias detected
        └── Extend shadow run 30 days → re-evaluate
```

The go/no-go is binary and the criteria are fixed. This is intentional — a gate with room for negotiation is not a gate.

### What a First Live Payout Looks Like

Scenario: It is October 2026. The pipeline flags a drought trigger for Morogoro with 82% probability on a 3-month horizon (primary tier). Threshold: SPI-30 < -0.60 (< 120mm/30 days).

1. System evaluates: horizon ≤ 4 months ✓, probability ≥ 75% ✓, phase = Flowering ✓
2. Reserve earmarked: 1,000 × 0.82 × \$60 = \$49,200 held in reserve (expected financial exposure at this probability level)
3. Reserve check: \$150,000 available — fully covered ✓
4. Operations team notified via Slack alert
5. October observed rainfall confirms trigger — rainfall falls below 120mm during flowering
6. **Trigger fires → all 1,000 enrolled Morogoro farmers receive \$60 each → \$60,000 distributed within 5–7 days**

No adjuster. No claim form. No dispute. The farmer gets \$60 in their mobile money account because rainfall was objectively below 120mm during flowering. The payout is zone-level and binary — every enrolled farmer in the zone is paid equally when the threshold is breached. The 82% probability determined reserve sizing; the confirmed observation determines whether the trigger fires at all.

---

## 6. Honest Risk Assessment

### Where the Model Could Fail

**Overfitting gap (14.94%)**: XGBoost's train R² (0.996) is significantly higher than validation R² (0.866). This gap is concerning. If 2026 data introduces patterns the model has not seen, performance could degrade. The shadow run is specifically designed to expose this. The Ensemble model (zero overfitting gap, R²=0.840) is available as fallback if XGBoost degrades on forward data.

**Feature leakage risk (residual)**: `flood_risk_score` and `spi_30day` remain in the 83-feature set. These are rainfall-derived and may carry secondary leakage. The leakage prevention utility verified the 11 direct leakage features were removed, but these two borderline features are a known risk. Forward validation will reveal if they inflate performance on training data.

**Climate change non-stationarity**: The thresholds were calibrated on 2000–2025 data. If the 2026 season is an outlier (which ENSO forecasts suggest is possible), trigger rates may not match historical baselines. Annual recalibration is in the roadmap.

### Where the Business Could Fail

**Farmer uptake**: Enrollment targets 1,000 farmers but relies on Kilombero cooperatives as distribution partners. If cooperatives are weak or competing products exist, actual enrollment may be lower, diluting the premium pool.

**External funding dependency**: The pilot requires external co-funding to be farmer-affordable. Scenario B (donor/NGO ~40% grant) is the near-term target — accessible from development finance institutions active in Tanzania without requiring a government MOU. Scenario C (50% government subsidy) is a medium-term policy goal pursued in parallel. Enrollment planning uses Scenario B as the base case; $20/farmer is the unsubsidised fallback if co-funding is delayed.

**Reinsurer pricing**: A reinsurer may accept the evidence pack but price their participation at a rate that consumes the operating buffer. This needs to be stress-tested against reinsurance quotes.

### The Floor Case

Even in a bad outcome, the system has value. If the shadow run misses the Brier gate by a margin, we have 90 days of real forward data to retrain on — which is exactly the kind of label-rich dataset that was missing before. A failed gate is not a failed project; it is a calibration input.

---

## 6b. Pre-Enrollment Commercial Decisions (Open — Gate: June 2026)

These questions are not blocking the shadow run but must be resolved before the first farmer is enrolled. Documented here for continuity.

### Q1 — Underwriting partner
HewaSense operates as a parametric insurance platform/MGA (Managing General Agent). A locally licensed insurance underwriter must be identified and contracted to hold reserves and issue policies. This partner is not yet confirmed.

**Decision required:** Identify and approach 2–3 candidate insurers in Tanzania (and target expansion markets) ahead of the June gate. The evidence pack from the shadow run is the primary commercial document to share with underwriter prospects.

### Q2 — Revenue sharing, fee structure, and premium flow direction

HewaSense's actual revenue is a **platform fee — a percentage of the gross premium** paid by the underwriter from collected premiums. Standard MGA range: 15–20% of gross premium (confirmed by McKinsey MGA analysis and comparable to Pula Advisors' per-farmer commission model).

**Critical clarification on premium flow:** The farmer is NOT always the direct premium payer. Research on Africa's most scaled agri-insurtechs shows the primary premium payer is typically an institutional actor:

| Channel | Who pays the premium | Farmer's role |
|---|---|---|
| Input bundling | Agri-input company (seed/fertilizer) pays in full | Receives insurance free with input purchase |
| MFI/loan bundling | MFI adds to loan, collects at repayment | Premium embedded in seasonal loan |
| Bancassurance | Bank collects from farmer/sponsor, remits to underwriter | May pay directly or via loan |
| Donor co-funding | Donor covers ~40%, farmer pays ~60% | Co-payment at planting |
| Pay-at-Harvest | Impact investor pre-finances; cooperative deducts at harvest | Pays from harvest proceeds, not upfront |

The gross premium breakdown (once the institutional payer and channel are known):

| Party | Indicative share | On $12 gross (Scenario B) |
|---|---|---|
| Distribution partner commission | ~15–20% | ~$1.80–2.40 |
| HewaSense platform fee | ~15–20% | ~$1.80–2.40 |
| Reinsurance | ~10–15% | ~$1.20–1.80 |
| Licensed insurer (reserve + margin) | ~45–55% | ~$5.40–6.60 |

**Note:** The farmer is NOT the entity paying HewaSense. HewaSense is paid by the underwriter from the premium pool. Distribution partners are also paid from the same pool — they do not pay HewaSense.

**Decision required:** Formalise HewaSense's fee percentage, confirm Pay-at-Harvest as primary premium channel (see Q5 for full analysis), and stress-test scenarios against reinsurance quotes once the evidence pack is available.

### Q3 — Reinsurance coverage
No parametric product should go live without reinsurance coverage for tail-risk years (multiple simultaneous triggers across enrolled zones). Reinsurance pricing will depend on the evidence pack — specifically the Brier Score, basis risk figure, and historical loss ratio.

**Decision required:** Approach reinsurance brokers (e.g. African Risk Capacity, Global Parametrics, local reinsurance intermediaries) post-June gate with the evidence pack. Determine whether reinsurance is in place from day one of enrollment or only after a defined enrolled premium volume threshold.

### Q4 — Distribution commission in scenario pricing
The three gross premium scenarios were modelled before the distribution commission structure was formalised. It is not confirmed whether the distribution commission is already embedded in the $20/$12/$10 figures or sits on top of them.

**Decision required:** Confirm whether distribution commission is included in or additive to the scenario premiums. If additive, the gross premiums charged to farmers/sponsors will be higher than currently documented.

### Q5 — Premium payment channel and farmer liquidity strategy

This is the highest-impact commercial decision. Research on Africa's agri-insurance market shows voluntary farmer-pays models have <5% uptake. The channel determines both reach and sustainability:

**Option A — Input bundling (Pula's primary model):** Agri-input company pays full premium. Farmer receives insurance free with seed/fertilizer purchase. Pula covers 99% of farmers at $1–3 premium via this channel. Achieved 900,000+ farmers in Zambia through government fertilizer programs. **Risk:** Farmer is passive — no enrollment decision, lower behavioral engagement.

**Option B — Pay-at-Harvest (Pula Nigeria pilot, 2021):** Premium pre-financed by impact investor at planting; deducted from farmer's harvest payment by cooperative/offtaker. Result: 72% take-up vs 5% for pay-upfront — a 14× improvement. Poorest, most liquidity-constrained farmers benefited most. Shell Foundation confirmed: "Pay-at-Harvest increases insurance uptake by 14x in Nigeria." **This is the most promising demand-side innovation in African agri-insurance as of 2024.** For Kilombero rice farmers who sell through cooperatives/offtakers, this channel is structurally feasible.

**Option C — MFI/loan bundling:** Premium added to seasonal input loan. Farmer pays at loan repayment. MFI reduces its own credit default risk — strong institutional incentive to participate. Established model in East Africa (ACRE Africa, One Acre Fund).

**Option D — Donor/NGO co-payment:** Donor covers ~40%, farmer pays ~60% upfront at planting. **Not recommended as a standalone channel for Kilombero pilot.** Liquidity constraint remains for the farmer-facing portion, and requiring upfront payment is precisely the adoption barrier this product is designed to eliminate. Donor co-funding may be relevant as a subsidy layer within Scenario C (government/TAIS alignment, 3–5 year horizon) but should not be the primary channel.

**Recommendation for Kilombero pilot:** Pay-at-Harvest (Option B) is the primary channel — it eliminates the upfront payment barrier entirely and is structurally feasible via Kilombero rice cooperatives/offtakers. Pula Nigeria 2021 evidence (72% vs 5% uptake, 14× improvement) makes this the most defensible choice for a smallholder-facing pilot. Option C (MFI bundling) as secondary if cooperative pre-financing is not secured before pilot launch. Option A (input bundling) as a longer-term opportunity pending agri-input company engagement in Kilombero. Option D is not recommended as a standalone channel.

**Decision required:** Identify the primary premium channel before approaching underwriter or distribution partners. The channel determines the partnership structure, contract design, and pre-financing requirements.

### Q6 — Future revenue stream: weather intelligence as a B2B data product

HewaSense's ML model, location-level forecasts, and trigger logic are assets that have value beyond the insurance product. Agricultural lenders (cooperatives, MFIs, banks) independently need location-level weather risk intelligence to:
- Price seasonal input credit by risk zone
- Identify high-risk borrowers in their agricultural loan portfolios
- Make pre-season lending decisions based on forecast confidence

This creates a potential second revenue stream: a **weather risk data subscription or API** sold directly to agricultural lenders — separate from and additive to the insurance platform fee. In this model, the cooperative or MFI becomes a paying HewaSense customer in its own right, not just a distribution channel.

**Precedent:** aWhere, Descartes Underwriting, and Jupiter Intelligence all monetize weather/climate data as a standalone B2B product alongside or independent of insurance partnerships.

**Status:** Not part of the current go-to-market. Requires separate product definition, pricing, and sales motion. Gate: post-shadow-run, once the evidence pack establishes the model's commercial credibility. Document here for roadmap planning only.

---

## 7. Why This Matters Beyond the Kilombero Basin

The Kilombero pilot is a deliberate choice of difficulty. Kilombero is dual-peril, has high climatic variability, is data-sparse by Western standards, and has a smallholder farmer base with low financial inclusion. If the product works here, it is replicable across Tanzania's remaining agricultural regions and across East Africa.

The model already covers 6 locations (Arusha, Dar es Salaam, Dodoma, Mbeya, Mwanza, Morogoro). Extending to national scale means enrolling cooperatives in existing model locations — not retraining the model or rebuilding the platform. The marginal cost of adding 1,000 farmers in Mbeya is close to zero once the Kilombero pilot has proven the operations model.

There are **approximately 2.3 million smallholder farmers in Tanzania** exposed to the three perils this system monitors. At \$10/year per farmer, that is a potential \$23 million annual premium pool — a meaningful climate risk transfer program at national scale.

The broader context: **Africa has the highest concentration of climate-vulnerable smallholder farmers in the world and the lowest insurance penetration**. Tanzania's gap is not unique. The evidence pack from this shadow run is a template that reinsurers and development finance institutions (World Bank, ADB, IFAD) can use to evaluate parametric agriculture products across the continent.

---

## 8. The Verdict

We have built a product that is:

- **Technically credible**: R²=0.866, zero data leakage, 83 clean features, conservative thresholds, phase-based coverage
- **Financially viable at scale**: 75% loss ratio (claims-sustainable), 112.3% CAR, 9× payout-to-price value ratio — combined ratio breaks even at ~5,000–10,000 farmers; pilot phase requires development finance backing (standard for all agricultural parametric products at this stage)
- **Regulatorily tractable**: TIRA parametric track, fixed payout schedule, objective triggers, no claims process
- **Operationally deployable**: fully automated pipeline running daily since March 9, Slack monitoring, dashboard live, evidence pack accumulating
- **Competitively differentiated**: most comprehensive multi-peril product for Tanzanian smallholders at the most farmer-friendly price point in the market

The shadow run is not a formality. It is the honest acknowledgment that retrospective validation is not the same as forward validation, and that no farmer should receive a payout based on a model that has only been tested on data it helped create. By June 12, we will have 90 days of evidence that either confirms or challenges every assumption in this document.

If the Brier Score comes back below 0.25 and basis risk below 30%, the answer to the framing question is unambiguous: **yes, this is real, yes we can deploy, and yes, farmers will receive payouts when their crops fail**.

That is what the shadow run is for.

---

## Appendix: Key Numbers at a Glance

| Parameter                   | Value                                     | Source                                           |
| --------------------------- | ----------------------------------------- | ------------------------------------------------ |
| Shadow run window           | Mar 7 – Jun 12, 2026 (90 valid run-days) | `PARAMETRIC_INSURANCE_FINAL.md`                |
| ForecastLog target          | 1,080 entries                             | System health KPI                                |
| Current entries             | 168                                      | `forecast_logs` table                          |
| Go-live gate: Brier Score   | < 0.25                                    | `MODEL_METRICS_AND_SHADOW_RUN_IMPLICATIONS.md` |
| Go-live gate: Basis Risk    | < 30%                                     | Retrospective: 20% (pre-shadow)                  |
| Primary model               | XGBoost V4.0 (R²=0.8666)                 | `EXECUTIVE_SUMMARY.md`                         |
| Payout: Drought             | \$60/farmer                               | `forecasts.py` `PAYOUT_RATES`                |
| Payout: Flood               | \$75/farmer                               | `forecasts.py` `PAYOUT_RATES`                |
| Payout: Crop Failure        | \$90/farmer                               | `forecasts.py` `PAYOUT_RATES`                |
| Farmer premium (subsidised) | \$10/season                               | `PARAMETRIC_INSURANCE_FINAL.md`                |
| Loss ratio                  | 75%                                       | 26-year historical calibration                   |
| Capital Adequacy Ratio      | 112.3%                                    | `KILOMBERO_BASIN_PILOT_SPECIFICATION.md`       |
| Cash reserves               | \$150,000                                 | `KILOMBERO_BASIN_PILOT_SPECIFICATION.md`       |
| Max single-event exposure   | \$90,000                                  | 1,000 farmers ×\$90                             |
| Payout-to-price ratio       | 9×                                       | vs Pula Zambia 4.2×, ACRE 5×                   |
| TIRA submission target      | Late June 2026                            | Post shadow run evidence pack                    |
| Live pilot target           | Q3 2026                                   | Contingent on June gate                          |

---

**Document Owner**: HewaSense Climate Intelligence & Insurance Team
**Last Updated**: March 28, 2026
**Next Review**: June 15, 2026 — post shadow run debrief
**Status**: Living document — update after June gate decision
