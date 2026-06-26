"""FastAPI server for SQUAD."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from .routes import streaming, settings, files, static


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Mounts all route routers (streaming, settings, files, static, ...) and
    applies CORS middleware. Additional routers (git, llm, infra, agent, deploy)
    are wired up progressively.
    """
    app = FastAPI(
        title="SQUAD API",
        description="SQUAD - Software Engineering Autonomous Development API",
        version="7.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount route routers
    app.include_router(streaming.router)
    app.include_router(settings.router)
    app.include_router(files.router)
    app.include_router(static.router)

    @app.get("/health")
    async def health_check() -> Dict[str, str]:
        return {"status": "healthy"}

    return app
