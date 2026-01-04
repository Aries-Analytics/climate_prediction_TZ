"""
Alert Service

Multi-channel alerting for pipeline failures, data staleness, and quality issues.
"""
import logging
import smtplib
import requests
from datetime import date, datetime
from typing import List, Optional, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Alert message structure"""
    severity: str  # 'critical' | 'warning' | 'info'
    title: str
    message: str
    timestamp: datetime
    affected_components: List[str]
    error_details: Optional[str] = None
    execution_id: Optional[str] = None


class AlertService:
    """
    Multi-channel alert service for pipeline notifications.
    
    Supports:
    - Email alerts via SMTP
    - Slack notifications via webhook
    - Structured logging
    """
    
    def __init__(
        self,
        email_enabled: bool = False,
        email_config: Optional[Dict] = None,
        slack_enabled: bool = False,
        slack_webhook_url: Optional[str] = None
    ):
        """
        Initialize alert service
        
        Args:
            email_enabled: Enable email alerts
            email_config: SMTP configuration dict
            slack_enabled: Enable Slack alerts
            slack_webhook_url: Slack webhook URL
        """
        self.email_enabled = email_enabled
        self.email_config = email_config or {}
        self.slack_enabled = slack_enabled
        self.slack_webhook_url = slack_webhook_url
    
    def send_alert(self, alert: Alert) -> None:
        """
        Send alert to all configured channels
        
        Args:
            alert: Alert to send
        """
        logger.info(f"Sending {alert.severity} alert: {alert.title}")
        
        # Always log the alert
        self._log_alert(alert)
        
        # Send to email if enabled
        if self.email_enabled:
            try:
                self._send_email_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
        
        # Send to Slack if enabled
        if self.slack_enabled:
            try:
                self._send_slack_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")
    
    def send_pipeline_failure(
        self,
        execution_id: str,
        error: Exception,
        affected_components: Optional[List[str]] = None
    ) -> None:
        """
        Send critical alert for pipeline failure
        
        Args:
            execution_id: Pipeline execution ID
            error: Exception that caused failure
            affected_components: List of affected components
        """
        alert = Alert(
            severity='critical',
            title='Pipeline Execution Failed',
            message=f'Pipeline execution {execution_id} failed with error: {str(error)}',
            timestamp=datetime.now(),
            affected_components=affected_components or ['pipeline'],
            error_details=str(error),
            execution_id=execution_id
        )
        self.send_alert(alert)
    
    def send_data_staleness_alert(self, source: str, last_date: date, days_old: int) -> None:
        """
        Send warning for stale data
        
        Args:
            source: Data source name
            last_date: Last update date
            days_old: Age in days
        """
        alert = Alert(
            severity='warning',
            title=f'Stale Data Detected: {source}',
            message=f'Data source {source} has not been updated in {days_old} days. Last update: {last_date}',
            timestamp=datetime.now(),
            affected_components=[source, 'data_ingestion']
        )
        self.send_alert(alert)
    
    def send_partial_failure_alert(
        self,
        failed_sources: List[str],
        succeeded_sources: List[str],
        execution_id: str
    ) -> None:
        """
        Send warning for partial ingestion failure
        
        Args:
            failed_sources: List of sources that failed
            succeeded_sources: List of sources that succeeded
            execution_id: Pipeline execution ID
        """
        alert = Alert(
            severity='warning',
            title='Partial Pipeline Failure',
            message=(
                f'Pipeline execution {execution_id} completed with partial failure. '
                f'Failed sources: {", ".join(failed_sources)}. '
                f'Succeeded sources: {", ".join(succeeded_sources)}.'
            ),
            timestamp=datetime.now(),
            affected_components=failed_sources,
            execution_id=execution_id
        )
        self.send_alert(alert)
    
    def send_quality_failure_alert(
        self,
        source: str,
        issues: List[str],
        execution_id: str
    ) -> None:
        """
        Send alert for data quality check failure
        
        Args:
            source: Data source name
            issues: List of quality issues detected
            execution_id: Pipeline execution ID
        """
        alert = Alert(
            severity='warning',
            title=f'Data Quality Issues: {source}',
            message=(
                f'Data quality checks failed for {source}. '
                f'Issues detected: {", ".join(issues)}'
            ),
            timestamp=datetime.now(),
            affected_components=[source, 'data_quality'],
            error_details='\n'.join(issues),
            execution_id=execution_id
        )
        self.send_alert(alert)
    
    def _log_alert(self, alert: Alert) -> None:
        """Log alert with structured format"""
        log_data = {
            'severity': alert.severity,
            'title': alert.title,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'affected_components': alert.affected_components,
            'execution_id': alert.execution_id
        }
        
        if alert.severity == 'critical':
            logger.error(f"ALERT: {log_data}")
        elif alert.severity == 'warning':
            logger.warning(f"ALERT: {log_data}")
        else:
            logger.info(f"ALERT: {log_data}")
    
    def _send_email_alert(self, alert: Alert) -> None:
        """Send alert via email"""
        if not self.email_config:
            return
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.email_config.get('from_address')
        msg['To'] = ', '.join(self.email_config.get('recipients', []))
        msg['Subject'] = f"[{alert.severity.upper()}] {alert.title}"
        
        # Build email body
        body = f"""
Climate Forecast Pipeline Alert

Severity: {alert.severity.upper()}
Title: {alert.title}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{alert.message}

Affected Components:
{', '.join(alert.affected_components)}
"""
        
        if alert.error_details:
            body += f"\n\nError Details:\n{alert.error_details}"
        
        if alert.execution_id:
            body += f"\n\nExecution ID: {alert.execution_id}"
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(
            self.email_config.get('smtp_host'),
            self.email_config.get('smtp_port', 587)
        ) as server:
            server.starttls()
            if self.email_config.get('smtp_user'):
                server.login(
                    self.email_config['smtp_user'],
                    self.email_config['smtp_password']
                )
            server.send_message(msg)
        
        logger.info(f"Email alert sent to {msg['To']}")
    
    def _send_slack_alert(self, alert: Alert) -> None:
        """Send alert via Slack webhook"""
        if not self.slack_webhook_url:
            return
        
        # Determine color based on severity
        color_map = {
            'critical': '#FF0000',  # Red
            'warning': '#FFA500',   # Orange
            'info': '#0000FF'       # Blue
        }
        
        # Build Slack message
        payload = {
            'attachments': [{
                'color': color_map.get(alert.severity, '#808080'),
                'title': f"[{alert.severity.upper()}] {alert.title}",
                'text': alert.message,
                'fields': [
                    {
                        'title': 'Affected Components',
                        'value': ', '.join(alert.affected_components),
                        'short': False
                    },
                    {
                        'title': 'Timestamp',
                        'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        'short': True
                    }
                ],
                'footer': 'Climate Forecast Pipeline',
                'ts': int(alert.timestamp.timestamp())
            }]
        }
        
        if alert.execution_id:
            payload['attachments'][0]['fields'].append({
                'title': 'Execution ID',
                'value': alert.execution_id,
                'short': True
            })
        
        # Send to Slack
        response = requests.post(
            self.slack_webhook_url,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        logger.info("Slack alert sent successfully")
