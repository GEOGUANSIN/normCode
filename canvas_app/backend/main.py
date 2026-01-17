"""NormCode Canvas API - FastAPI Application with layout mode support."""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging

# Add project root to path for infra imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Add backend directory to path for local imports
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Detect frontend dist directory (for production/packaged mode)
# Check multiple possible locations
_frontend_dist = None
possible_frontend_paths = [
    backend_dir.parent / "frontend" / "dist",  # Development: canvas_app/frontend/dist
    backend_dir.parent / "dist",  # Alternative layout
    Path(sys.executable).parent / "frontend" / "dist",  # PyInstaller bundled
    Path(sys.executable).parent / "_internal" / "frontend" / "dist",  # PyInstaller _internal
]
for fp in possible_frontend_paths:
    if fp.exists() and (fp / "index.html").exists():
        _frontend_dist = fp
        break

from routers import repository_router, graph_router, execution_router, websocket_router, project_router, editor_router, checkpoint_router, agent_router, llm_router, chat_router, db_inspector_router, deployment_router, portable_router
from core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress DEBUG logs from infra module (set to INFO to reduce noise)
# These are only useful during development/debugging of the infra layer itself
for infra_logger_name in ['infra', 'infra._core', 'infra._agent', 'infra._orchest', 'infra._loggers']:
    logging.getLogger(infra_logger_name).setLevel(logging.INFO)

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
app.include_router(
    checkpoint_router.router,
    prefix="/api/checkpoints",
    tags=["checkpoints"]
)
app.include_router(
    agent_router.router,
    tags=["agents"]
)
app.include_router(
    llm_router.router,
    tags=["llm"]
)
app.include_router(
    chat_router.router,
    tags=["chat"]
)

# Include DB inspector router
app.include_router(
    db_inspector_router.router,
    prefix="/api/db-inspector",
    tags=["db-inspector"]
)

# Include deployment router
app.include_router(
    deployment_router.router,
    prefix="/api/deployment",
    tags=["deployment"]
)

# Include portable project router
app.include_router(
    portable_router.router,
    prefix="/api/portable",
    tags=["portable"]
)

# Mount frontend static files if available (production mode)
if _frontend_dist:
    # Mount assets directory for JS, CSS, etc.
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")
    logger.info(f"Serving frontend from: {_frontend_dist}")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint - serve frontend or API info."""
    # In production mode with frontend dist, serve index.html
    if _frontend_dist:
        return FileResponse(_frontend_dist / "index.html")
    
    # In development mode, return API info
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


# Catch-all route for SPA client-side routing (must be after all API routes)
@app.get("/{full_path:path}", tags=["frontend"])
async def serve_spa(full_path: str):
    """Serve index.html for all unmatched routes (SPA client-side routing)."""
    if _frontend_dist:
        # Check if it's a static file request
        file_path = _frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise return index.html for client-side routing
        return FileResponse(_frontend_dist / "index.html")
    
    # In development mode, return 404 for non-API routes
    return {"error": "Not found", "path": full_path}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
