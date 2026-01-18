"""Execution control endpoints."""
import asyncio
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Any, List, Dict, Union
import logging

from services.execution_service import (
    execution_controller, execution_controller_registry, get_execution_controller,
    get_worker_registry, PanelType, RunMode,
)
from services.project_service import project_service
from schemas.execution_schemas import (
    ExecutionState, BreakpointRequest, LogsResponse, LogEntry,
    ExecutionConfig, LLM_MODELS, DEFAULT_MAX_CYCLES, DEFAULT_DB_PATH,
    SEQUENCE_STEPS, STEP_FULL_NAMES
)

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# Unified Execution Routing
# =============================================================================
# These helpers route execution commands to the appropriate controller based on
# the active project type (local vs remote). This enables the frontend to use
# the same API endpoints regardless of whether execution is local or remote.

def _get_active_executor():
    """
    Get the appropriate executor for the active project.
    
    Returns:
        Tuple of (executor, is_remote) where executor is either:
        - The local ExecutionController for local projects
        - The RemoteProxyExecutor for remote projects
    """
    from services.execution.remote_proxy_executor import get_active_remote_proxy
    
    # Check if there's an active remote proxy
    remote_proxy = get_active_remote_proxy()
    if remote_proxy and remote_proxy.is_connected:
        return remote_proxy, True
    
    # Check if active project is remote (by ID pattern)
    active_project = project_service.get_active_project()
    if active_project and active_project.is_remote:
        # Remote project but no proxy connected - return None
        logger.warning(f"Remote project {active_project.id} active but no proxy connected")
        return None, True
    
    # Default to local execution controller
    return execution_controller, False


async def _execute_command(command: str, *args, **kwargs):
    """
    Execute a command on the appropriate executor (local or remote).
    
    This is the unified routing function that enables the frontend to use
    the same API endpoints for both local and remote execution.
    """
    executor, is_remote = _get_active_executor()
    
    if executor is None:
        raise HTTPException(
            status_code=400,
            detail="No active executor. For remote projects, connect a proxy first."
        )
    
    method = getattr(executor, command, None)
    if method is None:
        raise HTTPException(
            status_code=400,
            detail=f"Executor does not support command: {command}"
        )
    
    return await method(*args, **kwargs)


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
    """Start or resume plan execution.
    
    This endpoint is unified - it routes to either local or remote
    execution based on the active project type.
    
    For remote projects that haven't started a run yet, this endpoint will:
    1. Start a run on the remote server (which auto-starts execution)
    2. Activate the remote proxy to stream events
    
    Note: The normal_server's POST /api/runs already starts execution in the
    background, so we don't need to call start() again - just connect the proxy.
    """
    from services.execution.remote_proxy_executor import get_active_remote_proxy, activate_remote_proxy
    
    try:
        # Check if we have a remote project without an active proxy
        active_project = project_service.get_active_project()
        remote_proxy = get_active_remote_proxy()
        
        if active_project and active_project.is_remote and (not remote_proxy or not remote_proxy.is_connected):
            # Remote project without active proxy - need to start a run first
            logger.info(f"Starting run for remote project: {active_project.id}")
            
            # Get server info from project
            server_url = active_project.server_url
            plan_id = active_project.plan_id
            
            if not server_url or not plan_id:
                raise HTTPException(
                    status_code=400,
                    detail="Remote project missing server_url or plan_id"
                )
            
            # Get LLM model from the remote project (if configured)
            # Note: llm_model is now agent-centric, so we only use remote_llm_model here
            llm_model = getattr(active_project, 'remote_llm_model', None)
            
            # Start a run on the remote server
            # NOTE: normal_server's POST /api/runs automatically starts execution
            # in the background, so the run will already be running when we connect
            import aiohttp
            run_payload = {"plan_id": plan_id}
            if llm_model and llm_model != "demo":
                run_payload["llm_model"] = llm_model
                logger.info(f"Starting remote run with LLM: {llm_model}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/api/runs",
                    json=run_payload
                ) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to start remote run: {error}"
                        )
                    run_data = await resp.json()
                    run_id = run_data.get("run_id")
            
            logger.info(f"Remote run started: {run_id}")
            
            # Activate the remote proxy to stream events
            # Don't call start() again - the run is already running!
            await activate_remote_proxy(
                server_url=server_url,
                run_id=run_id,
                project_id=active_project.id,
            )
            
            logger.info(f"Remote proxy activated for run: {run_id}")
            
            # The run is already executing on the remote server
            # The proxy is now streaming events to the frontend
            return CommandResponse(success=True, message="Remote execution started")
        
        # Normal case: use the unified routing
        await _execute_command("start")
        return CommandResponse(success=True, message="Execution started")
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to start execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause", response_model=CommandResponse)
async def pause_execution():
    """Pause execution after current inference.
    
    This endpoint is unified - works for both local and remote.
    """
    try:
        await _execute_command("pause")
        return CommandResponse(success=True, message="Execution paused")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", response_model=CommandResponse)
async def resume_execution():
    """Resume from paused state.
    
    This endpoint is unified - works for both local and remote.
    """
    try:
        await _execute_command("resume")
        return CommandResponse(success=True, message="Execution resumed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step", response_model=CommandResponse)
async def step_execution():
    """Execute single inference then pause.
    
    This endpoint is unified - works for both local and remote.
    """
    try:
        await _execute_command("step")
        return CommandResponse(success=True, message="Stepping to next inference")
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=CommandResponse)
async def stop_execution():
    """Stop execution.
    
    This endpoint is unified - works for both local and remote.
    """
    try:
        await _execute_command("stop")
        return CommandResponse(success=True, message="Execution stopped")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart", response_model=CommandResponse)
async def restart_execution():
    """Restart execution from the beginning.
    
    Resets all node statuses and allows re-running the plan.
    This endpoint is unified - works for both local and remote.
    """
    try:
        await _execute_command("restart")
        return CommandResponse(success=True, message="Execution reset - ready to run")
    except HTTPException:
        raise
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
    """Get execution logs, optionally filtered by flow_index.
    
    Routes to either local or remote executor based on active project.
    """
    executor, is_remote = _get_active_executor()
    
    if executor is None:
        return LogsResponse(logs=[], total_count=0)
    
    # Get logs - handle both sync and async methods
    if hasattr(executor, 'get_logs'):
        if asyncio.iscoroutinefunction(executor.get_logs):
            logs = await executor.get_logs(limit=limit, flow_index=flow_index)
        else:
            logs = executor.get_logs(limit=limit, flow_index=flow_index)
    else:
        logs = []
    
    # Get total count
    total_count = len(logs)
    if hasattr(executor, 'logs') and not is_remote:
        total_count = len(executor.logs)
    
    return LogsResponse(
        logs=[LogEntry(**log) if isinstance(log, dict) else log for log in logs],
        total_count=total_count
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
    
    Routes to either local or remote executor based on active project.
    
    Returns the current tensor data for a concept including:
    - data: The tensor data
    - axes: Axis names
    - shape: Tensor shape
    
    Returns empty response if concept not found or has no reference.
    """
    executor, is_remote = _get_active_executor()
    
    empty_response = {
        "concept_name": concept_name,
        "has_reference": False,
        "data": None,
        "axes": [],
        "shape": []
    }
    
    if executor is None:
        return empty_response
    
    # Get reference data - handle both sync and async methods
    if hasattr(executor, 'get_reference_data'):
        if asyncio.iscoroutinefunction(executor.get_reference_data):
            ref_data = await executor.get_reference_data(concept_name)
        else:
            ref_data = executor.get_reference_data(concept_name)
    else:
        ref_data = None
    
    if ref_data is None:
        return empty_response
    return ref_data


@router.get("/references")
async def get_all_references():
    """Get reference data for all concepts that have references.
    
    Routes to either local or remote executor based on active project.
    
    Returns a dict mapping concept_name -> reference_data.
    Useful for batch fetching all computed values.
    """
    executor, is_remote = _get_active_executor()
    
    if executor is None:
        return {}
    
    # Get all references - handle both sync and async methods
    if hasattr(executor, 'get_all_reference_data'):
        if asyncio.iscoroutinefunction(executor.get_all_reference_data):
            return await executor.get_all_reference_data()
        else:
            return executor.get_all_reference_data()
    return {}


@router.get("/concept-statuses")
async def get_concept_statuses():
    """Get concept statuses directly from the blackboard.
    
    Routes to either local or remote executor based on active project.
    
    Returns a dict mapping concept_name -> status ('complete' | 'empty' | etc.)
    This queries the infra layer directly, making it the source of truth
    for whether a concept has data.
    
    This is useful for the frontend to determine if a concept has data
    without needing to maintain parallel state in the canvas app.
    """
    executor, is_remote = _get_active_executor()
    
    if executor is None:
        return {}
    
    # Get concept statuses - handle both sync and async methods
    if hasattr(executor, 'get_concept_statuses'):
        if asyncio.iscoroutinefunction(executor.get_concept_statuses):
            return await executor.get_concept_statuses()
        else:
            return executor.get_concept_statuses()
    return {}


@router.get("/reference/{concept_name}/history")
async def get_reference_history(
    concept_name: str, 
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get historical iteration values for a concept.
    
    During loop iterations, concept values are cleared and recomputed.
    This endpoint returns historical snapshots from previous iterations,
    allowing the UI to display past values.
    
    Returns:
        - concept_name: The queried concept name
        - run_id: The current run ID
        - history: List of historical entries (newest first), each containing:
            - iteration_index: The iteration number
            - cycle_number: The orchestrator cycle when saved
            - data: The tensor data
            - axes: Axis names
            - shape: Tensor shape
            - timestamp: When the snapshot was saved
        - total_iterations: Total number of historical entries
    """
    if not execution_controller.orchestrator:
        return {
            "concept_name": concept_name,
            "run_id": None,
            "history": [],
            "total_iterations": 0,
            "message": "No active execution"
        }
    
    history = execution_controller.get_iteration_history(concept_name, limit)
    
    return {
        "concept_name": concept_name,
        "run_id": execution_controller.orchestrator.run_id,
        "history": history,
        "total_iterations": len(history)
    }


@router.get("/flow/{flow_index}/history")
async def get_flow_history(
    flow_index: str, 
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get historical iteration values for a specific flow_index.
    
    Similar to /reference/{concept_name}/history but queries by flow_index
    instead of concept name. Useful for the DetailPanel which has flow_index.
    
    Returns:
        - flow_index: The queried flow_index
        - run_id: The current run ID
        - history: List of historical entries (newest first)
        - total_iterations: Total number of historical entries
    """
    if not execution_controller.orchestrator:
        return {
            "flow_index": flow_index,
            "run_id": None,
            "history": [],
            "total_iterations": 0,
            "message": "No active execution"
        }
    
    history = execution_controller.get_flow_iteration_history(flow_index, limit)
    
    return {
        "flow_index": flow_index,
        "run_id": execution_controller.orchestrator.run_id,
        "history": history,
        "total_iterations": len(history)
    }


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


class RunModeRequest(BaseModel):
    """Request to set the run mode."""
    mode: str  # "slow" or "fast"


@router.post("/run-mode", response_model=CommandResponse)
async def set_run_mode(request: RunModeRequest):
    """Set the execution run mode.
    
    Run modes:
    - "slow" (default): Execute one inference at a time. Easier to follow execution flow.
    - "fast": Execute all ready inferences per cycle. Faster but harder to track.
    """
    try:
        mode = RunMode(request.mode)
        execution_controller.set_run_mode(mode)
        return CommandResponse(
            success=True,
            message=f"Run mode set to '{mode.value}'"
        )
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid run mode: {request.mode}. Must be 'slow' or 'fast'"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run-mode")
async def get_run_mode():
    """Get the current run mode."""
    return {"mode": execution_controller.run_mode.value}


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
    
    Routes to either local or remote executor based on active project.
    
    This allows injecting or modifying values at any ground or computed node.
    Optionally triggers re-execution of dependent nodes.
    
    Args:
        concept_name: The name of the concept to override
        request.new_value: The new value to set
        request.rerun_dependents: If True, mark dependents as stale and start execution
    """
    executor, is_remote = _get_active_executor()
    
    if executor is None:
        raise HTTPException(
            status_code=400,
            detail="No active executor. For remote projects, connect a proxy first."
        )
    
    if not hasattr(executor, 'override_value'):
        raise HTTPException(
            status_code=400,
            detail="Executor does not support value override"
        )
    
    try:
        if asyncio.iscoroutinefunction(executor.override_value):
            result = await executor.override_value(
                concept_name=concept_name,
                new_value=request.new_value,
                rerun_dependents=request.rerun_dependents
            )
        else:
            result = executor.override_value(
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


class ChatBufferRequest(BaseModel):
    """Request body for buffering a chat message."""
    message: str


@router.post("/chat-buffer")
async def buffer_chat_message(request: ChatBufferRequest):
    """Buffer a chat message for the running plan to consume.
    
    Only ONE message can be buffered at a time. If a message is already
    buffered (waiting to be consumed by the plan), this will fail.
    
    If there's already a pending input request, the message is delivered immediately.
    
    Args:
        request.message: The user's message
        
    Returns:
        success: True if message was buffered or delivered
        buffer_full: True if buffer already has a message waiting
        delivered: True if message was delivered to a waiting request immediately
        buffered_message: The message currently in the buffer (if any)
    """
    if not hasattr(execution_controller, 'chat_tool') or execution_controller.chat_tool is None:
        return {"success": False, "reason": "Chat tool not initialized"}
    
    result = execution_controller.chat_tool.buffer_message(request.message)
    return result


@router.get("/chat-buffer/status")
async def get_chat_buffer_status():
    """Get the status of the chat message buffer.
    
    Returns:
        execution_active: Whether execution is currently running
        has_pending_request: Whether the plan is waiting for input
        has_buffered_message: Whether there's a message waiting in the buffer
        buffered_message: The message content (if any)
    """
    if not hasattr(execution_controller, 'chat_tool') or execution_controller.chat_tool is None:
        return {
            "execution_active": False,
            "has_pending_request": False,
            "has_buffered_message": False,
            "buffered_message": None
        }
    
    chat_tool = execution_controller.chat_tool
    return {
        "execution_active": chat_tool.is_execution_active(),
        "has_pending_request": chat_tool.has_pending_request(),
        "has_buffered_message": chat_tool.has_buffered_message(),
        "buffered_message": chat_tool.get_buffered_message()
    }


# =============================================================================
# Worker Registry API (Normalized worker/panel management)
# =============================================================================

@router.get("/workers")
async def list_workers():
    """List all registered workers.
    
    Returns workers with their state and panel bindings.
    """
    registry = get_worker_registry()
    state = registry.get_registry_state()
    return state


@router.get("/workers/{worker_id}")
async def get_worker(worker_id: str):
    """Get details for a specific worker.
    
    Args:
        worker_id: The worker ID
        
    Returns:
        Worker state and bindings
    """
    registry = get_worker_registry()
    worker = registry.get_worker(worker_id)
    
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    return {
        "state": worker.state.to_dict(),
        "bindings": list(worker.bindings),
    }


@router.get("/workers/{worker_id}/state")
async def get_worker_state(worker_id: str):
    """Get execution state for a specific worker.
    
    This returns the full execution state from the worker's controller.
    """
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    return controller.get_state()


@router.get("/workers/{worker_id}/graph")
async def get_worker_graph(worker_id: str):
    """Get graph data for a specific worker.
    
    Returns the pre-built graph from when the worker loaded its repositories.
    This is fast since the graph is already computed.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    # Use pre-built graph if available (built when repos were loaded)
    if controller.graph_data:
        logger.info(f"Returning pre-built graph for worker {worker_id}: {len(controller.graph_data.nodes)} nodes")
        return {
            "nodes": [n.model_dump() for n in controller.graph_data.nodes],
            "edges": [e.model_dump() for e in controller.graph_data.edges],
            "worker_id": worker_id,
        }
    
    # Fallback: Build graph from JSON files if pre-built not available
    if not controller._load_config:
        raise HTTPException(
            status_code=400, 
            detail=f"Worker {worker_id} has no graph data and no load config"
        )
    
    try:
        from services.graph_service import build_graph_from_repositories
        import json
        
        concepts_path = controller._load_config.get("concepts_path")
        inferences_path = controller._load_config.get("inferences_path")
        
        if not concepts_path or not inferences_path:
            raise HTTPException(
                status_code=400,
                detail=f"Worker {worker_id} missing repository paths in load config"
            )
        
        with open(concepts_path, 'r', encoding='utf-8') as f:
            concepts_data = json.load(f)
        with open(inferences_path, 'r', encoding='utf-8') as f:
            inferences_data = json.load(f)
        
        logger.info(f"Building graph on-demand for worker {worker_id}")
        graph = build_graph_from_repositories(concepts_data, inferences_data)
        
        # Cache it for next time
        controller.graph_data = graph
        
        return {
            "nodes": [n.model_dump() for n in graph.nodes],
            "edges": [e.model_dump() for e in graph.edges],
            "worker_id": worker_id,
        }
    except FileNotFoundError as e:
        logger.error(f"Repository file not found for worker {worker_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Repository file not found: {str(e)}")
    except Exception as e:
        logger.exception(f"Failed to build graph for worker {worker_id}")
        raise HTTPException(status_code=500, detail=f"Failed to build graph: {str(e)}")


@router.get("/workers/{worker_id}/reference/{concept_name}")
async def get_worker_reference_data(worker_id: str, concept_name: str):
    """Get reference data for a concept from a specific worker.
    
    This allows fetching concept values from any worker, not just the active project.
    Useful when viewing an assistant's graph in a separate tab.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    if not controller.concept_repo:
        return {
            "concept_name": concept_name,
            "has_reference": False,
            "data": None,
            "axes": [],
            "shape": [],
            "error": "No concept repository loaded"
        }
    
    ref_data = controller.get_reference_data(concept_name)
    if ref_data is None:
        return {
            "concept_name": concept_name,
            "has_reference": False,
            "data": None,
            "axes": [],
            "shape": []
        }
    
    logger.debug(f"Got reference data for {concept_name} from worker {worker_id}")
    return ref_data


@router.get("/workers/{worker_id}/reference/{concept_name}/history")
async def get_worker_reference_history(
    worker_id: str, 
    concept_name: str,
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get historical iteration values for a concept from a specific worker.
    
    This allows fetching iteration history from workers like the chat controller,
    not just the main execution controller.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    if not controller.orchestrator:
        return {
            "concept_name": concept_name,
            "run_id": None,
            "history": [],
            "total_iterations": 0,
            "message": "No active execution for worker"
        }
    
    history = controller.get_iteration_history(concept_name, limit)
    
    logger.debug(f"Got {len(history)} history entries for {concept_name} from worker {worker_id}")
    return {
        "concept_name": concept_name,
        "run_id": controller.orchestrator.run_id,
        "history": history,
        "total_iterations": len(history)
    }


@router.get("/workers/{worker_id}/references")
async def get_worker_all_references(worker_id: str):
    """Get all reference data from a specific worker.
    
    Returns a dict mapping concept_name -> reference_data for all concepts
    that have values in this worker's concept repository.
    """
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    if not controller.concept_repo:
        return {"references": {}, "count": 0}
    
    return controller.get_all_reference_data()


class PanelBindRequest(BaseModel):
    """Request to bind a panel to a worker."""
    panel_id: str
    panel_type: str = "main"  # main, chat, secondary, floating, debug
    worker_id: str


@router.post("/panels/bind")
async def bind_panel(request: PanelBindRequest):
    """Bind a panel to view a specific worker.
    
    This allows any panel to view any worker's execution.
    A panel can only be bound to one worker at a time.
    
    Args:
        request.panel_id: Unique ID for the panel
        request.panel_type: Type of panel (main, chat, secondary, etc.)
        request.worker_id: The worker to bind to
    """
    registry = get_worker_registry()
    
    # Parse panel type
    try:
        panel_type = PanelType(request.panel_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid panel type: {request.panel_type}. Valid types: {[t.value for t in PanelType]}"
        )
    
    try:
        binding = registry.bind_panel(
            panel_id=request.panel_id,
            panel_type=panel_type,
            worker_id=request.worker_id,
        )
        return {
            "success": True,
            "panel_id": binding.panel_id,
            "panel_type": binding.panel_type.value,
            "worker_id": binding.worker_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/panels/{panel_id}/unbind")
async def unbind_panel(panel_id: str):
    """Unbind a panel from its current worker.
    
    Args:
        panel_id: The panel to unbind
    """
    registry = get_worker_registry()
    was_bound = registry.unbind_panel(panel_id)
    
    return {
        "success": True,
        "was_bound": was_bound,
        "panel_id": panel_id,
    }


class PanelSwitchRequest(BaseModel):
    """Request to switch a panel to a different worker."""
    worker_id: str


@router.post("/panels/{panel_id}/switch")
async def switch_panel_worker(panel_id: str, request: PanelSwitchRequest):
    """Switch a panel to view a different worker.
    
    This unbinds from the current worker and binds to the new one.
    
    Args:
        panel_id: The panel to switch
        request.worker_id: The new worker to view
    """
    registry = get_worker_registry()
    
    # Get current binding to preserve panel type
    current = registry.get_panel_binding(panel_id)
    panel_type = current.panel_type if current else PanelType.MAIN
    
    try:
        binding = registry.bind_panel(
            panel_id=panel_id,
            panel_type=panel_type,
            worker_id=request.worker_id,
        )
        return {
            "success": True,
            "panel_id": binding.panel_id,
            "old_worker_id": current.worker_id if current else None,
            "new_worker_id": binding.worker_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/panels/{panel_id}")
async def get_panel_binding(panel_id: str):
    """Get the binding for a specific panel.
    
    Returns which worker the panel is viewing, if any.
    """
    registry = get_worker_registry()
    binding = registry.get_panel_binding(panel_id)
    
    if not binding:
        return {
            "panel_id": panel_id,
            "bound": False,
            "worker_id": None,
        }
    
    return {
        "panel_id": binding.panel_id,
        "bound": True,
        "panel_type": binding.panel_type.value,
        "worker_id": binding.worker_id,
    }


@router.get("/panels/{panel_id}/state")
async def get_panel_worker_state(panel_id: str):
    """Get execution state for the worker bound to a panel.
    
    This is a convenience method to get the execution state
    that a specific panel should display.
    """
    registry = get_worker_registry()
    controller = registry.get_controller_for_panel(panel_id)
    
    if not controller:
        return {
            "panel_id": panel_id,
            "bound": False,
            "state": None,
        }
    
    return {
        "panel_id": panel_id,
        "bound": True,
        "state": controller.get_state(),
    }


# =============================================================================
# Worker Control API (Unified control for local and remote workers)
# =============================================================================

@router.post("/workers/{worker_id}/start")
async def worker_start(worker_id: str):
    """Start/resume execution for a worker (local or remote)."""
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    # Check if it's a remote controller
    if hasattr(controller, 'resume') and callable(controller.resume):
        await controller.resume()
    elif hasattr(controller, 'start') and callable(controller.start):
        await controller.start()
    else:
        raise HTTPException(status_code=400, detail=f"Worker {worker_id} does not support start")
    
    return {"success": True, "worker_id": worker_id, "action": "start"}


@router.post("/workers/{worker_id}/pause")
async def worker_pause(worker_id: str):
    """Pause execution for a worker."""
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    if hasattr(controller, 'pause') and callable(controller.pause):
        await controller.pause()
    else:
        raise HTTPException(status_code=400, detail=f"Worker {worker_id} does not support pause")
    
    return {"success": True, "worker_id": worker_id, "action": "pause"}


@router.post("/workers/{worker_id}/resume")
async def worker_resume(worker_id: str):
    """Resume execution for a worker."""
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    if hasattr(controller, 'resume') and callable(controller.resume):
        await controller.resume()
    else:
        raise HTTPException(status_code=400, detail=f"Worker {worker_id} does not support resume")
    
    return {"success": True, "worker_id": worker_id, "action": "resume"}


@router.post("/workers/{worker_id}/step")
async def worker_step(worker_id: str):
    """Execute one step/inference for a worker."""
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    if hasattr(controller, 'step') and callable(controller.step):
        await controller.step()
    else:
        raise HTTPException(status_code=400, detail=f"Worker {worker_id} does not support step")
    
    return {"success": True, "worker_id": worker_id, "action": "step"}


@router.post("/workers/{worker_id}/stop")
async def worker_stop(worker_id: str):
    """Stop execution for a worker."""
    registry = get_worker_registry()
    controller = registry.get_controller(worker_id)
    
    if not controller:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    
    if hasattr(controller, 'stop') and callable(controller.stop):
        await controller.stop()
    else:
        raise HTTPException(status_code=400, detail=f"Worker {worker_id} does not support stop")
    
    return {"success": True, "worker_id": worker_id, "action": "stop"}


# =============================================================================
# Remote Execution (connect to normal_server)
# =============================================================================

class RemoteConnectRequest(BaseModel):
    """Request to connect to a remote normal_server run."""
    server_url: str
    run_id: str
    panel_id: Optional[str] = None
    panel_type: str = "main"


class RemoteConnectResponse(BaseModel):
    """Response for remote connection."""
    success: bool
    worker_id: str
    server_url: str
    run_id: str
    state: dict


@router.post("/remote/connect", response_model=RemoteConnectResponse)
async def connect_to_remote(request: RemoteConnectRequest):
    """
    Connect to a run executing on a remote normal_server.
    
    This creates a RemoteExecutionController that:
    - Proxies all execution commands to the remote server
    - Subscribes to SSE events for real-time updates
    - Mirrors execution state locally for the canvas UI
    
    Args:
        request.server_url: Base URL of the normal_server (e.g., http://localhost:8080)
        request.run_id: The run ID to connect to
        request.panel_id: Optional panel to bind this worker to
        request.panel_type: Type of panel if binding
    
    Returns:
        Worker info and initial state
    """
    import logging
    logger = logging.getLogger(__name__)
    
    registry = get_worker_registry()
    
    # Parse panel type
    panel_type_enum = None
    if request.panel_id:
        try:
            panel_type_enum = PanelType(request.panel_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid panel type: {request.panel_type}"
            )
    
    try:
        # Register the remote worker
        worker = await registry.register_remote_worker(
            server_url=request.server_url,
            run_id=request.run_id,
            panel_id=request.panel_id,
            panel_type=panel_type_enum or PanelType.MAIN,
        )
        
        logger.info(f"Connected to remote run: {request.run_id} on {request.server_url}")
        
        return RemoteConnectResponse(
            success=True,
            worker_id=worker.state.worker_id,
            server_url=request.server_url,
            run_id=request.run_id,
            state=worker.state.to_dict(),
        )
        
    except Exception as e:
        logger.exception(f"Failed to connect to remote: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to remote server: {str(e)}"
        )


@router.post("/remote/disconnect/{worker_id}")
async def disconnect_remote(worker_id: str):
    """
    Disconnect from a remote normal_server run.
    
    This disconnects the SSE subscription and unregisters the worker.
    """
    registry = get_worker_registry()
    
    success = await registry.disconnect_remote_worker(worker_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Remote worker not found: {worker_id}"
        )
    
    return {"success": True, "worker_id": worker_id, "message": "Disconnected"}


@router.get("/remote/workers")
async def list_remote_workers():
    """
    List all connected remote workers.
    
    Returns information about all active remote connections.
    """
    registry = get_worker_registry()
    remote_workers = registry.get_remote_workers()
    
    return {
        "workers": [
            {
                "worker_id": w.state.worker_id,
                "server_url": w.state.metadata.get("server_url"),
                "run_id": w.state.run_id,
                "status": w.state.status.value,
                "connected": hasattr(w.controller, 'is_connected') and w.controller.is_connected,
                "bindings": list(w.bindings),
            }
            for w in remote_workers
        ],
        "count": len(remote_workers),
    }


@router.get("/remote/{worker_id}/state")
async def get_remote_worker_state(worker_id: str):
    """Get the current state of a remote worker."""
    registry = get_worker_registry()
    worker = registry.get_worker(worker_id)
    
    if not worker or worker.state.category.value != "remote":
        raise HTTPException(
            status_code=404,
            detail=f"Remote worker not found: {worker_id}"
        )
    
    # Get state from the remote controller
    if hasattr(worker.controller, 'get_state'):
        return worker.controller.get_state()
    
    return worker.state.to_dict()


@router.get("/remote/{worker_id}/graph")
async def get_remote_worker_graph(worker_id: str):
    """Get the graph data for a remote worker."""
    registry = get_worker_registry()
    worker = registry.get_worker(worker_id)
    
    if not worker or worker.state.category.value != "remote":
        raise HTTPException(
            status_code=404,
            detail=f"Remote worker not found: {worker_id}"
        )
    
    # Get graph from the remote controller
    if hasattr(worker.controller, 'get_graph_data'):
        graph_data = worker.controller.get_graph_data()
        if graph_data:
            return graph_data
    
    raise HTTPException(
        status_code=404,
        detail="Graph data not available for this remote worker"
    )


# =============================================================================
# Unified Remote Proxy (NEW - Relay Architecture)
# =============================================================================
# These endpoints manage the RemoteProxyExecutor which provides a transparent
# relay between the frontend and a remote normal_server. The frontend uses the
# same execution API endpoints (start, stop, etc.) and receives events through
# the same WebSocket - it doesn't need to know if execution is local or remote.

class ActivateRemoteProxyRequest(BaseModel):
    """Request to activate a remote proxy for unified execution."""
    server_url: str
    run_id: str
    project_id: Optional[str] = None  # Remote project tab ID


class RemoteProxyStatusResponse(BaseModel):
    """Response for remote proxy status."""
    active: bool
    connected: bool
    server_url: Optional[str] = None
    run_id: Optional[str] = None
    status: Optional[str] = None


@router.post("/remote-proxy/activate")
async def activate_remote_proxy(request: ActivateRemoteProxyRequest):
    """
    Activate the remote proxy executor for unified remote execution.
    
    This connects to a remote normal_server run and starts relaying:
    - Commands: start/stop/pause/step → remote server
    - Events: SSE from remote → WebSocket to frontend
    
    After activation, the standard execution endpoints (POST /start, /stop, etc.)
    will automatically route to the remote server. The frontend uses the same
    API and receives events through the same WebSocket.
    
    Args:
        server_url: Base URL of the normal_server
        run_id: The run ID to connect to
        project_id: Optional project tab ID for event routing
    """
    from services.execution.remote_proxy_executor import activate_remote_proxy
    
    try:
        proxy = await activate_remote_proxy(
            server_url=request.server_url,
            run_id=request.run_id,
            project_id=request.project_id,
        )
        
        return {
            "success": True,
            "message": "Remote proxy activated",
            "server_url": proxy.server_url,
            "run_id": proxy.run_id,
            "status": proxy.status.value,
        }
        
    except Exception as e:
        logger.exception(f"Failed to activate remote proxy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remote-proxy/deactivate")
async def deactivate_remote_proxy_endpoint():
    """
    Deactivate the remote proxy executor.
    
    Disconnects from the remote server and switches back to local execution.
    """
    from services.execution.remote_proxy_executor import deactivate_remote_proxy
    
    try:
        await deactivate_remote_proxy()
        return {"success": True, "message": "Remote proxy deactivated"}
    except Exception as e:
        logger.exception(f"Failed to deactivate remote proxy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/remote-proxy/status", response_model=RemoteProxyStatusResponse)
async def get_remote_proxy_status():
    """
    Get the current status of the remote proxy executor.
    """
    from services.execution.remote_proxy_executor import get_active_remote_proxy
    
    proxy = get_active_remote_proxy()
    
    if proxy and proxy.is_connected:
        return RemoteProxyStatusResponse(
            active=True,
            connected=True,
            server_url=proxy.server_url,
            run_id=proxy.run_id,
            status=proxy.status.value,
        )
    else:
        return RemoteProxyStatusResponse(
            active=False,
            connected=False,
        )
