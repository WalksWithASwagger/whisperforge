# 🚀 Getting Started with WhisperForge

**Quick start guide for the production-ready AI content generation platform**

---

## 🌐 **Try It Live**

**Production App**: [whisperforge.ai](https://whisperforge.ai)

No setup required! Create an account and start generating content immediately.

---

## 🎯 **What You'll Need**

### **For Using the Live App**
- **Google Account** (for OAuth sign-in) OR email address
- **AI API Key** from at least one provider:
  - OpenAI (recommended)
  - Anthropic Claude
  - Grok (X.AI)

### **For Local Development**
- Python 3.11+
- Git
- Supabase account (free tier works)
- AI provider API keys

---

## ⚡ **Quick Start (Using Live App)**

### **Step 1: Create Account**
1. Visit [whisperforge.ai](https://whisperforge.ai)
2. Click "🔵 Sign in with Google" OR register with email
3. Complete account setup

### **Step 2: Add API Keys**
1. Go to **Settings** → **API Keys**
2. Add your OpenAI, Anthropic, or Grok API key
3. Click **Save**

### **Step 3: Generate Content**
1. Upload an audio file (MP3, WAV, M4A, etc.)
2. Select your AI provider and model
3. Click **Start Pipeline**
4. Watch as AI generates:
   - Transcription
   - Key insights
   - Content outline
   - Social media posts
   - Image prompts

**That's it!** Your content is automatically saved to your account.

---

## 🎨 **Advanced Features**

### **Custom Knowledge Base**
1. **Settings** → **Knowledge Base**
2. Upload text/markdown files with your context
3. AI will use this context in all content generation

### **Custom Prompts**
1. **Settings** → **Custom Prompts**
2. Modify AI prompts for your specific use case
3. Personalize output style and format

### **Content History**
- All generated content is saved automatically
- Access via **Content History** page
- Search and organize your creations

---

## 🛠️ **Local Development Setup**

### **Prerequisites**
```bash
# Check Python version
python --version  # Should be 3.11+

# Install Git if needed
git --version
```

### **Clone and Setup**
```bash
# Clone repository
git clone https://github.com/WalksWithASwagger/whisperforge.git
cd whisperforge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **Environment Configuration**
```bash
# Create environment file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your favorite editor
```

**Required Environment Variables:**
```bash
# Supabase (create free account at supabase.com)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
JWT_SECRET=your-random-secret-here

# OAuth (for local testing)
OAUTH_REDIRECT_URL=http://localhost:8501

# AI Providers (get from respective providers)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GROK_API_KEY=your-grok-key

# Optional: Monitoring
SENTRY_DSN=your-sentry-dsn
ENVIRONMENT=development
```

### **Run Locally**
```bash
# Start the application
streamlit run app.py

# App will open at http://localhost:8501
```

---

## 🔧 **Configuration Tips**

### **AI Provider Setup**

#### **OpenAI (Recommended)**
1. Visit [platform.openai.com](https://platform.openai.com)
2. Create API key with billing enabled
3. Models: GPT-4, GPT-3.5-turbo (for transcription: Whisper)

#### **Anthropic Claude**
1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Create API key
3. Models: Claude-3-Sonnet, Claude-3-Haiku

#### **Grok (X.AI)**
1. Visit [x.ai](https://x.ai)
2. Request API access
3. Models: Grok-1, Grok-2

### **Supabase Setup**
1. Create free account at [supabase.com](https://supabase.com)
2. Create new project
3. Copy URL and keys from Settings → API
4. Database schema is auto-created on first run

---

## 🎯 **First Content Generation**

### **Test Audio File**
Use any of these formats:
- **MP3** (most common)
- **WAV** (high quality)
- **M4A** (Apple/iPhone recordings)
- **FLAC** (lossless)
- **MP4/MOV** (video with audio)

### **Recommended Test**
1. Record 2-3 minutes of yourself explaining a concept
2. Upload to WhisperForge
3. Use OpenAI GPT-4 for generation
4. Review all generated content types

### **What You'll Get**
- **Transcription**: Accurate speech-to-text
- **Wisdom**: Key insights and takeaways
- **Outline**: Structured content outline
- **Social Posts**: Platform-optimized content
- **Image Prompts**: AI-generated visual descriptions

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **"API Key Not Configured"**
- Check your API key is correctly entered in Settings
- Verify the key has proper permissions and billing enabled

#### **"Supabase Connection Failed"**
- Verify SUPABASE_URL and keys in environment
- Check Supabase project is active

#### **"Audio Upload Failed"**
- Supported formats: MP3, WAV, M4A, FLAC, MP4, MOV, AVI
- Maximum file size: ~100MB (automatically chunked)

#### **OAuth Issues**
- For local development, use http://localhost:8501
- For production, ensure correct redirect URL in Supabase auth settings

### **Getting Help**
- **Health Check**: Visit /?health to see system status
- **Logs**: Check browser console for error details
- **Support**: Contact via GitHub issues

---

## 🎉 **You're Ready!**

WhisperForge is designed to be intuitive and powerful. Start with the live app at [whisperforge.ai](https://whisperforge.ai) and explore all the features.

**Happy content creating!** 🚀 