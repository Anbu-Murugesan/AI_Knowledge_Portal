"""
Session state management for Streamlit UI
"""
import streamlit as st
from research.research_paper import DEFAULT_TOPICS


def initialize_session_state():
    """Initialize all session state variables"""

    # Chat session management
    if "all_chat_sessions" not in st.session_state:
        st.session_state["all_chat_sessions"] = {}
    if "current_chat_session_id" not in st.session_state:
        st.session_state["current_chat_session_id"] = "default_session"
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "selected_tool_temp" not in st.session_state:
        st.session_state["selected_tool_temp"] = "rss"
    if "last_tool" not in st.session_state:
        st.session_state["last_tool"] = "rss"
    if "research_choices" not in st.session_state:
        st.session_state["research_choices"] = DEFAULT_TOPICS if DEFAULT_TOPICS else []
    if "research_selected" not in st.session_state:
        st.session_state["research_selected"] = st.session_state["research_choices"][0] if st.session_state["research_choices"] else ""
    if "hackathon_results" not in st.session_state:
        st.session_state["hackathon_results"] = []
    if "conference_results" not in st.session_state:
        st.session_state["conference_results"] = []
    if "workshop_results" not in st.session_state:
        st.session_state["workshop_results"] = []
    if "show_tool_selector" not in st.session_state:
        st.session_state["show_tool_selector"] = False

    # Event filters
    if "hackathon_location_filter" not in st.session_state:
        st.session_state["hackathon_location_filter"] = "All"
    if "hackathon_type_filter" not in st.session_state:
        st.session_state["hackathon_type_filter"] = "All"
    if "conference_location_filter" not in st.session_state:
        st.session_state["conference_location_filter"] = "All"
    if "conference_type_filter" not in st.session_state:
        st.session_state["conference_type_filter"] = "All"
    if "workshop_location_filter" not in st.session_state:
        st.session_state["workshop_location_filter"] = "All"
    if "workshop_type_filter" not in st.session_state:
        st.session_state["workshop_type_filter"] = "All"
    if "clear_next" not in st.session_state:
        st.session_state["clear_next"] = False

    if "chat_user_input" not in st.session_state:
        st.session_state["chat_user_input"] = ""
    if "last_assistant_render" not in st.session_state:
        st.session_state["last_assistant_render"] = ""
    if "last_state" not in st.session_state:
        st.session_state["last_state"] = None

    if "chat_input_tab" not in st.session_state:
        st.session_state["chat_input_tab"] = st.session_state.get("chat_user_input", "")
