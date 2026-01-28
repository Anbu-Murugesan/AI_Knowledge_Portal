"""
Research paper retrieval and processing package
"""

# Expose main functions for easy importing
from .research_paper import get_research_papers, get_trending_papers_for_topic, DEFAULT_TOPICS

__all__ = [
    "get_research_papers",
    "get_trending_papers_for_topic",
    "DEFAULT_TOPICS"
]
