# HewaSense Retrospective Validation - V2 Summary

**Date:** 2026-03-03  
**Status:** Complete and Operational  
**Framework:** ATLAS / GOTCHA Compliant  
**Production Model:** Phase-Based Dynamic (20% Basis Risk)

---

## 1. Executive Summary

This document summarizes the retrospective validation of two competing parametric insurance trigger models, tested against 10 years of historical climate and yield data (2015-2025) for Kilombero Basin, Tanzania.

> [!IMPORTANT]
> **The Phase-Based Dynamic Model (20% basis risk) is the chosen production model.** The April threshold proxy (10% basis risk) is retained below only as a baseline comparison. The phase-based model correctly identifies both major crop failures (2017/2018 and 2021/2022), which is the primary success criterion.

---

## 2. Model Comparison Summary

| Metric | April Threshold (Baseline) | Phase-Based Dynamic (Production) |
|---|---|---|
| **Basis Risk** | 10.0% | **20.0%** |
| **Overall Accuracy** | 90.0% | **80.0%** |
| **Caught 2021/2022 Catastrophe** | ✅ Yes | ✅ Yes |
| **Caught 2017/2018 Failure** | ❌ No (False Negative) | ✅ **Yes** |
| **False Positives** | 0 | 2 (2015/2016, 2019/2020) |
| **False Negatives** | 1 (2017/2018) | 0 |
| **Trigger Mechanism** | Single month (April < 140mm) | 4-phase daily tracker with dual indices |
| **Premium** | N/A (proxy only) | $20/farmer/year |

### Why 20% Basis Risk Is Better Than 10%

The April threshold's 10% basis risk is **misleading** because it completely missed the 2017/2018 crop failure (yield dropped to 2.24 MT/Ha). A parametric insurance product that misses real disasters is fundamentally broken, regardless of its statistical accuracy.

The phase-based model's 20% basis risk comes from two **false positives** (unnecessary payouts in 2015/2016 and 2019/2020). False positives are far less harmful than false negatives:
- **False Positive** → Farmer receives a small payout they didn't strictly need → builds trust
- **False Negative** → Farmer loses their crop and receives nothing → destroys trust

---

## 3. Baseline: April Threshold Proxy (FOR REFERENCE ONLY)

### Threshold Optimization Sweep (Section 6.2)
| Threshold (mm) | Basis Risk (%) | False Negatives | False Positives |
|---|---|---|---|
| 100 | 20.0% | 2 | 0 |
| 110 | 20.0% | 2 | 0 |
| 120 | 20.0% | 2 | 0 |
| 130 | 20.0% | 2 | 0 |
| 140 | 10.0% | 1 | 0 |
| 150 | 10.0% | 1 | 0 |

### Year-by-Year (140mm Threshold)
| Marketing Year | April Rain (mm) | National Yield (MT/Ha) | Trigger? | Outcome |
|---|---|---|---|---|
| 2015/2016 | 348.2 | 2.54 | NO | TRUE NEGATIVE |
| 2016/2017 | 386.3 | 3.20 | NO | TRUE NEGATIVE |
| 2017/2018 | 211.9 | 2.24 | NO | **FALSE NEGATIVE** ⚠️ |
| 2018/2019 | 218.9 | 3.31 | NO | TRUE NEGATIVE |
| 2019/2020 | 362.9 | 3.30 | NO | TRUE NEGATIVE |
| 2020/2021 | 181.3 | 2.76 | NO | TRUE NEGATIVE |
| 2021/2022 | 136.7 | 2.00 | YES | TRUE POSITIVE ✅ |
| 2022/2023 | 179.7 | 3.33 | NO | TRUE NEGATIVE |
| 2023/2024 | 261.1 | 3.37 | NO | TRUE NEGATIVE |
| 2024/2025 | 178.2 | 3.39 | NO | TRUE NEGATIVE |

**Fatal Flaw:** Missed 2017/2018 entirely because that crop failure was not driven by April water stress alone. This is exactly why the single-month proxy was rejected in favor of the phase-based approach.

---

## 4. Production Model: Phase-Based Dynamic

See **[PHASE_BASED_COMPARISON.md](./PHASE_BASED_COMPARISON.md)** for the comprehensive technical reference of the chosen production model, including phase configurations, trigger mechanisms, and year-by-year analysis.

---

## 5. Strategic Decision Record

**Decision:** Adopt Phase-Based Dynamic Model for Kilombero Pilot  
**Date:** January 2026  
**Rationale:**
1. Catches both confirmed crop failures (2017/2018 and 2021/2022)
2. False positives (unnecessary payouts) build farmer trust
3. $20 premium is affordable for smallholder farmers
4. Dynamic planting detection reduces basis risk from calendar misalignment
5. Phase-specific triggers align payouts with actual agronomic stress windows

---

**Maintained By:** Tanzania Climate Prediction Team  
**Last Updated:** March 3, 2026
