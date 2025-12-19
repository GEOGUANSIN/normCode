"""NormCode Canvas API - FastAPI Application with layout mode support."""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Add project root to path for infra imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add backend directory to path for local imports
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from routers import repository_router, graph_router, execution_router, websocket_router, project_router, editor_router
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NormCode Canvas API",
    version="0.1.0",
    description="Backend for NormCode Graph Canvas Tool - visualize, execute, and debug NormCode plans",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    repository_router.router, 
    prefix="/api/repositories", 
    tags=["repositories"]
)
app.include_router(
    graph_router.router, 
    prefix="/api/graph", 
    tags=["graph"]
)
app.include_router(
    execution_router.router, 
    prefix="/api/execution", 
    tags=["execution"]
)
app.include_router(
    websocket_router.router, 
    prefix="/ws", 
    tags=["websocket"]
)
app.include_router(
    project_router.router,
    prefix="/api/project",
    tags=["project"]
)
app.include_router(
    editor_router.router,
    prefix="/api/editor",
    tags=["editor"]
)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "NormCode Canvas API",
        "version": "0.1.0",
        "docs": "/docs",
        "websocket": "/ws/events",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
