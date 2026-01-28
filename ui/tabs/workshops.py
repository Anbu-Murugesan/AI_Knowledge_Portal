"""
Workshops tab UI implementation
"""
import streamlit as st
import datetime
from events.workshops import get_events as get_workshops
from ui.helpers import apply_filters, format_events_as_text


def render_workshops_tab():
    """Render the workshops tab interface"""
    st.header("AI/ML Workshops")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        location_options = ["All", "Online", "Chennai", "Bangalore", "Hyderabad", "Pune", "Noida", "Delhi", "Mumbai", "Kolkata"]
        st.session_state["workshop_location_filter"] = st.selectbox(
            "Location",
            location_options,
            index=location_options.index(st.session_state.get("workshop_location_filter", "All")),
            key="workshop_location_select"
        )

    with col2:
        type_options = ["All", "Online", "Offline"]
        st.session_state["workshop_type_filter"] = st.selectbox(
            "Type",
            type_options,
            index=type_options.index(st.session_state.get("workshop_type_filter", "All")),
            key="workshop_type_select"
        )

    fetch_workshops = st.button("Load workshops", key="fetch_workshops_top")

    if fetch_workshops:
        with st.spinner("Loading workshops from cache..."):
            try:
                all_results = get_workshops()
                results = apply_filters(
                    all_results,
                    st.session_state["workshop_location_filter"],
                    st.session_state["workshop_type_filter"]
                )
            except Exception as e:
                st.error(f"Error loading workshops: {e}")
                results = []

            if not results:
                if not all_results:
                    st.info("No upcoming workshops found in cache. Run event_collector.py to update.")
                else:
                    st.info("No workshops match the selected filters.")
            else:
                st.markdown(f"**Showing {len(results)} workshop(s)**")

                # Download button
                text_content = format_events_as_text(results, "workshops")
                st.download_button(
                    label="📥 Download Workshops (.txt)",
                    data=text_content,
                    file_name=f"workshops_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    key="download_workshops"
                )

                for i, r in enumerate(results, start=1):
                    st.markdown(f"**{i}. {r.get('title','No title')}**")
                    st.markdown(f"Date: {r.get('date')}")
                    st.markdown(f"Location: {r.get('location', 'TBD')}")
                    st.markdown(f"Type: {r.get('type', 'TBD')}")
                    st.markdown(f"[Link]({r.get('url')})")
                    st.markdown(f"*Source: {r.get('source')}*")
                    st.markdown("---")
