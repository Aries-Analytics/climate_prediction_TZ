@echo off
echo ========================================
echo Backend Setup Script
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

echo.
echo Step 1: Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo Virtual environment created
)

echo.
echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Step 3: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 4: Installing dependencies...
pip install -r requirements.txt

echo.
echo Step 5: Setting up environment file...
if exist .env (
    echo .env file already exists
) else (
    copy .env.example .env
    echo .env file created from template
    echo IMPORTANT: Edit .env file with your configuration
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your database configuration
echo 2. Run: alembic upgrade head (to create database tables)
echo 3. Run: pytest tests/ -v (to run tests)
echo 4. Run: uvicorn app.main:app --reload (to start server)
echo.
echo To activate the virtual environment in the future:
echo   venv\Scripts\activate.bat
echo.
pause
