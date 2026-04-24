"""
Entry point for Pipeline Scheduler Service

Starts the APScheduler service for automated pipeline execution.
"""
import os
import sys
import logging
import signal
from pathlib import Path
from time import sleep
from dotenv import load_dotenv

# Load .env from project root (phase2/)
env_path = Path(__file__).resolve().parents[4] / '.env'
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for scheduler service"""
    logger.info("Starting Pipeline Scheduler Service")
    
    # Load configuration from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    schedule = os.getenv('PIPELINE_SCHEDULE', '0 6 * * *')  # Default: 6 AM EAT
    timezone = os.getenv('PIPELINE_TIMEZONE', 'Africa/Dar_es_Salaam')
    
    # Alert configuration
    alert_email_enabled = os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true'
    alert_slack_enabled = os.getenv('ALERT_SLACK_ENABLED', 'false').lower() == 'true'
    
    logger.info(f"Configuration:")
    logger.info(f"  Schedule: {schedule}")
    logger.info(f"  Timezone: {timezone}")
    logger.info(f"  Email alerts: {alert_email_enabled}")
    logger.info(f"  Slack alerts: {alert_slack_enabled}")
    
    # Initialize alert service if configured
    alert_service = None
    if alert_email_enabled or alert_slack_enabled:
        from app.services.pipeline.alert_service import AlertService
        slack_webhook_url = os.getenv('ALERT_SLACK_WEBHOOK_URL')
        alert_service = AlertService(
            email_enabled=alert_email_enabled,
            slack_enabled=alert_slack_enabled,
            slack_webhook_url=slack_webhook_url
        )
        logger.info(f"Alert service initialized (email={alert_email_enabled}, slack={alert_slack_enabled})")
    
    # Initialize and start scheduler
    from app.services.pipeline.scheduler import PipelineScheduler
    
    scheduler = PipelineScheduler(
        db_url=db_url,
        schedule=schedule,
        timezone=timezone,
        alert_service=alert_service
    )
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        scheduler.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start scheduler
    try:
        scheduler.start()
        
        next_run = scheduler.get_next_run_time()
        if next_run:
            logger.info(f"Next scheduled run: {next_run}")
        
        logger.info("Scheduler service running. Press Ctrl+C to stop.")
        
        # Keep the service running
        while True:
            sleep(60)
            
    except Exception as e:
        logger.error(f"Scheduler service failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
