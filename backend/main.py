"""
FastAPI backend application.

This backend wraps existing logic without modifying core functionality.
All routes call existing functions with identical parameters and return values.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.research import router as research_router
from backend.routes.blog import router as blog_router
from backend.routes.events import router as events_router

# Create FastAPI app
app = FastAPI(
    title="AI Knowledge Portal Backend",
    description="FastAPI backend that wraps existing AI Knowledge Portal logic",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    research_router,
    prefix="/api/research",
    tags=["research"]
)

app.include_router(
    blog_router,
    prefix="/api/blog",
    tags=["News and Blog"]
)

app.include_router(
    events_router,
    prefix="/api/events",
    tags=["events"]
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Knowledge Portal Backend API",
        "version": "1.0.0",
        "endpoints": {
            "research": "/api/research",
            "blog": "/api/blog",
            "events": "/api/events"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
