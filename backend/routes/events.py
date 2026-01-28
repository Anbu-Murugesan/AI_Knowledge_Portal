"""
Events API routes (hackathons, conferences, workshops).

These routes wrap the existing event functionality
without modifying any core logic.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.models import EventsResponse
from events.hackathons import get_events as get_hackathons
from events.conferences import get_events as get_conferences
from events.workshops import get_events as get_workshops

router = APIRouter()


@router.get("/hackathons", response_model=EventsResponse)
async def get_hackathons_events() -> EventsResponse:
    """
    Get hackathon events.

    This endpoint wraps the existing get_events function from hackathons.py
    with identical parameters and return values.
    """
    try:
        # Call existing function
        events = get_hackathons()
        return EventsResponse(events=events)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve hackathons: {str(e)}"
        )


@router.get("/conferences", response_model=EventsResponse)
async def get_conferences_events() -> EventsResponse:
    """
    Get conference events.

    This endpoint wraps the existing get_events function from conferences.py
    with identical parameters and return values.
    """
    try:
        # Call existing function
        events = get_conferences()
        return EventsResponse(events=events)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conferences: {str(e)}"
        )


@router.get("/workshops", response_model=EventsResponse)
async def get_workshops_events() -> EventsResponse:
    """
    Get workshop events.

    This endpoint wraps the existing get_events function from workshops.py
    with identical parameters and return values.
    """
    try:
        # Call existing function
        events = get_workshops()
        return EventsResponse(events=events)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve workshops: {str(e)}"
        )
