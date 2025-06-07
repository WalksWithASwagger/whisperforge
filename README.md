# 🎙️ WhisperForge - SATURDAY BAILOUT

> **Transform spoken ideas into comprehensive content with AI assistance**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](./whisperforge/VERSION)
[![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.38.0-red.svg)](https://streamlit.io)

WhisperForge is an AI-powered audio transcription and content creation pipeline designed for streamlining the process of turning spoken thoughts into polished, publishable content. Built with OpenAI's Whisper for transcription and multiple LLM providers for content enhancement.

## 🚀 Features

### 🎯 Core Pipeline (6 Stages)
1. **Audio Input Processing** - File validation, chunking for large files (>25MB), format support
2. **Audio Transcription** - OpenAI Whisper integration with parallel processing
3. **Content Generation** - AI-powered wisdom extraction, outlines, social content, image prompts, articles
4. **Content Enhancement** - SEO metadata, tagging, token usage tracking
5. **Export and Storage** - Notion database integration, structured organization
6. **Results and Distribution** - Multi-tab display, copy/download functionality

### 🤖 Multi-AI Provider Support
- **OpenAI** - GPT-4, GPT-3.5-turbo, Whisper
- **Anthropic** - Claude models
- **Grok** - X.AI integration
- **Configurable** - Easy to add new providers

### 📊 Advanced Features
- **Knowledge Base System** - Custom context injection
- **Custom Prompts** - Personalized content generation
- **Supabase Integration** - Complete database backend with analytics
- **MCP Integration** - Model Context Protocol support
- **Caching System** - Optimized performance
- **Progress Tracking** - Real-time pipeline monitoring

## 🏗️ Architecture

### Modular Core System
```
whisperforge/
├── core/                    # Modular architecture
│   ├── __init__.py         # Core exports
│   ├── config.py           # Configuration management
│   ├── pipeline.py         # Main pipeline orchestration
│   ├── processors.py       # Audio/content processing
│   ├── integrations.py     # AI provider integrations
│   ├── content_generation.py  # Content creation logic
│   ├── supabase_integration.py  # Database operations
│   ├── utils.py            # Utility functions
│   └── styling.py          # UI components
├── app.py                  # Main Streamlit application
├── app_supabase.py        # Supabase-enabled version
├── requirements.txt        # Dependencies
└── *.sql                  # Database schemas
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- API keys for your chosen AI providers
- (Optional) Notion API key and database ID
- (Optional) Supabase project for database backend

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd SATURDAY-BAILOUT/whisperforge
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp env.example .env
# Edit .env with your API keys
```

5. **Run the application**
```bash
streamlit run app.py
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file with your API keys:

```env
# Required: AI Providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
XAI_API_KEY=your_grok_key_here

# Optional: Notion Integration
NOTION_API_KEY=your_notion_key_here
NOTION_DATABASE_ID=your_database_id

# Optional: Supabase Integration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional: JWT Authentication
JWT_SECRET_KEY=your_jwt_secret_key
```

### Supabase Setup
For full database functionality:

1. Create a Supabase project
2. Run the schema setup:
```sql
-- Copy and run supabase_schema.sql in your Supabase SQL editor
```
3. Configure Row Level Security policies
4. Update your `.env` with Supabase credentials

## 📖 Usage Guide

### Basic Workflow
1. **Upload Audio** - Drop your audio file (MP3, WAV, OGG, M4A)
2. **Select AI Provider** - Choose your preferred model
3. **Transcribe** - Get AI-powered transcription
4. **Generate Content** - Create wisdom, outlines, social posts, articles
5. **Export** - Save to Notion or download locally

### Advanced Features

#### Custom Knowledge Base
- Add domain-specific context
- Enhance content generation with your expertise
- Persistent storage across sessions

#### Custom Prompts
- Personalize content generation
- Create templates for specific use cases
- Version control for prompt iterations

#### Batch Processing
- Handle large audio files (auto-chunking)
- Process multiple files
- Progress tracking and error handling

## 🗄️ Database Schema

The project includes comprehensive database schemas:

- **Users & Authentication** - JWT-based user management
- **Content Storage** - Transcripts, generated content, metadata
- **Knowledge Base** - Custom context and domain knowledge
- **Custom Prompts** - User-defined generation templates
- **Analytics** - Usage tracking, pipeline performance
- **Audit Logs** - Complete activity tracking

## 🧪 Testing

Run the included tests:
```bash
python test_notion.py      # Test Notion integration
python test_supabase.py    # Test Supabase connectivity
```

## 📋 Changelog

See [CHANGELOG.md](./whisperforge/changelog.md) for version history and updates.

## 📄 License

See [LICENSE](./whisperforge/LICENSE) for details.

## 🎯 Project Status: SATURDAY BAILOUT Ready

This project is fully prepared for weekend refactoring with [Loveable](https://loveable.dev):

### ✅ Audit Complete
- [x] Code compilation verified
- [x] Core modules tested
- [x] Dependencies confirmed
- [x] Architecture documented
- [x] Git repository initialized
- [x] Comprehensive documentation

### 🎮 Ready for Refactoring
- **Modular Architecture** - Clean separation of concerns
- **Complete Pipeline** - 6-stage content generation system
- **Multi-AI Support** - Provider abstraction layer
- **Database Integration** - Full Supabase backend
- **Documentation** - Comprehensive README and comments
- **Version Control** - Ready for collaborative development

---

**🚀 Let's turn those weekend ideas into production-ready content! 🚀** 