# Kilombero Basin Rice Pilot Specification
## Morogoro Region, Tanzania

**Document Version:** 1.2  
**Created:** January 12, 2026  
**Updated:** March 5, 2026 (Phase-Based model confirmed as production, data leakage fix applied, XGBoost R²=0.8666)  
**Location:** Kilombero Basin, Morogoro Region, Tanzania  
**Purpose:** Single-location pilot to validate ensemble climate prediction model with dual-index triggers before engaging an underwriter for a real pilot deployment

---

## Executive Summary

The **Kilombero Basin Rice Pilot** (Morogoro Region) is a focused, single-location parametric insurance pilot program designed to validate the production-ready ensemble climate prediction model in a real-world agricultural setting. The pilot covers **1,000 smallholder rice farmers** in the flood-prone Kilombero Valley. 

**Model Selection**: The HewaSense V4 Phase-Based Coverage Service actively models rice phenology via Growing Degree Days (GDD) and mitigates basis risk via continuous 5-day cumulative flood triggers. The model achieved a bounded **9.6% commercial loss ratio** in out-of-sample testing (2000-2014) and a validated **20% basis risk** in retrospective validation (2015-2025), with **zero false negatives** — catching both the 2017/2018 and 2021/2022 crop failures. See `PHASE_BASED_COMPARISON.md` for full validation details.

**Location Selection**: Morogoro was selected based on superior location-specific model performance (spatial cross-validation R² = 0.855) and an aggressive local ground-truth correlation validation (satellite proxy R = 0.888) scaling benchmark.

---

## Pilot Specifications

### Geographic Scope

| Parameter | Value |
|-----------|-------|
| **Primary Location** | Morogoro, Tanzania |
| **Location ID** | `6` (in database) |
| **Coordinates** | -6.8211°S, 37.6595°E |
| **Elevation** | 526 meters |
| **Climate Zone** | Tropical transition |
| **Region** | Eastern Tanzania |
| **Sub-Region** | Kilombero Basin |
| **Primary Crop** | Rice (paddy) |

### Farmer Coverage

| Metric | Value |
|--------|-------|
| **Total Farmers** | 1,000 smallholder rice farmers |
| **Coverage Type** | Full-season parametric insurance |
| **Farm Size** | ~0.5-2 hectares per farmer (average: 1 hectare) |
| **Total Insured Area** | ~1,000 hectares |
| **Farmer Profile** | Smallholder rice farmers in Kilombero Basin |

### Financial Parameters

| Parameter | Current Value | Required Value | Status |
|-----------|---------------|----------------|--------|
| **Current Cash Reserves** | $150,000 | $133,557 (100% CAR min) | ✅ **ADEQUATELY FUNDED** |
| **Payout Rate - Drought** | $60 per farmer | - | ✅ Market standard |
| **Payout Rate - Flood** | $75 per farmer | - | ✅ Market standard |
| **Payout Rate - Crop Failure** | $90 per farmer | - | ✅ Market standard |
| **Maximum Single-Event Payout** | $90,000 (all farmers, crop failure at 100%) | - | Covered by reserves |
| **Expected 6-Month Payout** | $133,557 | - | Based on multi-location data (pre-filter) |
| **Capital Adequacy Ratio (CAR)** | 112.3% | ≥100% (TIRA requirement) | ✅ **COMPLIANT** |
| **Reserve Buffer** | +12.3% | Positive | ✅ Meets regulatory standards |
| **Pilot Duration** | 12 months (one full growing season) | - | - |

> [!NOTE]
> **Reserve Adequacy Achieved**
> 
> **Updated Status**: The pilot now has **$150,000** in reserves, providing:
> - **112.3% Capital Adequacy Ratio (CAR)** - exceeds Tanzania TIRA 100% minimum requirement
> - **Coverage for worst-case scenario**: $90,000 maximum single-event payout (100% crop failure)
> - **Buffer for multi-event seasons**: Can handle expected $133k+ payout scenarios
> - **Operational margin**: 12.3% buffer for administrative costs and unexpected events
>
> **Regulatory Compliance**:
> - ✅ Meets Tanzania TIRA 100% CAR requirement
> - ✅ Aligns with regional standards (Uganda requires 200% CAR, we're at 112%)
> - ✅ Follows international best practices (NAIC prudent reserve guidelines)
>
> **Risk Management**:
> - Reserves can cover 1.67x the expected 6-month payout
> - Provides cushion for forecast uncertainty
> - Allows for basis risk adjustments
>
> **Funding Source**: To be secured through government grant, development partner support, or private investment before pilot launch.

---

### Reserve Calculation Methodology

**Expected Payout Calculation** (Current 6-month forecast):
```
High-risk forecasts (≥75% probability):
- Location 2 (Dar es Salaam): Flood at 80% → $75 × 1,000 farmers × 0.80 = $60,000
- Location 3 (Dodoma): Crop failure at 81.7% → $90 × 1,000 farmers × 0.817 = $73,557
Total Expected Payout: $133,557
```

**Note**: Once pilot is properly configured to Morogoro only (Location ID 6), this calculation will reflect only Morogoro-specific forecasts. Current forecast data shows multi-location risks, which inflates the payout estimate. However, even with single-location focus, adequate reserves remain critical.


## Model Performance Rationale

### Why Morogoro?

Morogoro was selected as the pilot location based on **objective model performance metrics** from the 6-location spatial evaluation:

#### Spatial Cross-Validation Performance (6 Locations)

| Location | R² Score | Spatial CV | Climate Zone | Assessment |
|----------|----------|------------|--------------|------------|
| Arusha | 0.712 | 0.234 | Highland subtropical | Good |
| Dar es Salaam | 0.689 | 0.198 | Coastal tropical | Moderate |
| Dodoma | 0.745 | 0.287 | Semi-arid | Good |
| Mbeya | 0.855 | 0.356 | Highland temperate | **Excellent** |
| Mwanza | 0.678 | 0.176 | Lake Victoria | Moderate |
| **Morogoro** ⭐ | **0.855** | **0.356** | Tropical transition | **Excellent (Best)** |

**Source:** `docs/current/6_LOCATION_EXPANSION_SUMMARY.md`, `docs/references/ML_MODEL_REFERENCE.md`

#### Key Performance Indicators

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Morogoro R² Score** | 0.855 (85.5%) | Tied for best among 6 locations (location-specific) |
| **Spatial CV** | 0.356 | Highest spatial generalization score |
| **Overall Ensemble Model** | — | Historical benchmark only — superseded by data leakage fix |
| **Production Model (XGBoost)** | 0.8666 (86.7%) | **Forward validation model** — primary serving model (post data leakage fix, 11 rainfall-derived features removed) |
| **RMSE** | 0.4008 (normalized) | ~35 mm/month in real units |
| **Seasonal Performance** | 97.6-98.7% | Historical single-location benchmarks (pre-leakage-fix; not applicable to production) |

> [!NOTE]
> **Performance Metrics Explained**: 
> - **85.5% (Morogoro-specific)**: How well the model performs when trained on 5 locations and tested on Morogoro (spatial cross-validation). This is the key metric for location selection.
> - **86.7% (XGBoost R²=0.8666)**: The model actually used for forward validation and pilot predictions. After the March 2026 data leakage fix (11 rainfall-derived features removed), this is the most accurate and honest metric.
> - **Ensemble (R²=0.8402)**: Secondary model available as fallback.

**Conclusion:** Morogoro demonstrates the **best spatial cross-validation performance**, indicating the model generalizes exceptionally well to this location, making it ideal for pilot validation.

---

## Trigger Specifications

### Climate-Based Triggers

Based on calibrated thresholds for Morogoro's tropical transition climate:

| Trigger Type | Metric | Threshold | Growing Stage | Payout |
|--------------|--------|-----------|---------------|--------|
| **Rainfall Deficit (Drought)** | Cumulative rainfall | Dynamic GDD Stage Checks | Vegetative/Reproductive | $60/farmer |
| **Excessive Rainfall (Flood)** | Cumulative rainfall | > 140mm acute or > 120-160mm (5-day) | Any stage | $75/farmer |
| **Crop Failure** | NDVI anomaly | < -0.15 deviation | Maturity | $90/farmer |

> [!NOTE]
> **Dual-Index Triggers (Planned - Q2 2026)**  
> Current triggers use rainfall and NDVI thresholds. The system infrastructure now supports **soil moisture index**, enabling dual-index triggers for improved accuracy:
> - **Drought**: *(rainfall < 150mm AND soil_moisture < 0.25) OR soil_moisture < 0.15*
> - **Flood**: *rainfall > 400mm AND soil_moisture > 0.90* (saturated soil amplifies flood risk)
> 
> This approach reduces basis risk in the flood-prone Kilombero Valley by accounting for soil saturation levels.

**Alert Threshold:** Forecast probability ≥ 75% triggers portfolio risk calculations and farmer alerts.

---

## System Architecture

### Multi-Location System Capability

The underlying system is designed for **6 locations**:
1. Arusha (ID: 1)
2. Dar es Salaam (ID: 2)
3. Dodoma (ID: 3)
4. Mbeya (ID: 4)
5. Mwanza (ID: 5)
6. **Morogoro (ID: 6)** ← **Pilot Focus**

**Critical Note:** The system will continue to:
- Collect climate data for all 6 locations
- Generate forecasts for all 6 locations
- Store historical data for all 6 locations

**However, the pilot program**:
- Calculates portfolio risk **only for Morogoro (Location ID 6)**
- Issues farmer alerts **only for Morogoro**
- Tracks financial exposure **only for Morogoro**
- Displays dashboard metrics **only for Morogoro**

This design allows for **future expansion** to other locations without system changes—only configuration updates.

---

## Data Sources (Kilombero Basin - Morogoro)

The ensemble model uses 5 integrated data sources for Kilombero Basin:

| Source | Variables | Resolution | Coverage |
|--------|-----------|------------|----------|
| **CHIRPS** | Rainfall | 0.05° (~5km) | 2000-Present |
| **NASA POWER** | Temperature, Solar, Humidity, **Soil Moisture (GWETPROF)** ⭐ | 0.5° (~50km) | 2000-Present |
| **ERA5** | Pressure, Wind, **Soil Moisture (SWVL1)** ⭐ | 0.25° (~25km) | 2000-Present |
| **MODIS NDVI** | Vegetation Index | 250m | 2000-Present |
| **Ocean Indices** | ENSO, IOD, NAO | Global | 2000-Present |

> [!NOTE]
> **Soil Moisture Index Added (Feb 2026)** ⭐
> 
> Infrastructure is ready to incorporate soil moisture data for **dual-index triggers** (rainfall + soil moisture):
> - **Current**: Triggers use rainfall and NDVI only
> - **Planned (Q2 2026)**: Activate dual-index triggers for improved flood/drought detection
> - **Benefit**: Reduced basis risk in flood-prone Kilombero Valley
> - **Details**: See [`SOIL_MOISTURE_FUTURE_ENHANCEMENT.md`](../SOIL_MOISTURE_FUTURE_ENHANCEMENT.md)

**Total Features:** 83 selected features (from 245 candidates, after removing 11 leaky rainfall-derived features via `utils/data_leakage_prevention.py`)  
**Data Quality:** 99.8% completeness for Morogoro location  

> [!WARNING]
> **Data Resolution Trade-Off**
> 
> CHIRPS rainfall (~5km grid) and NASA POWER temperature/soil moisture (~50km grid) operate at different resolutions. The validated satellite-to-local correlation (r=0.888) indicates strong agreement, but micro-climate variations within the Kilombero floodplain may not be fully captured.
> 
> **Planned Mitigation:** Deploy 2-3 ground-truthing rain gauges during forward validation to calibrate satellite data against actual local conditions.

---

## Forecast Horizons

The system generates forecasts at **4 time horizons**:

| Horizon | Timeframe | Use Case |
|---------|-----------|----------|
| 3 months | 90 days ahead | Seasonal planning |
| 4 months | 120 days ahead | Planting decisions |
| 5 months | 150 days ahead | Input procurement |
| 6 months | 180 days ahead | Financial planning |

**Forecast Generation:** Updated monthly or on-demand via API

---

## Pilot Objectives

### Primary Objectives

1. **Model Validation**: Verify 86.7% XGBoost R² accuracy translates to real-world forecast reliability (forward validation)
2. **Operational Testing**: Validate end-to-end system (data → forecast → alert → payout)
3. **Farmer Adoption**: Test farmer understanding and trust in parametric insurance
4. **Financial Viability**: Validate payout rates and reserve requirements

### Success Metrics

| Metric | Target | Measurement Period |
|--------|--------|-------------------|
| **Forecast Accuracy** | ≥ 85% R² on actual vs predicted | 12 months |
| **Alert Timeliness** | ≥ 30 days advance warning | Per event |
| **Payout Accuracy** | ≥ 90% true positives (correct triggers) | Per season |
| **Farmer Satisfaction** | ≥ 75% positive feedback | End of pilot |
| **Claims Processing** | ≤ 14 days from trigger to payout | Per claim |

---

---

## Configuration Implementation

### Environment Variables (.env)

**Pilot-specific configuration:**

```bash
# PILOT LOCATION CONFIGURATION (Kilombero Basin, Morogoro)
PILOT_MODE=true
PILOT_LOCATION=Morogoro
PILOT_BASIN=Kilombero
PILOT_COORDINATES=-6.8211,37.6595
PILOT_LOCATION_ID=6

# Forecast configuration
FORECAST_HORIZON_DAYS=31
PILOT_CROP=Rice
PILOT_FARMERS=1000

# Reserves and financial
CURRENT_RESERVES=150000  # USD
```

### Slack Alert Configuration

**Daily Summary Format:**
```
✅ Pipeline Success
Location: Morogoro (Kilombero Basin)
Forecasts: 31 for rice farmers
Quality: 95%
Farmers: 1,000 covered
🌾 Pilot: 1,000 rice farmers in Kilombero Basin
```

**Forecast Generation Alert:**
```
📈 Total: 31 forecasts
📍 Location: Morogoro (Kilombero Basin - Pilot)
🌾 Crop: Rice
👥 Farmers: 1,000
```

**Failure Alert:**
```
⚠️ Pipeline Failure
Impact: No new forecasts for Morogoro pilot (1,000 farmers affected)
```

**Recommended Slack Channels:**
- `#kilombero-pilot-daily` - Daily summaries (1 message/day)
- `#kilombero-pilot-alerts` - Issues & warnings (0-3/day)
- `#kilombero-pilot-status` - Execution status (2/day: start, complete)

### Backend Configuration Constants

**File:** `backend/app/api/forecasts.py`

```python
# ===== MOROGORO RICE PILOT CONFIGURATION =====
# Single-location pilot (Location ID 6 = Morogoro)
# System maintains 6-location capability for future expansion

PILOT_LOCATION_ID = 6  # Morogoro, Tanzania
PILOT_LOCATION_NAME = "Morogoro"
TOTAL_FARMERS = 1000  # Total farmers in Morogoro pilot
FARMERS_PER_LOCATION = 1000  # All farmers at single pilot location
CURRENT_RESERVES = 150000  # USD - Updated to meet 100% CAR regulatory requirement

# Payout rates (USD per farmer)
PAYOUT_RATES = {
    "drought": 60,
    "flood": 75,
    "crop_failure": 90
}

# ===== 4-TIER EARLY WARNING THRESHOLD SYSTEM =====
# Based on industry best practices (ARC, ACRE Africa, parametric insurance standards)
# See: docs/references/THRESHOLD_ANALYSIS_INDUSTRY_RESEARCH.md

MONITORING_THRESHOLD = 0.30   # 30% - Internal monitoring only, no farmer alerts
ADVISORY_THRESHOLD = 0.50     # 50% - Send advisory to farmers ("prepare contingency plans")
WARNING_THRESHOLD = 0.65      # 65% - Send warning to farmers ("implement preventive measures")
HIGH_RISK_THRESHOLD = 0.75    # 75% - Portfolio risk calculations, payout preparations

# Legacy support (deprecated - use specific thresholds above)
ALERT_THRESHOLD = ADVISORY_THRESHOLD  # Backwards compatibility
```

> [!NOTE]
> **4-Tier Threshold System Implemented**
> 
> The pilot now uses a graduated early warning system aligned with African agricultural insurance best practices:
> 
> | Threshold | Probability | Target Audience | Action Required |
> |-----------|-------------|-----------------|-----------------|
> | **Monitoring** | 30-49% | Internal risk management only | Dashboard tracking, no farmer communication |
> | **Advisory** | 50-64% | Farmers (SMS alert) | "Prepare contingency plans, monitor weather closely" |
> | **Warning** | 65-74% | Farmers (urgent SMS) | "Implement preventive measures, high risk detected" |
> | **High Risk** | 75%+ | Portfolio + Farmers (emergency SMS) | "Emergency preparations, insurance payout likely" |
> 
> **Benefits**:
> - Reduces "alert fatigue" (farmers only notified at ≥50% probability)
> - Graduated response framework improves actionability
> - Aligns with ARC, ACRE Africa, and regional best practices
> - Maintains internal monitoring at lower thresholds for risk assessment
>
> **Source**: Industry research documented in `THRESHOLD_ANALYSIS_INDUSTRY_RESEARCH.md`

### Database Filtering

All pilot-specific endpoints filter by `location_id = 6`:

```python
# Portfolio risk: Morogoro only
high_risk_forecasts = db.query(Forecast).filter(
    Forecast.location_id == PILOT_LOCATION_ID,  # Morogoro only
    Forecast.probability >= HIGH_RISK_THRESHOLD,
    Forecast.target_date >= today,
    Forecast.target_date <= target_end
).all()
```

**Note:** Forecasts for all 6 locations continue to be generated and stored, but pilot calculations use only Morogoro data.

---

## Dashboard Display

### Portfolio Risk Overview

**Display Format:**
- **Farmers at Risk:** "X of 1,000 farmers (Y%)" 
- **Location Context:** "Morogoro Pilot (Location ID: 6)"
- **Geographic Map:** Highlights Morogoro with pilot indicator

### Labels and Messaging

- "Kilombero Basin Rice Pilot (1,000 Farmers)"
- "Single-Location Pilot - Morogoro Region, Tanzania"
- "Flood-Prone Valley - Dual-Index Triggers Planned (Q2 2026)"
- "6-Month Forecast Horizon"

---

## Expansion Roadmap

### Phase 1: Kilombero Basin Pilot (Current)
**Location:** Kilombero Basin, Morogoro  
**Duration:** 12 months  
**Scope:** 1 location, 1,000 farmers  
**Objective:** Validate model, dual-index triggers, and operations in flood-prone rice valley

### Phase 2: Regional Expansion (Future)
**Locations:** Add Mbeya (also has R² = 0.855)  
**Scope:** 2 locations, 2,000 farmers  
**Objective:** Test multi-location operations

### Phase 3: National Rollout (Future)
**Locations:** All 6 locations  
**Scope:** 6 locations, up to 6,000 farmers  
**Objective:** Scale to national coverage

**Configuration Changes for Expansion:**
```python
# Phase 2: Multi-location
PILOT_LOCATION_IDS = [6, 4]  # Morogoro, Mbeya
TOTAL_FARMERS = 2000

# Phase 3: Full rollout
PILOT_LOCATION_IDS = [1, 2, 3, 4, 5, 6]  # All locations
TOTAL_FARMERS = 6000
```

---

## Risk Management

### Pilot-Specific Risks

| Risk | Mitigation |
|------|------------|
| **Reserves Insufficient** | Current reserve shortfall (detected); secure additional $110k funding |
| **Model Overfits to Morogoro** | Monitor performance monthly; compare against other locations |
| **Single Location Bias** | Document lessons learned for multi-location expansion |
| **Farmer Adoption Low** | Conduct education workshops; simplify insurance language |

### Financial Solvency

**Current Status (from dashboard):**
- Reserves: $25,000
- Expected Payouts (6-month): $133,557
- **Buffer: -434.2%** ← **CRITICAL UNDERFUNDING**

**Immediate Action Required:** Secure minimum $110,000 additional reserves to cover expected liability.

---

## Documentation References

| Document | Location | Purpose |
|----------|----------|---------|
| Model Performance Report | `docs/reports/FINAL_MODEL_PIPELINE_REPORT.md` | Overall model accuracy |
| Location Expansion Summary | `docs/current/6_LOCATION_EXPANSION_SUMMARY.md` | Spatial CV scores |
| ML Model Reference | `docs/references/ML_MODEL_REFERENCE.md` | Technical model details |
| Parametric Insurance | `docs/references/PARAMETRIC_INSURANCE_FINAL.md` | Insurance specifications |
| Dashboard Reference | `docs/references/FRONTEND_DASHBOARDS_COMPLETE_REFERENCE.md` | UI implementation |

---

## Contact & Governance

**Program Lead:** [To be assigned]  
**Technical Lead:** [To be assigned]  
**Location:** Morogoro Regional Office, Kilombero Basin  
**Monitoring:** Monthly performance reviews  
**Reporting:** Quarterly stakeholder updates

---

## Appendix: Morogoro Climate Profile

**Seasonal Rainfall Pattern:**
- **Long Rains:** March-May (primary growing season)
- **Short Rains:** October-December (secondary season)
- **Dry Seasons:** January-February, June-September
- **Annual Average:** ~900mm (suitable for rice cultivation)

**Historical Climate Risks (2000-2025):**
- **Drought Events:** ~15% of years (1-in-7 year event)
- **Flood Events:** ~12% of years (1-in-8 year event)
- **Crop Failures:** ~8% of years (1-in-12 year event based on NDVI)

**Model Performance by Season (Morogoro):**
- Long Rains: R² = 0.982 (98.2%) — *historical single-location benchmark*
- Short Rains: R² = 0.987 (98.7%) — *historical single-location benchmark*
- Dry Season: R² = 0.976 (97.6%) — *historical single-location benchmark*

> **Note**: Seasonal R² values above are from pre-data-leakage-fix single-location analysis and are historical benchmarks only. Production model (XGBoost R²=0.8666) uses 83 clean features across all locations.

---

**Document Status:** Forward Validation Phase (Retrospective Validation Complete)  
**Next Review:** July 2026 (end of forward testing period)
