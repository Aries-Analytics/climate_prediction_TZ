"""
Verification script for Dashboard System Integration (Task 28)
Tests all critical endpoints and functionality
"""
import requests
import sys
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str, passed: bool, details: str = ""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")

def test_backend_health() -> bool:
    """Test backend health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        passed = response.status_code == 200 and response.json().get("status") == "healthy"
        print_test("Backend Health Check", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("Backend Health Check", False, f"Error: {str(e)}")
        return False

def test_database_connection() -> bool:
    """Test database connectivity"""
    try:
        response = requests.get(f"{BASE_URL}/health/ready", timeout=5)
        data = response.json()
        passed = response.status_code == 200 and data.get("database") == "connected"
        print_test("Database Connection", passed, f"DB Status: {data.get('database')}")
        return passed
    except Exception as e:
        print_test("Database Connection", False, f"Error: {str(e)}")
        return False

def test_frontend_accessible() -> bool:
    """Test frontend is accessible"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        passed = response.status_code == 200
        print_test("Frontend Accessible", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test("Frontend Accessible", False, f"Error: {str(e)}")
        return False

def test_api_documentation() -> bool:
    """Test API documentation is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        passed = response.status_code == 200
        print_test("API Documentation", passed, f"Swagger UI accessible")
        return passed
    except Exception as e:
        print_test("API Documentation", False, f"Error: {str(e)}")
        return False

def test_cors_headers() -> bool:
    """Test CORS configuration"""
    try:
        response = requests.options(f"{BASE_URL}/api/dashboard/executive", 
                                   headers={"Origin": "http://localhost:3000"}, 
                                   timeout=5)
        has_cors = "access-control-allow-origin" in response.headers
        print_test("CORS Configuration", has_cors, f"CORS headers present: {has_cors}")
        return has_cors
    except Exception as e:
        print_test("CORS Configuration", False, f"Error: {str(e)}")
        return False

def test_security_headers() -> bool:
    """Test security headers are present"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        headers = response.headers
        required_headers = [
            "x-content-type-options",
            "x-frame-options",
            "x-xss-protection",
            "strict-transport-security"
        ]
        missing = [h for h in required_headers if h not in headers]
        passed = len(missing) == 0
        details = "All security headers present" if passed else f"Missing: {', '.join(missing)}"
        print_test("Security Headers", passed, details)
        return passed
    except Exception as e:
        print_test("Security Headers", False, f"Error: {str(e)}")
        return False

def test_api_endpoints_exist() -> Tuple[bool, List[str]]:
    """Test that key API endpoints exist (without auth)"""
    endpoints = [
        ("/api/auth/register", "POST"),
        ("/api/auth/login", "POST"),
        ("/api/dashboard/executive", "GET"),
        ("/api/models", "GET"),
        ("/api/triggers", "GET"),
        ("/api/climate/timeseries", "GET"),
        ("/api/risk/portfolio", "GET"),
    ]
    
    results = []
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            
            # We expect 401 (unauthorized), 403 (forbidden), or 422 (validation error) for protected endpoints
            # This confirms the endpoint exists and security is working
            exists = response.status_code in [200, 401, 403, 422]
            results.append((endpoint, exists, response.status_code))
        except Exception as e:
            results.append((endpoint, False, str(e)))
    
    all_exist = all(r[1] for r in results)
    details = "\n  ".join([f"{e}: {s}" for e, _, s in results])
    print_test("API Endpoints Exist", all_exist, details)
    return all_exist, [r[0] for r in results if not r[1]]

def run_verification():
    """Run all verification tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Dashboard System Integration Verification (Task 28){Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    results = []
    
    print(f"{Colors.YELLOW}Testing Core Services...{Colors.END}")
    results.append(("Backend Health", test_backend_health()))
    results.append(("Database Connection", test_database_connection()))
    results.append(("Frontend Accessible", test_frontend_accessible()))
    
    print(f"\n{Colors.YELLOW}Testing API Configuration...{Colors.END}")
    results.append(("API Documentation", test_api_documentation()))
    results.append(("CORS Configuration", test_cors_headers()))
    results.append(("Security Headers", test_security_headers()))
    
    print(f"\n{Colors.YELLOW}Testing API Endpoints...{Colors.END}")
    endpoints_ok, missing = test_api_endpoints_exist()
    results.append(("API Endpoints", endpoints_ok))
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total) * 100
    
    if percentage == 100:
        print(f"{Colors.GREEN}✓ ALL TESTS PASSED ({passed}/{total}){Colors.END}")
        print(f"\n{Colors.GREEN}System is ready for production!{Colors.END}")
        return 0
    elif percentage >= 80:
        print(f"{Colors.YELLOW}⚠ MOSTLY PASSING ({passed}/{total} - {percentage:.0f}%){Colors.END}")
        print(f"\n{Colors.YELLOW}System is functional but has some issues.{Colors.END}")
        return 1
    else:
        print(f"{Colors.RED}✗ TESTS FAILED ({passed}/{total} - {percentage:.0f}%){Colors.END}")
        print(f"\n{Colors.RED}System has critical issues.{Colors.END}")
        return 2

if __name__ == "__main__":
    sys.exit(run_verification())
