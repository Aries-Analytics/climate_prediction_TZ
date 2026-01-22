"""
Dev Dashboard Summary Script

Quick overview of dev environment status with color-coded terminal output.

Usage:
    python scripts/dev_dashboard_summary.py
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv()


# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header():
    """Print dashboard header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}   CLIMATE PREDICTION PIPELINE - DEV DASHBOARD{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Environment: {os.getenv('ENVIRONMENT', 'development').upper()}")
    print()


def get_data_sources_status(engine):
    """Get status of all data sources."""
    print(f"{Colors.BOLD}📊 DATA SOURCES STATUS{Colors.END}")
    print(f"{'-'*70}")
    
    sources = ["CHIRPS", "NASA_POWER", "ERA5", "NDVI", "OCEAN_INDICES"]
    staleness_threshold = int(os.getenv("DATA_STALENESS_THRESHOLD_DAYS", "7"))
    
    with engine.connect() as conn:
        for source in sources:
            try:
                query = text("""
                    SELECT 
                        COUNT(*) as count,
                        MAX(date) as latest,
                        MIN(date) as earliest
                    FROM climate_data
                    WHERE source = :source
                """)
                
                result = conn.execute(query, {"source": source}).fetchone()
                
                if result and result[0] > 0:
                    count = result[0]
                    latest = result[1]
                    earliest = result[2]
                    days_old = (datetime.now().date() - latest).days
                    
                    # Color code based on freshness
                    if days_old <= staleness_threshold:
                        color = Colors.GREEN
                        status = "✓"
                    elif days_old <= 14:
                        color = Colors.YELLOW
                        status = "⚠"
                    else:
                        color = Colors.RED
                        status = "✗"
                    
                    print(f"  {color}{status} {source:20}{Colors.END} " +
                          f"{count:>8,} records  |  Latest: {latest}  ({days_old}d ago)")
                else:
                    print(f"  {Colors.RED}✗ {source:20}{Colors.END} No data")
            
            except Exception as e:
                print(f"  {Colors.RED}✗ {source:20}{Colors.END} Error: {e}")
    
    print()


def get_recent_activity(engine):
    """Get recent pipeline activity."""
    print(f"{Colors.BOLD}📈 RECENT ACTIVITY{Colors.END}")
    print(f"{'-'*70}")
    
    with engine.connect() as conn:
        try:
            # Recent inserts/updates
            query = text("""
                SELECT 
                    DATE(created_at) as date,
                    source,
                    COUNT(*) as records
                FROM climate_data
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(created_at), source
                ORDER BY date DESC, source
                LIMIT 10
            """)
            
            results = conn.execute(query).fetchall()
            
            if results:
                for row in results:
                    date, source, count = row
                    print(f"  {Colors.CYAN}•{Colors.END} {date}  |  {source:20}  |  {count:>6,} records added")
            else:
                print(f"  {Colors.YELLOW}No recent activity in the last 7 days{Colors.END}")
        
        except Exception as e:
            print(f"  {Colors.RED}Error fetching activity: {e}{Colors.END}")
    
    print()


def get_database_stats(engine):
    """Get database statistics."""
    print(f"{Colors.BOLD}💾 DATABASE STATISTICS{Colors.END}")
    print(f"{'-'*70}")
    
    with engine.connect() as conn:
        try:
            # Total records
            query = text("SELECT COUNT(*) FROM climate_data")
            total = conn.execute(query).scalar()
            print(f"  Total Records: {Colors.GREEN}{total:,}{Colors.END}")
            
            # Date range
            query = text("SELECT MIN(date), MAX(date) FROM climate_data")
            earliest, latest = conn.execute(query).fetchone()
            if earliest and latest:
                print(f"  Date Range: {Colors.CYAN}{earliest} to {latest}{Colors.END}")
                years = (latest.year - earliest.year)
                months = years * 12 + (latest.month - earliest.month)
                print(f"  Coverage: {Colors.CYAN}{years} years, {months} months{Colors.END}")
            
            # Database size (PostgreSQL specific)
            try:
                db_name = os.getenv("POSTGRES_DB", "climate_dev")
                query = text(f"""
                    SELECT pg_size_pretty(pg_database_size('{db_name}'))
                """)
                size = conn.execute(query).scalar()
                print(f"  Database Size: {Colors.CYAN}{size}{Colors.END}")
            except:
                pass  # Size query may fail on some databases
        
        except Exception as e:
            print(f"  {Colors.RED}Error fetching stats: {e}{Colors.END}")
    
    print()


def get_alerts_status():
    """Get alerts configuration status."""
    print(f"{Colors.BOLD}🔔 ALERTS CONFIGURATION{Colors.END}")
    print(f"{'-'*70}")
    
    slack_enabled = os.getenv("ALERT_SLACK_ENABLED", "false").lower() == "true"
    email_enabled = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"
    
    if slack_enabled:
        webhook = os.getenv("ALERT_SLACK_WEBHOOK_URL", "")
        if webhook and webhook != "https://hooks.slack.com/services/YOUR/WEBHOOK/URL":
            print(f"  {Colors.GREEN}✓ Slack Alerts: ENABLED{Colors.END}")
        else:
            print(f"  {Colors.YELLOW}⚠ Slack Alerts: ENABLED but webhook not configured{Colors.END}")
    else:
        print(f"  {Colors.YELLOW}✗ Slack Alerts: DISABLED{Colors.END}")
    
    if email_enabled:
        print(f"  {Colors.GREEN}✓ Email Alerts: ENABLED{Colors.END}")
    else:
        print(f"  {Colors.YELLOW}✗ Email Alerts: DISABLED{Colors.END}")
    
    print()


def print_quick_actions():
    """Print quick action commands."""
    print(f"{Colors.BOLD}⚡ QUICK ACTIONS{Colors.END}")
    print(f"{'-'*70}")
    print(f"  Run pipeline:         python scripts/run_processing_pipeline.py")
    print(f"  Check health:         python scripts/monitor_pipeline_health.py")
    print(f"  Validate quality:     python scripts/validate_data_quality.py")
    print(f"  Test Slack alerts:    python -c \"from utils.slack_notifier import send_test_notification; send_test_notification()\"")
    print()


def main():
    """Main execution function."""
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print(f"{Colors.RED}❌ DATABASE_URL not set in environment{Colors.END}")
        sys.exit(1)
    
    try:
        engine = create_engine(db_url)
        
        print_header()
        get_data_sources_status(engine)
        get_recent_activity(engine)
        get_database_stats(engine)
        get_alerts_status()
        print_quick_actions()
        
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    except Exception as e:
        print(f"{Colors.RED}❌ Error generating dashboard: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
