# Trigger Configuration Update Guide

**Version:** 1.0.0  
**Last Updated:** November 2024

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration File Structure](#configuration-file-structure)
3. [How to Update Thresholds](#how-to-update-thresholds)
4. [Validation Process](#validation-process)
5. [Examples](#examples)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This guide explains how to update trigger thresholds in the Tanzania Climate Prediction system. The configuration file (`configs/trigger_thresholds.yaml`) controls all insurance trigger behavior without requiring code changes.

### When to Update Thresholds

- **Annual Recalibration:** Update yearly with new historical data
- **Trigger Rate Drift:** When monthly monitoring shows rates outside target ranges
- **Climate Change Adjustment:** When long-term trends indicate threshold shifts
- **Regional Expansion:** When adding new geographic regions

### Prerequisites

- Access to `configs/trigger_thresholds.yaml`
- Understanding of trigger calibration methodology (see `TRIGGER_CALIBRATION.md`)
- Historical climate data for validation
- Python environment with required packages

---

## Configuration File Structure

### Location

```
configs/trigger_thresholds.yaml
```

### Top-Level Structure

```yaml
version: "1.0.0"                    # Configuration version
calibration_date: "2024-11-17"      # Date of last calibration
data_period: "2018-01-01 to 2023-12-31"  # Historical data period used

target_trigger_rates:               # Target activation rates
  flood: 0.10                       # 10% of months
  drought: 0.12                     # 12% of months
  crop_failure: 0.06                # 6% of months

flood_triggers: { ... }             # Flood threshold configuration
drought_triggers: { ... }           # Drought threshold configuration
crop_failure_triggers: { ... }      # Crop failure threshold configuration
regional_adjustments: { ... }       # Regional variations (Phase 2)
```

### Threshold Entry Structure

Each threshold follows this pattern:

```yaml
threshold_name:
  threshold: <numeric_value>        # The actual threshold value
  rationale: "<explanation>"        # Why this value was chosen
  data_source: "<source>"           # Where the data came from
  calibration_date: "<date>"        # When it was last calibrated (optional)
```

---

## How to Update Thresholds

### Step 1: Backup Current Configuration

```bash
# Create backup with timestamp
cp configs/trigger_thresholds.yaml configs/trigger_thresholds_backup_$(date +%Y%m%d).yaml
```

### Step 2: Update Version and Metadata

```yaml
version: "1.1.0"  # Increment version
calibration_date: "2024-12-01"  # Update to current date
data_period: "2018-01-01 to 2024-11-30"  # Update data period
```

### Step 3: Modify Threshold Values

#### Example: Adjusting Flood Trigger

**Current Configuration:**
```yaml
flood_triggers:
  daily_rainfall_mm:
    threshold: 150
    rationale: "Based on historical flood events in Tanzania"
    data_source: "CHIRPS 2018-2023"
```

**Updated Configuration:**
```yaml
flood_triggers:
  daily_rainfall_mm:
    threshold: 145  # Reduced to increase sensitivity
    rationale: "Adjusted based on 2024 flood events and updated percentile analysis"
    data_source: "CHIRPS 2018-2024"
    calibration_date: "2024-12-01"
```

### Step 4: Document Changes

Add a comment block at the top of the file:

```yaml
# CHANGE LOG
# 2024-12-01: Reduced daily rainfall threshold from 150mm to 145mm
#             Reason: Flood trigger rate was 4.2%, below 5% target
#             Expected impact: Increase flood trigger rate to ~6%
```

### Step 5: Validate Configuration

```bash
# Run validation script
python -c "from modules.calibration.config_loader import validate_trigger_config; \
           import yaml; \
           config = yaml.safe_load(open('configs/trigger_thresholds.yaml')); \
           is_valid, errors = validate_trigger_config(config); \
           print('Valid!' if is_valid else f'Errors: {errors}')"
```

### Step 6: Test with Historical Data

```bash
# Reprocess sample data with new thresholds
python modules/processing/process_chirps.py --config configs/trigger_thresholds.yaml \
                                            --input outputs/processed/chirps_processed.csv \
                                            --output outputs/test/chirps_test.csv

# Check trigger rates
python -c "import pandas as pd; \
           df = pd.read_csv('outputs/test/chirps_test.csv'); \
           print(f'Flood rate: {df[\"flood_trigger\"].mean()*100:.2f}%')"
```

### Step 7: Generate Validation Report

```bash
# Compare old vs new trigger rates
python reporting/trigger_validation_report.py \
       --old-data outputs/processed/master_dataset.csv \
       --new-data outputs/test/master_dataset_new.csv \
       --output outputs/validation_reports/
```

### Step 8: Deploy to Production

```bash
# If validation passes, deploy new configuration
git add configs/trigger_thresholds.yaml
git commit -m "Update trigger thresholds - v1.1.0"
git push origin main
```

---

## Validation Process

### Automated Validation Checks

The system automatically validates:

1. **Required Fields:** All mandatory fields present
2. **Value Ranges:** Thresholds within reasonable bounds
3. **Data Types:** Numeric values are numbers, strings are strings
4. **Rationale:** Each threshold has documented justification

### Manual Validation Steps

1. **Trigger Rate Check**
   - Verify rates are within target ranges
   - Flood: 5-15%, Drought: 8-20%, Crop Failure: 3-10%

2. **Seasonal Alignment**
   - Flood triggers concentrate in rainy seasons (>70%)
   - Drought triggers concentrate in dry season (>60%)

3. **Financial Sustainability**
   - Loss ratio < 80%
   - Annual payout < $2,000 per entity

4. **Historical Event Alignment**
   - ≥70% of known extreme events trigger the system
   - <20% false positive rate

---

## Examples

### Example 1: Increase Flood Sensitivity

**Problem:** Flood trigger rate is 4%, below 5% target

**Solution:** Reduce thresholds to increase sensitivity

```yaml
# BEFORE
flood_triggers:
  daily_rainfall_mm:
    threshold: 150
  rainfall_7day_mm:
    threshold: 250

# AFTER
flood_triggers:
  daily_rainfall_mm:
    threshold: 140  # Reduced by 10mm
    rationale: "Increased sensitivity to capture more flood events"
    data_source: "CHIRPS 2018-2024"
    calibration_date: "2024-12-01"
  rainfall_7day_mm:
    threshold: 230  # Reduced by 20mm
    rationale: "Adjusted to align with updated daily threshold"
    data_source: "CHIRPS 2018-2024"
    calibration_date: "2024-12-01"
```

**Expected Impact:** Flood rate increases to ~6-7%

### Example 2: Reduce Drought False Positives

**Problem:** Drought trigger rate is 22%, above 20% target

**Solution:** Make drought criteria more stringent

```yaml
# BEFORE
drought_triggers:
  spi_30day:
    threshold: -1.5
  consecutive_dry_days:
    wet_season_threshold: 35
    dry_season_threshold: 45

# AFTER
drought_triggers:
  spi_30day:
    threshold: -1.7  # More stringent (more negative)
    rationale: "Reduced false positives by requiring more severe SPI"
    data_source: "CHIRPS 2018-2024"
    calibration_date: "2024-12-01"
  consecutive_dry_days:
    wet_season_threshold: 40  # Increased from 35
    dry_season_threshold: 50  # Increased from 45
    rationale: "Longer dry periods required to trigger"
    data_source: "CHIRPS 2018-2024"
    calibration_date: "2024-12-01"
```

**Expected Impact:** Drought rate decreases to ~18%

### Example 3: Activate Crop Failure Triggers

**Problem:** Crop failure trigger rate is 0%, below 3% target

**Solution:** Relax VCI and NDVI thresholds

```yaml
# BEFORE
crop_failure_triggers:
  vci_threshold:
    critical: 20
    duration_days: 30
  ndvi_anomaly_std:
    threshold: -2.0
    duration_days: 21

# AFTER
crop_failure_triggers:
  vci_threshold:
    critical: 25  # Increased from 20 (less stringent)
    duration_days: 25  # Reduced from 30
    rationale: "Relaxed to capture moderate crop stress events"
    data_source: "MODIS NDVI 2018-2024"
    calibration_date: "2024-12-01"
  ndvi_anomaly_std:
    threshold: -1.5  # Increased from -2.0 (less stringent)
    duration_days: 18  # Reduced from 21
    rationale: "Adjusted to detect earlier crop stress"
    data_source: "MODIS NDVI 2018-2024"
    calibration_date: "2024-12-01"
```

**Expected Impact:** Crop failure rate increases to ~4-5%

### Example 4: Seasonal Adjustment

**Problem:** Drought triggers occurring too frequently in wet season

**Solution:** Adjust seasonal thresholds

```yaml
# BEFORE
drought_triggers:
  consecutive_dry_days:
    wet_season_threshold: 35
    dry_season_threshold: 45

# AFTER
drought_triggers:
  consecutive_dry_days:
    wet_season_threshold: 42  # Increased for wet season
    dry_season_threshold: 45  # Kept same for dry season
    rationale: "Wet season droughts require longer dry periods"
    data_source: "CHIRPS 2018-2024 seasonal analysis"
    calibration_date: "2024-12-01"
```

**Expected Impact:** Fewer drought triggers in wet season, better seasonal alignment

---

## Troubleshooting

### Issue 1: Configuration File Not Loading

**Symptoms:**
```
ERROR: Failed to load trigger configuration
FileNotFoundError: configs/trigger_thresholds.yaml
```

**Solutions:**
1. Check file path is correct
2. Verify file exists: `ls -la configs/trigger_thresholds.yaml`
3. Check file permissions: `chmod 644 configs/trigger_thresholds.yaml`

### Issue 2: YAML Syntax Error

**Symptoms:**
```
ERROR: Invalid YAML syntax
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Solutions:**
1. Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('configs/trigger_thresholds.yaml'))"`
2. Check indentation (use spaces, not tabs)
3. Ensure colons have space after them: `threshold: 150` not `threshold:150`
4. Quote strings with special characters

### Issue 3: Validation Errors

**Symptoms:**
```
ERROR: Configuration validation failed
Missing required field: rationale
```

**Solutions:**
1. Ensure all required fields present:
   - `threshold`
   - `rationale`
   - `data_source`
2. Check threshold values are numeric
3. Verify rationale is a non-empty string

### Issue 4: Trigger Rates Not Changing

**Symptoms:**
- Updated configuration but trigger rates unchanged

**Solutions:**
1. Verify configuration is being loaded:
   ```python
   from modules.calibration.config_loader import load_trigger_config
   config = load_trigger_config()
   print(config['flood_triggers']['daily_rainfall_mm']['threshold'])
   ```
2. Clear any cached configurations
3. Restart processing pipeline
4. Check logs for configuration loading messages

### Issue 5: Unexpected Trigger Rates

**Symptoms:**
- Trigger rates far from expected values after threshold change

**Solutions:**
1. Verify threshold change direction:
   - Lower threshold = more triggers (higher rate)
   - Higher threshold = fewer triggers (lower rate)
2. Check data quality:
   ```python
   import pandas as pd
   df = pd.read_csv('outputs/processed/chirps_processed.csv')
   print(df['rainfall_mm'].describe())
   ```
3. Validate against historical percentiles
4. Review trigger logic (AND vs OR conditions)

### Issue 6: Seasonal Logic Not Working

**Symptoms:**
- Seasonal thresholds not being applied correctly

**Solutions:**
1. Verify month mapping:
   ```python
   # Wet season: Oct-May (months 10, 11, 12, 1, 2, 3, 4, 5)
   # Dry season: Jun-Sep (months 6, 7, 8, 9)
   ```
2. Check date column format
3. Ensure season_type column is created correctly

---

## Best Practices

### 1. Version Control

- Always commit configuration changes to git
- Use descriptive commit messages
- Tag releases: `git tag v1.1.0`

### 2. Documentation

- Document rationale for every change
- Include expected impact
- Reference data sources and dates

### 3. Testing

- Test on historical data before production
- Generate validation reports
- Review with stakeholders

### 4. Monitoring

- Track trigger rates monthly
- Set up alerts for rates outside target ranges
- Review quarterly for trends

### 5. Backup

- Keep backups of all configuration versions
- Store in separate location
- Document rollback procedure

---

## Configuration Change Checklist

Before deploying configuration changes:

- [ ] Backup current configuration
- [ ] Update version number
- [ ] Update calibration date
- [ ] Document rationale for all changes
- [ ] Validate YAML syntax
- [ ] Run automated validation checks
- [ ] Test with historical data
- [ ] Generate validation report
- [ ] Review trigger rates
- [ ] Check seasonal alignment
- [ ] Verify financial sustainability
- [ ] Get stakeholder approval
- [ ] Commit to version control
- [ ] Deploy to production
- [ ] Monitor for 1 week
- [ ] Document lessons learned

---

## Support

For questions or issues with trigger configuration:

1. Review this guide and `TRIGGER_CALIBRATION.md`
2. Check troubleshooting section
3. Review validation reports
4. Contact Tanzania Climate Prediction Team

---

## Appendix: Quick Reference

### Threshold Adjustment Rules

| To Increase Trigger Rate | To Decrease Trigger Rate |
|--------------------------|--------------------------|
| Lower threshold values | Raise threshold values |
| Change AND to OR | Change OR to AND |
| Reduce duration requirements | Increase duration requirements |
| Relax percentile cutoffs | Tighten percentile cutoffs |

### Target Ranges Quick Reference

| Trigger | Min | Target | Max | Action if Outside |
|---------|-----|--------|-----|-------------------|
| Flood | 5% | 10% | 15% | Adjust rainfall thresholds |
| Drought | 8% | 12% | 20% | Adjust SPI or dry days |
| Crop Failure | 3% | 6% | 10% | Adjust VCI or NDVI |

### Common Threshold Values

| Indicator | Typical Range | Current Value |
|-----------|---------------|---------------|
| Daily Rainfall | 100-200mm | 150mm |
| 7-day Rainfall | 200-300mm | 250mm |
| SPI-30 | -1.0 to -2.0 | -1.5 |
| Dry Days (Wet) | 30-40 days | 35 days |
| Dry Days (Dry) | 40-50 days | 45 days |
| VCI Critical | 15-25 | 20 |
| NDVI Anomaly | -1.5 to -2.5σ | -2.0σ |

---

**Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Nov 2024 | Initial configuration guide |
