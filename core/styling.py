"""
Aurora Styling utilities for WhisperForge
Beautiful, modern UI components with bioluminescent Aurora theme
"""

import streamlit as st

def apply_aurora_theme():
    """Apply the complete Aurora theme by loading our comprehensive CSS file"""
    # Load the comprehensive Aurora CSS file
    css_file_path = "static/css/main.css"
    
    try:
        with open(css_file_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        st.markdown(f"""
        <style>
        {css_content}
        </style>
        """, unsafe_allow_html=True)
        
    except FileNotFoundError:
        # Fallback to basic Aurora styling if file not found
        st.markdown("""
        <style>
        :root {
            --aurora-primary: #40E0D0;
            --aurora-secondary: #7DF9FF;
            --aurora-tertiary: #00FFFF;
            --aurora-bg-dark: #0a0f1c;
            --aurora-bg-darker: #0d1421;
            --aurora-bg-card: rgba(64, 224, 208, 0.03);
            --aurora-border: rgba(64, 224, 208, 0.2);
            --aurora-text: rgba(255, 255, 255, 0.95);
            --aurora-glow: 0 0 20px rgba(64, 224, 208, 0.3);
        }
        
        .stApp {
            background: linear-gradient(135deg, var(--aurora-bg-dark) 0%, var(--aurora-bg-darker) 100%);
            color: var(--aurora-text);
        }
        </style>
        """, unsafe_allow_html=True)

def create_aurora_header():
    """Create a flagship Aurora header with integrated navigation and logout - REBUILT FOR 2025"""
    
    # First, inject the CSS using st.markdown()
    st.markdown("""
    <style>
    .aurora-header {
        background: linear-gradient(135deg, rgba(0, 20, 40, 0.95), rgba(0, 40, 60, 0.98));
        border: 1px solid rgba(0, 255, 255, 0.2);
        border-radius: 12px;
        margin: 4px 0 16px 0;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    
    .aurora-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00FFFF, #40E0D0, transparent);
        animation: aurora-flow 8s ease-in-out infinite;
    }
    
    .aurora-header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 20px;
        position: relative;
        z-index: 1;
    }
    
    .aurora-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .aurora-title {
        font-size: 1.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00FFFF, #7DF9FF, #40E0D0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        text-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
        letter-spacing: -0.02em;
    }
    
    .aurora-status {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 8px;
        background: rgba(0, 255, 136, 0.1);
        border: 1px solid rgba(0, 255, 136, 0.2);
        border-radius: 20px;
        backdrop-filter: blur(5px);
    }
    
    .aurora-status-dot {
        width: 6px;
        height: 6px;
        background: #00FF88;
        border-radius: 50%;
        animation: status-pulse 2s ease-in-out infinite;
        box-shadow: 0 0 8px rgba(0, 255, 136, 0.6);
    }
    
    .aurora-status-text {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.75rem;
        font-weight: 500;
    }

    .aurora-nav {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    @keyframes aurora-flow {
        0%, 100% { 
            left: -100%; 
            opacity: 0; 
        }
        25% { 
            opacity: 1; 
        }
        75% { 
            opacity: 1; 
        }
        100% { 
            left: 100%; 
            opacity: 0; 
        }
    }
    
    @keyframes status-pulse {
        0%, 100% { 
            opacity: 1; 
            transform: scale(1); 
        }
        50% { 
            opacity: 0.6; 
            transform: scale(1.3); 
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Then render the HTML structure using st.markdown()
    st.markdown("""
    <header class="aurora-header">
        <div class="aurora-header-content">
            <div class="aurora-brand">
                <h1 class="aurora-title">WhisperForge</h1>
                <div class="aurora-status">
                    <div class="aurora-status-dot"></div>
                    <span class="aurora-status-text">Authenticated</span>
                </div>
            </div>
            <div id="aurora-nav-placeholder" class="aurora-nav">
                <!-- Navigation buttons will be inserted here by Streamlit -->
            </div>
        </div>
    </header>
    """, unsafe_allow_html=True)

def create_aurora_nav_buttons():
    """Create integrated navigation buttons for the Aurora header"""
    
    # Enhanced styling for integrated nav buttons
    st.markdown("""
    <style>
    /* Aurora nav button styling */
    .aurora-nav-button {
        margin: 0 2px !important;
    }
    
    .aurora-nav-button .stButton > button {
        background: rgba(0, 255, 255, 0.08) !important;
        border: 1px solid rgba(0, 255, 255, 0.15) !important;
        color: rgba(255, 255, 255, 0.8) !important;
        border-radius: 8px !important;
        padding: 6px 16px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        min-width: 80px !important;
        height: 32px !important;
        }
        
    .aurora-nav-button .stButton > button:hover {
        background: rgba(0, 255, 255, 0.15) !important;
        border-color: rgba(0, 255, 255, 0.25) !important;
        color: #00FFFF !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 255, 255, 0.1);
    }
    
    /* Active/Primary button styling */
    .aurora-nav-button .stButton > button[kind="primary"] {
        background: rgba(0, 255, 255, 0.2) !important;
        border-color: rgba(0, 255, 255, 0.3) !important;
        color: #00FFFF !important;
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.15);
    }
    
    /* Logout button special styling */
    .aurora-logout-button .stButton > button {
        background: rgba(255, 100, 100, 0.1) !important;
        border: 1px solid rgba(255, 100, 100, 0.2) !important;
        color: rgba(255, 180, 180, 0.9) !important;
    }
    
    .aurora-logout-button .stButton > button:hover {
        background: rgba(255, 100, 100, 0.2) !important;
        border-color: rgba(255, 100, 100, 0.3) !important;
        color: #FF6B6B !important;
    }
    </style>
    """, unsafe_allow_html=True)

    pages = [
        ("Processing", "Content Pipeline"),
        ("History", "Content History"), 
        ("Settings", "Settings"),
        ("Status", "Health Check")
    ]
    
    current_page = st.session_state.get('current_page', 'Content Pipeline')
    
    # Create horizontal layout for nav buttons
    nav_cols = st.columns([1, 1, 1, 1, 0.8])  # Last column smaller for logout
    
    for i, (page_name, page_key) in enumerate(pages):
        with nav_cols[i]:
            st.markdown('<div class="aurora-nav-button">', unsafe_allow_html=True)
            if st.button(
                page_name, 
                key=f"nav_{page_name}", 
                type="primary" if page_key == current_page else "secondary",
                use_container_width=True
            ):
                st.session_state.current_page = page_key
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Logout button in the last column
    with nav_cols[4]:
        st.markdown('<div class="aurora-logout-button">', unsafe_allow_html=True)
        if st.button("Sign Out", key="logout_btn", use_container_width=True):
            return True  # Signal logout
        st.markdown('</div>', unsafe_allow_html=True)
    
    return False  # No logout

def create_aurora_progress_card(title, current_step, total_steps, description=""):
    """Create a beautiful Aurora progress card"""
    progress = (current_step / total_steps) * 100
    st.markdown(f"""
    <div class="aurora-progress-container aurora-fade-in">
        <div class="aurora-progress-header">
            <h3 class="aurora-progress-title">{title}</h3>
            <div class="aurora-progress-stats">
                <span>{current_step}/{total_steps} steps • {progress:.0f}%</span>
            </div>
        </div>
        
        <div class="aurora-progress-bar">
            <div class="aurora-progress-fill" style="width: {progress}%"></div>
        </div>
        
        {f'<p style="color: var(--aurora-text-muted); margin: 8px 0 0 0;">{description}</p>' if description else ''}
    </div>
    """, unsafe_allow_html=True)

def create_aurora_step_card(title, description, status="pending", progress=0):
    """Create a beautiful step card with Aurora styling"""
    
    # Determine icon and styling based on status
    if status == "completed":
        icon = "✅"
        container_class = "aurora-step-container completed"
    elif status == "processing":
        icon = "🔄"
        container_class = "aurora-step-container processing"
    else:
        icon = "⭕"
        container_class = "aurora-step-container"
    
    progress_bar = ""
    if status == "processing" and progress > 0:
        progress_bar = f"""
        <div style="margin-top: 16px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                <span style="color: var(--aurora-text-muted); font-size: 0.8rem;">Processing...</span>
                <span style="color: var(--aurora-text-muted); font-size: 0.8rem;">{progress}%</span>
            </div>
            <div style="
                background: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                height: 6px;
                overflow: hidden;
            ">
                <div style="
                    background: linear-gradient(90deg, var(--aurora-primary), var(--aurora-secondary));
                    height: 100%;
                    width: {progress}%;
                    border-radius: 8px;
                    box-shadow: var(--aurora-glow);
                    transition: width 0.5s ease;
                "></div>
            </div>
        </div>
        """
    
    st.markdown(f"""
    <div class="{container_class} aurora-fade-in">
        <div class="aurora-step-header">
            <div class="aurora-step-info">
                <span class="aurora-step-icon">{icon}</span>
                <div>
                    <h4 class="aurora-step-title">{title}</h4>
                    <p class="aurora-step-description">{description}</p>
                </div>
            </div>
            <div class="aurora-step-progress">{progress if status == 'processing' else (100 if status == 'completed' else 0)}%</div>
        </div>
        {progress_bar}
    </div>
    """, unsafe_allow_html=True)

def create_aurora_content_card(title, content, content_type="text"):
    """Create a beautiful content display card"""
    
    # Truncate content if too long
    if len(content) > 500:
        preview_content = content[:500] + "..."
        show_full = True
    else:
        preview_content = content
        show_full = False
    
    st.markdown(f"""
    <div class="aurora-card aurora-fade-in">
        <div class="aurora-card-header">
            <h4 class="aurora-card-title">{title}</h4>
        </div>
        <div style="
            color: var(--aurora-text);
            line-height: 1.6;
            white-space: pre-wrap;
        ">{preview_content}</div>
    </div>
    """, unsafe_allow_html=True)

    if show_full:
        with st.expander("Show full content"):
            st.markdown(content)

# Aurora Component Utilities
class AuroraComponents:
    """Beautiful Aurora-themed UI components"""
    
    @staticmethod
    def success_message(message):
        """Aurora success message"""
        st.markdown(f"""
        <div style="
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 12px;
            padding: 16px;
            margin: 16px 0;
            color: var(--aurora-success);
        ">
            ✅ {message}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def warning_message(message):
        """Aurora warning message"""
        st.markdown(f"""
        <div style="
            background: rgba(255, 184, 0, 0.1);
            border: 1px solid rgba(255, 184, 0, 0.3);
            border-radius: 12px;
            padding: 16px;
            margin: 16px 0;
            color: var(--aurora-warning);
        ">
            ⚠️ {message}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def error_message(message):
        """Aurora error message"""
        st.markdown(f"""
        <div style="
            background: rgba(255, 68, 68, 0.1);
            border: 1px solid rgba(255, 68, 68, 0.3);
            border-radius: 12px;
            padding: 16px;
            margin: 16px 0;
            color: var(--aurora-error);
        ">
            ❌ {message}
        </div>
    """, unsafe_allow_html=True) 