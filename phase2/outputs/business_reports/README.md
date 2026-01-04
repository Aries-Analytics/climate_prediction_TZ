# Business Metrics Reports

This directory contains business-focused reports generated from climate predictions and insurance trigger data.

## 📊 Available Reports

### 1. Executive Summary (`executive_summary.md`)
**Audience:** Executives, stakeholders, decision-makers

High-level overview including:
- Total insurance triggers and financial impact
- Risk assessment by event type (drought, flood, crop failure)
- Key recommendations for risk management
- Overall risk level classification

**Format:** Markdown (human-readable)

---

### 2. Insurance Triggers Detailed (`insurance_triggers_detailed.csv`)
**Audience:** Insurance analysts, risk managers

Complete chronological list of all insurance trigger events with:
- Date of trigger activation
- Trigger type (drought, flood, crop failure, etc.)
- Confidence score (reliability of trigger)
- Severity level (for payout calculation)

**Format:** CSV (Excel-compatible)

**Use cases:**
- Audit trail for insurance payouts
- Historical trigger analysis
- Compliance reporting

---

### 3. Alert Timeline (`alert_timeline.csv`)
**Audience:** Operations teams, farmers, field agents

Actionable alerts with recommended responses:
- Alert type and severity classification
- Confidence scores
- Recommended actions for each alert type

**Format:** CSV (Excel-compatible)

**Use cases:**
- Early warning system
- Field operations planning
- Farmer notifications

---

### 4. Payout Estimates (`payout_estimates.csv`)
**Audience:** Finance teams, insurance underwriters

Detailed financial impact analysis:
- Estimated payout per trigger event
- Severity multipliers applied
- Confidence-adjusted calculations
- Triggered event combinations

**Format:** CSV (Excel-compatible)

**Use cases:**
- Budget planning
- Reserve calculations
- Premium pricing adjustments

---

### 5. Payout Summary by Year (`payout_summary_by_year.csv`)
**Audience:** Finance teams, executives

Annual financial summary:
- Total estimated payouts per year
- Number of trigger events per year
- Year-over-year trends

**Format:** CSV (Excel-compatible)

**Use cases:**
- Annual reporting
- Trend analysis
- Multi-year planning

---

### 6. Risk Dashboard (`risk_dashboard.json`)
**Audience:** Developers, dashboard applications

Machine-readable metrics for integration:
- Total trigger counts by type
- Average confidence scores
- Risk level indicators
- Date ranges and coverage

**Format:** JSON (API-compatible)

**Use cases:**
- Web dashboards
- Mobile applications
- API integrations
- Automated monitoring

---

## 🔄 Regenerating Reports

To regenerate all reports with updated data:

```bash
python generate_business_reports.py
```

With custom data source:

```bash
python generate_business_reports.py --data path/to/your/data.csv
```

With custom output directory:

```bash
python generate_business_reports.py --output path/to/output/
```

---

## 💡 Understanding the Metrics

### Trigger Types

- **Drought Trigger:** Activated when rainfall falls below critical thresholds
- **Flood Trigger:** Activated during extreme rainfall events
- **Crop Failure Trigger:** Activated when vegetation health (NDVI) indicates crop stress
- **Climate Triggers:** Based on ocean indices (ENSO, IOD) predicting climate anomalies

### Confidence Scores

- **High (70-100%):** Strong evidence, high reliability
- **Medium (40-69%):** Moderate evidence, reasonable confidence
- **Low (0-39%):** Weak evidence, use with caution

### Severity Levels

- **0.0-0.3:** Minor impact, low payout multiplier
- **0.3-0.6:** Moderate impact, standard payout
- **0.6-1.0:** Severe impact, high payout multiplier

### Risk Levels

- **🟢 LOW RISK:** <20% of months with triggers
- **🟡 MODERATE RISK:** 20-40% of months with triggers
- **🔴 HIGH RISK:** >40% of months with triggers

---

## 💰 Financial Model Clarifications

### Understanding Payout Figures

**IMPORTANT:** All payout figures in these reports are calculated **per insured entity** unless explicitly stated as "portfolio total" or "aggregate."

**Per-Entity Basis:**
- Annual premium: $2,400 USD
- Expected annual payout: $1,300-$1,900 USD
- Loss ratio: 54-79% (sustainable)

**Portfolio Basis (example with 417 entities):**
- Total annual premiums: $1,000,000 USD
- Expected total payouts: $542,000-$792,000 USD
- Portfolio loss ratio: 54-79% (sustainable)

### Reinsurance Structure

The system includes reinsurance protection for catastrophic losses:

- **Primary Retention:** $1,000,000 (primary insurer pays first $1M)
- **Reinsurance Layer:** $1M - $10M (reinsurer covers excess)
- **Total Capacity:** $11,000,000 (primary + reinsurance)

**Note:** The "$10M reinsurance capacity" is the maximum coverage available, NOT the expected annual payout. Expected payouts are $542k-$792k/year, well below the $1M retention threshold.

### Financial Sustainability

The product is financially sustainable because:
- Loss ratio: 54-79% (target: <80%)
- Expected payouts are 54-79% of premium income
- Remaining 21-46% covers admin costs, profit, and reserves
- Reinsurance protects against catastrophic scenarios

**For detailed financial model documentation, see:** `docs/FINANCIAL_MODEL.md`

---

## 📈 Using the Reports

### For Insurance Companies

1. Review `payout_estimates.csv` for reserve planning
2. Use `payout_summary_by_year.csv` for premium adjustments
3. Monitor `risk_dashboard.json` for real-time risk assessment
4. Share `executive_summary.md` with stakeholders

### For Farmers & Cooperatives

1. Check `alert_timeline.csv` for upcoming risks
2. Follow recommended actions for each alert
3. Track trigger history in `insurance_triggers_detailed.csv`
4. Plan seasonal activities based on risk patterns

### For Developers

1. Integrate `risk_dashboard.json` into applications
2. Build automated alerts from `alert_timeline.csv`
3. Create visualizations from CSV data
4. Set up monitoring based on confidence thresholds

---

## 🔧 Customization

### Adjusting Payout Rates

Edit `reporting/business_metrics.py` and modify the `PAYOUT_RATES` dictionary:

```python
PAYOUT_RATES = {
    'drought_trigger': 500,  # USD per event
    'flood_trigger': 750,
    'crop_failure_trigger': 1000,
    'severe_stress_trigger': 300
}
```

### Adding New Trigger Types

1. Ensure your data includes the new trigger column
2. Add the trigger to `PAYOUT_RATES` in `business_metrics.py`
3. Regenerate reports

---

## 📞 Support

For questions or issues with business reports:
1. Check the main project README
2. Review the data pipeline documentation
3. Verify input data contains required trigger columns

---

**Last Updated:** 2025-11-17
**Report Version:** 1.0
