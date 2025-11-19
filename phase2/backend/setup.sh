#!/bin/bash

echo "========================================"
echo "Backend Setup Script"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

echo ""
echo "Step 1: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo "Virtual environment created"
fi

echo ""
echo "Step 2: Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Step 3: Upgrading pip..."
python -m pip install --upgrade pip

echo ""
echo "Step 4: Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Step 5: Setting up environment file..."
if [ -f ".env" ]; then
    echo ".env file already exists"
else
    cp .env.example .env
    echo ".env file created from template"
    echo "IMPORTANT: Edit .env file with your configuration"
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database configuration"
echo "2. Run: alembic upgrade head (to create database tables)"
echo "3. Run: pytest tests/ -v (to run tests)"
echo "4. Run: uvicorn app.main:app --reload (to start server)"
echo ""
echo "To activate the virtual environment in the future:"
echo "  source venv/bin/activate"
echo ""
