"""Checkpoint management router for resume/fork functionality."""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class RunInfo(BaseModel):
    """Information about a stored run."""
    run_id: str
    first_execution: Optional[str] = None
    last_execution: Optional[str] = None
    execution_count: int = 0
    max_cycle: int = 0
    config: Optional[dict] = None


class CheckpointInfo(BaseModel):
    """Information about a checkpoint."""
    cycle: int
    inference_count: int
    timestamp: str


class ResumeRequest(BaseModel):
    """Request to resume from checkpoint."""
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None
    db_path: str
    run_id: str
    cycle: Optional[int] = None  # None = latest checkpoint
    mode: str = "PATCH"  # PATCH | OVERWRITE | FILL_GAPS
    llm_model: str = "demo"
    base_dir: Optional[str] = None
    max_cycles: int = 50
    paradigm_dir: Optional[str] = None


class ForkRequest(BaseModel):
    """Request to fork from checkpoint."""
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None
    db_path: str
    source_run_id: str
    new_run_id: Optional[str] = None  # Auto-generate if None
    cycle: Optional[int] = None
    mode: str = "PATCH"
    llm_model: str = "demo"
    base_dir: Optional[str] = None
    max_cycles: int = 50
    paradigm_dir: Optional[str] = None


class LoadResult(BaseModel):
    """Result of loading from checkpoint."""
    success: bool
    run_id: str
    mode: str  # "resume" or "fork"
    forked_from: Optional[str] = None
    completed_count: int
    total_count: int
    message: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/runs", response_model=List[RunInfo])
async def list_runs(db_path: str = Query(..., description="Path to orchestration.db")):
    """List all runs in the checkpoint database."""
    from services.execution_service import execution_controller
    
    # Validate db_path exists
    if not os.path.exists(db_path):
        return []  # No database = no runs
    
    try:
        runs = await execution_controller.list_runs(db_path)
        return [RunInfo(**r) for r in runs]
    except Exception as e:
        logger.error(f"Failed to list runs from {db_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/checkpoints", response_model=List[CheckpointInfo])
async def list_checkpoints(
    run_id: str,
    db_path: str = Query(..., description="Path to orchestration.db")
):
    """List all checkpoints for a specific run."""
    from services.execution_service import execution_controller
    
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    try:
        checkpoints = await execution_controller.list_checkpoints(db_path, run_id)
        return [CheckpointInfo(**c) for c in checkpoints]
    except Exception as e:
        logger.error(f"Failed to list checkpoints for {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/metadata")
async def get_run_metadata(
    run_id: str,
    db_path: str = Query(..., description="Path to orchestration.db")
):
    """Get metadata for a specific run."""
    from services.execution_service import execution_controller
    
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    try:
        metadata = await execution_controller.get_run_metadata(db_path, run_id)
        return metadata or {}
    except Exception as e:
        logger.error(f"Failed to get metadata for {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", response_model=LoadResult)
async def resume_execution(request: ResumeRequest):
    """Resume execution from a checkpoint (same run_id)."""
    from services.execution_service import execution_controller
    
    if not os.path.exists(request.db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    try:
        result = await execution_controller.resume_from_checkpoint(
            concepts_path=request.concepts_path,
            inferences_path=request.inferences_path,
            inputs_path=request.inputs_path,
            db_path=request.db_path,
            run_id=request.run_id,
            cycle=request.cycle,
            mode=request.mode,
            llm_model=request.llm_model,
            base_dir=request.base_dir,
            max_cycles=request.max_cycles,
            paradigm_dir=request.paradigm_dir,
        )
        return LoadResult(**result)
    except Exception as e:
        logger.exception(f"Failed to resume from checkpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fork", response_model=LoadResult)
async def fork_execution(request: ForkRequest):
    """Fork from a checkpoint with a new run_id."""
    from services.execution_service import execution_controller
    
    if not os.path.exists(request.db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    try:
        result = await execution_controller.fork_from_checkpoint(
            concepts_path=request.concepts_path,
            inferences_path=request.inferences_path,
            inputs_path=request.inputs_path,
            db_path=request.db_path,
            source_run_id=request.source_run_id,
            new_run_id=request.new_run_id,
            cycle=request.cycle,
            mode=request.mode,
            llm_model=request.llm_model,
            base_dir=request.base_dir,
            max_cycles=request.max_cycles,
            paradigm_dir=request.paradigm_dir,
        )
        return LoadResult(**result)
    except Exception as e:
        logger.exception(f"Failed to fork from checkpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db-exists")
async def check_db_exists(db_path: str = Query(..., description="Path to orchestration.db")):
    """Check if the checkpoint database exists."""
    return {"exists": os.path.exists(db_path), "path": db_path}


@router.delete("/runs/{run_id}")
async def delete_run(
    run_id: str,
    db_path: str = Query(..., description="Path to orchestration.db")
):
    """Delete a run and all its checkpoints from the database."""
    from services.execution_service import execution_controller
    
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    try:
        result = await execution_controller.delete_run(db_path, run_id)
        return result
    except Exception as e:
        logger.exception(f"Failed to delete run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
