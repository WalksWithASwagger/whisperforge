#!/bin/bash
# WhisperForge Test Environment Setup Script
# This script creates a Python virtual environment and installs
# the required dependencies for running tests.

set -e

if [ ! -f requirements.txt ]; then
  echo "Run this script from the project root where requirements.txt is located." >&2
  exit 1
fi

python -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install -r requirements.txt

echo "✅ Test environment ready. Activate it with 'source venv/bin/activate'"
