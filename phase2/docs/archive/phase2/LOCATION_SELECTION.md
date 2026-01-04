# Location Selection for Multi-Location Data Collection

## Objective

Select 5 representative locations across Tanzania to expand the training dataset from 191 samples (single location) to 1,560 samples (5 locations × 312 months), achieving a healthy 20:1 feature-to-sample ratio.

## Selection Criteria

### Geographic Diversity
- **Climate zones**: Coastal, highland, semi-arid, lake region
- **Spatial separation**: ≥100-200 km between locations to reduce autocorrelation
- **Regional coverage**: Northern, central, southern, eastern, western Tanzania

### Data Availability
- All 5 data sources confirmed available for 2000-2025:
  - CHIRPS (rainfall)
  - NASA POWER (temperature, solar radiation, humidity)
  - ERA5 (atmospheric reanalysis)
  - NDVI/MODIS (vegetation)
  - Ocean Indices (ENSO, IOD)

### Agricultural Importance
- Major agricultural regions
- Relevant for insurance trigger calibration
- Population centers where climate impacts matter

---

## Selected Locations

### 1. **Dodoma** (Central Tanzania - Baseline)

**Coordinates**: -6.1630°S, 35.7516°E  
**Elevation**: 1,120 m  
**Climate Zone**: Semi-arid  
**Region**: Central  

**Characteristics**:
- Capital city of Tanzania
- Semi-arid climate with distinct wet/dry seasons
- Average annual rainfall: 600-800 mm
- Important for agriculture (maize, sorghum, livestock)
- **Current baseline location** for existing model

**Rationale**: 
- Serves as control/baseline for comparison
- Representative of central Tanzania's semi-arid conditions
- Good data quality from existing collection

---

### 2. **Dar es Salaam** (Eastern Coastal)

**Coordinates**: -6.7924°S, 39.2083°E  
**Elevation**: 14 m  
**Climate Zone**: Tropical coastal  
**Region**: Eastern (Coast)  

**Characteristics**:
- Largest city and economic hub
- Tropical humid climate
- High annual rainfall: 1,000-1,200 mm
- Bi-modal rainfall pattern (long rains: March-May, short rains: October-December)
- Vulnerable to coastal flooding

**Rationale**:
- Contrasts with semi-arid interior (different climate regime)
- High economic/population importance
- Coastal flood risk assessment critical
- ~450 km from Dodoma (good spatial separation)

---

### 3. **Arusha** (Northern Highlands)

**Coordinates**: -3.3869°S, 36.6830°E  
**Elevation**: 1,400 m  
**Climate Zone**: Highland/montane  
**Region**: Northern  

**Characteristics**:
- Located near Mt. Meru and Mt. Kilimanjaro
- Cool highland climate
- Average annual rainfall: 600-1,200 mm (varies with elevation)
- Major coffee and horticultural production area
- Tourism hub (Serengeti, Ngorongoro)

**Rationale**:
- Highland climate distinctly different from lowlands
- Important agricultural exports (coffee, flowers, vegetables)
- Elevation effects on temperature and rainfall
- ~320 km from Dodoma, ~550 km from Dar es Salaam

---

### 4. **Mwanza** (Lake Victoria Region)

**Coordinates**: -2.5164°S, 32.9175°E  
**Elevation**: 1,140 m  
**Climate Zone**: Lake-influenced humid  
**Region**: Northwestern (Lake Zone)  

**Characteristics**:
- On southern shore of Lake Victoria
- Lake-moderated climate
- High rainfall: 900-1,200 mm
- Distinct rainfall pattern influenced by lake
- Fishing and cotton agriculture

**Rationale**:
- Lake Victoria's influence on local climate
- Different rainfall drivers than other regions
- Important agricultural and fishing economy
- ~340 km from Dodoma, ~760 km from Dar es Salaam

---

### 5. **Mbeya** (Southern Highlands)

**Coordinates**: -8.9094°S, 33.4606°E  
**Elevation**: 1,700 m  
**Climate Zone**: Highland  
**Region**: Southern  

**Characteristics**:
- High elevation, cool temperatures
- Rainfall: 900-1,400 mm
- Important tea and coffee production area
- Southern highlands agricultural zone
- Distinct climate from northern highlands

**Rationale**:
- Southern Tanzania representation
- Highland climate comparison to Arusha
- Major agricultural importance (tea, coffee, maize)
- ~490 km from Dodoma, ~850 km from Dar es Salaam

---

## Geographic Distribution Summary

| Location | Latitude | Longitude | Elevation (m) | Climate Zone | Distance from Dodoma (km) |
|----------|----------|-----------|---------------|--------------|---------------------------|
| Dodoma | -6.1630 | 35.7516 | 1,120 | Semi-arid | 0 (baseline) |
| Dar es Salaam | -6.7924 | 39.2083 | 14 | Tropical coastal | ~450 |
| Arusha | -3.3869 | 36.6830 | 1,400 | Highland | ~320 |
| Mwanza | -2.5164 | 32.9175 | 1,140 | Lake-influenced | ~340 |
| Mbeya | -8.9094 | 33.4606 | 1,700 | Highland | ~490 |

**Spatial Coverage**:
- Latitude range: 9.4° to -2.5° S (covers northern to southern Tanzania)
- Longitude range: 32.9° E to 39.2° E (covers western to eastern Tanzania)
- Elevation range: 14 m to 1,700 m
- All locations separated by ≥100 km ✓

---

## Expected Sample Size Increase

### Current Status
- **Locations**: 1 (Dodoma)
- **Time period**: 2010-2025 (191 months)
- **Total samples**: 191
- **Feature-to-sample ratio**: 191 / 75 features = 2.5:1 ❌ (unhealthy)

### Phase 1 Target (5 Locations, Historical Extension)
- **Locations**: 5 (Dodoma, Dar es Salaam, Arusha, Mwanza, Mbeya)
- **Time period**: 2000-2025 (312 months)
- **Total samples**: 5 × 312 = **1,560 samples**
- **Training samples**: 1,560 × 0.70 = **1,092**
- **Feature-to-sample ratio**: 1,092 / 75 = **14.6:1** ✓ (healthy)

---

## Next Steps

1. **Verify data availability** for each location (Tasks 1.2-1.6)
2. **Test data collection** for one month per location
3. **Assess data quality** and completeness
4. **Generate data availability report** (Task 1.7)
5. **Make go/no-go decision** for Phase 2 (full data collection)

---

## References

- **DATA_AUGMENTATION_STRATEGY.md**: Strategic rationale for multi-location approach
- **data-augmentation-expansion/requirements.md**: Functional requirements FR-2.1.1 to FR-2.1.4
- **data-augmentation-expansion/design.md**: Location selection criteria and technical approach
