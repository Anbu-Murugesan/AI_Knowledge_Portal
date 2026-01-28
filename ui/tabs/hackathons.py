"""
Hackathons tab UI implementation
"""
import streamlit as st
import datetime
import os
from events.hackathons import get_events as get_hackathons
from ui.helpers import apply_filters, format_events_as_text


def render_hackathons_tab():
    """Render the hackathons tab interface"""
    st.header("AI/ML Hackathons")

    # ----------------------------
    # Filters
    # ----------------------------
    col1, col2 = st.columns(2)
    with col1:
        location_options = ["All", "Online", "Chennai", "Bangalore", "Hyderabad", "Pune", "Noida", "Delhi", "Mumbai", "Kolkata"]
        location_filter = st.selectbox(
            "Location",
            location_options,
            index=location_options.index(st.session_state.get("hackathon_location_filter", "All")),
            key="hackathon_location_select"
        )
        st.session_state["hackathon_location_filter"] = location_filter

    with col2:
        type_options = ["All", "Online", "Offline"]
        type_filter = st.selectbox(
            "Type",
            type_options,
            index=type_options.index(st.session_state.get("hackathon_type_filter", "All")),
            key="hackathon_type_select"
        )
        st.session_state["hackathon_type_filter"] = type_filter

    fetch_hackathons = st.button("Load hackathons", key="fetch_hackathons_top")

    # ----------------------------
    # Load + filter data
    # ----------------------------
    if fetch_hackathons:
        with st.spinner("Loading hackathons from cache..."):
            try:
                # 1️⃣ LOAD cached data
                all_results = get_hackathons()

                # 2️⃣ APPLY filters (POSITIONAL ARGS)
                results = apply_filters(
                    all_results,
                    location_filter,
                    type_filter
                )

            except Exception as e:
                st.error(f"Error loading hackathons: {e}")
                all_results = []
                results = []

        # ----------------------------
        # Display results
        # ----------------------------
        if not results:
            if not all_results:
                st.info("No upcoming hackathons found in cache. Run event_collector.py to update.")
            else:
                st.info("No hackathons match the selected filters.")
        else:
            st.markdown(f"**Showing {len(results)} hackathon(s)**")

            # Download button
            text_content = format_events_as_text(results, "hackathons")
            st.download_button(
                label="📥 Download Hackathons (.txt)",
                data=text_content,
                file_name=f"hackathons_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="download_hackathons"
            )

            for i, r in enumerate(results, start=1):
                st.markdown(f"**{i}. {r.get('title','No title')}**")
                st.markdown(f"📅 Date: {r.get('date', 'TBD')}")
                st.markdown(f"📍 Location: {r.get('location', 'TBD')}")
                st.markdown(f"🧭 Type: {r.get('type', 'TBD')}")
                st.markdown(f"🔗 [Link]({r.get('url')})")
                st.markdown(f"*Source: {r.get('source', 'N/A')}*")
                st.markdown("---")
