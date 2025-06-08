# 🌌 WhisperForge

**AI-Powered Audio Content Generation with Aurora Bioluminescent UI**

Transform your audio files into comprehensive digital content using advanced AI. WhisperForge features a real-time streaming pipeline with research enrichment, visible AI thinking bubbles, and a modern Aurora-styled interface.

🌐 **Live Production App**: [whisperforge.ai](https://whisperforge.ai)

---

## ✨ **Current Features**

### **🎙️ Audio Processing Pipeline**
- **Upload**: MP3, WAV, M4A, FLAC, MP4, MOV, AVI support
- **Transcription**: AI-powered speech-to-text
- **Wisdom Extraction**: Key insights and actionable takeaways  
- **Research Enrichment**: Entity extraction with supporting research links
- **Content Outline**: Structured article frameworks
- **Article Generation**: Full long-form content creation
- **Social Content**: Platform-specific posts (Twitter, LinkedIn, Instagram, Facebook, YouTube)
- **Image Prompts**: AI-generated visual concept descriptions

### **🤖 Advanced AI Features**
- **Visible Thinking**: Real-time AI thought bubbles during processing
- **Research Enrichment**: Automatic entity research with curated links
- **Multi-AI Support**: OpenAI, Anthropic, and Grok integration
- **Custom Prompts**: Personalized AI generation templates
- **Knowledge Base**: Upload context files to guide AI output

### **🎨 Aurora UI System**
- **Bioluminescent Design**: Cyan/teal Aurora theme throughout
- **Real-time Streaming**: Live content generation with progress updates
- **Integrated Navigation**: Seamless header with logout/settings
- **Aurora Components**: Consistent styling system across all pages
- **Mobile Optimized**: Responsive design for all devices

### **🔐 Advanced Session Management**
- **Persistent Authentication**: Sessions survive browser refreshes
- **Secure Storage**: Encrypted API keys and user data
- **Google OAuth**: Seamless authentication integration
- **User Profiles**: Personal settings, prompts, and history

---

## 🏗️ **Architecture**

### **Core Modules**
```
core/
├── streaming_pipeline.py      # Real-time processing pipeline
├── streaming_results.py       # Live content display system  
├── research_enrichment.py     # Entity research & link generation
├── visible_thinking.py        # AI thought bubble system
├── session_manager.py         # Advanced session persistence
├── styling.py                 # Aurora UI components & themes
├── content_generation.py      # AI content creation functions
├── supabase_integration.py    # Database & auth backend
├── file_upload.py             # Audio file processing
├── notifications.py           # User feedback system
├── ui_components.py           # Reusable UI elements
├── monitoring.py              # Error tracking & analytics
└── utils.py                   # Shared utilities
```

### **Database (Supabase)**
- **Users**: Authentication, profiles, API keys
- **Content**: Generated content with full history
- **Settings**: Custom prompts, knowledge base files
- **Sessions**: Persistent user sessions across refreshes

### **Frontend**
- **Framework**: Streamlit (Python web app)
- **Styling**: Custom CSS with modern UI components
- **Deployment**: Render.com with automatic GitHub integration

### **Backend**
- **Database**: Supabase (PostgreSQL with real-time features)
- **Authentication**: Supabase Auth + Google OAuth
- **File Storage**: Temporary processing with automatic cleanup
- **API Integration**: Multi-provider AI routing (OpenAI/Anthropic/Grok)

### **Infrastructure**
- **Hosting**: Render.com (auto-scaling, SSL, custom domain)
- **Monitoring**: Sentry (error tracking, performance monitoring)
- **CI/CD**: Automatic deployment on GitHub push
- **Security**: Environment variables, encrypted API keys, bcrypt hashing

---

## 🚀 **Local Development**

### **Prerequisites**
```bash
Python 3.11+
Supabase account with project
AI provider API keys (OpenAI/Anthropic/Grok)
```

### **Setup**
```bash
# Clone and setup
git clone <repository-url>
cd whisperforge--prime

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies  
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Edit .env with your keys

# Run locally
streamlit run app.py
```

### **Required Environment Variables**
```bash
# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# AI Providers (At least one required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key  
GROK_API_KEY=your-grok-key

# Optional
SENTRY_DSN=your-sentry-dsn
ENVIRONMENT=development
```

---

## 🎯 **Key Technical Features**

### **Streaming Pipeline**
- Real-time step-by-step processing with live updates
- Session state persistence across browser refreshes
- Error handling with graceful fallbacks
- Progress tracking with Aurora-styled indicators

### **Research Enrichment**
- Automatic entity extraction (people, organizations, methods)
- AI-generated supporting research links
- "Why this matters" explanations
- Curated "gem" links per entity

### **Visible Thinking**
- Real-time AI thought bubbles during processing
- Aurora-styled chat bubbles with mood colors
- 90-character limit with smart truncation
- Canned fallbacks for robust operation

### **Aurora UI System**
- Consistent bioluminescent design language
- Integrated header with navigation and logout
- Responsive Aurora components
- Professional 2025-style interface

---

## 📊 **Production Status**

### **✅ Fully Operational**
- **Core Pipeline**: 8-step audio-to-content generation
- **UI/UX**: Complete Aurora theme implementation
- **Authentication**: Google OAuth + session persistence
- **Database**: Supabase integration with full CRUD
- **Error Handling**: Comprehensive error tracking and recovery
- **Monitoring**: Sentry integration for production insights

### **🚀 Ready for Deployment**
- **Heroku**: Configured with Procfile
- **Render**: Auto-deploy ready
- **Streamlit Cloud**: Compatible deployment
- **Docker**: Container-ready setup

---

## 🛠️ **Current Development Focus**

Based on user feedback, active development is focused on:

1. **Streaming UX Improvements**: Enhanced real-time content display
2. **History Page Fixes**: Database schema and display improvements  
3. **Processing Indicators**: Better visual feedback during generation
4. **Content Layout**: Modern, engaging result presentation
5. **Session Reliability**: Bulletproof authentication persistence

---

## 📝 **Contributing**

The codebase is actively developed with a focus on:
- Clean, modular architecture
- Comprehensive error handling
- Consistent Aurora design system
- Real-time user experience
- Production-ready deployment

---

## 📄 **License**

See [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using Python, Streamlit, Supabase, and Advanced AI** 