"""Execution control endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Any, List

from services.execution_service import execution_controller, execution_controller_registry, get_execution_controller
from services.project_service import project_service
from schemas.execution_schemas import (
    ExecutionState, BreakpointRequest, LogsResponse, LogEntry,
    ExecutionConfig, LLM_MODELS, DEFAULT_MAX_CYCLES, DEFAULT_DB_PATH,
    SEQUENCE_STEPS, STEP_FULL_NAMES
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
    
    Returns available LLM models (from both settings.yaml and LLM settings service),
    default values, and current config if loaded.
    """
    # Start with models from settings.yaml
    all_models = list(LLM_MODELS)
    
    # Add models from LLM settings service
    try:
        from services.llm_settings_service import llm_settings_service
        provider_names = llm_settings_service.get_available_models()
        for name in provider_names:
            if name not in all_models:
                all_models.append(name)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not get LLM providers: {e}")
    
    return ExecutionConfig(
        available_models=all_models,
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


class VerboseLoggingRequest(BaseModel):
    """Request to toggle verbose logging."""
    enabled: bool


@router.post("/verbose-logging", response_model=CommandResponse)
async def set_verbose_logging(request: VerboseLoggingRequest):
    """Enable or disable verbose (DEBUG level) logging.
    
    When enabled, captures detailed step-level logs from the orchestrator
    including step completions, state transitions, and debugging info.
    """
    try:
        execution_controller.set_verbose_logging(request.enabled)
        return CommandResponse(
            success=True, 
            message=f"Verbose logging {'enabled' if request.enabled else 'disabled'}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/step-progress")
async def get_step_progress(flow_index: Optional[str] = Query(default=None)):
    """Get step progress for a specific inference or current inference.
    
    Returns the current step progress including:
    - sequence_type: The type of sequence being executed
    - current_step: The current step abbreviation (e.g., "TVA")
    - current_step_index: 0-based index of current step
    - total_steps: Total steps in the sequence
    - steps: List of all step abbreviations
    - completed_steps: List of completed step abbreviations
    """
    progress = execution_controller.get_step_progress(flow_index)
    if not progress:
        return {
            "flow_index": flow_index or execution_controller.current_inference,
            "sequence_type": None,
            "current_step": None,
            "current_step_index": 0,
            "total_steps": 0,
            "steps": [],
            "completed_steps": [],
        }
    return progress


# =============================================================================
# Phase 4: Modification & Re-run Endpoints
# =============================================================================

class ValueOverrideRequest(BaseModel):
    """Request to override a concept's value."""
    new_value: Any
    rerun_dependents: bool = False


class ValueOverrideResponse(BaseModel):
    """Response for value override."""
    success: bool
    overridden: str
    stale_nodes: list


@router.post("/override/{concept_name}", response_model=ValueOverrideResponse)
async def override_value(concept_name: str, request: ValueOverrideRequest):
    """Override a concept's reference value.
    
    This allows injecting or modifying values at any ground or computed node.
    Optionally triggers re-execution of dependent nodes.
    
    Args:
        concept_name: The name of the concept to override
        request.new_value: The new value to set
        request.rerun_dependents: If True, mark dependents as stale and start execution
    """
    try:
        result = await execution_controller.override_value(
            concept_name=concept_name,
            new_value=request.new_value,
            rerun_dependents=request.rerun_dependents
        )
        return ValueOverrideResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RerunFromResponse(BaseModel):
    """Response for re-run from node."""
    success: bool
    from_flow_index: str
    reset_count: int
    reset_nodes: list


@router.post("/rerun-from/{flow_index}", response_model=RerunFromResponse)
async def rerun_from_node(flow_index: str):
    """Reset and re-execute from a specific node.
    
    This resets the target node and all its descendants, then starts
    execution from the beginning.
    
    Args:
        flow_index: The flow_index to re-run from
    """
    try:
        result = await execution_controller.rerun_from(flow_index)
        return RerunFromResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FunctionModifyRequest(BaseModel):
    """Request to modify a function node's working interpretation."""
    paradigm: Optional[str] = None
    prompt_location: Optional[str] = None
    output_type: Optional[str] = None
    retry: bool = False


class FunctionModifyResponse(BaseModel):
    """Response for function modification."""
    success: bool
    flow_index: str
    modified_fields: list


@router.post("/modify-function/{flow_index}", response_model=FunctionModifyResponse)
async def modify_function(flow_index: str, request: FunctionModifyRequest):
    """Modify a function node's working interpretation.
    
    This allows changing the paradigm, prompt location, output type, etc.
    for a function node before re-execution.
    
    Args:
        flow_index: The flow_index of the function node to modify
        request: The modifications to apply
    """
    try:
        modifications = {}
        if request.paradigm is not None:
            modifications['paradigm'] = request.paradigm
        if request.prompt_location is not None:
            modifications['prompt_location'] = request.prompt_location
        if request.output_type is not None:
            modifications['output_type'] = request.output_type
        
        result = await execution_controller.modify_function(
            flow_index=flow_index,
            modifications=modifications,
            retry=request.retry
        )
        return FunctionModifyResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependents/{concept_name}")
async def get_dependents(concept_name: str):
    """Get all flow_indices that depend on a concept.
    
    Useful for previewing which nodes would be affected by overriding a value.
    """
    try:
        dependents = execution_controller._find_dependents(concept_name)
        return {
            "concept_name": concept_name,
            "dependents": dependents,
            "count": len(dependents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/descendants/{flow_index}")
async def get_descendants(flow_index: str):
    """Get all downstream nodes from a flow_index.
    
    Useful for previewing which nodes would be reset by re-running from a node.
    """
    try:
        descendants = execution_controller._find_descendants(flow_index)
        return {
            "flow_index": flow_index,
            "descendants": descendants,
            "count": len(descendants)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# User Input Endpoints (Human-in-the-loop)
# =============================================================================

class UserInputSubmitRequest(BaseModel):
    """Request to submit user input response."""
    response: Any


class UserInputSubmitResponse(BaseModel):
    """Response for user input submission."""
    success: bool
    request_id: str
    message: str


@router.get("/user-input/pending")
async def get_pending_user_inputs():
    """Get all pending user input requests.
    
    Returns list of pending input requests that need user response.
    """
    if execution_controller.user_input_tool is None:
        return {"requests": [], "count": 0}
    
    requests = execution_controller.user_input_tool.get_pending_requests()
    return {
        "requests": requests,
        "count": len(requests)
    }


@router.post("/user-input/{request_id}/submit", response_model=UserInputSubmitResponse)
async def submit_user_input(request_id: str, request: UserInputSubmitRequest):
    """Submit a response for a pending user input request.
    
    Args:
        request_id: The ID of the pending request
        request.response: The user's response (string, bool, etc.)
    """
    if execution_controller.user_input_tool is None:
        raise HTTPException(status_code=400, detail="User input tool not initialized")
    
    success = execution_controller.user_input_tool.submit_response(
        request_id, 
        request.response
    )
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"No pending request found with ID: {request_id}"
        )
    
    return UserInputSubmitResponse(
        success=True,
        request_id=request_id,
        message="Response submitted successfully"
    )


@router.post("/user-input/{request_id}/cancel", response_model=UserInputSubmitResponse)
async def cancel_user_input(request_id: str):
    """Cancel a pending user input request.
    
    Args:
        request_id: The ID of the request to cancel
    """
    if execution_controller.user_input_tool is None:
        raise HTTPException(status_code=400, detail="User input tool not initialized")
    
    success = execution_controller.user_input_tool.cancel_request(request_id)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"No pending request found with ID: {request_id}"
        )
    
    return UserInputSubmitResponse(
        success=True,
        request_id=request_id,
        message="Request cancelled"
    )


# ============================================================================
# Chat Input (for chat-driven paradigms like c_ChatRead-o_Literal)
# ============================================================================

class ChatInputSubmitRequest(BaseModel):
    """Request body for submitting chat input."""
    value: str


@router.post("/chat-input/{request_id}")
async def submit_chat_input(request_id: str, request: ChatInputSubmitRequest):
    """Submit a response for a pending chat input request.
    
    This is used when a NormCode plan is blocking on a chat read operation
    (e.g., using the c_ChatRead-o_Literal paradigm).
    
    Args:
        request_id: The ID of the pending chat request
        request.value: The user's message
    """
    if not hasattr(execution_controller, 'chat_tool') or execution_controller.chat_tool is None:
        raise HTTPException(status_code=400, detail="Chat tool not initialized")
    
    success = execution_controller.chat_tool.submit_response(request_id, request.value)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"No pending chat request found with ID: {request_id}"
        )
    
    return {"success": True, "request_id": request_id}


@router.post("/chat-input/{request_id}/cancel")
async def cancel_chat_input(request_id: str):
    """Cancel a pending chat input request.
    
    Args:
        request_id: The ID of the request to cancel
    """
    if not hasattr(execution_controller, 'chat_tool') or execution_controller.chat_tool is None:
        raise HTTPException(status_code=400, detail="Chat tool not initialized")
    
    success = execution_controller.chat_tool.cancel_request(request_id)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"No pending chat request found with ID: {request_id}"
        )
    
    return {"success": True, "request_id": request_id, "message": "Request cancelled"}


@router.get("/chat-input/pending")
async def get_pending_chat_input():
    """Get the current pending chat input request, if any.
    
    Returns:
        The pending request details or null
    """
    if not hasattr(execution_controller, 'chat_tool') or execution_controller.chat_tool is None:
        return {"pending": None}
    
    pending = execution_controller.chat_tool.get_pending_request()
    return {"pending": pending}
