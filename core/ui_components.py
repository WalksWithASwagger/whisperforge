# WhisperForge UI Components - Stable, Reusable UI System
# Prevents UI container errors and provides consistent patterns

import streamlit as st
from pathlib import Path

def load_css():
    """Load the stable CSS framework"""
    css_file = Path(__file__).parent.parent / "static" / "css" / "whisperforge_ui.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Fallback minimal CSS if file doesn't exist
        st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(180deg, #0a0f1c 0%, #0d1421 100%) !important;
            font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        }
        .main .block-container {
            padding-top: 1rem !important;
            max-width: 1200px !important;
            margin: 0 auto !important;
        }
        </style>
        """, unsafe_allow_html=True)

class StableContainer:
    """Stable container system that prevents UI errors"""
    
    @staticmethod
    def auth_page():
        """Create stable auth page container"""
        load_css()
        return st.container()
    
    @staticmethod
    def main_app():
        """Create stable main app container"""
        load_css()
        return st.container()
    
    @staticmethod
    def content_section(title=None):
        """Create stable content section"""
        container = st.container()
        with container:
            if title:
                st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
        return container
    
    @staticmethod
    def upload_section():
        """Create stable upload section"""
        return st.container()
    
    @staticmethod
    def results_section():
        """Create stable results section"""
        return st.container()

class SafeComponents:
    """Safe, error-resistant UI components"""
    
    @staticmethod
    def logo_header(title="WhisperForge", tagline="Transform audio into structured content"):
        """Safe logo header that always works"""
        try:
            st.markdown(f"""
            <div class="auth-logo">{title}</div>
            <div class="auth-tagline">{tagline}</div>
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
    def safe_progress_bar(progress, text=""):
        """Safe progress bar with validation"""
        try:
            progress_val = max(0, min(100, int(progress)))
            if text:
                st.write(text)
            return st.progress(progress_val)
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

# Convenience functions for common patterns
def create_auth_layout():
    """Create consistent auth page layout"""
    container = StableContainer.auth_page()
    load_css()
    return container

def create_main_layout():
    """Create consistent main app layout"""
    container = StableContainer.main_app()
    load_css()
    return container

def handle_oauth_section():
    """Handle OAuth section safely"""
    return ErrorBoundary.safe_render(lambda: st.container())

def handle_email_auth_section():
    """Handle email auth section safely"""
    return ErrorBoundary.safe_render(lambda: st.container())

# Export all classes and functions
__all__ = [
    'StableContainer',
    'SafeComponents', 
    'StatusMessages',
    'LayoutHelpers',
    'ErrorBoundary',
    'load_css',
    'create_auth_layout',
    'create_main_layout',
    'handle_oauth_section',
    'handle_email_auth_section'
] 