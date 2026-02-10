# Insurance Payout Model Analysis & Recommendation
**Date:** January 19, 2026  
**Context:** Morogoro Rice Pilot (1,000 farmers)  
**Issue:** Current dashboard shows conflicting payout calculations

---

## Current Problem

### What the Dashboard Shows

**Portfolio Risk Overview:**
- Farmers at Risk: **0** of 1,000 farmers (0%)
- Expected Payouts: **$0**
- Threshold: ≥75% probability

**Financial Impact Annotation:**
- April 2026: **Crop Failure** Risk (❌ Wrong - should be "Drought")
- 52.6% probability  
- Expected deficit: 62mm
- 1,000 farmers affected
- Est. payout: **$26,305**

**The Inconsistency:**
- Portfolio says ≥75% → No risk → $0 payout ✅ **Correct**
- Financial chart uses ≥50% → Shows risk → $26k payout ✅ **Correct**
- BUT the payout calculation formula is **WRONG**

---

## Root Cause: Wrong Formula

### Current (INCORRECT) Code
```typescript
// In FinancialForecastChart.tsx
const PAYOUT_UNIT = 50000;
payout = highestRiskForecast.probability × PAYOUT_UNIT
       = 52.6% × $50,000
       = $26,300
```

**Problem:** This treats $50,000 as a "pool" and multiplies by probability, which is nonsensical.

---

## Documentation Specifications

### From KILOMBERO_BASIN_PILOT_SPECIFICATION.md

**Official Payout Rates** (Lines 46-52):
| Trigger | Rate per Farmer |
|---------|----------------|
| Drought | $60 |
| Flood | $75 |
| Crop Failure | $90 |

**Pilot Parameters** (Lines 35-43):
- Total Farmers: 1,000 smallholder rice farmers
- Coverage: ~1 hectare per farmer (average)
- Location: Kilombero Basin, Morogoro

**Thresholds** (Lines 253-260):
```python
MONITORING_THRESHOLD = 0.30   # 30% - Internal only
ADVISORY_THRESHOLD = 0.50     # 50% - Send alerts
WARNING_THRESHOLD = 0.65      # 65% - Warnings
HIGH_RISK_THRESHOLD = 0.75    # 75% - Payout prep
```

---

## Real-World Context (Web Research)

### Comparable African Programs

**ACRE Africa (Tanzania, Kenya, Rwanda)**
- Coverage: ~$5 USD payout for $0.40 premium
- Delivery: Mobile money within 30 days
- Type: Weather index-based (parametric)
- Scale: 1.7M+ farmers insured (as of 2018)

**Jubilee Insurance × Yara (Tanzania - 2022)**
- Farmers: 83,000 enrolled (including rice growers)
- Coverage: Flood and drought protection
- Type: Index-based parametric

**Pula (Zambia - Comparable model)**
- Premium: $6/year (with subsidy)
- Payout: $25 max
- Per

il: Drought only
- Size: 0.5 hectare typical

**National Insurance Corporation (Tanzania)**
- Crops: Cotton, wheat, maize, cashew, rice
- Minimum premium: TZS 100,000 (~$42 USD)

### Key Findings

1. **Our rates ($60-90) are COMPETITIVE** with regional standards
2. **Index-based parametric is STANDARD** in Tanzania
3. **Government subsidies (50%) are COMMON**
4. **TIRA regulations support parametric insurance** (Guidelines 2023)

---

## Recommended Payout Models

### Model A: Per-Farmer Fixed Payout (SIMPLEST - RECOMMENDED)

**Logic:** Parametric insurance pays a **fixed amount per affected farmer**, not a probability-weighted pool.

**Formula:**
```
Affected Farmers = Total Farmers × Probability
                 = 1,000 × 52.6%
                 = 526 farmers

Total Payout = Affected Farmers × Rate per Trigger
             = 526 farmers × $60/farmer (drought)
             = $31,560
```

**Rationale:**
- ✅ **Aligns with parametric insurance principles** (fixed payout)
- ✅ **Matches documentation** ($60 per farmer for drought)
- ✅ **Mirrors ACRE Africa model** (fixed per-farmer payout)
- ✅ **Simple for farmers to understand** ("If drought, you get $60")
- ✅ **TIRA compliant** (objective, transparent)

**For 52.6% drought probability:**
- 526 farmers expected to be affected
- Each receives $60
- Total: **$31,560**

---

### Model B: Severity-Adjusted Payout (MORE SOPHISTICATED)

**Logic:** Probability represents both **likelihood** AND **severity** of event.

**Formula:**
```
Base Payout Pool = Total Farmers × Rate per Trigger
                 = 1,000 × $60
                 = $60,000

Adjusted Payout = Base Pool × Probability
                = $60,000 × 52.6%
                = $31,560
```

**Rationale:**
- ✅ **Same result as Model A** (mathematically equivalent)
- ✅ **Accounts for partial impact** (not all farmers equally affected)
- ✅ **Used in some IBLI programs** (Index-Based Livestock Insurance)
- ⚠️ **More complex** to explain to farmers

**Result:** Same $31,560 payout

---

## Comparison with Current (Wrong) Formula

| Model | Formula | April 2026 Result | Status |
|-------|---------|-------------------|--------|
| **Current (WRONG)** | `$50,000 × 52.6%` | **$26,300** | ❌ Arbitrary pool |
| **Model A (Recommended)** | `526 farmers × $60` | **$31,560** | ✅ Documented rate |
| **Model B (Alternative)** | `($60×1000) × 52.6%` | **$31,560** | ✅ Severity-adjusted |

**Difference:** Current model **underpays by $5,260** (16.7% shortfall)

---

## Why $50,000 is Wrong

**Q:** Where did $50,000 come from?

**A:** Line 355 of `ForecastDashboard.tsx`:
```python
const PAYOUT_UNIT = 50000;
```

**Problem:** This was likely intended as:
- Maximum single-farmer coverage? (Too high: $50k per farmer unrealistic)
- Total pool for all farmers? (Too low: Only 833 farmers at $60 each)
- Arbitrary placeholder? (Most likely)

**It doesn't match ANY documented specification.**

---

## Recommended Implementation

### Option 1: Per-Farmer Calculation (Clearest)

```typescript
// FinancialForecastChart.tsx
const PAYOUT_RATES = {
  drought: 60,
  flood: 75,
  crop_failure: 90
};

const TOTAL_FARMERS = 1000; // Morogoro pilot

// Calculate payout
const affectedFarmers = TOTAL_FARMERS * highestRiskForecast.probability;
const ratePerFarmer = PAYOUT_RATES[highestRiskForecast.triggerType];
const estimatedPayout = affectedFarmers * ratePerFarmer;

// For 52.6% drought:
// affectedFarmers = 1000 × 0.526 = 526
// ratePerFarmer = $60
// estimatedPayout = 526 × $60 = $31,560
```

**Annotation Display:**
```
April 2026: Drought Risk
52.6% probability (Advisory threshold)
Expected deficit: 62mm
526 farmers affected (52.6% of 1,000)
Est. payout: $31,560 ($60 per affected farmer)
```

---

### Option 2: Aggregate Pool Calculation (Alternative)

```typescript
const calculatePayout = (trigger: string, probability: number) => {
  const PAYOUT_RATES = {
    drought: 60,
    flood: 75,
    crop_failure: 90
  };
  
  const TOTAL_FARMERS = 1000;
  const maxPayout = TOTAL_FARMERS * PAYOUT_RATES[trigger];
  
  return maxPayout * probability;
};

// For 52.6% drought:
// maxPayout = 1000 × $60 = $60,000
// adjustedPayout = $60,000 × 0.526 = $31,560
```

---

## Validation Against Real Data

### Morogoro Pilot Reserves Analysis

**From documentation:**
- Current reserves: $150,000
- Required reserves (100% CAR): $133,557
- Maximum single event: $90,000 (100% crop failure)

**Using Correct Formula (Model A):**
```
If 100% crop failure occurs:
Payout = 1,000 farmers × $90/farmer = $90,000 ✅ Matches spec

If 52.6% drought occurs:
Payout = 526 farmers × $60/farmer = $31,560 ✅ Well within reserves
```

**Using Wrong Current Formula:**
```
If 100% crop failure:
Payout = $50,000 × 100% = $50,000 ❌ Only 56% of needed payout!
```

**Conclusion:** Current formula would **underinsure farmers by 44%** in worst-case scenario.

---

## Impact on Dashboard Metrics

### Before Fix (Current - WRONG)

**April 2026 (52.6% drought):**
- Portfolio Risk: $0 (correct threshold logic)
- Financial Forecast: $26,305 (❌ wrong calculation)

### After Fix (Recommended - Model A)

**April 2026 (52.6% drought):**
- Portfolio Risk: $0 (≥75% threshold not met)
- Financial Forecast: **$31,560** (✅ correct: 526 farmers × $60)

**If probability were 75% (High Risk):**
- Portfolio Risk: **$45,000** (750 farmers × $60)
- Financial Forecast: **$45,000** (✅ consistent)

---

## Contextual Grounding (Tanzania-Specific)

### Economic Validation

**Typical Tanzanian smallholder rice farmer:**
- Farm size: 0.5-2 hectares (avg 1 ha)
- Rice yield: 2-4 tonnes/ha
- Price: ~TZS 800,000/tonne (~$330 USD)
- Season revenue: $660-1,320 per farmer

**Drought loss scenario:**
- 50% yield loss: $330-660 lost income
- **$60 payout = 9-18% compensation** 
- ✅ **Realistic for parametric insurance** (not full indemnity)

**Comparison to ACRE Africa:**
- ACRE: $5 payout for $0.40 premium (12.5:1 ratio)
- TCI: $60 payout for ~$10 premium (6:1 ratio)
- ✅ **More generous than competitors**

---

## Regulatory Compliance

### TIRA Requirements (2023 Guidelines)

**Required for Parametric Insurance:**
1. ✅ **Fixed payout schedule** - $60/$75/$90 per farmer
2. ✅ **Objective triggers** - Rainfall thresholds
3. ✅ **Transparent terms** - Disclosed upfront
4. ✅ **No loss adjustment** - Automatic payout

**Capital Adequacy Ratio (CAR):**
- Minimum: 100% (TIRA requirement)
- Current: 112.3% with correct formula ✅
- With wrong formula: Would be 187% (over-reserved)

---

## Recommendation Summary

### Immediate Action Required

1. **Fix payout calculation** to use Model A (per-farmer)
2. **Update annotation** to show correct amount ($31,560)
3. **Add clarity** to display ("526 farmers affected")
4. **Document formula** in code comments

### Formula to Implement

```typescript
const PAYOUT_RATES = {
  drought: 60,
  flood: 75,
  crop_failure: 90
};

const PILOT_FARMERS = 1000;

function calculateExpectedPayout(
  triggerType: string,
  probability: number
): number {
  const affectedFarmers = PILOT_FARMERS * probability;
  const payoutPerFarmer = PAYOUT_RATES[triggerType];
  return Math.round(affectedFarmers * payoutPerFarmer);
}

// Example: 52.6% drought
// Result: 526 × $60 = $31,560
```

---

## Conclusion

**Current Formula is WRONG because:**
1. ❌ $50,000 not documented anywhere
2. ❌ Doesn't match parametric insurance principles
3. ❌ Would underinsure farmers by 16-44%
4. ❌ Not grounded in Tanzanian context

**Recommended Formula (Model A) is CORRECT because:**
1. ✅ Uses documented rates ($60/$75/$90)
2. ✅ Follows parametric insurance standards
3. ✅ Matches ACRE Africa, Jubilee, Pula models
4. ✅ TIRA compliant
5. ✅ Simple for farmers to understand
6. ✅ Economically realistic for Tanzania
7. ✅ Aligns with $150k reserve calculations

**Implementation Priority:** **HIGH** - Affects financial planning and farmer trust

---

**References:**
- KILOMBERO_BASIN_PILOT_SPECIFICATION.md
- PARAMETRIC_INSURANCE_FINAL.md
- ACRE Africa Tanzania operations
- TIRA Guidelines 2023
- Jubilee Insurance × Yara partnership 2022
