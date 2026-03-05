import sys
import os
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
from utils.slack_notifier import (
    send_pipeline_status_notification,
    send_error_alert,
    send_data_quality_alert
)

def test_daily_summary(webhook_url):
    print("Testing Daily Summary Alert...")
    return send_pipeline_status_notification(
        webhook_url=webhook_url,
        status="success",
        sources_fetched={
            "CHIRPS": 31,
            "NASA POWER": 31,
            "ERA5": 31,
            "NDVI": 31,
            "Ocean Indices": 31
        },
        duration_seconds=45 * 60
    )

def test_pipeline_failure(webhook_url):
    print("Testing Pipeline Failure Alert...")
    return send_error_alert(
        webhook_url=webhook_url,
        error_type="DatabaseConnectionTimeout",
        error_message="Unable to connect to forecast database after 3 retries",
        source="Forecast Generation",
        traceback="Traceback (most recent call last):\n  File \"pipeline.py\", line 42, in generate_forecasts\n    db.connect()\nTimeoutError"
    )

def test_data_quality_warning(webhook_url):
    print("Testing Data Quality Warning...")
    return send_data_quality_alert(
        webhook_url=webhook_url,
        source="CHIRPS",
        issue_type="Missing Values",
        details="15% missing values (threshold: 10%)",
        affected_records=4,
        severity="warning"
    )

def test_data_quality_critical(webhook_url):
    print("Testing Data Quality Critical...")
    return send_data_quality_alert(
        webhook_url=webhook_url,
        source="NASA POWER",
        issue_type="Failed to fetch",
        details="45% missing values after retries",
        affected_records=14,
        severity="critical"
    )

def main():
    webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL", settings.ALERT_SLACK_WEBHOOK_URL)
    
    if not webhook_url:
        print("❌ Slack webhook URL not configured.")
        return 1
        
    print(f"Using Webhook URL: {webhook_url[:50]}...")
    
    tests = [
        test_daily_summary,
        test_pipeline_failure,
        test_data_quality_warning,
        test_data_quality_critical
    ]
    
    for test in tests:
        test(webhook_url)
        time.sleep(2) # Avoid rate limiting
        
    print("✅ All strategy messages sent!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
