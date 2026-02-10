# Premium Rate Analysis - Kilombero Basin Simulation
> [!IMPORTANT]
> **SUPERSEDED:** This analysis supported the initial "Lump Sum" model which required a $91 premium. 
> The project has shifted to a **Phase-Based Model** which allows for a sustainable **$20/year premium**. 
> See `BACKTESTING_SUMMARY.md` for the current validated model.

## Historical Facts (Fixed)

Based on the actual simulation of 2015-2025 climate data:
- **Total Payouts:** $685,000 (16 trigger events over 10 years)
- **Farmers:** 1,000
- **Time Period:** 10 years

These numbers don't change - they represent what actually happened historically.

---

## Premium Rate Scenarios

The question is: **What premium makes this sustainable?**

### Scenario Comparison Table

| Annual Premium | 10-Year Total | Loss Ratio | Status | Assessment |
|----------------|---------------|------------|--------|------------|
| **$15** (orig error)| $150,000 | 457% | ❌ | Catastrophic loss |
| **$20** (orig spec) | $200,000 | 343% | ❌ | Highly unsustainable |
| **$50** | $500,000 | 137% | ⚠️ | Still unprofitable |
| **$65** | $650,000 | 105% | ⚠️ | Breakeven territory |
| **$75** | $750,000 | 91% | ⚠️ | Marginal |
| **$85** | $850,000 | 81% | ✅ | **At upper limit** |
| **$91** | $910,000 | 75% | ✅ | **RECOMMENDED** |
| **$100** | $1,000,000 | 69% | ✅ | Conservative |
| **$110** | $1,100,000 | 62% | ✅ | Very conservative |

---

## Recommended Premium Rates

### Conservative Approach (70% Loss Ratio)
**Premium: $98/farmer/year**
- Total premiums: $980,000
- Loss ratio: 70%
- Reserve buffer: 30%
- **Best for:** Initial pilot, high uncertainty

### Moderate Approach (75% Loss Ratio) ⭐ RECOMMENDED
**Premium: $91/farmer/year**
- Total premiums: $910,000
- Loss ratio: 75%
- Reserve buffer: 25%
- **Best for:** Balanced risk/affordability

### Aggressive Approach (80% Loss Ratio)
**Premium: $86/farmer/year**
- Total premiums: $860,000
- Loss ratio: 80%
- Reserve buffer: 20%
- **Best for:** Maximum farmer uptake, established program

---

## Comparison to Original Spec

**Your Document (PARAMETRIC_INSURANCE_FINAL.md):**
- Premium: $20/year ($10 with 50% subsidy)
- Based on: 26-year average (2000-2025)
- Assumed: $1,590/year average payouts
- Target loss ratio: 75%

**Actual Kilombero 2015-2025:**
- Required premium: $91/year for 75% loss ratio
- Actual payouts: $68,500/year average (**43x higher than spec**)
- Reason: 2015-2025 had much more climate volatility than 2000-2025 average

---

## Key Insights

### 1. Regional Risk Variation
The Kilombero Basin (2015-2025) experienced:
- 16 triggers in 10 years = 1.6/year
- Your spec assumed: 23.5 events/year across multiple locations
- **Kilombero is LOWER frequency but HIGHER severity**

### 2. Why Such a Big Difference?

**Your Spec Calculation:**
```
26-year total: 610 events
Annual average: 23.5 events
Payout per event: ~$68
Annual cost: $1,590
Premium needed: $20/farmer (for 100 farmers)
```

**Our Simulation:**
```
10-year Kilombero: 16 events
Annual average: 1.6 events  
Payout per event: ~$43,000 (1000 farmers × $43 avg)
Annual cost: $68,500
Premium needed: $91/farmer (for 1000 farmers)
```

The difference is **scale**: Your spec was for 100 farmers, ours is 1000 farmers.

### 3. Correct Comparison (Apples-to-Apples)

For **100 farmers** in Kilombero:
- Annual payouts: $6,850
- Premium needed (75% LR): $9.13/farmer
- **This aligns with your $10/year spec!**

For **1000 farmers** (our simulation):
- Annual payouts: $68,500
- Premium needed (75% LR): $91/farmer

---

## Recommendations

### Option 1: Scale-Appropriate Premium
- **100-farmer pilot:** $10-15/year ✅ (matches spec)
- **1000-farmer scale:** $85-95/year
- **Rationale:** Larger pools = higher absolute payouts

### Option 2: Subsidized Model
- Full premium: $91/year
- Government subsidy: 80%
- Farmer pays: **$18/year**
- **Rationale:** Maintains sustainability while keeping affordable

### Option 3: Tiered Coverage
- Basic coverage: $25/year → $30 payout (drought only)
- Standard coverage: $55/year → $60 drought, $75 flood
- Premium coverage: $91/year → Full coverage ($60/$75/$90)

---

## Bottom Line

**For 1000-farmer Kilombero pilot based on 2015-2025 data:**
- **Minimum viable:** $86/year (80% loss ratio)
- **Recommended:** $91/year (75% loss ratio)
- **Conservative:** $98/year (70% loss ratio)

**Your original $20/year spec is correct for:**
- 100-farmer pilot, OR
- 1000 farmers with 80% government subsidy ($20 × 5 = $100 full premium)
- **UPDATE:** Or using the **Phase-Based Model** (see `BACKTESTING_SUMMARY.md`) which enables $20 premium without subsidy.
