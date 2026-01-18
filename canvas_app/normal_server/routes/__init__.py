"""
API Routes Package

Modular route definitions for the NormCode server.
"""


def include_all_routes(app):
    """Include all route modules in the app."""
    # Import here to avoid circular imports and support both package and direct run
    from routes.health import router as health_router
    from routes.plans import router as plans_router
    from routes.runs import router as runs_router
    from routes.db_inspector import router as db_inspector_router
    from routes.streaming import router as streaming_router
    
    app.include_router(health_router)
    app.include_router(plans_router, prefix="/api/plans", tags=["plans"])
    app.include_router(runs_router, prefix="/api/runs", tags=["runs"])
    app.include_router(db_inspector_router, tags=["db-inspector"])
    app.include_router(streaming_router, tags=["streaming"])

