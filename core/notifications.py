"""
Beautiful Notification System for WhisperForge
Animated toast notifications and status updates
"""

import streamlit as st
import time
from typing import Optional, Literal
from datetime import datetime

class NotificationManager:
    """Manages beautiful notifications and status updates"""
    
    def __init__(self):
        self.notifications = []
        
    def show_toast(self, 
                   message: str, 
                   type: Literal["success", "error", "warning", "info"] = "info",
                   duration: float = 3.0,
                   icon: Optional[str] = None):
        """Show a beautiful toast notification"""
        
        # Auto-select icon based on type if not provided
        if not icon:
            icons = {
                "success": "✅",
                "error": "❌", 
                "warning": "⚠️",
                "info": "ℹ️"
            }
            icon = icons.get(type, "ℹ️")
        
        # Color scheme for different types
        colors = {
            "success": {
                "bg": "rgba(54, 211, 153, 0.1)",
                "border": "rgba(54, 211, 153, 0.4)",
                "text": "#36D399"
            },
            "error": {
                "bg": "rgba(248, 114, 114, 0.1)",
                "border": "rgba(248, 114, 114, 0.4)", 
                "text": "#F87272"
            },
            "warning": {
                "bg": "rgba(251, 189, 35, 0.1)",
                "border": "rgba(251, 189, 35, 0.4)",
                "text": "#FBBD23"
            },
            "info": {
                "bg": "rgba(58, 191, 248, 0.1)",
                "border": "rgba(58, 191, 248, 0.4)",
                "text": "#3ABFF8"
            }
        }
        
        color = colors[type]
        
        toast_html = f"""
        <div class="toast-notification {type}" id="toast-{int(time.time())}">
            <div class="toast-content">
                <span class="toast-icon">{icon}</span>
                <span class="toast-message">{message}</span>
            </div>
            <div class="toast-progress">
                <div class="toast-progress-bar"></div>
            </div>
        </div>
        
        <style>
        .toast-notification {{
            background: {color['bg']};
            border: 1px solid {color['border']};
            border-radius: 8px;
            padding: 12px 16px 4px 16px;
            margin: 8px 0;
            position: relative;
            overflow: hidden;
            animation: toast-slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}
        
        .toast-content {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .toast-icon {{
            font-size: 16px;
        }}
        
        .toast-message {{
            color: var(--text-primary);
            font-weight: 500;
            font-size: 0.9rem;
        }}
        
        .toast-progress {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: rgba(255, 255, 255, 0.1);
        }}
        
        .toast-progress-bar {{
            height: 100%;
            background: {color['text']};
            animation: toast-progress {duration}s linear forwards;
        }}
        
        @keyframes toast-slide-in {{
            from {{
                transform: translateX(100%);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
        
        @keyframes toast-progress {{
            from {{ width: 100%; }}
            to {{ width: 0%; }}
        }}
        </style>
        
        <script>
        setTimeout(function() {{
            var toast = document.getElementById('toast-{int(time.time())}');
            if (toast) {{
                toast.style.animation = 'toast-slide-out 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards';
                setTimeout(function() {{
                    toast.remove();
                }}, 300);
            }}
        }}, {duration * 1000});
        </script>
        """
        
        return st.markdown(toast_html, unsafe_allow_html=True)
    
    def show_status_indicator(self, 
                             status: str, 
                             details: str = "",
                             animated: bool = True):
        """Show a status indicator with optional animation"""
        
        # Status configurations
        status_configs = {
            "processing": {
                "icon": "🔄",
                "color": "#3ABFF8",
                "bg": "rgba(58, 191, 248, 0.1)",
                "border": "rgba(58, 191, 248, 0.3)"
            },
            "complete": {
                "icon": "✅", 
                "color": "#36D399",
                "bg": "rgba(54, 211, 153, 0.1)",
                "border": "rgba(54, 211, 153, 0.3)"
            },
            "error": {
                "icon": "❌",
                "color": "#F87272", 
                "bg": "rgba(248, 114, 114, 0.1)",
                "border": "rgba(248, 114, 114, 0.3)"
            },
            "waiting": {
                "icon": "⏳",
                "color": "#FBBD23",
                "bg": "rgba(251, 189, 35, 0.1)", 
                "border": "rgba(251, 189, 35, 0.3)"
            }
        }
        
        config = status_configs.get(status, status_configs["waiting"])
        animation_class = "status-animated" if animated else ""
        
        status_html = f"""
        <div class="status-indicator {animation_class}">
            <div class="status-main">
                <span class="status-icon">{config['icon']}</span>
                <span class="status-text">{status.title()}</span>
            </div>
            {f'<div class="status-details">{details}</div>' if details else ''}
        </div>
        
        <style>
        .status-indicator {{
            background: {config['bg']};
            border: 1px solid {config['border']};
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            transition: all 0.3s ease;
        }}
        
        .status-main {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .status-icon {{
            font-size: 18px;
        }}
        
        .status-text {{
            color: {config['color']};
            font-weight: 600;
            font-size: 1rem;
        }}
        
        .status-details {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-top: 4px;
            margin-left: 26px;
        }}
        
        .status-animated .status-icon {{
            animation: status-pulse 1.5s ease-in-out infinite;
        }}
        
        @keyframes status-pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.1); }}
        }}
        </style>
        """
        
        return st.markdown(status_html, unsafe_allow_html=True)

# Global notification manager instance
notification_manager = NotificationManager()

# Convenience functions
def show_success(message: str, duration: float = 3.0):
    """Show success notification"""
    return notification_manager.show_toast(message, "success", duration)

def show_error(message: str, duration: float = 5.0):
    """Show error notification"""
    return notification_manager.show_toast(message, "error", duration)

def show_warning(message: str, duration: float = 4.0):
    """Show warning notification"""
    return notification_manager.show_toast(message, "warning", duration)

def show_info(message: str, duration: float = 3.0):
    """Show info notification"""
    return notification_manager.show_toast(message, "info", duration)

def show_processing_status(details: str = ""):
    """Show processing status indicator"""
    return notification_manager.show_status_indicator("processing", details, True)

def show_complete_status(details: str = ""):
    """Show completion status indicator"""
    return notification_manager.show_status_indicator("complete", details, False)

def show_error_status(details: str = ""):
    """Show error status indicator"""
    return notification_manager.show_status_indicator("error", details, False)

def create_step_completion_animation():
    """Create a beautiful step completion animation"""
    animation_html = """
    <div class="step-completion-animation">
        <div class="completion-circle">
            <div class="checkmark">✓</div>
        </div>
        <div class="completion-text">Step Complete!</div>
    </div>
    
    <style>
    .step-completion-animation {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 16px;
        animation: completion-appear 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .completion-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, #36D399 0%, #10B981 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        animation: completion-scale 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 12px rgba(54, 211, 153, 0.3);
    }
    
    .checkmark {
        color: white;
        font-weight: bold;
        font-size: 16px;
        animation: checkmark-appear 0.3s ease 0.3s both;
    }
    
    .completion-text {
        color: #36D399;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    @keyframes completion-appear {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes completion-scale {
        0% { transform: scale(0); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    
    @keyframes checkmark-appear {
        from {
            opacity: 0;
            transform: scale(0);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    </style>
    """
    
    return st.markdown(animation_html, unsafe_allow_html=True)

def create_loading_spinner(text: str = "Processing..."):
    """Create a beautiful loading spinner"""
    spinner_html = f"""
    <div class="loading-spinner-container">
        <div class="loading-spinner">
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
        </div>
        <div class="loading-text">{text}</div>
    </div>
    
    <style>
    .loading-spinner-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;
        padding: 20px;
    }}
    
    .loading-spinner {{
        position: relative;
        width: 40px;
        height: 40px;
    }}
    
    .spinner-ring {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 3px solid transparent;
        border-top: 3px solid #7928CA;
        border-radius: 50%;
        animation: spinner-rotate 1.2s linear infinite;
    }}
    
    .spinner-ring:nth-child(2) {{
        border-top-color: #FF0080;
        animation-delay: -0.4s;
        animation-duration: 1.8s;
    }}
    
    .spinner-ring:nth-child(3) {{
        border-top-color: #3ABFF8;
        animation-delay: -0.8s;
        animation-duration: 2.4s;
    }}
    
    .loading-text {{
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 500;
    }}
    
    @keyframes spinner-rotate {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """
    
    return st.markdown(spinner_html, unsafe_allow_html=True) 