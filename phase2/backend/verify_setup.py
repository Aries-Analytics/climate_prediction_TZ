#!/usr/bin/env python3
"""
Verification script to check if the backend setup is correct
"""
import sys
import os

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} missing: {filepath}")
        return False

def verify_setup():
    """Verify the backend setup"""
    print("=" * 60)
    print("Backend Setup Verification")
    print("=" * 60)
    
    checks = []
    
    # Check core files
    print("\n📁 Core Files:")
    checks.append(check_file_exists("app/main.py", "Main application"))
    checks.append(check_file_exists("app/core/config.py", "Configuration"))
    checks.append(check_file_exists("app/core/database.py", "Database setup"))
    checks.append(check_file_exists("requirements.txt", "Requirements"))
    checks.append(check_file_exists("Dockerfile", "Dockerfile"))
    
    # Check models
    print("\n🗄️  Database Models:")
    checks.append(check_file_exists("app/models/user.py", "User model"))
    checks.append(check_file_exists("app/models/climate_data.py", "Climate data model"))
    checks.append(check_file_exists("app/models/trigger_event.py", "Trigger event model"))
    checks.append(check_file_exists("app/models/model_metric.py", "Model metric model"))
    checks.append(check_file_exists("app/models/model_prediction.py", "Model prediction model"))
    checks.append(check_file_exists("app/models/audit_log.py", "Audit log model"))
    
    # Check services
    print("\n⚙️  Services:")
    checks.append(check_file_exists("app/services/auth_service.py", "Auth service"))
    checks.append(check_file_exists("app/services/dashboard_service.py", "Dashboard service"))
    checks.append(check_file_exists("app/services/model_service.py", "Model service"))
    checks.append(check_file_exists("app/services/trigger_service.py", "Trigger service"))
    checks.append(check_file_exists("app/services/climate_service.py", "Climate service"))
    checks.append(check_file_exists("app/services/risk_service.py", "Risk service"))
    
    # Check API routes
    print("\n🌐 API Routes:")
    checks.append(check_file_exists("app/api/auth.py", "Auth routes"))
    checks.append(check_file_exists("app/api/dashboard.py", "Dashboard routes"))
    checks.append(check_file_exists("app/api/models.py", "Models routes"))
    checks.append(check_file_exists("app/api/triggers.py", "Triggers routes"))
    checks.append(check_file_exists("app/api/climate.py", "Climate routes"))
    checks.append(check_file_exists("app/api/risk.py", "Risk routes"))
    
    # Check tests
    print("\n🧪 Tests:")
    checks.append(check_file_exists("tests/conftest.py", "Test configuration"))
    checks.append(check_file_exists("tests/test_auth.py", "Auth tests"))
    checks.append(check_file_exists("tests/test_models.py", "Model tests"))
    checks.append(check_file_exists("tests/test_triggers.py", "Trigger tests"))
    checks.append(check_file_exists("tests/test_dashboard.py", "Dashboard tests"))
    
    # Check Alembic
    print("\n🔄 Migrations:")
    checks.append(check_file_exists("alembic.ini", "Alembic config"))
    checks.append(check_file_exists("alembic/env.py", "Alembic environment"))
    checks.append(check_file_exists("alembic/versions/001_initial_schema.py", "Initial migration"))
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total) * 100
    
    print(f"Results: {passed}/{total} checks passed ({percentage:.1f}%)")
    
    if passed == total:
        print("✅ All checks passed! Backend setup is complete.")
        return 0
    else:
        print(f"❌ {total - passed} checks failed. Please review the missing files.")
        return 1

if __name__ == "__main__":
    sys.exit(verify_setup())
