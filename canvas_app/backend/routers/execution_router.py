"""Execution control endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services.execution_service import execution_controller
from schemas.execution_schemas import ExecutionState, BreakpointRequest, LogsResponse, LogEntry

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


@router.post("/breakpoints", response_model=CommandResponse)
async def set_breakpoint(request: BreakpointRequest):
    """Set or clear a breakpoint."""
    try:
        if request.enabled:
            execution_controller.set_breakpoint(request.flow_index)
            return CommandResponse(success=True, message=f"Breakpoint set at {request.flow_index}")
        else:
            execution_controller.clear_breakpoint(request.flow_index)
            return CommandResponse(success=True, message=f"Breakpoint cleared at {request.flow_index}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/breakpoints/{flow_index}", response_model=CommandResponse)
async def clear_breakpoint(flow_index: str):
    """Clear a breakpoint."""
    try:
        execution_controller.clear_breakpoint(flow_index)
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
