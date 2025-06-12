#!/bin/bash

# WhisperForge Startup Script
echo "🚀 Starting WhisperForge with real Supabase credentials..."

# Auto-load environment variables from .env if present
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Check for required environment variables
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ Missing required environment variables:"
    echo "   Please set SUPABASE_URL and SUPABASE_ANON_KEY before running this script."
    echo "   Example:"
    echo "   export SUPABASE_URL='<your-supabase-url>'"
    echo "   export SUPABASE_ANON_KEY='<your-supabase-anon-key>'"
    exit 1
fi
export ENVIRONMENT="development"
export DEBUG="true"
export LOG_LEVEL="INFO"

echo "✅ Environment variables set"
echo "🔗 Supabase URL: $SUPABASE_URL"
echo "🔑 Supabase Key: ${SUPABASE_ANON_KEY:0:20}..."

# Test Supabase connection
echo "🧪 Testing Supabase connection..."
python -c "from core.supabase_integration import get_supabase_client; client = get_supabase_client(); print('✅ Supabase connection successful!' if client.test_connection() else '❌ Connection failed')"

# Start Streamlit app
echo "🌐 Starting Streamlit app on http://localhost:8501"
echo "📝 Press Ctrl+C to stop the app"
echo ""

streamlit run app.py --server.port 8501 --server.address 0.0.0.0 