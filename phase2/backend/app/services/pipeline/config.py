"""
Pipeline Configuration Management

Loads and validates configuration from environment variables and config files.
"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Pipeline configuration settings"""
    
    # Scheduling
    schedule: str = "0 6 * * *"  # Daily at 06:00 UTC
    timezone: str = "UTC"
    enable_scheduler: bool = True
    
    # Database
    database_url: str = ""
    
    # Alerting - Email
    alert_email_enabled: bool = False
    alert_email_smtp_host: str = ""
    alert_email_smtp_port: int = 587
    alert_email_from: str = ""
    alert_email_recipients: list = None
    alert_email_smtp_user: str = ""
    alert_email_smtp_password: str = ""
    
    # Alerting - Slack
    alert_slack_enabled: bool = False
    alert_slack_webhook_url: str = ""
    
    # Retry Configuration
    retry_max_attempts: int = 3
    retry_initial_delay: float = 2.0
    retry_backoff_factor: float = 2.0
    
    # Data Quality
    data_staleness_threshold_days: int = 7
    forecast_staleness_threshold_days: int = 7
    
    # Monitoring
    monitoring_port: int = 9090
    health_check_port: int = 8080
    
    def __post_init__(self):
        """Initialize mutable defaults"""
        if self.alert_email_recipients is None:
            self.alert_email_recipients = []


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


class ConfigLoader:
    """
    Loads and validates pipeline configuration.
    
    Configuration sources (in order of precedence):
    1. Environment variables
    2. Configuration file (if provided)
    3. Default values
    """
    
    @staticmethod
    def load_from_env() -> PipelineConfig:
        """
        Load configuration from environment variables
        
        Returns:
            PipelineConfig with loaded settings
            
        Raises:
            ConfigurationError: If required config is missing or invalid
        """
        try:
            config = PipelineConfig()
            
            # Scheduling
            config.schedule = os.getenv('PIPELINE_SCHEDULE', config.schedule)
            config.timezone = os.getenv('PIPELINE_TIMEZONE', config.timezone)
            config.enable_scheduler = os.getenv('PIPELINE_ENABLE_SCHEDULER', 'true').lower() == 'true'
            
            # Database (required)
            config.database_url = os.getenv('DATABASE_URL', '')
            if not config.database_url:
                raise ConfigurationError("DATABASE_URL environment variable is required")
            
            # Email alerting
            config.alert_email_enabled = os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true'
            if config.alert_email_enabled:
                config.alert_email_smtp_host = os.getenv('ALERT_EMAIL_SMTP_HOST', '')
                config.alert_email_smtp_port = int(os.getenv('ALERT_EMAIL_SMTP_PORT', '587'))
                config.alert_email_from = os.getenv('ALERT_EMAIL_FROM', '')
                
                recipients_str = os.getenv('ALERT_EMAIL_RECIPIENTS', '')
                if recipients_str:
                    config.alert_email_recipients = [r.strip() for r in recipients_str.split(',')]
                
                config.alert_email_smtp_user = os.getenv('ALERT_EMAIL_SMTP_USER', '')
                config.alert_email_smtp_password = os.getenv('ALERT_EMAIL_SMTP_PASSWORD', '')
                
                # Validate email config
                if not config.alert_email_smtp_host:
                    raise ConfigurationError("ALERT_EMAIL_SMTP_HOST required when email alerts enabled")
                if not config.alert_email_recipients:
                    raise ConfigurationError("ALERT_EMAIL_RECIPIENTS required when email alerts enabled")
            
            # Slack alerting
            config.alert_slack_enabled = os.getenv('ALERT_SLACK_ENABLED', 'false').lower() == 'true'
            if config.alert_slack_enabled:
                config.alert_slack_webhook_url = os.getenv('ALERT_SLACK_WEBHOOK_URL', '')
                if not config.alert_slack_webhook_url:
                    raise ConfigurationError("ALERT_SLACK_WEBHOOK_URL required when Slack alerts enabled")
            
            # Retry configuration
            config.retry_max_attempts = int(os.getenv('RETRY_MAX_ATTEMPTS', str(config.retry_max_attempts)))
            config.retry_initial_delay = float(os.getenv('RETRY_INITIAL_DELAY', str(config.retry_initial_delay)))
            config.retry_backoff_factor = float(os.getenv('RETRY_BACKOFF_FACTOR', str(config.retry_backoff_factor)))
            
            # Validate retry config
            if config.retry_max_attempts < 1:
                raise ConfigurationError("RETRY_MAX_ATTEMPTS must be >= 1")
            if config.retry_initial_delay <= 0:
                raise ConfigurationError("RETRY_INITIAL_DELAY must be > 0")
            if config.retry_backoff_factor < 1:
                raise ConfigurationError("RETRY_BACKOFF_FACTOR must be >= 1")
            
            # Data quality thresholds
            config.data_staleness_threshold_days = int(os.getenv(
                'DATA_STALENESS_THRESHOLD_DAYS',
                str(config.data_staleness_threshold_days)
            ))
            config.forecast_staleness_threshold_days = int(os.getenv(
                'FORECAST_STALENESS_THRESHOLD_DAYS',
                str(config.forecast_staleness_threshold_days)
            ))
            
            # Monitoring
            config.monitoring_port = int(os.getenv('MONITORING_PORT', str(config.monitoring_port)))
            config.health_check_port = int(os.getenv('HEALTH_CHECK_PORT', str(config.health_check_port)))
            
            logger.info("Configuration loaded successfully from environment")
            return config
            
        except ValueError as e:
            raise ConfigurationError(f"Invalid configuration value: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    @staticmethod
    def load_from_file(config_path: str) -> PipelineConfig:
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            PipelineConfig with loaded settings
            
        Raises:
            ConfigurationError: If file not found or invalid
        """
        try:
            import yaml
            
            path = Path(config_path)
            if not path.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")
            
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                raise ConfigurationError(f"Configuration file is empty: {config_path}")
            
            config = PipelineConfig()
            
            # Map YAML keys to config attributes
            if 'scheduling' in data:
                config.schedule = data['scheduling'].get('schedule', config.schedule)
                config.timezone = data['scheduling'].get('timezone', config.timezone)
                config.enable_scheduler = data['scheduling'].get('enable', config.enable_scheduler)
            
            if 'database' in data:
                config.database_url = data['database'].get('url', config.database_url)
            
            if 'alerting' in data:
                email = data['alerting'].get('email', {})
                config.alert_email_enabled = email.get('enabled', config.alert_email_enabled)
                config.alert_email_smtp_host = email.get('smtp_host', config.alert_email_smtp_host)
                config.alert_email_smtp_port = email.get('smtp_port', config.alert_email_smtp_port)
                config.alert_email_from = email.get('from_address', config.alert_email_from)
                config.alert_email_recipients = email.get('recipients', config.alert_email_recipients)
                
                slack = data['alerting'].get('slack', {})
                config.alert_slack_enabled = slack.get('enabled', config.alert_slack_enabled)
                config.alert_slack_webhook_url = slack.get('webhook_url', config.alert_slack_webhook_url)
            
            if 'retry' in data:
                config.retry_max_attempts = data['retry'].get('max_attempts', config.retry_max_attempts)
                config.retry_initial_delay = data['retry'].get('initial_delay', config.retry_initial_delay)
                config.retry_backoff_factor = data['retry'].get('backoff_factor', config.retry_backoff_factor)
            
            if 'thresholds' in data:
                config.data_staleness_threshold_days = data['thresholds'].get(
                    'data_staleness_days',
                    config.data_staleness_threshold_days
                )
                config.forecast_staleness_threshold_days = data['thresholds'].get(
                    'forecast_staleness_days',
                    config.forecast_staleness_threshold_days
                )
            
            if 'monitoring' in data:
                config.monitoring_port = data['monitoring'].get('port', config.monitoring_port)
                config.health_check_port = data['monitoring'].get('health_check_port', config.health_check_port)
            
            logger.info(f"Configuration loaded successfully from file: {config_path}")
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration file: {e}")
    
    @staticmethod
    def validate_config(config: PipelineConfig) -> None:
        """
        Validate configuration settings
        
        Args:
            config: Configuration to validate
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate database URL
        if not config.database_url:
            raise ConfigurationError("Database URL is required")
        
        # Validate schedule (basic cron validation)
        parts = config.schedule.split()
        if len(parts) != 5:
            raise ConfigurationError(
                f"Invalid cron schedule '{config.schedule}'. "
                "Must have 5 parts: minute hour day month day_of_week"
            )
        
        # Validate retry settings
        if config.retry_max_attempts < 1:
            raise ConfigurationError("retry_max_attempts must be >= 1")
        if config.retry_initial_delay <= 0:
            raise ConfigurationError("retry_initial_delay must be > 0")
        if config.retry_backoff_factor < 1:
            raise ConfigurationError("retry_backoff_factor must be >= 1")
        
        # Validate thresholds
        if config.data_staleness_threshold_days < 1:
            raise ConfigurationError("data_staleness_threshold_days must be >= 1")
        if config.forecast_staleness_threshold_days < 1:
            raise ConfigurationError("forecast_staleness_threshold_days must be >= 1")
        
        # Validate ports
        if not (1 <= config.monitoring_port <= 65535):
            raise ConfigurationError("monitoring_port must be between 1 and 65535")
        if not (1 <= config.health_check_port <= 65535):
            raise ConfigurationError("health_check_port must be between 1 and 65535")
        
        logger.info("Configuration validation passed")
    
    @staticmethod
    def get_email_config(config: PipelineConfig) -> Optional[Dict[str, Any]]:
        """
        Get email configuration dictionary for AlertService
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Email config dict or None if email not enabled
        """
        if not config.alert_email_enabled:
            return None
        
        return {
            'smtp_host': config.alert_email_smtp_host,
            'smtp_port': config.alert_email_smtp_port,
            'from_address': config.alert_email_from,
            'recipients': config.alert_email_recipients,
            'smtp_user': config.alert_email_smtp_user,
            'smtp_password': config.alert_email_smtp_password,
        }
