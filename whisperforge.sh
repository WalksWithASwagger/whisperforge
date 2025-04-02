#!/bin/bash

# WhisperForge Unified Control Script
# Manages WhisperForge in both development and production modes

# Default settings
MODE=${MODE:-dev}
DEV_PORT=8501
PROD_PORT=9000

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "${BLUE}"
    echo "▄       ▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ "
    echo "▐░▌     ▐░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░░░░░░░░░░▌▐░░░░░░░░░░░▐░░░░░░░░░░░▌"
    echo "▐░▌     ▐░▌▀▀▀▀█░█▀▀▀▀▐░█▀▀▀▀▀▀▀█░▐░█▀▀▀▀▀▀▀█░▐░█▀▀▀▀▀▀▀▀▀▐░█▀▀▀▀▀▀▀█░▐░█▀▀▀▀▀▀▀█░▐░█▀▀▀▀▀▀▀█░▐░█▀▀▀▀▀▀▀▀▀▐░█▀▀▀▀▀▀▀█░▌"
    echo "▐░▌     ▐░▌    ▐░▌    ▐░▌       ▐░▐░▌       ▐░▐░▌         ▐░▌       ▐░▐░▌       ▐░▐░▌       ▐░▐░▌         ▐░▌       ▐░▌"
    echo "▐░█▄▄▄▄▄█░▌    ▐░▌    ▐░█▄▄▄▄▄▄▄█░▐░█▄▄▄▄▄▄▄█░▐░█▄▄▄▄▄▄▄▄▄▐░▌       ▐░▐░█▄▄▄▄▄▄▄█░▐░█▄▄▄▄▄▄▄█░▐░▌ ▄▄▄▄▄▄▄▄▐░█▄▄▄▄▄▄▄█░▌"
    echo "▐░░░░░░░░░▌    ▐░▌    ▐░░░░░░░░░░░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░▌       ▐░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░▌▐░░░░░░░░▐░░░░░░░░░░░▌"
    echo "▐░█▀▀▀▀▀█░▌    ▐░▌    ▐░█▀▀▀▀▀▀▀█░▐░█▀▀▀▀█░█▀▀▐░█▀▀▀▀▀▀▀▀▀▐░▌       ▐░▐░█▀▀▀▀█░█▀▀▐░█▀▀▀▀▀▀▀█░▐░▌ ▀▀▀▀▀▀█░▐░█▀▀▀▀▀▀▀█░▌"
    echo "▐░▌     ▐░▌    ▐░▌    ▐░▌       ▐░▐░▌     ▐░▌ ▐░▌         ▐░▌       ▐░▐░▌     ▐░▌ ▐░▌       ▐░▐░▌       ▐░▐░▌       ▐░▌"
    echo "▐░▌     ▐░▌▄▄▄▄█░█▄▄▄▄▐░▌       ▐░▐░▌      ▐░▌▐░█▄▄▄▄▄▄▄▄▄▐░█▄▄▄▄▄▄▄█░▐░▌      ▐░▌▐░▌       ▐░▐░█▄▄▄▄▄▄▄█░▐░▌       ▐░▌"
    echo "▐░▌     ▐░▐░░░░░░░░░░░▐░▌       ▐░▐░▌       ▐░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░▌       ▐░▐░▌       ▐░▐░░░░░░░░░░░▐░▌       ▐░▌"
    echo " ▀       ▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀         ▀ ▀         ▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀         ▀ ▀         ▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀         ▀ "
    echo -e "${NC}"
}

function print_usage() {
    echo "WhisperForge Control Script"
    echo ""
    echo "Usage: $0 COMMAND"
    echo ""
    echo "Commands:"
    echo "  dev         Start in development mode with live code reloading (port $DEV_PORT)"
    echo "  prod        Start in production mode (port $PROD_PORT)"
    echo "  stop        Stop all WhisperForge containers"
    echo "  logs        Show logs (follow mode)"
    echo "  build       Rebuild Docker images"
    echo "  shell       Open a shell in the container"
    echo "  backup      Create a backup of the database"
    echo "  status      Show running containers status"
    echo ""
    echo "Environment Variables:"
    echo "  MODE        Set to 'dev' or 'prod' (default: $MODE)"
}

function start_dev() {
    echo -e "${GREEN}Starting WhisperForge in DEVELOPMENT mode...${NC}"
    echo "This mode enables live code reloading (http://localhost:$DEV_PORT)"
    
    # Build the base image first
    docker-compose build
    
    # Start with the development overlay
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
}

function start_prod() {
    echo -e "${GREEN}Starting WhisperForge in PRODUCTION mode...${NC}"
    echo "Application will be available at http://localhost:$PROD_PORT"
    
    # Use the production script (without code mounting)
    ./docker-utils.sh build && ./docker-utils.sh start
}

function show_status() {
    echo -e "${BLUE}WhisperForge Container Status:${NC}"
    docker ps --filter "name=whisperforge"
}

# Main execution
print_header

case "$1" in
    dev)
        start_dev
        ;;
    prod)
        start_prod
        ;;
    stop)
        echo -e "${YELLOW}Stopping WhisperForge containers...${NC}"
        docker-compose down
        ;;
    logs)
        echo -e "${BLUE}Showing container logs (Ctrl+C to exit)...${NC}"
        docker-compose logs -f
        ;;
    build)
        echo -e "${GREEN}Building WhisperForge containers...${NC}"
        docker-compose build
        ;;
    shell)
        echo -e "${BLUE}Opening a shell in the container...${NC}"
        docker-compose exec whisperforge bash
        ;;
    backup)
        echo -e "${GREEN}Creating database backup...${NC}"
        ./docker-utils.sh backup
        ;;
    status)
        show_status
        ;;
    *)
        print_usage
        exit 1
        ;;
esac 