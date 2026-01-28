"""
Event data storage and caching
"""
import os
import json
from typing import Dict, List, Any


# Configuration
CACHE_FILE = "events_cache.json"


def save_cache(events_by_category: Dict[str, List[Dict[str, Any]]]):
    """
    Save events cache to JSON file.

    Args:
        events_by_category: Dictionary with categories as keys and event lists as values
    """
    try:
        # Add metadata
        cache_data = {
            "metadata": {
                "last_updated": json.dumps(None),  # Will be set by datetime
                "total_events": sum(len(events) for events in events_by_category.values()),
                "categories": list(events_by_category.keys())
            },
            "events": events_by_category
        }

        # Set timestamp
        import datetime
        cache_data["metadata"]["last_updated"] = datetime.datetime.now().isoformat()

        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        print(f"Cache saved to {CACHE_FILE} with {cache_data['metadata']['total_events']} events")

    except Exception as e:
        print(f"Failed to save cache: {e}")
        raise


def load_cache() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load events cache from JSON file.

    Returns:
        Dictionary with categories as keys and event lists as values
    """
    if not os.path.exists(CACHE_FILE):
        print(f"Cache file {CACHE_FILE} not found, returning empty cache")
        return {"hackathons": [], "conferences": [], "workshops": []}

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        events_by_category = cache_data.get("events", {})
        metadata = cache_data.get("metadata", {})

        print(f"Cache loaded from {CACHE_FILE}")
        print(f"  Last updated: {metadata.get('last_updated', 'unknown')}")
        print(f"  Total events: {metadata.get('total_events', 0)}")
        print(f"  Categories: {metadata.get('categories', [])}")

        return events_by_category

    except Exception as e:
        print(f"Failed to load cache: {e}")
        return {"hackathons": [], "conferences": [], "workshops": []}


def get_cache_info() -> Dict[str, Any]:
    """
    Get information about the current cache.

    Returns:
        Dictionary with cache metadata
    """
    if not os.path.exists(CACHE_FILE):
        return {
            "exists": False,
            "last_updated": None,
            "total_events": 0,
            "categories": []
        }

    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        metadata = cache_data.get("metadata", {})
        return {
            "exists": True,
            "last_updated": metadata.get("last_updated"),
            "total_events": metadata.get("total_events", 0),
            "categories": metadata.get("categories", [])
        }

    except Exception as e:
        return {
            "exists": False,
            "last_updated": None,
            "total_events": 0,
            "categories": [],
            "error": str(e)
        }
