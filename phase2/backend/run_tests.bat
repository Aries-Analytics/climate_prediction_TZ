@echo off
REM Run all tests with coverage
echo Running tests...
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

if %ERRORLEVEL% EQU 0 (
    echo All tests passed!
) else (
    echo Some tests failed!
    exit /b 1
)
