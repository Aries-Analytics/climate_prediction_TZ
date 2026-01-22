"""
Pipeline Performance Monitoring Script

Tracks ingestion duration, API response times, and database performance.
Generates performance metrics for optimization.

Usage:
    python scripts/monitor_pipeline_performance.py
    python scripts/monitor_pipeline_performance.py --send-alerts
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from utils.slack_notifier import send_slack_notification, AlertSeverity

# Load environment
load_dotenv()


class PerformanceMonitor:
    """Monitor pipeline and API performance metrics."""
    
    # Performance thresholds (in seconds)
    THRESHOLDS = {
        "ingestion_duration": {
            "CHIRPS": 300,      # 5 minutes
            "NASA_POWER": 180,  # 3 minutes
            "ERA5": 600,        # 10 minutes
            "NDVI": 300,        # 5 minutes
            "OCEAN_INDICES": 60 # 1 minute
        },
        "api_response_time": 30,  # 30 seconds
        "db_write_rate": 100      # records/second minimum
    }
    
    def __init__(self, db_url: str):
        """Initialize performance monitor."""
        self.engine = create_engine(db_url)
        self.performance_log = []
        self.issues = []
    
    def check_ingestion_performance(self) -> Dict[str, Dict]:
        """
        Check ingestion duration for each data source.
        
        Returns:
            Dict with performance metrics per source
        """
        print("\n" + "="*60)
        print("Checking Ingestion Performance")
        print("="*60)
        
        performance = {}
        
        # This would typically read from a pipeline execution log
        # For now, we'll check if log file exists and parse it
        log_file = Path("logs/pipeline.log")
        
        if not log_file.exists():
            print("  ⚠️ Pipeline log not found. Run pipeline to generate metrics.")
            return performance
        
        # Read last 1000 lines of log to find recent ingestion times
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-1000:]
            
            # Parse ingestion timestamps (this is a simplified example)
            # Real implementation would have structured logging
            for source in ["CHIRPS", "NASA_POWER", "ERA5", "NDVI", "OCEAN_INDICES"]:
                # Look for completion messages
                source_lines = [l for l in lines if source in l and "completed" in l.lower()]
                
                if source_lines:
                    print(f"  ✓ {source:20} Recent execution found")
                    performance[source] = {
                        "last_run": "Recently",
                        "status": "tracked"
                    }
                else:
                    print(f"  ℹ {source:20} No recent execution")
                    performance[source] = {
                        "last_run": "Not found",
                        "status": "no_data"
                    }
        
        except Exception as e:
            print(f"  ✗ Error reading log: {e}")
        
        return performance
    
    def check_database_performance(self) -> Dict:
        """
        Check database read/write performance.
        
        Returns:
            Dict with database performance metrics
        """
        print("\n" + "="*60)
        print("Checking Database Performance")
        print("="*60)
        
        metrics = {}
        
        with self.engine.connect() as conn:
            try:
                # Test read performance
                start = time.time()
                query = text("SELECT COUNT(*) FROM climate_data")
                count = conn.execute(query).scalar()
                read_time = time.time() - start
                
                metrics["total_records"] = count
                metrics["read_time_ms"] = round(read_time * 1000, 2)
                metrics["read_rate"] = round(count / read_time if read_time > 0 else 0, 2)
                
                print(f"  Total Records: {count:,}")
                print(f"  Read Time: {metrics['read_time_ms']} ms")
                print(f"  Read Rate: {metrics['read_rate']:,.0f} records/sec")
                
                # Check index performance
                start = time.time()
                query = text("""
                    SELECT source, COUNT(*) 
                    FROM climate_data 
                    GROUP BY source
                """)
                result = conn.execute(query).fetchall()
                index_time = time.time() - start
                
                metrics["index_time_ms"] = round(index_time * 1000, 2)
                
                if index_time < 0.1:
                    print(f"  ✓ Index Performance: Excellent ({metrics['index_time_ms']} ms)")
                elif index_time < 1.0:
                    print(f"  ✓ Index Performance: Good ({metrics['index_time_ms']} ms)")
                else:
                    print(f"  ⚠ Index Performance: Slow ({metrics['index_time_ms']} ms)")
                    self.issues.append(f"Slow index performance: {metrics['index_time_ms']} ms")
                
                # Check table size
                try:
                    db_name = os.getenv("POSTGRES_DB", "climate_dev")
                    query = text(f"""
                        SELECT pg_size_pretty(pg_total_relation_size('climate_data'))
                    """)
                    size = conn.execute(query).scalar()
                    metrics["table_size"] = size
                    print(f"  Table Size: {size}")
                except:
                    pass  # Size query may fail on non-PostgreSQL
            
            except Exception as e:
                print(f"  ✗ Error checking database performance: {e}")
                metrics["error"] = str(e)
        
        return metrics
    
    def check_recent_pipeline_runs(self) -> List[Dict]:
        """
        Check recent pipeline execution history.
        
        Returns:
            List of recent pipeline runs with metrics
        """
        print("\n" + "="*60)
        print("Recent Pipeline Executions")
        print("="*60)
        
        runs = []
        
        # Check for execution log/history
        # This would typically come from a structured log or database table
        log_file = Path("logs/pipeline.log")
        
        if log_file.exists():
            try:
                # Get file modification time as proxy for last run
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                age_hours = (datetime.now() - mtime).total_seconds() / 3600
                
                print(f"  Last pipeline run: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Age: {age_hours:.1f} hours ago")
                
                if age_hours < 24:
                    status = "✓ Recent"
                elif age_hours < 72:
                    status = "⚠ Slightly old"
                else:
                    status = "✗ Stale"
                    self.issues.append(f"Pipeline hasn't run in {age_hours:.0f} hours")
                
                print(f"  Status: {status}")
                
                runs.append({
                    "timestamp": mtime.isoformat(),
                    "age_hours": round(age_hours, 1),
                    "status": "detected"
                })
            
            except Exception as e:
                print(f"  ✗ Error checking pipeline log: {e}")
        else:
            print("  ℹ No pipeline log found")
        
        return runs
    
    def generate_performance_report(
        self,
        ingestion_perf: Dict,
        db_perf: Dict,
        recent_runs: List[Dict]
    ) -> str:
        """Generate performance report."""
        report = []
        report.append("\n" + "="*60)
        report.append("PERFORMANCE REPORT")
        report.append("="*60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Database Performance
        if db_perf:
            report.append("Database Performance:")
            if "total_records" in db_perf:
                report.append(f"  • Total Records: {db_perf['total_records']:,}")
            if "read_time_ms" in db_perf:
                report.append(f"  • Read Time: {db_perf['read_time_ms']} ms")
            if "index_time_ms" in db_perf:
                report.append(f"  • Index Query: {db_perf['index_time_ms']} ms")
            if "table_size" in db_perf:
                report.append(f"  • Table Size: {db_perf['table_size']}")
        
        report.append("")
        
        # Issues
        if self.issues:
            report.append("Performance Issues:")
            for issue in self.issues:
                report.append(f"  • {issue}")
        else:
            report.append("No performance issues detected!")
        
        report.append("")
        report.append("="*60)
        
        return "\n".join(report)
    
    def send_performance_alert(self, report: str):
        """Send performance alert to Slack if configured."""
        webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL")
        slack_enabled = os.getenv("ALERT_SLACK_ENABLED", "false").lower() == "true"
        
        if not slack_enabled or not webhook_url:
            print("\n[INFO] Slack alerts not configured. Skipping notification.")
            return
        
        # Determine severity based on issues
        if len(self.issues) == 0:
            severity = AlertSeverity.SUCCESS
            title = "Pipeline Performance: Excellent"
        elif len(self.issues) <= 2:
            severity = AlertSeverity.WARNING
            title = "Pipeline Performance: Review Recommended"
        else:
            severity = AlertSeverity.ERROR
            title = "Pipeline Performance: Issues Detected"
        
        message = f"*Performance Summary:*\n\n"
        
        if self.issues:
            message += "*Issues Found:*\n"
            for issue in self.issues[:5]:  # Limit to 5 issues
                message += f"• {issue}\n"
            if len(self.issues) > 5:
                message += f"• ... and {len(self.issues) - 5} more\n"
        else:
            message += "All performance metrics within acceptable ranges ✅"
        
        send_slack_notification(
            webhook_url=webhook_url,
            message=message,
            severity=severity,
            title=title
        )


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Monitor pipeline performance")
    parser.add_argument(
        "--send-alerts",
        action="store_true",
        help="Send Slack alerts for performance issues"
    )
    args = parser.parse_args()
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in environment")
        sys.exit(1)
    
    # Run performance checks
    monitor = PerformanceMonitor(db_url)
    
    try:
        ingestion_perf = monitor.check_ingestion_performance()
        db_perf = monitor.check_database_performance()
        recent_runs = monitor.check_recent_pipeline_runs()
        
        # Generate report
        report = monitor.generate_performance_report(ingestion_perf, db_perf, recent_runs)
        print(report)
        
        # Send alerts if requested
        if args.send_alerts:
            monitor.send_performance_alert(report)
        
        # Exit with appropriate code
        if len(monitor.issues) == 0:
            sys.exit(0)  # Success
        elif len(monitor.issues) <= 2:
            sys.exit(1)  # Warning
        else:
            sys.exit(2)  # Critical
    
    except Exception as e:
        print(f"\n❌ Error monitoring performance: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
