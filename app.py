"""
Main Streamlit application entry point
"""
from ui import setup_page_config, render_main_ui


# Configure and run the main UI
def main():
    setup_page_config()
    render_main_ui()


if __name__ == "__main__":
    main()
