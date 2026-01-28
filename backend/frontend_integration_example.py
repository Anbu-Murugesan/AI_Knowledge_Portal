"""
Frontend integration examples.

This file shows how the existing Streamlit frontend can be modified
to call the FastAPI backend instead of direct function calls.

The integration is designed so switching between modes is simple.
"""

import os
from typing import List, Dict, Any, Optional
import requests
import streamlit as st


# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class APIClient:
    """Client for calling backend APIs."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def get_research_papers(self, query: str, mode: str = "topic", load_max_docs: int = 8, top_k: int = 10) -> List[Dict[str, Any]]:
        """Call research papers API."""
        url = f"{self.base_url}/api/research/papers"
        payload = {
            "query": query,
            "mode": mode,
            "load_max_docs": load_max_docs,
            "top_k": top_k
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["papers"]

    def search_blog_rss(self, query: str, selected_tool: str = "rss", selected_blog: Optional[str] = None, build_if_missing: bool = False) -> Dict[str, Any]:
        """Call blog/RSS search API."""
        url = f"{self.base_url}/api/blog/search"
        payload = {
            "query": query,
            "selected_tool": selected_tool,
            "selected_blog": selected_blog,
            "build_if_missing": build_if_missing
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["result"]

    def get_hackathons(self) -> List[Dict[str, Any]]:
        """Call hackathons API."""
        url = f"{self.base_url}/api/events/hackathons"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["events"]

    def get_conferences(self) -> List[Dict[str, Any]]:
        """Call conferences API."""
        url = f"{self.base_url}/api/events/conferences"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["events"]

    def get_workshops(self) -> List[Dict[str, Any]]:
        """Call workshops API."""
        url = f"{self.base_url}/api/events/workshops"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data["events"]


# Global API client instance
api_client = APIClient()


# Example: Modified research tab that can use either direct calls or API calls
def render_research_tab(use_api: bool = False):
    """
    Modified research tab that can switch between direct function calls and API calls.

    Args:
        use_api: If True, use API calls; if False, use direct function calls
    """
    st.header("📄 Research Papers — arXiv")

    col1, col2 = st.columns(2)
    with col1:
        topic = st.selectbox("📌 Select Topic", ["machine learning", "deep learning"])

    with col2:
        keyword_input = st.text_input("🔍 Search by Keyword", placeholder="e.g. RAG, transformers")

    col3, col4 = st.columns(2)
    with col3:
        author_input = st.text_input("✍️ Search by Author", placeholder="e.g. Yann LeCun")

    with col4:
        fetch_papers = st.button("▶️ Fetch Papers")

    if fetch_papers:
        # Determine query mode and parameters
        author = author_input.strip()
        keyword = keyword_input.strip()

        if author:
            mode, query = "author", author
        elif keyword:
            mode, query = "keywords", keyword
        else:
            mode, query = "topic", topic

        with st.spinner("Fetching research papers..."):
            try:
                if use_api:
                    # Use API call
                    papers = api_client.get_research_papers(
                        query=query,
                        mode=mode,
                        load_max_docs=8,
                        top_k=10
                    )
                else:
                    # Use direct function call (existing behavior)
                    from research.retrievers import get_research_papers
                    papers = get_research_papers(
                        query=query,
                        mode=mode,
                        load_max_docs=8,
                        top_k=10
                    )

                if not papers:
                    st.info("No papers found.")
                else:
                    st.success(f"Found {len(papers)} papers")

                    for i, p in enumerate(papers, start=1):
                        # Shorten long titles (existing logic)
                        full_title = p.get('title', 'No title')
                        if len(full_title) > 100:
                            title_parts = full_title.split('.')
                            short_title = title_parts[0].strip() + '.' if title_parts[0] else full_title[:100] + '...'
                        else:
                            short_title = full_title

                        st.markdown(f"### {i}. {short_title}")

                        # Display paper metadata (existing logic)
                        authors = p.get("authors") or []
                        if authors:
                            st.markdown(f"*Authors:* {', '.join(authors)}")

                        # ... rest of existing display logic

            except Exception as e:
                st.error(f"Failed to fetch papers: {e}")


# Example: Modified blog search that can use either direct calls or API calls
def run_blog_search(query: str, selected_tool: str = "rss", selected_blog: Optional[str] = None, use_api: bool = False):
    """
    Modified blog search that can switch between direct function calls and API calls.

    Args:
        query: Search query
        selected_tool: "rss" or "blog"
        selected_blog: Blog source name (if using blog tool)
        use_api: If True, use API calls; if False, use direct function calls

    Returns:
        Search result state object
    """
    if use_api:
        # Use API call
        return api_client.search_blog_rss(
            query=query,
            selected_tool=selected_tool,
            selected_blog=selected_blog,
            build_if_missing=False
        )
    else:
        # Use direct function call (existing behavior)
        from core.workflows import run_full_workflow_example
        return run_full_workflow_example(
            query=query,
            selected_tool=selected_tool,
            selected_blog=selected_blog,
            build_if_missing=False
        )


# Example: Modified events loading that can use either direct calls or API calls
def load_events(event_type: str, use_api: bool = False) -> List[Dict[str, Any]]:
    """
    Modified events loading that can switch between direct function calls and API calls.

    Args:
        event_type: "hackathons", "conferences", or "workshops"
        use_api: If True, use API calls; if False, use direct function calls

    Returns:
        List of events
    """
    if use_api:
        # Use API calls
        if event_type == "hackathons":
            return api_client.get_hackathons()
        elif event_type == "conferences":
            return api_client.get_conferences()
        elif event_type == "workshops":
            return api_client.get_workshops()
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    else:
        # Use direct function calls (existing behavior)
        if event_type == "hackathons":
            from events.hackathons import get_events
            return get_events()
        elif event_type == "conferences":
            from events.conferences import get_events
            return get_events()
        elif event_type == "workshops":
            from events.workshops import get_events
            return get_events()
        else:
            raise ValueError(f"Unknown event type: {event_type}")


# Example: Toggle between API and direct calls in Streamlit
def add_backend_toggle():
    """
    Add a toggle to switch between API calls and direct function calls.
    This allows easy testing and gradual migration.
    """
    col1, col2 = st.columns([3, 1])
    with col2:
        use_api = st.checkbox("Use API", value=False, help="Toggle between direct function calls and API calls")
    return use_api


if __name__ == "__main__":
    # Example usage
    print("API Client Example:")
    print(f"Backend URL: {BACKEND_URL}")

    # Test API client (would work if backend is running)
    client = APIClient()
    print("API client created successfully")

    print("\nTo use in Streamlit:")
    print("1. Import: from backend.frontend_integration_example import api_client, add_backend_toggle")
    print("2. Add toggle: use_api = add_backend_toggle()")
    print("3. Replace function calls with API calls when use_api=True")
