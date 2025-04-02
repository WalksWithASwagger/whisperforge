#!/bin/bash
set -e

echo "Starting WhisperForge Docker environment"
echo "Using database path: $DATABASE_PATH"

# Ensure directories exist
mkdir -p /app/data /app/uploads /app/temp /app/logs
echo "Directories created/verified"

# Source environment variables from .env file
if [ -f ".env" ]; then
    echo "Loading API keys from .env file"
    export $(grep -v '^#' .env | xargs)
fi

# Wait for the directory to be available (especially when mounting Docker volumes)
while [ ! -d "$(dirname $DATABASE_PATH)" ]; do
    echo "Waiting for data directory to be available..."
    sleep 1
done

# Initialize the database if it doesn't exist
if [ ! -f "$DATABASE_PATH" ]; then
    echo "Initializing database at $DATABASE_PATH"
    python -c "from app import init_db; init_db()"
    echo "Database initialized"
fi

# Check if there are admin users with NULL api_keys and update them
echo "Checking for admin users with NULL api_keys"
python -c "from app import init_admin_user; init_admin_user()"

# Create environment file for Streamlit
env | grep -E 'OPENAI|ANTHROPIC|NOTION|GROK|API' > /app/.env.streamlit
echo "Environment variables prepared for Streamlit"

# Start the app
echo "Starting Streamlit application..."
export STREAMLIT_ENV_FILE="/app/.env.streamlit"
exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0 