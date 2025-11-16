# Business Reports Guide

## Overview

The business reporting system transforms technical ML outputs into actionable business insights for insurance companies, farmers, and stakeholders.

## Quick Start

Generate all business reports with one command:

```bash
python generate_business_reports.py
```

Reports will be saved to: `outputs/business_reports/`

## What Gets Generated

### 📄 Reports (CSV/JSON/Markdown)

1. **executive_summary.md** - Executive overview with key metrics
2. **insurance_triggers_detailed.csv** - Complete trigger event log
3. **alert_timeline.csv** - Actionable alerts with recommendations
4. **payout_estimates.csv** - Financial impact per event
5. **payout_summary_by_year.csv** - Annual financial summary
6. **risk_dashboard.json** - API-ready metrics

### 📊 Visualizations (PNG)

1. **trigger_timeline.png** - Trigger events over time
2. **financial_impact.png** - Payouts and events by year
3. **alert_distribution.png** - Alert types and severity breakdown
4. **risk_heatmap.png** - Monthly risk patterns

## Key Business Metrics

### Insurance Triggers

The system tracks multiple trigger types:

- **Drought Triggers**: Low rainfall periods
- **Flood Triggers**: Extreme rainfall events
- **Crop Failure Triggers**: Vegetation stress indicators
- **Climate Triggers**: ENSO/IOD-based predictions

Each trigger includes:
- Activation date
- Confidence score (reliability)
- Severity level (for payout calculation)

### Financial Impact

Payout estimates are calculated using:

```
Payout = Base_Rate × (0.5 + Severity) × Confidence
```

Default rates (customizable):
- Drought: $500 per event
- Flood: $750 per event
- Crop Failure: $1,000 per event
- Severe Stress: $300 per event

### Risk Assessment

Overall risk is classified as:

- 🟢 **LOW RISK**: <20% of months with triggers
- 🟡 **MODERATE RISK**: 20-40% of months with triggers
- 🔴 **HIGH RISK**: >40% of months with triggers

## Use Cases

### For Insurance Companies

**Premium Pricing:**
```bash
# Review yearly payout trends
cat outputs/business_reports/payout_summary_by_year.csv
```

**Risk Assessment:**
```bash
# Check current risk level
cat outputs/business_reports/risk_dashboard.json
```

**Claims Processing:**
```bash
# Verify trigger events
cat outputs/business_reports/insurance_triggers_detailed.csv
```

### For Farmers & Cooperatives

**Early Warnings:**
- Check `alert_timeline.csv` for upcoming risks
- Follow recommended actions for each alert type
- Plan seasonal activities based on risk patterns

**Insurance Claims:**
- Track trigger history in `insurance_triggers_detailed.csv`
- Verify payout eligibility
- Document crop damage during trigger events

### For Developers

**API Integration:**
```python
import json

# Load risk metrics
with open('outputs/business_reports/risk_dashboard.json') as f:
    metrics = json.load(f)

print(f"Total triggers: {metrics['total_trigger_events']}")
print(f"Risk level: {metrics['avg_severity']}")
```

**Dashboard Creation:**
- Use PNG visualizations in web dashboards
- Parse CSV files for custom charts
- Monitor `risk_dashboard.json` for real-time updates

## Customization

### Adjust Payout Rates

Edit `reporting/business_metrics.py`:

```python
PAYOUT_RATES = {
    'drought_trigger': 500,  # Change to your rate
    'flood_trigger': 750,
    'crop_failure_trigger': 1000,
    'severe_stress_trigger': 300
}
```

### Add Custom Triggers

1. Ensure your data includes the new trigger column
2. Add to `PAYOUT_RATES` dictionary
3. Regenerate reports

### Change Risk Thresholds

Edit `_assess_overall_risk()` method in `business_metrics.py`:

```python
if trigger_rate >= 0.4:  # Change threshold
    return "🔴 HIGH RISK"
```

## Automation

### Daily Report Generation

Create a scheduled task (Windows) or cron job (Linux):

```bash
# Run daily at 6 AM
0 6 * * * cd /path/to/project && python generate_business_reports.py
```

### Email Alerts

Integrate with email service:

```python
from reporting.business_metrics import BusinessMetricsReporter
import smtplib

# Generate reports
reporter = BusinessMetricsReporter()
reports = reporter.generate_full_report('data.csv')

# Send email if high risk
with open('outputs/business_reports/risk_dashboard.json') as f:
    risk = json.load(f)
    
if risk['total_trigger_events'] > threshold:
    send_alert_email(risk)
```

## Troubleshooting

### No Trigger Columns Found

**Problem:** Dataset doesn't contain trigger columns

**Solution:** Run the full data pipeline first:
```bash
python run_pipeline.py
```

### Empty Reports

**Problem:** No trigger events in data

**Solution:** Check date range and trigger thresholds in processing modules

### Visualization Errors

**Problem:** Missing matplotlib or seaborn

**Solution:** Install dependencies:
```bash
pip install matplotlib seaborn
```

## Report Interpretation

### Executive Summary

**Key sections:**
- **Key Metrics**: Overall statistics
- **Alert Summary**: Breakdown by trigger type
- **Financial Impact**: Payout estimates
- **Risk Assessment**: Current risk level
- **Recommendations**: Actionable next steps

### Alert Timeline

**Severity levels:**
- **HIGH**: Confidence ≥ 70% - Immediate action required
- **MEDIUM**: Confidence 40-69% - Monitor closely
- **LOW**: Confidence < 40% - Awareness only

**Recommended actions:**
- Drought: Monitor water resources, prepare irrigation
- Flood: Prepare drainage, protect crops
- Crop Failure: Assess damage, initiate claims

### Financial Reports

**Payout estimates include:**
- Base rate for trigger type
- Severity multiplier (0.5 to 1.5)
- Confidence adjustment
- Combined trigger effects

**Note:** Estimates are for planning purposes. Actual payouts depend on policy terms.

## Best Practices

1. **Regular Updates**: Regenerate reports after new predictions
2. **Version Control**: Archive reports with timestamps
3. **Validation**: Cross-check with actual weather events
4. **Communication**: Share executive summary with stakeholders
5. **Action Plans**: Develop response protocols for each alert type

## Integration Examples

### Power BI / Tableau

Import CSV files directly:
1. Open Power BI / Tableau
2. Import `payout_summary_by_year.csv`
3. Create visualizations from columns
4. Refresh data source after regenerating reports

### Excel

1. Open Excel
2. Data → From Text/CSV
3. Select any CSV report
4. Create pivot tables and charts

### Python Analysis

```python
import pandas as pd

# Load reports
triggers = pd.read_csv('outputs/business_reports/insurance_triggers_detailed.csv')
payouts = pd.read_csv('outputs/business_reports/payout_estimates.csv')

# Custom analysis
monthly_avg = payouts.groupby('date')['estimated_payout_usd'].mean()
print(f"Average monthly payout: ${monthly_avg.mean():.2f}")
```

## Support

For questions or issues:
1. Check `outputs/business_reports/README.md`
2. Review data pipeline documentation
3. Verify input data contains required trigger columns

---

**Last Updated:** 2025-11-17
**Version:** 1.0
