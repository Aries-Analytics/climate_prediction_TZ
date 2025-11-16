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
        if 'date' not in df.columns and 'year' in df.columns and 'month' in df.columns:
            df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        
        reports_generated = {}
        
        # 1. Insurance Triggers Summary
        log_info("\n[1/5] Generating insurance triggers report...")
        trigger_report = self._generate_trigger_report(df)
        reports_generated['triggers'] = trigger_report
        
        # 2. Alert Timeline
        log_info("\n[2/5] Generating alert timeline...")
        alert_timeline = self._generate_alert_timeline(df)
        reports_generated['alerts'] = alert_timeline
        
        # 3. Financial Impact Analysis
        log_info("\n[3/5] Generating financial impact analysis...")
        financial_report = self._generate_financial_report(df)
        reports_generated['financial'] = financial_report
        
        # 4. Risk Assessment Dashboard
        log_info("\n[4/5] Generating risk assessment dashboard...")
        risk_dashboard = self._generate_risk_dashboard(df)
        reports_generated['risk'] = risk_dashboard
        
        # 5. Executive Summary
        log_info("\n[5/5] Generating executive summary...")
        exec_summary = self._generate_executive_summary(df, reports_generated)
        reports_generated['executive'] = exec_summary
        
        log_info("\n" + "=" * 80)
        log_info("✓ Business metrics reports generated successfully!")
        log_info(f"✓ Reports saved to: {self.output_dir}")
        log_info("=" * 80)
        
        return reports_generated
    
    def _generate_trigger_report(self, df: pd.DataFrame) -> str:
        """Generate detailed insurance trigger events report."""
        
        # Identify trigger columns
        trigger_cols = [c for c in df.columns if 'trigger' in c.lower() and 'confidence' not in c.lower()]
        
        if not trigger_cols:
            log_warning("No trigger columns found in dataset")
            return None
        
        # Extract trigger events
        trigger_events = []
        
        for idx, row in df.iterrows():
            date = row.get('date', f"{row.get('year', 'N/A')}-{row.get('month', 'N/A'):02d}")
            
            for col in trigger_cols:
                if row[col] == 1:  # Trigger activated
                    confidence_col = f"{col}_confidence"
                    confidence = row.get(confidence_col, 0.0)
                    
                    trigger_events.append({
                        'date': date,
                        'trigger_type': col.replace('_trigger', '').replace('_', ' ').title(),
                        'activated': 'Yes',
                        'confidence': f"{confidence:.2%}",
                        'severity': row.get('trigger_severity', row.get('trigger_severity_left', 0.0))
                    })
        
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
            date = row.get('date', f"{row.get('year', 'N/A')}-{row.get('month', 'N/A'):02d}")
            
            # Drought alerts
            if row.get('drought_trigger', 0) == 1:
                alerts.append({
                    'date': date,
                    'alert_type': 'DROUGHT',
                    'severity': self._classify_severity(row.get('drought_trigger_confidence', 0)),
                    'confidence': row.get('drought_trigger_confidence', 0),
                    'action_required': 'Monitor water resources, prepare irrigation'
                })
            
            # Flood alerts
            if row.get('flood_trigger', 0) == 1:
                alerts.append({
                    'date': date,
                    'alert_type': 'FLOOD',
                    'severity': self._classify_severity(row.get('flood_trigger_confidence', 0)),
                    'confidence': row.get('flood_trigger_confidence', 0),
                    'action_required': 'Prepare drainage, protect crops'
                })
            
            # Crop failure alerts
            if row.get('crop_failure_trigger', 0) == 1:
                alerts.append({
                    'date': date,
                    'alert_type': 'CROP_FAILURE',
                    'severity': self._classify_severity(row.get('crop_failure_trigger_confidence', 0)),
                    'confidence': row.get('crop_failure_trigger_confidence', 0),
                    'action_required': 'Assess crop damage, initiate insurance claims'
                })
        
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
            'drought_trigger': 500,  # USD per trigger event
            'flood_trigger': 750,
            'crop_failure_trigger': 1000,
            'severe_stress_trigger': 300
        }
        
        financial_data = []
        
        for idx, row in df.iterrows():
            date = row.get('date', f"{row.get('year', 'N/A')}-{row.get('month', 'N/A'):02d}")
            year = row.get('year', pd.to_datetime(date).year if isinstance(date, str) else None)
            
            total_payout = 0
            triggered_events = []
            
            for trigger_type, base_payout in PAYOUT_RATES.items():
                if row.get(trigger_type, 0) == 1:
                    # Adjust payout by severity
                    severity = row.get('trigger_severity', 0.5)
                    confidence = row.get(f"{trigger_type}_confidence", 0.5)
                    
                    payout = base_payout * (0.5 + severity) * confidence
                    total_payout += payout
                    triggered_events.append(trigger_type.replace('_trigger', ''))
            
            if total_payout > 0:
                financial_data.append({
                    'date': date,
                    'year': year,
                    'triggered_events': ', '.join(triggered_events),
                    'estimated_payout_usd': round(total_payout, 2),
                    'severity_multiplier': row.get('trigger_severity', 0.5),
                    'confidence_score': row.get('drought_trigger_confidence', 0.5)
                })
        
        # Save detailed payouts
        financial_df = pd.DataFrame(financial_data)
        output_path = self.output_dir / "payout_estimates.csv"
        financial_df.to_csv(output_path, index=False)
        log_info(f"   ✓ Saved: {output_path}")
        
        # Generate summary by year
        if not financial_df.empty and 'year' in financial_df.columns:
            yearly_summary = financial_df.groupby('year').agg({
                'estimated_payout_usd': 'sum',
                'triggered_events': 'count'
            }).rename(columns={'triggered_events': 'total_events'})
            
            summary_path = self.output_dir / "payout_summary_by_year.csv"
            yearly_summary.to_csv(summary_path)
            log_info(f"   ✓ Saved: {summary_path}")
        
        return str(output_path)
    
    def _generate_risk_dashboard(self, df: pd.DataFrame) -> str:
        """Generate risk assessment dashboard data."""
        
        risk_metrics = {
            'total_records': len(df),
            'date_range': f"{df['date'].min()} to {df['date'].max()}" if 'date' in df.columns else 'N/A',
            'drought_events': int(df.get('drought_trigger', pd.Series([0])).sum()),
            'flood_events': int(df.get('flood_trigger', pd.Series([0])).sum()),
            'crop_failure_events': int(df.get('crop_failure_trigger', pd.Series([0])).sum()),
            'total_trigger_events': int(df.get('any_trigger', pd.Series([0])).sum()),
            'high_risk_periods': int((df.get('trigger_severity', pd.Series([0])) > 0.7).sum()),
            'avg_drought_confidence': float(df.get('drought_trigger_confidence', pd.Series([0])).mean()),
            'avg_flood_confidence': float(df.get('flood_trigger_confidence', pd.Series([0])).mean()),
            'avg_severity': float(df.get('trigger_severity', pd.Series([0])).mean())
        }
        
        # Save as JSON
        output_path = self.output_dir / "risk_dashboard.json"
        with open(output_path, 'w') as f:
            json.dump(risk_metrics, f, indent=2)
        log_info(f"   ✓ Saved: {output_path}")
        
        return str(output_path)
    
    def _generate_executive_summary(self, df: pd.DataFrame, reports: Dict) -> str:
        """Generate executive summary markdown report."""
        
        # Calculate key metrics
        total_triggers = int(df.get('any_trigger', pd.Series([0])).sum())
        drought_events = int(df.get('drought_trigger', pd.Series([0])).sum())
        flood_events = int(df.get('flood_trigger', pd.Series([0])).sum())
        crop_failures = int(df.get('crop_failure_trigger', pd.Series([0])).sum())
        
        # Load financial data if available
        total_payout = 0
        if 'financial' in reports:
            try:
                financial_df = pd.read_csv(reports['financial'])
                total_payout = financial_df['estimated_payout_usd'].sum()
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

| Alert Type | Count | Percentage |
|------------|-------|------------|
| 🌵 **Drought Events** | {drought_events} | {drought_events/len(df)*100:.1f}% |
| 🌊 **Flood Events** | {flood_events} | {flood_events/len(df)*100:.1f}% |
| 🌾 **Crop Failure Events** | {crop_failures} | {crop_failures/len(df)*100:.1f}% |

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
        with open(output_path, 'w', encoding='utf-8') as f:
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
        if 'month' in df.columns and 'any_trigger' in df.columns:
            monthly_risk = df.groupby('month')['any_trigger'].sum()
            highest_month = monthly_risk.idxmax()
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            return month_names[int(highest_month) - 1] if highest_month <= 12 else 'Unknown'
        return "Unknown"
    
    def _assess_overall_risk(self, df: pd.DataFrame) -> str:
        """Assess overall risk level."""
        if 'any_trigger' not in df.columns:
            return "UNKNOWN"
        
        trigger_rate = df['any_trigger'].sum() / len(df)
        
        if trigger_rate >= 0.4:
            return "🔴 HIGH RISK"
        elif trigger_rate >= 0.2:
            return "🟡 MODERATE RISK"
        else:
            return "🟢 LOW RISK"


def main():
    """Main function to generate business reports."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate business metrics reports')
    parser.add_argument('--data', type=str, default='outputs/processed/master_dataset.csv',
                       help='Path to master dataset')
    parser.add_argument('--output', type=str, default=None,
                       help='Output directory for reports')
    
    args = parser.parse_args()
    
    reporter = BusinessMetricsReporter(output_dir=args.output)
    reports = reporter.generate_full_report(data_path=args.data)
    
    print("\n✓ Business metrics reports generated successfully!")
    print(f"✓ Check: {reporter.output_dir}")


if __name__ == "__main__":
    main()
