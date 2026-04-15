"""
Slack Notification Utility

Sends formatted notifications to Slack for pipeline monitoring and alerts.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class AlertSeverity(Enum):
    """Alert severity levels with associated colors and emojis."""
    INFO = ("good", "ℹ️", "#36a64f")  # Green
    SUCCESS = ("good", "✅", "#2eb886")  # Green
    WARNING = ("warning", "⚠️", "#ff9900")  # Orange
    ERROR = ("danger", "❌", "#cc0000")  # Red
    CRITICAL = ("danger", "🚨", "#990000")  # Dark red


def send_slack_notification(
    webhook_url: str,
    message: str,
    severity: AlertSeverity = AlertSeverity.INFO,
    title: Optional[str] = None,
    fields: Optional[List[Dict[str, str]]] = None,
    footer: Optional[str] = None
) -> bool:
    """
    Send a formatted notification to Slack.
    
    Args:
        webhook_url: Slack webhook URL
        message: Main message text
        severity: Alert severity level
        title: Optional title for the message
        fields: Optional list of field dicts with 'title' and 'value'
        footer: Optional footer text
    
    Returns:
        True if notification sent successfully, False otherwise
    """
    if not REQUESTS_AVAILABLE:
        print(f"[Slack] requests library not available. Message: {message}")
        return False
    
    if not webhook_url or webhook_url == "https://hooks.slack.com/services/YOUR/WEBHOOK/URL":
        print(f"[Slack] Webhook URL not configured. Message: {message}")
        return False
    
    # Build Slack message payload
    emoji, _, color = severity.value
    
    attachment = {
        "color": color,
        "text": message,
        "footer": footer or "Climate Prediction Pipeline",
        "ts": int(datetime.now().timestamp())
    }
    
    if title:
        attachment["title"] = f"{emoji} {title}"
    
    if fields:
        attachment["fields"] = [
            {
                "title": field.get("title", ""),
                "value": field.get("value", ""),
                "short": field.get("short", True)
            }
            for field in fields
        ]
    
    payload = {
        "attachments": [attachment]
    }
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[Slack] ✓ Notification sent: {title or message[:50]}")
            return True
        else:
            print(f"[Slack] ✗ Failed to send notification. Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"[Slack] ✗ Error sending notification: {e}")
        return False


def format_pipeline_status(
    status: str,
    sources_fetched: Dict[str, int],
    duration_seconds: float,
    errors: Optional[List[str]] = None
) -> Dict:
    """
    Format pipeline status update for Slack.
    
    Args:
        status: Overall status ("success", "partial", "failed")
        sources_fetched: Dict mapping source name to record count
        duration_seconds: Pipeline duration in seconds
        errors: List of error messages (if any)
    
    Returns:
        Dict with formatted message components
    """
    # Determine severity
    if status == "success":
        severity = AlertSeverity.SUCCESS
        title = "Pipeline Run Completed Successfully"
    elif status == "partial":
        severity = AlertSeverity.WARNING
        title = "Pipeline Run Completed with Warnings"
    else:
        severity = AlertSeverity.ERROR
        title = "Pipeline Run Failed"
    
    # Format sources summary
    sources_summary = "\n".join([
        f"• {source}: {count:,} records"
        for source, count in sources_fetched.items()
    ])
    
    total_records = sum(sources_fetched.values())
    
    # Build message
    message = f"*Data Sources Processed:*\n{sources_summary}\n\n"
    message += f"*Total Records:* {total_records:,}\n"
    message += f"*Duration:* {duration_seconds:.1f} seconds"
    
    if errors:
        message += f"\n\n*Errors:*\n" + "\n".join([f"• {err}" for err in errors])
    
    # Build fields
    fields = [
        {"title": "Status", "value": status.upper(), "short": True},
        {"title": "Duration", "value": f"{duration_seconds:.1f}s", "short": True},
        {"title": "Total Records", "value": f"{total_records:,}", "short": True},
        {"title": "Sources", "value": str(len(sources_fetched)), "short": True}
    ]
    
    return {
        "severity": severity,
        "title": title,
        "message": message,
        "fields": fields
    }


def format_error_alert(
    error_type: str,
    error_message: str,
    source: Optional[str] = None,
    traceback: Optional[str] = None
) -> Dict:
    """
    Format error alert for Slack.
    
    Args:
        error_type: Type of error (e.g., "APIError", "DatabaseError")
        error_message: Error message
        source: Data source that failed (if applicable)
        traceback: Optional stack trace
    
    Returns:
        Dict with formatted message components
    """
    title = f"Error: {error_type}"
    if source:
        title += f" ({source})"
    
    message = f"*Error Message:*\n```{error_message}```"
    
    if traceback:
        # Truncate long tracebacks
        if len(traceback) > 500:
            traceback = traceback[:500] + "...\n[truncated]"
        message += f"\n\n*Stack Trace:*\n```{traceback}```"
    
    fields = [
        {"title": "Error Type", "value": error_type, "short": True}
    ]
    
    if source:
        fields.append({"title": "Data Source", "value": source, "short": True})
    
    return {
        "severity": AlertSeverity.ERROR,
        "title": title,
        "message": message,
        "fields": fields
    }


def format_data_quality_alert(
    source: str,
    issue_type: str,
    details: str,
    affected_records: int,
    severity: str = "warning"
) -> Dict:
    """
    Format data quality alert for Slack.
    
    Args:
        source: Data source with quality issue
        issue_type: Type of issue (e.g., "Missing Data", "Outliers")
        details: Detailed description
        affected_records: Number of affected records
        severity: "warning" or "critical"
    
    Returns:
        Dict with formatted message components
    """
    alert_severity = AlertSeverity.WARNING if severity == "warning" else AlertSeverity.CRITICAL
    
    title = f"Data Quality Issue: {source}"
    
    message = f"*Issue Type:* {issue_type}\n"
    message += f"*Details:* {details}\n"
    message += f"*Affected Records:* {affected_records:,}"
    
    fields = [
        {"title": "Source", "value": source, "short": True},
        {"title": "Issue Type", "value": issue_type, "short": True},
        {"title": "Severity", "value": severity.upper(), "short": True},
        {"title": "Affected Records", "value": f"{affected_records:,}", "short": True}
    ]
    
    return {
        "severity": alert_severity,
        "title": title,
        "message": message,
        "fields": fields
    }


def send_pipeline_status_notification(
    webhook_url: str,
    status: str,
    sources_fetched: Dict[str, int],
    duration_seconds: float,
    errors: Optional[List[str]] = None
) -> bool:
    """
    Send pipeline status notification to Slack.
    
    Convenience function combining formatting and sending.
    """
    formatted = format_pipeline_status(status, sources_fetched, duration_seconds, errors)
    
    return send_slack_notification(
        webhook_url=webhook_url,
        message=formatted["message"],
        severity=formatted["severity"],
        title=formatted["title"],
        fields=formatted.get("fields")
    )


def send_error_alert(
    webhook_url: str,
    error_type: str,
    error_message: str,
    source: Optional[str] = None,
    traceback: Optional[str] = None
) -> bool:
    """
    Send error alert to Slack.
    
    Convenience function combining formatting and sending.
    """
    formatted = format_error_alert(error_type, error_message, source, traceback)
    
    return send_slack_notification(
        webhook_url=webhook_url,
        message=formatted["message"],
        severity=formatted["severity"],
        title=formatted["title"],
        fields=formatted.get("fields")
    )


def send_data_quality_alert(
    webhook_url: str,
    source: str,
    issue_type: str,
    details: str,
    affected_records: int,
    severity: str = "warning"
) -> bool:
    """
    Send data quality alert to Slack.
    
    Convenience function combining formatting and sending.
    """
    formatted = format_data_quality_alert(source, issue_type, details, affected_records, severity)
    
    return send_slack_notification(
        webhook_url=webhook_url,
        message=formatted["message"],
        severity=formatted["severity"],
        title=formatted["title"],
        fields=formatted.get("fields")
    )


def send_test_notification(webhook_url: Optional[str] = None) -> bool:
    """
    Send a test notification to verify Slack integration.
    
    Args:
        webhook_url: Slack webhook URL (uses env var if not provided)
    
    Returns:
        True if successful
    """
    if webhook_url is None:
        webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ No Slack webhook URL provided or found in environment")
        return False
    
    return send_slack_notification(
        webhook_url=webhook_url,
        message="Slack integration is working correctly! 🎉",
        severity=AlertSeverity.SUCCESS,
        title="Test Notification",
        fields=[
            {"title": "Timestamp", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "short": True},
            {"title": "Environment", "value": "Development", "short": True}
        ]
    )


# Example usage
if __name__ == "__main__":
    # Test notification
    print("Testing Slack notification...")
    success = send_test_notification()
    
    if success:
        print("✅ Test notification sent successfully!")
    else:
        print("❌ Failed to send test notification. Check your webhook URL.")
