# ⚡ WhisperForge

**AI-Powered Content Generation from Audio**

Transform your audio content into comprehensive digital assets using advanced AI. WhisperForge transcribes, analyzes, and generates multiple content formats from your audio files.

🌐 **Live Production App**: [whisperforge.ai](https://whisperforge.ai)

---

## 🚀 **Current Status**

✅ **Production Ready** - Live at whisperforge.ai  
✅ **Custom Domain** - Fully configured with SSL  
✅ **User Authentication** - Google OAuth + email registration  
✅ **Database Integration** - Supabase backend with user data persistence  
✅ **Enterprise Monitoring** - Sentry error tracking and performance monitoring  
✅ **Multi-AI Support** - OpenAI, Anthropic, and Grok integration  
✅ **Secure** - bcrypt password hashing, encrypted storage  

---

## 🎯 **What WhisperForge Does**

### **📝 Content Pipeline**
1. **Audio Upload** - Supports MP3, WAV, M4A, FLAC, MP4, MOV, AVI
2. **AI Transcription** - High-quality speech-to-text
3. **Wisdom Extraction** - Key insights and actionable takeaways
4. **Content Outline** - Structured article/blog post outlines
5. **Social Media** - Platform-specific posts (Twitter, LinkedIn, Instagram)
6. **Image Prompts** - AI-generated image descriptions

### **🎛️ Features**
- **Custom Knowledge Base** - Upload context files to guide AI generation
- **Custom Prompts** - Personalize AI output for your brand/style
- **Content History** - Save and revisit all generated content
- **API Key Management** - Securely store your AI provider keys
- **Usage Tracking** - Monitor quota and usage patterns

---

## 🏗️ **Architecture**

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

## 🛠️ **Local Development**

### **Prerequisites**
```bash
Python 3.11+
Git
Supabase account
AI provider API keys (OpenAI, Anthropic, or Grok)
```

### **Setup**
```bash
# Clone repository
git clone https://github.com/WalksWithASwagger/whisperforge.git
cd whisperforge

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys and database URLs

# Run locally
streamlit run app.py
```

### **Environment Variables**
```bash
# Database (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
JWT_SECRET=your-random-secret

# Authentication (Required)
OAUTH_REDIRECT_URL=http://localhost:8501  # or your domain

# AI Providers (At least one required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GROK_API_KEY=your-grok-key

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
ENVIRONMENT=development
APP_VERSION=1.0.0
```

---

## 📊 **Monitoring & Health**

### **Health Check**
- **URL**: https://whisperforge.ai/?health
- **Checks**: Database connectivity, AI providers, environment variables

### **Error Tracking**
- **Platform**: Sentry
- **Features**: Real-time error alerts, performance monitoring, user context

### **Analytics**
- **User Actions**: Page views, pipeline executions, feature usage
- **Performance**: Operation timing, AI provider response times
- **Health**: System status, uptime monitoring

---

## 🔐 **Security Features**

✅ **Password Security** - bcrypt hashing with salt  
✅ **API Key Encryption** - Secure storage of user API keys  
✅ **OAuth Integration** - Google sign-in with Supabase Auth  
✅ **Environment Isolation** - Production/development separation  
✅ **Input Validation** - Sanitized user inputs  
✅ **Error Handling** - Graceful degradation without data exposure  

---

## 📈 **Production Metrics**

- **Deployment**: Render.com with auto-scaling
- **Uptime**: Monitored via health checks
- **Performance**: <5s average content generation
- **Security**: Zero known vulnerabilities
- **User Experience**: Google Lighthouse optimized

---

## 🎯 **Next Development Priorities**

1. **💳 Payment Integration** - Stripe subscription billing
2. **🎨 UI Enhancement** - Modern design system
3. **📱 Mobile Optimization** - Responsive design improvements
4. **⚡ Performance** - Caching, async processing
5. **📊 Analytics Dashboard** - User insights and metrics

---

## 🤝 **Contributing**

WhisperForge is actively developed. See [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) for contribution guidelines.

---

## 📄 **License**

See [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using Python, Streamlit, Supabase, and AI** 