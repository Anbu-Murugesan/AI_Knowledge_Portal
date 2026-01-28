"""
Research papers API routes.

These routes wrap the existing research paper functionality
without modifying any core logic.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from backend.models import ResearchPapersRequest, ResearchPapersResponse, ErrorResponse
from research.retrievers import get_research_papers

router = APIRouter()


@router.post("/papers", response_model=ResearchPapersResponse)
async def get_papers(request: ResearchPapersRequest) -> ResearchPapersResponse:
    """
    Get research papers from arXiv.

    This endpoint wraps the existing get_research_papers function
    with identical parameters and return values.
    """
    try:
        # Call existing function with exact same parameters
        papers = get_research_papers(
            query=request.query,
            mode=request.mode,
            load_max_docs=request.load_max_docs,
            top_k=request.top_k
        )

        return ResearchPapersResponse(papers=papers)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve research papers: {str(e)}"
        )


