# WhisperForge - Main Application Redirect
# 
# This file redirects to the current main application: app_simple.py
# 
# The old OAuth version has been archived

import streamlit as st
import os

# Page config
st.set_page_config(
    page_title="WhisperForge - Redirect",
    page_icon="🌌",
    layout="wide"
)

st.error("""
🔄 **Application Redirect**

You're accessing the old app.py file. The main application has moved to `app_simple.py`.

**Current Status:**
- ✅ Main App: `app_simple.py` (v2.8.0 with large file processing)
- 🔄 This File: Redirect notice

**To run the main app:**
```bash
streamlit run app_simple.py
```

**Note:** The Procfile has been updated to use app_simple.py for production deployment.
""")

st.info("This redirect will be removed in a future version. Please update your bookmarks and scripts to use `app_simple.py`.")

# Show current working directory and available files
st.markdown("### Available Files:")
files = [f for f in os.listdir(".") if f.endswith(".py") and f.startswith("app")]
for file in sorted(files):
    if file == "app_simple.py":
        st.success(f"✅ **{file}** (Main Application)")
    elif "deprecated" in file or "backup" in file:
        st.warning(f"⚠️ **{file}** (Deprecated)")
    else:
        st.info(f"ℹ️ **{file}**") 