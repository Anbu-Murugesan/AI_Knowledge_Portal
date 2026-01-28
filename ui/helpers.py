"""
UI helper functions for formatting and data processing
"""
import datetime
import streamlit as st
from typing import List, Dict, Any


def render_structured_post(gen: Dict[str, Any]) -> str:
    lines = []
    hook = gen.get("hook", "") if isinstance(gen, dict) else ""
    paragraphs = gen.get("paragraphs", []) if isinstance(gen, dict) else []
    bullets = gen.get("bullets", []) if isinstance(gen, dict) else []
    sources = gen.get("sources", []) if isinstance(gen, dict) else []

    if hook:
        lines.append(f"**Hook:**  \n{hook}\n")

    if paragraphs:
        lines.append("**Post:**")
        for p in paragraphs:
            lines.append(p + "\n")

    if bullets:
        lines.append("**Takeaways:**")
        for b in bullets:
            lines.append(f"- {b}")

    if sources:
        lines.append("\n**Sources:**")
        for s in sources:
            t = s.get("title", "") if isinstance(s, dict) else ""
            l = s.get("link", "") if isinstance(s, dict) else ""
            if t and l:
                lines.append(f"- {t}: {l}")
            elif l:
                lines.append(f"- {l}")
            elif t:
                lines.append(f"- {t}")

    return "\n\n".join(lines) if lines else ""


def apply_filters(events, location_filter, type_filter):
    """Apply location and type filters to events list."""
    if not events:
        return []

    filtered = events.copy()

    # Apply location filter
    if location_filter != "All":
        if location_filter == "Online":
            filtered = [e for e in filtered if e.get('location', '').lower() == 'online']
        else:
            filtered = [e for e in filtered if location_filter.lower() in e.get('location', '').lower()]

    # Apply type filter
    if type_filter != "All":
        filtered = [e for e in filtered if e.get('type', '') == type_filter]

    return filtered


def format_events_as_text(events, event_type):
    """Format events list as text for download."""
    if not events:
        return f"No {event_type} found."

    lines = [f"AI/ML {event_type.title()} - {len(events)} events\n"]
    lines.append("=" * 50)
    lines.append("")

    for i, event in enumerate(events, 1):
        lines.append(f"{i}. {event.get('title', 'No title')}")
        lines.append(f"   Date: {event.get('date', 'TBD')}")
        lines.append(f"   Location: {event.get('location', 'TBD')}")
        lines.append(f"   Type: {event.get('type', 'TBD')}")
        lines.append(f"   URL: {event.get('url', 'N/A')}")
        lines.append(f"   Source: {event.get('source', 'N/A')}")
        lines.append("")

    lines.append("=" * 50)
    lines.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(lines)


def format_papers_as_text(papers, topic):
    """Format research papers list as text for download."""
    if not papers:
        return f"No papers found for topic: {topic}"

    lines = [f"Research Papers - Topic: {topic} - {len(papers)} papers\n"]
    lines.append("=" * 50)
    lines.append("")

    for i, paper in enumerate(papers, 1):
        lines.append(f"{i}. {paper.get('title', 'No title')}")
        authors = paper.get("authors") or []
        if authors:
            lines.append(f"   Authors: {', '.join(authors)}")
        else:
            lines.append("   Authors: N/A")

        if paper.get("date"):
            try:
                date_str = paper['date'].date().isoformat() if hasattr(paper['date'], 'date') else str(paper['date'])
                lines.append(f"   Date: {date_str}")
            except Exception:
                lines.append(f"   Date: {paper['date']}")
        else:
            lines.append("   Date: N/A")

        if paper.get("url"):
            lines.append(f"   Abstract: {paper.get('url')}")
        if paper.get("pdf"):
            lines.append(f"   PDF: {paper.get('pdf')}")

        snippet = paper.get("snippet") or paper.get("raw_summary") or ""
        if snippet:
            lines.append(f"   Summary: {snippet[:500]}{'...' if len(snippet) > 500 else ''}")

        lines.append("")

    lines.append("=" * 50)
    lines.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(lines)


def get_chat_download_content(session_id: str) -> str:
    """Format a single chat session for download."""
    session_history = st.session_state["all_chat_sessions"].get(session_id, [])
    if not session_history:
        return f"No chat history found for session: {session_id}"

    lines = [f"Chat Session: {session_id}\n"]
    lines.append("=" * 50)
    lines.append("")

    for message in session_history:
        role = message.get("role", "Unknown").title()
        text = message.get("text", "")
        ts = message.get("ts", "N/A")
        lines.append(f"[{ts}] {role}: {text}")
    lines.append("")
    lines.append("=" * 50)
    lines.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(lines)


def extract_short_summary(item, max_chars=200) -> str:
    """
    Try several metadata fields for a short summary:
      - item['summary']
      - item['snippet']
      - item.get('page_content') first 300 chars
      - item.get('description')
    Return a single-line (or two-line) trimmed summary.
    """
    candidate = ""
    if isinstance(item, dict):
        candidate = (item.get("summary") or item.get("snippet") or item.get("description") or "").strip()
        if not candidate:
            candidate = (item.get("page_content") or item.get("content") or "").strip()
    else:
        candidate = str(item).strip()

    if not candidate:
        return ""

    s = " ".join(candidate.split())
    if len(s) <= max_chars:
        return s
    truncated = s[:max_chars].rsplit(" ", 1)[0]
    return truncated + "…"


def format_top_results_for_ui_with_summary_plain_title(state, top_n: int = 5) -> str:
    """
    Build a markdown block listing top_n results with:
      - clickable title (embedded link)
      - NO raw URL shown
      - 1–2 line summary
    """
    docs = getattr(state, "retrieved_docs", None)
    if not docs:
        docs = getattr(state, "sources", None) or []

    normalized = []
    for item in docs:
        if not item:
            continue

        title = (item.get("title") or "").strip()
        link = (item.get("link") or "").strip()
        summary = extract_short_summary(item, max_chars=200)

        if not title:
            continue

        normalized.append({
            "title": title,
            "link": link,
            "summary": summary
        })

    top = normalized[:top_n]

    if not top:
        return "No retriever results available."

    md_lines = [f"**Top {len(top)} Results:**\n"]

    for e in top:
        title = e["title"]
        link = e["link"]
        summary = e["summary"]

        # ✅ Title is clickable, link NOT shown separately
        # if link:
            # md_lines.append(f"- **[{title}]({link})**")
        if link:
            md_lines.append(f"- **[{title}]({link})**")
        else:
            md_lines.append(f"- **{title}**")

        if summary:
            md_lines.append(f"  _{summary}_")

        md_lines.append("")

    return "\n".join(md_lines)


def render_bulleted_articles(state) -> str:
    """
    Render final LLM output:
    title
    link
    bullet points
    """
    posts = getattr(state, "generated_post", None)

    if not posts or not isinstance(posts, list):
        return "No summarized results available."

    lines = []
    for i, item in enumerate(posts, 1):
        title = item.get("title", "").strip()
        link = item.get("link", "").strip()
        bullets = item.get("key_points", [])

        if not title and not bullets:
            continue

        if link:
            lines.append(f"### {i}. [{title}]({link})")
        else:
            lines.append(f"### {i}. {title}")


        # lines.append(f"### {i}. {title}")
        # if link:
        #     lines.append(link)

        if bullets:
            for b in bullets:
                lines.append(f"- {b}")
        else:
            lines.append("_No key points extracted._")

        lines.append("")  # spacing

    return "\n".join(lines)


def render_structured_post(gen: Dict[str, Any]) -> str:
    lines = []
    hook = gen.get("hook", "") if isinstance(gen, dict) else ""
    paragraphs = gen.get("paragraphs", []) if isinstance(gen, dict) else []
    bullets = gen.get("bullets", []) if isinstance(gen, dict) else []
    sources = gen.get("sources", []) if isinstance(gen, dict) else []

    if hook:
        lines.append(f"**Hook:**  \n{hook}\n")

    if paragraphs:
        lines.append("**Post:**")
        for p in paragraphs:
            lines.append(p + "\n")

    if bullets:
        lines.append("**Takeaways:**")
        for b in bullets:
            lines.append(f"- {b}")

    if sources:
        lines.append("\n**Sources:**")
        for s in sources:
            t = s.get("title", "") if isinstance(s, dict) else ""
            l = s.get("link", "") if isinstance(s, dict) else ""
            if t and l:
                lines.append(f"- {t}: {l}")
            elif l:
                lines.append(f"- {l}")
            elif t:
                lines.append(f"- {t}")

    return "\n\n".join(lines) if lines else ""
