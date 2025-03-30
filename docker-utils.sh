#!/bin/bash

case "$1" in
  build)
    echo "Building Docker image..."
    docker-compose build
    ;;
  start)
    echo "Starting WhisperForge application..."
    docker-compose up -d
    echo "Application started. Access it at http://localhost:9000"
    ;;
  stop)
    echo "Stopping WhisperForge application..."
    docker-compose down
    ;;
  restart)
    echo "Restarting WhisperForge application..."
    docker-compose restart
    ;;
  logs)
    echo "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
    ;;
  shell)
    echo "Opening shell in container..."
    docker-compose exec whisperforge bash
    ;;
  backup)
    echo "Creating backup of data volume..."
    BACKUP_FILE="whisperforge-data-$(date +%Y%m%d_%H%M%S).tar.gz"
    docker run --rm -v whisperforge-data:/data -v $(pwd):/backup alpine tar -czf "/backup/$BACKUP_FILE" /data
    echo "Backup created: $BACKUP_FILE"
    ;;
  *)
    echo "WhisperForge Docker Utilities"
    echo "Usage: $0 {build|start|stop|restart|logs|shell|backup}"
    exit 1
esac 