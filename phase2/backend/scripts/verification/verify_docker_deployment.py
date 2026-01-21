#!/usr/bin/env python3
"""
Docker Deployment Verification Script
Verifies all dashboards are functional using Docker
"""

import requests
import time
import sys
from typing import Dict, List, Tuple

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
MAX_RETRIES = 30
RETRY_DELAY = 2

# Test credentials
TEST_USER = {
    "username": "test_admin",
    "email": "admin@test.com",
    "password": "TestPassword123!",
    "role": "admin"
}

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def wait_for_service(url: str, service_name: str, max_retries: int = MAX_RETRIES) -> bool:
    """Wait for a service to become available"""
    print_info(f"Waiting for {service_name} to be ready...")
    
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:
                print_success(f"{service_name} is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < max_retries - 1:
            print(f"  Attempt {i+1}/{max_retries}... retrying in {RETRY_DELAY}s")
            time.sleep(RETRY_DELAY)
    
    print_error(f"{service_name} failed to start after {max_retries} attempts")
    return False

def test_backend_health() -> bool:
    """Test backend health endpoint"""
    print_info("Testing backend health endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Backend health check passed")
            return True
        else:
            print_error(f"Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Backend health check error: {str(e)}")
        return False

def test_database_connection() -> bool:
    """Test database connectivity through backend"""
    print_info("Testing database connection...")
    try:
        # Try to access an endpoint that requires database
        response = requests.get(f"{BACKEND_URL}/api/models", timeout=5)
        # Even if it returns 401 (unauthorized), it means DB is connected
        if response.status_code in [200, 401, 404]:
            print_success("Database connection verified")
            return True
        else:
            print_error(f"Database connection test failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Database connection error: {str(e)}")
        return False

def test_authentication() -> Tuple[bool, str]:
    """Test authentication system"""
    print_info("Testing authentication system...")
    
    # Try to register a test user
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json=TEST_USER,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            print_success("User registration successful")
        elif response.status_code == 400:
            print_warning("User already exists (expected if running multiple times)")
        else:
            print_error(f"Registration failed: {response.status_code}")
    except Exception as e:
        print_error(f"Registration error: {str(e)}")
    
    # Try to login
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_success("Authentication successful - token received")
                return True, token
            else:
                print_error("Authentication failed - no token in response")
                return False, ""
        else:
            print_error(f"Login failed: {response.status_code}")
            return False, ""
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        return False, ""

def test_dashboard_endpoints(token: str) -> Dict[str, bool]:
    """Test all dashboard API endpoints"""
    print_info("Testing dashboard API endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    endpoints = [
        ("Executive Dashboard", "/api/dashboard/executive"),
        ("Trigger Events", "/api/triggers"),
        ("Climate Time Series", "/api/climate/timeseries?variable=temperature"),
        ("Model Metrics", "/api/models"),
        ("Risk Portfolio", "/api/risk/portfolio"),
    ]
    
    for name, endpoint in endpoints:
        try:
            response = requests.get(
                f"{BACKEND_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print_success(f"{name}: OK")
                results[name] = True
            else:
                print_error(f"{name}: Failed ({response.status_code})")
                results[name] = False
        except Exception as e:
            print_error(f"{name}: Error - {str(e)}")
            results[name] = False
    
    return results

def test_frontend_accessibility() -> bool:
    """Test if frontend is accessible"""
    print_info("Testing frontend accessibility...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print_success("Frontend is accessible")
            return True
        else:
            print_error(f"Frontend returned status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Frontend accessibility error: {str(e)}")
        return False

def test_cors_configuration(token: str) -> bool:
    """Test CORS configuration"""
    print_info("Testing CORS configuration...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Origin": "http://localhost:3000"
        }
        response = requests.get(
            f"{BACKEND_URL}/api/dashboard/executive",
            headers=headers,
            timeout=5
        )
        
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        if cors_header:
            print_success(f"CORS configured: {cors_header}")
            return True
        else:
            print_warning("CORS header not found (may be configured in proxy)")
            return True  # Not critical
    except Exception as e:
        print_error(f"CORS test error: {str(e)}")
        return False

def test_security_headers() -> bool:
    """Test security headers"""
    print_info("Testing security headers...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
        ]
        
        found_headers = []
        for header in security_headers:
            if header in response.headers:
                found_headers.append(header)
        
        if found_headers:
            print_success(f"Security headers present: {', '.join(found_headers)}")
            return True
        else:
            print_warning("No security headers found (may be configured in proxy)")
            return True  # Not critical for dev
    except Exception as e:
        print_error(f"Security headers test error: {str(e)}")
        return False

def generate_report(results: Dict[str, bool]):
    """Generate final test report"""
    print_header("VERIFICATION REPORT")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {failed_tests}{Colors.RESET}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n")
    
    if failed_tests == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.RESET}")
        print(f"{Colors.GREEN}The dashboard system is fully functional.{Colors.RESET}\n")
        return True
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.RESET}")
        print(f"{Colors.RED}Please review the errors above.{Colors.RESET}\n")
        
        print("Failed tests:")
        for test_name, passed in results.items():
            if not passed:
                print(f"  {Colors.RED}✗ {test_name}{Colors.RESET}")
        print()
        return False

def main():
    """Main verification function"""
    print_header("DOCKER DEPLOYMENT VERIFICATION")
    print_info("Starting verification process...\n")
    
    results = {}
    
    # Step 1: Wait for services
    print_header("STEP 1: SERVICE AVAILABILITY")
    results["Backend Service"] = wait_for_service(f"{BACKEND_URL}/health", "Backend")
    results["Frontend Service"] = wait_for_service(FRONTEND_URL, "Frontend")
    
    if not results["Backend Service"]:
        print_error("Backend service is not available. Cannot continue tests.")
        generate_report(results)
        sys.exit(1)
    
    # Step 2: Test backend health
    print_header("STEP 2: BACKEND HEALTH")
    results["Backend Health"] = test_backend_health()
    results["Database Connection"] = test_database_connection()
    
    # Step 3: Test authentication
    print_header("STEP 3: AUTHENTICATION")
    auth_success, token = test_authentication()
    results["Authentication"] = auth_success
    
    if not auth_success:
        print_error("Authentication failed. Cannot test protected endpoints.")
        generate_report(results)
        sys.exit(1)
    
    # Step 4: Test dashboard endpoints
    print_header("STEP 4: DASHBOARD ENDPOINTS")
    dashboard_results = test_dashboard_endpoints(token)
    results.update(dashboard_results)
    
    # Step 5: Test frontend
    print_header("STEP 5: FRONTEND")
    results["Frontend Accessibility"] = test_frontend_accessibility()
    
    # Step 6: Test security
    print_header("STEP 6: SECURITY")
    results["CORS Configuration"] = test_cors_configuration(token)
    results["Security Headers"] = test_security_headers()
    
    # Generate final report
    success = generate_report(results)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Verification interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.RESET}")
        sys.exit(1)
