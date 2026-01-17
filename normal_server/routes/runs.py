"""
Runs API Routes

Endpoints for run execution, control, and monitoring.
"""

import json
import uuid
import shutil
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query

from service import (
    get_config, StartRunRequest, RunStatus, RunState,
    active_runs, discover_plans, execute_run, execute_run_with_resume,
    # IDE-level debugging schemas
    BreakpointRequest, BreakpointResponse,
    ValueOverrideRequest, ValueOverrideResponse,
    ReferenceDataResponse, NodeStatusesResponse,
    LogEntry, LogsResponse, CommandResponse,
)

router = APIRouter()


def _get_historical_run_info(run_id: str, run_dir: Path, db_path: Path) -> Optional[RunStatus]:
    """
    Reconstruct run info from disk for a historical (non-active) run.
    """
    try:
        plan_id = "unknown"
        status = "unknown"
        started_at = None
        completed_at = None
        progress = None
        error = None
        
        # Try to get info from database
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get run metadata if available
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='run_metadata'")
                if cursor.fetchone():
                    cursor.execute("SELECT key, value FROM run_metadata WHERE run_id = ?", (run_id,))
                    metadata = {row['key']: row['value'] for row in cursor.fetchall()}
                    plan_id = metadata.get('plan_id', plan_id)
                    status = metadata.get('status', 'completed')
                    started_at = metadata.get('started_at')
                    completed_at = metadata.get('completed_at')
                
                # Get execution counts for progress
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='executions'")
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                            MAX(cycle) as max_cycle
                        FROM executions 
                        WHERE run_id = ?
                    """, (run_id,))
                    row = cursor.fetchone()
                    if row:
                        progress = {
                            "completed_count": row['completed'] or 0,
                            "total_count": row['total'] or 0,
                            "cycle_count": row['max_cycle'] or 0,
                            "current_inference": None,
                        }
                        # Infer status from execution data if not set
                        if status == "unknown":
                            if row['completed'] == row['total'] and row['total'] > 0:
                                status = "completed"
                            elif row['total'] > 0:
                                status = "stopped"  # Has executions but not all completed
                
                conn.close()
            except Exception as e:
                logging.debug(f"Could not read DB for run {run_id}: {e}")
        
        # Fallback: get times from directory modification
        if not started_at:
            try:
                stat = run_dir.stat()
                started_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
                if not completed_at and status in ('completed', 'failed', 'stopped'):
                    completed_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception:
                pass
        
        # If we have a database, assume it's a valid historical run
        if db_path.exists() or status != "unknown":
            return RunStatus(
                run_id=run_id,
                plan_id=plan_id,
                status=status if status != "unknown" else "historical",
                started_at=started_at,
                completed_at=completed_at,
                progress=progress,
                error=error,
            )
        
        return None
        
    except Exception as e:
        logging.debug(f"Failed to get historical run info for {run_id}: {e}")
        return None


@router.post("", response_model=RunStatus)
async def start_run(request: StartRunRequest, background_tasks: BackgroundTasks):
    """Start a new plan execution."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if request.plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {request.plan_id}")
    
    plan_config = plans[request.plan_id]
    run_id = request.run_id or str(uuid.uuid4())
    
    if run_id in active_runs:
        raise HTTPException(409, f"Run already exists: {run_id}")
    
    # Create run state
    run_state = RunState(run_id, request.plan_id, plan_config)
    active_runs[run_id] = run_state
    
    # Start execution in background
    background_tasks.add_task(
        execute_run,
        run_state,
        request.llm_model,
        request.max_cycles
    )
    
    return run_state.to_status()


@router.get("", response_model=List[RunStatus])
async def list_runs(include_historical: bool = True):
    """
    List all runs (active and historical).
    
    Args:
        include_historical: If True, also scan disk for completed runs not in memory.
    
    Returns active runs from memory, plus historical runs from disk if requested.
    """
    result = []
    seen_run_ids = set()
    
    # 1. Add all active runs from memory
    for run in active_runs.values():
        result.append(run.to_status())
        seen_run_ids.add(run.run_id)
    
    # 2. Scan disk for historical runs (if requested)
    if include_historical:
        cfg = get_config()
        if cfg.runs_dir.exists():
            for run_dir in cfg.runs_dir.iterdir():
                if run_dir.is_dir():
                    run_id = run_dir.name
                    if run_id in seen_run_ids:
                        continue  # Already in active runs
                    
                    # Try to reconstruct run info from disk
                    db_path = run_dir / "run.db"
                    run_info = _get_historical_run_info(run_id, run_dir, db_path)
                    if run_info:
                        result.append(run_info)
    
    # Sort by started_at descending (most recent first)
    result.sort(key=lambda r: r.started_at or "", reverse=True)
    
    return result


@router.get("/{run_id}", response_model=RunStatus)
async def get_run(run_id: str):
    """Get status of a specific run (active or historical)."""
    # Check active runs first
    if run_id in active_runs:
        return active_runs[run_id].to_status()
    
    # Check for historical run on disk
    cfg = get_config()
    run_dir = cfg.runs_dir / run_id
    if run_dir.exists():
        db_path = run_dir / "run.db"
        run_info = _get_historical_run_info(run_id, run_dir, db_path)
        if run_info:
            return run_info
    
    raise HTTPException(404, f"Run not found: {run_id}")


@router.get("/{run_id}/result")
async def get_run_result(run_id: str):
    """Get the result of a completed run (active or historical)."""
    # Check active runs first
    if run_id in active_runs:
        run = active_runs[run_id]
        if run.status != "completed":
            raise HTTPException(400, f"Run not completed (status: {run.status})")
        return run.result
    
    # Check for historical run result from database
    cfg = get_config()
    run_dir = cfg.runs_dir / run_id
    db_path = run_dir / "run.db"
    
    if not db_path.exists():
        raise HTTPException(404, f"Run not found: {run_id}")
    
    # Try to get final concepts from the last checkpoint
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the latest checkpoint with completed concepts
        cursor.execute("""
            SELECT state_json FROM checkpoints 
            WHERE run_id = ?
            ORDER BY cycle DESC, inference_count DESC
            LIMIT 1
        """, (run_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            state = json.loads(row['state_json'])
            completed_concepts = state.get('completed_concepts', {})
            
            final_concepts = []
            for name, data in completed_concepts.items():
                concept_result = {
                    "name": name,
                    "has_value": bool(data),
                }
                if isinstance(data, dict):
                    concept_result["shape"] = data.get("shape")
                    if "tensor" in data:
                        tensor_str = json.dumps(data["tensor"])
                        if len(tensor_str) > 5000:
                            tensor_str = tensor_str[:4997] + "..."
                        concept_result["value"] = tensor_str
                final_concepts.append(concept_result)
            
            return {
                "run_id": run_id,
                "plan_id": "unknown",  # Would need to extract from metadata
                "status": "completed",
                "final_concepts": final_concepts,
            }
        
        raise HTTPException(400, "No checkpoint data found for this run")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to read run result: {e}")


@router.post("/{run_id}/stop")
async def stop_run(run_id: str):
    """Stop a running execution gracefully."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    if run.status not in ("running", "paused", "stepping"):
        raise HTTPException(400, f"Run not active (status: {run.status})")
    
    # Request graceful stop
    run.request_stop()
    run.completed_at = datetime.now()
    
    # Emit stop event
    await run.emit_event("execution:stopped", {
        "run_id": run_id,
    })
    
    return {"status": "stopped", "run_id": run_id}


@router.post("/{run_id}/pause")
async def pause_run(run_id: str):
    """Pause a running execution."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    if run.status != "running":
        raise HTTPException(400, f"Run not running (status: {run.status})")
    
    run.request_pause()
    
    # Emit pause event
    await run.emit_event("execution:paused", {
        "run_id": run_id,
    })
    
    return {"status": "paused", "run_id": run_id}


@router.post("/{run_id}/continue")
async def continue_run_execution(run_id: str):
    """Continue a paused execution (not to be confused with checkpoint resume)."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    if run.status not in ("paused", "stepping"):
        raise HTTPException(400, f"Run not paused (status: {run.status})")
    
    run.request_resume()
    
    # Emit resume event
    await run.emit_event("execution:resumed", {
        "run_id": run_id,
    })
    
    return {"status": "running", "run_id": run_id}


@router.post("/{run_id}/step")
async def step_run(run_id: str):
    """Execute one inference then pause."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    if run.status not in ("paused", "stepping", "running"):
        raise HTTPException(400, f"Run not active (status: {run.status})")
    
    run.request_step()
    
    # Emit step event
    await run.emit_event("execution:stepping", {
        "run_id": run_id,
    })
    
    return {"status": "stepping", "run_id": run_id}


@router.post("/{run_id}/resume")
async def resume_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    cycle: Optional[int] = None,
    inference_count: Optional[int] = None,
    llm_model: Optional[str] = None,
    fork: bool = False,
):
    """
    Resume a run from a checkpoint.
    
    Args:
        run_id: The run to resume from
        cycle: Checkpoint cycle to resume from (latest if not specified)
        inference_count: Specific inference count within cycle
        llm_model: Override LLM model for resumed run
        fork: If True, create a new run ID (fork); if False, continue same run
    
    Returns:
        The new/resumed run status
    """
    cfg = get_config()
    run_dir = cfg.runs_dir / run_id
    db_path = run_dir / "run.db"
    
    if not db_path.exists():
        raise HTTPException(404, f"Database not found for run: {run_id}")
    
    # Find the checkpoint to resume from
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if cycle is not None:
            if inference_count is not None:
                cursor.execute("""
                    SELECT cycle, inference_count, state_json 
                    FROM checkpoints 
                    WHERE run_id = ? AND cycle = ? AND inference_count = ?
                """, (run_id, cycle, inference_count))
            else:
                cursor.execute("""
                    SELECT cycle, inference_count, state_json 
                    FROM checkpoints 
                    WHERE run_id = ? AND cycle = ?
                    ORDER BY inference_count DESC LIMIT 1
                """, (run_id, cycle))
        else:
            cursor.execute("""
                SELECT cycle, inference_count, state_json 
                FROM checkpoints 
                WHERE run_id = ?
                ORDER BY cycle DESC, inference_count DESC LIMIT 1
            """, (run_id,))
        
        row = cursor.fetchone()
        
        # Also get the plan_id from metadata if available
        plan_id = None
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='run_metadata'")
        if cursor.fetchone():
            cursor.execute("SELECT value FROM run_metadata WHERE run_id = ? AND key = 'plan_id'", (run_id,))
            meta_row = cursor.fetchone()
            if meta_row:
                plan_id = meta_row['value']
        
        conn.close()
        
        if not row:
            raise HTTPException(404, f"No checkpoint found for run {run_id}")
        
        checkpoint_cycle = row["cycle"]
        checkpoint_inference = row["inference_count"]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to read checkpoint: {e}")
    
    # Determine the new run ID
    if fork:
        new_run_id = str(uuid.uuid4())
    else:
        new_run_id = run_id
    
    # Find the plan config
    if not plan_id:
        raise HTTPException(400, "Cannot determine plan_id for this run")
    
    plans = discover_plans(cfg.plans_dir)
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    
    # Create run state
    run_state = RunState(new_run_id, plan_id, plan_config)
    
    # Store resume info for the execution
    run_state._resume_from = {
        "original_run_id": run_id,
        "cycle": checkpoint_cycle,
        "inference_count": checkpoint_inference,
        "db_path": str(db_path),
    }
    
    active_runs[new_run_id] = run_state
    
    # Start execution in background (with resume)
    background_tasks.add_task(
        execute_run_with_resume,
        run_state,
        llm_model,
        None,  # max_cycles
    )
    
    return {
        "status": "resuming",
        "run_id": new_run_id,
        "plan_id": plan_id,
        "resumed_from": {
            "run_id": run_id,
            "cycle": checkpoint_cycle,
            "inference_count": checkpoint_inference,
        },
        "is_fork": fork,
    }


# =============================================================================
# IDE-Level Debugging Endpoints
# =============================================================================

@router.post("/{run_id}/run-to/{flow_index}")
async def run_to_node(run_id: str, flow_index: str):
    """
    Run execution until a specific node is executed, then pause.
    
    This sets a one-time target - execution will run until the specified
    flow_index is reached, then automatically pause. The target is cleared
    after being hit.
    """
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    if flow_index not in run._node_statuses:
        raise HTTPException(400, f"Unknown flow_index: {flow_index}")
    
    if run._node_statuses.get(flow_index) == 'completed':
        raise HTTPException(400, f"Node {flow_index} is already completed")
    
    # Set the run-to target
    run.set_run_to_target(flow_index)
    
    # Resume if paused
    if run.status == "paused":
        run.request_resume()
    
    await run.emit_event("execution:run_to", {
        "run_id": run_id,
        "target": flow_index,
    })
    
    return {"status": "running_to", "run_id": run_id, "target": flow_index}


@router.get("/{run_id}/breakpoints")
async def list_breakpoints(run_id: str):
    """List all breakpoints for a run."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    return {"run_id": run_id, "breakpoints": list(run.breakpoints)}


@router.post("/{run_id}/breakpoints")
async def set_breakpoint(run_id: str, request: BreakpointRequest):
    """Set or clear a breakpoint at a flow_index."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    if request.enabled:
        run.add_breakpoint(request.flow_index)
        await run.emit_event("breakpoint:set", {
            "flow_index": request.flow_index,
        })
    else:
        run.remove_breakpoint(request.flow_index)
        await run.emit_event("breakpoint:cleared", {
            "flow_index": request.flow_index,
        })
    
    return BreakpointResponse(
        success=True,
        flow_index=request.flow_index,
        enabled=request.enabled,
        all_breakpoints=list(run.breakpoints)
    )


@router.delete("/{run_id}/breakpoints/{flow_index}")
async def clear_breakpoint(run_id: str, flow_index: str):
    """Clear a specific breakpoint."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    run.remove_breakpoint(flow_index)
    
    await run.emit_event("breakpoint:cleared", {
        "flow_index": flow_index,
    })
    
    return BreakpointResponse(
        success=True,
        flow_index=flow_index,
        enabled=False,
        all_breakpoints=list(run.breakpoints)
    )


@router.delete("/{run_id}/breakpoints")
async def clear_all_breakpoints(run_id: str):
    """Clear all breakpoints for a run."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    old_breakpoints = list(run.breakpoints)
    run.clear_all_breakpoints()
    
    await run.emit_event("breakpoints:cleared_all", {
        "cleared": old_breakpoints,
    })
    
    return {"success": True, "cleared": old_breakpoints}


@router.get("/{run_id}/node-statuses")
async def get_node_statuses(run_id: str):
    """Get all node statuses for a run."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    return NodeStatusesResponse(
        run_id=run_id,
        statuses=run._node_statuses,
        current_inference=run.current_inference
    )


@router.get("/{run_id}/reference/{concept_name}")
async def get_reference_data(run_id: str, concept_name: str):
    """
    Get reference data for a specific concept.
    
    Returns the current computed value including data, shape, and axes.
    """
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    ref_data = run.get_reference_data(concept_name)
    
    if ref_data is None:
        return ReferenceDataResponse(
            concept_name=concept_name,
            has_reference=False
        )
    
    return ReferenceDataResponse(**ref_data)


@router.get("/{run_id}/references")
async def get_all_references(run_id: str):
    """Get reference data for all concepts that have values."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    return run.get_all_reference_data()


@router.post("/{run_id}/override/{concept_name}")
async def override_value(run_id: str, concept_name: str, request: ValueOverrideRequest):
    """
    Override a concept's reference value.
    
    This allows injecting or modifying values at any node.
    Optionally marks dependents as stale and triggers re-execution.
    """
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    if not run.orchestrator or not run.orchestrator.concept_repo:
        raise HTTPException(400, "Orchestrator not initialized")
    
    try:
        # Get the concept and update its reference
        concept_entry = run.orchestrator.concept_repo.get_concept(concept_name)
        if not concept_entry:
            raise HTTPException(404, f"Concept not found: {concept_name}")
        
        # Set the new value
        run.orchestrator.concept_repo.add_reference(concept_name, request.new_value)
        
        # Find dependent nodes if needed
        stale_nodes = []
        if request.rerun_dependents:
            # Find all inferences that use this concept as input
            for item in run.orchestrator.waitlist.items:
                inf_entry = item.inference_entry
                for inp in inf_entry.inputs:
                    if inp.concept_name == concept_name:
                        flow_index = inf_entry.flow_info.get('flow_index', '')
                        if flow_index:
                            stale_nodes.append(flow_index)
                            run._node_statuses[flow_index] = 'pending'
                            run.orchestrator.blackboard.set_item_status(flow_index, 'pending')
        
        await run.emit_event("value:overridden", {
            "concept_name": concept_name,
            "stale_nodes": stale_nodes,
        })
        run.add_log("info", "", f"Value overridden for '{concept_name}', {len(stale_nodes)} nodes marked stale")
        
        # Resume if requested and paused
        if request.rerun_dependents and run.status == "paused":
            run.request_resume()
        
        return ValueOverrideResponse(
            success=True,
            concept_name=concept_name,
            stale_nodes=stale_nodes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to override value: {e}")


@router.get("/{run_id}/logs")
async def get_logs(
    run_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    flow_index: Optional[str] = Query(default=None)
):
    """Get execution logs for a run, optionally filtered by flow_index."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    logs = run.get_logs(limit=limit, flow_index=flow_index)
    
    return LogsResponse(
        logs=[LogEntry(**log) for log in logs],
        total_count=len(run.logs)
    )


@router.get("/{run_id}/graph")
async def get_run_graph(run_id: str):
    """
    Get graph visualization data for a run.
    
    Returns nodes and edges suitable for rendering in a graph UI.
    """
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    try:
        from service.plans import load_plan_graph
        graph_data = load_plan_graph(run.config)
        return graph_data
    except Exception as e:
        raise HTTPException(500, f"Failed to load graph: {e}")


# =============================================================================
# Run Management Endpoints
# =============================================================================

@router.delete("")
async def clear_all_runs():
    """Remove ALL runs from the server (stops active runs first)."""
    cfg = get_config()
    
    # Stop all active runs
    stopped = []
    for run_id, run_state in list(active_runs.items()):
        if run_state.status == "running":
            run_state.status = "stopped"
            run_state.completed_at = datetime.now()
            stopped.append(run_id)
    
    # Clear active runs dict
    active_runs.clear()
    
    # Remove all run directories
    removed = []
    failed = []
    
    if cfg.runs_dir.exists():
        for run_dir in cfg.runs_dir.iterdir():
            if run_dir.is_dir():
                try:
                    shutil.rmtree(run_dir)
                    removed.append(run_dir.name)
                    logging.info(f"Removed run directory: {run_dir.name}")
                except Exception as e:
                    failed.append({"run_id": run_dir.name, "error": str(e)})
                    logging.error(f"Failed to remove run {run_dir.name}: {e}")
    
    return {
        "status": "completed",
        "stopped_count": len(stopped),
        "removed_count": len(removed),
        "stopped": stopped,
        "removed": removed,
        "failed": failed
    }


@router.post("/server/reset")
async def reset_server():
    """
    Full server reset - clears ALL plans AND runs.
    
    This is a destructive operation that removes:
    - All deployed plans
    - All run data and history
    - All active run states
    
    Use with caution!
    """
    cfg = get_config()
    
    results = {
        "plans_removed": [],
        "runs_removed": [],
        "runs_stopped": [],
        "errors": []
    }
    
    # 1. Stop all active runs
    for run_id, run_state in list(active_runs.items()):
        if run_state.status == "running":
            run_state.status = "stopped"
            run_state.completed_at = datetime.now()
            results["runs_stopped"].append(run_id)
    active_runs.clear()
    
    # 2. Clear all runs directories
    if cfg.runs_dir.exists():
        for run_dir in cfg.runs_dir.iterdir():
            if run_dir.is_dir():
                try:
                    shutil.rmtree(run_dir)
                    results["runs_removed"].append(run_dir.name)
                except Exception as e:
                    results["errors"].append({"type": "run", "id": run_dir.name, "error": str(e)})
    
    # 3. Clear all plans
    plans = discover_plans(cfg.plans_dir)
    for plan_id, plan_config in plans.items():
        try:
            plan_dir = plan_config.project_dir
            if plan_dir.exists():
                shutil.rmtree(plan_dir)
                results["plans_removed"].append(plan_id)
        except Exception as e:
            results["errors"].append({"type": "plan", "id": plan_id, "error": str(e)})
    
    logging.warning(f"SERVER RESET: Removed {len(results['plans_removed'])} plans and {len(results['runs_removed'])} runs")
    
    return {
        "status": "reset_complete",
        "plans_removed_count": len(results["plans_removed"]),
        "runs_removed_count": len(results["runs_removed"]),
        "runs_stopped_count": len(results["runs_stopped"]),
        "details": results
    }

