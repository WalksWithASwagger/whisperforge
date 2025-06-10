#!/usr/bin/env python3
"""
WhisperForge Main Router
Serves different pages based on URL parameters
"""

import streamlit as st
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_page_from_url():
    """Get page parameter from URL"""
    query_params = st.query_params
    return query_params.get("page", "main")

def main():
    """Main router - serves different pages based on URL"""
    
    # Get page parameter
    page = get_page_from_url()
    
    if page == "waitlist":
        # Import and run waitlist page
        from waitlist import main as waitlist_main
        waitlist_main()
    else:
        # Import and run main app
        from app import main as app_main
        app_main()

if __name__ == "__main__":
    main() 