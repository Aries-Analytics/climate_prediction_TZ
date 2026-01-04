@echo off
echo ============================================================
echo FORECAST GENERATION - SETUP AND RUN
echo ============================================================
echo.

echo Step 1: Setting up database...
python setup_database.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Database setup failed. Please check the errors above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 2: Running forecast generation...
echo ============================================================
echo.

python scripts\generate_real_forecasts.py

echo.
echo ============================================================
echo DONE!
echo ============================================================
pause
