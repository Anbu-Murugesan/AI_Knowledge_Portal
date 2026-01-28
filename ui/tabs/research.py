"""
Research papers tab UI implementation
"""
import streamlit as st
import datetime
from research.research_paper import get_research_papers
from ui.helpers import format_papers_as_text


def render_research_tab():
    """Render the research papers tab interface"""
    st.header("📄 Research Papers — arXiv")

    # ---------------- Layout: 2 x 2 ----------------
    col1, col2 = st.columns(2)
    with col1:
        topic = st.selectbox(
            "📌 Select Topic",
            options=st.session_state["research_choices"],
            index=(
                st.session_state["research_choices"].index(
                    st.session_state["research_selected"]
                )
                if st.session_state["research_selected"] in st.session_state["research_choices"]
                else 0
            ),
            key="research_topic_select"
        )

    with col2:
        keyword_input = st.text_input(
            "🔍 Search by Keyword",
            placeholder="e.g. RAG, transformers, diffusion",
            key="research_keyword_input"
        )

    col3, col4 = st.columns(2)
    with col3:
        author_input = st.text_input(
            "✍️ Search by Author",
            placeholder="e.g. Yann LeCun, Andrew Ng",
            key="research_author_input"
        )

    with col4:
        fetch_papers = st.button("▶️ Fetch Papers", key="research_fetch_btn")

    papers = []  # ✅ ensure scope exists

    # ---------------- Query Resolution ----------------
    if fetch_papers:
        author = author_input.strip()
        keyword = keyword_input.strip()

        # 🔹 Decide mode & query (PRIORITY ORDER)
        if author:
            mode = "author"
            query = author
            st.caption(f"🔎 Author search: **{author}**")

        elif keyword:
            mode = "keywords"
            query = keyword
            st.caption(f"🔎 Keyword search: **{keyword}**")

        else:
            mode = "topic"
            query = topic
            st.caption(f"🔎 Topic search: **{topic}**")

        with st.spinner("Fetching research papers from arXiv..."):
            try:
                papers = get_research_papers(query=query, mode=mode)
            except Exception as e:
                st.error(f"Failed to fetch papers: {e}")
                papers = []

    # ---------------- Results ----------------
    if fetch_papers:
        if not papers:
            st.info("No papers found for the given query.")
        else:
            st.success(f"Found {len(papers)} papers")

            # 📥 DOWNLOAD BUTTON (ADDED)
            text_content = format_papers_as_text(papers, query)
            st.download_button(
                label="📥 Download Research Papers (.txt)",
                data=text_content,
                file_name=f"research_{query}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                key="download_research"
            )

            for i, p in enumerate(papers, start=1):
                # Shorten long titles to one sentence for better UI display
                full_title = p.get('title', 'No title')
                if len(full_title) > 100:  # If title is too long
                    # Take first sentence or first 100 characters, whichever comes first
                    title_parts = full_title.split('.')
                    short_title = title_parts[0].strip() + '.' if title_parts[0] else full_title[:100] + '...'
                else:
                    short_title = full_title

                st.markdown(f"### {i}. {short_title}")

                authors = p.get("authors") or []
                if authors:
                    st.markdown(f"*Authors:* {', '.join(authors)}")

                if p.get("date"):
                    try:
                        st.markdown(f"*Date:* {p['date'].date().isoformat()}")
                    except Exception:
                        st.markdown(f"*Date:* {p['date']}")

                links = []
                if p.get("url"):
                    links.append(f"[Abstract]({p['url']})")
                if p.get("pdf"):
                    links.append(f"[PDF]({p['pdf']})")
                if links:
                    st.markdown(" | ".join(links))

                if p.get("llm_overview"):
                    st.markdown("**🧠 Overview**")
                    st.write(p["llm_overview"])

                if p.get("llm_key_points"):
                    st.markdown("**🔹 Key Contributions**")
                    for kp in p["llm_key_points"]:
                        st.markdown(f"- {kp}")

                st.markdown("---")
