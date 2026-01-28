"""
Chat tab UI implementation
"""
import streamlit as st
import datetime
import traceback
import os
from core.workflows import run_full_workflow_example, BLOG_SOURCES
from ui.helpers import render_bulleted_articles, format_top_results_for_ui_with_summary_plain_title, get_chat_download_content


def render_chat_tab():
    """Render the chat tab interface"""
    st.markdown("### 💬 Chat")

    # ---------------------------
    # TOOL + BLOG SELECTOR
    # ---------------------------
    BLOG_OPTIONS = list(BLOG_SOURCES.keys())

    TOOL_LABEL_MAP = {
        "AI News": "rss",
        "Blogs": "blog"
    }

    tool_display = st.selectbox(
        " ",
        list(TOOL_LABEL_MAP.keys()),
        index=1,
        key="chat_tools_selectbox",
        label_visibility="collapsed"
    )

    tool_choice_local = TOOL_LABEL_MAP[tool_display]

    if tool_choice_local == "blog":
        # Use existing selected_blog if set and not None, otherwise fall back to first option
        default_blog = st.session_state.get("selected_blog") or BLOG_OPTIONS[0]
        try:
            default_index = BLOG_OPTIONS.index(default_blog)
        except ValueError:
            default_index = 0

        selected_blog = st.selectbox(
            "Select Blog Source",
            BLOG_OPTIONS,
            index=default_index,
            key="selected_blog_ui"
        )
        st.session_state["selected_blog"] = selected_blog
    else:
        st.session_state["selected_blog"] = None

    # ---------------------------
    # USER INPUT
    # ---------------------------
    user_query_input = st.text_input(
        "Ask a question",
        key="chat_input_tab",
        placeholder="Ask about AI news or blog insights...",
        label_visibility="collapsed"
    )

    send_pressed = st.button("Send", key="chat_send_btn")

    # ---------------------------
    # SEND HANDLER
    # ---------------------------
    if send_pressed and user_query_input:
        tool_choice = tool_choice_local
        session_id = st.session_state["current_chat_session_id"]

        # Store USER message
        st.session_state["all_chat_sessions"].setdefault(session_id, []).append({
            "role": "user",
            "text": user_query_input,
            "tool": tool_choice,
            "ts": datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        })

        auto_build = False
        if tool_choice == "blog":
            blog_dir = BLOG_SOURCES[st.session_state["selected_blog"]]["faiss_dir"]
            if not os.path.exists(os.path.join(blog_dir, "index.faiss")):
                auto_build = True
                st.info(f"🔧 Building {st.session_state['selected_blog']} index (first time only)")

        with st.spinner("Retrieving results..."):
            try:
                state = run_full_workflow_example(
                    query=user_query_input,
                    selected_tool=tool_choice,
                    selected_blog=st.session_state.get("selected_blog"),
                    build_if_missing=auto_build
                )

                output_md = render_bulleted_articles(state)
                if not output_md or "No summarized" in output_md:
                    output_md = format_top_results_for_ui_with_summary_plain_title(state)

            except Exception as e:
                output_md = f"❌ Error: {e}\n\n{traceback.format_exc()}"

        # Store ASSISTANT message
        st.session_state["all_chat_sessions"][session_id].append({
            "role": "assistant",
            "text": output_md,
            "tool": tool_choice,
            "ts": datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        })

        st.session_state["chat_user_input"] = ""
        st.rerun()

    # ---------------------------
    # CHAT HISTORY RENDER
    # ---------------------------
    st.markdown("### Conversation")

    history = st.session_state["all_chat_sessions"].get(
        st.session_state["current_chat_session_id"], []
    )

    # Group messages into Q&A pairs and display newest first
    qa_pairs = []
    i = 0
    while i < len(history):
        if history[i]["role"] == "user":
            user_msg = history[i]
            # Look for the next assistant message
            assistant_msg = None
            j = i + 1
            while j < len(history) and history[j]["role"] != "assistant":
                j += 1
            if j < len(history):
                assistant_msg = history[j]
            qa_pairs.append((user_msg, assistant_msg))
            i = j + 1
        else:
            i += 1

    # Display Q&A pairs in reverse chronological order (newest first)
    for user_msg, assistant_msg in reversed(qa_pairs):
        # Display question first
        with st.chat_message("user"):
            st.markdown(user_msg["text"])

        # Display answer second (if exists)
        if assistant_msg:
            with st.chat_message("assistant"):
                st.markdown(assistant_msg["text"])

    # =========================================================
    # 🔽 SESSION + DOWNLOAD (BOTTOM — AS REQUESTED)
    # =========================================================
    st.markdown("---")
    st.subheader("Session Controls")

    col1, col2 = st.columns([1, 1])

    # ➕ New Chat
    with col1:
        if st.button("➕ Start New Chat", key="chat_new_session_btn"):
            new_session_id = f"session_{len(st.session_state['all_chat_sessions']) + 1}"
            st.session_state["all_chat_sessions"][new_session_id] = []
            st.session_state["current_chat_session_id"] = new_session_id
            st.session_state["chat_user_input"] = ""
            st.rerun()

    # 📥 Download Chat
    with col2:
        if history:
            download_content = get_chat_download_content(
                st.session_state["current_chat_session_id"]
            )
            st.download_button(
                label="📥 Download Chat (.txt)",
                data=download_content,
                file_name=f"chat_{st.session_state['current_chat_session_id']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="download_chat_btn"
            )

    # 🔽 Session Selector (BOTTOM)
    session_ids = list(st.session_state["all_chat_sessions"].keys())
    if session_ids:
        selected_session = st.selectbox(
            "Select Chat Session",
            session_ids,
            index=session_ids.index(st.session_state["current_chat_session_id"]),
            key="chat_session_selector_bottom"
        )
        st.session_state["current_chat_session_id"] = selected_session
