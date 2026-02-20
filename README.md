# WhisperForge v3.1.0

**Transform audio into structured, intelligent content with AI-powered processing.**

WhisperForge is a Streamlit application that converts audio files into comprehensive content packages including transcripts, insights, articles, and social media posts. Supports files up to 2GB with intelligent chunking and parallel processing.

## Key Features

- **Audio Transcription** - Speech-to-text using OpenAI Whisper
- **Wisdom Extraction** - AI-powered insights and key takeaways
- **Content Outline** - Structured organization and flow
- **Article Generation** - Complete written content from audio
- **Social Media Posts** - Platform-optimized content (5 posts)
- **Notion Integration** - Auto-publish with rich formatting
- **Knowledge Base** - Add custom context from your files
- **Custom Prompts** - Personalize AI output per pipeline step
- **Large File Processing** - Handle files up to 2GB with FFmpeg chunking
- **Real-time Streaming** - Watch content generate step-by-step

## Quick Start

### Prerequisites

- Python 3.11+
- FFmpeg (required for files >100MB)
- Supabase account (for data storage)
- OpenAI API key (for AI processing)

### Installation

#### Automated setup (recommended)

```bash
git clone https://github.com/your-username/whisperforge.git
cd whisperforge
python main.py
```

`main.py` automatically creates a `.venv`, installs dependencies, and launches the app. On subsequent runs it skips setup and starts immediately.

```bash
python main.py --setup          # Force re-create the venv
python main.py --setup --dev    # Re-create venv with dev/test dependencies
python main.py -- --server.port 8080   # Forward args to Streamlit
```

#### Manual setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app_simple.py
```

### Configuration

Copy the example env file and fill in your values:

```bash
cp env.example .env
```

Required variables:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
```

Optional variables:

```env
NOTION_API_KEY=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
SENTRY_DSN=your_sentry_dsn
ENVIRONMENT=development          # or production
DEBUG=true
LOG_LEVEL=DEBUG
```

## Content Pipeline

1. **Transcription** - OpenAI Whisper speech-to-text
2. **Wisdom Extraction** - Key insights and takeaways
3. **Outline Creation** - Structured content organization
4. **Article Generation** - Complete written content
5. **Social Media** - 5 platform-optimized posts
6. **Notion Publishing** - Auto-publish with formatted pages

## Project Structure

```
whisperforge/
├── main.py                    # App launcher (auto-setup + run)
├── setup.py                   # Venv creation and dependency installer
├── app_simple.py              # Main Streamlit application
├── app.py                     # Redirect to main app
├── core/                      # Core modules
│   ├── content_generation.py  # AI content generation
│   ├── streaming_pipeline.py  # Step-by-step processing
│   ├── streaming_results.py   # Real-time content display
│   ├── file_upload.py         # Large file processing
│   ├── supabase_integration.py# Database operations
│   ├── auth_wrapper.py        # Authentication
│   ├── visible_thinking.py    # AI thinking bubbles
│   ├── session_manager.py     # User session handling
│   ├── styling.py             # Aurora UI components
│   └── ...
├── shared/                    # Shared config and security utilities
├── prompts/                   # Default and custom AI prompts
├── static/                    # CSS, JS, and assets
├── scripts/                   # Utility and audit scripts
├── tests/                     # Test suite
├── docs/                      # Documentation
├── requirements.txt           # Production dependencies
└── requirements-dev.txt       # Dev/test dependencies (includes production)
```

## Testing

Install dev dependencies:

```bash
python main.py --setup --dev
# or manually:
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest                                     # All tests
pytest -m unit                             # Unit tests only
pytest -m integration                      # Integration tests
pytest tests/test_basic_functionality.py -v  # Specific file
```

## Technical Stack

- **Frontend**: Streamlit with custom Aurora CSS
- **Backend**: Supabase (PostgreSQL)
- **AI**: OpenAI GPT-4 + Whisper
- **Auth**: Supabase Auth
- **Deployment**: Streamlit Cloud / Render.com

## Security

Recent hardening includes:

- HTML content sanitization (XSS prevention)
- JWT validation with PyJWT (replaced python-jose)
- XSRF protection enabled
- Server bound to localhost by default
- No hardcoded credentials in source
- Input validation on file uploads

## Documentation

- [Large File Processing Guide](docs/LARGE_FILE_PROCESSING_v2.8.0.md)
- [Critical Fixes Report](docs/CRITICAL_FIXES_REPORT_v2.8.0.md)
- [Monitoring Setup](docs/monitoring.md)
- [Changelog](CHANGELOG.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
