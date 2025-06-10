# WhisperForge - Join the Waitlist
# Beautiful landing page for waitlist signups

import streamlit as st

# Page config MUST be first
st.set_page_config(
    page_title="WhisperForge - Transform Your Voice Into Wisdom",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
import logging
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Supabase integration
try:
    from core.supabase_integration import get_supabase_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase integration not available")

def apply_waitlist_theme():
    """Apply beautiful aurora theme for the waitlist landing page"""
    st.markdown("""
    <style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Aurora Theme Variables */
    :root {
        --aurora-primary: #00FFFF;
        --aurora-secondary: #40E0D0;
        --aurora-tertiary: #7DF9FF;
        --aurora-accent: #8A2BE2;
        --aurora-bg-dark: #0a0f1c;
        --aurora-bg-darker: #06080f;
        --aurora-bg-card: rgba(0, 255, 255, 0.03);
        --aurora-border: rgba(0, 255, 255, 0.15);
        --aurora-border-hover: rgba(0, 255, 255, 0.3);
        --aurora-text: rgba(255, 255, 255, 0.95);
        --aurora-text-muted: rgba(255, 255, 255, 0.7);
        --aurora-success: #00FF88;
        --aurora-glow: 0 0 20px rgba(0, 255, 255, 0.4);
        --aurora-glow-strong: 0 0 40px rgba(0, 255, 255, 0.6);
    }
    
    /* Hide Streamlit elements */
    .stAppViewContainer > .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    header[data-testid="stHeader"] {
        background: transparent;
        height: 0;
    }
    
    .stAppViewContainer {
        background: linear-gradient(135deg, var(--aurora-bg-darker) 0%, var(--aurora-bg-dark) 100%);
        background-attachment: fixed;
    }
    
    /* Hide hamburger menu */
    button[title="View full screen"]{
        visibility: hidden;
    }
    
    /* Main container */
    .waitlist-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 2rem;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 4rem 0 6rem 0;
        position: relative;
    }
    
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--aurora-primary), var(--aurora-tertiary), var(--aurora-secondary));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: var(--aurora-glow);
        margin-bottom: 1.5rem;
        line-height: 1.1;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        color: var(--aurora-text);
        margin-bottom: 2rem;
        font-weight: 400;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.4;
    }
    
    .hero-description {
        font-size: 1.1rem;
        color: var(--aurora-text-muted);
        margin-bottom: 3rem;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }
    
    /* Signup Form */
    .signup-form {
        background: var(--aurora-bg-card);
        border: 1px solid var(--aurora-border);
        border-radius: 20px;
        padding: 3rem;
        margin: 2rem auto;
        max-width: 500px;
        backdrop-filter: blur(20px);
        box-shadow: var(--aurora-glow);
        position: relative;
        overflow: hidden;
    }
    
    .signup-form::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--aurora-primary), var(--aurora-secondary), transparent);
        animation: aurora-scan 8s ease-in-out infinite;
    }
    
    .form-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--aurora-primary);
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: var(--aurora-glow);
    }
    
    /* Custom input styling */
    .stTextInput > div > div > input {
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid var(--aurora-border) !important;
        border-radius: 12px !important;
        color: var(--aurora-text) !important;
        font-size: 1.1rem !important;
        padding: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--aurora-primary) !important;
        box-shadow: var(--aurora-glow) !important;
    }
    
    .stTextInput > label {
        color: var(--aurora-primary) !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Beautiful submit button */
    .stButton > button {
        background: linear-gradient(135deg, var(--aurora-primary), var(--aurora-secondary)) !important;
        color: var(--aurora-bg-dark) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--aurora-glow-strong) !important;
    }
    
    /* Features Section */
    .features-section {
        padding: 4rem 0;
        text-align: center;
    }
    
    .features-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--aurora-primary);
        margin-bottom: 3rem;
        text-shadow: var(--aurora-glow);
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin-top: 2rem;
    }
    
    .feature-card {
        background: var(--aurora-bg-card);
        border: 1px solid var(--aurora-border);
        border-radius: 16px;
        padding: 2rem;
        transition: all 0.3s ease;
        position: relative;
        backdrop-filter: blur(16px);
    }
    
    .feature-card:hover {
        border-color: var(--aurora-border-hover);
        transform: translateY(-4px);
        box-shadow: var(--aurora-glow);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        display: block;
    }
    
    .feature-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--aurora-primary);
        margin-bottom: 1rem;
    }
    
    .feature-description {
        color: var(--aurora-text-muted);
        line-height: 1.5;
    }
    
    /* Social Proof */
    .social-proof {
        text-align: center;
        padding: 3rem 0;
        background: var(--aurora-bg-card);
        border-radius: 20px;
        margin: 3rem 0;
        border: 1px solid var(--aurora-border);
    }
    
    .waitlist-count {
        font-size: 3rem;
        font-weight: 800;
        color: var(--aurora-primary);
        text-shadow: var(--aurora-glow);
    }
    
    .waitlist-text {
        font-size: 1.2rem;
        color: var(--aurora-text-muted);
        margin-top: 0.5rem;
    }
    
    /* Success message */
    .success-message {
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 2rem 0;
        text-align: center;
        color: var(--aurora-success);
        font-weight: 600;
    }
    
    /* Animations */
    @keyframes aurora-scan {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    
    @keyframes aurora-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        
        .hero-subtitle {
            font-size: 1.2rem;
        }
        
        .signup-form {
            margin: 2rem 1rem;
            padding: 2rem;
        }
        
        .waitlist-container {
            padding: 0 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def save_waitlist_signup(name, email):
    """Save waitlist signup to Supabase"""
    if not SUPABASE_AVAILABLE:
        logger.error("Supabase not available")
        return False
    
    try:
        db = get_supabase_client()
        success = db.save_waitlist_signup(name, email)
        return success
    except Exception as e:
        logger.error(f"Error saving waitlist signup: {e}")
        return False

def get_waitlist_count():
    """Get current waitlist count"""
    if not SUPABASE_AVAILABLE:
        return 247  # Fallback number
    
    try:
        db = get_supabase_client()
        count = db.get_waitlist_count()
        return max(count, 247)  # Always show at least 247 for social proof
    except Exception as e:
        logger.error(f"Error getting waitlist count: {e}")
        return 247

def main():
    # Apply beautiful theme
    apply_waitlist_theme()
    
    # Main container
    st.markdown('<div class="waitlist-container">', unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">WhisperForge</h1>
        <div class="hero-subtitle">Transform Your Voice Into Wisdom</div>
        <div class="hero-description">
            Turn any audio into actionable insights, compelling articles, and social content 
            with the power of AI. Join thousands of creators, entrepreneurs, and thought 
            leaders who are amplifying their voice.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Get waitlist count for social proof
    waitlist_count = get_waitlist_count()
    
    # Social Proof
    st.markdown(f"""
    <div class="social-proof">
        <div class="waitlist-count">{waitlist_count:,}</div>
        <div class="waitlist-text">creators already on the waitlist</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Signup Form
    st.markdown('<div class="signup-form">', unsafe_allow_html=True)
    st.markdown('<div class="form-title">Join the Waitlist</div>', unsafe_allow_html=True)
    
    # Check if already submitted
    if 'signup_success' not in st.session_state:
        st.session_state.signup_success = False
    
    if not st.session_state.signup_success:
        with st.form("waitlist_form", clear_on_submit=True):
            name = st.text_input("Full Name", placeholder="Enter your full name")
            email = st.text_input("Email Address", placeholder="Enter your email address")
            
            submitted = st.form_submit_button("🚀 Join the Waitlist")
            
            if submitted:
                # Validation
                if not name.strip():
                    st.error("Please enter your name")
                elif not email.strip():
                    st.error("Please enter your email address")
                elif not validate_email(email):
                    st.error("Please enter a valid email address")
                else:
                    # Save to waitlist
                    success = save_waitlist_signup(name.strip(), email.strip())
                    
                    if success:
                        st.session_state.signup_success = True
                        st.rerun()
                    else:
                        st.error("Something went wrong. Please try again.")
    
    else:
        # Success state
        st.markdown("""
        <div class="success-message">
            🎉 <strong>Welcome to the WhisperForge family!</strong><br>
            You're all set! We'll notify you as soon as we launch.
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Sign up another email"):
            st.session_state.signup_success = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Features Section
    st.markdown("""
    <div class="features-section">
        <h2 class="features-title">Transform Audio Into Everything</h2>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🎙️</div>
                <div class="feature-title">Voice to Wisdom</div>
                <div class="feature-description">
                    Extract key insights and actionable wisdom from any audio - 
                    podcasts, meetings, interviews, or voice memos.
                </div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📝</div>
                <div class="feature-title">Instant Articles</div>
                <div class="feature-description">
                    Generate compelling, well-structured articles from your audio 
                    content in minutes, not hours.
                </div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📱</div>
                <div class="feature-title">Social Content</div>
                <div class="feature-description">
                    Create engaging social media posts, threads, and content 
                    tailored for every platform.
                </div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🎨</div>
                <div class="feature-title">Visual Prompts</div>
                <div class="feature-description">
                    Generate stunning image prompts and visual concepts 
                    that bring your content to life.
                </div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <div class="feature-title">Custom AI</div>
                <div class="feature-description">
                    Train the AI on your knowledge base and style 
                    for personalized, on-brand content.
                </div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <div class="feature-title">Lightning Fast</div>
                <div class="feature-description">
                    Process hours of audio in minutes with our 
                    optimized AI pipeline and smart workflows.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Close container
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: var(--aurora-text-muted); border-top: 1px solid var(--aurora-border); margin-top: 4rem;">
        <p>© 2024 WhisperForge. Transform your voice into wisdom.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 