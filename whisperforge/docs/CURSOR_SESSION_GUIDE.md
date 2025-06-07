# WhisperForge: Cursor Session Guide

## 🎯 PROJECT INTENTIONS & VISION

### Primary Goal
Transform **WhisperForge** from a working prototype into a **production-ready SaaS product** that automatically converts audio content into comprehensive, multi-format content for content creators, marketers, and businesses.

### User's Vision
- **Target Market**: Content creators, marketers, podcasters, businesses
- **Value Proposition**: Upload audio → Get complete content package (transcripts, articles, social posts, images)
- **Business Model**: Freemium SaaS with tiered subscriptions ($9-$99/month)
- **Timeline**: 12-week development roadmap to launch

### Current Status (v1.0-alpha)
- ✅ **Working MVP deployed** on Streamlit Cloud
- ✅ **Repository cleaned and organized** 
- ✅ **Development workflow established**
- ✅ **Core pipeline functional** (audio → content generation)
- 🚧 **Ready for feature development** following roadmap

---

## 🏗️ ARCHITECTURE OVERVIEW

### Core Pipeline (6 Stages)
1. **Audio Input Processing**: File upload, validation, chunking strategy
2. **Audio Transcription**: OpenAI Whisper with smart chunking
3. **Content Generation Pipeline**: 5 sequential sub-stages:
   - Wisdom extraction from transcript
   - Outline creation using transcript + wisdom  
   - Social media content generation
   - Image prompt creation
   - Full article writing
4. **Content Enhancement**: SEO metadata and tagging
5. **Export and Storage**: Notion database integration
6. **Results and Distribution**: Multi-tab display with copy/download

### Tech Stack
- **Frontend**: Streamlit (current), planned migration to React/Next.js
- **Backend**: Python, FastAPI (planned)
- **Database**: Supabase (PostgreSQL)
- **AI Providers**: OpenAI, Anthropic, Grok (multi-provider support)
- **Storage**: Supabase Storage
- **Deployment**: Streamlit Cloud (current), planned Docker/AWS

---

## 📁 DIRECTORY STRUCTURE

```
whisperforge/
├── app_supabase.py              # Main Streamlit application (CURRENT ENTRY POINT)
├── app.py                       # Legacy main app (173KB, 4294 lines)
├── core/                        # Business logic modules
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── pipeline.py             # Main content generation pipeline
│   ├── processors.py           # Content processors (audio, text, image)
│   ├── integrations.py         # External service integrations
│   ├── utils.py                # Utility functions
│   └── supabase_integration.py # Supabase database operations
├── src/                        # Future organized code structure
│   ├── whisperforge/           # Core package
│   └── config/                 # Configuration files
├── tests/                      # All test files
│   ├── __init__.py
│   ├── test_notion.py          # Notion integration tests
│   └── test_supabase.py        # Supabase integration tests
├── docs/                       # Documentation
├── static/                     # Static assets (CSS, JS, images)
├── scripts/                    # Utility scripts
├── data/                       # Data files, cache, uploads
├── temp/                       # Temporary files
├── uploads/                    # User uploaded files
├── generated_images/           # AI-generated images
├── exports/                    # Export files
├── requirements.txt            # Python dependencies
├── env.example                 # Environment variables template
├── supabase_schema.sql         # Database schema
└── deployment/                 # Deployment configurations
```

---

## 🔧 CORE FUNCTIONS & COMPONENTS

### Main Application (`app_supabase.py`)
**Entry Point**: Primary Streamlit application with Supabase integration

**Key Functions**:
- `main()`: Application entry point with navigation
- `show_file_upload()`: Audio file upload interface
- `process_audio_pipeline()`: Main content generation workflow
- `show_results()`: Display generated content in tabs

### Core Pipeline (`core/pipeline.py`)
**Purpose**: Orchestrates the 6-stage content generation pipeline

**Key Functions**:
- `run_content_pipeline()`: Main pipeline orchestrator
- `extract_wisdom()`: Extract key insights from transcript
- `create_outline()`: Generate content outline
- `generate_social_content()`: Create social media posts
- `create_image_prompts()`: Generate image descriptions
- `write_full_article()`: Create comprehensive article

### Processors (`core/processors.py`)
**Purpose**: Handle specific content processing tasks

**Key Classes**:
- `AudioProcessor`: Audio file handling and transcription
- `TextProcessor`: Text analysis and content generation
- `ImageProcessor`: Image prompt generation and management

### Integrations (`core/integrations.py`)
**Purpose**: External service integrations

**Key Classes**:
- `OpenAIIntegration`: OpenAI API wrapper
- `AnthropicIntegration`: Anthropic Claude integration
- `NotionIntegration`: Notion database operations
- `SupabaseIntegration`: Database and storage operations

### Configuration (`core/config.py`)
**Purpose**: Centralized configuration management

**Key Features**:
- Environment variable loading
- AI provider configurations
- Database connection settings
- Feature flags and settings

### Utilities (`core/utils.py`)
**Purpose**: Common utility functions

**Key Functions**:
- `chunk_audio()`: Smart audio file chunking
- `validate_file()`: File validation and security
- `format_content()`: Content formatting utilities
- `handle_errors()`: Error handling and logging

---

## 🔑 CRITICAL ENVIRONMENT VARIABLES

### Required for Basic Functionality
```bash
# Supabase (Required)
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_ANON_KEY="your-supabase-anon-key"

# AI Providers (At least OpenAI required)
OPENAI_API_KEY="sk-your-openai-key"
ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"  # Optional
GROK_API_KEY="your-grok-key"                   # Optional

# Security
JWT_SECRET="your-jwt-secret"                   # Required for auth

# Optional Integrations
NOTION_API_KEY="secret_your-notion-key"
NOTION_DATABASE_ID="your-database-id"

# Settings
DEBUG="false"
LOG_LEVEL="INFO"
```

### Streamlit Cloud Secrets Format
```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-supabase-anon-key"
OPENAI_API_KEY = "sk-your-openai-key"
JWT_SECRET = "your-jwt-secret"
```

---

## 🗃️ DATABASE SCHEMA (Supabase)

### Core Tables
```sql
-- Users and Authentication
users (id, email, created_at, subscription_tier, usage_stats)

-- Content Processing
content_jobs (id, user_id, status, audio_file_url, metadata)
transcripts (id, job_id, text, language, confidence_score)
generated_content (id, job_id, content_type, content, metadata)

-- Knowledge Base
knowledge_base (id, user_id, title, content, tags, embeddings)
custom_prompts (id, user_id, name, prompt_text, category)

-- Analytics
usage_analytics (id, user_id, feature, usage_count, timestamp)
```

### Key Relationships
- `content_jobs` → `transcripts` (1:1)
- `content_jobs` → `generated_content` (1:many)
- `users` → `content_jobs` (1:many)
- `users` → `knowledge_base` (1:many)

---

## 🎨 USER INTERFACE STRUCTURE

### Current Streamlit Interface
```python
# Main Navigation
├── 📁 File Upload Tab
│   ├── Audio file uploader
│   ├── File validation
│   └── Processing controls
├── ⚙️ Configuration Tab  
│   ├── AI provider selection
│   ├── Custom prompts
│   └── Processing options
├── 📊 Results Tab
│   ├── Transcript display
│   ├── Generated content tabs
│   ├── Export options
│   └── Notion integration
└── 👤 User Management
    ├── Authentication
    ├── Usage statistics  
    └── Subscription management
```

### Planned React/Next.js Interface
- Modern, responsive design
- Real-time progress indicators
- Drag-and-drop file upload
- Advanced content editing
- Collaborative features

---

## 🚀 DEVELOPMENT WORKFLOW

### Git Branching Strategy
```
main           # Production-ready, auto-deploys to Streamlit Cloud
├── develop    # Integration branch for features
├── feature/*  # New feature development
├── hotfix/*   # Critical production fixes
└── release/*  # Release preparation
```

### Development Process
1. **Start Feature**: `git checkout -b feature/feature-name develop`
2. **Develop**: Follow code standards, write tests
3. **Submit**: Create PR to develop branch
4. **Review**: Code review and testing
5. **Merge**: Merge to develop, then release to main

### Code Standards
- **Python**: Black formatting, type hints, docstrings
- **Testing**: pytest, >80% coverage
- **Documentation**: Update docs with changes
- **Security**: No hardcoded secrets, proper error handling

---

## 🎯 CURRENT PRIORITIES & ROADMAP

### Phase 1: Foundation (Week 1-2) ✅ COMPLETED
- [x] Repository cleanup and organization
- [x] Development workflow establishment  
- [x] Documentation creation
- [x] Production deployment

### Phase 2: Core Enhancement (Week 3-4) 🚧 CURRENT
**Immediate Next Steps**:
1. **UI/UX Redesign**: Modern interface, progress indicators
2. **Error Handling**: Comprehensive error management
3. **User Authentication**: Proper login/signup system
4. **Content Preview**: Preview before processing

### Phase 3: Advanced Features (Week 5-6)
- Batch processing capabilities
- Custom prompt templates
- Content scheduling
- Analytics dashboard

### Phase 4: Production Ready (Week 7-8)
- Payment processing (Stripe)
- Monitoring and alerts
- Performance optimization
- Security hardening

### Phase 5: Launch & Scale (Week 9-12)
- Beta testing program
- Marketing website
- Customer support
- Growth optimization

---

## 🔧 DEVELOPMENT GUIDELINES FOR CURSOR SESSIONS

### When Starting a New Session
1. **Check current branch**: `git status` and `git branch`
2. **Review recent commits**: `git log --oneline -5`
3. **Check deployment status**: Verify Streamlit Cloud is working
4. **Read GETTING_STARTED.md** for latest context

### Code Change Best Practices
1. **Always create feature branch** from develop
2. **Test changes locally** before committing
3. **Update documentation** for significant changes
4. **Follow naming conventions**: Clear, descriptive names
5. **Add type hints and docstrings** for new functions

### Testing Before Deployment
```bash
# Local testing
streamlit run whisperforge/app_supabase.py

# Run tests
python -m pytest whisperforge/tests/

# Check code quality
black whisperforge/
flake8 whisperforge/
```

### Common Development Tasks

#### Adding New AI Provider
1. Create integration class in `core/integrations.py`
2. Add configuration in `core/config.py`
3. Update UI selection in main app
4. Add tests in `tests/`

#### Adding New Content Type
1. Create processor in `core/processors.py`
2. Add pipeline stage in `core/pipeline.py`
3. Update UI results display
4. Add database schema if needed

#### UI Improvements
1. Modify Streamlit components in `app_supabase.py`
2. Update CSS in `static/css/`
3. Test on different screen sizes
4. Ensure accessibility compliance

---

## 🐛 COMMON ISSUES & SOLUTIONS

### Deployment Issues
- **Requirements conflicts**: Update `requirements.txt` with compatible versions
- **Environment variables**: Check Streamlit Cloud secrets configuration
- **Memory limits**: Optimize large file processing

### Database Issues  
- **Connection errors**: Verify Supabase credentials
- **Schema changes**: Run migrations via Supabase dashboard
- **Performance**: Check query optimization and indexes

### AI Provider Issues
- **Rate limits**: Implement retry logic and backoff
- **API errors**: Add proper error handling and fallbacks
- **Cost management**: Track usage and implement limits

---

## 📈 BUSINESS CONTEXT

### Revenue Model
- **Freemium**: 10 hours/month free
- **Starter**: $9/month (50 hours)
- **Pro**: $29/month (200 hours + advanced features)
- **Enterprise**: $99/month (unlimited + API access)

### Key Metrics to Track
- Monthly Active Users (MAU)
- Content processing volume
- Feature adoption rates
- Customer acquisition cost
- Churn rate and retention

### Competitive Advantages
- Multi-AI provider support
- Comprehensive content pipeline
- Notion integration
- Custom prompt templates
- Batch processing capabilities

---

## 🎯 SUCCESS CRITERIA

### Technical Success
- 99.9% uptime on Streamlit Cloud
- <30 second processing time for 10MB audio
- >80% code test coverage
- Zero security vulnerabilities

### Business Success  
- 1000+ active users by month 3
- $10K MRR by month 6
- <5% monthly churn rate
- 4.5+ star user rating

### User Success
- Intuitive, self-service interface
- High-quality content generation
- Reliable, fast processing
- Excellent customer support

---

## 📞 GETTING HELP

### When Things Break
1. **Check logs**: Streamlit Cloud logs and local console
2. **Verify environment**: Ensure all required variables are set
3. **Test locally**: Reproduce issue in development
4. **Check git history**: Review recent changes

### Resources
- **Roadmap**: `CLEANUP_AND_ROADMAP.md`
- **Workflow**: `DEVELOPMENT_WORKFLOW.md`
- **Getting Started**: `GETTING_STARTED.md`
- **This Guide**: Complete context and intentions

### Development Philosophy
- **User-first**: Every change should improve user experience
- **Quality over speed**: Better to ship fewer, higher-quality features
- **Data-driven**: Use analytics to guide development decisions
- **Security-conscious**: Always consider security implications

---

*This guide preserves the complete context and intentions for WhisperForge development. Always refer to this when starting new Cursor sessions to maintain continuity and alignment with the project vision.*

**Last Updated**: June 2024  
**Version**: v1.0-alpha  
**Next Session Goal**: Begin Phase 2 core enhancements 