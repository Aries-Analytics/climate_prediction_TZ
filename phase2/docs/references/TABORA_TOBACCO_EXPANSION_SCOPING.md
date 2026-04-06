# Tabora Region — Location 7 Expansion Scoping: Tobacco Parametric Insurance

**Date**: March 22, 2026
**Status**: 📋 SCOPING — Deferred to post-shadow-run (review gate: mid-2026)
**Version**: 1.0
**Author**: HewaSense Climate Intelligence & Parametric Insurance Team

---

## Executive Summary

Tabora Region is Tanzania's dominant tobacco-producing area and a strong candidate for HewaSense's seventh location and second crop (tobacco, a cash crop). The technical case is solid — all required climate data sources (CHIRPS, ERA5, NASA POWER, NDVI) cover Tabora coordinates fully, and the pipeline architecture requires only a new Location record. The market case is compelling: confirmed large-scale climate losses, an active precedent product (ACRE Africa/NBC WII), a government insurance consortium already paying out TZS 3 billion to Tabora tobacco farmers, and a superior distribution channel via the mandatory TTB contract farming system.

The primary constraint is **ESG/tobacco financing exclusions**: IFC, World Bank, and most multilateral donors formally exclude tobacco from financing. Major reinsurers (Munich Re, Swiss Re) are withdrawing from tobacco-related underwriting under ESG commitments. The viable funding path runs through tobacco buyers (Alliance One, Mkwawa), the domestic TAIC pool, and Tanzanian commercial banks — not international development finance.

**Decision deferred to post-shadow-run (mid-2026).** Before committing, a scoping conversation with TTB and at least one tobacco buyer is required to confirm current farmer counts and distribution partnership appetite.

---

## 1. Tabora Region — Geography & Climate

### Location

- **Region:** Tabora Region, central-western Tanzania — the largest region by land area
- **City coordinates:** ~5.0°S, 32.8°E
- **Elevation:** ~1,200 metres above sea level (central plateau)
- **Tobacco districts:** Urambo, Kaliua, Uyui, Sikonge, Tabora Municipal, Nzega

**Key district coordinates for sub-grid modelling:**

| District | Latitude | Longitude |
|----------|----------|-----------|
| Urambo | ~5.0°S | ~32.1°E |
| Kaliua | ~5.1°S | ~31.8°E |
| Uyui | ~5.0°S | ~33.1°E |
| Sikonge | ~5.6°S | ~32.8°E |
| Tabora Municipal | ~5.1°S | ~32.8°E |
| Nzega | ~4.2°S | ~33.2°E |

### Climate Zone

**Tropical savanna (Köppen Aw)** — same classification as Morogoro but with a distinctly drier, more continental character due to its inland position.

### Rainfall Pattern

- **Annual average:** 700–1,000 mm (~880 mm at Tabora city; eastern parts as low as 700 mm)
- **Seasonality:** Strongly **unimodal** — a single rainy season November–April; May–October is completely dry
- **Wettest month:** March (~170 mm); **Driest months:** July–August (~0 mm)
- **Growing window:** Effectively 4–5 months with no recovery season

### Temperature

- Coolest month (July): ~22°C mean
- Warmest month (October): ~26°C mean (rising under climate change projections)
- Daily mean: ~23°C

### Climate Risk Profile

| Risk | Hazard Level | Notes |
|------|-------------|-------|
| **River flooding** | HIGH (ThinkHazard) | Kaliua and Nzega flooded April 2018; increasing intensity projected |
| **Intra-seasonal dry spells** | HIGH (literature) | Dec–Feb dry spells critical during vegetative growth; 30-day post-planting dry spell risk documented |
| **Late onset of rains** | SIGNIFICANT | Delays transplanting, compresses entire season |
| **Temperature increase** | HIGH (CMIP6) | Tabora among regions with highest projected temperature rise in Tanzania |
| **Curing-season rainfall** | MODERATE | Excessive March–April rain degrades flue-cured leaf quality |
| **Long-term drought** | LOW (ThinkHazard) — contested | ThinkHazard low rating conflicts with agricultural literature; treat with caution |

### Comparison with Morogoro (Current Pilot)

| Feature | Tabora | Morogoro |
|---------|--------|----------|
| Climate zone | Tropical savanna (Aw) | Tropical savanna (Aw) |
| Annual rainfall | 700–1,000 mm | 800–1,200 mm |
| Rainfall pattern | **Strongly unimodal** (Nov–Apr only) | Bimodal influence, wetter |
| Elevation | ~1,200 m | ~500 m |
| Dry season | May–Oct (complete dry) | June–Aug main dry |
| Primary crop | Flue-cured Virginia tobacco | Rice |
| Climate character | Drier, inland continental | Wetter, Indian Ocean influence |
| Recovery season if crop fails | None | Partial |

**Key modelling implication:** Tabora's unimodal season means a missed trigger year is a total loss year for the farmer. There is no corrective second season. Trigger thresholds must be calibrated conservatively and basis risk minimised more aggressively than in Morogoro.

---

## 2. Tobacco Farming in Tabora

### National Context

Tanzania is now **Africa's second-largest tobacco producer** (after Zimbabwe):
- 2023/24 production: **122,858 metric tons**
- Export value: **USD 340 million (2023)**, up 90% year-on-year from USD 178 million (2022)
- Registered growers nationally: **~80,000+ (2024/25)**, up from ~11,000 in 2022 (government price reforms drove surge)
- Production targets: 200,000 MT for 2024/25; 300,000 MT for 2025/26

### Tabora's Dominance

- Tabora has historically accounted for **approximately 50% of national tobacco output** (most cited figure in literature; exact current share requires TTB confirmation)
- Tabora registered growers: **7,901 in 2017/18** (most recent publicly available regional figure; real current count is almost certainly substantially higher given national surge — requires direct TTB engagement)
- TTB offices in Tabora with dedicated tobacco offices: Urambo, Kaliua, Sikonge

### Tobacco Type

- **Flue-cured Virginia (FCV) dominates** — ~80% of Tanzania's national crop; Tabora and Iringa are the primary producing regions
- Burley tobacco is secondary
- FCV is the highest-value type and the most climate-sensitive for trigger design

### Growing Season (Tobacco Calendar)

| Phase | Months | Climate dependency |
|-------|--------|--------------------|
| Nursery/seedbed | July–September | Dry season — irrigated nurseries |
| Transplanting | October–November | Requires first rains onset |
| Vegetative growth | November–January | **Most critical** — rainfall deficit here destroys yield |
| Harvesting (leaf-by-leaf) | March–May | Some rain acceptable |
| Flue-curing | April–June | **Dry conditions required** — rain damages quality |

**The entire commercial crop is rain-fed and confined within the November–April window.**

### Farm Economics

| Metric | Value | Source |
|--------|-------|--------|
| Average farm size | ~9.6 acres (~3.9 ha, combined tobacco/maize) | PMC 2015 survey, 306 farmers |
| Typical tobacco yield | ~1,023 kg per farmer | PMC 2015 |
| Achievable yield | 1.65 t/ha current vs. 2.4 t/ha potential (K326 variety) | Literature |
| Minimum floor price 2024/25 | USD 2.10/kg | Mkwawa/TTB data |
| Export price per ton | USD 7,959/ton (2024), up from USD 4,151 (2023) | Tobacco Reporter |
| Gross revenue (1–2 ha at 1.65 t/ha, $2.10/kg) | USD 3,465–6,930/season | Calculated |

> **Important caveat:** Academic research (PMC, Tabora, 306 farmers) found that "when net income is estimated per acre or per manpower, farmers are often better off in non-tobacco crops." Input costs (fertiliser, pesticide, fuelwood for curing) are heavy. **Insurance product design should target input cost recovery + minimum income floor, not full gross revenue replacement.** The insurable interest is lower than gross leaf value suggests.

### Key Tobacco Buyers (Operating in Tabora)

All purchases are made at TTB-registered market centres through mandatory tripartite contracts (Primary Cooperative Society + Financier + Leaf Merchant).

| Buyer | Market Share | Tabora Operations |
|-------|-------------|-------------------|
| **Alliance One Tanzania Ltd (AOTTL)** | ~39% historically | Operates in Tabora; paid TZS 7.3 billion to farmers under 2023/24–2024/25 contracts |
| **Mkwawa Leaf Tobacco Ltd (MLT)** | 30%+ target | Contracted 26,000–27,400 smallholders by 2024/25; explicitly covers Sikonge, Urambo, Uyui, Kaliua, Tabora; volumes: 7,500 MT (2022) → 65,000 MT (2025) |
| **Premium Active Tanzania Ltd (PATL)** | Smaller share | Third buyer |

---

## 3. Climate Risks to Tobacco in Tabora

### Primary Yield-Destroying Events

1. **Rainfall deficit / dry spell during December–February (vegetative growth):**
   The most critical risk. Water below 50% field capacity during vigorous growth reduces leaf number, causes premature lower-leaf aging, induces upper-leaf shrinkage and thickening, and stunts root development. Tabora's intra-seasonal dry spells are well-documented; 30-day post-planting dry spell risk is a known hazard at Tabora station.

2. **Late onset of rains (October–November):**
   Delays transplanting, compresses the entire season, forces late-harvest scheduling, and exposes crop to water stress during critical early stages. Late onset past November 15–20 is a documented trigger for partial season failure.

3. **Excessive rain during March–April curing:**
   Rain during flue-curing causes fermentation, mould, and leaf discolouration — degrading quality grade and therefore price received. This is a quality loss trigger, not a quantity trigger, but it affects farmer net income directly.

4. **High temperature events (>30–32°C) during October–November transplanting:**
   Causes wilting, leaf deformity, necrotic spots; reduces photosynthesis. October pre-planting temperatures average 26°C and are rising under climate projections.

5. **River flooding (April, Kaliua and Nzega districts):**
   ThinkHazard rates Tabora river flood risk as HIGH. Documented event: Kaliua and Nzega flooded April 2018. Increasing intensity expected under CMIP6 models.

### Historical Loss Events

- **1990s drought/wind events:** Attributed partly to rapid deforestation from tobacco expansion (240,000 ha of miombo woodland cleared in ~20 years)
- **April 2018:** Flooding in Kaliua and Nzega (core tobacco districts)
- **2023:** Tanzania Agriculture Insurance Consortium (TAIC) paid **TZS 3 billion+ to Tabora tobacco farmers** following confirmed natural disaster losses — the clearest direct evidence that large-scale climate loss events occur and are insurable in Tabora

### Climate Change Projections (Tabora Specific)

- Tabora is among Tanzanian regions with the **highest projected temperature increase** under CMIP6 models
- **Increasing drought frequency** confirmed in semi-arid western Tanzania over recent decades
- **High confidence in more intense precipitation events** (ThinkHazard) — paradoxically more severe dry spells AND more intense flood events
- Projected 2050: significant temperature rise, rainfall decline, woodland loss — all compounding crop stress
- Tobacco is particularly vulnerable because climate stress degrades both **yield quantity AND leaf quality grade**, reducing both volume and price simultaneously

---

## 4. Insurance & Financing Landscape

### Existing Products — Direct Precedents

**This is the most important section for validating the opportunity:**

1. **ACRE Africa / NBC Tanzania Weather Index Insurance (WII):**
   - Launched ~2021; active in Tabora, Kigoma, Geita, Shinyanga
   - Uses satellite rainfall data (parametric index)
   - Enrolled **1,280+ tobacco farmers** by mid-2023
   - Bundled with NBC Tanzania agricultural loans
   - *This is the closest direct precedent — a functioning parametric tobacco insurance product in Tabora is already operational*

2. **Tanzania Agriculture Insurance Consortium (TAIC / Konsotia ya Bima ya Kilimo):**
   - Launched July 1, 2023 — 15 insurance companies, government-backed under ATI
   - **Started with tobacco as the initial crop**
   - Paid **TZS 3 billion+ to Tabora tobacco farmers** in 2023 after confirmed climate losses
   - Target: registration of 5 million farmers nationally
   - *TAIC is the domestic risk pool that effectively sidesteps international reinsurer ESG exclusions*

**HewaSense differentiation over ACRE Africa/NBC:**
- Multi-peril coverage (drought + flood + crop failure via NDVI) vs. their single rainfall index
- Phase-based triggers aligned with tobacco phenology — more precise, lower basis risk
- Direct buyer-embedded distribution (Alliance One / Mkwawa channel) vs. bank-bundled
- Forward-validated evidence pack (shadow run Brier Scores) vs. purely historical calibration

### Financing Landscape — By Source

| Source | Status for Tobacco | Notes |
|--------|-------------------|-------|
| **Tobacco buyers (Alliance One, Mkwawa)** | ✅ Most viable | Strong incentives to protect farmer income + reduce input-debt defaults; have farmer registries, field agents, deduction mechanisms |
| **TAIC domestic pool** | ✅ Active and paying | Already insuring Tabora tobacco; domestic pool bypasses international reinsurer ESG exclusions |
| **NBC Tanzania / CRDB** | ✅ Viable | NBC already demonstrated with ACRE Africa; loan-bundled model works |
| **IFC** | ❌ **Hard exclusion** | IFC formally excludes "production or trade in tobacco" from all financing — policy, no exceptions |
| **World Bank** | ❌ **Hard exclusion** | Formal policy prohibiting tobacco lending |
| **USAID Feed the Future** | ❌ Excluded | Does not support tobacco; Feed the Future mandate is food security crops |
| **GIZ (BMZ-funded)** | ❌ Likely excluded | German development cooperation ESG screens exclude tobacco |
| **IFAD** | ⚠️ Uncertain | IFAD does not specifically target tobacco; eligibility unclear — would require direct query |
| **Munich Re / Swiss Re** | ⚠️ Withdrawing | Both have committed to ESG-driven withdrawal from tobacco underwriting under Tobacco Free Finance Pledge (130 signatories) |
| **GSMA M4D** | ❌ Unlikely | Focuses on food security/nutrition crops |

**Conclusion on financing:** The Scenario B (donor/NGO ~40% grant) pathway used for the Morogoro rice pilot **does not apply cleanly to tobacco**. The funding path for Tabora tobacco runs through **buyers + TAIC + domestic banking** — not international development finance. This is a material structural difference from the rice pilot.

### Distribution Channel Assessment

The mandatory TTB tripartite contract farming system provides a **superior distribution channel** compared to most crops:

- Every farmer is registered with TTB by name and district
- Buyers maintain pre-season input credit relationships with all enrolled farmers
- Post-harvest premium deduction from crop payment is possible (no cash collection problem)
- Alliance One and Mkwawa have field agent networks across all six tobacco districts
- TTB market-centre infrastructure provides verified farmer identity (eliminates fraud risk)

This is the same model ACRE Africa + NBC Tanzania operate — but going directly through buyers eliminates the bank intermediary and dramatically reduces distribution cost.

---

## 5. Regulatory & Institutional Context

### Tanzania Tobacco Board (TTB)

- Established: Tobacco Industry Act No. 24 of 2001 (amended 2009)
- **Mandatory farmer registration:** No farmer may grow tobacco without TTB registration under a Primary Cooperative Society or individual registration
- **Tripartite system:** 100% of crop grown through formal three-party contracts (cooperative + financier + buyer)
- **Market control:** All tobacco sold at TTB-registered centres with TTB classifiers; buyers must pay within 14 days of purchase
- **Tree-planting mandate:** TTB requires tobacco farmers to plant trees to offset curing fuelwood use (ESG mitigation mechanism)
- **TTB offices in tobacco districts:** Urambo, Kaliua, Sikonge — all core Tabora tobacco areas

**For insurance:** TTB's verified farmer registry eliminates the identity and farmer-count uncertainty that plagues other crop insurance programmes. Enrolment can be cross-referenced against TTB records.

### TIRA — Regulatory Position

- Active supporter of index-based and parametric insurance — collaborated with NIC and Ministry of Agriculture on national index insurance strategy since 2014–15
- Over 60 new insurance products approved 2021–2024, including climate risk covers and crop insurance
- **Formal TIRA regional engagement in Tabora: December 2, 2023** (TIRA regional launch event) — indicates active on-the-ground presence
- No identified regulatory barriers to parametric tobacco insurance; TIRA framework is accommodating

---

## 6. Technical Feasibility

### Climate Data Coverage

All data sources used in the current HewaSense pipeline confirm full Tabora coverage:

| Dataset | Coverage | Tabora Status |
|---------|----------|---------------|
| **CHIRPS v3** | Global (60°N–60°S) | ✅ Full coverage at ~5°S, 32.8°E; 0.05° (~5km) resolution; data from 1981 |
| **ERA5** | Global | ✅ Full coverage; 0.25° (~28km) resolution; 1979–present |
| **NASA POWER** | Global | ✅ Full coverage; 0.5° resolution; 1981–present |
| **MODIS/Landsat NDVI** | Global | ✅ Full coverage; 250m–500m; 2000–present |

**Pipeline change required:** Add one Location record (Location ID 7 = Tabora), ingest historical data, retrain or extend training dataset, calibrate tobacco-specific thresholds. No architectural changes.

### Proposed Parametric Indices for Tobacco

Based on literature synthesis and crop-climate interaction analysis:

| Index | Trigger Window | Threshold (Indicative) | Justification |
|-------|---------------|----------------------|---------------|
| **Cumulative Growing Season Rainfall (CGSR)** | November–March | < 500–600 mm total | Strongest predictor of tobacco yield; CHIRPS 5km resolution; primary drought trigger |
| **Dry Spell Index (DSI)** | December–February | > 21 consecutive dry days | Vegetative growth most critical; 30-day post-planting dry spell risk documented in Tabora |
| **Late Onset of Rains** | October–November | First significant rain > Nov 15–20 | Delayed onset compresses season and reduces yield potential |
| **NDVI Anomaly** | January (peak vegetative) | > −1.5σ deviation from 10-year mean | Vegetation health proxy; validated in Tanzania WII pilots |
| **Curing-Season Excessive Rain** | March–April | > defined mm threshold over defined period | Damages flue-cured leaf quality; quality loss trigger |
| **Temperature Maximum Index** | October–November | Days > 32°C | Rising temperatures during transplanting phase |

> **Note:** All thresholds above are indicative pending calibration against historical Tabora data (2000–2025). Calibration methodology follows the same approach as Morogoro (26-year historical analysis, trigger rate targeting, loss ratio validation).

### Modelling Considerations Specific to Tobacco

1. **Unimodal season = no margin for error:** Unlike Morogoro's bimodal influence, a failed trigger year in Tabora is a total loss with no corrective season. Thresholds must be calibrated conservatively.
2. **Quality degradation trigger:** Tobacco has a unique trigger type — excessive rain during curing causes quality loss, not physical crop destruction. This requires an NDVI-proxied or direct rainfall trigger tied to the post-harvest window, distinct from standard crop failure triggers.
3. **Higher premium justified:** Tobacco's cash-crop status and higher gross revenue per hectare (relative to subsistence rice) supports a higher absolute premium and payout rate than the rice pilot.

---

## 7. Risks, Complications, and Mitigations

### Risk 1 — ESG/Tobacco Controversy (CRITICAL)

**Issue:**
- IFC, World Bank, most multilateral donors formally exclude tobacco from financing
- Munich Re and Swiss Re are withdrawing from tobacco underwriting under Tobacco Free Finance Pledge (130 financial institution signatories)
- Deforestation: 4,134 ± 390 ha of undisturbed miombo woodland destroyed annually in Tabora for tobacco curing fuelwood
- Child labour: ILO documentation exists for Tabora tobacco-growing communities
- This is a structural funding constraint, not a reputational risk only

**Mitigation:**
- Restrict funding search to buyers (Alliance One, Mkwawa), TAIC, and domestic banking (NBC, CRDB)
- Frame the product as **smallholder household resilience and income stabilisation** — not tobacco industry support. This framing is accurate: insurance helps farmers weather losses and reduces input-debt defaults, regardless of the crop
- Reference ACRE Africa's successful framing precedent
- Acknowledge deforestation context; TTB's mandatory tree-planting and emerging solar barn pilots are the mitigation narrative
- Accept that international development finance (IFC, World Bank, USAID, GIZ) is effectively unavailable for this module

### Risk 2 — Net Income Per Farmer May Be Very Low

**Issue:** PMC academic research (Tabora, 306 farmers) found that net income per acre for tobacco farmers may be lower than for alternative crops once inputs are counted. Heavy input costs (fertiliser, pesticide, fuelwood) compress margins.

**Mitigation:** Product structure should target **input cost recovery + minimum income floor** (not gross revenue replacement). Payout rates should be calibrated to cover the farmer's actual out-of-pocket loss, not theoretical gross leaf value.

### Risk 3 — Existing Competition (ACRE Africa/NBC)

**Issue:** ACRE Africa + NBC Tanzania already operates a parametric tobacco insurance product in Tabora with 1,280+ enrolled farmers.

**Mitigation:** Differentiate on multi-peril coverage breadth, tobacco phase-based precision triggers, direct buyer-embedded distribution channel, and forward-validated Brier Score evidence pack (ACRE Africa has no equivalent evidence pack).

### Risk 4 — Stale Farmer Count Data

**Issue:** The only publicly available Tabora-specific registered farmer count is 7,901 from 2017/18. National numbers have surged to 80,000+ by 2024; Tabora's share is unknown without TTB engagement.

**Mitigation:** Engage TTB directly to obtain current district-level registered farmer counts before committing to pilot scope. This is a pre-condition for pilot sizing.

### Risk 5 — Reinsurance Gap

**Issue:** With Munich Re and Swiss Re withdrawing, finding reinsurance capacity for a tobacco-specific parametric product is harder than for food crops.

**Mitigation:** TAIC (domestic pool) is the primary reinsurance backstop. The Brier Score evidence pack from the shadow run will be the key document to demonstrate actuarial soundness to any reinsurer approached.

---

## 8. Recommended Path Forward

### Timing

**Do not proceed before mid-2026.** This is not ready to action during the shadow run period. The shadow run must complete and the evidence pack (Brier Score < 0.25, basis risk < 30%) must be in hand before any expansion conversation. The evidence pack is the credibility foundation for any approach to buyers or TAIC.

### Pre-Conditions Before Commitment

1. **Shadow run gate passed** (Brier Score < 0.25, mid-2026)
2. **TTB engagement:** Direct query to TTB for current district-level registered farmer counts
3. **Buyer partnership conversation:** Approach Alliance One or Mkwawa about embedded distribution — are they interested in co-financing insurance as part of their contract farming obligations?
4. **TAIC alignment:** Confirm TAIC is open to including HewaSense-modelled parametric tobacco product in their pool

### Recommended Pilot Design (If Gate Passed)

- **Scope:** 1,000 tobacco farmers, Urambo or Uyui district (highest TTB registration density), Tabora Region
- **Crop:** Flue-cured Virginia tobacco
- **Premium structure:** Buyer-co-financed (buyers deduct premium from crop payment post-harvest); target $15–25/farmer/season reflecting higher cash-crop value
- **Coverage:** Drought (December–February dry spell or CGSR deficit) + Flooding (April, Kaliua/Nzega) + Crop failure (January NDVI anomaly) + Curing quality loss (March–April excessive rain)
- **Distribution partner:** Alliance One or Mkwawa (whichever engages first)
- **Reinsurance backstop:** TAIC domestic pool
- **Regulatory:** TIRA submission alongside (or shortly after) Morogoro rice submission, leveraging same evidence pack format

### Financing Scenario (Tobacco-Specific)

| Scenario | Source | Farmer Pays | Notes |
|----------|--------|-------------|-------|
| **D — Buyer co-financed** | Alliance One / Mkwawa contribution | ~$10/year | Buyer deducts from crop payment; most viable near-term |
| **E — Farmer self-pay** | No subsidy | $15–25/year | Viable only if price reforms continue; higher premium justified by cash-crop status |
| **F — TAIC pool subsidy** | Government-backed domestic pool | TBD | TAIC has tobacco mandate; may co-subsidise |

> Note: Standard Scenarios A/B/C (Morogoro rice) do not apply cleanly here due to tobacco ESG financing exclusions. Buyer co-financing (Scenario D) is the primary near-term path.

---

## 9. Key Numbers at a Glance

| Metric | Value | Source / Date |
|--------|-------|---------------|
| Tabora coordinates | ~5.0°S, 32.8°E | Geographic standard |
| Elevation | ~1,200 m | Britannica |
| Annual rainfall | 700–1,000 mm | Climate records |
| Rain season | November–April (unimodal) | Meteorological data |
| Tanzania national tobacco output | 122,858 MT (2023/24) | Kilimo Kwanza |
| Tanzania Africa rank | 2nd (after Zimbabwe) | Tobacco Asia, 2024 |
| National registered growers | ~80,000+ (2024/25) | Hot Commodity, 2024 |
| Tabora registered growers | 7,901 (2017/18 — stale; needs TTB update) | Statista/MoA |
| Tabora share of national output | ~50% (historical estimate) | Multiple sources |
| Dominant type | Flue-cured Virginia (~80% nationally) | TTB/literature |
| Transplanting | October–November | Growing season |
| Harvest | March–May | Growing season |
| Average farm size (Tabora) | ~9.6 acres / ~3.9 ha | PMC 2015, 306 farmers |
| Average yield per farmer | ~1,023 kg | PMC 2015 |
| Floor price 2024/25 | USD 2.10/kg | Mkwawa/TTB |
| Major buyers | Alliance One, Mkwawa (MLT), PATL | Trade press |
| Flood hazard | HIGH (ThinkHazard) | ThinkHazard 2024 |
| Existing WII product | ACRE Africa/NBC — 1,280+ farmers in Tabora | UNSGSA 2023 |
| TAIC payout to Tabora tobacco | TZS 3 billion+ (2023) | Kilimo Kwanza |
| IFC/World Bank tobacco finance | ❌ Excluded by policy | IFC Exclusion List |
| Munich Re / Swiss Re underwriting | ⚠️ Withdrawing | Tobacco Free Finance Pledge |
| TAIC domestic pool | ✅ Active, tobacco mandate | Launched July 2023 |
| All climate data sources | ✅ Full coverage at Tabora coordinates | CHIRPS, ERA5, NASA POWER, NDVI |

---

## 10. Next Review

**Review date:** Mid-2026 — coincides with shadow run evidence pack completion and Go/No-Go decision.

**At that review, assess:**
1. Did the shadow run pass the gate (Brier Score < 0.25)?
2. Has TTB engagement happened — do we have current farmer counts?
3. Have initial conversations with Alliance One or Mkwawa occurred?
4. Is TAIC receptive to a HewaSense-modelled tobacco product?

If all four are positive: proceed to Tabora tobacco pilot design in parallel with Morogoro rice live pilot.

---

## References

- Tanzania Tobacco Board (TTB): tobaccoboard.go.tz — regulatory framework, tripartite system
- PMC (2015): Comparative analysis of smallholder tobacco and maize farmers in Tabora — farm size, yield, net income
- Kilimo Kwanza (2024): Tanzania rises to Africa's second-largest tobacco producer
- TAIC Launch (July 2023): TanzaniaInvest — TZS 3 billion payout to Tabora tobacco farmers
- UNSGSA (2023): ACRE Africa/NBC Tanzania WII — 1,280+ tobacco farmers enrolled
- ThinkHazard — Tabora: river flood (HIGH), water scarcity (LOW — treat with caution vs. literature)
- PMC (2026): Future climate projections across Tanzania under CMIP6
- IFC Exclusion List (2007): formal tobacco financing exclusion
- World Bank Policy on Tobacco: formal tobacco lending prohibition
- Tobacco Free Finance Pledge (UNEP FI): 130 financial institution signatories
- Besra Journals: Tobacco Insurance in Africa — reinsurance gap analysis
- Frontiers in Agronomy (2025): Pedological characterisation of soils under tobacco cultivation in Tabora Region
- Frontiers in Plant Science (2024): Tobacco production under global climate change
- Mkwawa Leaf Tobacco Ltd (2024): The Citizen / Daily News — farmer contracts, volumes, Tabora districts

---

**Document Owner**: HewaSense Climate Intelligence & Parametric Insurance Team
**Created**: March 22, 2026
**Next Review**: Mid-2026 (post shadow run gate)
**Status**: SCOPING — not committed to roadmap until post-shadow-run pre-conditions are met
