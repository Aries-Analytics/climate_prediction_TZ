# HewaSense — Climate Intelligence for Smallholder Farmers

## Parametric Crop Insurance · Kilombero Basin, Tanzania

**Document Type**: External Introduction
**Date**: April 2026
**Status**: Forward Validation Active — Q2 2026
**Audience**: Partners · Development Finance · Government Advisors · Prospective Underwriters

---

## The Problem

Tanzania's Kilombero Basin is one of East Africa's most productive rice-growing regions — and one of its most climate-exposed. Farmers here face droughts when the Indian Ocean Dipole suppresses long rains, floods when El Niño years bring excess rainfall, and crop failure from vegetation stress that neither drought nor flood alone explains.

Across three perils and 26 years of historical data, climate thresholds have been breached an average of 23.5 times per year. Smallholders in the region face multiple distinct hazards each season with **no financial safety net**.

Conventional indemnity insurance cannot solve this. It requires claims adjusters, receipts-based proof of loss, and dispute processes — none of which are accessible to rural smallholders in sub-Saharan Africa. The result: **the farmers most exposed to climate risk are the least served by the insurance industry**.

---

## What HewaSense Does

HewaSense is a **parametric crop insurance system** built for smallholder farmers. It does not pay based on what a farmer claims they lost. It pays when an objective, satellite-derived climate measurement crosses a pre-disclosed threshold — automatically, within **5–7 days**, with no claims process.

| Feature | Indemnity Insurance | HewaSense |
|---|---|---|
| Payout trigger | Farm-level assessment | Objective climate threshold |
| Claims process | Required | None |
| Payout time | Weeks–months | 5–7 days |
| Disputes | Frequent | Not possible |
| Scalability | Adjuster-bound | Fully automated |

### Phase-Based Coverage

A simple monthly rainfall trigger misses biological reality. Rice has four distinct growth phases with different vulnerability windows. HewaSense tracks each phase dynamically — a drought during flowering (weeks 9–12) carries the most weight because stress in that window destroys the entire season regardless of what happened before or after.

This phase-based logic eliminates the most damaging form of basis risk: paying out during the dry season on a crop that was already harvested, or missing a real mid-season failure because seasonal totals looked normal.

### Three Perils, One Product

HewaSense covers drought, flood, and crop failure — with independent, calibrated triggers for each. Drought and flood are rainfall-derived. Crop failure uses satellite vegetation data, catching stress scenarios that rainfall-only triggers miss (cloud cover, pest pressure, waterlogging).

Each trigger has a different historical frequency and a different payout rate, reflecting the distinct financial impact of each peril on a smallholder household.

---

## Is It Working? — The Forward Validation Run

The system has been running daily on live 2026 climate data since April 14, generating forecasts for two distinct zones in the Kilombero Basin (Ifakara TC and Mlimba DC). This is not a proof-of-concept exercise — the concept was proven during development. This is a **90-day forward validation**: every forecast the system generates is logged and will be evaluated against observed outcomes — per-zone and in aggregate — when forecast windows mature in July.

Two gate metrics determine go-live eligibility:

**Forecast Calibration (Brier Score < 0.25):** When the system says 75% drought risk, drought should actually occur roughly 75% of the time. A Brier Score below 0.25 is the academic and industry standard for climate forecast reliability. It means the probabilities are actionable — not just directionally correct.

**Basis Risk < 30%:** In at least 70% of cases where a trigger fires, a real adverse event must have occurred. Retrospective validation against 26 years of historical data returned 20% basis risk — already within the gate. The forward run confirms this on data the model has never seen.

The go/no-go decision is binary and criteria are fixed. A gate with room for negotiation is not a gate.

### The Evidence Pack

At validation close (~July 13), the system automatically compiles an evidence pack: per-zone and aggregate forecast accuracy metrics, a full forecast-actual log timestamped for every forecast with zone identification, and a model compliance attestation. This documentation trail is what turns a validated pilot into an underwriteable product.

---

## Does It Make Financial Sense?

### The Loss Ratio

The program is calibrated to a **75% loss ratio** — $0.75 of every $1 in premium goes to paying claims. This reflects actual historical claims exposure across 26 years of Kilombero Basin climate data. It is not adjusted to look more attractive.

### Farmer Value

| | Pula (Zambia) | ACRE (Kenya) | HewaSense |
|---|---|---|---|
| Farmer cost | \$6/year | \$8/year | \$10–12/year |
| Max payout | \$25 | \$40 | \$90 |
| Perils covered | 1 | 2 | 3 |
| Payout-to-price ratio | 4.2× | 5× | **9×** |

The value proposition is not the cheapest product. It is the **highest value at an affordable price point** — $90 of coverage for less than 2 days' smallholder wages.

### Scale and Sustainability

| Scale | Gross Premium | Combined Ratio | Operational Status |
|---|---|---|---|
| 1,000 farmers (pilot) | $20,000/yr | ~137% | Requires co-funding |
| 5,000 farmers | $100,000/yr | ~104% | Near break-even |
| 10,000 farmers | $200,000/yr | ~99% | Break-even |

At pilot scale, the combined ratio reflects a gap between premium income and total operating costs. This is standard for every agricultural parametric program at launch — KLIP Kenya, IBLI Ethiopia, and ACRE Africa all launched under this structure, supported by development finance until they reached operating scale.

Break-even is approximately 5,000–10,000 farmers. The Kilombero pilot with 1,000 farmers is the proof-of-concept phase that earns the right to scale.

### Funding Pathway

| Scenario | Farmer Cost | Mechanism |
|---|---|---|
| A — Unsubsidised | $20/year | No external funding |
| B — Donor/NGO co-funding (near-term target) | ~$12/year | ~40% grant contribution |
| C — Government subsidy (medium-term) | $10/year | 50% government subsidy via TAIS framework |

Scenario B is the near-term operational pathway — accessible from development finance institutions without a government MOU, achievable at pilot scale. Scenario C is a credible medium-term path: Tanzania's Agriculture Insurance Scheme (TAIS) already designates government premium subsidies as part of its mandate.

### Capital Position

Current reserves cover the worst-case single-event exposure (100% simultaneous crop failure across all enrolled farmers) **1.67 times over**, with a buffer explicitly sized to account for correlated multi-peril events during ENSO years.

---

## The Path to Live Payouts

| Milestone | Target |
|---|---|
| Forward validation closes | June 2026 |
| Evidence pack compiled | June 2026 |
| Go/No-Go decision | Mid-2026 |
| ↳ If No-Go: threshold recalibration, model retraining, or trigger redesign | TBD |
| Stakeholder engagement — insurance underwriters | Q3 2026 |
| Pilot alignment — 1,000 farmer enrollment | Q4 2026 |
| **First live policies + payout capability** | **2026/27 season (target)** |

### What a First Payout Looks Like

The system flags a drought trigger for Morogoro with elevated probability on a primary-tier forecast. A financial reserve is automatically earmarked based on that probability. When observed rainfall confirms the threshold was breached, **all 1,000 enrolled Kilombero farmers receive a fixed payout within 5–7 days** — no claims form, no adjuster, no dispute. Every farmer in the zone receives the same amount because every farmer faces the same zone-level climate risk.

---

## Why Kilombero — and Why It Matters Beyond

Kilombero is a deliberate choice of difficulty. It is dual-peril, data-sparse, and serves a farmer base with low financial inclusion. If the product works here, the replication case across Tanzania and East Africa is straightforward.

There are approximately **2.3 million smallholder farmers in Tanzania** exposed to the three perils this system monitors. Africa has the highest concentration of climate-vulnerable smallholder farmers in the world and the lowest insurance penetration. The validation evidence from this run is a replicable template — for reinsurers, development finance institutions, and government programs evaluating parametric agriculture insurance across the continent.

---

## Key Numbers

| | |
|---|---|
| Pilot target | 1,000 farmers, Kilombero Basin |
| Perils covered | Drought · Flood · Crop Failure |
| Payout range | $60–$90 per farmer per event |
| Farmer premium (unsubsidised) | $20/year |
| Farmer cost (co-funded target) | ~$12/year |
| Historical loss ratio | 75% |
| Retrospective basis risk | 20% |
| Forward validation window | April 14 – July 13, 2026 (two-zone) |
| Go-live gate — forecast calibration | Brier Score < 0.25 |
| Go-live gate — basis risk | < 30% |
| Payout-to-price ratio | 9× (vs 4–5× for comparable products) |
| Payout timing | 5–7 days from confirmed trigger |
| Target go-live | Q3 2026 |

---

**HewaSense Climate Intelligence & Insurance**
**Contact**: [Contact details]
**April 2026**
