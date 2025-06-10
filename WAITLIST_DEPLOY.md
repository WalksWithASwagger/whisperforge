# 🚀 Deploy Standalone Waitlist

## Quick Deploy to Render (2 minutes)

### Method 1: Same Account, New Service
1. Go to your Render dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo: `WalksWithASwagger/whisperforge`
4. **Service Name**: `whisperforge-waitlist`
5. **Build Command**: `pip install -r requirements-waitlist.txt`
6. **Start Command**: `streamlit run waitlist.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
7. **Environment Variables**:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   ```
8. Click **"Create Web Service"**

### Result:
- **Main App**: `https://whisperforge.ai` (unchanged)
- **Waitlist**: `https://whisperforge-waitlist.onrender.com`

## Method 2: Streamlit Cloud (Free)
1. Go to **https://share.streamlit.io/**
2. **New app** → Connect GitHub repo
3. **Main file**: `waitlist.py`
4. **Environment variables**: Add your Supabase credentials
5. Deploy

### Result:
- **Waitlist**: `https://your-app.streamlit.app`

## 📧 Share This URL
Once deployed, share the waitlist URL in your emails:
```
https://whisperforge-waitlist.onrender.com
```

Clean, fast, and focused on conversions! 🌟 