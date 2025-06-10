# WhisperForge - Join the Waitlist
# Compact aurora bioluminescent landing page

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

def apply_aurora_theme():
    """Apply compact aurora bioluminescent theme"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    :root {
        --aurora-primary: #00FFFF;
        --aurora-secondary: #40E0D0;
        --aurora-tertiary: #7DF9FF;
        --aurora-purple: #8A2BE2;
        --aurora-pink: #FF1493;
        --aurora-green: #00FF88;
        --aurora-bg-dark: #0a0f1c;
        --aurora-bg-darker: #050a14;
        --aurora-bg-deepest: #020408;
        --aurora-text: rgba(255, 255, 255, 0.95);
        --aurora-text-muted: rgba(255, 255, 255, 0.7);
        --aurora-glow: 0 0 30px rgba(0, 255, 255, 0.5);
        --aurora-glow-strong: 0 0 60px rgba(0, 255, 255, 0.8);
        --aurora-glow-purple: 0 0 30px rgba(138, 43, 226, 0.6);
        --aurora-glow-green: 0 0 30px rgba(0, 255, 136, 0.6);
    }
    
    /* Hide all Streamlit elements */
    .stAppViewContainer > .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    .stAppViewContainer {
        background: radial-gradient(ellipse at top, var(--aurora-bg-dark) 0%, var(--aurora-bg-darker) 50%, var(--aurora-bg-deepest) 100%);
        min-height: 100vh;
        overflow: hidden;
    }
    
    button[title="View full screen"], 
    .stActionButton,
    footer,
    .stDeployButton {
        display: none !important;
    }
    
    /* Aurora Background Animation */
    .aurora-container::before {
        content: "";
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: 
            radial-gradient(circle at 20% 30%, rgba(0, 255, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(138, 43, 226, 0.08) 0%, transparent 50%),
            radial-gradient(circle at 60% 70%, rgba(0, 255, 136, 0.06) 0%, transparent 50%),
            radial-gradient(circle at 30% 80%, rgba(255, 20, 147, 0.05) 0%, transparent 50%);
        animation: aurora-drift 20s ease-in-out infinite alternate;
        pointer-events: none;
        z-index: -1;
    }
    
    /* Main Landing Container */
    .aurora-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 2rem;
        font-family: 'Inter', sans-serif;
        position: relative;
    }
    
    .landing-card {
        background: linear-gradient(145deg, 
            rgba(0, 255, 255, 0.05) 0%, 
            rgba(138, 43, 226, 0.03) 50%, 
            rgba(0, 255, 136, 0.02) 100%);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 32px;
        padding: 4rem 3rem;
        max-width: 600px;
        width: 100%;
        position: relative;
        overflow: hidden;
        box-shadow: 
            var(--aurora-glow),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        animation: card-float 6s ease-in-out infinite;
    }
    
    /* Animated border */
    .landing-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent, 
            var(--aurora-primary), 
            var(--aurora-purple), 
            var(--aurora-green), 
            transparent);
        animation: aurora-scan 8s ease-in-out infinite;
    }
    
    /* Bioluminescent orbs */
    .landing-card::after {
        content: "";
        position: absolute;
        top: 20%;
        right: 10%;
        width: 4px;
        height: 4px;
        background: var(--aurora-primary);
        border-radius: 50%;
        box-shadow: var(--aurora-glow);
        animation: bioluminescent-pulse 3s ease-in-out infinite;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, 
            var(--aurora-primary) 0%, 
            var(--aurora-tertiary) 30%, 
            var(--aurora-purple) 60%, 
            var(--aurora-green) 100%);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        line-height: 1.1;
        text-shadow: var(--aurora-glow);
        animation: title-glow 4s ease-in-out infinite alternate;
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        color: var(--aurora-text);
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 500;
        opacity: 0.9;
    }
    
    .hero-description {
        font-size: 1rem;
        color: var(--aurora-text-muted);
        text-align: center;
        margin-bottom: 2.5rem;
        line-height: 1.6;
        max-width: 90%;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Social Proof Compact */
    .social-proof-compact {
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: rgba(0, 255, 255, 0.02);
        border-radius: 16px;
        border: 1px solid rgba(0, 255, 255, 0.1);
    }
    
    .waitlist-count-compact {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(45deg, var(--aurora-primary), var(--aurora-green));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: var(--aurora-glow);
    }
    
    .waitlist-text-compact {
        font-size: 0.9rem;
        color: var(--aurora-text-muted);
        margin-top: 0.5rem;
    }
    
    /* Form Styling */
    .stTextInput > div > div > input {
        background: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(0, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        color: var(--aurora-text) !important;
        font-size: 1rem !important;
        padding: 1rem 1.25rem !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--aurora-primary) !important;
        box-shadow: var(--aurora-glow) !important;
        background: rgba(0, 255, 255, 0.02) !important;
    }
    
    .stTextInput > label {
        color: var(--aurora-primary) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.3) !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, 
            var(--aurora-primary) 0%, 
            var(--aurora-secondary) 50%, 
            var(--aurora-green) 100%) !important;
        color: var(--aurora-bg-deepest) !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 1rem 2rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        width: 100% !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: var(--aurora-glow) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: var(--aurora-glow-strong) !important;
    }
    
    .stButton > button::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 100% !important;
        height: 100% !important;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent) !important;
        transition: left 0.5s !important;
    }
    
    .stButton > button:hover::before {
        left: 100% !important;
    }
    
    /* Success State */
    .success-message {
        background: linear-gradient(135deg, 
            rgba(0, 255, 136, 0.1) 0%, 
            rgba(0, 255, 255, 0.05) 100%);
        border: 1px solid rgba(0, 255, 136, 0.3);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        color: var(--aurora-green);
        font-weight: 600;
        box-shadow: var(--aurora-glow-green);
        backdrop-filter: blur(20px);
    }
    
    .success-title {
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        background: linear-gradient(45deg, var(--aurora-green), var(--aurora-primary));
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Animations */
    @keyframes aurora-drift {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        33% { transform: translate(2%, -2%) rotate(1deg); }
        66% { transform: translate(-1%, 1%) rotate(-0.5deg); }
    }
    
    @keyframes aurora-scan {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    
    @keyframes card-float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes bioluminescent-pulse {
        0%, 100% { 
            opacity: 0.6; 
            transform: scale(1);
            box-shadow: 0 0 10px var(--aurora-primary);
        }
        50% { 
            opacity: 1; 
            transform: scale(1.5);
            box-shadow: 0 0 20px var(--aurora-primary);
        }
    }
    
    @keyframes title-glow {
        0% { filter: brightness(1) drop-shadow(0 0 10px rgba(0,255,255,0.3)); }
        100% { filter: brightness(1.1) drop-shadow(0 0 20px rgba(0,255,255,0.5)); }
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .aurora-container {
            padding: 1rem;
        }
        
        .landing-card {
            padding: 3rem 2rem;
        }
        
        .hero-title {
            font-size: 2.5rem;
        }
        
        .hero-subtitle {
            font-size: 1.1rem;
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
    # Apply aurora theme
    apply_aurora_theme()
    
    # Main aurora container
    st.markdown('<div class="aurora-container">', unsafe_allow_html=True)
    st.markdown('<div class="landing-card">', unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="hero-title">WhisperForge</div>
    <div class="hero-subtitle">Transform Your Voice Into Wisdom</div>
    <div class="hero-description">
        Turn any audio into actionable insights, compelling articles, and social content 
        with the power of AI. Join the creators who are amplifying their voice.
    </div>
    """, unsafe_allow_html=True)
    
    # Social Proof
    waitlist_count = get_waitlist_count()
    st.markdown(f"""
    <div class="social-proof-compact">
        <div class="waitlist-count-compact">{waitlist_count:,}</div>
        <div class="waitlist-text-compact">creators already on the waitlist</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Signup Form
    if 'signup_success' not in st.session_state:
        st.session_state.signup_success = False
    
    if not st.session_state.signup_success:
        with st.form("waitlist_form", clear_on_submit=True):
            name = st.text_input("Full Name", placeholder="Enter your full name")
            email = st.text_input("Email Address", placeholder="Enter your email address")
            
            submitted = st.form_submit_button("Join the Waitlist")
            
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
            <div class="success-title">Welcome to WhisperForge!</div>
            <div>You're all set! We'll notify you as soon as we launch.</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Sign up another email"):
            st.session_state.signup_success = False
            st.rerun()
    
    # Close containers
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 