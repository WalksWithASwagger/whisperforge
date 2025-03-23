# WhisperForge

WhisperForge is an AI-powered audio transcription and analysis tool that integrates OpenAI's Whisper model with Notion for documentation.

## Features
- Audio file transcription (MP3, WAV, M4A, OGG)
- Automatic chunking of large audio files
- Language detection and support
- Direct export to Notion
- Insights extraction from transcribed content

## Prerequisites
- Python 3.11 (required for audioop support)
- ffmpeg
- OpenAI API key
- Notion API key and integration

## Installation

1. Create Python virtual environment:

```bash
python3.11 -m venv whisperforge-
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install ffmpeg:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

## Configuration
1. Create `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_key_here
NOTION_API_KEY=your_notion_key_here  # Optional if using Notion integration
```

2. Set up Notion integration:
   - Create a new integration at https://www.notion.so/my-integrations
   - Share your target Notion page with the integration

## Usage
Run the Streamlit app:

```bash
streamlit run app.py
```

## Contributing
[Your contribution guidelines here]

## License
[Your chosen license here]

## Development Status
Currently implementing:
- Notion integration for permanent storage
- Monitoring and observability with Prometheus/Grafana
- Service health checks and logging
