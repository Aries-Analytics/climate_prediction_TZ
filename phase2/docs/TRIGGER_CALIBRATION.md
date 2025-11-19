# Insurance Trigger Calibration Methodology

**Version:** 1.0.0  
**Last Updated:** November 2024  
**Authors:** Tanzania Climate Prediction Team

---

## Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Calibration Objectives](#calibration-objectives)
4. [Statistical Methods](#statistical-methods)
5. [Threshold Selection Rationale](#threshold-selection-rationale)
6. [Validation Approach](#validation-approach)
7. [References](#references)

---

## Overview

This document describes the methodology used to calibrate insurance triggers for the Tanzania Climate Prediction system. The calibration process ensures that parametric insurance payouts occur only during genuine extreme weather events, making the insurance product financially sustainable while providing adequate coverage to farmers.

### Key Principles

1. **Data-Driven:** All thresholds based on historical climate data analysis
2. **Scientifically Justified:** Methods aligned with WMO and FAO standards
3. **Financially Sustainable:** Target trigger rates ensure viable insurance product
4. **Regionally Appropriate:** Thresholds reflect Tanzania's climate patterns

---

## Problem Statement

### Initial State

The original trigger system had critical issues:

- **Flood Trigger:** 100% activation rate (triggered every month)
- **Drought Trigger:** 13.9% activation rate (acceptable but unvalidated)
- **Crop Failure Trigger:** 0% activation rate (too conservative)
- **Financial Impact:** $5,004/year average payout per insured entity (unsustainable)

### Root Causes

1. **Arbitrary Thresholds:** Triggers not calibrated to Tanzania's climate
2. **No Historical Validation:** Thresholds not tested against actual events
3. **Overly Sensitive Logic:** OR conditions causing excessive triggering
4. **Missing Seasonal Context:** No adjustment for wet vs dry seasons

---

## Calibration Objectives

### Target Trigger Rates

Based on actuarial analysis and historical extreme weather frequency:

| Trigger Type | Target Rate | Rationale |
|--------------|-------------|-----------|
| **Flood** | 5-15% | Extreme rainfall events occur 1-2 times per year |
| **Drought** | 8-20% | Agricultural droughts occur 1-3 times per year |
| **Crop Failure** | 3-10% | Severe vegetation stress is less frequent |

### Financial Sustainability Goals

- **Loss Ratio:** < 80% of premium income
- **Annual Payout:** < $2,000 per insured entity
- **Trigger Accuracy:** > 70% alignment with known extreme events

---

## Statistical Methods

### 1. Percentile-Based Threshold Analysis

**Method:** Calculate percentiles from historical data distribution

**Application:**
- Rainfall thresholds: 90th, 95th, 97th, 99th percentiles
- VCI thresholds: 5th, 10th, 15th percentiles (lower is worse)
- NDVI anomaly thresholds: Based on standard deviations

**Rationale:** Percentiles identify truly extreme values relative to historical norms

**Example:**
```python
# Calculate 99th percentile for daily rainfall
daily_rainfall_99th = df['rainfall_mm'].quantile(0.99)
# Result: 150mm (only 1% of days exceed this)
```

### 2. Iterative Threshold Optimization

**Algorithm:**

```
1. Start with percentile-based initial threshold
2. Apply threshold to historical data
3. Calculate resulting trigger rate
4. If rate outside target range:
   a. Adjust threshold using binary search
   b. Repeat steps 2-3
5. Validate against known extreme events
6. Return optimized threshold
```

**Convergence Criteria:**
- Trigger rate within target range
- Minimum 70% alignment with known events
- Maximum 10 iterations

### 3. Seasonal Adjustment

**Method:** Apply different thresholds based on season

**Tanzania Seasons:**
- **Wet Season:** October-May (rainy periods)
- **Dry Season:** June-September (minimal rainfall)

**Application:**
- Drought triggers use longer dry day thresholds in dry season (45 days vs 35 days)
- Flood triggers expected to concentrate in wet season (>70% of events)

**Rationale:** Climate patterns vary significantly by season in Tanzania

### 4. Multi-Condition Logic

**Approach:** Combine multiple indicators with AND/OR logic

**Flood Trigger Logic:**
```
Flood = (Daily Rainfall > 99th percentile) OR
        (7-day Rainfall > 97th percentile) OR
        (Heavy Rain Days ≥ 5 in 7-day window) OR
        (Rainfall Percentile > 99)
```

**Drought Trigger Logic:**
```
Drought = (SPI-30 < -1.5) AND
          (Consecutive Dry Days > Threshold)
```

**Rationale:** 
- OR logic for floods: Any extreme rainfall pattern triggers
- AND logic for droughts: Requires both indicators to reduce false positives

### 5. Confidence Score Calculation

**Method:** Weight trigger confidence by number of conditions met

**Formula:**
```
Confidence = Base + (Conditions_Met / Total_Conditions) × (1 - Base)

Where:
- Base = 0.25 (minimum confidence)
- Conditions_Met = Number of threshold conditions exceeded
- Total_Conditions = Total number of conditions in trigger logic
```

**Example:**
```python
# Flood trigger with 3 of 4 conditions met
confidence = 0.25 + (3/4) * (1 - 0.25) = 0.8125
```

---

## Threshold Selection Rationale

### Flood Triggers

#### Daily Rainfall Threshold: 150mm

**Data Source:** CHIRPS 2018-2023  
**Method:** 99th percentile of daily rainfall  
**Validation:** Aligns with Tanzania Meteorological Authority flood warnings  
**Reference:** WMO Guidelines on Extreme Rainfall Events

**Justification:**
- Only 1% of days exceed this threshold
- Historical flood events (2018, 2020) had rainfall >150mm
- Consistent with East African flood thresholds

#### 7-Day Cumulative Rainfall: 250mm

**Data Source:** CHIRPS 2018-2023  
**Method:** 97th percentile of 7-day rolling sum  
**Validation:** Sustained heavy rainfall leading to flooding  

**Justification:**
- Captures cumulative effect of sustained rainfall
- Soil saturation occurs after multiple days of heavy rain
- Aligns with hydrological flood models

#### Heavy Rain Days: 5 days in 7-day window

**Data Source:** CHIRPS 2018-2023  
**Method:** Days with rainfall > 95th percentile (50mm)  
**Validation:** Multiple heavy rain days indicate flood risk  

**Justification:**
- Single heavy rain day may not cause flooding
- Multiple days overwhelm drainage systems
- Observed pattern in historical flood events

### Drought Triggers

#### SPI-30 Threshold: -1.5

**Data Source:** Calculated from CHIRPS 2018-2023  
**Method:** Standardized Precipitation Index (30-day)  
**Validation:** WMO drought classification standards  
**Reference:** WMO SPI User Guide (2012)

**Justification:**
- SPI < -1.5 indicates "severe drought" per WMO standards
- Normalized index allows comparison across regions
- 30-day window captures agricultural drought timescale

#### Consecutive Dry Days: 35 days (wet season) / 45 days (dry season)

**Data Source:** CHIRPS 2018-2023  
**Method:** Analysis of dry spell duration by season  
**Validation:** FAO crop water requirements  

**Justification:**
- Wet season: Crops expect regular rainfall, 35-day gap is critical
- Dry season: Normal to have longer dry periods, 45-day threshold appropriate
- Aligns with maize growing cycle (90-120 days)

### Crop Failure Triggers

#### VCI Threshold: 20 (Critical) / 35 (Severe)

**Data Source:** MODIS NDVI 2018-2023  
**Method:** Vegetation Condition Index percentiles  
**Validation:** FAO crop stress monitoring guidelines  
**Reference:** FAO VCI Methodology (2019)

**Justification:**
- VCI < 20 indicates severe vegetation stress (FAO standard)
- VCI 20-35 indicates moderate stress
- Validated against Tanzania crop yield data

#### NDVI Anomaly: -2.0 Standard Deviations

**Data Source:** MODIS NDVI 2018-2023  
**Method:** Standardized NDVI anomaly  
**Validation:** Remote sensing crop monitoring literature  

**Justification:**
- -2σ represents significant deviation from normal
- Captures vegetation stress not reflected in VCI alone
- Consistent with academic literature on crop monitoring

#### Stress Duration: 30 days (VCI) / 21 days (NDVI)

**Data Source:** Agricultural literature and expert consultation  
**Method:** Minimum duration for crop damage  
**Validation:** Crop physiology research  

**Justification:**
- Short-term stress may not cause permanent crop damage
- 21-30 days exceeds crop recovery capacity
- Aligns with critical growth stages for maize and beans

---

## Validation Approach

### 1. Historical Event Validation

**Method:** Compare trigger activations to known extreme weather events

**Known Events Database:**
- 2018 Floods: March-May (Dar es Salaam, Morogoro)
- 2019 Drought: June-September (Central regions)
- 2020 Floods: April-May (Lake Victoria basin)
- 2022 Drought: January-March (Northern regions)

**Success Criteria:**
- ≥70% of known events trigger the system
- <20% false positive rate (triggers without known events)

### 2. Seasonal Pattern Validation

**Method:** Verify triggers align with Tanzania's climate patterns

**Expected Patterns:**
- Flood triggers: >70% during rainy seasons (Mar-May, Oct-Dec)
- Drought triggers: >60% during dry season (Jun-Sep)
- Crop failure: Distributed across growing seasons

**Validation:**
```python
# Calculate seasonal concentration
rainy_months = [3, 4, 5, 10, 11, 12]
flood_in_rainy = floods[floods['month'].isin(rainy_months)].count()
seasonal_alignment = flood_in_rainy / total_floods
# Target: > 0.70
```

### 3. Financial Sustainability Validation

**Method:** Calculate loss ratio and annual payout estimates

**Metrics:**
- **Loss Ratio:** Annual Payout / Annual Premium Income
- **Target:** < 80%
- **Calculation:** Based on trigger rates and payout amounts

**Example:**
```
Annual Premium: $2,400 per entity
Target Loss Ratio: 80%
Maximum Annual Payout: $1,920

Actual Trigger Rates:
- Flood: 10% × $750 = $75/year
- Drought: 15% × $500 = $75/year  
- Crop Failure: 6% × $1,000 = $60/year
Total: $210/year (8.75% loss ratio) ✓
```

### 4. Confidence Score Validation

**Method:** Verify confidence scores correlate with event severity

**Analysis:**
- High confidence triggers (>0.7) should align with severe events
- Low confidence triggers (0.25-0.4) should be borderline cases
- Distribution should be reasonable (not all high or all low)

---

## References

### International Standards

1. **World Meteorological Organization (WMO)**
   - SPI User Guide (2012)
   - Guidelines on Extreme Weather Events
   - Climate Monitoring Standards

2. **Food and Agriculture Organization (FAO)**
   - Vegetation Condition Index Methodology (2019)
   - Crop Water Requirements Guidelines
   - Agricultural Drought Monitoring

3. **Intergovernmental Panel on Climate Change (IPCC)**
   - Special Report on Extreme Events (SREX)
   - Climate Change and Agriculture

### Regional Data Sources

4. **Tanzania Meteorological Authority (TMA)**
   - Historical flood and drought records
   - Climate normals for Tanzania
   - Extreme weather event database

5. **FEWS NET (Famine Early Warning Systems Network)**
   - East Africa food security monitoring
   - Crop condition assessments
   - Drought impact analysis

### Data Sources

6. **CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data)**
   - Funk, C., et al. (2015). "The climate hazards infrared precipitation with stations"
   - 0.05° resolution daily rainfall data
   - Validated for East Africa

7. **MODIS NDVI (Moderate Resolution Imaging Spectroradiometer)**
   - NASA Earth Observations
   - 250m resolution vegetation indices
   - 16-day composite products

### Academic Literature

8. **McKee, T.B., et al. (1993)**
   - "The relationship of drought frequency and duration to time scales"
   - Original SPI methodology

9. **Kogan, F.N. (1995)**
   - "Application of vegetation index and brightness temperature for drought detection"
   - VCI methodology

10. **Sheffield, J., & Wood, E.F. (2008)**
    - "Global Trends and Variability in Soil Moisture and Drought Characteristics"
    - Drought monitoring best practices

---

## Appendix: Calibration Workflow

### Step-by-Step Process

```
1. Data Preparation
   ├── Load historical CHIRPS data (2018-2023)
   ├── Load historical NDVI data (2018-2023)
   ├── Calculate derived indicators (SPI, VCI, etc.)
   └── Quality check and outlier detection

2. Statistical Analysis
   ├── Calculate percentiles for all indicators
   ├── Analyze seasonal patterns
   ├── Identify extreme value distributions
   └── Generate statistical summary report

3. Threshold Calibration
   ├── Set initial thresholds (percentile-based)
   ├── Simulate trigger rates
   ├── Iterate to achieve target rates
   └── Validate against known events

4. Configuration Generation
   ├── Create trigger_thresholds.yaml
   ├── Document rationale for each threshold
   ├── Include data sources and dates
   └── Version control configuration

5. Validation
   ├── Reprocess historical data with new thresholds
   ├── Generate validation reports
   ├── Compare old vs new trigger rates
   └── Verify financial sustainability

6. Documentation
   ├── Update calibration methodology
   ├── Create configuration update guide
   └── Document lessons learned
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | Nov 2024 | Initial calibration methodology | Tanzania Climate Team |

---

**For questions or updates to this methodology, contact the Tanzania Climate Prediction Team.**
