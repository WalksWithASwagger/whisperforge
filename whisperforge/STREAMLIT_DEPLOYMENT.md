# Streamlit Cloud Deployment Guide

## 🚀 **Deployment Configuration**

### **App Settings:**
- **Main file**: `whisperforge/app_supabase.py`
- **Python version**: 3.9+ (auto-detected from requirements.txt)
- **Branch**: `develop`

### **Required Secrets (Environment Variables):**

In Streamlit Cloud → App Settings → Secrets, add:

```toml
SUPABASE_URL = "https://utyjhedtqaagihuogyuy.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0eWpoZWR0cWFhZ2lodW9neXV5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkzMjEyMDUsImV4cCI6MjA2NDg5NzIwNX0.vpRRn7anpmCokYcje5yJr3r2iC_8s11_LXQcCTgxtR8"

# Note: Google OAuth credentials are configured in Supabase dashboard, NOT as environment variables
```

## 🔐 **Google OAuth Configuration**

### **Google Cloud Console Updates:**

1. **Go to**: https://console.cloud.google.com/
2. **Navigate to**: APIs & Services → Credentials
3. **Edit your OAuth 2.0 Client ID**
4. **Ensure these redirect URIs are added**:
   - `https://utyjhedtqaagihuogyuy.supabase.co/auth/v1/callback` (Supabase)
   - `http://localhost:8507` (local development - optional)

### **Production Redirect URI:**
Once you have your Streamlit Cloud URL, you may also want to add:
```
https://your-app-name.streamlit.app
```

## 📋 **Deployment Checklist**

### **Pre-Deployment:**
- [x] Code pushed to GitHub (`develop` branch)
- [x] `requirements.txt` updated with all dependencies
- [x] Google OAuth configured in Supabase
- [x] Google Cloud Console redirect URIs configured

### **During Deployment:**
- [ ] Connect Streamlit Cloud to GitHub repository
- [ ] Set main file path: `whisperforge/app_supabase.py`  
- [ ] Add environment variables in Secrets tab
- [ ] Deploy and wait for build completion

### **Post-Deployment:**
- [ ] Test app loads without environment variable errors
- [ ] Test Google OAuth login flow
- [ ] Verify user authentication works
- [ ] Check logs for any issues

## 🔍 **Troubleshooting**

### **Environment Variable Errors:**
```
Failed to connect to Supabase: SUPABASE_URL and SUPABASE_ANON_KEY must be set
```
**Solution**: Add the secrets in Streamlit Cloud app settings

### **OAuth Redirect Errors:**
```
Error 400: redirect_uri_mismatch
```
**Solution**: Add production URL to Google Cloud Console redirect URIs

### **Import Errors:**
```
ModuleNotFoundError: No module named 'X'
```
**Solution**: Ensure all dependencies are in `requirements.txt`

## 🎯 **Expected Behavior**

After successful deployment:
1. **App loads** with WhisperForge interface
2. **Google Sign-In button** appears and works
3. **User authentication** creates/updates users in Supabase
4. **Content pipeline** functions with authenticated users
5. **No environment variable errors** in logs

## 📞 **Support**

If you encounter issues:
1. Check Streamlit Cloud app logs
2. Verify all secrets are correctly set
3. Test Google OAuth redirect URIs
4. Ensure Supabase project is accessible 