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

