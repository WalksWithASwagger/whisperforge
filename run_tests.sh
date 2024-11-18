#!/bin/bash
set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Add the project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Load environment variables
export $(cat .env.test | xargs)

# Run the test script
python -m tests.test_storage

# Deactivate virtual environment
deactivate