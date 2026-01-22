"""
Pipeline Health Monitoring Script

Checks data freshness, completeness, and quality for all climate data sources.
Generates health report and sends Slack alerts for issues.

Usage:
    python scripts/monitor_pipeline_health.py
    python scripts/monitor_pipeline_health.py --send-alerts
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from utils.slack_notifier import send_slack_notification, AlertSeverity

# Load environment
load_dotenv()


class PipelineHealthMonitor:
    """Monitor pipeline health and data quality."""
    
    # Expected data sources
    DATA_SOURCES = ["CHIRPS", "NASA_POWER", "ERA5", "NDVI", "OCEAN_INDICES"]
    
    def __init__(self, db_url: str):
        """Initialize health monitor."""
        self.engine = create_engine(db_url)
        self.staleness_threshold_days = int(os.getenv("DATA_STALENESS_THRESHOLD_DAYS", "7"))
        self.health_score = 100
        self.issues = []
    
    def check_data_freshness(self) -> Dict[str, Tuple[datetime, int]]:
        """
        Check how recent the data is for each source.
        
        Returns:
            Dict mapping source to (latest_date, days_old)
        """
        print("\n" + "="*60)
        print("Checking Data Freshness")
        print("="*60)
        
        freshness = {}
        
        with self.engine.connect() as conn:
            for source in self.DATA_SOURCES:
                try:
                    query = text("""
                        SELECT MAX(date) as latest_date, COUNT(*) as record_count
                        FROM climate_data
                        WHERE source = :source
                    """)
                    
                    result = conn.execute(query, {"source": source}).fetchone()
                    
                    if result and result[0]:
                        latest_date = result[0]
                        days_old = (datetime.now().date() - latest_date).days
                        freshness[source] = (latest_date, days_old)
                        
                        # Assess freshness
                        if days_old <= self.staleness_threshold_days:
                            status = "✓ Fresh"
                        elif days_old <= 14:
                            status = "⚠ Stale"
                            self.health_score -= 5
                            self.issues.append(f"{source}: Data is {days_old} days old")
                        else:
                            status = "✗ Very Stale"
                            self.health_score -= 15
                            self.issues.append(f"{source}: Data is VERY stale ({days_old} days old)")
                        
                        print(f"{status:12} {source:20} Last update: {latest_date} ({days_old} days ago)")
                    else:
                        print(f"✗ No Data   {source:20} No records found")
                        self.health_score -= 20
                        self.issues.append(f"{source}: No data available")
                        freshness[source] = (None, 999)
                
                except Exception as e:
                    print(f"✗ Error     {source:20} Error checking: {e}")
                    self.health_score -= 10
                    self.issues.append(f"{source}: Error checking freshness")
                    freshness[source] = (None, 999)
        
        return freshness
    
    def check_data_completeness(self) -> Dict[str, Dict]:
        """
        Check if we have complete data for expected date ranges.
        
        Returns:
            Dict with completeness info per source
        """
        print("\n" + "="*60)
        print("Checking Data Completeness")
        print("="*60)
        
        completeness = {}
        
        with self.engine.connect() as conn:
            for source in self.DATA_SOURCES:
                try:
                    query = text("""
                        SELECT 
                            MIN(date) as earliest_date,
                            MAX(date) as latest_date,
                            COUNT(*) as record_count,
                            COUNT(DISTINCT date) as unique_dates
                        FROM climate_data
                        WHERE source = :source
                    """)
                    
                    result = conn.execute(query, {"source": source}).fetchone()
                    
                    if result and result[2] > 0:
                        earliest = result[0]
                        latest = result[1]
                        record_count = result[2]
                        unique_dates = result[3]
                        
                        # Calculate expected months
                        if earliest and latest:
                            months_expected = ((latest.year - earliest.year) * 12 + 
                                             (latest.month - earliest.month) + 1)
                            completeness_pct = (unique_dates / months_expected) * 100
                            
                            completeness[source] = {
                                "earliest": earliest,
                                "latest": latest,
                                "record_count": record_count,
                                "unique_dates": unique_dates,
                                "expected_dates": months_expected,
                                "completeness_pct": completeness_pct
                            }
                            
                            if completeness_pct >= 95:
                                status = "✓ Complete"
                            elif completeness_pct >= 80:
                                status = "⚠ Partial"
                                self.health_score -= 3
                            else:
                                status = "✗ Incomplete"
                                self.health_score -= 10
                                self.issues.append(f"{source}: Only {completeness_pct:.1f}% complete")
                            
                            print(f"{status:12} {source:20} {unique_dates}/{months_expected} months ({completeness_pct:.1f}%)")
                        else:
                            print(f"✗ Error     {source:20} Invalid date range")
                    else:
                        print(f"✗ No Data   {source:20} No records")
                        completeness[source] = {"record_count": 0}
                
                except Exception as e:
                    print(f"✗ Error     {source:20} Error: {e}")
                    completeness[source] = {"error": str(e)}
        
        return completeness
    
    def check_data_quality(self) -> Dict[str, Dict]:
        """
        Check for basic data quality issues.
        
        Returns:
            Dict with quality metrics per source
        """
        print("\n" + "="*60)
        print("Checking Data Quality")
        print("="*60)
        
        quality = {}
        
        with self.engine.connect() as conn:
            for source in self.DATA_SOURCES:
                try:
                    # Check for null values in key columns
                    query = text("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) as null_values
                        FROM climate_data
                        WHERE source = :source
                    """)
                    
                    result = conn.execute(query, {"source": source}).fetchone()
                    
                    if result and result[0] > 0:
                        total = result[0]
                        null_count = result[1] or 0
                        null_pct = (null_count / total) * 100
                        
                        quality[source] = {
                            "total_records": total,
                            "null_count": null_count,
                            "null_pct": null_pct
                        }
                        
                        if null_pct == 0:
                            status = "✓ Excellent"
                        elif null_pct < 5:
                            status = "✓ Good"
                        elif null_pct < 10:
                            status = "⚠ Fair"
                            self.health_score -= 3
                        else:
                            status = "✗ Poor"
                            self.health_score -= 10
                            self.issues.append(f"{source}: {null_pct:.1f}% null values")
                        
                        print(f"{status:12} {source:20} {null_pct:.2f}% null values")
                    else:
                        print(f"✗ No Data   {source:20} No records")
                        quality[source] = {"total_records": 0}
                
                except Exception as e:
                    print(f"✗ Error     {source:20} Error: {e}")
                    quality[source] = {"error": str(e)}
        
        return quality
    
    def generate_health_report(
        self,
        freshness: Dict,
        completeness: Dict,
        quality: Dict
    ) -> str:
        """Generate comprehensive health report."""
        report = []
        report.append("\n" + "="*60)
        report.append("PIPELINE HEALTH REPORT")
        report.append("="*60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Overall Health Score: {max(0, self.health_score)}/100")
        report.append("")
        
        # Categorize health
        if self.health_score >= 90:
            health_category = "✓ EXCELLENT"
        elif self.health_score >= 75:
            health_category = "⚠ GOOD"
        elif self.health_score >= 50:
            health_category = "⚠ FAIR"
        else:
            health_category = "✗ POOR"
        
        report.append(f"Status: {health_category}")
        report.append("")
        
        # Issues
        if self.issues:
            report.append("Issues Found:")
            for issue in self.issues:
                report.append(f"  • {issue}")
        else:
            report.append("No issues found!")
        
        report.append("")
        report.append("="*60)
        
        return "\n".join(report)
    
    def send_health_alert(self, report: str):
        """Send health alert to Slack if configured."""
        webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL")
        slack_enabled = os.getenv("ALERT_SLACK_ENABLED", "false").lower() == "true"
        
        if not slack_enabled or not webhook_url:
            print("\n[INFO] Slack alerts not configured. Skipping notification.")
            return
        
        # Determine severity
        if self.health_score >= 90:
            severity = AlertSeverity.SUCCESS
            title = "Pipeline Health: Excellent"
        elif self.health_score >= 75:
            severity = AlertSeverity.INFO
            title = "Pipeline Health: Good"
        elif self.health_score >= 50:
            severity = AlertSeverity.WARNING
            title = "Pipeline Health: Fair - Review Needed"
        else:
            severity = AlertSeverity.ERROR
            title = "Pipeline Health: Poor - Action Required"
        
        message = f"*Health Score:* {max(0, self.health_score)}/100\n\n"
        
        if self.issues:
            message += "*Issues:*\n"
            for issue in self.issues[:5]:  # Limit to 5 issues
                message += f"• {issue}\n"
            if len(self.issues) > 5:
                message += f"• ... and {len(self.issues) - 5} more\n"
        else:
            message += "All systems green! ✅"
        
        send_slack_notification(
            webhook_url=webhook_url,
            message=message,
            severity=severity,
            title=title
        )


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Monitor pipeline health")
    parser.add_argument(
        "--send-alerts",
        action="store_true",
        help="Send Slack alerts for issues"
    )
    args = parser.parse_args()
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in environment")
        sys.exit(1)
    
    # Run health checks
    monitor = PipelineHealthMonitor(db_url)
    
    try:
        freshness = monitor.check_data_freshness()
        completeness = monitor.check_data_completeness()
        quality = monitor.check_data_quality()
        
        # Generate report
        report = monitor.generate_health_report(freshness, completeness, quality)
        print(report)
        
        # Send alerts if requested
        if args.send_alerts:
            monitor.send_health_alert(report)
        
        # Exit with appropriate code
        if monitor.health_score >= 75:
            sys.exit(0)  # Success
        elif monitor.health_score >= 50:
            sys.exit(1)  # Warning
        else:
            sys.exit(2)  # Critical
    
    except Exception as e:
        print(f"\n❌ Error running health checks: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
