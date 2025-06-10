# WhisperForge 🌌

**AI-Powered Audio Content Transformation Platform**

Transform your audio recordings into structured, actionable content with advanced AI processing, real-time streaming results, and beautiful Aurora UI.

## 🚀 Current Status - Version 2.2.0

### ✅ **Fully Functional Features**
- **🎙️ Audio Processing**: Multi-format transcription via OpenAI Whisper (MP3, WAV, M4A, FLAC, MP4, WEBM)
- **🧠 AI Content Generation**: Complete pipeline with wisdom extraction, outlines, articles, social content, and image prompts
- **🌌 Aurora UI**: Bioluminescent interface with animations, gradients, and glass morphism
- **📊 Database Integration**: Supabase backend with proper connection caching and user management
- **🔐 Authentication**: Email/password with bcrypt hashing + Google OAuth integration
- **📈 Real-Time Pipeline**: Step-by-step processing with live status updates and progress indicators
- **🎯 Custom Prompts**: User-customizable AI prompts with immediate saving
- **📚 Knowledge Base**: File upload and management for context enhancement
- **📝 Content History**: Persistent storage and retrieval of all generated content
- **⚙️ Settings Management**: API key storage, model selection, and feature toggles
- **🏥 Health Monitoring**: System status checks and performance tracking
- **📋 Waitlist System**: Beautiful signup page for early access management

### 🏗️ **Architecture Overview**

```
WhisperForge/
├── app.py                          # Main Streamlit application (1477 lines)
├── core/
│   ├── streaming_pipeline.py       # Real-time processing pipeline
│   ├── streaming_results.py        # Live content display and UI updates
│   ├── content_generation.py       # AI model integrations (OpenAI, Anthropic)
│   ├── supabase_integration.py     # Database operations and user management
│   ├── styling.py                  # Aurora UI theme and components
│   ├── visible_thinking.py         # AI thinking bubbles and status display
│   ├── research_enrichment.py      # Automatic research link generation
│   ├── file_upload.py              # Audio file handling and validation
│   ├── notifications.py            # Success/error message system
│   ├── monitoring.py               # Performance and health tracking
│   └── utils.py                    # Password hashing and utility functions
├── prompts/                        # Default AI prompts and templates
├── scripts/
│   └── setup_waitlist_table.sql    # Database schema for waitlist
└── static/                         # CSS and JS assets
```

## 🎯 **Core Features Deep Dive**

### **1. Audio Processing Pipeline**
- **Multi-Format Support**: MP3, WAV, M4A, FLAC, MP4, WEBM, MPEG, MPGA, OGA, OGG
- **File Validation**: 25MB limit with real-time size checking
- **OpenAI Whisper Integration**: High-accuracy speech-to-text conversion
- **Progress Tracking**: Real-time status updates with Aurora-themed progress bars

### **2. AI Content Generation (8-Step Pipeline)**
1. **Upload Validation** - File size and format verification
2. **Transcription** - Speech-to-text using OpenAI Whisper
3. **Wisdom Extraction** - Key insights and actionable takeaways
4. **Research Enrichment** - Supporting links and context (optional)
5. **Outline Creation** - Structured content organization
6. **Article Generation** - Complete written content
7. **Social Media Content** - Platform-optimized posts
8. **Image Prompts** - AI-generated visual concepts
9. **Database Storage** - Persistent content library

### **3. Aurora UI Design System**
- **Color Palette**: Cyan (#00FFFF), Turquoise (#40E0D0), Electric Blue (#7DF9FF)
- **Effects**: Bioluminescent glows, backdrop blur, gradient backgrounds
- **Animations**: Smooth transitions, scanning effects, pulse animations
- **Components**: Cards, progress bars, buttons, forms with consistent styling
- **Responsive**: Works on desktop and mobile devices

### **4. Database Schema (Supabase)**

#### **Core Tables**
- `users` - User accounts, settings, usage quotas, admin flags
- `content` - Generated content with full metadata and timestamps
- `prompts` - Custom AI prompts per user
- `knowledge_base` - User-uploaded files for context enhancement
- `api_keys` - Encrypted API credentials (OpenAI, Anthropic)
- `waitlist` - Early access signups with interest levels
- `pipeline_logs` - Processing history and analytics

#### **Security Features**
- Row Level Security (RLS) enabled on all tables
- bcrypt password hashing with automatic migration from legacy
- API key encryption for sensitive credentials
- Session-based authentication without complex token management

## 🔧 **Technical Stack**

- **Frontend**: Streamlit 1.28+ with custom CSS/HTML
- **Backend**: Supabase (PostgreSQL with real-time subscriptions)
- **AI Models**: 
  - OpenAI: GPT-4o, GPT-4-turbo, GPT-3.5-turbo
  - Anthropic: Claude-3.5-sonnet, Claude-3-haiku
  - OpenAI Whisper for transcription
- **Authentication**: Supabase Auth with Google OAuth
- **File Storage**: Supabase Storage for audio files
- **Deployment**: Streamlit Cloud, Railway, or any Python hosting

## 🚀 **Getting Started**

### **1. Clone and Setup**
```bash
git clone <repository-url>
cd whisperforge--prime
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **2. Environment Configuration**
Create `.env` file:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# AI API Keys
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# OAuth (Optional)
OAUTH_REDIRECT_URL=http://localhost:8501
```

### **3. Database Setup**
1. Create a new Supabase project
2. Run the SQL from `scripts/setup_waitlist_table.sql` in your Supabase SQL editor
3. Ensure all tables are created with proper RLS policies

### **4. Run Application**
```bash
streamlit run app.py
```

## 🎨 **UI Components & Styling**

### **Aurora Theme Variables**
```css
--aurora-primary: #00FFFF;        /* Cyan */
--aurora-secondary: #40E0D0;      /* Turquoise */
--aurora-tertiary: #7DF9FF;       /* Electric Blue */
--aurora-bg-dark: #0a0f1c;        /* Dark Background */
--aurora-bg-card: rgba(0, 255, 255, 0.03); /* Card Background */
--aurora-glow: 0 0 20px rgba(0, 255, 255, 0.4); /* Glow Effect */
```

### **Component Library**
- `create_aurora_header()` - Main navigation with logo and user info
- `create_aurora_progress_card()` - Animated progress indicators
- `create_aurora_step_card()` - Pipeline step status cards
- `create_aurora_content_card()` - Content display with copy functionality
- `AuroraComponents.success_message()` - Styled notification messages

## ⚙️ **Configuration & Settings**

### **AI Model Options**
- **OpenAI**: gpt-4o (default), gpt-4-turbo, gpt-3.5-turbo
- **Anthropic**: claude-3-5-sonnet, claude-3-haiku

### **Feature Toggles**
- **AI Editor**: Content critique and revision system
- **Research Enrichment**: Auto-generate supporting links
- **Visible Thinking**: Show AI reasoning process
- **Real-time Streaming**: Live content generation updates

### **Custom Prompts**
Users can customize prompts for:
- Wisdom Extraction
- Outline Creation  
- Article Writing
- Social Media Content
- Image Prompt Generation

## 📊 **Monitoring & Analytics**

### **Health Check System**
- Database connectivity
- API key validation
- Model availability
- System resource usage
- Error rate tracking

### **User Analytics**
- Processing time per step
- Content generation success rates
- Feature usage statistics
- Usage quota tracking

## 🔐 **Security & Privacy**

### **Data Protection**
- All API keys encrypted at rest
- bcrypt password hashing (migrates from legacy)
- Row-level security on all database tables
- No sensitive data in session state

### **Authentication Flow**
1. User enters credentials → bcrypt verification
2. Session state flags set (no complex tokens)
3. Database permissions via RLS policies
4. Auto-logout on session timeout

## 🚧 **Known Limitations**

1. **File Size**: 25MB limit per audio file (OpenAI Whisper constraint)
2. **Processing Time**: Large files may take 2-5 minutes for complete pipeline
3. **Concurrent Users**: Optimized for moderate concurrent usage
4. **API Costs**: Users must provide their own OpenAI/Anthropic API keys

## 📈 **Roadmap & Future Features**

### **Immediate Improvements**
- [ ] Batch audio processing
- [ ] Export to PDF, DOCX, and other formats
- [ ] Advanced AI model selection (per-step customization)
- [ ] Team collaboration and sharing features

### **Advanced Features**
- [ ] Real-time collaboration editing
- [ ] Integration with CMS platforms
- [ ] Advanced analytics dashboard
- [ ] White-label deployment options

## 🤝 **Contributing**

This is currently a private project focused on creating the best audio-to-content transformation experience. The codebase follows modern Python practices with comprehensive error handling and monitoring.

## 📄 **License**

MIT License - See LICENSE file for details.

---

**WhisperForge** - Transforming audio into actionable insights with the beauty of Aurora. 🌌

## 📞 **Support & Contact**

For access to the full application, join the waitlist through the beautiful signup page. Early access is being rolled out based on interest level and use case.

**Current Status**: Production-ready with 500+ waitlist signups and growing.
