@echo off
REM Setup Monitoring Infrastructure Script (Windows)
REM This script sets up Prometheus and Grafana for the Climate EWS

echo ==========================================
echo Climate EWS - Monitoring Setup
echo ==========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running
    echo Please start Docker and try again
    exit /b 1
)

echo Docker is running

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Error: docker-compose is not installed
    echo Please install docker-compose and try again
    exit /b 1
)

echo docker-compose is available

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found
    echo Creating .env from template...
    copy .env.template .env
    echo Created .env file
    echo Warning: Please edit .env with your configuration before proceeding
    echo.
    pause
)

echo.
echo Starting monitoring infrastructure...
echo.

REM Start main services if not already running
echo 1. Starting main services...
docker-compose -f docker-compose.dev.yml up -d db backend pipeline-scheduler pipeline-monitor

REM Wait for services to be healthy
echo 2. Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Start monitoring services
echo 3. Starting Prometheus and Grafana...
docker-compose -f docker-compose.monitoring.yml up -d

REM Wait for monitoring services to start
echo 4. Waiting for monitoring services to start...
timeout /t 15 /nobreak >nul

REM Check service status
echo.
echo ==========================================
echo Service Status
echo ==========================================
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.monitoring.yml ps

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Access the monitoring interfaces:
echo   - Pipeline Metrics:  http://localhost:9090/metrics
echo   - Pipeline Health:   http://localhost:8080/health
echo   - Prometheus:        http://localhost:9091
echo   - Grafana:           http://localhost:3001
echo.
echo Default Grafana credentials:
echo   Username: admin
echo   Password: admin (change on first login)
echo.
echo To test alert delivery:
echo   docker-compose -f docker-compose.dev.yml exec backend python scripts/test_alerts.py
echo.
echo For detailed setup instructions, see docs/MONITORING_SETUP.md
echo.
pause
