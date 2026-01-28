# slides_app.py
"""
Streamlit app to render the presentation content for:

⭐ Internal AI Knowledge Portal
A unified intelligence hub for AI Engineers, Researchers & Data Teams

This file renders the exact structure and wording you provided.
Run: streamlit run slides_app.py
"""
import streamlit as st

st.set_page_config(page_title="Internal AI Knowledge Portal — Overview", layout="wide")

# --- Header Section ---
# Title + subtitle (as requested)
st.title("⭐ Internal AI Knowledge Portal")
st.markdown("## **A Unified Intelligence Hub for AI Engineers, Researchers & Data Teams**")

st.markdown("---")

# 🚀 Conceptual Overview (1st heading)
st.header("🚀 Conceptual Overview")
st.write(
    "Modern AI teams struggle with one core challenge:\n\n"
)
st.markdown(
    """
    <div padding: 15px; border-radius: 5px; border-left: 5px solid #ff9800;'>
        <h4 style='color: #e65100;'>AI information is exploding faster than teams can consume it.</h4>
    </div>
    """, 
    unsafe_allow_html=True
)
st.write("\n")
st.write(
    "Every day, new AI models, research papers, blog posts, and industry updates are released across hundreds of sources. "
    "Engineers, analysts, and product teams spend enormous time searching, filtering, and trying to stay up-to-date — often missing "
    "critical advancements that could influence product decisions.\n\n"
    "The Internal AI Knowledge Portal solves this problem by bringing **all AI-related knowledge into one centralized, searchable, "
    "and intelligent workspace**, powered by RAG, vector search, and automated data collection."
)


st.markdown("---")

# 🧠 What the Portal Does (2nd heading)
st.header("🧠 What the Portal Does")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Aggregates & Organizes External AI Knowledge 📰")
    # st.markdown(
    #     """
    #     * **Past week AI news** from RSS feeds
    #     * **Curated AI blogs** organized by topic
    #     * Latest **research papers** from arXiv
    #     * Upcoming AI **hackathons, conferences**, and workshops
    #     """
    # )

with col2:
    st.subheader("2. Provides a Smart AI Chatbot for Knowledge Retrieval 💬")
    # st.markdown(
    #     """
    #     * Search across all collected knowledge with **keywords or natural language**
    #     * Get **precise, synthesized AI insights** instead of long lists of documents
    #     """
    # )

st.markdown("---")

# REALTIME (3rd heading)
st.header("⏳ Realtime Usecases")

st.info("A unified intelligence hub")
st.warning("Finance & Investment Research Portal")
st.info("Pharma & Life Sciences Research Portal")



st.markdown("---")

# KEY BENEFITS (4th heading)
st.header("✅ Key Benefits")

# Define only one column (col_b content) which will now span full width
# st.columns(2) is removed entirely to collapse to a single column layout

# Content originally in col_b, now spanning full width
st.markdown("### **Reduces Noise & Saves Time** ⏱️")

# Content originally inside the expander, now displayed in normal markdown style
st.markdown(
    """
    * **Hyper-Focused Curation**
    * **Manual Research Reduction**
    """
)

st.markdown("---")
