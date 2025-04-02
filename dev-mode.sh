#!/bin/bash

# WhisperForge Development Mode Script
# Starts the application with live code reloading

echo "Starting WhisperForge in DEVELOPMENT mode..."
echo "This will mount your local code into the container for live reloading."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running or not installed."
    echo "Please start Docker and try again."
    exit 1
fi

# Ensure we have the latest base image
echo "Building base WhisperForge image..."
docker-compose build

# Start in development mode with live code reloading
echo "Starting development environment (with live code reloading)..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# This script will stay attached to the container logs
# Use Ctrl+C to exit 