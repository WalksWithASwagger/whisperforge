#!/bin/bash
# Run the main WhisperForge app locally
# Usage: ./run_main_app.sh

echo "🌌 Starting WhisperForge Main App..."
echo "🔗 App will be available at: http://localhost:8501"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Run the main app
streamlit run app_main.py --server.port=8501 --server.address=0.0.0.0 