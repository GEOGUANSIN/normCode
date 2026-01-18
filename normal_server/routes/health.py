"""
Health and Info Endpoints
"""

from datetime import datetime
from fastapi import APIRouter

from service import get_config, get_available_llm_models, SETTINGS_PATH, discover_plans, active_runs

router = APIRouter()


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.get("/info")
async def info():
    """Server information."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    llm_models = get_available_llm_models()
    
    # Count only actually running/pending runs as "active"
    running_count = sum(1 for r in active_runs.values() if r.status in ('running', 'pending'))
    completed_count = sum(1 for r in active_runs.values() if r.status == 'completed')
    
    return {
        "version": "0.1.0",
        "plans_count": len(plans),
        "active_runs": running_count,
        "completed_runs": completed_count,
        "total_runs": len(active_runs),
        "plans_dir": str(cfg.plans_dir),
        "runs_dir": str(cfg.runs_dir),
        "llm_models": llm_models,
        "settings_path": str(SETTINGS_PATH) if SETTINGS_PATH and SETTINGS_PATH.exists() else None
    }


@router.get("/api/models")
async def list_models():
    """List available LLM models."""
    return get_available_llm_models()


@router.get("/api/connect")
async def connection_info():
    """
    Connection info endpoint for RemoteProxyExecutor.
    
    The canvas_app's RemoteProxyExecutor calls this to verify connectivity
    and get server capabilities before establishing a long-lived SSE connection.
    
    Returns:
        Server capabilities, version, and status information needed for
        establishing a remote execution session.
    """
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    running_count = sum(1 for r in active_runs.values() if r.status in ('running', 'pending'))
    paused_count = sum(1 for r in active_runs.values() if r.status == 'paused')
    
    return {
        "status": "ready",
        "version": "0.1.0",
        "capabilities": {
            "sse_streaming": True,
            "websocket": True,
            "breakpoints": True,
            "step_execution": True,
            "pause_resume": True,
            "value_override": True,
            "run_to": True,
            "checkpoints": True,
            "db_inspector": True,
        },
        "plans_count": len(plans),
        "active_runs": running_count,
        "paused_runs": paused_count,
        "endpoints": {
            "runs": "/api/runs",
            "plans": "/api/plans",
            "stream": "/api/runs/{run_id}/stream",
            "websocket": "/ws/runs/{run_id}",
        },
    }


@router.get("/api/plans/{plan_id}/manifest")
async def get_plan_manifest(plan_id: str):
    """
    Get the project manifest for a plan.
    
    This is used by canvas_app to open a remote plan as a proper project tab.
    The manifest contains all the metadata needed to integrate the remote
    project into the canvas_app's unified tab system.
    
    Returns:
        Project manifest with name, description, paths, and graph metadata.
    """
    from fastapi import HTTPException
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    
    # Count nodes for metadata
    try:
        from service import load_plan_graph
        graph = load_plan_graph(plan_config)
        node_count = len(graph.get("nodes", []))
        edge_count = len(graph.get("edges", []))
    except Exception:
        node_count = 0
        edge_count = 0
    
    return {
        "plan_id": plan_id,
        "name": plan_config.name,
        "description": plan_config.description,
        "is_remote": True,
        "read_only": True,  # Remote projects are read-only in canvas
        "graph_metadata": {
            "node_count": node_count,
            "edge_count": edge_count,
        },
        "llm_model": plan_config.llm_model,
        "max_cycles": plan_config.max_cycles,
    }
