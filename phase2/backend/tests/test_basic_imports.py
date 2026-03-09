"""
Basic import and instantiation tests - no pytest, no database
Run with: python tests/test_basic_imports.py
"""

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from app.services.pipeline.orchestrator import PipelineOrchestrator
        print("✓ Orchestrator imported")
    except Exception as e:
        print(f"✗ Orchestrator import failed: {e}")
        return False
    
    try:
        from app.services.pipeline.retry_handler import RetryHandler
        print("✓ RetryHandler imported")
    except Exception as e:
        print(f"✗ RetryHandler import failed: {e}")
        return False
    
    try:
        from app.services.pipeline.alert_service import AlertService
        print("✓ AlertService imported")
    except Exception as e:
        print(f"✗ AlertService import failed: {e}")
        return False
    
    try:
        from app.services.pipeline.monitoring import MonitoringService
        print("✓ MonitoringService imported")
    except Exception as e:
        print(f"✗ MonitoringService import failed: {e}")
        return False
    
    try:
        from app.services.pipeline.scheduler import PipelineScheduler
        print("✓ PipelineScheduler imported")
    except Exception as e:
        print(f"✗ PipelineScheduler import failed: {e}")
        return False
    
    return True


def test_retry_handler():
    """Test RetryHandler basic functionality"""
    print("\nTesting RetryHandler...")
    
    from app.services.pipeline.retry_handler import RetryHandler
    
    # Test instantiation
    handler = RetryHandler(max_attempts=2, initial_delay=0.01, backoff_factor=2.0)
    print("✓ RetryHandler instantiated")
    
    # Test successful operation
    def success_func():
        return "success"
    
    result = handler.retry(success_func)
    assert result == "success", f"Expected 'success', got {result}"
    print("✓ Successful operation works")

    # Test retry on failure then success
    attempt_count = [0]
    def fail_once():
        attempt_count[0] += 1
        if attempt_count[0] < 2:
            raise Exception("First attempt fails")
        return "success_after_retry"

    result = handler.retry(fail_once)
    assert result == "success_after_retry"
    assert attempt_count[0] == 2
    print("✓ Retry logic works")
    
    return True


def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    from app.core.config import settings
    
    assert settings.DATABASE_URL is not None
    print(f"✓ DATABASE_URL loaded: {settings.DATABASE_URL[:30]}...")
    
    assert settings.PIPELINE_SCHEDULE is not None
    print(f"✓ PIPELINE_SCHEDULE: {settings.PIPELINE_SCHEDULE}")
    
    assert settings.RETRY_MAX_ATTEMPTS > 0
    print(f"✓ RETRY_MAX_ATTEMPTS: {settings.RETRY_MAX_ATTEMPTS}")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("BASIC FUNCTIONALITY TESTS")
    print("=" * 60)
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_config():
        all_passed = False
    
    if not test_retry_handler():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL BASIC TESTS PASSED")
        print("=" * 60)
        exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        exit(1)
