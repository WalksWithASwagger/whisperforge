"""
Styling utilities for WhisperForge without Streamlit page config conflicts
"""

import streamlit as st

def local_css():
    """Apply local CSS styling"""
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-bottom: 2rem;
        border-radius: 10px;
    }
    
    .content-section {
        background: #f8f9fa;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    </style>
    """, unsafe_allow_html=True)

def add_production_css():
    """Add production-ready CSS styling"""
    st.markdown("""
    <style>
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }
    
    /* Animation for loading states */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem 0;
            font-size: 1.5rem;
        }
        
        .content-section {
            padding: 1rem;
            margin: 0.5rem 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def create_custom_header():
    """Create a custom header for the app"""
    st.markdown("""
    <div class="main-header">
        <h1>WhisperForge - Aurora Edition</h1>
        <p>Transform Audio into Actionable Content with AI</p>
    </div>
    """, unsafe_allow_html=True)

def load_js():
    """Load custom JavaScript (if needed)"""
    st.markdown("""
    <script>
    // Custom JavaScript can be added here if needed
    console.log('WhisperForge Supabase loaded');
    </script>
    """, unsafe_allow_html=True) 