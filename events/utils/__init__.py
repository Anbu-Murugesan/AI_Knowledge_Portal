"""
Utility functions for event processing
"""
import datetime
import re
from dateutil.parser import parse as parse_date, ParserError
from dateutil.tz import tzlocal
from typing import List


def parse_date_candidates(text: str) -> List[datetime.date]:
    """
    Extract all possible date candidates from text.

    Args:
        text: Text to parse for dates

    Returns:
        List of date objects found in the text
    """
    if not text:
        return []

    # Common date patterns
    date_patterns = [
        # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
        r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b',
        # YYYY/MM/DD, YYYY-MM-DD, YYYY.MM.DD
        r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b',
        # Month DD, YYYY (e.g., "January 15, 2024")
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b',
        # DD Month YYYY (e.g., "15 January 2024")
        r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b',
        # Month YYYY (e.g., "January 2024")
        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b',
    ]

    dates_found = []

    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                if len(match) == 3:  # DD/MM/YYYY or YYYY/MM/DD patterns
                    # Try different interpretations
                    for order in [(0,1,2), (2,1,0)]:  # DD/MM/YYYY or YYYY/MM/DD
                        try:
                            day, month, year = [int(match[i]) for i in order]
                            if 1 <= day <= 31 and 1 <= month <= 12 and 2000 <= year <= 2030:
                                date_obj = datetime.date(year, month, day)
                                dates_found.append(date_obj)
                                break
                        except (ValueError, IndexError):
                            continue
                elif len(match) == 3 and isinstance(match[0], str):  # Month DD, YYYY
                    month_str, day_str, year_str = match
                    try:
                        month_names = {
                            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
                        }
                        month = month_names[month_str.lower()]
                        day = int(day_str)
                        year = int(year_str)
                        date_obj = datetime.date(year, month, day)
                        dates_found.append(date_obj)
                    except (ValueError, KeyError):
                        continue
            except Exception:
                continue

    # Remove duplicates and sort
    unique_dates = list(set(dates_found))
    unique_dates.sort()

    return unique_dates


def detect_location(text: str) -> str:
    """
    Detect location from event text.

    Args:
        text: Text to analyze for location

    Returns:
        Location string or "Online" if detected as virtual
    """
    if not text:
        return "TBD"

    text_lower = text.lower()

    # Check for online/virtual indicators first
    online_keywords = [
        "online", "virtual", "remote", "webinar", "zoom", "google meet",
        "microsoft teams", "skype", "discord", "slack", "hybrid"
    ]

    for keyword in online_keywords:
        if keyword in text_lower:
            return "Online"

    # Indian cities (prioritized)
    indian_cities = {
        "mumbai": "Mumbai", "delhi": "Delhi", "bangalore": "Bangalore", "bengaluru": "Bangalore",
        "chennai": "Chennai", "hyderabad": "Hyderabad", "pune": "Pune", "kolkata": "Kolkata",
        "ahmedabad": "Ahmedabad", "jaipur": "Jaipur", "surat": "Surat", "lucknow": "Lucknow",
        "kanpur": "Kanpur", "nagpur": "Nagpur", "indore": "Indore", "thane": "Thane",
        "bhopal": "Bhopal", "visakhapatnam": "Visakhapatnam", "pimpri": "Pune", "vadodara": "Vadodara",
        "ghaziabad": "Ghaziabad", "ludhiana": "Ludhiana", "agra": "Agra", "nashik": "Nashik",
        "meerut": "Meerut", "rajkot": "Rajkot", "varanasi": "Varanasi", "srinagar": "Srinagar",
        "aurangabad": "Aurangabad", "dhanbad": "Dhanbad", "amritsar": "Amritsar", "allahabad": "Prayagraj"
    }

    for city_key, city_name in indian_cities.items():
        if city_key in text_lower:
            return city_name

    # If no specific location found, return TBD
    return "TBD"


def detect_event_type(text: str) -> str:
    """
    Detect event type from title and content.

    Args:
        text: Text to analyze for event type

    Returns:
        Event type: "hackathon", "conference", or "workshop"
    """
    if not text:
        return "conference"  # default

    text_lower = text.lower()

    # Strong indicators for hackathons
    hackathon_keywords = [
        "hackathon", "hack", "kaggle", "hacker", "coding challenge",
        "data science competition", "ml competition", "ai competition"
    ]

    # Strong indicators for workshops
    workshop_keywords = [
        "workshop", "tutorial", "bootcamp", "training", "hands-on",
        "practical session", "lab session"
    ]

    # Conference indicators (broader)
    conference_keywords = [
        "conference", "summit", "symposium", "conclave", "forum",
        "meetup", "seminar", "webinar", "talk", "presentation"
    ]

    # Check for hackathon indicators first (most specific)
    for keyword in hackathon_keywords:
        if keyword in text_lower:
            return "hackathon"

    # Check for workshop indicators
    for keyword in workshop_keywords:
        if keyword in text_lower:
            return "workshop"

    # Default to conference for anything else
    for keyword in conference_keywords:
        if keyword in text_lower:
            return "conference"

    return "conference"  # fallback
