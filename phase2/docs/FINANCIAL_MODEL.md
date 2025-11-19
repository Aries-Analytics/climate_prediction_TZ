# Financial Model Documentation

**Project:** Tanzania Climate Prediction - Parametric Insurance  
**Last Updated:** November 19, 2025  
**Status:** Production Ready

---

## Executive Summary

This document explains the financial structure of the parametric insurance product, including premium pricing, payout calculations, reinsurance arrangements, and sustainability metrics. The model is designed to be financially sustainable while providing meaningful coverage for climate-related risks.

---

## Table of Contents

1. [Premium Structure](#premium-structure)
2. [Payout Calculation](#payout-calculation)
3. [Reinsurance Structure](#reinsurance-structure)
4. [Financial Sustainability](#financial-sustainability)
5. [Example Scenarios](#example-scenarios)
6. [Configuration](#configuration)

---

## Premium Structure

### Per-Entity Pricing

Each insured entity (farmer, cooperative, or organization) pays an **annual premium of $2,400 USD**.

**Coverage Includes:**
- Drought protection
- Flood protection
- Crop failure protection

**Premium Assumptions:**
- Based on historical trigger rates (21.53% combined)
- Target loss ratio: <80%
- Includes administrative costs and profit margin

### Portfolio Assumptions

**Example Portfolio:**
- Total premium pool: $1,000,000/year
- Number of insured entities: 417 (calculated as $1M ÷ $2,400)
- Geographic coverage: Tanzania (single point location for MVP)

---

## Payout Calculation

### Base Payout Rates

When a trigger activates, the base payout depends on the trigger type:

| Trigger Type | Base Payout (USD) |
|--------------|-------------------|
| Drought | $500 |
| Flood | $750 |
| Crop Failure | $1,000 |
| Severe Stress | $300 |

**Note:** These rates are configured in `reporting/business_metrics.py` (line 217-222) and can be adjusted based on actuarial analysis.

### Adjustment Factors

The final payout is adjusted by two factors:

#### 1. Severity Multiplier

```
severity_multiplier = 0.5 + severity_score
```

- **severity_score**: Ranges from 0.0 (minor) to 1.0 (severe)
- **Result**: Multiplier ranges from 0.5× to 1.5× base payout

**Example:**
- Base flood payout: $750
- Severity score: 0.8 (severe flood)
- Multiplier: 0.5 + 0.8 = 1.3
- Adjusted payout: $750 × 1.3 = $975

#### 2. Confidence Adjustment

```
final_payout = base_payout × severity_multiplier × confidence_score
```

- **confidence_score**: Ranges from 0.0 to 1.0
- Reflects the reliability of the trigger detection

**Example:**
- Adjusted payout (from above): $975
- Confidence: 0.85 (high confidence)
- Final payout: $975 × 0.85 = $829

### Complete Payout Formula

```
final_payout = base_rate × (0.5 + severity) × confidence
```

### Multiple Triggers

When multiple triggers activate in the same month, payouts are summed:

**Example:**
- Drought trigger: $500 × 1.2 × 0.9 = $540
- Crop failure trigger: $1,000 × 1.1 × 0.8 = $880
- **Total monthly payout: $1,420**

---

## Reinsurance Structure

### Overview

Reinsurance protects the primary insurer from catastrophic losses by transferring excess risk to a reinsurer.

### Structure

```
┌─────────────────────────────────────────────────┐
│  Total Annual Payouts                           │
├─────────────────────────────────────────────────┤
│                                                 │
│  $10M+ ┌────────────────────────────────────┐  │
│        │  EXCESS (Not Covered)              │  │
│  $10M  ├────────────────────────────────────┤  │
│        │                                    │  │
│        │  REINSURANCE LAYER                 │  │
│        │  Coverage: $1M - $10M              │  │
│        │  (Reinsurer pays)                  │  │
│        │                                    │  │
│  $1M   ├────────────────────────────────────┤  │
│        │  PRIMARY RETENTION                 │  │
│        │  (Primary insurer pays)            │  │
│  $0    └────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Primary Retention** | $1,000,000 | Primary insurer pays first $1M of losses |
| **Attachment Point** | $1,000,000 | Reinsurance starts at $1M |
| **Coverage Limit** | $10,000,000 | Maximum reinsurance coverage |
| **Total Capacity** | $11,000,000 | Primary ($1M) + Reinsurance ($10M) |

### How It Works

**Scenario 1: Low Loss Year**
- Total payouts: $600,000
- Primary insurer pays: $600,000
- Reinsurer pays: $0
- **Primary insurer net loss: $600,000**

**Scenario 2: Moderate Loss Year**
- Total payouts: $3,500,000
- Primary insurer pays: $1,000,000 (retention)
- Reinsurer pays: $2,500,000 (excess over $1M)
- **Primary insurer net loss: $1,000,000**

**Scenario 3: Catastrophic Loss Year**
- Total payouts: $12,000,000
- Primary insurer pays: $1,000,000 (retention)
- Reinsurer pays: $9,000,000 (capped at $10M limit)
- Uncovered: $2,000,000 (exceeds total capacity)
- **Primary insurer net loss: $1,000,000 + $2,000,000 = $3,000,000**

### Reinsurance Premium

The primary insurer pays the reinsurer a premium for this coverage:

```
reinsurance_premium = ceded_premium × reinsurance_rate
```

**Typical rates:** 10-20% of the premium ceded to reinsurance

---

## Financial Sustainability

### Loss Ratio

The key metric for financial sustainability:

```
loss_ratio = total_payouts ÷ total_premium_income
```

**Sustainability Thresholds:**
- **< 50%**: Highly profitable (may be overpriced)
- **50-65%**: Optimal range (sustainable + competitive)
- **65-80%**: Acceptable (sustainable but tight margins)
- **> 80%**: Unsustainable (losing money)

### Current Performance

Based on calibrated triggers (2000-2023 data):

| Metric | Value | Status |
|--------|-------|--------|
| **Combined trigger rate** | 21.53% | ✓ Within target |
| **Average triggers/year** | 2.6 events | ✓ Acceptable |
| **Estimated annual payout/entity** | ~$1,300-$1,900 | ✓ Sustainable |
| **Estimated loss ratio** | 54-79% | ✓ Optimal range |

### Portfolio-Level Sustainability

**Assumptions:**
- 417 insured entities
- $1M total annual premiums
- Historical trigger rates maintained

**Expected Annual Performance:**

| Metric | Amount (USD) |
|--------|--------------|
| Total premium income | $1,000,000 |
| Expected total payouts | $542,000 - $792,000 |
| Expected loss ratio | 54% - 79% |
| Primary insurer net exposure | $542,000 - $792,000 |
| Reinsurance utilization | 0% (below $1M retention) |

**Conclusion:** The product is financially sustainable at current trigger rates and pricing.

---

## Example Scenarios

### Scenario 1: Normal Year (Low Trigger Activity)

**Triggers:**
- 1 drought event (severity 0.4, confidence 0.85)
- 1 flood event (severity 0.3, confidence 0.90)

**Calculations:**
```
Drought payout = $500 × (0.5 + 0.4) × 0.85 = $383
Flood payout = $750 × (0.5 + 0.3) × 0.90 = $540
Total annual payout = $923
```

**Entity-level loss ratio:** $923 ÷ $2,400 = 38.5% ✓

### Scenario 2: High-Risk Year (Multiple Triggers)

**Triggers:**
- 2 drought events (avg severity 0.6, avg confidence 0.80)
- 1 flood event (severity 0.7, confidence 0.85)
- 1 crop failure event (severity 0.5, confidence 0.75)

**Calculations:**
```
Drought 1 = $500 × 1.1 × 0.80 = $440
Drought 2 = $500 × 1.1 × 0.80 = $440
Flood = $750 × 1.2 × 0.85 = $765
Crop failure = $1,000 × 1.0 × 0.75 = $750
Total annual payout = $2,395
```

**Entity-level loss ratio:** $2,395 ÷ $2,400 = 99.8% ⚠️

**Note:** This is an outlier year. Across the portfolio, most entities won't experience this many triggers, keeping the overall loss ratio sustainable.

### Scenario 3: Portfolio-Wide Catastrophe

**Event:** Severe regional drought affecting 80% of insured entities

**Impact:**
- 334 entities (80% of 417) trigger drought payout
- Average payout: $500 × 1.3 × 0.85 = $553

**Calculations:**
```
Total payouts = 334 × $553 = $184,702
Portfolio loss ratio = $184,702 ÷ $1,000,000 = 18.5% ✓
Primary insurer pays = $184,702 (below $1M retention)
Reinsurance pays = $0
```

**Conclusion:** Even with 80% of entities triggering, the system remains sustainable due to calibrated trigger rates.

---

## Configuration

### Current Configuration Location

Payout rates are currently hardcoded in:
```
reporting/business_metrics.py
Lines 217-222
```

```python
PAYOUT_RATES = {
    'drought_trigger': 500,
    'flood_trigger': 750,
    'crop_failure_trigger': 1000,
    'severe_stress_trigger': 300
}
```

### Recommended: Move to Config File

**Future Enhancement:** Create `configs/financial_parameters.yaml`

```yaml
# Financial Parameters Configuration
premiums:
  per_entity_annual_usd: 2400

payout_rates:
  drought_trigger: 500
  flood_trigger: 750
  crop_failure_trigger: 1000
  severe_stress_trigger: 300

severity:
  min_multiplier: 0.5
  max_multiplier: 1.5

reinsurance:
  primary_retention_usd: 1000000
  attachment_point_usd: 1000000
  coverage_limit_usd: 10000000

sustainability:
  target_loss_ratio_max: 0.80
  optimal_range: [0.50, 0.65]
```

**Benefits:**
- Easy to update without code changes
- Version controlled
- Environment-specific configs (dev/prod)
- Centralized parameter management

---

## Clarifications on Common Confusions

### "$10M/year with reinsurance" - What does this mean?

This refers to the **reinsurance coverage capacity**, NOT expected annual payouts.

**Breakdown:**
- **$1M**: Primary insurer's maximum annual exposure (retention)
- **$10M**: Reinsurance layer capacity (covers losses from $1M to $11M)
- **$11M**: Total system capacity (primary + reinsurance)

**Expected annual payouts:** $542k-$792k (well below the $1M retention)

### "Total premiums $1M" - Is this sustainable?

Yes! Here's why:

```
Premium income:     $1,000,000/year
Expected payouts:   $542,000-$792,000/year
Expected profit:    $208,000-$458,000/year
Loss ratio:         54-79% ✓
```

The system is designed so expected payouts are 54-79% of premiums, leaving 21-46% for:
- Administrative costs
- Profit margin
- Reserve building
- Reinsurance premiums

### Per-Entity vs Portfolio Totals

Always clarify which level you're discussing:

| Metric | Per Entity | Portfolio (417 entities) |
|--------|------------|--------------------------|
| Annual premium | $2,400 | $1,000,000 |
| Expected payout | $1,300-$1,900 | $542,000-$792,000 |
| Loss ratio | 54-79% | 54-79% |

---

## Monitoring and Adjustments

### Monthly Monitoring

Track these metrics monthly:
- Trigger activation rates by type
- Average payout per trigger
- Month-to-date loss ratio
- Year-to-date loss ratio

### Annual Recalibration

Review annually:
- Actual vs expected trigger rates
- Actual vs expected payouts
- Loss ratio trends
- Climate pattern changes

### Adjustment Triggers

Consider recalibration if:
- Loss ratio exceeds 80% for 2 consecutive years
- Trigger rates drift >20% from targets
- New climate data suggests threshold changes
- Portfolio size changes significantly

---

## References

- **Calibration Report:** `docs/FINAL_CALIBRATION_REPORT.md`
- **Trigger Configuration:** `configs/trigger_thresholds.yaml`
- **Business Reports:** `outputs/business_reports/`
- **Payout Calculator:** `reporting/business_metrics.py`

---

## Appendix: Actuarial Formulas

### Expected Annual Payout (Per Entity)

```
E[Payout] = Σ (trigger_rate_i × base_payout_i × E[severity_i] × E[confidence_i])
```

Where:
- `i` = trigger type (drought, flood, crop failure)
- `trigger_rate_i` = probability of trigger i activating in a year
- `E[severity_i]` = expected severity multiplier for trigger i
- `E[confidence_i]` = expected confidence score for trigger i

### Portfolio Loss Ratio

```
Loss_Ratio = (Σ payouts_all_entities) ÷ (N × premium_per_entity)
```

Where:
- `N` = number of insured entities
- `premium_per_entity` = annual premium per entity

### Reinsurance Recovery

```
Recovery = max(0, min(total_payout - retention, coverage_limit - retention))
```

Where:
- `retention` = primary insurer's retention amount
- `coverage_limit` = maximum reinsurance coverage

---

**Document Version:** 1.0  
**Author:** Kiro AI  
**Review Date:** November 19, 2025
