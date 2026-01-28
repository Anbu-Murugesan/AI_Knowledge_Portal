"""
Research paper utility functions
"""
import logging
import re
from datetime import datetime
from html import unescape
from typing import Dict, Any

from research.config import LOG_LEVEL, LOG_FORMAT


# ================== LOGGING ==================

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT
    )


# ================== UTILITY FUNCTIONS ==================

def parse_date(meta: Dict[str, Any]) -> datetime | None:
    """
    Parse date from arXiv metadata.

    Args:
        meta: ArXiv metadata dictionary

    Returns:
        Parsed datetime object or None if parsing fails
    """
    try:
        date_str = meta.get("Published") or meta.get("published") or meta.get("date")
        if not date_str:
            return None

        # Handle different date formats from arXiv
        if isinstance(date_str, str):
            # Try different common formats
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%d %b %Y",
                "%Y-%m-%dT%H:%M:%SZ",
                "%a, %d %b %Y %H:%M:%S %Z"
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

        return None
    except Exception:
        return None


def prepare_abstract_for_llm(text: str, max_words: int = 120) -> str:
    """
    Prepare abstract text for LLM processing by cleaning and truncating.

    Args:
        text: Raw abstract text
        max_words: Maximum number of words to keep

    Returns:
        Cleaned and truncated abstract text
    """
    if not text:
        return ""

    # Unescape HTML entities
    text = unescape(text)

    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())

    # Split into words and truncate
    words = text.split()
    if len(words) > max_words:
        words = words[:max_words]
        text = ' '.join(words) + '...'

    return text


def filter_papers_by_author(papers: list[Dict[str, Any]], author_query: str) -> list[Dict[str, Any]]:
    """
    Filter papers by author name (case-insensitive partial match).

    Args:
        papers: List of paper dictionaries
        author_query: Author name to search for

    Returns:
        Filtered list of papers by the specified author
    """
    if not author_query or not papers:
        return papers

    query_lower = author_query.lower().strip()
    filtered = []

    for paper in papers:
        authors = paper.get("authors", [])
        if isinstance(authors, str):
            authors = [authors]

        # Check if any author matches the query
        for author in authors:
            if query_lower in author.lower():
                filtered.append(paper)
                break

    return filtered
