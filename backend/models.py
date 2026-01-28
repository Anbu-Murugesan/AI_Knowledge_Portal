"""
Pydantic models for API request/response schemas.

These models define the exact structure of data exchanged between
frontend and backend, matching existing function signatures.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


# Research Papers API Models
class ResearchPapersRequest(BaseModel):
    """Request model for research papers API."""
    query: str
    mode: str = "topic"
    load_max_docs: int = 8
    top_k: int = 10


class ResearchPapersResponse(BaseModel):
    """Response model for research papers API."""
    papers: List[Dict[str, Any]]


# Blog/RSS API Models
class BlogSearchRequest(BaseModel):
    """Request model for blog/RSS search API."""
    query: str
    selected_tool: str = "rss"
    selected_blog: Optional[str] = None
    build_if_missing: bool = False


class BlogSearchResponse(BaseModel):
    """Response model for blog/RSS search API."""
    result: Dict[str, Any]


# Events API Models (Hackathons, Conferences, Workshops)
class EventsResponse(BaseModel):
    """Response model for events API."""
    events: List[Dict[str, Any]]


# Error Response Model
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    details: Optional[str] = None
