# Regional Threshold Variation Guide

**Version:** 1.0.0 (Phase 2 Feature)  
**Status:** Planning Document  
**Last Updated:** November 2024

---

## Table of Contents

1. [Overview](#overview)
2. [Tanzania Climate Zones](#tanzania-climate-zones)
3. [Regional Threshold Strategy](#regional-threshold-strategy)
4. [Implementation Guide](#implementation-guide)
5. [Configuration Examples](#configuration-examples)
6. [Data Requirements](#data-requirements)

---

## Overview

This document describes how to implement region-specific trigger thresholds for Tanzania's diverse climate zones. Regional variation allows the insurance system to account for different climate patterns across coastal, highland, and lowland areas.

### Status: Phase 2 Feature

Regional thresholds are **not currently implemented** in the system. This is a planned enhancement for Phase 2. The current system uses national-level thresholds that work reasonably well across Tanzania but could be improved with regional calibration.

### Benefits of Regional Thresholds

1. **Improved Accuracy:** Thresholds tailored to local climate patterns
2. **Better Coverage:** Appropriate triggers for each region's risks
3. **Reduced False Positives:** Fewer inappropriate triggers
4. **Enhanced Fairness:** Premiums and payouts reflect regional risk

---

## Tanzania Climate Zones

### Zone 1: Coastal Region

**Geographic Coverage:**
- Dar es Salaam
- Tanga
- Pwani (Coast)
- Lindi
- Mtwara

**Climate Characteristics:**
- High humidity year-round
- Two rainy seasons: March-May (long rains), October-December (short rains)
- Annual rainfall: 800-1,200mm
- Temperature: 25-30°C average
- **Flood Risk:** HIGH (coastal flooding, heavy rainfall)
- **Drought Risk:** MODERATE

**Threshold Adjustments Needed:**
- **Flood:** More sensitive (lower thresholds)
- **Drought:** Less sensitive (higher thresholds)
- **Crop Failure:** Moderate sensitivity

### Zone 2: Highland Region

**Geographic Coverage:**
- Arusha
- Kilimanjaro
- Mbeya
- Iringa
- Njombe

**Climate Characteristics:**
- Cooler temperatures due to elevation
- Distinct wet and dry seasons
- Annual rainfall: 600-1,000mm
- Temperature: 15-25°C average
- **Flood Risk:** LOW (good drainage, elevation)
- **Drought Risk:** MODERATE
- **Frost Risk:** Present in some areas

**Threshold Adjustments Needed:**
- **Flood:** Less sensitive (higher thresholds)
- **Drought:** Moderate sensitivity
- **Crop Failure:** More sensitive (frost + drought)

### Zone 3: Central Lowland Region

**Geographic Coverage:**
- Dodoma
- Singida
- Tabora

**Climate Characteristics:**
- Semi-arid climate
- Single rainy season: November-April
- Annual rainfall: 500-800mm
- Temperature: 22-28°C average
- **Flood Risk:** LOW
- **Drought Risk:** HIGH

**Threshold Adjustments Needed:**
- **Flood:** Much less sensitive (higher thresholds)
- **Drought:** More sensitive (lower thresholds)
- **Crop Failure:** More sensitive

### Zone 4: Lake Victoria Basin

**Geographic Coverage:**
- Mwanza
- Kagera
- Mara
- Geita

**Climate Characteristics:**
- Influenced by Lake Victoria
- Reliable rainfall year-round
- Annual rainfall: 900-1,400mm
- Temperature: 20-28°C average
- **Flood Risk:** MODERATE-HIGH (lake flooding)
- **Drought Risk:** LOW

**Threshold Adjustments Needed:**
- **Flood:** More sensitive (lake + rainfall)
- **Drought:** Less sensitive
- **Crop Failure:** Moderate sensitivity

### Zone 5: Southern Highlands

**Geographic Coverage:**
- Ruvuma
- Songwe
- Rukwa

**Climate Characteristics:**
- Highland climate with valleys
- Single rainy season: November-April
- Annual rainfall: 800-1,200mm
- Temperature: 18-26°C average
- **Flood Risk:** MODERATE
- **Drought Risk:** MODERATE

**Threshold Adjustments Needed:**
- **Flood:** Moderate sensitivity
- **Drought:** Moderate sensitivity
- **Crop Failure:** Moderate sensitivity

---

## Regional Threshold Strategy

### Multiplier Approach

Use base national thresholds with regional multipliers:

```
Regional_Threshold = National_Threshold × Regional_Multiplier
```

**Example:**
```
National flood threshold: 150mm daily rainfall
Coastal multiplier: 0.85
Coastal flood threshold: 150mm × 0.85 = 127.5mm
```

### Recommended Multipliers

| Zone | Flood | Drought | Crop Failure |
|------|-------|---------|--------------|
| Coastal | 0.85 | 1.15 | 1.00 |
| Highland | 1.20 | 1.00 | 0.90 |
| Central Lowland | 1.40 | 0.80 | 0.85 |
| Lake Victoria | 0.90 | 1.25 | 1.05 |
| Southern Highlands | 1.05 | 0.95 | 0.95 |

**Interpretation:**
- **< 1.0:** More sensitive (lower threshold, more triggers)
- **= 1.0:** Same as national threshold
- **> 1.0:** Less sensitive (higher threshold, fewer triggers)

---

## Implementation Guide

### Step 1: Define Geographic Boundaries

Create a geographic lookup table:

```python
# regions.py
TANZANIA_REGIONS = {
    'coastal': {
        'regions': ['Dar es Salaam', 'Tanga', 'Pwani', 'Lindi', 'Mtwara'],
        'lat_range': (-10.5, -4.5),
        'lon_range': (38.5, 40.5),
        'description': 'Coastal zone with high humidity and flood risk'
    },
    'highland': {
        'regions': ['Arusha', 'Kilimanjaro', 'Mbeya', 'Iringa', 'Njombe'],
        'lat_range': (-9.5, -2.5),
        'lon_range': (33.0, 37.5),
        'elevation_min': 1000,  # meters
        'description': 'Highland zone with cooler temperatures'
    },
    'central_lowland': {
        'regions': ['Dodoma', 'Singida', 'Tabora'],
        'lat_range': (-7.0, -3.5),
        'lon_range': (32.0, 36.5),
        'description': 'Semi-arid central region'
    },
    'lake_victoria': {
        'regions': ['Mwanza', 'Kagera', 'Mara', 'Geita'],
        'lat_range': (-3.0, -1.0),
        'lon_range': (31.0, 34.0),
        'description': 'Lake Victoria basin'
    },
    'southern_highlands': {
        'regions': ['Ruvuma', 'Songwe', 'Rukwa'],
        'lat_range': (-11.5, -8.0),
        'lon_range': (31.5, 36.0),
        'description': 'Southern highland zone'
    }
}
```

### Step 2: Implement Region Detection

```python
def detect_region(lat: float, lon: float, region_name: str = None) -> str:
    """
    Detect climate zone based on coordinates or region name.
    
    Parameters
    ----------
    lat : float
        Latitude
    lon : float
        Longitude
    region_name : str, optional
        Administrative region name
    
    Returns
    -------
    str
        Climate zone identifier
    """
    # Method 1: Use region name if provided
    if region_name:
        for zone, info in TANZANIA_REGIONS.items():
            if region_name in info['regions']:
                return zone
    
    # Method 2: Use coordinates
    for zone, info in TANZANIA_REGIONS.items():
        lat_min, lat_max = info['lat_range']
        lon_min, lon_max = info['lon_range']
        
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return zone
    
    # Default: return national
    return 'national'
```

### Step 3: Update Configuration File

Add regional adjustments to `trigger_thresholds.yaml`:

```yaml
regional_adjustments:
  enabled: true  # Set to true to activate regional thresholds
  
  coastal:
    description: "Coastal zone - high flood risk, moderate drought risk"
    flood_multiplier: 0.85
    drought_multiplier: 1.15
    crop_failure_multiplier: 1.00
    
  highland:
    description: "Highland zone - low flood risk, moderate drought risk"
    flood_multiplier: 1.20
    drought_multiplier: 1.00
    crop_failure_multiplier: 0.90
    
  central_lowland:
    description: "Central lowland - low flood risk, high drought risk"
    flood_multiplier: 1.40
    drought_multiplier: 0.80
    crop_failure_multiplier: 0.85
    
  lake_victoria:
    description: "Lake Victoria basin - moderate-high flood risk, low drought risk"
    flood_multiplier: 0.90
    drought_multiplier: 1.25
    crop_failure_multiplier: 1.05
    
  southern_highlands:
    description: "Southern highlands - moderate risks"
    flood_multiplier: 1.05
    drought_multiplier: 0.95
    crop_failure_multiplier: 0.95
```

### Step 4: Modify Processing Logic

Update trigger calculation to use regional thresholds:

```python
def _add_insurance_triggers(df):
    """Add insurance triggers with regional adjustments."""
    
    # Load configuration
    config = load_trigger_config()
    
    # Detect region for each row
    df['climate_zone'] = df.apply(
        lambda row: detect_region(
            row['latitude'], 
            row['longitude'], 
            row.get('region_name')
        ),
        axis=1
    )
    
    # Apply regional multipliers if enabled
    if config.get('regional_adjustments', {}).get('enabled', False):
        df = apply_regional_thresholds(df, config)
    else:
        df = apply_national_thresholds(df, config)
    
    return df

def apply_regional_thresholds(df, config):
    """Apply region-specific thresholds."""
    
    for zone in df['climate_zone'].unique():
        if zone == 'national':
            continue
            
        # Get regional multipliers
        zone_config = config['regional_adjustments'].get(zone, {})
        flood_mult = zone_config.get('flood_multiplier', 1.0)
        drought_mult = zone_config.get('drought_multiplier', 1.0)
        
        # Get base thresholds
        base_rainfall = config['flood_triggers']['daily_rainfall_mm']['threshold']
        base_spi = config['drought_triggers']['spi_30day']['threshold']
        
        # Calculate regional thresholds
        regional_rainfall = base_rainfall * flood_mult
        regional_spi = base_spi * drought_mult
        
        # Apply to rows in this zone
        zone_mask = df['climate_zone'] == zone
        
        df.loc[zone_mask, 'flood_trigger'] = (
            df.loc[zone_mask, 'rainfall_mm'] > regional_rainfall
        ).astype(int)
        
        df.loc[zone_mask, 'drought_trigger'] = (
            (df.loc[zone_mask, 'spi_30day'] < regional_spi) &
            (df.loc[zone_mask, 'consecutive_dry_days'] > 35)
        ).astype(int)
    
    return df
```

### Step 5: Calibrate Regional Thresholds

For each region:

1. **Extract Regional Data:**
   ```python
   coastal_data = df[df['climate_zone'] == 'coastal']
   ```

2. **Calculate Regional Percentiles:**
   ```python
   coastal_p99 = coastal_data['rainfall_mm'].quantile(0.99)
   ```

3. **Determine Multiplier:**
   ```python
   national_p99 = df['rainfall_mm'].quantile(0.99)
   multiplier = coastal_p99 / national_p99
   ```

4. **Validate Trigger Rates:**
   ```python
   coastal_flood_rate = coastal_data['flood_trigger'].mean()
   # Target: 5-15%
   ```

5. **Iterate Until Optimal:**
   - Adjust multipliers
   - Reprocess data
   - Check trigger rates
   - Repeat until within target

---

## Configuration Examples

### Example 1: Enable Regional Thresholds

```yaml
# In trigger_thresholds.yaml

regional_adjustments:
  enabled: true  # Changed from false
  
  # ... rest of regional configuration
```

### Example 2: Adjust Coastal Flood Sensitivity

```yaml
coastal:
  description: "Coastal zone - increased flood sensitivity"
  flood_multiplier: 0.80  # Changed from 0.85 (more sensitive)
  drought_multiplier: 1.15
  crop_failure_multiplier: 1.00
  rationale: "2024 coastal floods indicate need for higher sensitivity"
  calibration_date: "2024-12-01"
```

### Example 3: Add New Region

```yaml
regional_adjustments:
  enabled: true
  
  # ... existing regions ...
  
  zanzibar:
    description: "Zanzibar islands - unique coastal climate"
    flood_multiplier: 0.75
    drought_multiplier: 1.30
    crop_failure_multiplier: 1.10
    rationale: "Island climate requires distinct thresholds"
    data_source: "TMA Zanzibar station data 2018-2024"
    calibration_date: "2024-12-01"
```

---

## Data Requirements

### Minimum Data for Regional Calibration

For each region, you need:

1. **Historical Climate Data:**
   - Minimum 5 years of daily data
   - CHIRPS rainfall data
   - MODIS NDVI data
   - Coverage across the region

2. **Geographic Information:**
   - Latitude/longitude coordinates
   - Administrative region names
   - Elevation data (for highlands)

3. **Known Extreme Events:**
   - Historical flood events by region
   - Historical drought events by region
   - Crop failure records

4. **Validation Data:**
   - Insurance claims data (if available)
   - Agricultural yield data
   - Weather station observations

### Data Quality Checks

Before regional calibration:

- [ ] Sufficient data coverage (>80% of days)
- [ ] No systematic biases between regions
- [ ] Consistent data sources across regions
- [ ] Validated against weather stations
- [ ] Outliers identified and handled

---

## Implementation Checklist

### Phase 2 Implementation Steps

- [ ] **Data Collection**
  - [ ] Gather 5+ years of regional climate data
  - [ ] Compile known extreme events by region
  - [ ] Collect geographic boundary definitions
  - [ ] Validate data quality

- [ ] **Analysis**
  - [ ] Calculate regional climate statistics
  - [ ] Determine optimal multipliers
  - [ ] Validate against historical events
  - [ ] Document regional characteristics

- [ ] **Configuration**
  - [ ] Update trigger_thresholds.yaml
  - [ ] Add regional multipliers
  - [ ] Document rationale for each region
  - [ ] Version control changes

- [ ] **Code Updates**
  - [ ] Implement region detection logic
  - [ ] Update trigger calculation functions
  - [ ] Add regional threshold application
  - [ ] Update validation reports

- [ ] **Testing**
  - [ ] Test region detection accuracy
  - [ ] Validate trigger rates by region
  - [ ] Check seasonal alignment by region
  - [ ] Verify financial sustainability

- [ ] **Deployment**
  - [ ] Deploy to test environment
  - [ ] Monitor for 1 month
  - [ ] Gather stakeholder feedback
  - [ ] Deploy to production

- [ ] **Documentation**
  - [ ] Update user guides
  - [ ] Create regional threshold maps
  - [ ] Document lessons learned
  - [ ] Train users on regional features

---

## Validation Metrics by Region

Track these metrics for each region:

| Metric | Target | Coastal | Highland | Central | Lake | Southern |
|--------|--------|---------|----------|---------|------|----------|
| Flood Rate | 5-15% | TBD | TBD | TBD | TBD | TBD |
| Drought Rate | 8-20% | TBD | TBD | TBD | TBD | TBD |
| Crop Failure Rate | 3-10% | TBD | TBD | TBD | TBD | TBD |
| Seasonal Alignment | >70% | TBD | TBD | TBD | TBD | TBD |
| Event Detection | >70% | TBD | TBD | TBD | TBD | TBD |

---

## Future Enhancements

### Phase 3 Possibilities

1. **Sub-Regional Thresholds:**
   - District-level calibration
   - Microclimate adjustments

2. **Dynamic Thresholds:**
   - Adjust based on climate trends
   - Machine learning optimization

3. **Crop-Specific Thresholds:**
   - Different thresholds for maize, rice, beans
   - Growth stage considerations

4. **Real-Time Adjustment:**
   - Update thresholds based on recent data
   - Adaptive learning algorithms

---

## Support and Resources

### Additional Documentation

- `TRIGGER_CALIBRATION.md` - Calibration methodology
- `TRIGGER_CONFIGURATION_GUIDE.md` - Configuration updates
- Tanzania Meteorological Authority climate zones
- FAO AgroEcological Zones for Tanzania

### Contact

For questions about regional threshold implementation:
- Tanzania Climate Prediction Team
- Regional agricultural extension officers
- TMA regional offices

---

**Note:** This is a planning document for Phase 2. Regional thresholds are not currently active in the system. The `enabled: false` flag in the configuration file prevents regional adjustments from being applied.

---

**Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Nov 2024 | Initial regional variation guide (Phase 2 planning) |
