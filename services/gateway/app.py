"""FastAPI application factory for Gaia."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .deps import deps, Dependencies
from .routes.commits import router as commits_router
from .routes.read import router as read_router
from .routes.search import router as search_router
from .routes.jobs import router as jobs_router


def custom_openapi(app: FastAPI):
    """Generate custom OpenAPI schema with additional metadata."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add servers
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Local development server"},
    ]
    
    # Add API version info
    openapi_schema["info"]["version"] = "3.0.0"
    openapi_schema["info"]["contact"] = {
        "name": "Gaia API Support",
        "url": "https://github.com/SiliconEinstein/Gaia/issues",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_app(dependencies: Dependencies | None = None) -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Gaia API",
        version="3.0.0",
        description="""
# Gaia API — Large Knowledge Model

Gaia is a Large Knowledge Model (LKM) system that stores and reasons about scientific knowledge
using a hypergraph structure. All knowledge is represented as hyperedges connecting propositions.

## Key Concepts

- **Nodes**: Propositions or statements (e.g., "YH10 superconducts at 400GPa")
- **HyperEdges**: Relationships between propositions (e.g., paper extraction, deduction, contradiction)
- **Commits**: Git-like operations for submitting changes to the knowledge graph
- **Review Pipeline**: Multi-step AI-powered validation of new knowledge

## API Layers

### Layer 1: Knowledge Graph API (This Document)
- Commits and merge workflow
- Node and edge CRUD operations
- Search and retrieval
- Job management

### Layer 2: Research API (Future)
- Novelty scoring
- Reliability assessment
- Contradiction detection
- Provenance tracking

## Quick Start

1. Submit a commit: `POST /commits`
2. Review the commit: `POST /commits/{id}/review`
3. Merge if approved: `POST /commits/{id}/merge`
4. Search knowledge: `POST /search/nodes`

## Status Codes

| Code | Meaning |
|------|---------|
| 200  | Success |
| 400  | Bad Request - validation error |
| 404  | Not Found |
| 409  | Conflict - invalid state transition |
| 503  | Service Unavailable - graph store down |
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Set custom OpenAPI schema generator
    app.openapi = lambda: custom_openapi(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    active_deps = dependencies or deps

    # When custom dependencies are injected (e.g. in tests), propagate
    # them to the module-level singleton so route handlers can use them.
    if dependencies is not None:
        deps.storage = dependencies.storage
        deps.search_engine = dependencies.search_engine
        deps.commit_engine = dependencies.commit_engine
        deps.inference_engine = dependencies.inference_engine
        deps.job_manager = dependencies.job_manager

    @app.on_event("startup")
    async def startup():
        if active_deps.storage is None:
            active_deps.initialize()

    @app.on_event("shutdown")
    async def shutdown():
        await active_deps.cleanup()

    @app.get(
        "/health",
        summary="Health check",
        description="Check API health and get version information.",
        response_model=dict,
        responses={
            200: {
                "description": "API is healthy",
                "content": {
                    "application/json": {
                        "example": {"status": "ok", "version": "3.0.0"}
                    }
                }
            }
        },
        tags=["system"]
    )
    async def health():
        """
        Health check endpoint.
        
        Returns API status and version information.
        Use this to verify the API is running and accessible.
        """
        return {"status": "ok", "version": "3.0.0"}

    app.include_router(commits_router)
    app.include_router(read_router)
    app.include_router(search_router)
    app.include_router(jobs_router)

    return app
