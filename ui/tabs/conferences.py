"""
Conferences tab UI implementation
"""
import streamlit as st
import datetime
from events.conferences import get_events as get_conferences
from ui.helpers import apply_filters, format_events_as_text


def render_conferences_tab():
    """Render the conferences tab interface"""
    st.header("AI/ML Conferences")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        location_options = ["All", "Online", "Chennai", "Bangalore", "Hyderabad", "Pune", "Noida", "Delhi", "Mumbai", "Kolkata"]
        st.session_state["conference_location_filter"] = st.selectbox(
            "Location",
            location_options,
            index=location_options.index(st.session_state.get("conference_location_filter", "All")),
            key="conference_location_select"
        )

    with col2:
        type_options = ["All", "Online", "Offline"]
        st.session_state["conference_type_filter"] = st.selectbox(
            "Type",
            type_options,
            index=type_options.index(st.session_state.get("conference_type_filter", "All")),
            key="conference_type_select"
        )

    fetch_conferences = st.button("Load conferences", key="fetch_conferences_top")

    if fetch_conferences:
        with st.spinner("Loading conferences from cache..."):
            try:
                all_results = get_conferences()
                results = apply_filters(
                    all_results,
                    st.session_state["conference_location_filter"],
                    st.session_state["conference_type_filter"]
                )
            except Exception as e:
                st.error(f"Error loading conferences: {e}")
                results = []

            if not results:
                if not all_results:
                    st.info("No upcoming conferences found in cache. Run event_collector.py to update.")
                else:
                    st.info("No conferences match the selected filters.")
            else:
                st.markdown(f"**Showing {len(results)} conference(s)**")

                # Download button
                text_content = format_events_as_text(results, "conferences")
                st.download_button(
                    label="📥 Download Conferences (.txt)",
                    data=text_content,
                    file_name=f"conferences_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_conferences"
                )

                for i, r in enumerate(results, start=1):
                    st.markdown(f"**{i}. {r.get('title','No title')}**")
                    st.markdown(f"Date: {r.get('date')}")
                    st.markdown(f"Location: {r.get('location', 'TBD')}")
                    st.markdown(f"Type: {r.get('type', 'TBD')}")
                    st.markdown(f"[Link]({r.get('url')})")
                    st.markdown(f"*Source: {r.get('source')}*")
                    st.markdown("---")
