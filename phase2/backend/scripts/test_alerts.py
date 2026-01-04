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

from app.services.pipeline.alerts import AlertService
from app.core.config import settings


async def test_email_alerts():
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
        await alert_service.send_email_alert(
            subject="Test Alert - Climate EWS",
            body="This is a test alert from the Climate Early Warning System.\n\n"
                 "If you receive this email, email alerts are configured correctly.",
            alert_type="test"
        )
        print("✓ Test email sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False


async def test_slack_alerts():
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
        await alert_service.send_slack_alert(
            title="Test Alert - Climate EWS",
            message="This is a test alert from the Climate Early Warning System.\n\n"
                    "If you receive this message, Slack alerts are configured correctly.",
            severity="info",
            alert_type="test"
        )
        print("✓ Test Slack message sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send test Slack message: {e}")
        return False


async def test_pipeline_failure_alert():
    """Test pipeline failure alert"""
    print("\n=== Testing Pipeline Failure Alert ===")
    
    alert_service = AlertService()
    
    try:
        print("\nSending test pipeline failure alert...")
        await alert_service.send_pipeline_failure_alert(
            execution_id="test-execution-123",
            error_message="This is a test pipeline failure alert",
            failed_sources=["test-source-1", "test-source-2"],
            duration_seconds=120
        )
        print("✓ Pipeline failure alert sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send pipeline failure alert: {e}")
        return False


async def test_staleness_alert():
    """Test data staleness alert"""
    print("\n=== Testing Staleness Alert ===")
    
    alert_service = AlertService()
    
    try:
        print("\nSending test staleness alert...")
        await alert_service.send_staleness_alert(
            data_age_days=10,
            forecast_age_days=8
        )
        print("✓ Staleness alert sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send staleness alert: {e}")
        return False


async def main():
    """Run all alert tests"""
    print("=" * 60)
    print("Climate Early Warning System - Alert Delivery Test")
    print("=" * 60)
    
    results = {
        "email": await test_email_alerts(),
        "slack": await test_slack_alerts(),
        "pipeline_failure": await test_pipeline_failure_alert(),
        "staleness": await test_staleness_alert()
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
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
