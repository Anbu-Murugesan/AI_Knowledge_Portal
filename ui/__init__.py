"""
Main UI module for the AI Knowledge Portal
"""
import os
import streamlit as st
from .session import initialize_session_state
from .tabs.chat import render_chat_tab
from .tabs.research import render_research_tab
from .tabs.hackathons import render_hackathons_tab
from .tabs.conferences import render_conferences_tab
from .tabs.workshops import render_workshops_tab
from core.workflows import BLOG_SOURCES, run_full_workflow_example


def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(page_title="Multi-tool Chatbot + Research + Workshops", layout="wide")


def render_main_ui():
    """Render the main UI with all tabs"""
    # Initialize session state
    initialize_session_state()

    # Title
    st.title("⭐ Internal AI Knowledge Portal")

    # Create tabs
    tab_chat, tab_research, tab_hackathons, tab_conferences, tab_workshops = st.tabs([
        "Chatbot", "Research Papers", "Hackathons", "Conferences", "Workshops"
    ])

    # Render each tab
    with tab_chat:
        render_chat_tab()

    with tab_research:
        render_research_tab()

    with tab_hackathons:
        render_hackathons_tab()

    with tab_conferences:
        render_conferences_tab()

    with tab_workshops:
        render_workshops_tab()

    # Footer controls
    render_footer()


def render_footer():
    """Render footer with utility controls"""
    col_left, col_right = st.columns([3, 1])
    with col_left:
        st.write("Session info:")
        st.write(f"Selected tool (last message): **{st.session_state['last_tool']}**")
        st.write(f"Chat sessions: {len(st.session_state['all_chat_sessions'])}")

    with col_right:
        if st.button("Rebuild indexes (slow)", key="footer_rebuild_btn"):
            with st.spinner("Rebuilding indexes... this runs scraping + indexing and may take many minutes"):
                try:
                    res = run_full_workflow_example(query="", selected_tool="rss", build_if_missing=True)
                except Exception as e:
                    st.error(f"Rebuild failed with exception: {e}")
                else:
                    if getattr(res, "status", "") == "error" or getattr(res, "error", None):
                        st.error(f"Rebuild failed: {getattr(res, 'error', 'unknown error')}")
                    else:
                        st.success("Rebuild finished. Indexes persisted and ready for queries.")

        if st.button("Clear chat", key="footer_clear_btn"):
            # Clear current chat session
            if st.session_state["current_chat_session_id"] in st.session_state["all_chat_sessions"]:
                st.session_state["all_chat_sessions"][st.session_state["current_chat_session_id"]] = []
                st.session_state["chat_history"] = []
            st.session_state["last_assistant_render"] = ""
            st.session_state["last_state"] = None
            st.session_state["chat_user_input"] = ""
            if hasattr(st, "experimental_rerun"):
                st.rerun()


def render_blog_selector():
    """Render blog selection UI component"""
    BLOG_OPTIONS = list(BLOG_SOURCES.keys())
    default_blog = st.session_state.get("selected_blog", "KDnuggets")

    selected_blog = st.selectbox(
        "Select Blog Source",
        BLOG_OPTIONS,
        index=BLOG_OPTIONS.index(default_blog) if default_blog in BLOG_OPTIONS else 0,
        key="selected_blog_ui"
    )
    st.session_state["selected_blog"] = selected_blog

    blog_dir = BLOG_SOURCES[selected_blog]["faiss_dir"]
    if os.path.isdir(blog_dir):
        st.caption(f"✅ {selected_blog} index is ready")
    else:
        st.caption(f"⚠️ {selected_blog} index not built yet")


def check_build_status(tool_choice):
    """Check if index needs building and show appropriate UI"""
    if tool_choice == "blog":
        blog_dir = BLOG_SOURCES[st.session_state["selected_blog"]]["faiss_dir"]
        index_file = os.path.join(blog_dir, "index.faiss")
        if not os.path.exists(index_file):
            auto_build = True
            st.session_state["is_building"] = True
            st.info(f"🔧 Building {st.session_state['selected_blog']} index (first time only)")
            return auto_build
    return False
