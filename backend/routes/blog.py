"""
Blog/RSS search API routes.

These routes wrap the existing blog/RSS functionality
without modifying any core logic.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.models import BlogSearchRequest, BlogSearchResponse
from core.workflows import run_full_workflow_example

router = APIRouter()


@router.post("/search", response_model=BlogSearchResponse)
async def search_blog_rss(request: BlogSearchRequest) -> BlogSearchResponse:
    """
    Search blog/RSS content.

    This endpoint wraps the existing run_full_workflow_example function
    with identical parameters and return values.
    """
    try:
        # Call existing function with exact same parameters
        result = run_full_workflow_example(
            query=request.query,
            selected_tool=request.selected_tool,
            selected_blog=request.selected_blog,
            build_if_missing=request.build_if_missing
        )

        return BlogSearchResponse(result=result.__dict__ if hasattr(result, '__dict__') else result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search blog/RSS content: {str(e)}"
        )


