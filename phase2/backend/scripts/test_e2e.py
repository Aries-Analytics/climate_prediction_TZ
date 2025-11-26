"""
End-to-End Testing Script

Tests complete data flow from loading to display.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import logging
from verify_data import verify_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_e2e():
    """Run end-to-end tests"""
    
    logger.info("=" * 80)
    logger.info("END-TO-END TESTING")
    logger.info("=" * 80)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Database verification
    logger.info("\nTest 1: Database Verification")
    try:
        if verify_data():
            logger.info("✓ PASS: Database verification")
            tests_passed += 1
        else:
            logger.error("✗ FAIL: Database verification")
            tests_failed += 1
    except Exception as e:
        logger.error(f"✗ FAIL: Database verification - {e}")
        tests_failed += 1
    
    # Test 2: Backend API health
    logger.info("\nTest 2: Backend API Health")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✓ PASS: Backend API responding")
            tests_passed += 1
        else:
            logger.error(f"✗ FAIL: Backend API returned {response.status_code}")
            tests_failed += 1
    except Exception as e:
        logger.error(f"✗ FAIL: Backend API not accessible - {e}")
        tests_failed += 1
    
    # Test 3: API endpoints
    logger.info("\nTest 3: API Endpoints")
    endpoints = [
        "/api/dashboard/executive",
        "/api/models",
        "/api/triggers",
        "/api/climate/timeseries",
        "/api/risk/portfolio"
    ]
    
    # Note: These require authentication, so we test without auth
    # In production, add proper auth token
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            # 401 is expected without auth, means endpoint exists
            if response.status_code in [200, 401]:
                logger.info(f"✓ PASS: {endpoint} exists")
                tests_passed += 1
            else:
                logger.error(f"✗ FAIL: {endpoint} returned {response.status_code}")
                tests_failed += 1
        except Exception as e:
            logger.error(f"✗ FAIL: {endpoint} - {e}")
            tests_failed += 1
    
    # Test 4: Frontend accessibility
    logger.info("\nTest 4: Frontend Accessibility")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            logger.info("✓ PASS: Frontend accessible")
            tests_passed += 1
        else:
            logger.error(f"✗ FAIL: Frontend returned {response.status_code}")
            tests_failed += 1
    except Exception as e:
        logger.error(f"✗ FAIL: Frontend not accessible - {e}")
        tests_failed += 1
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Tests Passed: {tests_passed}")
    logger.info(f"Tests Failed: {tests_failed}")
    logger.info(f"Total Tests: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        logger.info("\n✓ ALL TESTS PASSED!")
        return True
    else:
        logger.error(f"\n✗ {tests_failed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = test_e2e()
    sys.exit(0 if success else 1)
