"""
Test Alert Delivery Script

Tests email and Slack alert delivery for the pipeline monitoring system.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.pipeline.alert_service import AlertService
from app.core.config import settings


def test_email_alerts():
    """Test email alert delivery"""
    print("\n=== Testing Email Alerts ===")
    
    if not settings.ALERT_EMAIL_ENABLED:
        print("❌ Email alerts are disabled in configuration")
        print("   Set ALERT_EMAIL_ENABLED=true to enable")
        return False
    
    print(f"✓ Email alerts enabled")
    print(f"  SMTP Host: {settings.ALERT_EMAIL_SMTP_HOST}")
    print(f"  SMTP Port: {settings.ALERT_EMAIL_SMTP_PORT}")
    print(f"  From: {settings.ALERT_EMAIL_FROM}")
    print(f"  Recipients: {settings.ALERT_EMAIL_RECIPIENTS}")
    
    alert_service = AlertService()
    
    try:
        print("\nSending test email...")
        # Testing email alert using a pseudo pipeline failure pattern since send_email is private
        alert_service.send_pipeline_failure(
            execution_id="test-email-execution",
            error=Exception("Test Error for Email"),
        )
        print("✓ Test email sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False


def test_slack_alerts():
    """Test Slack alert delivery"""
    print("\n=== Testing Slack Alerts ===")
    
    if not settings.ALERT_SLACK_ENABLED:
        print("❌ Slack alerts are disabled in configuration")
        print("   Set ALERT_SLACK_ENABLED=true to enable")
        return False
    
    print(f"✓ Slack alerts enabled")
    print(f"  Webhook URL: {settings.ALERT_SLACK_WEBHOOK_URL[:50]}...")
    
    alert_service = AlertService()
    
    try:
        print("\nSending test Slack message...")
        # Using partial failure to test slack since we just want to fire any alert message through it
        alert_service.send_partial_failure_alert(
            execution_id="test-slack-execution",
            failed_sources=["Test slack"],
            succeeded_sources=["Test slack"]
        )
        print("✓ Test Slack message sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send test Slack message: {e}")
        return False


def test_pipeline_failure_alert():
    """Test pipeline failure alert"""
    print("\n=== Testing Pipeline Failure Alert ===")
    
    alert_service = AlertService()
    
    try:
        print("\nSending test pipeline failure alert...")
        alert_service.send_pipeline_failure(
            execution_id="test-execution-123",
            error=Exception("This is a test pipeline failure alert"),
            affected_components=["test-source-1", "test-source-2"],
        )
        print("✓ Pipeline failure alert sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send pipeline failure alert: {e}")
        return False


def test_staleness_alert():
    """Test data staleness alert"""
    print("\n=== Testing Staleness Alert ===")
    
    alert_service = AlertService()
    
    try:
        print("\nSending test staleness alert...")
        from datetime import date
        alert_service.send_data_staleness_alert(
            source="Test Data",
            last_date=date.today(),
            days_old=10
        )
        print("✓ Staleness alert sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send staleness alert: {e}")
        return False


def main():
    """Run all alert tests"""
    print("=" * 60)
    print("Climate Early Warning System - Alert Delivery Test")
    print("=" * 60)
    
    results = {
        "email": test_email_alerts(),
        "slack": test_slack_alerts(),
        "pipeline_failure": test_pipeline_failure_alert(),
        "staleness": test_staleness_alert()
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n✓ All alert tests passed!")
        return 0
    else:
        print(f"\n❌ {total_tests - total_passed} alert test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
