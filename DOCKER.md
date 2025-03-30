# WhisperForge Docker Setup

This document provides instructions for running WhisperForge in Docker.

## Prerequisites

1. Docker Engine installed on your system
2. Docker Compose installed on your system
3. API keys for required services (OpenAI, Anthropic, etc.)

## Setup Instructions

### 1. Prepare Environment Variables

Create a `.env` file with your API keys and configuration:

```bash
cp .env.template .env
```

Edit the `.env` file and add your actual API keys and settings.

### 2. Build the Docker Image

```bash
./docker-utils.sh build
```

Or manually:

```bash
docker-compose build
```

### 3. Start the Application

```bash
./docker-utils.sh start
```

Or manually:

```bash
docker-compose up -d
```

The application will be available at http://localhost:9000

### 4. View Logs

```bash
./docker-utils.sh logs
```

Or manually:

```bash
docker-compose logs -f
```

### 5. Stop the Application

```bash
./docker-utils.sh stop
```

Or manually:

```bash
docker-compose down
```

## Data Persistence

All data is stored in Docker volumes for persistence:

- `whisperforge-data`: Database and data files
- `whisperforge-uploads`: User uploads
- `whisperforge-temp`: Temporary files
- `whisperforge-logs`: Application logs
- `./prompts` (bind mount): Prompt templates and knowledge base

## Backup and Restore

### Create a Backup

To back up the data volume:

```bash
./docker-utils.sh backup
```

Or manually:

```bash
docker run --rm -v whisperforge-data:/data -v $(pwd):/backup alpine tar -czf /backup/whisperforge-data-$(date +%Y%m%d_%H%M%S).tar.gz /data
```

### Restore from Backup

To restore from a backup:

```bash
# Replace backup-file.tar.gz with your actual backup filename
docker run --rm -v whisperforge-data:/data -v $(pwd):/backup alpine sh -c "rm -rf /data/* && tar -xzf /backup/backup-file.tar.gz -C /"
```

## Troubleshooting

### Container Not Starting

Check the logs for errors:

```bash
docker-compose logs
```

### API Key Issues

Make sure your `.env` file contains valid API keys.

### Database Issues

You can access the running container to inspect the database:

```bash
docker-compose exec whisperforge bash
```

From inside the container:

```bash
sqlite3 /app/data/whisperforge.db
```

### No Space Left on Device

Docker volumes might be filling up your disk. You can clean up unused volumes:

```bash
docker volume prune
``` 