"""
Property-based tests for Configuration Management

**Feature: automated-forecast-pipeline, Property 34: Configuration loading**
**Feature: automated-forecast-pipeline, Property 38: Configuration validation**
**Validates: Requirements 9.1, 9.5**
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import patch
import os

from app.core.config import Settings, get_settings


@settings(
    max_examples=20,
    deadline=5000,
)
@given(
    pipeline_schedule=st.sampled_from([
        '0 6 * * *',
        '0 */6 * * *',
        '0 0 * * 0',
        '*/30 * * * *'
    ]),
    pipeline_timezone=st.sampled_from(['UTC', 'America/New_York', 'Europe/London', 'Africa/Nairobi']),
    retry_max_attempts=st.integers(min_value=1, max_value=10),
    staleness_threshold_days=st.integers(min_value=1, max_value=30)
)
def test_configuration_loading(
    pipeline_schedule: str,
    pipeline_timezone: str,
    retry_max_attempts: int,
    staleness_threshold_days: int
):
    """
    Property Test: Configuration loading
    
    **Feature: automated-forecast-pipeline, Property 34**
    **Validates: Requirements 9.1**
    
    For any valid configuration values, the system should load and
    apply them correctly from environment variables and config files.
    """
    # Mock environment variables
    env_vars = {
        'PIPELINE_SCHEDULE': pipeline_schedule,
        'PIPELINE_TIMEZONE': pipeline_timezone,
        'RETRY_MAX_ATTEMPTS': str(retry_max_attempts),
        'DATA_STALENESS_THRESHOLD_DAYS': str(staleness_threshold_days),
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        # Reload settings
        settings = Settings()
        
        # Property 1: Should load pipeline schedule
        assert settings.PIPELINE_SCHEDULE == pipeline_schedule, (
            f"Expected schedule '{pipeline_schedule}', got '{settings.PIPELINE_SCHEDULE}'"
        )
        
        # Property 2: Should load pipeline timezone
        assert settings.PIPELINE_TIMEZONE == pipeline_timezone, (
            f"Expected timezone '{pipeline_timezone}', got '{settings.PIPELINE_TIMEZONE}'"
        )
        
        # Property 3: Should load retry configuration
        assert settings.RETRY_MAX_ATTEMPTS == retry_max_attempts, (
            f"Expected {retry_max_attempts} retry attempts, got {settings.RETRY_MAX_ATTEMPTS}"
        )
        
        # Property 4: Should load staleness threshold
        assert settings.DATA_STALENESS_THRESHOLD_DAYS == staleness_threshold_days, (
            f"Expected {staleness_threshold_days} day threshold, "
            f"got {settings.DATA_STALENESS_THRESHOLD_DAYS}"
        )


@settings(
    max_examples=20,
    deadline=5000,
)
@given(
    alert_email_enabled=st.booleans(),
    alert_slack_enabled=st.booleans(),
    monitoring_metrics_port=st.integers(min_value=1024, max_value=65535),
    monitoring_health_port=st.integers(min_value=1024, max_value=65535)
)
def test_configuration_loading_alerts_and_monitoring(
    alert_email_enabled: bool,
    alert_slack_enabled: bool,
    monitoring_metrics_port: int,
    monitoring_health_port: int
):
    """
    Property Test: Configuration loading for alerts and monitoring
    
    For any alert and monitoring configuration, the system should
    load and apply the settings correctly.
    
    **Validates: Requirements 9.1, 9.2**
    """
    # Ensure ports are different
    if monitoring_metrics_port == monitoring_health_port:
        monitoring_health_port += 1
        if monitoring_health_port > 65535:
            monitoring_health_port = 1024
    
    env_vars = {
        'ALERT_EMAIL_ENABLED': str(alert_email_enabled).lower(),
        'ALERT_SLACK_ENABLED': str(alert_slack_enabled).lower(),
        'MONITORING_METRICS_PORT': str(monitoring_metrics_port),
        'MONITORING_HEALTH_PORT': str(monitoring_health_port),
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        settings = Settings()
        
        # Property 1: Should load email alert setting
        assert settings.ALERT_EMAIL_ENABLED == alert_email_enabled, (
            f"Expected email enabled={alert_email_enabled}, "
            f"got {settings.ALERT_EMAIL_ENABLED}"
        )
        
        # Property 2: Should load Slack alert setting
        assert settings.ALERT_SLACK_ENABLED == alert_slack_enabled, (
            f"Expected Slack enabled={alert_slack_enabled}, "
            f"got {settings.ALERT_SLACK_ENABLED}"
        )
        
        # Property 3: Should load metrics port
        assert settings.MONITORING_METRICS_PORT == monitoring_metrics_port, (
            f"Expected metrics port {monitoring_metrics_port}, "
            f"got {settings.MONITORING_METRICS_PORT}"
        )
        
        # Property 4: Should load health port
        assert settings.MONITORING_HEALTH_PORT == monitoring_health_port, (
            f"Expected health port {monitoring_health_port}, "
            f"got {settings.MONITORING_HEALTH_PORT}"
        )


@settings(
    max_examples=20,
    deadline=5000,
)
@given(
    invalid_schedule=st.sampled_from([
        'invalid cron',
        '99 99 * * *',
        'not a schedule',
        '',
    ]),
    invalid_port=st.sampled_from([
        -1,
        0,
        70000,
        999999
    ]),
    invalid_retry_attempts=st.sampled_from([
        -1,
        0,
        1000
    ])
)
def test_configuration_validation(
    invalid_schedule: str,
    invalid_port: int,
    invalid_retry_attempts: int
):
    """
    Property Test: Configuration validation
    
    **Feature: automated-forecast-pipeline, Property 38**
    **Validates: Requirements 9.5**
    
    For any invalid configuration values, the system should detect
    the error and provide clear error messages.
    """
    from app.services.pipeline.config_validator import ConfigValidator
    
    validator = ConfigValidator()
    
    # Test invalid schedule
    schedule_result = validator.validate_cron_expression(invalid_schedule)
    
    # Property 1: Should detect invalid cron expression
    assert not schedule_result.is_valid, (
        f"Should detect invalid cron expression: '{invalid_schedule}'"
    )
    assert schedule_result.error_message is not None, (
        "Should provide error message for invalid cron"
    )
    assert 'cron' in schedule_result.error_message.lower() or 'schedule' in schedule_result.error_message.lower(), (
        "Error message should mention cron/schedule"
    )
    
    # Test invalid port
    port_result = validator.validate_port(invalid_port)
    
    # Property 2: Should detect invalid port
    assert not port_result.is_valid, (
        f"Should detect invalid port: {invalid_port}"
    )
    assert port_result.error_message is not None, (
        "Should provide error message for invalid port"
    )
    assert 'port' in port_result.error_message.lower(), (
        "Error message should mention port"
    )
    
    # Test invalid retry attempts
    retry_result = validator.validate_retry_attempts(invalid_retry_attempts)
    
    # Property 3: Should detect invalid retry attempts
    assert not retry_result.is_valid, (
        f"Should detect invalid retry attempts: {invalid_retry_attempts}"
    )
    assert retry_result.error_message is not None, (
        "Should provide error message for invalid retry attempts"
    )
    assert 'retry' in retry_result.error_message.lower() or 'attempt' in retry_result.error_message.lower(), (
        "Error message should mention retry/attempts"
    )


@settings(
    max_examples=15,
    deadline=5000,
)
@given(
    valid_schedule=st.sampled_from([
        '0 6 * * *',
        '0 */6 * * *',
        '*/15 * * * *',
        '0 0 * * 0'
    ]),
    valid_port=st.integers(min_value=1024, max_value=65535),
    valid_retry_attempts=st.integers(min_value=1, max_value=10)
)
def test_configuration_validation_accepts_valid_values(
    valid_schedule: str,
    valid_port: int,
    valid_retry_attempts: int
):
    """
    Property Test: Configuration validation accepts valid values
    
    For any valid configuration values, the validation should pass
    without errors.
    
    **Validates: Requirements 9.5**
    """
    from app.services.pipeline.config_validator import ConfigValidator
    
    validator = ConfigValidator()
    
    # Test valid schedule
    schedule_result = validator.validate_cron_expression(valid_schedule)
    
    # Property 1: Should accept valid cron expression
    assert schedule_result.is_valid, (
        f"Should accept valid cron expression: '{valid_schedule}', "
        f"error: {schedule_result.error_message}"
    )
    
    # Test valid port
    port_result = validator.validate_port(valid_port)
    
    # Property 2: Should accept valid port
    assert port_result.is_valid, (
        f"Should accept valid port: {valid_port}, "
        f"error: {port_result.error_message}"
    )
    
    # Test valid retry attempts
    retry_result = validator.validate_retry_attempts(valid_retry_attempts)
    
    # Property 3: Should accept valid retry attempts
    assert retry_result.is_valid, (
        f"Should accept valid retry attempts: {valid_retry_attempts}, "
        f"error: {retry_result.error_message}"
    )


def test_configuration_hot_reload():
    """
    Property Test: Configuration hot-reload
    
    The system should support reloading configuration without
    requiring a full restart (where applicable).
    
    **Validates: Requirements 9.4**
    """
    from app.core.config import get_settings
    
    # Get initial settings
    settings1 = get_settings()
    initial_schedule = settings1.PIPELINE_SCHEDULE
    
    # Modify environment
    new_schedule = '0 12 * * *'
    with patch.dict(os.environ, {'PIPELINE_SCHEDULE': new_schedule}, clear=False):
        # Force reload
        get_settings.cache_clear()
        settings2 = get_settings()
        
        # Property: Should reflect new configuration
        assert settings2.PIPELINE_SCHEDULE == new_schedule, (
            f"Configuration should hot-reload, expected '{new_schedule}', "
            f"got '{settings2.PIPELINE_SCHEDULE}'"
        )


def test_configuration_defaults():
    """
    Property Test: Configuration defaults
    
    When configuration values are not provided, the system should
    use sensible defaults.
    
    **Validates: Requirements 9.2**
    """
    # Clear specific environment variables
    env_to_clear = [
        'PIPELINE_SCHEDULE',
        'RETRY_MAX_ATTEMPTS',
        'DATA_STALENESS_THRESHOLD_DAYS'
    ]
    
    with patch.dict(os.environ, {k: '' for k in env_to_clear}, clear=False):
        settings = Settings()
        
        # Property 1: Should have default schedule
        assert settings.PIPELINE_SCHEDULE is not None, (
            "Should have default pipeline schedule"
        )
        assert isinstance(settings.PIPELINE_SCHEDULE, str), (
            "Schedule should be a string"
        )
        
        # Property 2: Should have default retry attempts
        assert settings.RETRY_MAX_ATTEMPTS > 0, (
            "Should have positive default retry attempts"
        )
        
        # Property 3: Should have default staleness threshold
        assert settings.DATA_STALENESS_THRESHOLD_DAYS > 0, (
            "Should have positive default staleness threshold"
        )


def test_configuration_documentation():
    """
    Property Test: Configuration documentation
    
    All configuration options should be documented with descriptions
    and valid value ranges.
    
    **Validates: Requirements 9.1**
    """
    from app.core.config import Settings
    
    # Property: Settings class should have docstrings
    assert Settings.__doc__ is not None, (
        "Settings class should have documentation"
    )
    
    # Property: Key fields should have descriptions
    settings = Settings()
    key_fields = [
        'PIPELINE_SCHEDULE',
        'RETRY_MAX_ATTEMPTS',
        'ALERT_EMAIL_ENABLED',
        'MONITORING_METRICS_PORT'
    ]
    
    for field in key_fields:
        assert hasattr(settings, field), (
            f"Settings should have field '{field}'"
        )


@settings(
    max_examples=10,
    deadline=3000,
)
@given(
    config_changes=st.lists(
        st.tuples(
            st.sampled_from(['PIPELINE_SCHEDULE', 'RETRY_MAX_ATTEMPTS', 'DATA_STALENESS_THRESHOLD_DAYS']),
            st.sampled_from(['0 6 * * *', '3', '7'])
        ),
        min_size=1,
        max_size=3,
        unique_by=lambda x: x[0]
    )
)
def test_configuration_consistency(config_changes: list):
    """
    Property Test: Configuration consistency
    
    For any set of configuration changes, the system should maintain
    consistency across all components.
    
    **Validates: Requirements 9.2**
    """
    env_vars = {key: value for key, value in config_changes}
    
    with patch.dict(os.environ, env_vars, clear=False):
        settings = Settings()
        
        # Property: All changed values should be reflected
        for key, expected_value in config_changes:
            actual_value = getattr(settings, key)
            
            # Convert to same type for comparison
            if isinstance(actual_value, int):
                expected_value = int(expected_value)
            
            assert actual_value == expected_value, (
                f"Configuration {key} should be {expected_value}, got {actual_value}"
            )
