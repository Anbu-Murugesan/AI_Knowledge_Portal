"""
Event data collection from web sources
"""
import os
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Configuration
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# Tavily search queries for AI/ML events (expanded for maximum results)
TAVILY_QUERIES = [
    # Hackathon queries
    "AI hackathon 2026 india kaggle hackerearth",
    "machine learning hackathon 2026 india",
    "deep learning hackathon 2026 india",
    "computer vision hackathon 2026 india",

    # Conference queries
    "AI conference 2026 india neurips icml cvpr aaai",
    "machine learning conference 2026 india",
    "deep learning conference 2026 india",
    "computer vision conference 2026 india",

    # Workshop queries
    "AI workshop 2026 india",
    "machine learning workshop 2026 india",
    "deep learning workshop 2026 india",
    "computer vision workshop 2026 india",

    # Additional specialized queries
    "generative AI hackathon 2026 india",
    "LLM workshop 2026 india",
    "agentic AI conference 2026 india",
    "RAG workshop 2026 india",
    "transformers conference 2026 india",
    "diffusion models workshop 2026 india",
    "computer vision hackathon 2026 india",
    "reinforcement learning conference 2026 india",
    "NLP workshop 2026 india",
    "data science conference 2026 india",
]


def search_tavily(query: str) -> List[Dict[str, Any]]:
    """
    Search using Tavily API for AI/ML events.

    Args:
        query: Search query string

    Returns:
        List of event dictionaries with title, url, content, etc.
    """
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY environment variable not set")

    try:
        from tavily import TavilyClient
    except ImportError:
        raise ImportError("tavily-python package not installed. Run: pip install tavily-python")

    client = TavilyClient(api_key=TAVILY_API_KEY)

    try:
        # Use Tavily search
        response = client.search(
            query=query,
            search_depth="advanced",
            include_images=False,
            include_answer=False,
            include_raw_content=False,
            max_results=20,
            include_domains=None,
            exclude_domains=None
        )

        results = response.get("results", [])

        # Convert Tavily results to our format
        events = []
        for result in results:
            title = result.get("title", "").strip()
            url = result.get("url", "").strip()
            content = result.get("content", "").strip()

            if title and url:
                events.append({
                    "title": title,
                    "url": url,
                    "content": content,
                    "source": "tavily",
                    "query": query
                })

        return events

    except Exception as e:
        print(f"Tavily search failed for query '{query}': {e}")
        return []


def collect_events_from_web() -> List[Dict[str, Any]]:
    """
    Collect events from all web sources (currently Tavily).

    Returns:
        List of raw event dictionaries
    """
    all_events = []

    print(f"Starting event collection with {len(TAVILY_QUERIES)} queries...")

    for i, query in enumerate(TAVILY_QUERIES, 1):
        print(f"Query {i}/{len(TAVILY_QUERIES)}: {query}")

        try:
            events = search_tavily(query)
            all_events.extend(events)
            print(f"  Found {len(events)} events")

            # Small delay to be respectful
            if i < len(TAVILY_QUERIES):
                import time
                time.sleep(0.5)

        except Exception as e:
            print(f"  Failed: {e}")
            continue

    print(f"Total events collected: {len(all_events)}")
    return all_events
