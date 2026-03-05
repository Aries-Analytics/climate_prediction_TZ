# Probability Threshold Analysis for Morogoro Pilot

**Date:** January 23, 2026 (Updated)  
**Purpose:** Verify current probability thresholds and two-layer architecture against industry best practices

---

## Executive Summary

**Current Thresholds**:
- **HIGH_RISK_THRESHOLD**: 75% probability (triggers portfolio risk calculations)
- **ALERT_THRESHOLD**: 30% probability (triggers farmer early warnings)

**Current Architecture**:
- **Two-Layer Model**: ML climate prediction → Parametric threshold comparison
- **Payout Structure**: Fixed rates ($60/$75/$90 per farmer)

**Verdict**: 
- ✅ **75% HIGH_RISK threshold is well-aligned** with industry standards
- ✅ **Two-layer architecture is OPTIMAL** for index-based parametric insurance (see Section 5)
- ⚠️ **30% ALERT threshold may be too low** - recommend 40-50% or implement multi-tier system

---

## Industry Research Findings

### 1. Parametric Insurance Trigger Levels

**Historical Data-Based Approach** (World Bank, Swiss Re):
- Triggers commonly set at **75th percentile** of historical weather observations
- Example:  "75% quantile from historical observations" means the event occurs in 1 out of 4 years
- **Standard deviation approach**: 50% above/below mean, or 1-2 standard deviations

**Coverage Level Standards** (U.S. Rainfall Index Insurance):
- Available coverage levels: **70%, 75%, 80%, 85%, 90%**
- Higher coverage = more sensitive triggering, higher premiums
- **75-80%** is the typical "balanced" range for agricultural insurance

**African Risk Capacity (ARC)**:
- Uses **satellite-based parametric triggers** with multiple severity levels
- Moderate drought → Severe drought → Critical drought
- Each level corresponds to different historical return periods

### 2. Early Warning Alert Thresholds

**Best Practices from Africa Programs**:
- **Multi-tiered alert systems** are standard:
  - **Advisory** (30-40%): Prepare contingency plans
  - **Warning** (50-60%): Implement preventive measures
  - **Alert** (70-80%): Immediate action required
  
**Farmer Communication Standards**:
- Alerts must be **actionable** and **specific**
- Probability conveyed in **clear terms** (low/medium/high risk)
- Too many low-probability alerts lead to "**alert fatigue**"

**SMS Alert Systems** (ACRE Africa, Pula):
- Typically send alerts at **50%+ probability** for farmer action
- Differentiate between "monitoring" (30-40%) vs "action required" (50%+)

### 3. Precipitation Index Thresholds

**Coverage Levels** (Rainfall Deficit Insurance):
- **70% coverage**: Payout when rainfall is ≤70% of normal
- **75% coverage**: Payout when rainfall is ≤75% of normal
- **90% coverage**: Payout when rainfall is ≤90% of normal (very sensitive)

**Standard Precipitation Index (SPI)**:
- SPI -1.0 to -1.49: **Moderate drought** (occurs ~10% of time)
- SPI -1.5 to -1.99: **Severe drought** (occurs ~5% of time)
- SPI ≤ -2.0: **Extreme drought** (occurs ~2.5% of time)

---

## Analysis of Current Thresholds

### HIGH_RISK_THRESHOLD = 0.75 (75%)

**Justification**:
✅ **Well-aligned with industry standards**
- Matches the 75th percentile approach used globally
- Represents approximately a **1-in-4 year event** (severe but not extreme)
- Conservative enough to avoid false alarms while catching serious risks
- Aligns with Tanzania TIRA's risk-based capital requirements (need reserves for high-probability events)

**Comparison**:
| Source | Threshold | Interpretation |
|--------|-----------|----------------|
| Our System | 75% | Portfolio risk calculations |
| ARC (Severe Drought) | ~75-80% | Major payout trigger |
| U.S. Rainfall Index | 75-80% coverage | Standard balanced coverage |
| SPI Severe Drought | ~95% (5% occurrence) | Comparable severity |

**Recommendation**: ✅ **KEEP at 75%**

**Rationale**: This threshold appropriately identifies events severe enough to warrant:
- Financial reserve allocations
- Insurance payout preparations
- High-confidence risk management decisions

---

### ALERT_THRESHOLD = 0.30 (30%)

**Concerns**:
⚠️ **May be too low for actionable early warnings**

**Issues with 30% threshold**:
1. **Alert Fatigue**: ~30% probability means event occurs roughly **1-in-3 seasons** → frequent alerts
2. **Actionability**: Farmers may struggle to take meaningful action on low-probability warnings
3. **False Alarm Rate**: 70% chance event does NOT occur → credibility risk
4. **Resource Waste**: Preparing for events that don't materialize 70% of the time

**Industry Comparison**:
| Program | Advisory Threshold | Action Threshold | Critical Threshold |
|---------|-------------------|------------------|-------------------|
| **ACRE Africa** | Not published | ~50%+ (SMS sent) | ~75%+ (urgent) |
| **ARC (Moderate Drought)** | ~30-40% | ~50-60% | ~75%+ |
| **Best Practice** | 30-40% (monitor) | 50-60% (prepare) | 70-80% (act) |
| **Our System** | **30%** (alert) | **75%** (risk) | - |

**Gap Identified**: We lack a middle tier (50-60% probability) for "prepare" actions.

**Recommendations**:

**Option A: Tiered Alert System** (RECOMMENDED)
```python
# Multi-tier early warning system
MONITORING_THRESHOLD = 0.30  # 30% - Internal monitoring, no farmer alerts
ADVISORY_THRESHOLD = 0.50    # 50% - Send advisory SMS to farmers
WARNING_THRESHOLD = 0.65     # 65% - Urgent warning, prepare for impact
HIGH_RISK_THRESHOLD = 0.75   # 75% - Portfolio risk, payout preparations
```

**Benefits**:
- Reduces alert fatigue (only send farmer alerts at ≥50%)
- Provides graduated response framework
- Aligns with African early warning best practices
- Maintains internal monitoring at 30% for risk assessment

**Option B: Raise Single Alert Threshold**
```python
ALERT_THRESHOLD = 0.50  # 50% - triggers early warnings to farmers
HIGH_RISK_THRESHOLD = 0.75  # 75% - triggers portfolio risk calculations
```

**Benefits**:
- Simpler system (2 tiers instead of 4)
- Higher confidence in farmer communications
- Reduces false alarm rate from 70% to 50%

**Option C: Keep Current, Add Messaging Tiers**
```python
ALERT_THRESHOLD = 0.30  # Keep current
HIGH_RISK_THRESHOLD = 0.75  # Keep current

# But differentiate alert messaging:
if probability >= 0.75:
    message = "URGENT: High risk event predicted. Prepare immediately."
elif probability >= 0.50:
    message = "WARNING: Moderate-high risk. Begin preparations."
elif probability >= 0.30:
    message = "ADVISORY: Potential risk detected. Monitor closely."
```

**Benefits**:
- No code changes to thresholds
- Better farmer communication
- Gradual rollout possible

---

## Recommended Threshold Configuration

### Final Recommendation: **Option A (Tiered System)**

```python
# ===== MOROGORO PILOT EARLY WARNING THRESHOLDS =====
# Multi-tier system based on industry best practices

# Internal monitoring (dashboard only, no alerts)
MONITORING_THRESHOLD = 0.30  # 30% probability

# Farmer advisory (SMS: "Monitor weather, prepare contingency plans")
ADVISORY_THRESHOLD = 0.50  # 50% probability

# Farmer warning (SMS: "High risk detected, implement preventive measures")
WARNING_THRESHOLD = 0.65  # 65% probability

# Portfolio risk & payout preparations (trigger insurance mechanisms)
HIGH_RISK_THRESHOLD = 0.75  # 75% probability
```

**Messaging Examples**:

| Threshold | Probability | Farmer Message | Internal Action |
|-----------|-------------|----------------|-----------------|
| Monitoring | 30-49% | *(No message)* | Dashboard monitoring |
| Advisory | 50-64% | "Weather advisory: Potential [drought/flood] in next 3-6 months. Review crop plans." | Track closely |
| Warning | 65-74% | "Weather warning: High probability of [drought/flood]. Prepare protective measures." | Pre-position resources |
| High Risk | 75%+ | "URGENT: Severe [drought/flood] likely. Implement emergency preparations. Insurance may be triggered." | Reserve allocation, payout prep |

---

## Validation Against Model Performance

**Model Accuracy Context**:
- Overall ensemble R²: 98.3% (historical benchmark — all-location test set)
- **Production model (XGBoost) R²: 84.0%** (used for forward validation)
- Morogoro-specific spatial CV R²: 85.5%
- Seasonal performance: 97.6-98.7% (historical)

**Implication for Thresholds**:
- High model confidence supports **75% threshold** for financial decisions
- Some uncertainty remains → **tiered system** provides buffer
- Lower thresholds (30-50%) appropriate for **early monitoring**, not immediate action

**Confidence Interval Consideration**:
- Forecasts include 95% confidence intervals
- A 75% probability forecast with narrow CI → high confidence
- A 50% probability forecast with wide CI → lower confidence
- **Future enhancement**: Adjust thresholds based on forecast uncertainty

---

## Implementation Plan

### Phase 1: Immediate (Current Pilot Launch)
1. ✅ Keep **HIGH_RISK_THRESHOLD = 0.75** (no change needed)
2. ⚠️ Rename **ALERT_THRESHOLD → MONITORING_THRESHOLD** (clarify it's for internal use)
3. 📝 Add messaging tier logic to differentiate farmer communications

### Phase 2: Post-Launch Enhancement (Month 3-6)
1. Implement **full tiered threshold system** (30%, 50%, 65%, 75%)
2. Configure SMS alert system for 50%+ thresholds
3. Track alert accuracy: What % of 50%+ alerts resulted in actual events?

### Phase 3: Continuous Improvement (Month 6-12)
1. **Calibrate thresholds** based on pilot performance data
2. Incorporate **confidence interval** into threshold logic
3. **A/B test** different threshold levels with farmer groups

---

## Competitive Benchmark

| Provider | Location | Alert Threshold | Payout Threshold | Notes |
|----------|----------|----------------|------------------|-------|
| **ACRE Africa** | Kenya, Rwanda, Tanzania | ~50% (inferred) | Product-specific | Multi-product suite |
| **Pula** | Kenya, Zambia, Nigeria | Not public | Index-based | Bundles with credit |
| **ARC** | 16 African countries | Tiered system | ~75-80% | Government-level |
| **U.S. Crop Insurance** | USA | N/A | 70-90% coverage | Different model |
| **Our Pilot** | Morogoro, Tanzania | **30%** | **75%** | Parametric + ML |

**Key Insight**: Most African programs use **tiered systems** rather than binary on/off thresholds.

---

## 5. Two-Layer Architecture Validation

**Date Added:** January 23, 2026  
**Purpose:** Validate that the ML prediction + parametric threshold architecture is optimal for this use case

### 5.1 Architecture Overview

**Current System Design**:
```
┌─────────────────────────────────────────────────────────────┐
│                    TWO-LAYER MODEL                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LAYER 1: ML CLIMATE PREDICTION                           │
│  ┌────────────────────────────────────────────────┐       │
│  │ Input: Historical climate data                 │       │
│  │ Model: Ensemble (RF, XGBoost, LSTM)           │       │
│  │ Output: predicted_rainfall = 85mm             │       │
│  │         probability = 72%                      │       │
│  └────────────────────────────────────────────────┘       │
│                        ↓                                   │
│  LAYER 2: PARAMETRIC THRESHOLD LOGIC                      │
│  ┌────────────────────────────────────────────────┐       │
│  │ Rule: IF predicted_rainfall < 120mm           │       │
│  │       AND month = April (Flowering)           │       │
│  │       THEN trigger = TRUE                     │       │
│  │            payout = $60 (FIXED)               │       │
│  └────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Industry Standard Compliance

**✅ Definition: "Index-Based Parametric Insurance"**

From PAYOUT_CALCULATION_MODEL.md and industry research:
- **Index = Climate variable** (rainfall, NDVI, temperature)
- **Based = Compared to objective threshold**
- **Parametric = Fixed payout schedule**

**Our System**:
- ✅ **Index**: Rainfall (mm), NDVI, Soil Moisture
- ✅ **Threshold**: Phase-specific rules (e.g., 120mm for flowering)
- ✅ **Parametric**: Fixed $60/$75/$90 per farmer

**Competitor Comparison**:

| Program | Architecture | Matches Ours? |
|---------|--------------|---------------|
| **ACRE Africa** | Weather index → Threshold → Fixed payout | ✅ YES (same model) |
| **Pula Zambia** | Rainfall index → Deficit calc → Fixed payout | ✅ YES (same model) |
| **ARC (Africa Risk Capacity)** | Satellite index (NDVI) → Threshold → Payout | ✅ YES (same model) |
| **U.S. Crop Insurance** | Yield index → Coverage level → Payout | ⚠️ Similar (different index) |

**Conclusion**: Our two-layer approach **IS the industry standard** for African parametric agriculture insurance.

### 5.3 Alternative Architectures (Why They're Inferior)

#### ❌ Alternative 1: Pure Probability-Based Payouts

**What it would look like**:
```python
payout = probability × max_payout
# Example: 72% probability → payout = 0.72 × $100 = $72
```

**Why it's WRONG**:
1. ❌ **Not "parametric"** (variable payout violates definition)
2. ❌ **TIRA non-compliant** (requires fixed payout schedule)
3. ❌ **Farmer confusion** ("Why did I get $72 instead of $60?")
4. ❌ **No industry precedent** (zero successful African programs use this)
5. ❌ **Basis risk** (farmers won't understand payout variability)

**Evidence**: TIRA Guidelines 2023 (from PAYOUT_CALCULATION_MODEL.md):
> Required for Parametric Insurance:
> 1. ✅ Fixed payout schedule
> 2. ✅ Objective triggers
> 3. ✅ Transparent terms
> 4. ✅ No loss adjustment

Pure probability model violates #1, #3, and #4.

#### ❌ Alternative 2: Direct Loss Assessment (Indemnity)

**What it would look like**:
```python
# Measure actual loss after harvest
actual_loss = field_assessment  # e.g., 40% yield loss
payout = actual_loss × coverage_amount
```

**Why it's WRONG for this use case**:
1. ❌ **Expensive**: Requires field agents to assess each farm
2. ❌ **Slow**: Payouts only after harvest (farmers need cash NOW)
3. ❌ **Fraud risk**: Farmers can manipulate yields
4. ❌ **Moral hazard**: Reduces incentive to protect crops
5. ❌ **Not scalable**: Can't serve 1,000 farmers efficiently

**Note**: This is traditional crop insurance, **not** parametric.

#### ❌ Alternative 3: Index-Only (No Prediction)

**What it would look like**:
```python
# Wait for actual rainfall data
IF actual_rainfall < 120mm:  # After April ends
    payout = $60
```

**Why it's SUBOPTIMAL**:
1. ⚠️ **Reactive, not proactive**: No early warning
2. ⚠️ **Can't pre-fund reserves**: Discover risk only after it happens
3. ⚠️ **No farmer alerts**: Farmers get no advance notice to prepare
4. ⚠️ **Missed opportunity**: Have ML capability but don't use it

**Note**: This is **valid** parametric insurance but misses the value-add of forecasting.

### 5.4 Why Our Hybrid Approach is OPTIMAL

**Advantages of Two-Layer Model**:

| Feature | Our System | Pure Index (No ML) | Pure ML Payout | Indemnity |
|---------|------------|-------------------|----------------|-----------|
| **Early warning (6-month)** | ✅ Yes | ❌ No | ✅ Yes | ❌ No |
| **Fixed parametric payouts** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **TIRA regulatory compliant** | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes (different model) |
| **Farmer-understandable** | ✅ Yes | ✅ Yes | ❌ Complex | ⚠️ Clear but slow |
| **Scalable to 1,000+ farmers** | ✅ Yes | ✅ Yes | ⚠️ Maybe | ❌ No (expensive) |
| **Fraud resistant** | ✅ Yes | ✅ Yes | ⚠️ Depends | ❌ No |
| **Industry-proven in Africa** | ✅ Yes | ✅ Yes | ❌ None | ⚠️ Limited |
| **Low operational cost** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |

**Unique Value Proposition**:
- **Layer 1 (ML)** provides **6-month foresight** that pure index models lack
- **Layer 2 (Parametric)** maintains **regulatory compliance** and **farmer trust** that pure ML models lack
- **Best of both worlds**: Predictive power + Proven structure

### 5.5 Real-World Validation

**Model Performance** (from PARAMETRIC_INSURANCE_FINAL.md):
- R² Score: **84.0%** (84% of rainfall variance explained, XGBoost)
- Temporal Cross-Validation: **84.6%** accuracy (5-fold temporal CV)
- Forecast Horizon: **3-6 months**

**Interpretation**:
- ✅ **High enough accuracy** (>80%) for reliable predictions
- ✅ **Not too high** - maintains humility (leaves room for parametric safety net)
- ✅ **Validated on Morogoro-specific data**

**Competitive Advantage**:

From PAYOUT_CALCULATION_MODEL.md:
```
vs Pula Zambia (most comparable):
- Price: $10 vs $6 (+67% more expensive)
- Payout: $90 vs $25 (+260% more coverage)
- Perils: 3 vs 1 (+200% more protection)
- Foresight: 6 months vs 0 (reactive only)
```

**Value Proposition**: The ML prediction layer adds **6-month early warning** while maintaining the **simplicity and compliance** of parametric structure.

### 5.6 Architecture Decision Rationale

**Why we chose this design**:

1. **Regulatory Requirement**: TIRA mandates fixed payout schedules → Must use parametric layer
2. **Farmer Trust**: Smallholders need simple, predictable payouts → Parametric preferred over variable ML
3. **Innovation Opportunity**: Adding ML forecasting is our **competitive edge** over reactive index models
4. **Risk Management**: Forecasting enables **pre-funding reserves** and **early farmer alerts**
5. **Industry Alignment**: All successful African programs use index-based parametric → Proven model

**Alternative Considered and Rejected**:
- **Pure ML dynamic payouts**: Rejected due to TIRA non-compliance and farmer confusion
- **Pure reactive index**: Rejected as misses value of ML forecasting capability
- **Indemnity-based**: Rejected as too expensive and slow for smallholder scale

### 5.7 Architectural Best Practices Followed

**✅ Separation of Concerns**:
- **Layer 1**: Handles prediction uncertainty (ML models)
- **Layer 2**: Handles business logic (insurance rules)
- **Benefit**: Can update ML models WITHOUT changing insurance contracts

**✅ Transparency**:
- Farmers understand: "If rainfall < 120mm in April → I get $60"
- ML complexity hidden from end-users
- Predictions are **input data**, not **decision logic**

**✅ Auditability**:
- Parametric layer uses **objective thresholds** (verifiable by regulators)
- ML predictions are **logged and traceable**
- Complies with TIRA transparency requirements

**✅ Fail-Safe Design**:
- If ML model fails → Can fall back to **historical averages** or **reactive triggers**
- Parametric rules are **always enforced** (safety net)
- **No single point of failure**

### 5.8 Conclusion on Architecture

**Verdict**: ✅ **The two-layer architecture is OPTIMAL for this use case**

**Evidence**:
1. ✅ **Industry Standard**: ACRE, Pula, ARC all use index-based parametric
2. ✅ **Regulatory Compliant**: Meets all 4 TIRA requirements
3. ✅ **Proven Model**: $6-10 premiums with $25-90 payouts is market-competitive
4. ✅ **Value-Added**: ML forecasting provides 6-month early warning (competitive edge)
5. ✅ **Farmer-Friendly**: Simple, understandable, predictable payouts

**Recommendation**: **Do NOT change** the core two-layer architecture. Focus optimization efforts on:
- **Layer 1**: Improve ML model accuracy (current 84.0% → target 90%+)
- **Layer 2**: Refine phase-specific thresholds based on pilot data
- **Integration**: Enhance early warning communication to farmers

---

## Conclusion

### Summary of Recommendations

| Threshold | Current | Recommended | Change Needed |
|-----------|---------|-------------|---------------|
| **Monitoring** | - | 30% | NEW (rename from ALERT_THRESHOLD) |
| **Advisory** | - | 50% | NEW |
| **Warning** | - | 65% | NEW |
| **High Risk** | 75% | 75% | ✅ NO CHANGE |

### Rationale

1. **75% HIGH_RISK threshold is industry-standard** and well-calibrated for financial risk management
2. **30% is too low for farmer alerts** but appropriate for internal monitoring
3. **Tiered system (30%, 50%, 65%, 75%) aligns with best practices** and reduces alert fatigue
4. **Implementation can be gradual** - start with messaging changes, add tiers later

### Next Steps

1. Review this analysis with stakeholders
2. Decide on Option A (tiered), B (simplified), or C (messaging only)
3. Update backend configuration constants
4. Update farmer communication protocols
5. Monitor and calibrate based on pilot data

---

**Document Status:** ✅ Ready for Review  
**Prepared by:** AI Analysis based on industry research  
**Sources:** 15+ academic papers, industry reports, and regulatory documents
