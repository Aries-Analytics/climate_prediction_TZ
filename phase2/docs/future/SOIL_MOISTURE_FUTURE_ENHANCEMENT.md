# Soil Moisture Index - Future Enhancement Documentation

**Status**: ✅ Infrastructure Ready (Feb 2026)  
**Implementation**: Database + Ingestion Complete  
**Planned Use**: Kilombero Pilot (Morogoro) - Near-Term Activation 🎯  
**Activation**: Pending (Requires Historical Backfill + Model Retraining)

---

## Overview

Soil moisture has been added to the climate data infrastructure as a future enhancement for improved drought detection and trigger accuracy. The database schema and ingestion modules have been updated to capture this data, but it is not yet actively used in ML models or parametric insurance triggers.

---

## Current Status

### ✅ Completed (Feb 2026)

1. **Database Schema**
   - Added `soil_moisture` column to `climate_data` table
   - Type: `NUMERIC(5,3)` (supports 0.000-1.000 range)
   - Nullable: TRUE (allows gradual population)
   - Index: `idx_climate_soil_moisture` for query optimization
   - Migration: `006_add_soil_moisture.py` applied successfully

2. **Data Ingestion**
   - **ERA5**: Fetches `volumetric_soil_water_layer_1` (swvl1)
     - 0-7cm soil depth
     - Updated to store in `soil_moisture` column
   - **NASA POWER**: Fetches `GWETPROF` (Profile Soil Moisture)
     - Root zone moisture (0-100cm)
     - Updated to store in `soil_moisture` column

3. **Documentation**
   - Updated [`data_dictionary.md`](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/docs/references/data_dictionary.md)
   - Updated [`DATA_PIPELINE_REFERENCE.md`](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/docs/references/DATA_PIPELINE_REFERENCE.md)
   - Created [`soil_moisture_impact_analysis.md`](file:///c:/Users/YYY/.gemini/antigravity/brain/984a3285-21e0-4934-ac05-b61da503c9fa/soil_moisture_impact_analysis.md)
   - Updated [`PARAMETRIC_INSURANCE_FINAL.md`](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/docs/references/PARAMETRIC_INSURANCE_FINAL.md#L140) reference

### ⏳ Pending (Future Activation)

**Not Currently Active**:
- ML models do NOT use soil moisture features
- Parametric triggers do NOT check soil moisture values
- Historical data (2000-2024) does NOT have soil moisture populated

**To Activate**:
- Backfill historical soil moisture data (2000-2025)
- Add soil moisture to feature engineering
- Retrain ML models with new features
- Update parametric trigger logic
- Backtest dual-index triggers

---

## Kilombero Pilot Use Case 🎯

**Location**: Kilombero Basin, Morogoro Region, Tanzania  
**Crop**: Rice (Oryza sativa)  
**Farmers**: 1,000 smallholder farmers  
**Area**: Flood-prone valley with variable soil moisture

### Why Soil Moisture Matters for Kilombero

1. **Flood-Prone Basin**: Kilombero Valley experiences both flooding and drought
   - Soil saturation increases flood risk even with moderate rainfall
   - Dual-index (rainfall + soil moisture) provides better flood prediction

2. **Rice-Specific Water Needs**: Rice requires consistent soil moisture during critical phases
   - Transplanting: High moisture (>0.80) required
   - Flowering: Moderate moisture (0.40-0.60) optimal
   - Ripening: Lower moisture (0.20-0.40) preferred

3. **Reduced Basis Risk**: Soil moisture directly correlates with crop stress
   - Better trigger accuracy = fewer disputes
   - Improved farmer trust in parametric insurance

### Recommended Timeline for Kilombero

**Q1 2026 (Current)**: Infrastructure ready ✅  
**Q2 2026**: Activate for Kilombero pilot
- Backfill 2020-2025 soil moisture data (Morogoro location)
- Calibrate dual-index triggers for rice phases
- Backtest on Kilombero-specific historical events (2015 floods, 2019 drought)

**Q3-Q4 2026**: Monitor and refine during pilot season

---

## Use Cases (When Activated)

### 1. Dual-Index Drought Triggers

Combining rainfall and soil moisture reduces false positives:

```python
# Current (Rainfall Only)
if rainfall_mm < 120:
    trigger_payout(60)  # May trigger even if soil is saturated

# Future (Dual-Index)
if (rainfall_mm < 120 AND soil_moisture < 0.25) OR soil_moisture < 0.15:
    trigger_payout(60)  # More accurate crop stress detection
```

**Benefits**:
- Reduced basis risk (better alignment with actual crop stress)
- Industry best practice (ACRE uses dual-index)
- Fewer false positives from short dry spells over saturated soil

### 2. Enhanced Flood Detection

Saturated soil amplifies flood risk:

```python
# Current
if daily_rainfall > 258:
    trigger_payout(75)

# Future (Soil-Aware)
if daily_rainfall > 258 AND soil_moisture > 0.90:
    trigger_payout(100)  # Higher payout due to saturation + heavy rain
elif daily_rainfall > 200 AND soil_moisture > 0.95:
    trigger_payout(75)  # Lower rainfall threshold if soil saturated
```

### 3. ML Model Improvements

Adding soil moisture features may improve:
- Drought prediction accuracy (+5-10% expected)
- Flood risk forecasting
- NDVI forecasting (vegetation responds to soil moisture)

---

## Data Sources

| Source | Variable | Coverage | Resolution | Update Freq |
|--------|----------|----------|------------|-------------|
| ERA5 | `volumetric_soil_water_layer_1` (swvl1) | Global | 0.25° (~28km) | Daily |
| NASA POWER | `GWETPROF` | Global | 0.5° (~55km) | Daily |

**Data Format**: 0-1 fraction (volumetric water content)
- 0.05-0.15: Wilting point (crops stressed)
- 0.20-0.40: Field capacity (optimal)
- 0.90-1.00: Saturation (flood risk)

---

## Activation Roadmap

### Phase 1: Infrastructure (✅ COMPLETE - Feb 2026)
- [x] Database migration
- [x] Ingestion code updates
- [x] Documentation

### Phase 2: Data Population (Estimated: 2-3 days)
- [ ] Backfill historical soil moisture (2020-2025)
- [ ] Verify data quality and coverage
- [ ] Populate database with 5 years of data

### Phase 3: ML Integration (Estimated: 1-2 days)
- [ ] Add soil moisture to feature engineering
- [ ] Retrain models with new features
- [ ] Evaluate model performance improvements
- [ ] Update forecasting code

### Phase 4: Trigger Calibration (Estimated: 3-4 days)
- [ ] Define soil moisture thresholds by rice phase
- [ ] Update trigger logic for dual-index
- [ ] Backtest on 2020-2025 historical data
- [ ] Validate loss ratios and financial sustainability

### Phase 5: Production Deployment (Estimated: 1 day)
- [ ] Deploy updated models
- [ ] Deploy updated triggers
- [ ] Monitor initial performance
- [ ] Adjust thresholds if needed

**Total Estimated Effort**: 1-2 weeks  
**Recommended Timeline**: Post-pilot (Q2 2026)

---

## References

- **Implementation Details**: [`walkthrough.md`](file:///c:/Users/YYY/.gemini/antigravity/brain/984a3285-21e0-4934-ac05-b61da503c9fa/walkthrough.md)
- **Impact Analysis**: [`soil_moisture_impact_analysis.md`](file:///c:/Users/YYY/.gemini/antigravity/brain/984a3285-21e0-4934-ac05-b61da503c9fa/soil_moisture_impact_analysis.md)
- **Parametric Insurance**: [`PARAMETRIC_INSURANCE_FINAL.md`](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/docs/references/PARAMETRIC_INSURANCE_FINAL.md#L140)
- **Migration Script**: [`006_add_soil_moisture.py`](file:///c:/Users/YYY/Omdena_Capstone_project/capstone-project-lordwalt/phase2/backend/alembic/versions/006_add_soil_moisture.py)

---

**Last Updated**: February 2, 2026  
**Maintained By**: Tanzania Climate Intelligence Platform Team
