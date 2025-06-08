# WhisperForge UI Components - Stable, Reusable UI System
# Prevents UI container errors and provides consistent patterns

import streamlit as st
from pathlib import Path

def load_aurora_css():
    """Load the Aurora CSS framework with beautiful animations"""
    css_file = Path(__file__).parent.parent / "static" / "css" / "whisperforge_ui.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Always load Aurora styling enhancements
    from .styling import apply_aurora_theme
    apply_aurora_theme()

class AuroraContainer:
    """Beautiful Aurora-themed container system with animations"""
    
    @staticmethod
    def auth_page():
        """Create Aurora auth page container"""
        load_aurora_css()
        return st.container()
    
    @staticmethod
    def main_app():
        """Create Aurora main app container"""
        load_aurora_css()
        return st.container()
    
    @staticmethod
    def content_section(title=None):
        """Create Aurora content section with beautiful styling"""
        container = st.container()
        with container:
            if title:
                st.markdown(f'''
                <div class="aurora-card aurora-fade-in">
                    <h3 style="
                        color: var(--aurora-primary);
                        font-size: 1.4rem;
                        font-weight: 700;
                        margin: 0;
                        text-shadow: var(--aurora-glow);
                    ">{title}</h3>
                </div>
                ''', unsafe_allow_html=True)
        return container
    
    @staticmethod
    def upload_section():
        """Create Aurora upload section with hover effects"""
        container = st.container()
        with container:
            st.markdown('''
            <div class="upload-section aurora-fade-in">
            </div>
            ''', unsafe_allow_html=True)
        return container
    
    @staticmethod
    def results_section():
        """Create Aurora results section"""
        container = st.container()
        with container:
            st.markdown('''
            <div class="results-container aurora-fade-in">
            </div>
            ''', unsafe_allow_html=True)
        return container

class AuroraComponents:
    """Beautiful Aurora-themed UI components with smooth animations"""
    
    @staticmethod
    def logo_header(title="WhisperForge", tagline="Transform audio into structured content"):
        """Beautiful Aurora logo header with glowing effects"""
        try:
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
                ">{tagline}</p>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            # Fallback to standard Streamlit
            st.title(title)
            st.caption(tagline)
    
    @staticmethod
    def safe_button(label, key=None, type="secondary", use_container_width=True, disabled=False):
        """Safe button that handles all edge cases"""
        try:
            return st.button(
                label, 
                key=key, 
                type=type, 
                use_container_width=use_container_width,
                disabled=disabled
            )
        except Exception as e:
            st.error(f"Button error: {e}")
            return False
    
    @staticmethod
    def safe_link_button(label, url, type="primary", use_container_width=True):
        """Safe link button with fallback"""
        try:
            return st.link_button(label, url, type=type, use_container_width=use_container_width)
        except Exception as e:
            st.error(f"Link button error: {e}")
            st.markdown(f'[{label}]({url})')
            return False
    
    @staticmethod
    def safe_file_uploader(label, accepted_types=None, key=None):
        """Safe file uploader with validation"""
        try:
            return st.file_uploader(
                label,
                type=accepted_types,
                key=key,
                label_visibility="collapsed" if label == "" else "visible"
            )
        except Exception as e:
            st.error(f"File upload error: {e}")
            return None
    
    @staticmethod
    def safe_text_input(label, placeholder="", key=None, type="default"):
        """Safe text input with validation"""
        try:
            return st.text_input(
                label,
                placeholder=placeholder,
                key=key,
                type=type,
                label_visibility="collapsed" if label == "" else "visible"
            )
        except Exception as e:
            st.error(f"Text input error: {e}")
            return ""
    
    @staticmethod
    def safe_selectbox(label, options, key=None, index=0):
        """Safe selectbox with validation"""
        try:
            if not options:
                options = ["No options available"]
            if index >= len(options):
                index = 0
            return st.selectbox(label, options, key=key, index=index)
        except Exception as e:
            st.error(f"Selectbox error: {e}")
            return options[0] if options else "Error"
    
    @staticmethod
    def aurora_progress_bar(progress, text="", title="Processing"):
        """Beautiful Aurora progress bar with glowing effects"""
        try:
            progress_val = max(0, min(100, int(progress)))
            st.markdown(f"""
            <div class="aurora-progress-container aurora-fade-in">
                <div class="aurora-progress-header">
                    <h4 class="aurora-progress-title">{title}</h4>
                    <div class="aurora-progress-stats">
                        <span>{progress_val}%</span>
                    </div>
                </div>
                
                <div class="aurora-progress-bar">
                    <div class="aurora-progress-fill" style="width: {progress_val}%"></div>
                </div>
                
                {f'<p style="color: var(--aurora-text-muted); margin: 8px 0 0 0;">{text}</p>' if text else ''}
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Progress bar error: {e}")
            return None
    
    @staticmethod
    def safe_tabs(tab_names):
        """Safe tabs with fallback"""
        try:
            return st.tabs(tab_names)
        except Exception as e:
            st.error(f"Tabs error: {e}")
            # Fallback to simple sections
            return [st.container() for _ in tab_names]
    
    @staticmethod
    def safe_columns(spec):
        """Safe columns with fallback"""
        try:
            return st.columns(spec)
        except Exception as e:
            st.error(f"Columns error: {e}")
            # Fallback to single column
            return [st.container()]

class StatusMessages:
    """Consistent status message system"""
    
    @staticmethod
    def success(message, container=None):
        """Display success message"""
        if container:
            with container:
                st.success(message)
        else:
            st.success(message)
    
    @staticmethod
    def error(message, container=None):
        """Display error message"""
        if container:
            with container:
                st.error(message)
        else:
            st.error(message)
    
    @staticmethod
    def warning(message, container=None):
        """Display warning message"""
        if container:
            with container:
                st.warning(message)
        else:
            st.warning(message)
    
    @staticmethod
    def info(message, container=None):
        """Display info message"""
        if container:
            with container:
                st.info(message)
        else:
            st.info(message)

class LayoutHelpers:
    """Layout helper functions"""
    
    @staticmethod
    def divider(text="", container=None):
        """Create divider with optional text"""
        target = container if container else st
        if text:
            target.markdown(f"""
            <div style="text-align: center; margin: 2rem 0;">
                <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 1rem 0;">
                <span style="color: rgba(255,255,255,0.5); background: #0d1421; padding: 0 1rem;">{text}</span>
                <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 1rem 0;">
            </div>
            """, unsafe_allow_html=True)
        else:
            target.markdown("---")
    
    @staticmethod
    def spacer(height="1rem"):
        """Create vertical spacer"""
        st.markdown(f'<div style="height: {height};"></div>', unsafe_allow_html=True)
    
    @staticmethod
    def center_content(content):
        """Center content horizontally"""
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            content()

class ErrorBoundary:
    """Error boundary for UI components"""
    
    @staticmethod
    def wrap(func, fallback_message="An error occurred", *args, **kwargs):
        """Wrap function with error boundary"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"{fallback_message}: {str(e)}")
            return None
    
    @staticmethod
    def safe_render(component_func, *args, **kwargs):
        """Safely render a component with error handling"""
        try:
            return component_func(*args, **kwargs)
        except Exception as e:
            st.error(f"Component render error: {str(e)}")
            # Try to render basic fallback
            try:
                st.write("⚠️ Component failed to load")
                return None
            except:
                pass  # Even fallback failed

# Aurora convenience functions for common patterns
def create_auth_layout():
    """Create beautiful Aurora auth page layout"""
    container = AuroraContainer.auth_page()
    return container

def create_main_layout():
    """Create beautiful Aurora main app layout"""
    container = AuroraContainer.main_app()
    return container

def handle_oauth_section():
    """Handle OAuth section safely with Aurora styling"""
    return ErrorBoundary.safe_render(lambda: st.container())

def handle_email_auth_section():
    """Handle email auth section safely with Aurora styling"""
    return ErrorBoundary.safe_render(lambda: st.container())

# Export all Aurora classes and functions
__all__ = [
    'AuroraContainer',
    'AuroraComponents', 
    'StatusMessages',
    'LayoutHelpers',
    'ErrorBoundary',
    'load_aurora_css',
    'create_auth_layout',
    'create_main_layout',
    'handle_oauth_section',
    'handle_email_auth_section'
] 