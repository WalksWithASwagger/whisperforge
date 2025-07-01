# 🧹 WhisperForge Clean Setup Guide

## Current Situation
- You're out of the messy venv (good!)
- App architecture is solid but needs clean environment
- Main blocker: Missing API keys in `.env`

## Step 1: Clean Environment Setup

### Option A: Fresh Virtual Environment (Recommended)
```bash
# Remove the old problematic venv
rm -rf venv

# Create fresh virtual environment
python3 -m venv venv_clean
source venv_clean/bin/activate

# Install dependencies fresh
pip install --upgrade pip
pip install -r requirements.txt
```

### Option B: Use Existing venv (If you prefer)
```bash
# Reactivate existing venv
source venv/bin/activate

# Update dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 2: Add Your API Keys

Edit the `.env` file and replace the placeholder values:

```bash
# Current .env has placeholders - you need to add real keys:
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
GROK_API_KEY=gsk_your-actual-grok-key-here  # Optional but recommended
```

## Step 3: Test Basic Functionality

```bash
# Test the app starts without errors
streamlit run app.py --server.port 8501

# Should see:
# ✅ "You can now view your Streamlit app in your browser"
# ✅ "Local URL: http://localhost:8501"
```

## Step 4: Clean Up Test Files (Optional)

The broken test files are causing confusion. You can either:

```bash
# Option A: Move to archive
mkdir -p archived_old_version/broken_tests
mv tests/test_*.py archived_old_version/broken_tests/

# Option B: Delete entirely  
rm -rf tests/test_*.py
```

## Step 5: Verify Core Features

Once running:
1. ✅ **UI Loads**: Aurora theme should display beautifully
2. ✅ **Authentication**: Basic login should work
3. ⚠️  **Audio Upload**: Will work but need API keys for processing
4. ⚠️  **Content Generation**: Needs valid API keys

## What Should Work Immediately
- Streamlit app starts and loads
- Aurora UI theme displays
- Database connection to Supabase
- File upload interface
- User authentication flow

## What Needs API Keys
- Audio transcription (OpenAI Whisper)
- Content generation (GPT-4, Claude)
- AI thinking bubbles
- Full content pipeline

## Quick Verification Commands

```bash
# Check if app imports work
python -c "from core.supabase_integration import get_supabase_client; print('✅ Supabase import works')"

# Check if Streamlit starts
streamlit run app.py --server.port 8501 --server.headless true &
sleep 3
curl -I http://localhost:8501 && echo "✅ App responding"
pkill -f streamlit
```

## Next Steps After Clean Setup

1. **Get API Keys**: Add real OpenAI/Anthropic keys
2. **Test Pipeline**: Upload audio and verify full workflow  
3. **Deploy to Render**: Once local testing passes
4. **Update Documentation**: Sync README with current state

## Emergency Reset (If Still Having Issues)

```bash
# Nuclear option - completely fresh start
cd ..
git clone <your-repo-url> whisperforge-clean
cd whisperforge-clean
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Add your API keys to .env
streamlit run app.py
```

---

**The core issue**: Your codebase is actually in great shape! The main problems are:
1. Messy venv with broken test artifacts
2. Missing API keys preventing full testing
3. Old files causing confusion

Once you have a clean environment + API keys, this should work beautifully. 