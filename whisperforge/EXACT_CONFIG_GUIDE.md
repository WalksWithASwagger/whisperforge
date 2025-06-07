# 📋 Exact Configuration Guide

## Copy-Paste Configuration Values

### 🔵 Google Cloud Console Configuration

**Go to**: [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)

**Create OAuth Client ID** → **Web Application**

#### Authorized JavaScript Origins:
```
http://localhost:8501
https://your-app-name.streamlit.app
```
*Replace `your-app-name` with your actual Streamlit app name*

#### Authorized Redirect URIs:
```
https://utyjhedtqaagihuogyuy.supabase.co/auth/v1/callback
```
*This is your Supabase project's auth callback URL*

---

### 🟢 Supabase Dashboard Configuration  

**Go to**: [Supabase Dashboard - Auth Providers](https://supabase.com/dashboard/project/utyjhedtqaagihuogyuy/auth/providers)

**Enable Google Provider**:
- ✅ **Enabled**: `true`
- **Client ID**: `[paste from Google Console]`
- **Client Secret**: `[paste from Google Console]`
- **Redirect URL**: `https://utyjhedtqaagihuogyuy.supabase.co/auth/v1/callback`

---

### 🌐 Environment Configuration

#### Local Development (.env file):
```env
# Supabase Configuration
SUPABASE_URL=https://utyjhedtqaagihuogyuy.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key

# OAuth will auto-detect localhost:8501
```

#### Streamlit Cloud (Secrets):
```toml
# In your app settings → Secrets
SUPABASE_URL = "https://utyjhedtqaagihuogyuy.supabase.co"
SUPABASE_ANON_KEY = "your-supabase-anon-key"
STREAMLIT_APP_URL = "https://your-actual-app-name.streamlit.app"
```

---

## 🔍 Verification Checklist

### ✅ Google Console:
- [ ] OAuth Client ID created
- [ ] Both localhost and streamlit.app origins added
- [ ] Supabase callback URL added
- [ ] Client ID and Secret copied

### ✅ Supabase Dashboard:
- [ ] Google provider enabled
- [ ] Client ID and Secret pasted
- [ ] Redirect URL matches exactly
- [ ] Configuration saved

### ✅ Environment Setup:
- [ ] Local .env file configured
- [ ] Streamlit secrets configured (for production)
- [ ] App URL updated in secrets

### ✅ Testing:
- [ ] Local development works
- [ ] Production deployment works
- [ ] OAuth flow completes successfully
- [ ] User gets logged in to app

---

## 🚨 Common Issues & Solutions

**Problem**: "Invalid redirect URI"
**Solution**: Make sure URLs match EXACTLY (including https/http)

**Problem**: "Client ID not found"  
**Solution**: Double-check Client ID/Secret in Supabase

**Problem**: "Works locally but not in production"
**Solution**: Update STREAMLIT_APP_URL in secrets

**Problem**: "OAuth provider not configured"
**Solution**: Enable Google provider in Supabase dashboard

---

## 🎯 Final URLs Summary

**Your App URLs**:
- Local: `http://localhost:8501`
- Production: `https://your-app-name.streamlit.app`

**Supabase Callback**: 
- `https://utyjhedtqaagihuogyuy.supabase.co/auth/v1/callback`

**Google Console Setup**: Add all 3 URLs above (origins + callback) 