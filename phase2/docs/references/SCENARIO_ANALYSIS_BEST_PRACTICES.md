# Parametric Insurance Scenario Analysis - Industry Best Practices

**Date:** January 12, 2026  
**Research Source:** ARC, Swiss Re, Munich Re, World Bank, PwC Actuarial Standards  
**Purpose:** Design comprehensive scenario analysis for Morogoro Rice Pilot

---

## Industry Standard Parameters

### **1. Climate/Weather Parameters** (Primary Triggers)

Based on ARC Africa RiskView and parametric insurance best practices:

#### **A. Rainfall Parameters**
- **Cumulative Seasonal Rainfall** (mm)
  - Range: -80% to +150% of historical mean
  - Critical thresholds: <30% = severe drought, >150% = flood risk
  
- **Rainfall Distribution** (timing/concentration)
  - Early season drought (germination failure)
  - Mid-season dry spells (flowering stress)
  - Late season excess (harvest disruption)

- **Consecutive Dry Days (CDD)**
  - Critical for rice: >15 days during flowering

#### **B. Temperature Parameters**
- **Heat Stress** (+°C above normal)
  - Range: 0°C to +5°C
  - Critical: >2°C during flowering (yield loss 20-40%)
  
- **Cold Stress** (-°C below normal)
  - Range: -2°C to 0°C
  - Critical for rice transplanting phase

#### **C. Extreme Weather Events**
- **Heavy Rainfall Days** (>50mm/day)
  - Flood trigger: 3+ consecutive days
  
- **Hail Events** (frequency/intensity)
- **Strong Winds** (>60 km/h during critical growth stages)

### **2. Crop-Specific Parameters** (Rice - Kilombero Basin)

#### **A. Growth Stage Impacts**
Rice has 4 critical stages:
1. **Germination/Establishment** (0-30 days)
   - Vulnerable to: dry planting conditions, early drought
2. **Vegetative Growth** (30-60 days)
   - Vulnerable to: waterlogging, nutrient deficiency
3. **Flowering** (60-90 days)
   - Vulnerable to: heat stress, water stress (MOST CRITICAL)
4. **Grain Filling/Maturation** (90-120 days)
   - Vulnerable to: pests, excess rainfall

#### **B. Water Requirements Satisfaction Index (WRSI)**
- ARC standard for drought modeling
- Measures: Actual ET / Potential ET
- Thresholds:
  - WRSI <50% = Crop failure (90% yield loss)
  - WRSI 50-70% = Severe stress (40-60% yield loss)
  - WRSI 70-85% = Moderate stress (20-30% yield loss)
  - WRSI >85% = Normal conditions

### **3. Vegetation/Satellite Indices**

#### **NDVI (Normalized Difference Vegetation Index)**
- Range: -1 to +1 (typical crop: 0.2-0.8)
- Drought indicator: NDVI <0.3
- Used for: Real-time crop health monitoring

#### **VHI (Vegetation Health Index)**
- Combines: Temperature Condition Index (TCI) + Vegetation Condition Index (VCI)
- Range: 0-100
- Thresholds:
  - VHI <20 = Extreme drought
  - VHI 20-35 = Severe drought
  - VHI 35-50 = Moderate drought

### **4. Soil Parameters**

#### **Soil Moisture Content** (%)
- Field capacity vs. wilting point
- Critical for rice: Maintaining saturation (0-5cm standing water)

#### **Soil Type** (Kilombero Basin)
- Heavy clay soils (good water retention)
- pH levels: 5.5-7.5 optimal for rice

### **5. Economic Parameters** (Portfolio Impact)

#### **A. Premium Adjustments**
- Dynamic pricing based on forecast probability
- Range: -20% to +50% of base premium

#### **B. Coverage Levels**
- Sum insured: 50%, 70%, 90% of expected revenue
- Morogoro: Currently 100% coverage ($90/farmer max)

#### **C. Deductibles/Waiting Periods**
- Standard: 14-30 day waiting period
- Deductible: First 10% of loss (reduce moral hazard)

### **6. Multi-Peril Scenarios** (Realistic Combinations)

Real-world disasters rarely occur in isolation:

1. **El Niño Drought** (ARC historical scenarios)
   - Rainfall: -50%
   - Temperature: +2°C
   - WRSI: <60%
   - Duration: Full season
   
2. **La Niña Flood**
   - Rainfall: +80%
   - Heavy rainfall days: 8+ days
   - Waterlogging duration: >10 days
   
3. **Flash Drought** (Rapid onset)
   - Normal start (-10%)
   - Mid-season collapse: -70% rainfall
   - Consecutive dry days: 25+
   
4. **Heat Wave + Water Stress**
   - Temperature: +4°C
   - Rainfall: -30%
   - Timing: During flowering (days 60-75)
   
5. **Sequential Shocks**
   - Early drought (-40%) → Mid-season flood (+80%)
   - Tests recovery capacity

---

## Recommended Scenario Framework

### **Tier 1: Standard Scenarios** (Regulatory/Annual Review)

Required by insurance regulators:

1. **Baseline** = Historical 20-year average
2. **Moderate Stress** = 1-in-10-year event
3. **Severe Stress** = 1-in-25-year event
4. **Extreme Stress** = 1-in-50-year event

### **Tier 2: Tailored Scenarios** (Operational Decision-Making)

Specific to Morogoro Rice Context:

1. **Localized Drought** (Kilombero Basin specific)
2. **Kilombero River Flood** (riverine flooding)
3. **Delayed Monsoon** (planting window missed)
4. **Pest Outbreak** (triggered by weather anomalies)
5. **Price Shock** (market collapse + climate stress)

### **Tier 3: Climate Change Projections** (Long-term Planning)

IPCC RCP scenarios for Tanzania:

- **RCP 4.5** (moderate emissions): +1.5°C by 2050
- **RCP 8.5** (high emissions): +3°C by 2050
- Rainfall uncertainty: -10% to +20%

---

## Implementation Recommendations

### **Phase 1: Enhanced Scenario Builder** (User-Friendly)

Replace current simple sliders with structured interface:

**Scenario Templates:**
- Dropdown menu with 10 pre-defined scenarios
- Each with auto-populated parameters
- Option to customize

**Parameter Groups:**
1. **Rainfall & Water**
   - Seasonal total (slider: -80% to +150%)
   - Distribution pattern (dropdown: Early/Mid/Late drought or flood)
   - Consecutive dry days (slider: 0-40 days)

2. **Temperature & Heat**
   - Average temperature change (slider: -2°C to +5°C)
   - Heat wave days >35°C (slider: 0-30 days)
   - Timing (checkboxes: Each growth stage)

3. **Extreme Events**
   - Heavy rainfall days (slider: 0-15 days)
   - Hail/wind events (yes/no + intensity)

4. **Crop & Soil**
   - Growth stage affected (dropdown)
   - WRSI estimate (auto-calculated from rainfall)
   - Soil moisture status (low/normal/saturated)

5. **Economic Factors**
   - Premium adjustment (slider: -20% to +50%)
   - Crop price change (slider: -40% to +80%)
   - Coverage level (50%, 70%, 90%, 100%)

### **Phase 2: Advanced Outputs**

**Scenario Results Should Show:**

1. **Direct Impact**
   - Expected yield loss (0-100%)
   - Affected farmers (0-1000)
   - Payout amount ($0 - $90,000)

2. **Portfolio Metrics**
   - Updated loss ratio
   - Reserve depletion %
   - Solvency status

3. **Comparison Charts**
   - Scenario vs. Baseline
   - Scenario vs. Current High-Risk Forecasts
   - Multiple scenarios compared

4. **Sensitivity Analysis**
   - "What if rainfall was 10% worse?"
   - Key parameter tipping points

### **Phase 3: Stress Testing Suite**

Automated batch testing:
- Run all 10 standard scenarios
- Generate PDF report
- Traffic light dashboard (Green/Yellow/Red)

---

## Data Requirements

To implement properly, you need:

### **Historical Data** (Minimum):
- 20 years of rainfall data (Kilombero Basin)
- 10 years of rice yield data (Morogoro)
- 5 years of temperature anomalies

### **Real-Time Data** (Ongoing):
- Daily rainfall (weather stations or satellite)
- NDVI from Sentinel-2 (free)
- Temperature forecasts (Met Tanzania)

### **Calibration Data**:
- Farmer yield surveys
- Actual payout history (once pilot runs 1 year)

---

## Industry Benchmarks

| Parameter | ARC Africa | Swiss Re | Your Current | Recommended |
|-----------|------------|----------|--------------|-------------|
| Scenario Count | 15+ standard | 20+ tailored | 2 basic | 10 standard + custom |
| Parameters | 8-12 | 15-20 | 2 | 10-15 |
| WRSI Integration | ✅ Core | ✅ Optional | ❌ | ✅ Add |
| Multi-peril | ✅ Yes | ✅ Yes | ❌ | ✅ Add |
| Growth stage | ✅ Yes | ✅ Yes | ❌ | ✅ Add |
| Climate projections | ✅ RCP 4.5/8.5 | ✅ Yes | ❌ | Future phase |

---

## Sample Output (Enhanced Scenario)

**Scenario:** "El Niño Drought - Severe"

**Parameters:**
- Rainfall: -55% (82mm vs. 182mm normal)
- Temperature: +2.5°C
- Consecutive dry days: 28 days (during flowering)
- WRSI: 58% (Severe stress)
- Growth stage: Flowering (most vulnerable)

**Calculated Impacts:**
- Expected yield loss: 62%
- Farmers triggering payout: 850 (85%)
- Drought payout: $51,000 ($60 × 850)
- Portfolio loss ratio: 136% (CRITICAL)
- Reserve after payout: $99,000 (66% depleted)
- Solvency: ⚠️ MONITOR - reserves adequate but single event depletes 33%

**Recommendations:**
1. 🚨 Secure $50k reinsurance layer for >80% trigger events
2. 📊 Increase premiums by 15% OR reduce coverage to 80%
3. 🌾 Encourage drought-resistant rice varieties (reduce payout frequency)

---

## Next Steps for Implementation

1. ✅ Research complete (this document)
2. ⏳ Design enhanced UI with parameter groups
3. ⏳ Update backend to handle multi-parameter scenarios
4. ⏳ Add pre-defined scenario templates
5. ⏳ Implement WRSI calculation
6. ⏳ Add growth stage modeling
7. ⏳ Create PDF report generator

**Priority:** Implement Parameter Groups + Templates first (biggest UX improvement)

---

**Document prepared by:** AI Analysis based on industry research  
**Version:** 1.0  
**Purpose:** Guide Phase 3B scenario analysis enhancement
