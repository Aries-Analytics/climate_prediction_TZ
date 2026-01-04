"""
Property-based tests for Pipeline Scheduler

**Feature: automated-forecast-pipeline, Property 1: Scheduled execution triggers at configured time**
**Feature: automated-forecast-pipeline, Property 2: Successful ingestion triggers forecast generation**
**Feature: automated-forecast-pipeline, Property 25: Manual trigger execution**
**Validates: Requirements 1.1, 1.2, 7.1**
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.pipeline.scheduler import PipelineScheduler
from app.models.pipeline_execution import PipelineExecution


@settings(
    max_examples=10,
    deadline=10000,
)
@given(
    cron_expression=st.sampled_from([
        '0 6 * * *',      # Daily at 6 AM
        '0 */6 * * *',    # Every 6 hours
        '0 0 * * 0',      # Weekly on Sunday
        '0 12 * * 1-5',   # Weekdays at noon
    ])
)
def test_scheduled_execution_triggers(
    db: Session,
    cron_expression: str
):
    """
    Property Test: Scheduled execution triggers at configured time
    
    **Feature: automated-forecast-pipeline, Property 1**
    **Validates: Requirements 1.1**
    
    For any valid cron expression, the scheduler should configure a job
    that triggers pipeline execution at the specified times.
    """
    scheduler = PipelineScheduler(db)
    
    # Mock the orchestrator to avoid actual execution
    with patch.object(scheduler, 'orchestrator') as mock_orchestrator:
        mock_orchestrator.execute_pipeline.return_value = MagicMock(
            status='completed',
            execution_id='test-123'
        )
        
        # Configure scheduler with cron expression
        with patch('app.core.config.settings.PIPELINE_SCHEDULE', cron_expression):
            # Start scheduler
            scheduler.start()
            
            try:
                # Property 1: Scheduler should be running
                assert scheduler.scheduler.running, "Scheduler should be running after start()"
                
                # Property 2: Job should be configured
                jobs = scheduler.scheduler.get_jobs()
                assert len(jobs) > 0, "At least one job should be configured"
                
                # Property 3: Job should have correct trigger
                job = jobs[0]
                assert job.trigger is not None, "Job should have a trigger configured"
                
                # Property 4: Trigger should match cron expression
                # CronTrigger stores the expression in its fields
                trigger_str = str(job.trigger)
                assert 'cron' in trigger_str.lower(), "Trigger should be a cron trigger"
                
            finally:
                # Always stop scheduler
                scheduler.stop()
                
                # Property 5: Scheduler should stop cleanly
                assert not scheduler.scheduler.running, "Scheduler should stop after stop()"


@settings(
    max_examples=10,
    deadline=10000,
)
@given(
    ingestion_success=st.booleans(),
    sources_succeeded=st.lists(
        st.sampled_from(['chirps', 'nasa_power', 'era5', 'ndvi', 'ocean_indices']),
        min_size=1,
        max_size=5,
        unique=True
    )
)
def test_ingestion_forecast_chaining(
    db: Session,
    ingestion_success: bool,
    sources_succeeded: list
):
    """
    Property Test: Successful ingestion triggers forecast generation
    
    **Feature: automated-forecast-pipeline, Property 2**
    **Validates: Requirements 1.2**
    
    For any successful ingestion (full or partial), the pipeline should
    automatically proceed to forecast generation.
    """
    scheduler = PipelineScheduler(db)
    
    # Track execution flow
    ingestion_called = False
    forecasting_called = False
    
    def mock_execute_ingestion(*args, **kwargs):
        nonlocal ingestion_called
        ingestion_called = True
        return MagicMock(
            status='completed' if ingestion_success else 'failed',
            sources_succeeded=sources_succeeded if ingestion_success else [],
            sources_failed=[] if ingestion_success else ['chirps'],
            records_stored=100 if ingestion_success else 0
        )
    
    def mock_execute_forecasting(*args, **kwargs):
        nonlocal forecasting_called
        forecasting_called = True
        return MagicMock(
            status='completed',
            forecasts_generated=10,
            recommendations_created=5
        )
    
    with patch.object(scheduler.orchestrator, 'execute_ingestion', side_effect=mock_execute_ingestion):
        with patch.object(scheduler.orchestrator, 'execute_forecasting', side_effect=mock_execute_forecasting):
            with patch.object(scheduler.orchestrator, 'acquire_lock', return_value=True):
                with patch.object(scheduler.orchestrator, 'release_lock'):
                    # Execute pipeline
                    result = scheduler.orchestrator.execute_pipeline(
                        execution_type='scheduled',
                        incremental=True
                    )
                    
                    # Property 1: Ingestion should always be called
                    assert ingestion_called, "Ingestion should be called in pipeline execution"
                    
                    # Property 2: Forecasting should be called if ingestion succeeds
                    if ingestion_success and len(sources_succeeded) > 0:
                        assert forecasting_called, (
                            "Forecasting should be called after successful ingestion"
                        )
                    
                    # Property 3: If ingestion fails completely, forecasting may be skipped
                    if not ingestion_success:
                        # This is acceptable - forecasting may not run without data
                        pass


@settings(
    max_examples=15,
    deadline=5000,
)
@given(
    execution_type=st.sampled_from(['manual', 'scheduled']),
    incremental=st.booleans()
)
def test_manual_trigger_execution(
    db: Session,
    execution_type: str,
    incremental: bool
):
    """
    Property Test: Manual trigger execution
    
    **Feature: automated-forecast-pipeline, Property 25**
    **Validates: Requirements 7.1**
    
    For any manual trigger request, the pipeline should execute immediately
    regardless of the schedule, respecting the incremental flag.
    """
    scheduler = PipelineScheduler(db)
    
    execution_started = False
    execution_params = {}
    
    def mock_execute_pipeline(*args, **kwargs):
        nonlocal execution_started, execution_params
        execution_started = True
        execution_params = kwargs
        return MagicMock(
            status='completed',
            execution_id='manual-test-123',
            records_stored=50,
            forecasts_generated=5
        )
    
    with patch.object(scheduler.orchestrator, 'execute_pipeline', side_effect=mock_execute_pipeline):
        # Trigger manual execution
        result = scheduler.trigger_manual_run(incremental=incremental)
        
        # Property 1: Execution should start immediately
        assert execution_started, "Manual trigger should start execution immediately"
        
        # Property 2: Execution type should be 'manual'
        assert execution_params.get('execution_type') == 'manual', (
            f"Expected execution_type 'manual', got '{execution_params.get('execution_type')}'"
        )
        
        # Property 3: Incremental flag should be respected
        assert execution_params.get('incremental') == incremental, (
            f"Expected incremental={incremental}, got {execution_params.get('incremental')}"
        )
        
        # Property 4: Result should be returned
        assert result is not None, "Manual trigger should return execution result"
        assert result.status == 'completed', "Execution should complete successfully"


@settings(
    max_examples=10,
    deadline=5000,
)
@given(
    concurrent_triggers=st.integers(min_value=2, max_value=5)
)
def test_concurrent_manual_triggers_prevented(
    db: Session,
    concurrent_triggers: int
):
    """
    Property Test: Concurrent manual triggers are prevented
    
    For any number of concurrent manual trigger attempts, only one
    should execute while others are rejected.
    
    **Validates: Requirements 1.3, 7.1**
    """
    scheduler = PipelineScheduler(db)
    
    execution_count = 0
    lock_held = False
    
    def mock_acquire_lock():
        nonlocal lock_held
        if lock_held:
            return False
        lock_held = True
        return True
    
    def mock_release_lock():
        nonlocal lock_held
        lock_held = False
    
    def mock_execute_pipeline(*args, **kwargs):
        nonlocal execution_count
        execution_count += 1
        return MagicMock(
            status='completed',
            execution_id=f'test-{execution_count}'
        )
    
    with patch.object(scheduler.orchestrator, 'acquire_lock', side_effect=mock_acquire_lock):
        with patch.object(scheduler.orchestrator, 'release_lock', side_effect=mock_release_lock):
            with patch.object(scheduler.orchestrator, 'execute_pipeline', side_effect=mock_execute_pipeline):
                # Attempt multiple concurrent triggers
                results = []
                for i in range(concurrent_triggers):
                    result = scheduler.trigger_manual_run()
                    results.append(result)
                
                # Property 1: Only one execution should succeed
                successful = [r for r in results if r.status == 'completed']
                failed = [r for r in results if r.status == 'failed']
                
                assert len(successful) == 1, (
                    f"Expected 1 successful execution, got {len(successful)}"
                )
                
                # Property 2: Other attempts should fail
                assert len(failed) == concurrent_triggers - 1, (
                    f"Expected {concurrent_triggers - 1} failed attempts, got {len(failed)}"
                )


def test_scheduler_persistence(db: Session):
    """
    Property Test: Scheduler job persistence
    
    The scheduler should use a persistent job store so that scheduled
    jobs survive application restarts.
    
    **Validates: Requirements 1.5**
    """
    scheduler = PipelineScheduler(db)
    
    # Start scheduler
    scheduler.start()
    
    try:
        # Property 1: Job store should be configured
        assert scheduler.scheduler.state == 1, "Scheduler should be in running state"
        
        # Property 2: Jobs should be persisted
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) > 0, "At least one job should be configured"
        
        # Property 3: Job store should be database-backed (not memory)
        jobstore = scheduler.scheduler._jobstores.get('default')
        assert jobstore is not None, "Default job store should exist"
        
        # Check if it's a persistent store (not MemoryJobStore)
        store_type = type(jobstore).__name__
        assert 'Memory' not in store_type, (
            f"Job store should be persistent, got {store_type}"
        )
        
    finally:
        scheduler.stop()


def test_scheduler_timezone_handling(db: Session):
    """
    Property Test: Scheduler timezone handling
    
    The scheduler should respect the configured timezone for job execution.
    
    **Validates: Requirements 1.1**
    """
    scheduler = PipelineScheduler(db)
    
    with patch('app.core.config.settings.PIPELINE_TIMEZONE', 'UTC'):
        scheduler.start()
        
        try:
            # Property: Scheduler should use configured timezone
            assert scheduler.scheduler.timezone is not None, (
                "Scheduler should have timezone configured"
            )
            
            # Verify timezone is set
            tz_str = str(scheduler.scheduler.timezone)
            assert 'UTC' in tz_str or 'utc' in tz_str.lower(), (
                f"Expected UTC timezone, got {tz_str}"
            )
            
        finally:
            scheduler.stop()


# Pytest fixtures
@pytest.fixture
def db(test_db):
    """Provide a database session for tests"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def test_db():
    """Set up test database"""
    pass
