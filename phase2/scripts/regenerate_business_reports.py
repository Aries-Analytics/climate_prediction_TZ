"""
Regenerate business reports with calibrated trigger data.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from reporting.business_metrics import BusinessMetricsReporter

def main():
    """Regenerate all business reports with new calibrated triggers."""
    print("="*70)
    print("REGENERATING BUSINESS REPORTS")
    print("="*70)
    
    # Path to master dataset with new triggers
    data_path = "outputs/processed/master_dataset.csv"
    
    print(f"\nUsing data: {data_path}")
    
    # Initialize reporter
    reporter = BusinessMetricsReporter()
    
    # Generate full report
    print("\nGenerating business metrics reports...")
    results = reporter.generate_full_report(data_path)
    
    print("\n" + "="*70)
    print("REPORTS GENERATED SUCCESSFULLY")
    print("="*70)
    print(f"\nReports saved to: outputs/business_reports/")
    print("\nGenerated files:")
    print("  - executive_summary.md")
    print("  - insurance_triggers_detailed.csv")
    print("  - alert_timeline.csv")
    print("  - payout_estimates.csv")
    print("  - risk_dashboard.json")
    
    return results

if __name__ == '__main__':
    main()
