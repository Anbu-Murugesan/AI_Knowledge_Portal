"""
Main Streamlit application entry point
"""
import streamlit as st
from ui import setup_page_config, render_main_ui

# Import rebuild manager
from core.rebuild_manager import trigger_rebuild_if_needed
from core.logging_config import get_frontend_logger

# Setup logger
logger = get_frontend_logger()

# Trigger rebuild check on app startup (only once per session)
if 'rebuild_checked' not in st.session_state:
    logger.info("Application started - triggering rebuild check")
    trigger_rebuild_if_needed()
    st.session_state['rebuild_checked'] = True
    logger.debug("Rebuild check completed")


# Configure and run the main UI
def main():
    logger.info("Initializing Streamlit application")
    setup_page_config()
    render_main_ui()
    logger.debug("UI rendered successfully")


if __name__ == "__main__":
    main()
