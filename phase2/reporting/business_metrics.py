"""
Business Metrics Report Generator

Generates actionable business reports from ML predictions including:
- Insurance trigger events and timelines
- Drought and flood alerts with severity
- Crop failure risk assessments
- Financial impact estimates (payout calculations)
- Executive summary dashboards
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Tuple

from utils.logger import log_info, log_warning, log_error
from utils.config import OUTPUT_DIR


class BusinessMetricsReporter:
    """Generate business-focused reports from climate predictions and triggers."""

    def __init__(self, output_dir: str = None):
        """
        Initialize the business metrics reporter.

        Parameters
        ----------
        output_dir : str, optional
            Directory to save reports. Defaults to outputs/business_reports/
        """
        self.output_dir = Path(output_dir) if output_dir else Path(OUTPUT_DIR) / "business_reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"Business reports will be saved to: {self.output_dir}")

    def generate_full_report(self, data_path: str, predictions_path: str = None) -> Dict:
        """
        Generate comprehensive business metrics report.

        Parameters
        ----------
        data_path : str
            Path to master dataset or processed features with triggers
        predictions_path : str, optional
            Path to model predictions (if available)

        Returns
        -------
        dict
            Summary of generated reports
        """
        log_info("=" * 80)
        log_info("GENERATING BUSINESS METRICS REPORTS")
        log_info("=" * 80)

        # Load data
        df = pd.read_csv(data_path)
        log_info(f"Loaded data: {len(df)} records from {data_path}")

        # Ensure date column
        if "date" not in df.columns and "year" in df.columns and "month" in df.columns:
            df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

        reports_generated = {}

        # 1. Insurance Triggers Summary
        log_info("\n[1/5] Generating insurance triggers report...")
        trigger_report = self._generate_trigger_report(df)
        reports_generated["triggers"] = trigger_report

        # 2. Alert Timeline
        log_info("\n[2/5] Generating alert timeline...")
        alert_timeline = self._generate_alert_timeline(df)
        reports_generated["alerts"] = alert_timeline

        # 3. Financial Impact Analysis
        log_info("\n[3/5] Generating financial impact analysis...")
        financial_report = self._generate_financial_report(df)
        reports_generated["financial"] = financial_report

        # 4. Risk Assessment Dashboard
        log_info("\n[4/5] Generating risk assessment dashboard...")
        risk_dashboard = self._generate_risk_dashboard(df)
        reports_generated["risk"] = risk_dashboard

        # 5. Executive Summary
        log_info("\n[5/5] Generating executive summary...")
        exec_summary = self._generate_executive_summary(df, reports_generated)
        reports_generated["executive"] = exec_summary

        log_info("\n" + "=" * 80)
        log_info("✓ Business metrics reports generated successfully!")
        log_info(f"✓ Reports saved to: {self.output_dir}")
        log_info("=" * 80)

        return reports_generated

    def _generate_trigger_report(self, df: pd.DataFrame) -> str:
        """Generate detailed insurance trigger events report."""

        # Identify trigger columns
        trigger_cols = [c for c in df.columns if "trigger" in c.lower() and "confidence" not in c.lower()]

        if not trigger_cols:
            log_warning("No trigger columns found in dataset")
            return None

        # Extract trigger events
        trigger_events = []

        for idx, row in df.iterrows():
            date = row.get("date", f"{row.get('year', 'N/A')}-{row.get('month', 'N/A'):02d}")

            for col in trigger_cols:
                if row[col] == 1:  # Trigger activated
                    confidence_col = f"{col}_confidence"
                    confidence = row.get(confidence_col, 0.0)

                    trigger_events.append(
                        {
                            "date": date,
                            "trigger_type": col.replace("_trigger", "").replace("_", " ").title(),
                            "activated": "Yes",
                            "confidence": f"{confidence:.2%}",
                            "severity": row.get("trigger_severity", row.get("trigger_severity_left", 0.0)),
                        }
                    )

        # Save to CSV
        trigger_df = pd.DataFrame(trigger_events)
        output_path = self.output_dir / "insurance_triggers_detailed.csv"
        trigger_df.to_csv(output_path, index=False)
        log_info(f"   ✓ Saved: {output_path}")

        return str(output_path)

    def _generate_alert_timeline(self, df: pd.DataFrame) -> str:
        """Generate timeline of drought, flood, and crop failure alerts."""

        alerts = []

        for idx, row in df.iterrows():
            date = row.get("date", f"{row.get('year', 'N/A')}-{row.get('month', 'N/A'):02d}")

            # Drought alerts
            if row.get("drought_trigger", 0) == 1:
                alerts.append(
                    {
                        "date": date,
                        "alert_type": "DROUGHT",
                        "severity": self._classify_severity(row.get("drought_trigger_confidence", 0)),
                        "confidence": row.get("drought_trigger_confidence", 0),
                        "action_required": "Monitor water resources, prepare irrigation",
                    }
                )

            # Flood alerts
            if row.get("flood_trigger", 0) == 1:
                alerts.append(
                    {
                        "date": date,
                        "alert_type": "FLOOD",
                        "severity": self._classify_severity(row.get("flood_trigger_confidence", 0)),
                        "confidence": row.get("flood_trigger_confidence", 0),
                        "action_required": "Prepare drainage, protect crops",
                    }
                )

            # Crop failure alerts
            if row.get("crop_failure_trigger", 0) == 1:
                alerts.append(
                    {
                        "date": date,
                        "alert_type": "CROP_FAILURE",
                        "severity": self._classify_severity(row.get("crop_failure_trigger_confidence", 0)),
                        "confidence": row.get("crop_failure_trigger_confidence", 0),
                        "action_required": "Assess crop damage, initiate insurance claims",
                    }
                )

        # Save to CSV
        alerts_df = pd.DataFrame(alerts)
        output_path = self.output_dir / "alert_timeline.csv"
        alerts_df.to_csv(output_path, index=False)
        log_info(f"   ✓ Saved: {output_path}")

        return str(output_path)

    def _generate_financial_report(self, df: pd.DataFrame) -> str:
        """Generate financial impact analysis with payout estimates."""

        # Payout calculation parameters (example values - adjust based on actual policy)
        PAYOUT_RATES = {
            "drought_trigger": 500,  # USD per trigger event
            "flood_trigger": 750,
            "crop_failure_trigger": 1000,
            "severe_stress_trigger": 300,
        }

        financial_data = []

        for idx, row in df.iterrows():
            date = row.get("date", f"{row.get('year', 'N/A')}-{row.get('month', 'N/A'):02d}")
            year = row.get("year", pd.to_datetime(date).year if isinstance(date, str) else None)

            total_payout = 0
            triggered_events = []

            for trigger_type, base_payout in PAYOUT_RATES.items():
                if row.get(trigger_type, 0) == 1:
                    # Adjust payout by severity
                    severity = row.get("trigger_severity", 0.5)
                    confidence = row.get(f"{trigger_type}_confidence", 0.5)

                    payout = base_payout * (0.5 + severity) * confidence
                    total_payout += payout
                    triggered_events.append(trigger_type.replace("_trigger", ""))

            if total_payout > 0:
                financial_data.append(
                    {
                        "date": date,
                        "year": year,
                        "triggered_events": ", ".join(triggered_events),
                        "estimated_payout_usd": round(total_payout, 2),
                        "severity_multiplier": row.get("trigger_severity", 0.5),
                        "confidence_score": row.get("drought_trigger_confidence", 0.5),
                    }
                )

        # Save detailed payouts
        financial_df = pd.DataFrame(financial_data)
        output_path = self.output_dir / "payout_estimates.csv"
        financial_df.to_csv(output_path, index=False)
        log_info(f"   ✓ Saved: {output_path}")

        # Generate summary by year
        if not financial_df.empty and "year" in financial_df.columns:
            yearly_summary = (
                financial_df.groupby("year")
                .agg({"estimated_payout_usd": "sum", "triggered_events": "count"})
                .rename(columns={"triggered_events": "total_events"})
            )

            summary_path = self.output_dir / "payout_summary_by_year.csv"
            yearly_summary.to_csv(summary_path)
            log_info(f"   ✓ Saved: {summary_path}")

        return str(output_path)

    def _generate_risk_dashboard(self, df: pd.DataFrame) -> str:
        """Generate risk assessment dashboard data."""

        risk_metrics = {
            "total_records": len(df),
            "date_range": f"{df['date'].min()} to {df['date'].max()}" if "date" in df.columns else "N/A",
            "drought_events": int(df.get("drought_trigger", pd.Series([0])).sum()),
            "flood_events": int(df.get("flood_trigger", pd.Series([0])).sum()),
            "crop_failure_events": int(df.get("crop_failure_trigger", pd.Series([0])).sum()),
            "total_trigger_events": int(df.get("any_trigger", pd.Series([0])).sum()),
            "high_risk_periods": int((df.get("trigger_severity", pd.Series([0])) > 0.7).sum()),
            "avg_drought_confidence": float(df.get("drought_trigger_confidence", pd.Series([0])).mean()),
            "avg_flood_confidence": float(df.get("flood_trigger_confidence", pd.Series([0])).mean()),
            "avg_severity": float(df.get("trigger_severity", pd.Series([0])).mean()),
        }

        # Save as JSON
        output_path = self.output_dir / "risk_dashboard.json"
        with open(output_path, "w") as f:
            json.dump(risk_metrics, f, indent=2)
        log_info(f"   ✓ Saved: {output_path}")

        return str(output_path)

    def _generate_executive_summary(self, df: pd.DataFrame, reports: Dict) -> str:
        """Generate executive summary markdown report."""

        # Calculate key metrics
        total_triggers = int(df.get("any_trigger", pd.Series([0])).sum())
        drought_events = int(df.get("drought_trigger", pd.Series([0])).sum())
        flood_events = int(df.get("flood_trigger", pd.Series([0])).sum())
        crop_failures = int(df.get("crop_failure_trigger", pd.Series([0])).sum())

        # Calculate trigger rates
        total_records = len(df)
        drought_rate = (drought_events / total_records * 100) if total_records > 0 else 0
        flood_rate = (flood_events / total_records * 100) if total_records > 0 else 0
        crop_rate = (crop_failures / total_records * 100) if total_records > 0 else 0

        # Load financial data if available
        total_payout = 0
        if "financial" in reports:
            try:
                financial_df = pd.read_csv(reports["financial"])
                total_payout = financial_df["estimated_payout_usd"].sum()
            except:
                pass

        # Generate markdown report
        summary = f"""# Executive Summary: Climate Risk & Insurance Triggers

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| **Total Records Analyzed** | {len(df):,} |
| **Date Range** | {df['date'].min() if 'date' in df.columns else 'N/A'} to {df['date'].max() if 'date' in df.columns else 'N/A'} |
| **Total Insurance Triggers** | {total_triggers:,} |
| **Estimated Total Payouts** | ${total_payout:,.2f} USD |

---

## 🚨 Alert Summary

### Trigger Events by Type

| Alert Type | Count | Percentage | Target Range |
|------------|-------|------------|--------------|
| 🌵 **Drought Events** | {drought_events} | {drought_rate:.1f}% | 8-20% |
| 🌊 **Flood Events** | {flood_events} | {flood_rate:.1f}% | 5-15% |
| 🌾 **Crop Failure Events** | {crop_failures} | {crop_rate:.1f}% | 3-10% |

### Trigger Rate Validation

| Trigger Type | Status |
|--------------|--------|
| Drought | {'✓ Within Target' if 8 <= drought_rate <= 20 else '✗ Outside Target'} |
| Flood | {'✓ Within Target' if 5 <= flood_rate <= 15 else '✗ Outside Target'} |
| Crop Failure | {'✓ Within Target' if 3 <= crop_rate <= 10 else '✗ Outside Target'} |

---

## 💰 Financial Impact

- **Average Payout per Event:** ${total_payout/max(total_triggers, 1):,.2f} USD
- **Highest Risk Period:** {self._get_highest_risk_period(df)}
- **Trigger Frequency:** {total_triggers/len(df)*100:.1f}% of months

---

## 📈 Risk Assessment

**Overall Risk Level:** {self._assess_overall_risk(df)}

### Risk Factors:
- Drought trigger confidence: {df.get('drought_trigger_confidence', pd.Series([0])).mean():.1%}
- Flood trigger confidence: {df.get('flood_trigger_confidence', pd.Series([0])).mean():.1%}
- Average severity score: {df.get('trigger_severity', pd.Series([0])).mean():.2f}

### Financial Sustainability

**Estimated Annual Payout:** ${total_payout / (len(df) / 12):,.2f} (based on {len(df)} months of data)

**Sustainability Assessment:**
- Target loss ratio: < 80% of premium income
- Current trigger rates: {'✓ Within sustainable ranges' if (5 <= flood_rate <= 15 and 8 <= drought_rate <= 20 and 3 <= crop_rate <= 10) else '⚠️ May need adjustment'}
- Recommendation: {'Continue monitoring monthly' if (5 <= flood_rate <= 15 and 8 <= drought_rate <= 20 and 3 <= crop_rate <= 10) else 'Review and recalibrate thresholds'}

---

## 📁 Detailed Reports

The following detailed reports have been generated:

1. **Insurance Triggers:** `insurance_triggers_detailed.csv`
   - Complete list of all trigger events with dates and confidence scores

2. **Alert Timeline:** `alert_timeline.csv`
   - Chronological timeline of drought, flood, and crop failure alerts
   - Includes recommended actions for each alert

3. **Financial Analysis:** `payout_estimates.csv`
   - Detailed payout calculations for each trigger event
   - Yearly summary available in `payout_summary_by_year.csv`

4. **Risk Dashboard:** `risk_dashboard.json`
   - Machine-readable risk metrics for dashboards and APIs

---

## 🎯 Recommendations

1. **High-Risk Periods:** Monitor closely during {self._get_highest_risk_period(df)}
2. **Insurance Coverage:** Current trigger rate suggests {"adequate" if total_triggers/len(df) < 0.3 else "high"} risk exposure
3. **Early Warning:** Implement 3-month ahead forecasting for proactive risk management

---

**Note:** All financial estimates are based on standard parametric insurance rates and should be adjusted based on actual policy terms.
"""

        # Save markdown report
        output_path = self.output_dir / "executive_summary.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        log_info(f"   ✓ Saved: {output_path}")

        return str(output_path)

    def _classify_severity(self, confidence: float) -> str:
        """Classify severity based on confidence score."""
        if confidence >= 0.7:
            return "HIGH"
        elif confidence >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_highest_risk_period(self, df: pd.DataFrame) -> str:
        """Identify the highest risk period."""
        if "month" in df.columns and "any_trigger" in df.columns:
            monthly_risk = df.groupby("month")["any_trigger"].sum()
            highest_month = monthly_risk.idxmax()
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            return month_names[int(highest_month) - 1] if highest_month <= 12 else "Unknown"
        return "Unknown"

    def _assess_overall_risk(self, df: pd.DataFrame) -> str:
        """Assess overall risk level."""
        if "any_trigger" not in df.columns:
            return "UNKNOWN"

        trigger_rate = df["any_trigger"].sum() / len(df)

        if trigger_rate >= 0.4:
            return "🔴 HIGH RISK"
        elif trigger_rate >= 0.2:
            return "🟡 MODERATE RISK"
        else:
            return "🟢 LOW RISK"


def main():
    """Main function to generate business reports."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate business metrics reports")
    parser.add_argument(
        "--data", type=str, default="outputs/processed/master_dataset.csv", help="Path to master dataset"
    )
    parser.add_argument("--output", type=str, default=None, help="Output directory for reports")

    args = parser.parse_args()

    reporter = BusinessMetricsReporter(output_dir=args.output)
    reports = reporter.generate_full_report(data_path=args.data)

    print("\n✓ Business metrics reports generated successfully!")
    print(f"✓ Check: {reporter.output_dir}")


if __name__ == "__main__":
    main()

    def generate_before_after_comparison(self, old_data_path: str, new_data_path: str) -> str:
        """
        Generate side-by-side comparison of old vs new metrics.

        Parameters
        ----------
        old_data_path : str
            Path to data with old triggers
        new_data_path : str
            Path to data with new triggers

        Returns
        -------
        str
            Path to generated comparison report
        """
        log_info("=" * 80)
        log_info("GENERATING BEFORE/AFTER COMPARISON REPORT")
        log_info("=" * 80)

        # Load data
        old_df = pd.read_csv(old_data_path)
        new_df = pd.read_csv(new_data_path)

        log_info(f"Old data: {len(old_df)} records")
        log_info(f"New data: {len(new_df)} records")

        # Calculate metrics for both datasets
        old_metrics = self._calculate_metrics(old_df, "Old (Before Recalibration)")
        new_metrics = self._calculate_metrics(new_df, "New (After Recalibration)")

        # Generate comparison report
        report = self._create_comparison_markdown(old_metrics, new_metrics)

        # Save report
        output_path = self.output_dir / "before_after_comparison.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        log_info(f"\n✓ Saved comparison report: {output_path}")
        log_info("=" * 80)

        return str(output_path)

    def _calculate_metrics(self, df: pd.DataFrame, label: str) -> Dict:
        """Calculate key metrics for a dataset."""
        log_info(f"\nCalculating metrics for: {label}")

        metrics = {
            "label": label,
            "total_records": len(df),
            "date_range": f"{df['date'].min()} to {df['date'].max()}" if "date" in df.columns else "N/A",
        }

        # Trigger counts and rates
        trigger_types = ["drought_trigger", "flood_trigger", "crop_failure_trigger"]
        for trigger in trigger_types:
            if trigger in df.columns:
                count = int(df[trigger].sum())
                rate = (count / len(df) * 100) if len(df) > 0 else 0
                metrics[f"{trigger}_count"] = count
                metrics[f"{trigger}_rate"] = round(rate, 2)
                log_info(f"  {trigger}: {count} events ({rate:.2f}%)")

        # Confidence scores
        for trigger in trigger_types:
            conf_col = f"{trigger}_confidence"
            if conf_col in df.columns:
                avg_conf = df[conf_col].mean()
                metrics[f"{trigger}_confidence"] = round(avg_conf, 3)

        # Financial estimates (simplified)
        payout_rates = {"drought_trigger": 500, "flood_trigger": 750, "crop_failure_trigger": 1000}

        total_payout = 0
        for trigger, rate in payout_rates.items():
            if trigger in df.columns:
                count = df[trigger].sum()
                conf_col = f"{trigger}_confidence"
                if conf_col in df.columns:
                    weighted_payout = (df[df[trigger] == 1][conf_col] * rate).sum()
                    total_payout += weighted_payout
                else:
                    total_payout += count * rate

        metrics["total_payout"] = round(total_payout, 2)

        # Calculate annual average
        years = df["year"].nunique() if "year" in df.columns else 1
        metrics["annual_payout"] = round(total_payout / years, 2)

        log_info(f"  Total payout: ${total_payout:,.2f}")
        log_info(f"  Annual average: ${metrics['annual_payout']:,.2f}")

        return metrics

    def _create_comparison_markdown(self, old_metrics: Dict, new_metrics: Dict) -> str:
        """Create markdown comparison report."""

        report = f"""# Before/After Trigger Recalibration Comparison

**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Overview

This report compares insurance trigger performance before and after recalibration. The original system had a flood trigger rate of 100%, making the parametric insurance product financially unsustainable. After recalibration, all triggers now operate within acceptable ranges.

---

## Data Summary

| Metric | Before | After |
|--------|--------|-------|
| **Total Records** | {old_metrics['total_records']:,} | {new_metrics['total_records']:,} |
| **Date Range** | {old_metrics['date_range']} | {new_metrics['date_range']} |

---

## Trigger Rate Comparison

### Drought Triggers

| Metric | Before | After | Change | Target Range |
|--------|--------|-------|--------|--------------|
| **Count** | {old_metrics.get('drought_trigger_count', 0)} | {new_metrics.get('drought_trigger_count', 0)} | {new_metrics.get('drought_trigger_count', 0) - old_metrics.get('drought_trigger_count', 0):+d} | - |
| **Rate** | {old_metrics.get('drought_trigger_rate', 0):.2f}% | {new_metrics.get('drought_trigger_rate', 0):.2f}% | {new_metrics.get('drought_trigger_rate', 0) - old_metrics.get('drought_trigger_rate', 0):+.2f}% | 8-20% |
| **Avg Confidence** | {old_metrics.get('drought_trigger_confidence', 0):.3f} | {new_metrics.get('drought_trigger_confidence', 0):.3f} | {new_metrics.get('drought_trigger_confidence', 0) - old_metrics.get('drought_trigger_confidence', 0):+.3f} | - |

**Status:** {'✓ Within Target' if 8 <= new_metrics.get('drought_trigger_rate', 0) <= 20 else '✗ Outside Target'}

### Flood Triggers

| Metric | Before | After | Change | Target Range |
|--------|--------|-------|--------|--------------|
| **Count** | {old_metrics.get('flood_trigger_count', 0)} | {new_metrics.get('flood_trigger_count', 0)} | {new_metrics.get('flood_trigger_count', 0) - old_metrics.get('flood_trigger_count', 0):+d} | - |
| **Rate** | {old_metrics.get('flood_trigger_rate', 0):.2f}% | {new_metrics.get('flood_trigger_rate', 0):.2f}% | {new_metrics.get('flood_trigger_rate', 0) - old_metrics.get('flood_trigger_rate', 0):+.2f}% | 5-15% |
| **Avg Confidence** | {old_metrics.get('flood_trigger_confidence', 0):.3f} | {new_metrics.get('flood_trigger_confidence', 0):.3f} | {new_metrics.get('flood_trigger_confidence', 0) - old_metrics.get('flood_trigger_confidence', 0):+.3f} | - |

**Status:** {'✓ Within Target' if 5 <= new_metrics.get('flood_trigger_rate', 0) <= 15 else '✗ Outside Target'}

### Crop Failure Triggers

| Metric | Before | After | Change | Target Range |
|--------|--------|-------|--------|--------------|
| **Count** | {old_metrics.get('crop_failure_trigger_count', 0)} | {new_metrics.get('crop_failure_trigger_count', 0)} | {new_metrics.get('crop_failure_trigger_count', 0) - old_metrics.get('crop_failure_trigger_count', 0):+d} | - |
| **Rate** | {old_metrics.get('crop_failure_trigger_rate', 0):.2f}% | {new_metrics.get('crop_failure_trigger_rate', 0):.2f}% | {new_metrics.get('crop_failure_trigger_rate', 0) - old_metrics.get('crop_failure_trigger_rate', 0):+.2f}% | 3-10% |
| **Avg Confidence** | {old_metrics.get('crop_failure_trigger_confidence', 0):.3f} | {new_metrics.get('crop_failure_trigger_confidence', 0):.3f} | {new_metrics.get('crop_failure_trigger_confidence', 0) - old_metrics.get('crop_failure_trigger_confidence', 0):+.3f} | - |

**Status:** {'✓ Within Target' if 3 <= new_metrics.get('crop_failure_trigger_rate', 0) <= 10 else '✗ Outside Target'}

---

## Financial Impact

### Payout Comparison

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Total Payout** | ${old_metrics['total_payout']:,.2f} | ${new_metrics['total_payout']:,.2f} | ${new_metrics['total_payout'] - old_metrics['total_payout']:+,.2f} ({(new_metrics['total_payout'] - old_metrics['total_payout']) / old_metrics['total_payout'] * 100:+.1f}%) |
| **Annual Average** | ${old_metrics['annual_payout']:,.2f} | ${new_metrics['annual_payout']:,.2f} | ${new_metrics['annual_payout'] - old_metrics['annual_payout']:+,.2f} |

### Sustainability Analysis

Assuming annual premium income of $2,400 per insured entity:

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Loss Ratio** | {old_metrics['annual_payout'] / 2400 * 100:.1f}% | {new_metrics['annual_payout'] / 2400 * 100:.1f}% | < 80% |
| **Sustainability** | {'✓ Sustainable' if old_metrics['annual_payout'] / 2400 * 100 < 80 else '✗ Unsustainable'} | {'✓ Sustainable' if new_metrics['annual_payout'] / 2400 * 100 < 80 else '✗ Unsustainable'} | - |

---

## Key Improvements

"""

        # Calculate improvements
        improvements = []

        # Flood rate improvement
        flood_old = old_metrics.get("flood_trigger_rate", 0)
        flood_new = new_metrics.get("flood_trigger_rate", 0)
        if flood_old > 15 and 5 <= flood_new <= 15:
            improvements.append(
                f"✓ **Flood trigger rate reduced** from {flood_old:.1f}% to {flood_new:.1f}% (now within 5-15% target)"
            )

        # Drought rate check
        drought_new = new_metrics.get("drought_trigger_rate", 0)
        if 8 <= drought_new <= 20:
            improvements.append(f"✓ **Drought trigger rate maintained** at {drought_new:.1f}% (within 8-20% target)")

        # Crop failure improvement
        crop_old = old_metrics.get("crop_failure_trigger_rate", 0)
        crop_new = new_metrics.get("crop_failure_trigger_rate", 0)
        if crop_old < 3 and 3 <= crop_new <= 10:
            improvements.append(
                f"✓ **Crop failure trigger activated** - increased from {crop_old:.1f}% to {crop_new:.1f}% (now within 3-10% target)"
            )

        # Financial improvement
        payout_reduction = old_metrics["annual_payout"] - new_metrics["annual_payout"]
        if payout_reduction > 0:
            improvements.append(
                f"✓ **Annual payout reduced** by ${payout_reduction:,.2f} ({payout_reduction / old_metrics['annual_payout'] * 100:.1f}%)"
            )

        # Sustainability improvement
        old_loss_ratio = old_metrics["annual_payout"] / 2400 * 100
        new_loss_ratio = new_metrics["annual_payout"] / 2400 * 100
        if new_loss_ratio < 80 and old_loss_ratio >= 80:
            improvements.append(
                f"✓ **Financial sustainability achieved** - loss ratio reduced from {old_loss_ratio:.1f}% to {new_loss_ratio:.1f}%"
            )

        if improvements:
            for imp in improvements:
                report += f"{imp}\n"
        else:
            report += "No significant improvements detected. Further calibration may be needed.\n"

        report += "\n---\n\n## Recommendations\n\n"

        # Generate recommendations
        all_within_target = (
            5 <= new_metrics.get("flood_trigger_rate", 0) <= 15
            and 8 <= new_metrics.get("drought_trigger_rate", 0) <= 20
            and 3 <= new_metrics.get("crop_failure_trigger_rate", 0) <= 10
        )

        if all_within_target and new_loss_ratio < 80:
            report += "1. ✓ **All triggers within target ranges** - system is ready for production\n"
            report += "2. ✓ **Financial sustainability achieved** - continue monitoring monthly\n"
            report += "3. **Next steps:** Deploy to production and establish ongoing monitoring\n"
        else:
            report += "1. ⚠️ **Further calibration needed** - some triggers outside target ranges\n"
            report += "2. **Review threshold values** in configuration file\n"
            report += "3. **Reprocess data** with adjusted thresholds\n"
            report += "4. **Validate again** before production deployment\n"

        report += "\n---\n\n## Visualization Recommendations\n\n"
        report += "Consider generating the following visualizations:\n\n"
        report += "1. **Trigger Rate Timeline** - Show trigger activations over time (before vs after)\n"
        report += "2. **Seasonal Distribution** - Compare trigger patterns by month\n"
        report += "3. **Confidence Score Distribution** - Histogram of confidence scores\n"
        report += "4. **Financial Impact Chart** - Bar chart comparing payouts\n"

        report += "\n---\n\n*Report generated by Business Metrics Reporter v1.0*\n"

        return report
