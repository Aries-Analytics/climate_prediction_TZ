#!/bin/bash
# Dashboard Setup Script
# Sets up and loads data into the dashboard

set -e

echo "=========================================="
echo "Dashboard Data Integration Setup"
echo "=========================================="
echo ""

# Step 1: Start database
echo "Step 1: Starting PostgreSQL database..."
docker-compose -f docker-compose.dev.yml up -d db
echo "Waiting for database to be ready..."
sleep 5
echo "✓ Database started"
echo ""

# Step 2: Run migrations
echo "Step 2: Running database migrations..."
cd backend
alembic upgrade head
echo "✓ Migrations complete"
echo ""

# Step 3: Load data
echo "Step 3: Loading data..."
python scripts/load_all_data.py --clear
echo "✓ Data loaded"
echo ""

# Step 4: Seed users
echo "Step 4: Creating users..."
python scripts/seed_users.py
echo "✓ Users created"
echo ""

# Step 5: Verify
echo "Step 5: Verifying data..."
python scripts/verify_data.py
echo "✓ Verification complete"
echo ""

# Step 6: Start all services
echo "Step 6: Starting all services..."
cd ..
docker-compose -f docker-compose.dev.yml up -d
echo "✓ All services started"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Access the dashboard at: http://localhost:3000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
echo "Default credentials:"
echo "  Admin: admin / admin123"
echo "  Analyst: analyst / analyst123"
echo "  Viewer: viewer / viewer123"
echo ""
echo "To view logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "To stop: docker-compose -f docker-compose.dev.yml down"
echo "=========================================="
