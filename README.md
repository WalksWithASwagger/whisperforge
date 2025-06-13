# WhisperForge v2.8.0 🌌

**Transform audio into structured, intelligent content with AI-powered processing**

WhisperForge is a powerful Streamlit application that converts audio files into comprehensive content packages including transcripts, insights, articles, and social media posts. Now with **revolutionary large file processing** supporting files up to **2GB**.

## ✨ Key Features

- 🎙️ **Audio Transcription** - High-quality speech-to-text using OpenAI Whisper
- 💡 **Wisdom Extraction** - AI-powered insights and key takeaways
- 🔍 **Research Enrichment** - Entity extraction with curated research links
- 📋 **Content Outline** - Structured organization and flow
- 📰 **Article Generation** - Complete written content from audio
- 📱 **Social Media Posts** - Platform-optimized content
- 🖼️ **Image Prompts** - AI-generated visual concepts
- 📝 **Editor Review** - Quality enhancement with AI critique
- 📚 **Notion Integration** - Automatic publishing to Notion workspace
- 🚀 **Large File Processing** - Handle files up to 2GB with intelligent chunking
- 🌊 **Real-time Streaming** - Watch content generate step-by-step
- 🎨 **Aurora Theme** - Beautiful bioluminescent UI design

## 🏗️ Project Structure

```
whisperforge--prime/
├── app_simple.py          # Main Streamlit application (v2.8.0)
├── app.py                 # Redirect to main app
├── core/                  # Core functionality modules
│   ├── content_generation.py
│   ├── file_upload.py     # Enhanced large file processing
│   ├── research_enrichment.py
│   ├── supabase_integration.py
│   └── ...
├── prompts/               # Custom AI prompts
├── static/                # CSS, JS, and assets
├── tests/                 # Test suite
├── docs/                  # Documentation
└── requirements.txt       # Dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Supabase account (for data storage)
- OpenAI API key (for AI processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/whisperforge.git
   cd whisperforge
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application**
   ```bash
   streamlit run app_simple.py
   ```

## 🔧 Configuration

Create a `.env` file with your API keys:

```env
# Required
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key

# Optional
ANTHROPIC_API_KEY=your_anthropic_api_key
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
```

## 🎯 Usage

1. **Upload Audio** - Support for MP3, WAV, M4A, and video files up to 2GB
2. **Choose Processing Mode** - Standard (≤25MB) or Enhanced Large File (≤2GB)
3. **Watch Real-time Processing** - See content generate step-by-step
4. **Review Results** - Comprehensive content package with all outputs
5. **Auto-publish** - Optional Notion integration for seamless publishing

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest tests/test_basic_functionality.py -v  # Specific test file
```

## 📚 Documentation

- [Large File Processing Guide](docs/LARGE_FILE_PROCESSING_v2.8.0.md)
- [Development Workflow](archived_docs/DEVELOPMENT_WORKFLOW.md)
- [API Documentation](docs/API.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for Whisper and GPT models
- Supabase for backend infrastructure
- Streamlit for the amazing web framework
- The open-source community for inspiration and tools

---

**WhisperForge v2.8.0** - Transform your audio into intelligent content 🌌

## 🎯 **Architecture Overview**

```
├── app_simple.py          # Main Streamlit application (v2.8.0)
├── app.py                 # Redirect to main app
├── core/
│   ├── streaming_pipeline.py    # Step-by-step content processing
│   ├── streaming_results.py     # Real-time content display
│   ├── content_generation.py    # AI content generation functions
│   ├── supabase_integration.py  # Database operations
│   ├── visible_thinking.py      # AI thinking bubbles
│   ├── session_manager.py       # User session handling
│   └── styling.py              # Aurora UI components
└── prompts/                # Default and custom AI prompts
```

## 🌊 **Core Features**

### **1. Real-Time Audio Processing**
- Upload audio files (MP3, WAV, M4A, FLAC, etc.)
- Automatic transcription using OpenAI Whisper
- Progressive content generation with live updates

### **2. Enhanced AI Content Pipeline**
1. **Transcription** - Speech-to-text conversion
2. **Wisdom Extraction** - Key insights and takeaways
3. **Outline Creation** - Structured content organization
4. **Article Generation** - Complete written content
5. **Social Media** - Platform-optimized posts
6. **🌌 Notion Publishing** - Auto-publish to Notion with beautiful formatting
7. **Database Storage** - Persistent content library with Supabase

### **3. Modern Aurora Interface**
- Bioluminescent 2025 design system
- Real-time progress indicators
- Animated content cards
- Responsive Aurora color scheme

## 🔧 **Technical Stack**

- **Frontend**: Streamlit with custom Aurora CSS
- **Backend**: Supabase (PostgreSQL)
- **AI Models**: OpenAI GPT-4, Anthropic Claude
- **Audio Processing**: OpenAI Whisper
- **Authentication**: Supabase Auth + OAuth
- **Deployment**: Streamlit Cloud ready

## 🚀 **Getting Started**

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd whisperforge--prime
   ```

2. **Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   Create `.env` file or set environment variables:
   ```env
   # Required - Supabase Database
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key  # Optional for admin features
   
   # Required - AI Providers (at least one)
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   GROK_API_KEY=your_grok_key  # Optional
   
   # Notion Integration - Auto-Publishing
   NOTION_API_KEY=your_notion_integration_token
   NOTION_DATABASE_ID=your_notion_database_id
   
   # Optional - OAuth & Integrations
   OAUTH_REDIRECT_URL=http://localhost:8501  # For OAuth flows
   
   # Optional - Security & Monitoring
   JWT_SECRET=your_jwt_secret_key
   SENTRY_DSN=your_sentry_dsn  # For error tracking
   
   # Optional - Development
   DEBUG=true
   LOG_LEVEL=INFO
   ENVIRONMENT=development
   ```

4. **Run Application**
   ```bash
   streamlit run app_simple.py
   ```

## 🎨 **Aurora Design System**

The WhisperForge UI uses a custom Aurora design system featuring:

- **Bioluminescent Effects**: Glowing borders and animations
- **Gradient Backgrounds**: Dynamic color transitions
- **Glass Morphism**: Backdrop blur effects
- **Responsive Cards**: Animated content containers
- **Progress Streams**: Real-time processing indicators

## 📊 **Database Schema**

### **Core Tables**
- `users` - User accounts and settings
- `content` - Generated content and metadata  
- `prompts` - Custom AI prompts
- `knowledge_base` - User-uploaded files
- `api_keys` - Encrypted API credentials

## 🔐 **Security Features**

- **Encrypted Storage**: API keys and sensitive data
- **Session Management**: Secure user sessions
- **Input Validation**: File size and type restrictions
- **Rate Limiting**: API usage controls

## 🛡 **Current Known Issues**

1. **Database Content Retrieval**: 26 processed files not displaying in history (investigating field name mismatches)
2. **Real-time Streaming**: Content shows but not truly real-time like cursor chat
3. **Session Persistence**: Authentication doesn't persist across refreshes consistently
4. **Prompt Saving**: Custom prompts saving but not loading properly
5. **Thinking Bubbles**: AI thinking stream not integrating smoothly

## 🔄 **Debugging Tools**

The content history page includes debug information:
- Database connection status
- Raw record samples
- Session state inspection
- Content structure analysis

## 📈 **Roadmap**

### **Immediate Fixes**
- [ ] Fix content history display issues
- [ ] Implement true real-time streaming
- [ ] Resolve session persistence
- [ ] Debug prompt saving/loading

### **Enhancements**
- [ ] Batch audio processing
- [ ] Export to multiple formats
- [ ] Advanced AI model selection
- [ ] Team collaboration features

## 💡 **Contributing**

This is currently a private project focused on creating the best audio-to-content transformation experience with a beautiful, modern interface.

## 📄 **License**

MIT License - See LICENSE file for details.

---

**WhisperForge** - Transforming audio into actionable insights with the beauty of Aurora. 🌌 

## 🏗 **Architecture (Simplified)**

### **Session Management**
```python
# Simple, reliable pattern
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

@st.cache_resource  
def init_supabase():
    return get_supabase_client()
```

### **Database Pattern**
- **Supabase Client**: Cached with `@st.cache_resource`
- **User Data**: Loaded fresh each session (not cached in session state)
- **Content Storage**: Direct to database, no complex state management

### **Authentication Flow**
1. User enters credentials → Verify against Supabase
2. Set simple session state flags → No tokens or complex persistence  
3. Load user preferences from database → Use `@st.cache_data` for performance 