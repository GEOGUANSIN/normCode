"""Execution control endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services.execution_service import execution_controller
from services.project_service import project_service
from schemas.execution_schemas import (
    ExecutionState, BreakpointRequest, LogsResponse, LogEntry,
    ExecutionConfig, LLM_MODELS, DEFAULT_MAX_CYCLES, DEFAULT_DB_PATH
)

router = APIRouter()


class CommandResponse(BaseModel):
    """Response for execution commands."""
    success: bool
    message: str


@router.get("/state", response_model=ExecutionState)
async def get_execution_state():
    """Get current execution state."""
    state = execution_controller.get_state()
    return ExecutionState(**state)


@router.post("/start", response_model=CommandResponse)
async def start_execution():
    """Start or resume plan execution."""
    try:
        await execution_controller.start()
        return CommandResponse(success=True, message="Execution started")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause", response_model=CommandResponse)
async def pause_execution():
    """Pause execution after current inference."""
    try:
        await execution_controller.pause()
        return CommandResponse(success=True, message="Execution paused")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", response_model=CommandResponse)
async def resume_execution():
    """Resume from paused state."""
    try:
        await execution_controller.resume()
        return CommandResponse(success=True, message="Execution resumed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step", response_model=CommandResponse)
async def step_execution():
    """Execute single inference then pause."""
    try:
        await execution_controller.step()
        return CommandResponse(success=True, message="Stepping to next inference")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=CommandResponse)
async def stop_execution():
    """Stop execution."""
    try:
        await execution_controller.stop()
        return CommandResponse(success=True, message="Execution stopped")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart", response_model=CommandResponse)
async def restart_execution():
    """Restart execution from the beginning.
    
    Resets all node statuses and allows re-running the plan.
    """
    try:
        await execution_controller.restart()
        return CommandResponse(success=True, message="Execution reset - ready to run")
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-to/{flow_index}", response_model=CommandResponse)
async def run_to_node(flow_index: str):
    """Run execution until a specific node is reached, then pause.
    
    This runs the execution from the current state until the specified
    flow_index is executed, then automatically pauses. Useful for
    debugging - run to a specific point and inspect the state.
    
    Args:
        flow_index: The flow_index of the node to run to
    """
    try:
        await execution_controller.run_to(flow_index)
        return CommandResponse(success=True, message=f"Running to {flow_index}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/breakpoints", response_model=CommandResponse)
async def set_breakpoint(request: BreakpointRequest):
    """Set or clear a breakpoint."""
    try:
        if request.enabled:
            execution_controller.set_breakpoint(request.flow_index)
        else:
            execution_controller.clear_breakpoint(request.flow_index)
        
        # Sync breakpoints to project if one is open
        if project_service.is_project_open:
            project_service.save_project(breakpoints=list(execution_controller.breakpoints))
        
        if request.enabled:
            return CommandResponse(success=True, message=f"Breakpoint set at {request.flow_index}")
        else:
            return CommandResponse(success=True, message=f"Breakpoint cleared at {request.flow_index}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/breakpoints/{flow_index}", response_model=CommandResponse)
async def clear_breakpoint(flow_index: str):
    """Clear a breakpoint."""
    try:
        execution_controller.clear_breakpoint(flow_index)
        
        # Sync breakpoints to project if one is open
        if project_service.is_project_open:
            project_service.save_project(breakpoints=list(execution_controller.breakpoints))
        
        return CommandResponse(success=True, message=f"Breakpoint cleared at {flow_index}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breakpoints")
async def list_breakpoints():
    """List all breakpoints."""
    return {"breakpoints": list(execution_controller.breakpoints)}


@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    flow_index: Optional[str] = Query(default=None)
):
    """Get execution logs, optionally filtered by flow_index."""
    logs = execution_controller.get_logs(limit=limit, flow_index=flow_index)
    return LogsResponse(
        logs=[LogEntry(**log) for log in logs],
        total_count=len(execution_controller.logs)
    )


@router.get("/config", response_model=ExecutionConfig)
async def get_config():
    """Get execution configuration options and defaults.
    
    Returns available LLM models, default values, and current config if loaded.
    """
    return ExecutionConfig(
        available_models=LLM_MODELS,
        default_max_cycles=DEFAULT_MAX_CYCLES,
        default_db_path=DEFAULT_DB_PATH,
    )


@router.get("/reference/{concept_name}")
async def get_reference_data(concept_name: str):
    """Get reference data for a concept.
    
    Returns the current tensor data for a concept including:
    - data: The tensor data
    - axes: Axis names
    - shape: Tensor shape
    
    Returns empty response if concept not found or has no reference.
    """
    ref_data = execution_controller.get_reference_data(concept_name)
    if ref_data is None:
        # Return empty response instead of 404 to avoid console noise
        return {
            "concept_name": concept_name,
            "has_reference": False,
            "data": None,
            "axes": [],
            "shape": []
        }
    return ref_data


@router.get("/references")
async def get_all_references():
    """Get reference data for all concepts that have references.
    
    Returns a dict mapping concept_name -> reference_data.
    Useful for batch fetching all computed values.
    """
    return execution_controller.get_all_reference_data()
