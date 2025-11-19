#!/bin/bash

# Run all tests with coverage
echo "Running tests..."
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed!"
    exit 1
fi
