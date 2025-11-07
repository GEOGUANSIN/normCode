from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import graph_router
from schemas.config import settings

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="NormCode Flow Graph API",
        description="API for managing flow graph nodes and edges",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allow_methods,
        allow_headers=settings.allow_headers,
        expose_headers=settings.expose_headers,
    )
    
    # Include routers
    app.include_router(graph_router.router)
    
    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.host, 
        port=settings.port
    ) 