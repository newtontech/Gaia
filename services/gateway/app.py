"""FastAPI application factory for Gaia."""

from __future__ import annotations

from fastapi import FastAPI

from .deps import deps, Dependencies


def create_app(dependencies: Dependencies | None = None) -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(title="Gaia", version="0.1.0", description="Large Knowledge Model API")

    active_deps = dependencies or deps

    @app.on_event("startup")
    async def startup():
        if active_deps.storage is None:
            active_deps.initialize()

    @app.on_event("shutdown")
    async def shutdown():
        await active_deps.cleanup()

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    # Routes will be added in Tasks 23-24
    # from .routes import commits, read, search
    # app.include_router(commits.router)
    # app.include_router(read.router)
    # app.include_router(search.router)

    return app
