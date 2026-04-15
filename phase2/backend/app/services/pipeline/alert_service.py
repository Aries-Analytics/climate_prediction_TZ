"""
Alert Service

Multi-channel alerting for pipeline failures, data staleness, and quality issues.
Supports rich Slack formatting per SLACK_ALERT_STRATEGY.md.
"""
import logging
import smtplib
import requests
from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
import pytz

logger = logging.getLogger(__name__)

# East Africa Time zone (UTC+3)
EAT_TZ = pytz.timezone('Africa/Dar_es_Salaam')

# Pilot context constants (from persona_config.yaml)
PILOT_REGION = "Kilombero Basin (Ifakara TC + Mlimba DC)"
PILOT_CROP = "Rice"
PILOT_FARMERS = 1_000

# Source display names
SOURCE_DISPLAY_NAMES = {
    'chirps': 'CHIRPS',
    'nasa_power': 'NASA POWER',
    'era5': 'ERA5',
    'ndvi': 'NDVI',
    'ocean_indices': 'Ocean Indices',
}


@dataclass
class Alert:
    """Alert message structure"""
    severity: str  # 'critical' | 'warning' | 'info' | 'success'
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
    - Slack notifications via webhook (with rich Block Kit formatting)
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
    
    # ── Rich pipeline alerts ──────────────────────────────────────────
    
    def send_pipeline_success_alert(
        self,
        execution_id: str,
        duration_seconds: int,
        sources_succeeded: List[str],
        sources_failed: List[str],
        records_stored: int,
        forecasts_generated: int,
        execution_type: str = 'scheduled',
        db=None,
        next_run_time: Optional[str] = None,
        per_source_records: Optional[Dict[str, int]] = None,
    ) -> None:
        """
        Send rich success alert matching SLACK_ALERT_STRATEGY.md format.
        
        Queries DB for per-source quality metrics and total record count
        when a db session is provided.  Falls back to per_source_records
        dict passed directly from the orchestrator.
        """
        now_eat = datetime.now(timezone.utc).astimezone(EAT_TZ)
        date_str = now_eat.strftime('%A, %B %d, %Y — %H:%M EAT')
        
        # ── Gather enrichment data from DB ──
        quality_score = None
        source_records: Dict[str, int] = dict(per_source_records or {})
        total_db_records: Optional[int] = None
        forecast_log_count: Optional[int] = None
        
        if db is not None:
            try:
                from app.models.pipeline_execution import DataQualityMetrics
                from app.models.climate_data import ClimateData
                from app.models.forecast_log import ForecastLog
                from sqlalchemy import func

                # Per-source record counts from this execution's quality metrics
                quality_rows = (
                    db.query(DataQualityMetrics)
                    .filter(DataQualityMetrics.execution_id == execution_id)
                    .all()
                )
                scores = []
                for qm in quality_rows:
                    source_records[qm.source] = qm.total_records
                    if qm.quality_score is not None:
                        scores.append(float(qm.quality_score))

                if scores:
                    quality_score = round(sum(scores) / len(scores) * 100)

                # Total climate data records (reference data, not tracked for shadow run)
                total_db_records = db.query(func.count(ClimateData.id)).scalar()

                # ForecastLog count — the shadow run KPI (from start date only)
                from app.config.shadow_run import SHADOW_RUN_START
                forecast_log_count = db.query(func.count(ForecastLog.id)).filter(
                    func.date(ForecastLog.issued_at) >= SHADOW_RUN_START
                ).scalar()
            except Exception as e:
                logger.warning(f"Failed to query enrichment data for success alert: {e}")
        
        # ── Fallback quality score from ingestion success rate ──
        total_sources = len(sources_succeeded) + len(sources_failed)
        if quality_score is None and total_sources > 0:
            quality_score = round(len(sources_succeeded) / total_sources * 100)
        
        # ── Build ingestion lines ──
        # Sources that returned 0 records are shown with ⚠️ — they didn't fail
        # (no exception raised) but also produced no data, which warrants attention.
        ingestion_lines = []
        for src in sources_succeeded:
            display = SOURCE_DISPLAY_NAMES.get(src, src.upper())
            count = source_records.get(src)
            if count is not None and count == 0:
                ingestion_lines.append(f"⚠️ {display}: 0 records (fetch returned empty)")
            elif count is not None:
                ingestion_lines.append(f"✓ {display}: {count} records")
            else:
                ingestion_lines.append(f"✓ {display}")
        for src in sources_failed:
            display = SOURCE_DISPLAY_NAMES.get(src, src.upper())
            ingestion_lines.append(f"✗ {display}: FAILED")
        
        ingestion_text = "\n".join(ingestion_lines) if ingestion_lines else "No sources"
        
        # ── Quality line ──
        if quality_score is not None:
            q_emoji = "✅" if quality_score >= 80 else ("⚠️" if quality_score >= 50 else "🚨")
            quality_line = f"Score: {quality_score}% {q_emoji}"
        else:
            quality_line = "Score: N/A"
        
        # ── Shadow run progress line ──
        from app.config.shadow_run import SHADOW_RUN_TARGET_FORECASTS
        if forecast_log_count is not None:
            pct = forecast_log_count / SHADOW_RUN_TARGET_FORECASTS * 100
            db_line = f"Shadow Run: {forecast_log_count} / {SHADOW_RUN_TARGET_FORECASTS} forecasts ({pct:.1f}%)"
        else:
            db_line = "Shadow Run: N/A"
        
        # ── Next run ──
        next_run_line = f"_Next run: {next_run_time}_" if next_run_time else ""
        
        # ── Duration ──
        if duration_seconds and duration_seconds >= 60:
            dur_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"
        else:
            dur_str = f"{duration_seconds}s" if duration_seconds else "N/A"
        
        # ── Build rich Slack text ──
        text_body = (
            f"✅ *Tanzania Climate Pipeline — Daily Summary*\n"
            f"_{date_str}_\n\n"
            f"*Execution Status*\n"
            f"Status: ✅ SUCCESS\n"
            f"Duration: {dur_str}\n"
            f"Trigger: {execution_type.capitalize()}\n\n"
            f"*Data Ingestion — {sum(1 for s in sources_succeeded if source_records.get(s, 0) > 0)} sources updated, "
            f"{sum(1 for s in sources_succeeded if source_records.get(s, 0) == 0)} current*\n"
            f"{ingestion_text}\n\n"
            f"*Forecast Generation*\n"
            f"Total: {forecasts_generated} forecasts\n"
            f"Location: {PILOT_REGION} — Pilot\n"
            f"Crop: {PILOT_CROP} | Farmers: {PILOT_FARMERS:,}\n\n"
            f"*Data Quality*\n"
            f"{quality_line}\n\n"
            f"*System Health*\n"
            f"{db_line}\n"
        )
        if next_run_line:
            text_body += f"\n{next_run_line}"
        
        # Also log normally
        logger.info(f"Pipeline SUCCESS alert: {execution_id}, {forecasts_generated} forecasts, {dur_str}")
        
        # Send via Slack
        if self.slack_enabled:
            try:
                self._send_rich_slack_alert(
                    text=text_body,
                    color='#36A64F',  # Green
                    footer_text=f"Execution ID: {execution_id}",
                )
            except Exception as e:
                logger.error(f"Failed to send rich Slack success alert: {e}")
        
        # Also send email if enabled
        if self.email_enabled:
            try:
                plain_alert = Alert(
                    severity='success',
                    title='Pipeline Execution Completed',
                    message=text_body.replace('*', '').replace('_', ''),
                    timestamp=datetime.now(timezone.utc),
                    affected_components=['pipeline'],
                    execution_id=execution_id,
                )
                self._send_email_alert(plain_alert)
            except Exception as e:
                logger.error(f"Failed to send email success alert: {e}")
    
    def send_shadow_run_complete_alert(
        self,
        valid_run_days: int,
        total_forecasts: int,
        brier_score: Optional[float],
        brier_gate_pass: Optional[bool],
        basis_risk_pct: Optional[float],
        basis_gate_pass: Optional[bool],
        basis_risk_detail: Optional[Dict[str, Any]] = None,
        overall_verdict: str = "PENDING",
    ) -> None:
        """
        Send shadow run completion alert with go/no-go gate results.

        Called once when valid_run_days reaches 90.  Both Brier Score and
        NDVI proxy basis risk are reported.  If basis risk data is insufficient
        (no evaluated primary-tier triggers yet), the gate is marked pending.
        """
        now_eat = datetime.now(timezone.utc).astimezone(EAT_TZ)
        date_str = now_eat.strftime('%A, %B %d, %Y — %H:%M EAT')

        # ── Brier Score line ──
        if brier_score is not None:
            brier_emoji = "✅" if brier_gate_pass else "❌"
            brier_status = "PASS" if brier_gate_pass else "FAIL"
            brier_line = f"{brier_emoji} Brier Score: {brier_score:.4f} (gate: < 0.25) — {brier_status}"
        else:
            brier_line = "⏳ Brier Score: Not yet available (forecasts still maturing)"

        # ── Basis risk line ──
        if basis_risk_pct is not None:
            basis_emoji = "✅" if basis_gate_pass else "❌"
            basis_status = "PASS" if basis_gate_pass else "FAIL"
            corroborated = (basis_risk_detail or {}).get("corroborated", "?")
            total_primary = (basis_risk_detail or {}).get("total_primary", "?")
            basis_line = (
                f"{basis_emoji} Basis Risk (NDVI proxy): {basis_risk_pct:.1f}% "
                f"(gate: < 30%) — {basis_status}\n"
                f"   _{corroborated}/{total_primary} primary triggers corroborated by satellite vegetation_"
            )
        else:
            basis_line = (
                "⏳ Basis Risk (NDVI proxy): Insufficient evaluated triggers\n"
                "   _Harvest survey required for verified ground truth_"
            )

        # ── Verdict colour ──
        if overall_verdict.startswith("GO"):
            verdict_emoji = "✅"
            color = "#36A64F"
        elif overall_verdict.startswith("NO-GO"):
            verdict_emoji = "❌"
            color = "#FF0000"
        else:
            verdict_emoji = "⏳"
            color = "#FFA500"

        from app.config.shadow_run import SHADOW_RUN_TARGET_DAYS as _TARGET_DAYS
        from app.config.shadow_run import SHADOW_RUN_TARGET_FORECASTS as _TARGET_FC
        text_body = (
            f"🏁 *HewaSense Shadow Run Complete — {_TARGET_DAYS} Valid Run-Days*\n"
            f"_{date_str}_\n\n"
            f"*Shadow Run Summary*\n"
            f"Valid run-days: {valid_run_days} / {_TARGET_DAYS} ✅\n"
            f"Total forecasts logged: {total_forecasts} / {_TARGET_FC:,}\n\n"
            f"*Go / No-Go Gates*\n"
            f"{brier_line}\n"
            f"{basis_line}\n\n"
            f"*Overall Verdict*\n"
            f"{verdict_emoji} {overall_verdict}\n\n"
            f"*Next Steps*\n"
            f"1. Download Evidence Pack from dashboard for full metrics\n"
            f"2. Conduct harvest survey (30-50 farmers) for verified basis risk\n"
            f"3. Go/No-Go decision meeting with partner underwriter\n"
        )

        logger.info(f"Shadow run complete alert: verdict={overall_verdict}")

        if self.slack_enabled:
            try:
                self._send_rich_slack_alert(
                    text=text_body,
                    color=color,
                    footer_text="HewaSense — Shadow Run Completion Report",
                )
            except Exception as e:
                logger.error(f"Failed to send shadow run complete Slack alert: {e}")

    def send_pipeline_failure_rich_alert(
        self,
        execution_id: str,
        error_message: str,
        duration_seconds: Optional[int] = None,
        sources_succeeded: Optional[List[str]] = None,
        sources_failed: Optional[List[str]] = None,
        failed_stage: str = "Unknown",
        forecasts_generated: int = 0,
    ) -> None:
        """
        Send rich failure alert matching SLACK_ALERT_STRATEGY.md format.
        
        Includes what succeeded before failure, error details, impact, and actions.
        """
        now_eat = datetime.now(timezone.utc).astimezone(EAT_TZ)
        date_str = now_eat.strftime('%A, %B %d, %Y — %H:%M EAT')
        
        sources_succeeded = sources_succeeded or []
        sources_failed = sources_failed or []
        
        # Duration
        if duration_seconds and duration_seconds >= 60:
            dur_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"
        else:
            dur_str = f"{duration_seconds}s" if duration_seconds else "N/A"
        
        # What succeeded
        succeeded_lines = []
        if sources_succeeded:
            succeeded_lines.append(f"✅ Data Ingestion: {len(sources_succeeded)}/{len(sources_succeeded) + len(sources_failed)} sources")
        if forecasts_generated > 0:
            succeeded_lines.append(f"✅ Forecasts: {forecasts_generated} generated before failure")
        succeeded_text = "\n".join(succeeded_lines) if succeeded_lines else "None"
        
        # Failed sources
        failed_src_text = ""
        if sources_failed:
            failed_names = [SOURCE_DISPLAY_NAMES.get(s, s.upper()) for s in sources_failed]
            failed_src_text = f"\nFailed Sources: {', '.join(failed_names)}"
        
        text_body = (
            f"❌ *PIPELINE FAILURE — Immediate Action Required*\n"
            f"_{date_str}_\n\n"
            f"*Execution Details*\n"
            f"Status: ❌ FAILED\n"
            f"Duration: {dur_str} (before failure)\n"
            f"Failed At: {failed_stage} Stage\n\n"
            f"*What Succeeded*\n"
            f"{succeeded_text}\n\n"
            f"*Failure Details*\n"
            f"Error: `{error_message}`{failed_src_text}\n\n"
            f"*Impact*\n"
            f"🚫 No new forecasts generated today\n"
            f"⚠️ Previous forecasts still available\n"
            f"📊 Dashboard showing stale data\n\n"
            f"*Immediate Actions*\n"
            f"1. Check logs: `docker-compose logs scheduler`\n"
            f"2. Manual retry: `python -m app.cli pipeline run`\n\n"
            f"*Auto-Recovery*\n"
            f"⏰ Will retry tomorrow at 06:00 AM EAT\n"
        )
        
        logger.error(f"Pipeline FAILURE alert: {execution_id}, error={error_message}")
        
        if self.slack_enabled:
            try:
                self._send_rich_slack_alert(
                    text=text_body,
                    color='#FF0000',  # Red
                    footer_text=f"Execution ID: {execution_id}",
                )
            except Exception as e:
                logger.error(f"Failed to send rich Slack failure alert: {e}")
        
        if self.email_enabled:
            try:
                plain_alert = Alert(
                    severity='critical',
                    title='Pipeline Execution FAILED',
                    message=text_body.replace('*', '').replace('_', '').replace('`', ''),
                    timestamp=datetime.now(timezone.utc),
                    affected_components=sources_failed or ['pipeline'],
                    error_details=error_message,
                    execution_id=execution_id,
                )
                self._send_email_alert(plain_alert)
            except Exception as e:
                logger.error(f"Failed to send email failure alert: {e}")
    
    # ── Legacy alert methods (unchanged) ──────────────────────────────
    
    def send_pipeline_failure(
        self,
        execution_id: str,
        error: Exception,
        affected_components: Optional[List[str]] = None
    ) -> None:
        """
        Send critical alert for pipeline failure (legacy / simple format)
        
        Args:
            execution_id: Pipeline execution ID
            error: Exception that caused failure
            affected_components: List of affected components
        """
        alert = Alert(
            severity='critical',
            title='Pipeline Execution Failed',
            message=f'Pipeline execution {execution_id} failed with error: {str(error)}',
            timestamp=datetime.now(timezone.utc),
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
            timestamp=datetime.now(timezone.utc),
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
            timestamp=datetime.now(timezone.utc),
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
            timestamp=datetime.now(timezone.utc),
            affected_components=[source, 'data_quality'],
            error_details='\n'.join(issues),
            execution_id=execution_id
        )
        self.send_alert(alert)
    
    # ── Internal transport methods ────────────────────────────────────
    
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
        """Send alert via Slack webhook (legacy attachment format)"""
        if not self.slack_webhook_url:
            return
        
        # Determine color based on severity
        color_map = {
            'critical': '#FF0000',  # Red
            'warning': '#FFA500',   # Orange
            'info': '#0000FF',      # Blue
            'success': '#36A64F',   # Green
        }
        
        # Convert timestamp to East Africa Time (EAT)
        eat_time = alert.timestamp.astimezone(EAT_TZ)
        
        # Build Slack message payload matching the working format
        attachment = {
            'color': color_map.get(alert.severity, '#808080'),
            'text': alert.message,
            'title': f"[{alert.severity.upper()}] {alert.title}",
            'footer': 'Climate Forecast Pipeline',
            'ts': int(alert.timestamp.timestamp()),
            'fields': [
                {
                    'title': 'Affected Components',
                    'value': ', '.join(alert.affected_components),
                    'short': False
                },
                {
                    'title': 'Timestamp',
                    'value': f"{eat_time.strftime('%Y-%m-%d %H:%M:%S')} EAT",
                    'short': True
                }
            ]
        }
        
        payload = {
            "attachments": [attachment]
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
    
    def _send_rich_slack_alert(
        self,
        text: str,
        color: str = '#36A64F',
        footer_text: str = '',
    ) -> None:
        """
        Send a rich Slack alert using attachment with mrkdwn text.
        
        Uses the attachment format (compatible with all Slack webhook types)
        with rich mrkdwn-formatted text body for the daily summary look.
        
        Args:
            text: Full mrkdwn-formatted message body
            color: Sidebar color hex
            footer_text: Footer line (e.g. execution ID)
        """
        if not self.slack_webhook_url:
            return
        
        payload: Dict[str, Any] = {
            "attachments": [
                {
                    "color": color,
                    "mrkdwn_in": ["text"],
                    "text": text,
                    "footer": f"Climate Forecast Pipeline | {footer_text}" if footer_text else "Climate Forecast Pipeline",
                    "ts": int(datetime.now(timezone.utc).timestamp()),
                }
            ]
        }
        
        response = requests.post(
            self.slack_webhook_url,
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        logger.info("Rich Slack alert sent successfully")
