# WhisperForge Quick Reference Guide

## Development Workflow

### Start Development Mode (with live reloading)
```bash
./whisperforge.sh dev
```
- Access at http://localhost:8501
- Changes to code reload automatically
- Terminal shows real-time logs

### Start Production Mode
```bash
./whisperforge.sh prod
```
- Access at http://localhost:9000
- Clean environment with built image

### Common Commands

| Command | Description |
|---------|-------------|
| `./whisperforge.sh status` | Show running containers |
| `./whisperforge.sh logs` | View container logs |
| `./whisperforge.sh shell` | Open a shell in the container |
| `./whisperforge.sh stop` | Stop all containers |
| `./whisperforge.sh build` | Rebuild Docker images |
| `./whisperforge.sh backup` | Create a backup of your data |

## Development Tips

### Making Code Changes
1. Start in development mode: `./whisperforge.sh dev`
2. Edit code with your favorite editor
3. Save changes and they reload automatically
4. View logs in a separate terminal: `./whisperforge.sh logs`

### Fixing Common Issues

**Changes not reloading:**
- Try refreshing the browser
- Check logs for errors: `./whisperforge.sh logs`
- Restart the container: `./whisperforge.sh stop && ./whisperforge.sh dev`

**Database issues:**
```bash
# Access container shell
./whisperforge.sh shell

# Inside container:
rm /app/data/whisperforge.db
exit

# Restart
./whisperforge.sh stop
./whisperforge.sh dev
```

**Adding new dependencies:**
1. Add to requirements.txt
2. Rebuild: `./whisperforge.sh build`
3. Restart: `./whisperforge.sh dev`

## Documentation
- Full development guide: [DEVELOPMENT.md](DEVELOPMENT.md)
- Project overview: [README.md](README.md)
- Docker specifics: [DOCKER.md](DOCKER.md)

## Environment Setup
- API keys are stored in `.env` file
- Database is in Docker volume: `whisperforge-data`
- Uploads stored in Docker volume: `whisperforge-uploads` 