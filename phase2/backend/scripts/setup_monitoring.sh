#!/bin/bash

# Setup Monitoring Infrastructure Script
# This script sets up Prometheus and Grafana for the Climate EWS

set -e

echo "=========================================="
echo "Climate EWS - Monitoring Setup"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

echo "✓ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed"
    echo "Please install docker-compose and try again"
    exit 1
fi

echo "✓ docker-compose is available"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠ Warning: .env file not found"
    echo "Creating .env from template..."
    cp .env.template .env
    echo "✓ Created .env file"
    echo "⚠ Please edit .env with your configuration before proceeding"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to exit..."
fi

echo ""
echo "Starting monitoring infrastructure..."
echo ""

# Start main services if not already running
echo "1. Starting main services..."
docker-compose -f docker-compose.dev.yml up -d db backend pipeline-scheduler pipeline-monitor

# Wait for services to be healthy
echo "2. Waiting for services to be healthy..."
sleep 10

# Start monitoring services
echo "3. Starting Prometheus and Grafana..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for monitoring services to start
echo "4. Waiting for monitoring services to start..."
sleep 15

# Check service status
echo ""
echo "=========================================="
echo "Service Status"
echo "=========================================="
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Access the monitoring interfaces:"
echo "  • Pipeline Metrics:  http://localhost:9090/metrics"
echo "  • Pipeline Health:   http://localhost:8080/health"
echo "  • Prometheus:        http://localhost:9091"
echo "  • Grafana:           http://localhost:3001"
echo ""
echo "Default Grafana credentials:"
echo "  Username: admin"
echo "  Password: admin (change on first login)"
echo ""
echo "To test alert delivery:"
echo "  docker-compose -f docker-compose.dev.yml exec backend python scripts/test_alerts.py"
echo ""
echo "For detailed setup instructions, see docs/MONITORING_SETUP.md"
echo ""
