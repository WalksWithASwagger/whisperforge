# WhisperForge Development Guide

This document outlines the recommended development workflow for WhisperForge using a Docker-based approach with live code reloading. This approach provides the benefits of a consistent development environment while still allowing for rapid iterations.

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your system
- Git
- A text editor or IDE (VSCode recommended)
- Basic knowledge of Python and Streamlit

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/whisperforge.git
   cd whisperforge
   ```

2. Copy the environment template and configure your API keys:
   ```bash
   cp .env.template .env
   ```
   
   Edit the `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   NOTION_API_KEY=your_key_here
   NOTION_DATABASE_ID=your_db_id_here
   ```

3. Make the control scripts executable:
   ```bash
   chmod +x whisperforge.sh dev-mode.sh docker-utils.sh
   ```

## Development Workflow

WhisperForge now uses a unified approach that allows you to choose between development mode (with live code reloading) and production mode.

### Starting Development Mode

Run the following command to start WhisperForge in development mode:

```bash
./whisperforge.sh dev
```

This will:
1. Build the Docker image if needed
2. Mount your local code directory into the container
3. Start Streamlit with live reloading enabled
4. Make the application available at http://localhost:8501

In this mode, any changes you make to the code will be immediately reflected in the running application without having to restart the container.

### How Development Mode Works

The development mode uses Docker Compose with two configuration files:

1. `docker-compose.yml` - Base configuration
2. `docker-compose.dev.yml` - Development overrides

The key features enabled in development mode are:

- **Code Bind Mount**: Your local code directory is mounted into the container
- **Live Reloading**: Streamlit watches for file changes and automatically restarts
- **Consistent Port**: Always uses port 8501 for development 

### Common Development Tasks

#### Viewing Logs

```bash
./whisperforge.sh logs
```

#### Opening a Shell in the Container

```bash
./whisperforge.sh shell
```

#### Stopping the Application

```bash
./whisperforge.sh stop
```

#### Checking Container Status

```bash
./whisperforge.sh status
```

## Database and Files

### Location of Key Files

In development mode, persistent data is stored in Docker volumes:

- **Database**: `whisperforge-data` volume, mapped to `/app/data` in the container
- **Uploads**: `whisperforge-uploads` volume, mapped to `/app/uploads` in the container
- **Temp Files**: `whisperforge-temp` volume, mapped to `/app/temp` in the container
- **Logs**: `whisperforge-logs` volume, mapped to `/app/logs` in the container

Your local code directory is mounted at `/app` in the container, so any changes you make to the code are immediately reflected.

### Backing Up Your Data

To create a backup of all persistent data:

```bash
./whisperforge.sh backup
```

This will create a timestamped backup file in your current directory.

## Production Mode

When you're ready to test your application in a production-like environment:

```bash
./whisperforge.sh prod
```

This will:
1. Build a clean Docker image with your code
2. Start WhisperForge without code mounting (using the built image)
3. Make the application available at http://localhost:9000

## Best Practices

### Code Organization

- Keep related functionality in separate modules
- Use relative imports when importing from other modules
- Follow the existing project structure
- Document new functionality with docstrings

### Testing Changes

1. Make your changes in development mode
2. Test functionality using the development server
3. When satisfied, rebuild in production mode to test with a clean environment

### Common Issues and Solutions

#### Container Won't Start

Check for syntax errors in your Python code. In development mode, the container might not start if there are syntax errors.

```bash
python -m py_compile app.py
```

#### Changes Not Reflecting

If your changes aren't showing up:

1. Check if you're running in development mode (`./whisperforge.sh dev`)
2. Try refreshing the browser
3. Check the logs for errors (`./whisperforge.sh logs`)

#### Database Issues

If you need to reset your database:

```bash
# Start a shell in the container
./whisperforge.sh shell

# Inside the container, delete the database file
rm /app/data/whisperforge.db

# Exit the shell
exit

# Restart the application
./whisperforge.sh stop
./whisperforge.sh dev
```

## Advanced Usage

### Custom Environment Variables

You can add custom environment variables in the `.env` file. They will be available in both development and production modes.

### Modifying Docker Configuration

If you need to modify the Docker configuration:

1. Development-specific changes should go in `docker-compose.dev.yml`
2. Base changes that apply to both modes should go in `docker-compose.yml`

### Adding Dependencies

If you add new Python dependencies:

1. Add them to `requirements.txt`
2. Rebuild the Docker image: `./whisperforge.sh build`
3. Restart in development mode: `./whisperforge.sh dev` 