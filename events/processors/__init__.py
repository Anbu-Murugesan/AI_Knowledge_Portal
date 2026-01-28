"""
Event processing and categorization logic
"""
import datetime
from typing import List, Dict, Any


def categorize_event(title: str, url: str, description: str = "") -> str:
    """
    Categorize event based on title, URL, and description.

    Args:
        title: Event title
        url: Event URL
        description: Event description/content

    Returns:
        Category: "hackathons", "conferences", or "workshops"
    """
    combined_text = f"{title} {url} {description}".lower()

    # Hackathon indicators
    hackathon_keywords = [
        "hackathon", "hack", "kaggle", "hacker", "coding challenge",
        "data science competition", "ml competition", "ai competition",
        "hackerearth", "hackerrank", "codechef"
    ]

    # Workshop indicators
    workshop_keywords = [
        "workshop", "tutorial", "bootcamp", "training", "hands-on",
        "practical session", "lab session", "masterclass"
    ]

    # Conference indicators
    conference_keywords = [
        "conference", "summit", "symposium", "conclave", "forum",
        "neurips", "icml", "cvpr", "aaai", "acl", "emnlp"
    ]

    # Check for hackathon keywords
    for keyword in hackathon_keywords:
        if keyword in combined_text:
            return "hackathons"

    # Check for workshop keywords
    for keyword in workshop_keywords:
        if keyword in combined_text:
            return "workshops"

    # Check for conference keywords
    for keyword in conference_keywords:
        if keyword in combined_text:
            return "conferences"

    # Default categorization based on common patterns
    if "hack" in combined_text:
        return "hackathons"
    elif "workshop" in combined_text or "tutorial" in combined_text:
        return "workshops"
    else:
        return "conferences"


def process_raw_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a raw event into standardized format.

    Args:
        raw_event: Raw event dictionary from collector

    Returns:
        Processed event dictionary with standardized fields
    """
    title = raw_event.get("title", "").strip()
    url = raw_event.get("url", "").strip()
    content = raw_event.get("content", "").strip()

    # Import here to avoid circular imports
    from events.utils import parse_date_candidates, detect_location, detect_event_type

    # Extract dates
    dates = parse_date_candidates(f"{title} {content}")
    if dates:
        # Use the first future date found
        today = datetime.date.today()
        future_dates = [d for d in dates if d >= today]
        if future_dates:
            event_date = future_dates[0]
        else:
            event_date = dates[0]  # fallback to any date found
    else:
        event_date = None

    # Detect location
    location = detect_location(f"{title} {content}")

    # Detect event type
    event_type = detect_event_type(title)

    # Categorize event
    category = categorize_event(title, url, content)

    # Create processed event
    processed_event = {
        "title": title,
        "url": url,
        "date": event_date.isoformat() if event_date else None,
        "location": location,
        "type": event_type,
        "source": raw_event.get("source", "unknown"),
        "description": content[:500] if content else "",  # truncate long descriptions
        "category": category,
        "collected_at": datetime.datetime.now().isoformat()
    }

    return processed_event


def process_events_batch(raw_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a batch of raw events into standardized format.

    Args:
        raw_events: List of raw event dictionaries

    Returns:
        List of processed event dictionaries
    """
    processed_events = []

    for raw_event in raw_events:
        try:
            processed_event = process_raw_event(raw_event)
            processed_events.append(processed_event)
        except Exception as e:
            print(f"Failed to process event '{raw_event.get('title', 'unknown')}': {e}")
            continue

    return processed_events


def deduplicate_events_globally(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate events based on title similarity and URL.

    Args:
        events: List of event dictionaries

    Returns:
        Deduplicated list of events
    """
    if not events:
        return []

    # Sort by date (newest first) to prefer more recent entries
    events_sorted = sorted(events, key=lambda x: x.get("collected_at", ""), reverse=True)

    seen_titles = set()
    seen_urls = set()
    deduplicated = []

    for event in events_sorted:
        title = event.get("title", "").lower().strip()
        url = event.get("url", "").lower().strip()

        # Skip if we've seen this exact URL
        if url and url in seen_urls:
            continue

        # Skip if title is very similar (basic similarity check)
        title_words = set(title.split())
        is_duplicate = False

        for seen_title in seen_titles:
            seen_words = set(seen_title.split())
            # If 80% of words overlap, consider it a duplicate
            if len(title_words & seen_words) / max(len(title_words), len(seen_words)) > 0.8:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_titles.add(title)
            if url:
                seen_urls.add(url)
            deduplicated.append(event)

    return deduplicated


def deduplicate_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate events within the same category.

    Args:
        events: List of events to deduplicate

    Returns:
        Deduplicated list
    """
    return deduplicate_events_globally(events)


def filter_future_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter events to only include future events.

    Args:
        events: List of event dictionaries

    Returns:
        List of future events only
    """
    future_events = []
    today = datetime.date.today()

    for event in events:
        event_date_str = event.get("date")
        if event_date_str:
            try:
                event_date = datetime.date.fromisoformat(event_date_str)
                if event_date >= today:
                    future_events.append(event)
            except (ValueError, TypeError):
                # If date parsing fails, include the event anyway
                future_events.append(event)
        else:
            # If no date, include the event
            future_events.append(event)

    return future_events
