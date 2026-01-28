"""
Event Collector for AI/ML Events

Background job that runs every 6 hours to collect upcoming events related to:
- AI, Machine Learning, Deep Learning, Computer Vision, Generative AI, Agentic AI, RAG

Data Sources:
1. Tavily web search (primary and only method - requires TAVILY_API_KEY)

Requirements:
- pip install tavily-python python-dateutil
- Set TAVILY_API_KEY environment variable

Output: JSON cache file with deduplicated future events
"""

from typing import Dict, List, Any
from events.collectors import collect_events_from_web
from events.processors import (
    process_events_batch,
    deduplicate_events_globally,
    filter_future_events
)
from events.storage import save_cache


def collect_all_events() -> Dict[str, List[Dict[str, Any]]]:
    """
    Main function to collect and process all events.

    Returns:
        Dictionary with categories as keys and event lists as values
    """
    # Step 1: Collect raw events from web sources
    print("Step 1: Collecting raw events from web sources...")
    raw_events = collect_events_from_web()

    if not raw_events:
        print("No events collected from web sources")
        return {"hackathons": [], "conferences": [], "workshops": []}

    # Step 2: Process raw events into standardized format
    print(f"Step 2: Processing {len(raw_events)} raw events...")
    processed_events = process_events_batch(raw_events)

    # Step 3: Global deduplication
    print(f"Step 3: Deduplicating {len(processed_events)} processed events...")
    deduplicated_events = deduplicate_events_globally(processed_events)

    # Step 4: Filter future events only
    print(f"Step 4: Filtering future events from {len(deduplicated_events)} events...")
    future_events = filter_future_events(deduplicated_events)

    # Step 5: Categorize events by type
    print(f"Step 5: Categorizing {len(future_events)} future events...")
    events_by_category = {"hackathons": [], "conferences": [], "workshops": []}

    for event in future_events:
        category = event.get("category", "conferences")  # default fallback
        if category in events_by_category:
            events_by_category[category].append(event)
        else:
            # If unknown category, put in conferences
            events_by_category["conferences"].append(event)

    # Print summary
    total_events = sum(len(events) for events in events_by_category.values())
    print("\nCollection Summary:")
    print(f"  Hackathons: {len(events_by_category['hackathons'])}")
    print(f"  Conferences: {len(events_by_category['conferences'])}")
    print(f"  Workshops: {len(events_by_category['workshops'])}")
    print(f"  Total: {total_events}")

    return events_by_category


def main():
    """Main collection function."""
    try:
        events = collect_all_events()
        save_cache(events)
        print("Event collection completed successfully")
    except Exception as e:
        print(f"Event collection failed: {e}")
        raise


if __name__ == "__main__":
    main()


# Cron schedule: run every 6 hours
# 0 */6 * * * /path/to/python /path/to/event_collector.py
