"""
Aurora Styling utilities for WhisperForge
Beautiful, modern UI components with bioluminescent Aurora theme
"""

import streamlit as st

def apply_aurora_theme():
    """Apply the complete Aurora theme with smooth animations"""
    st.markdown("""
    <style>
    /* Aurora Theme Variables */
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
        --aurora-success: #00FF88;
        --aurora-warning: #FFB800;
        --aurora-error: #FF4444;
        --aurora-glow: 0 0 20px rgba(0, 255, 255, 0.4);
        --aurora-glow-strong: 0 0 30px rgba(0, 255, 255, 0.6);
    }
    
    /* Beautiful Aurora Progress Bars */
    .aurora-progress-container {
        background: var(--aurora-bg-card);
        border: 1px solid var(--aurora-border);
        border-radius: 16px;
        padding: 24px;
        margin: 20px 0;
        backdrop-filter: blur(24px);
        position: relative;
        overflow: hidden;
    }
    
    .aurora-progress-container::before {
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--aurora-primary), var(--aurora-secondary), transparent);
        animation: aurora-scan 8s ease-in-out infinite;
    }
    
    .aurora-progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    
    .aurora-progress-title {
        color: var(--aurora-primary);
        font-size: 1.4rem;
        font-weight: 700;
        margin: 0;
        text-shadow: var(--aurora-glow);
    }
    
    .aurora-progress-stats {
        color: var(--aurora-text-muted);
        font-size: 0.9rem;
    }
    
    .aurora-progress-bar {
        background: rgba(0, 0, 0, 0.4);
        border-radius: 12px;
        height: 8px;
        overflow: hidden;
        margin: 16px 0;
    }
    
    .aurora-progress-fill {
        background: linear-gradient(90deg, var(--aurora-primary), var(--aurora-tertiary), var(--aurora-secondary));
        height: 100%;
        border-radius: 12px;
        box-shadow: var(--aurora-glow);
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .aurora-progress-fill::after {
        content: "";
        position: absolute;
        top: 0;
        right: 0;
        width: 20px;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3));
        animation: aurora-shimmer 2s ease-in-out infinite;
    }
    
    /* Beautiful Step Containers */
    .aurora-step-container {
        background: var(--aurora-bg-card);
        border: 1px solid var(--aurora-border);
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .aurora-step-container.processing {
        border-color: var(--aurora-border-hover);
        background: rgba(0, 255, 255, 0.08);
        box-shadow: var(--aurora-glow);
    }
    
    .aurora-step-container.completed {
        border-color: rgba(0, 255, 136, 0.4);
        background: rgba(0, 255, 136, 0.05);
    }
    
    .aurora-step-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .aurora-step-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .aurora-step-icon {
        font-size: 1.2rem;
        animation: aurora-pulse 2s ease-in-out infinite;
    }
    
    .aurora-step-title {
        color: var(--aurora-primary);
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
    }
    
    .aurora-step-description {
        color: var(--aurora-text-muted);
        font-size: 0.9rem;
        margin: 4px 0 0 0;
    }
    
    .aurora-step-progress {
        color: var(--aurora-text);
        font-weight: bold;
    }
    
    /* Beautiful Cards */
    .aurora-card {
        background: var(--aurora-bg-card);
        border: 1px solid var(--aurora-border);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        backdrop-filter: blur(16px);
        transition: all 0.3s ease;
        position: relative;
    }
    
    .aurora-card:hover {
        border-color: var(--aurora-border-hover);
        transform: translateY(-2px);
        box-shadow: var(--aurora-glow);
    }
    
    .aurora-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    
    .aurora-card-title {
        color: var(--aurora-primary);
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0;
    }
    
    /* Aurora Animations */
    @keyframes aurora-scan {
        0%, 100% { left: -100%; }
        50% { left: 100%; }
    }
    
    @keyframes aurora-shimmer {
        0%, 100% { opacity: 0; }
        50% { opacity: 1; }
    }
    
    @keyframes aurora-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes aurora-glow {
        0%, 100% { box-shadow: var(--aurora-glow); }
        50% { box-shadow: var(--aurora-glow-strong); }
    }
    
    /* Smooth fade-in for all elements */
    .aurora-fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

def create_aurora_header(title="WhisperForge", subtitle="Transform Audio into Structured Content with AI"):
    """Create a beautiful Aurora-themed header"""
    st.markdown(f"""
    <div class="aurora-card aurora-fade-in" style="text-align: center; margin-bottom: 2rem;">
        <h1 style="
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(120deg, var(--aurora-primary), var(--aurora-tertiary), var(--aurora-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: var(--aurora-glow);
            margin: 0 0 16px 0;
            animation: aurora-glow 3s ease-in-out infinite;
        ">{title}</h1>
        <p style="
            color: var(--aurora-text-muted);
            font-size: 1.2rem;
            margin: 0;
            font-weight: 300;
        ">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

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