"""
Research paper retrieval from arXiv
"""
from datetime import datetime
from typing import List, Dict, Any

try:
    from langchain_community.retrievers import ArxivRetriever
    _ARXIV_AVAILABLE = True
except ImportError:
    ArxivRetriever = None
    _ARXIV_AVAILABLE = False

from research.config import DEFAULT_LOAD_MAX_DOCS, DEFAULT_TOP_K
from research.processors import make_paper_record_from_doc


def get_research_papers(
    query: str,
    mode: str = "topic",
    load_max_docs: int = DEFAULT_LOAD_MAX_DOCS,
    per_topic: int = 5,  # Not used in current implementation
    top_k: int = DEFAULT_TOP_K,
) -> List[Dict[str, Any]]:
    """
    Retrieve research papers from arXiv based on query.

    Args:
        query: Search query (topic, keywords, or author)
        mode: Search mode - "topic", "keywords", or "author"
        load_max_docs: Maximum documents to load from arXiv
        per_topic: Legacy parameter (not used)
        top_k: Maximum number of papers to return

    Returns:
        List of paper dictionaries with standardized format
    """
    if not _ARXIV_AVAILABLE:
        print("ArXiv retriever not available. Please install langchain-community.")
        return []

    try:
        # Initialize retriever
        retriever = ArxivRetriever(
            load_max_docs=load_max_docs,
            load_all_available_meta=True,
        )

        # Perform search based on mode
        docs = []
        if mode == "author":
            # Author search using arXiv syntax
            docs = retriever.invoke(f'au:"{query}"') or []
        else:
            # Topic or keyword search
            docs = retriever.invoke(query) or []

        # Limit to load_max_docs
        docs = docs[:load_max_docs]

        # Convert documents to paper records
        papers = []
        for doc in docs:
            try:
                paper_record = make_paper_record_from_doc(doc)
                papers.append(paper_record)
            except Exception as e:
                print(f"Failed to process document: {e}")
                continue

        # Apply keyword filtering for keyword mode
        if mode == "keywords":
            query_lower = query.lower()
            papers = [
                paper for paper in papers
                if query_lower in paper.get("title", "").lower()
                or query_lower in paper.get("raw_summary", "").lower()
            ]

        # Sort by date (newest first) and limit results
        papers.sort(key=lambda p: p["date"] or datetime.min, reverse=True)
        return papers[:top_k]

    except Exception as e:
        print(f"Research paper retrieval failed: {e}")
        return []
