"""
Generate Business Metrics Reports

Quick script to generate all business-focused reports from climate data.
Run this after training models or updating predictions.

Usage:
    python generate_business_reports.py
    python generate_business_reports.py --data path/to/data.csv
"""

import sys
from pathlib import Path

# Add project root to path (go up 2 levels from scripts/reporting/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from reporting.business_metrics import BusinessMetricsReporter
from reporting.visualize_business_metrics import BusinessMetricsVisualizer
from utils.logger import log_info


def main():
    """Generate all business reports."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate business metrics reports for climate insurance'
    )
    parser.add_argument(
        '--data', 
        type=str, 
        default='outputs/processed/master_dataset.csv',
        help='Path to master dataset with triggers (default: outputs/processed/master_dataset.csv)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default=None,
        help='Output directory for reports (default: outputs/business_reports/)'
    )
    
    args = parser.parse_args()
    
    # Check if data file exists
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"❌ Error: Data file not found: {data_path}")
        print(f"   Please run the data pipeline first or specify correct path with --data")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("BUSINESS METRICS REPORT GENERATOR")
    print("=" * 80)
    print(f"Data source: {data_path}")
    print(f"Output: {args.output or 'outputs/business_reports/'}")
    print("=" * 80 + "\n")
    
    # Generate reports
    reporter = BusinessMetricsReporter(output_dir=args.output)
    reports = reporter.generate_full_report(data_path=str(data_path))
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    visualizer = BusinessMetricsVisualizer(reports_dir=str(reporter.output_dir))
    visualizer.generate_all_visualizations()
    
    # Print summary
    print("\n" + "=" * 80)
    print("✓ REPORTS GENERATED SUCCESSFULLY")
    print("=" * 80)
    print(f"\n📁 Reports location: {reporter.output_dir}\n")
    print("📊 Available reports:")
    print("   1. executive_summary.md - High-level overview for stakeholders")
    print("   2. insurance_triggers_detailed.csv - All trigger events with dates")
    print("   3. alert_timeline.csv - Drought/flood/crop failure alerts")
    print("   4. payout_estimates.csv - Financial impact per event")
    print("   5. payout_summary_by_year.csv - Yearly financial summary")
    print("   6. risk_dashboard.json - Machine-readable metrics")
    print("\n📈 Visualizations:")
    print("   1. trigger_timeline.png - Timeline of trigger events")
    print("   2. financial_impact.png - Payouts and events by year")
    print("   3. alert_distribution.png - Alert types and severity")
    print("   4. risk_heatmap.png - Monthly risk patterns")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
