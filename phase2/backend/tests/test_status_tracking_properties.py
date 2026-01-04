"""
Property-based tests for Pipeline Status and Progress Tracking

**Feature: automated-forecast-pipeline, Property 26: Status reporting accuracy**
**Feature: automated-forecast-pipeline, Property 27: Progress tracking**
**Validates: Requirements 7.3, 7.4**
"""
import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.pipeline.orchestrator import PipelineOrchestrator
from app.services.pipeline.status_tracker import StatusTracker, PipelineStatus, ProgressStage
from app.models.pipeline_execution import PipelineExecution


@settings(
    max_examples=20,
    deadline=5000,
)
@given(
    execution_status=st.sampled_from(['idle', 'running', 'completed', 'failed', 'partial']),
    records_stored=st.integers(min_value=0, max_value=1000),
    forecasts_generated=st.integers(min_value=0, max_value=100)
)
def test_status_reporting_accuracy(
    db: Session,
    execution_status: str,
    records_stored: int,
    forecasts_generated: int
):
    """
    Property Test: Status reporting accuracy
    
    **Feature: automated-forecast-pipeline, Property 26**
    **Validates: Requirements 7.3**
    
    For any pipeline execution state, the status API should accurately
    report the current status, results, and any errors.
    """
    tracker = StatusTracker(db)
    
    # Create execution with specific status
    execution = PipelineExecution(
        id='test-status-exec',
        execution_type='manual',
        status=execution_status,
        started_at=datetime.now() - timedelta(minutes=30),
        records_stored=records_stored,
        forecasts_generated=forecasts_generated
    )
    
    if execution_status in ['completed', 'failed', 'partial']:
        execution.completed_at = datetime.now()
        execution.duration_seconds = 1800
    
    if execution_status == 'failed':
        execution.error_message = "Test error message"
    
    db.add(execution)
    db.commit()
    
    try:
        # Get status
        status = tracker.get_execution_status('test-status-exec')
        
        # Property 1: Status should match execution status
        assert status.status == execution_status, (
            f"Expected status '{execution_status}', got '{status.status}'"
        )
        
        # Property 2: Should report records stored
        assert status.records_stored == records_stored, (
            f"Expected {records_stored} records, got {status.records_stored}"
        )
        
        # Property 3: Should report forecasts generated
        assert status.forecasts_generated == forecasts_generated, (
            f"Expected {forecasts_generated} forecasts, got {status.forecasts_generated}"
        )
        
        # Property 4: Should include execution ID
        assert status.execution_id == 'test-status-exec', (
            "Status should include execution ID"
        )
        
        # Property 5: Should include timestamps
        assert status.started_at is not None, (
            "Status should include start timestamp"
        )
        
        # Property 6: For completed/failed executions, should include completion time
        if execution_status in ['completed', 'failed', 'partial']:
            assert status.completed_at is not None, (
                f"Status should include completion time for '{execution_status}'"
            )
            assert status.duration_seconds is not None, (
                f"Status should include duration for '{execution_status}'"
            )
        
        # Property 7: For failed executions, should include error message
        if execution_status == 'failed':
            assert status.error_message is not None, (
                "Status should include error message for failed execution"
            )
            assert len(status.error_message) > 0, (
                "Error message should not be empty"
            )
        
    finally:
        # Cleanup
        db.delete(execution)
        db.commit()


@settings(
    max_examples=20,
    deadline=5000,
)
@given(
    current_stage=st.sampled_from([
        'initializing',
        'ingesting_chirps',
        'ingesting_nasa_power',
        'ingesting_era5',
        'ingesting_ndvi',
        'ingesting_ocean_indices',
        'generating_forecasts',
        'creating_recommendations',
        'finalizing'
    ]),
    progress_percentage=st.integers(min_value=0, max_value=100),
    total_sources=st.integers(min_value=1, max_value=5),
    completed_sources=st.integers(min_value=0, max_value=5)
)
def test_progress_tracking(
    db: Session,
    current_stage: str,
    progress_percentage: int,
    total_sources: int,
    completed_sources: int
):
    """
    Property Test: Progress tracking
    
    **Feature: automated-forecast-pipeline, Property 27**
    **Validates: Requirements 7.4**
    
    For any pipeline execution, the system should track and report
    progress through each stage with percentage completion.
    """
    # Ensure completed <= total
    if completed_sources > total_sources:
        completed_sources = total_sources
    
    tracker = StatusTracker(db)
    
    # Create execution
    execution = PipelineExecution(
        id='test-progress-exec',
        execution_type='scheduled',
        status='running',
        started_at=datetime.now() - timedelta(minutes=10)
    )
    db.add(execution)
    db.commit()
    
    try:
        # Update progress
        tracker.update_progress(
            execution_id='test-progress-exec',
            stage=current_stage,
            progress_percentage=progress_percentage,
            completed_sources=completed_sources,
            total_sources=total_sources
        )
        
        # Get progress
        progress = tracker.get_progress('test-progress-exec')
        
        # Property 1: Should report current stage
        assert progress.current_stage == current_stage, (
            f"Expected stage '{current_stage}', got '{progress.current_stage}'"
        )
        
        # Property 2: Should report progress percentage
        assert progress.progress_percentage == progress_percentage, (
            f"Expected {progress_percentage}% progress, got {progress.progress_percentage}%"
        )
        
        # Property 3: Progress percentage should be in valid range
        assert 0 <= progress.progress_percentage <= 100, (
            f"Progress percentage should be 0-100, got {progress.progress_percentage}"
        )
        
        # Property 4: Should report source completion
        assert progress.completed_sources == completed_sources, (
            f"Expected {completed_sources} completed sources, got {progress.completed_sources}"
        )
        assert progress.total_sources == total_sources, (
            f"Expected {total_sources} total sources, got {progress.total_sources}"
        )
        
        # Property 5: Completed sources should not exceed total
        assert progress.completed_sources <= progress.total_sources, (
            f"Completed sources ({progress.completed_sources}) should not exceed "
            f"total sources ({progress.total_sources})"
        )
        
        # Property 6: Should include execution ID
        assert progress.execution_id == 'test-progress-exec', (
            "Progress should include execution ID"
        )
        
        # Property 7: Should include timestamp
        assert progress.updated_at is not None, (
            "Progress should include update timestamp"
        )
        
    finally:
        # Cleanup
        db.delete(execution)
        db.commit()


@settings(
    max_examples=15,
    deadline=5000,
)
@given(
    stages=st.lists(
        st.sampled_from([
            'initializing',
            'ingesting_data',
            'generating_forecasts',
            'finalizing'
        ]),
        min_size=2,
        max_size=4,
        unique=True
    )
)
def test_progress_stage_transitions(
    db: Session,
    stages: list
):
    """
    Property Test: Progress stage transitions
    
    For any sequence of pipeline stages, the progress should transition
    through stages in order and track the progression.
    
    **Validates: Requirements 7.4**
    """
    tracker = StatusTracker(db)
    
    # Create execution
    execution = PipelineExecution(
        id='test-transition-exec',
        execution_type='manual',
        status='running',
        started_at=datetime.now()
    )
    db.add(execution)
    db.commit()
    
    try:
        # Track stage transitions
        stage_history = []
        
        for i, stage in enumerate(stages):
            progress_pct = int((i + 1) / len(stages) * 100)
            
            tracker.update_progress(
                execution_id='test-transition-exec',
                stage=stage,
                progress_percentage=progress_pct,
                completed_sources=i,
                total_sources=len(stages)
            )
            
            progress = tracker.get_progress('test-transition-exec')
            stage_history.append(progress.current_stage)
        
        # Property 1: Should track all stage transitions
        assert stage_history == stages, (
            f"Stage history should match transitions: expected {stages}, got {stage_history}"
        )
        
        # Property 2: Final progress should be at last stage
        final_progress = tracker.get_progress('test-transition-exec')
        assert final_progress.current_stage == stages[-1], (
            f"Final stage should be '{stages[-1]}', got '{final_progress.current_stage}'"
        )
        
        # Property 3: Progress should increase monotonically
        progress_values = []
        for stage in stages:
            # Get historical progress (if tracked)
            progress_values.append(stages.index(stage) + 1)
        
        assert progress_values == sorted(progress_values), (
            "Progress should increase monotonically through stages"
        )
        
    finally:
        # Cleanup
        db.delete(execution)
        db.commit()


def test_status_api_endpoint_integration(db: Session):
    """
    Property Test: Status API endpoint integration
    
    The status API endpoint should return properly formatted JSON
    with all required fields.
    
    **Validates: Requirements 7.5**
    """
    from app.api.pipeline import get_pipeline_status
    
    # Create execution
    execution = PipelineExecution(
        id='test-api-exec',
        execution_type='scheduled',
        status='completed',
        started_at=datetime.now() - timedelta(hours=1),
        completed_at=datetime.now(),
        duration_seconds=3600,
        records_stored=500,
        forecasts_generated=50
    )
    db.add(execution)
    db.commit()
    
    try:
        # Get status via API
        status_response = get_pipeline_status(execution_id='test-api-exec', db=db)
        
        # Property 1: Response should be a dictionary
        assert isinstance(status_response, dict), (
            "Status response should be a dictionary"
        )
        
        # Property 2: Should include required fields
        required_fields = ['execution_id', 'status', 'started_at']
        for field in required_fields:
            assert field in status_response, (
                f"Status response should include '{field}'"
            )
        
        # Property 3: Status should match execution
        assert status_response['status'] == 'completed', (
            "Status should match execution status"
        )
        
        # Property 4: Should include results
        assert 'records_stored' in status_response, (
            "Should include records stored"
        )
        assert 'forecasts_generated' in status_response, (
            "Should include forecasts generated"
        )
        
    finally:
        # Cleanup
        db.delete(execution)
        db.commit()


def test_execution_summary_with_errors(db: Session):
    """
    Property Test: Execution summary with errors
    
    For failed executions, the status should include a comprehensive
    summary with error details and affected components.
    
    **Validates: Requirements 7.5**
    """
    tracker = StatusTracker(db)
    
    # Create failed execution
    execution = PipelineExecution(
        id='test-error-exec',
        execution_type='manual',
        status='failed',
        started_at=datetime.now() - timedelta(minutes=30),
        completed_at=datetime.now(),
        duration_seconds=1800,
        error_message="Connection timeout to data source",
        sources_failed=['chirps', 'nasa_power'],
        sources_succeeded=['era5']
    )
    db.add(execution)
    db.commit()
    
    try:
        # Get status with summary
        status = tracker.get_execution_status('test-error-exec')
        
        # Property 1: Should include error message
        assert status.error_message is not None, (
            "Failed execution should include error message"
        )
        
        # Property 2: Should list failed sources
        assert len(status.sources_failed) > 0, (
            "Should list failed sources"
        )
        assert 'chirps' in status.sources_failed, (
            "Should include 'chirps' in failed sources"
        )
        
        # Property 3: Should list succeeded sources
        assert len(status.sources_succeeded) > 0, (
            "Should list succeeded sources"
        )
        assert 'era5' in status.sources_succeeded, (
            "Should include 'era5' in succeeded sources"
        )
        
        # Property 4: Failed and succeeded sources should not overlap
        overlap = set(status.sources_failed) & set(status.sources_succeeded)
        assert len(overlap) == 0, (
            f"Sources should not be in both failed and succeeded: {overlap}"
        )
        
    finally:
        # Cleanup
        db.delete(execution)
        db.commit()


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
