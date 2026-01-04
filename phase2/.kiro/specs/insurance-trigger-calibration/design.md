# Design Document: Insurance Trigger Calibration

## Overview

This design addresses the critical issue where flood triggers activate 100% of the time, making the parametric insurance product financially unsustainable. The solution involves a comprehensive recalibration of all insurance triggers (drought, flood, crop failure) using data-driven statistical analysis of historical climate patterns in Tanzania.

**Current State:**
- Flood trigger: 100% activation rate (should be 5-15%)
- Drought trigger: 13.9% activation rate (acceptable but needs validation)
- Crop failure trigger: 0% activation rate (too conservative)
- Average payout: $417/month per insured entity
- Annual cost: $5,004/year (unsustainable)

**Target State:**
- Flood trigger: 5-15% activation rate
- Drought trigger: 8-20% activation rate
- Crop failure trigger: 3-10% activation rate
- Triggers aligned with Tanzania's seasonal patterns
- Financially sustainable payout structure

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Trigger Calibration System                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │     1. Data Analysis & Calibration      │
        │  - Load historical climate data         │
        │  - Calculate percentiles & statistics   │
        │  - Identify extreme event thresholds    │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │     2. Threshold Recommendation         │
        │  - Generate threshold proposals         │
        │  - Validate against known events        │
        │  - Calculate expected trigger rates     │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │     3. Configuration Generation         │
        │  - Create trigger_thresholds.yaml       │
        │  - Document rationale & sources         │
        │  - Version control configuration        │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │     4. Trigger Recalculation            │
        │  - Apply new thresholds to data         │
        │  - Recalculate all trigger flags        │
        │  - Update confidence scores             │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │     5. Validation & Reporting           │
        │  - Compare old vs new trigger rates     │
        │  - Generate validation reports          │
        │  - Update business metrics              │
        └─────────────────────────────────────────┘
```

### Component Architecture

```
modules/
├── calibration/
│   ├── __init__.py
│   ├── analyze_thresholds.py      # Statistical analysis
│   ├── calibrate_triggers.py      # Threshold recommendation
│   └── validate_triggers.py       # Validation against events
├── processing/
│   ├── process_chirps.py          # Updated with new thresholds
│   └── process_ndvi.py            # Updated with new thresholds
└── config/
    └── trigger_thresholds.yaml    # Centralized configuration

reporting/
├── business_metrics.py            # Updated with new triggers
└── trigger_validation_report.py  # New validation reporting
```

## Components and Interfaces

### Component 1: Threshold Analyzer (`modules/calibration/analyze_thresholds.py`)

**Purpose:** Analyze historical climate data to determine appropriate trigger thresholds.

**Key Functions:**

```python
def analyze_rainfall_distribution(df: pd.DataFrame) -> Dict[str, float]:
    """
    Analyze rainfall distribution to determine flood thresholds.
    
    Returns:
        Dictionary with percentile values:
        - daily_rainfall_p95, p97, p99
        - rainfall_7day_p95, p97, p99
        - rainfall_30day_p90, p95, p97
    """

def analyze_drought_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """
    Analyze drought indicators to determine drought thresholds.
    
    Returns:
        Dictionary with:
        - spi_thresholds (by severity level)
        - consecutive_dry_days_thresholds (by season)
        - rainfall_deficit_thresholds
    """

def analyze_vegetation_stress(df: pd.DataFrame) -> Dict[str, float]:
    """
    Analyze NDVI/VCI to determine crop failure thresholds.
    
    Returns:
        Dictionary with:
        - vci_thresholds (by severity)
        - ndvi_anomaly_thresholds
        - stress_duration_thresholds
    """

def generate_threshold_report(analysis_results: Dict) -> str:
    """
    Generate comprehensive threshold analysis report.
    
    Returns:
        Path to generated PDF/HTML report
    """
```

**Inputs:**
- Historical CHIRPS rainfall data (2010-2025)
- Historical NDVI data (2010-2025)
- Known extreme weather event dates (optional)

**Outputs:**
- Statistical summary JSON file
- Threshold recommendation report
- Distribution visualization plots

### Component 2: Trigger Calibrator (`modules/calibration/calibrate_triggers.py`)

**Purpose:** Generate optimized trigger threshold configurations.

**Key Functions:**

```python
def calibrate_flood_triggers(
    rainfall_stats: Dict,
    target_trigger_rate: float = 0.10
) -> Dict[str, float]:
    """
    Calibrate flood trigger thresholds to achieve target rate.
    
    Parameters:
        rainfall_stats: Output from analyze_rainfall_distribution
        target_trigger_rate: Desired trigger rate (default 10%)
    
    Returns:
        Dictionary with calibrated thresholds:
        - daily_rainfall_threshold
        - rainfall_7day_threshold
        - heavy_rain_days_threshold
        - rainfall_percentile_threshold
    """

def calibrate_drought_triggers(
    drought_stats: Dict,
    target_trigger_rate: float = 0.12
) -> Dict[str, float]:
    """
    Calibrate drought trigger thresholds.
    
    Returns:
        Dictionary with calibrated thresholds by season
    """

def calibrate_crop_failure_triggers(
    vegetation_stats: Dict,
    target_trigger_rate: float = 0.06
) -> Dict[str, float]:
    """
    Calibrate crop failure trigger thresholds.
    
    Returns:
        Dictionary with calibrated VCI and NDVI thresholds
    """

def simulate_trigger_rates(
    df: pd.DataFrame,
    thresholds: Dict
) -> Dict[str, float]:
    """
    Simulate trigger rates with proposed thresholds.
    
    Returns:
        Dictionary with simulated rates for each trigger type
    """
```

**Algorithm for Threshold Calibration:**

1. Start with percentile-based thresholds (e.g., 95th, 97th, 99th)
2. Apply thresholds to historical data
3. Calculate resulting trigger rate
4. If rate is outside target range:
   - Adjust thresholds iteratively
   - Use binary search for efficiency
5. Validate against known extreme events
6. Return optimized thresholds

### Component 3: Configuration Manager (`modules/config/trigger_thresholds.yaml`)

**Purpose:** Centralized, version-controlled trigger threshold configuration.

**Configuration Structure:**

```yaml
version: "1.0.0"
calibration_date: "2025-11-17"
data_period: "2018-01-01 to 2023-12-31"
target_trigger_rates:
  flood: 0.10  # 10% of months
  drought: 0.12  # 12% of months
  crop_failure: 0.06  # 6% of months

flood_triggers:
  daily_rainfall_mm:
    threshold: 150  # 99th percentile
    rationale: "Based on historical flood events in Tanzania"
    data_source: "CHIRPS 2010-2025"
  
  rainfall_7day_mm:
    threshold: 250  # 97th percentile
    rationale: "Sustained heavy rainfall leading to flooding"
    data_source: "CHIRPS 2010-2025"
  
  heavy_rain_days_7day:
    threshold: 5
    heavy_rain_definition_mm: 50  # 95th percentile
    rationale: "Multiple heavy rain days indicate flood risk"
  
  rainfall_percentile:
    threshold: 99
    rationale: "Extreme rainfall events"

drought_triggers:
  spi_30day:
    threshold: -1.5
    rationale: "Severe drought classification per WMO standards"
    data_source: "Calculated from CHIRPS"
  
  consecutive_dry_days:
    wet_season_threshold: 35  # Oct-May
    dry_season_threshold: 45  # Jun-Sep
    dry_day_definition_mm: 1.0
    rationale: "Extended dry periods during growing season"
  
  rainfall_deficit_pct:
    threshold: 50
    rationale: "Significant deficit from climatological normal"

crop_failure_triggers:
  vci_threshold:
    critical: 20
    severe: 35
    duration_days: 30
    rationale: "FAO crop stress thresholds"
    data_source: "MODIS NDVI 2010-2025"
  
  ndvi_anomaly_std:
    threshold: -2.0
    duration_days: 21
    rationale: "Significant vegetation stress"
  
  crop_failure_risk_score:
    threshold: 75
    rationale: "High probability of crop failure"

regional_adjustments:
  enabled: false  # Phase 2 feature
  regions:
    coastal:
      flood_multiplier: 1.2  # Higher flood risk
    highland:
      drought_multiplier: 0.8  # Lower drought risk
    lowland:
      flood_multiplier: 1.1
```

### Component 4: Updated Processing Modules

**Changes to `modules/processing/process_chirps.py`:**

```python
from modules.calibration.config_loader import load_trigger_config

def _add_insurance_triggers(df):
    """
    Add insurance trigger indicators using calibrated thresholds.
    """
    # Load configuration
    config = load_trigger_config()
    flood_config = config['flood_triggers']
    drought_config = config['drought_triggers']
    
    # FLOOD TRIGGER (updated thresholds)
    df["flood_trigger"] = (
        (df["rainfall_7day"] > flood_config['rainfall_7day_mm']['threshold']) |
        (df["rainfall_mm"] > flood_config['daily_rainfall_mm']['threshold']) |
        (df["heavy_rain_days_7day"] >= flood_config['heavy_rain_days_7day']['threshold']) |
        (df["rainfall_percentile"] > flood_config['rainfall_percentile']['threshold'])
    ).astype(int)
    
    # DROUGHT TRIGGER (updated with seasonal logic)
    # Determine season-specific threshold
    df['season_type'] = df['month'].apply(
        lambda m: 'wet' if m in [10, 11, 12, 1, 2, 3, 4, 5] else 'dry'
    )
    
    dry_day_threshold = df['season_type'].map({
        'wet': drought_config['consecutive_dry_days']['wet_season_threshold'],
        'dry': drought_config['consecutive_dry_days']['dry_season_threshold']
    })
    
    df["drought_trigger"] = (
        (df["spi_30day"] < drought_config['spi_30day']['threshold']) &
        (df["consecutive_dry_days"] >= dry_day_threshold)
    ).astype(int)
    
    # Update confidence calculations
    # ... (similar updates with config-driven thresholds)
    
    return df
```

**Changes to `modules/processing/process_ndvi.py`:**

```python
def _add_insurance_triggers(df):
    """
    Add crop failure triggers using calibrated thresholds.
    """
    config = load_trigger_config()
    crop_config = config['crop_failure_triggers']
    
    # CROP FAILURE TRIGGER (updated)
    vci_threshold = crop_config['vci_threshold']['critical']
    duration_threshold = crop_config['vci_threshold']['duration_days']
    
    df["crop_failure_trigger"] = (
        ((df["vci"] < vci_threshold) & (df["stress_duration"] >= duration_threshold)) |
        ((df["ndvi_anomaly_std"] < crop_config['ndvi_anomaly_std']['threshold']) &
         (df["stress_duration"] >= crop_config['ndvi_anomaly_std']['duration_days'])) |
        (df["crop_failure_risk"] > crop_config['crop_failure_risk_score']['threshold'])
    ).astype(int)
    
    return df
```

### Component 5: Validation Reporter (`reporting/trigger_validation_report.py`)

**Purpose:** Generate comprehensive validation reports comparing old vs new triggers.

**Key Functions:**

```python
def compare_trigger_rates(
    old_data: pd.DataFrame,
    new_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Compare trigger rates before and after recalibration.
    
    Returns:
        DataFrame with comparison metrics
    """

def validate_seasonal_patterns(df: pd.DataFrame) -> Dict:
    """
    Validate that triggers align with Tanzania's rainy seasons.
    
    Returns:
        Dictionary with seasonal trigger distribution
    """

def calculate_financial_impact(df: pd.DataFrame) -> Dict:
    """
    Calculate updated financial impact with new triggers.
    
    Returns:
        Dictionary with payout estimates and sustainability metrics
    """

def generate_validation_report(
    old_data: pd.DataFrame,
    new_data: pd.DataFrame,
    output_dir: str
) -> str:
    """
    Generate comprehensive validation report.
    
    Returns:
        Path to generated report
    """
```

## Data Models

### Threshold Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Dict, Optional

class ThresholdConfig(BaseModel):
    """Threshold configuration with validation."""
    threshold: float
    rationale: str
    data_source: str
    calibration_date: Optional[str] = None

class FloodTriggerConfig(BaseModel):
    daily_rainfall_mm: ThresholdConfig
    rainfall_7day_mm: ThresholdConfig
    heavy_rain_days_7day: Dict[str, float]
    rainfall_percentile: ThresholdConfig

class DroughtTriggerConfig(BaseModel):
    spi_30day: ThresholdConfig
    consecutive_dry_days: Dict[str, float]
    rainfall_deficit_pct: ThresholdConfig

class CropFailureTriggerConfig(BaseModel):
    vci_threshold: Dict[str, float]
    ndvi_anomaly_std: ThresholdConfig
    crop_failure_risk_score: ThresholdConfig

class TriggerThresholds(BaseModel):
    """Complete trigger threshold configuration."""
    version: str
    calibration_date: str
    data_period: str
    target_trigger_rates: Dict[str, float]
    flood_triggers: FloodTriggerConfig
    drought_triggers: DroughtTriggerConfig
    crop_failure_triggers: CropFailureTriggerConfig
    regional_adjustments: Optional[Dict] = None
```

### Validation Report Schema

```python
class TriggerValidationReport(BaseModel):
    """Validation report data model."""
    report_date: str
    data_period: str
    
    trigger_rates: Dict[str, Dict[str, float]]  # old vs new
    seasonal_distribution: Dict[str, Dict[str, int]]
    confidence_scores: Dict[str, Dict[str, float]]
    
    financial_impact: Dict[str, float]
    sustainability_metrics: Dict[str, bool]
    
    recommendations: List[str]
    warnings: List[str]
```

## Error Handling

### Configuration Validation

```python
def validate_trigger_config(config: Dict) -> Tuple[bool, List[str]]:
    """
    Validate trigger configuration for correctness.
    
    Checks:
    - All required fields present
    - Thresholds within reasonable ranges
    - Rationale provided for each threshold
    - Data sources documented
    
    Returns:
        (is_valid, list_of_errors)
    """
```

### Fallback Mechanisms

1. **Missing Configuration:**
   - Log warning
   - Use scientifically-justified default values
   - Continue processing with defaults

2. **Invalid Threshold Values:**
   - Log error with details
   - Reject configuration
   - Require manual correction

3. **Data Quality Issues:**
   - Flag outliers in calibration data
   - Provide data quality report
   - Recommend data cleaning steps

## Testing Strategy

### Unit Tests

```python
# tests/test_calibration.py

def test_analyze_rainfall_distribution():
    """Test rainfall percentile calculation."""
    
def test_calibrate_flood_triggers():
    """Test flood trigger calibration achieves target rate."""
    
def test_config_validation():
    """Test configuration validation catches errors."""
    
def test_threshold_application():
    """Test new thresholds applied correctly to data."""
```

### Integration Tests

```python
# tests/test_trigger_integration.py

def test_end_to_end_calibration():
    """Test complete calibration workflow."""
    
def test_trigger_rate_validation():
    """Test trigger rates within acceptable ranges."""
    
def test_financial_sustainability():
    """Test payout rates are financially sustainable."""
```

### Validation Tests

```python
# tests/test_trigger_validation.py

def test_seasonal_alignment():
    """Test triggers align with Tanzania's rainy seasons."""
    
def test_known_event_detection():
    """Test triggers activate during known flood/drought events."""
    
def test_trigger_consistency():
    """Test triggers are consistent across data processing runs."""
```

## Performance Considerations

### Calibration Performance

- **Expected Runtime:** 2-5 minutes for full calibration
- **Memory Usage:** ~500MB for 6 years of daily data
- **Optimization:** Use vectorized pandas operations

### Processing Performance

- **Impact:** Minimal (configuration loading is fast)
- **Caching:** Load configuration once per processing run
- **Scalability:** Configuration-driven approach scales well

## Security Considerations

### Configuration Security

- Store configuration in version control
- Require code review for threshold changes
- Document all changes with rationale
- Maintain audit trail of configuration versions

### Data Privacy

- No PII in calibration data
- Aggregate statistics only in reports
- Secure storage of historical climate data

## Deployment Strategy

### Phase 1: Calibration (Week 1)

1. Implement threshold analyzer
2. Run calibration on historical data
3. Generate threshold recommendations
4. Review and approve thresholds

### Phase 2: Implementation (Week 1-2)

1. Create configuration file
2. Update processing modules
3. Implement configuration loader
4. Run integration tests

### Phase 3: Validation (Week 2)

1. Reprocess historical data with new triggers
2. Generate validation reports
3. Compare old vs new trigger rates
4. Update business metrics

### Phase 4: Deployment (Week 2)

1. Deploy to production
2. Monitor trigger rates
3. Generate updated financial reports
4. Document lessons learned

## Monitoring and Maintenance

### Ongoing Monitoring

- Track trigger rates monthly
- Alert if rates drift outside acceptable ranges
- Monitor confidence score distributions
- Review financial sustainability metrics

### Annual Recalibration

- Recalibrate thresholds annually with new data
- Update configuration with latest statistics
- Validate against recent extreme events
- Adjust for climate change trends

## Dependencies

### External Libraries

- pandas >= 1.5.0
- numpy >= 1.23.0
- scipy >= 1.9.0 (for statistical functions)
- pyyaml >= 6.0 (for configuration)
- pydantic >= 2.0 (for validation)

### Internal Dependencies

- utils/logger.py
- utils/config.py
- modules/processing/process_chirps.py
- modules/processing/process_ndvi.py
- reporting/business_metrics.py

## Future Enhancements

### Phase 2 Features

1. **Regional Variation:**
   - Different thresholds by geographic zone
   - Coastal vs highland vs lowland calibration

2. **Machine Learning Integration:**
   - Use ML to predict optimal thresholds
   - Adaptive thresholds based on climate trends

3. **Real-time Monitoring:**
   - Dashboard for trigger rate monitoring
   - Automated alerts for anomalies

4. **Climate Change Adjustment:**
   - Trend analysis for threshold drift
   - Automatic recalibration recommendations

## References

- WMO Standardized Precipitation Index User Guide
- FAO Vegetation Condition Index methodology
- Tanzania Meteorological Authority climate data
- Parametric insurance best practices (World Bank)
- Historical flood/drought event databases for Tanzania
