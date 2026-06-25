"""FastAPI server for SQUAD."""

from fastapi import FastAPI
from typing import Dict, Any


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="SQUAD API",
        description="SQUAD - Software Engineering Autonomous Development API",
        version="5.0.0"
    )
    
    @app.get("/")
    async def root() -> Dict[str, str]:
        return {"message": "Welcome to SQUAD API"}
    
    @app.get("/health")
    async def health_check() -> Dict[str, str]:
        return {"status": "healthy"}
    
    return app
