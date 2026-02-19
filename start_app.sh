#!/bin/bash
set -euo pipefail

# WhisperForge Startup Script
echo "Starting WhisperForge..."

# Auto-load environment variables from .env if present
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Check for required environment variables
if [ -z "${SUPABASE_URL:-}" ] || [ -z "${SUPABASE_ANON_KEY:-}" ]; then
    echo "Missing required environment variables:"
    echo "   Please set SUPABASE_URL and SUPABASE_ANON_KEY before running this script."
    echo "   Example:"
    echo "   export SUPABASE_URL='<your-supabase-url>'"
    echo "   export SUPABASE_ANON_KEY='<your-supabase-anon-key>'"
    exit 1
fi
ENVIRONMENT="${1:-${ENVIRONMENT:-development}}"
export ENVIRONMENT

if [ "$ENVIRONMENT" = "production" ]; then
  export DEBUG="${DEBUG:-false}"
  export LOG_LEVEL="${LOG_LEVEL:-INFO}"
else
  export DEBUG="${DEBUG:-true}"
  export LOG_LEVEL="${LOG_LEVEL:-DEBUG}"
fi

echo "Running in $ENVIRONMENT mode"

echo "Environment variables set"
echo "Supabase URL: [set]"
echo "Supabase Key: [set]"

# Test Supabase connection
echo "Testing Supabase connection..."
python -c "from core.supabase_integration import get_supabase_client; client = get_supabase_client(); print('Supabase connection successful!' if client.test_connection() else 'Connection failed')"

# Start Streamlit app with correct file (app_simple.py is the main app)
echo "Starting WhisperForge on http://localhost:8501"
echo "Press Ctrl+C to stop the app"
echo ""

streamlit run app_simple.py --server.port 8501 --server.address 127.0.0.1
