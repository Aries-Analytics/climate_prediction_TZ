# Spatial Coverage Analysis - 6-Location System

**Report Date**: December 30, 2025  
**Analysis Type**: Leave-One-Location-Out Cross-Validation  
**Model**: XGBoost (Best Performer)

---

## Geographic Distribution

### Location Details

| # | Location | Coordinates | Elevation | Zone | Pop (M) |
|---|----------|-------------|-----------|------|---------|
| 1 | Morogoro | -6.82°N, 37.66°E | 526m | Tropical | 2.2 |
| 2 | Mbeya | -8.90°N, 33.45°E | 1,700m | Highland | 2.7 |
| 3 | Mwanza | -2.52°N, 32.90°E | 1,140m | Lake | 3.7 |
| 4 | Dodoma | -6.17°N, 35.74°E | 1,120m | Semi-arid | 2.1 |
| 5 | Dar es Salaam | -6.79°N, 39.27°E | 10m | Coastal | 6.7 |
| 6 | Arusha | -3.39°N, 36.68°E | 1,400m | Highland | 1.7 |

**Total Coverage**: 19.1 million people across diverse climate zones

---

## Spatial Generalization Performance

### Summary Statistics (XGBoost LOLO CV)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Mean R²** | 0.812 | ≥0.75 | ✅ **+8%** |
| **Std Dev** | 0.046 | <0.10 | ✅ Stable |
| **Min R²** | 0.737 | ≥0.70 | ✅ Pass |
| **Max R²** | 0.855 | - | Excellent |
| **Success Rate** | 83% | ≥75% | ✅ Pass |

---

## Performance Tiers

### Tier 1: Excellent (R² > 0.85)
- **Morogoro**: 85.5% ⭐ (NEW location)
- **Mbeya**: 85.5%

### Tier 2: Strong (R² 0.80-0.85)
- **Mwanza**: 84.6%
- **Dodoma**: 81.6%

### Tier 3: Good (R² 0.70-0.80)
- **Dar es Salaam**: 76.5%
- **Arusha**: 73.7%

**Result**: 67% locations in Tier 1-2 (Excellent-Strong)

---

## Climate Zone Analysis

### Performance by Zone

| Zone | Locations | Avg R² | Status |
|------|-----------|--------|--------|
| **Highland** | Mbeya, Arusha | 79.6% | Good |
| **Tropical** | Morogoro | 85.5% | Excellent |
| **Lake Region** | Mwanza | 84.6% | Excellent |
| **Semi-arid** | Dodoma | 81.6% | Strong |
| **Coastal** | Dar es Salaam | 76.5% | Good |

**Insight**: Model generalizes well across all climate types

---

## Comparison: 5 vs 6 Locations

| Metric | 5-Location | 6-Location | Improvement |
|--------|------------|------------|-------------|
| Mean R² | 0.745 | **0.812** | **+9.0%** ⭐ |
| Std Dev | 0.054 | **0.046** | +15% stability |
| Min R² | 0.673 | 0.737 | +9.5% |
| Max R² | 0.811 | 0.855 | +5.4% |
| Success Rate | 60% | **83%** | +23% |

**Conclusion**: 6-location expansion significantly improved performance

---

## Regional Insights

### Best Performing (Morogoro - NEW)
- R²=0.855, RMSE=0.356
- **Why**: Tropical transition zone, good data diversity
- **Action**: Use as reference for future expansions

### Challenging (Arusha)
- R²=0.737, RMSE=0.461
- **Why**: Highland microclimate complexity
- **Action**: Consider location-specific tuning

### Coastal (Dar es Salaam)
- R²=0.765, RMSE=0.442
- **Why**: Unique coastal dynamics
- **Action**: Add coastal-specific features

---

## Expansion Readiness

###✅ Proven Scalability
- Successfully expanded 5→6 locations
- New location (Morogoro) performs best
- No degradation in existing locations

### ✅ Quality Metrics
- Mean R² above 0.80 threshold
- Stability improved (+15%)
- Success rate exceeds 80%

### ✅ Next Steps
- Ready for 7th location addition
- Target: Northern/Western Tanzania
- Expected: Maintain >0.80 mean R²

---

## Business Recommendations

### Immediate
1. **Deploy to all 6 locations** - Performance validated
2. **Priority rollout**: Morogoro, Mbeya, Mwanza (Tier 1)
3. **Monitor closely**: Dar es Salaam, Arusha (Tier 3)

### Short-term (Q1 2026)
1. Add 2-3 more locations
2. Implement location-specific fine-tuning for Tier 3
3. Expand to neighboring countries (Kenya, Uganda)

### Long-term (2026)
1. Achieve 10+ location coverage
2. Develop regional ensemble models
3. Enable real-time multi-location forecasts

---

**Prepared By**: Geospatial Analytics Team  
**Reviewed**: December 30, 2025  
**Next Update**: Q1 2026
