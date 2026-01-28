"""
research_paper.py

Fetch arXiv papers and generate:
- 2-line LLM overview
- 3–5 bullet key points per paper

Supports:
- Topic search
- Keyword search
- Author filtering (post-process)

This is now a thin orchestrator that uses the modular research/ package.
"""

from typing import List, Dict, Any
from research.config import DEFAULT_TOPICS
from research.retrievers import get_research_papers
from research.utils import filter_papers_by_author


# ================== PUBLIC API ==================

def get_trending_papers_for_topic(topic: str, **kwargs) -> List[Dict[str, Any]]:
    """
    Legacy function for backward compatibility.
    Use get_research_papers() directly for new code.
    """
    return get_research_papers(query=topic, mode="topic", **kwargs)


# ================== CLI TEST ==================

if __name__ == "__main__":
    # Test the research paper retrieval
    results = get_research_papers("Yann LeCun", mode="author")
    for paper in results:
        print(f"{paper['title']} - {paper['authors']}")
