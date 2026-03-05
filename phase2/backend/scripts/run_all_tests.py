"""
Run All Tests Script

Runs the complete test suite and generates a summary report.
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def run_tests():
    """Run all tests and generate report"""
    
    print("=" * 80)
    print("AUTOMATED FORECAST PIPELINE - TEST SUITE")
    print("=" * 80)
    print(f"Started: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_categories = [
        {
            "name": "Property-Based Tests",
            "pattern": "test_*_properties.py",
            "description": "Tests with random inputs using Hypothesis"
        },
        {
            "name": "Unit Tests",
            "pattern": "test_*_unit.py",
            "description": "Tests for specific edge cases"
        },
        {
            "name": "Integration Tests",
            "pattern": "test_*_integration.py",
            "description": "End-to-end workflow tests"
        },
        {
            "name": "Other Tests",
            "pattern": "test_*.py",
            "description": "Additional test files"
        }
    ]
    
    results = {}
    
    for category in test_categories:
        print(f"\n{'=' * 80}")
        print(f"Running: {category['name']}")
        print(f"Description: {category['description']}")
        print(f"Pattern: {category['pattern']}")
        print('=' * 80)
        
        try:
            # Run pytest for this category
            result = subprocess.run(
                [
                    sys.executable, "-m", "pytest",
                    f"tests/{category['pattern']}",
                    "-v",
                    "--tb=short",
                    "--maxfail=3"
                ],
                cwd=backend_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            results[category['name']] = {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode == 0:
                print(f"✓ {category['name']} PASSED")
            else:
                print(f"✗ {category['name']} FAILED")
                
        except subprocess.TimeoutExpired:
            print(f"✗ {category['name']} TIMEOUT")
            results[category['name']] = {'returncode': -1, 'error': 'timeout'}
        except Exception as e:
            print(f"✗ {category['name']} ERROR: {e}")
            results[category['name']] = {'returncode': -1, 'error': str(e)}
    
    # Generate summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_passed = sum(1 for r in results.values() if r.get('returncode') == 0)
    total_categories = len(results)
    
    for name, result in results.items():
        status = "✓ PASSED" if result.get('returncode') == 0 else "✗ FAILED"
        print(f"{name}: {status}")
    
    print()
    print(f"Categories Passed: {total_passed}/{total_categories}")
    print(f"Completed: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    
    return total_passed == total_categories


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
