#!/usr/bin/env python3
"""
WhisperForge Waitlist - Standalone Page
Beautiful, simple waitlist signup that can be shared via email
"""

import streamlit as st
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config MUST be first
st.set_page_config(
    page_title="WhisperForge - Join the Waitlist",
    page_icon="🌌",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def init_supabase():
    """Initialize Supabase client for waitlist"""
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            return None, False
            
        client = create_client(url, key)
        return client, True
    except Exception as e:
        logger.error(f"Supabase initialization failed: {e}")
        return None, False

def save_waitlist_signup(email: str, name: str = "", interest_level: str = "medium") -> bool:
    """Save waitlist signup to Supabase"""
    try:
        client, success = init_supabase()
        if not success or not client:
            return False
        
        # Check if email already exists
        existing = client.table("waitlist").select("id").eq("email", email).execute()
        if existing.data:
            logger.warning(f"Email already in waitlist: {email}")
            return False
        
        waitlist_data = {
            "email": email,
            "name": name,
            "interest_level": interest_level,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        result = client.table("waitlist").insert(waitlist_data).execute()
        
        if result.data:
            logger.info(f"Waitlist signup successful: {email}")
            return True
        return False
    except Exception as e:
        logger.error(f"Waitlist signup error: {e}")
        return False

def main():
    """Main waitlist page"""
    
    # Hide Streamlit UI elements
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    </style>
    """, unsafe_allow_html=True)
    
    # Aurora theme styling
    st.markdown("""
    <style>
    /* Aurora Theme */
    :root {
        --aurora-primary: #00FFFF;
        --aurora-secondary: #40E0D0;
        --aurora-tertiary: #7DF9FF;
        --aurora-bg-dark: #0a0f1c;
        --aurora-bg-darker: #0d1421;
        --aurora-bg-card: rgba(0, 255, 255, 0.03);
        --aurora-border: rgba(0, 255, 255, 0.15);
        --aurora-border-hover: rgba(0, 255, 255, 0.3);
        --aurora-text: rgba(255, 255, 255, 0.9);
        --aurora-text-muted: rgba(255, 255, 255, 0.6);
        --aurora-glow: 0 0 20px rgba(0, 255, 255, 0.4);
    }
    
    .stApp {
        background: linear-gradient(180deg, var(--aurora-bg-dark) 0%, var(--aurora-bg-darker) 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    }
    
    .waitlist-container {
        max-width: 600px;
        margin: 0 auto;
        padding: 40px 20px;
        text-align: center;
    }
    
    .waitlist-header {
        background: linear-gradient(135deg, var(--aurora-bg-card), rgba(64, 224, 208, 0.08));
        border: 1px solid var(--aurora-border);
        border-radius: 20px;
        padding: 50px 40px;
        margin-bottom: 40px;
        backdrop-filter: blur(20px);
        position: relative;
        overflow: hidden;
    }
    
    .waitlist-header::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--aurora-primary), var(--aurora-secondary), transparent);
        animation: aurora-scan 8s ease-in-out infinite;
    }
    
    .waitlist-logo {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(120deg, var(--aurora-primary), var(--aurora-tertiary), var(--aurora-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: var(--aurora-glow);
        margin-bottom: 20px;
        line-height: 1.2;
    }
    
    .waitlist-subtitle {
        color: var(--aurora-text);
        font-size: 1.3rem;
        margin-bottom: 16px;
        line-height: 1.5;
        font-weight: 500;
    }
    
    .waitlist-description {
        color: var(--aurora-text-muted);
        font-size: 1.1rem;
        line-height: 1.6;
        max-width: 480px;
        margin: 0 auto;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 24px;
        margin: 50px 0;
    }
    
    .feature-card {
        background: var(--aurora-bg-card);
        border: 1px solid var(--aurora-border);
        border-radius: 16px;
        padding: 28px 20px;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        border-color: var(--aurora-border-hover);
        transform: translateY(-4px);
        box-shadow: var(--aurora-glow);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 16px;
        display: block;
    }
    
    .feature-title {
        color: var(--aurora-primary);
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }
    
    .feature-desc {
        color: var(--aurora-text-muted);
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    .form-container {
        background: linear-gradient(135deg, var(--aurora-bg-card), rgba(64, 224, 208, 0.05));
        border: 1px solid var(--aurora-border);
        border-radius: 20px;
        padding: 40px;
        margin: 40px 0;
        backdrop-filter: blur(16px);
    }
    
    .form-title {
        color: var(--aurora-primary);
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 24px;
        text-shadow: var(--aurora-glow);
    }
    
    /* Streamlit form styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid var(--aurora-border) !important;
        border-radius: 12px !important;
        color: var(--aurora-text) !important;
        padding: 16px !important;
        font-size: 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--aurora-border-hover) !important;
        box-shadow: var(--aurora-glow) !important;
    }
    
    .stSelectbox > div > div > div {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid var(--aurora-border) !important;
        border-radius: 12px !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--aurora-primary), var(--aurora-secondary)) !important;
        border: none !important;
        border-radius: 12px !important;
        color: var(--aurora-bg-dark) !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding: 16px 32px !important;
        transition: all 0.3s ease !important;
        text-transform: none !important;
        letter-spacing: 0.5px !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0, 255, 255, 0.3) !important;
    }
    
    .stats-bar {
        background: var(--aurora-bg-card);
        border: 1px solid var(--aurora-border);
        border-radius: 12px;
        padding: 20px;
        margin: 30px 0;
        backdrop-filter: blur(10px);
    }
    
    .stats-text {
        color: var(--aurora-text-muted);
        font-size: 1rem;
    }
    
    .highlight {
        color: var(--aurora-primary);
        font-weight: 600;
    }
    
    @keyframes aurora-scan {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    
    @keyframes aurora-pulse {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .waitlist-container {
            padding: 20px 15px;
        }
        
        .waitlist-header {
            padding: 30px 20px;
        }
        
        .waitlist-logo {
            font-size: 2.5rem;
        }
        
        .form-container {
            padding: 25px;
        }
        
        .feature-grid {
            grid-template-columns: 1fr;
            gap: 16px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main container
    st.markdown('<div class="waitlist-container">', unsafe_allow_html=True)
    
    # Header section
    st.markdown("""
    <div class="waitlist-header">
        <div class="waitlist-logo">WhisperForge 🌌</div>
        <div class="waitlist-subtitle">
            Transform audio into actionable insights
        </div>
        <div class="waitlist-description">
            Join the waitlist for early access to the most advanced AI-powered audio content transformation platform. Turn your recordings into structured articles, social media content, and actionable wisdom.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Features section
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🎙️</div>
            <div class="feature-title">Smart Transcription</div>
            <div class="feature-desc">AI-powered speech-to-text with context understanding and speaker recognition</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">💎</div>
            <div class="feature-title">Wisdom Extraction</div>
            <div class="feature-desc">Automatically identify key insights, quotes, and actionable takeaways</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📋</div>
            <div class="feature-title">Structured Content</div>
            <div class="feature-desc">Generate outlines, articles, and social media posts instantly</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🚀</div>
            <div class="feature-title">Real-time Processing</div>
            <div class="feature-desc">Watch your content transform live with beautiful progress indicators</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Waitlist form
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.markdown('<div class="form-title">Join the Waitlist</div>', unsafe_allow_html=True)
    
    with st.form("waitlist_form", clear_on_submit=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            email = st.text_input(
                "Email Address",
                placeholder="your@email.com",
                help="We'll notify you when early access is available",
                label_visibility="collapsed"
            )
        
        with col2:
            name = st.text_input(
                "Name (Optional)",
                placeholder="Your name",
                label_visibility="collapsed"
            )
        
        interest_level = st.selectbox(
            "How interested are you?",
            ["High - I need this now!", "Medium - Sounds interesting", "Low - Just exploring"],
            help="Help us prioritize early access invitations",
            label_visibility="collapsed"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Join Waitlist", use_container_width=True)
        
        if submitted:
            if not email:
                st.error("Please enter your email address")
            elif "@" not in email or "." not in email:
                st.error("Please enter a valid email address")
            else:
                # Map interest level
                interest_map = {
                    "High - I need this now!": "high",
                    "Medium - Sounds interesting": "medium", 
                    "Low - Just exploring": "low"
                }
                
                # Save to waitlist
                if save_waitlist_signup(email, name, interest_map[interest_level]):
                    st.success("🎉 Welcome to the waitlist! We'll be in touch soon with early access.")
                    st.balloons()
                else:
                    st.error("This email is already on our waitlist! Check your inbox for updates.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Stats section
    st.markdown("""
    <div class="stats-bar">
        <div class="stats-text">
            ✨ <span class="highlight">Early access launching soon</span> • 
            🔒 <span class="highlight">Your email is safe with us</span> • 
            🚀 <span class="highlight">Join 500+ innovators waiting</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; color: rgba(255, 255, 255, 0.5); font-size: 0.9rem;">
        <p>WhisperForge - Transforming audio into actionable insights with AI 🌌</p>
        <p style="margin-top: 10px;">
            <a href="mailto:hello@whisperforge.ai" style="color: var(--aurora-primary); text-decoration: none;">Contact Us</a> • 
            <a href="#" style="color: var(--aurora-primary); text-decoration: none;">Privacy Policy</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 