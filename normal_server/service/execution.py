"""
Run Execution Logic

Handles the execution of NormCode plans with event emission.
"""

import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from .config import get_config
from .state import RunState
from .globals import broadcast_event
from runner import load_repositories, create_body


def setup_run_logging(run_dir: Path, run_id: str) -> logging.FileHandler:
    """
    Set up file logging for a specific run.
    Returns the file handler so it can be removed after the run.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = run_dir / f"run_{run_id[:8]}_{timestamp}.log"
    
    # Create file handler with DEBUG level to capture all details
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    ))
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    logging.info(f"Run logging initialized: {log_file}")
    return file_handler


async def execute_run_with_events(run_state: RunState, orchestrator, total_inferences: int):
    """
    Execute orchestrator cycles with granular event emission.
    This wraps the orchestrator's async execution to emit events for each inference.
    """
    completed_count = 0
    cycle_count = 0
    
    # Get the blackboard to monitor status changes
    bb = orchestrator.blackboard
    tracker = orchestrator.tracker
    
    # Track previous statuses to detect changes
    prev_statuses = dict(run_state._node_statuses)
    
    async def emit_status_changes():
        """Emit events for status changes since last check."""
        nonlocal prev_statuses
        changes = {}
        
        for item in orchestrator.waitlist.items:
            flow_index = item.inference_entry.flow_info.get('flow_index', '')
            if flow_index:
                current_status = bb.get_item_status(flow_index)
                if prev_statuses.get(flow_index) != current_status:
                    changes[flow_index] = current_status
                    run_state.set_node_status(flow_index, current_status)
        
        if changes:
            await run_state.emit_event("node:statuses", {"statuses": changes})
            prev_statuses = dict(run_state._node_statuses)
        
        return changes
    
    async def run_cycle_async():
        """Run one cycle with event emission."""
        nonlocal completed_count, cycle_count
        
        cycle_count = tracker.cycle_count + 1
        retries = []
        
        # Find ready items
        ready_items = []
        for item in orchestrator.waitlist.items:
            flow_index = item.inference_entry.flow_info.get('flow_index', '')
            status = bb.get_item_status(flow_index)
            if status == 'pending' and orchestrator._is_ready(item):
                ready_items.append(item)
        
        if not ready_items:
            return False, retries
        
        # Execute each ready item with events
        for item in ready_items:
            # Check for pause/stop before each inference
            if run_state._stop_requested:
                return False, retries
            
            # Wait if paused
            if not run_state._pause_event.is_set():
                await run_state.emit_event("execution:paused", {
                    "completed_count": completed_count,
                    "total_count": total_inferences,
                    "cycle_count": cycle_count,
                })
            
            should_continue = await run_state.wait_if_paused()
            if not should_continue:
                return False, retries
            
            flow_index = item.inference_entry.flow_info.get('flow_index', '')
            concept_name = item.inference_entry.concept_to_infer.concept_name
            
            # Update current inference tracking
            run_state.current_inference = flow_index
            
            # Check for breakpoint BEFORE execution
            if run_state.check_breakpoint(flow_index):
                run_state.status = "paused"
                run_state._pause_event.clear()
                await run_state.emit_event("breakpoint:hit", {
                    "flow_index": flow_index,
                    "concept_name": concept_name,
                    "completed_count": completed_count,
                    "total_count": total_inferences,
                })
                run_state.add_log("info", flow_index, f"Breakpoint hit - paused before execution")
                
                # Wait for resume
                should_continue = await run_state.wait_if_paused()
                if not should_continue:
                    return False, retries
            
            # Emit inference started
            await run_state.emit_event("inference:started", {
                "flow_index": flow_index,
                "concept_name": concept_name,
            })
            run_state.add_log("info", flow_index, f"Starting: {concept_name}")
            
            # Execute the item
            start_time = time.time()
            try:
                new_status = await orchestrator._execute_item_async(item)
                duration = time.time() - start_time
                
                if new_status == 'completed':
                    completed_count += 1
                    await run_state.emit_event("inference:completed", {
                        "flow_index": flow_index,
                        "duration": duration,
                    })
                    run_state.add_log("info", flow_index, f"Completed in {duration:.2f}s")
                elif new_status == 'retry':
                    retries.append(item)
                    await run_state.emit_event("inference:retry", {
                        "flow_index": flow_index,
                    })
                    run_state.add_log("warning", flow_index, f"Needs retry")
                else:
                    await run_state.emit_event("inference:failed", {
                        "flow_index": flow_index,
                        "status": new_status,
                    })
                    run_state.add_log("error", flow_index, f"Failed with status: {new_status}")
                
            except Exception as e:
                duration = time.time() - start_time
                await run_state.emit_event("inference:error", {
                    "flow_index": flow_index,
                    "error": str(e),
                    "duration": duration,
                })
                raise
            
            # Emit status changes after each inference
            await emit_status_changes()
            
            # Emit progress update
            await run_state.emit_event("execution:progress", {
                "completed_count": completed_count,
                "total_count": total_inferences,
                "cycle_count": cycle_count,
                "current_inference": flow_index,
            })
            
            # Handle step mode - pause after completing one inference
            run_state.complete_step()
        
        # Check if any items are still pending
        progress_made = len(ready_items) > 0
        return progress_made, retries
    
    # Main execution loop
    retries = []
    while bb.get_all_pending_or_in_progress_items():
        tracker.cycle_count += 1
        
        await run_state.emit_event("cycle:started", {
            "cycle": tracker.cycle_count,
        })
        
        progress_made, retries = await run_cycle_async()
        
        await run_state.emit_event("cycle:completed", {
            "cycle": tracker.cycle_count,
            "progress_made": progress_made,
        })
        
        if not progress_made and not retries:
            logging.warning("No progress made and no retries - possible deadlock")
            break
        
        # Check max cycles
        if tracker.cycle_count >= orchestrator.max_cycles:
            logging.warning(f"Max cycles ({orchestrator.max_cycles}) reached")
            break
        
        # Small yield to allow other async operations
        await asyncio.sleep(0)
    
    # Get final concepts (same pattern as Orchestrator.run())
    final_concepts = [c for c in orchestrator.concept_repo.get_all_concepts() if c.is_final_concept]
    return final_concepts


async def execute_run(run_state: RunState, llm_override: Optional[str], max_cycles_override: Optional[int]):
    """Execute a run in the background with granular event emission."""
    from infra._orchest._orchestrator import Orchestrator
    
    run_state.status = "running"
    run_state.started_at = datetime.now()
    
    # Emit run started event
    await run_state.emit_event("run:started", {
        "plan_id": run_state.plan_id,
        "started_at": run_state.started_at.isoformat(),
    })
    
    # Setup run-specific logging
    cfg = get_config()
    run_dir = cfg.runs_dir / run_state.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run_log_handler = setup_run_logging(run_dir, run_state.run_id)
    
    try:
        logging.info(f"=" * 60)
        logging.info(f"Starting Run: {run_state.run_id}")
        logging.info(f"Plan: {run_state.plan_id}")
        logging.info(f"Config path: {run_state.config.config_path}")
        logging.info(f"=" * 60)
        
        # Load repositories
        concept_repo, inference_repo = load_repositories(run_state.config)
        
        # Create body with deployment tools for actual LLM runs
        body = create_body(run_state.config, llm_override, use_deployment_tools=True)
        
        logging.info(f"Run {run_state.run_id}: Using LLM '{llm_override or run_state.config.llm_model}'")
        
        # Create orchestrator
        max_cycles = max_cycles_override or run_state.config.max_cycles
        
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            body=body,
            max_cycles=max_cycles,
            db_path=str(run_dir / "run.db"),
            run_id=run_state.run_id
        )
        
        run_state.orchestrator = orchestrator
        
        # Get total inference count for progress tracking
        total_inferences = len(list(orchestrator.waitlist.items))
        
        # Emit initial node statuses (all pending)
        initial_statuses = {}
        for item in orchestrator.waitlist.items:
            flow_index = item.inference_entry.flow_info.get('flow_index', '')
            if flow_index:
                initial_statuses[flow_index] = 'pending'
                run_state.set_node_status(flow_index, 'pending')
        
        await run_state.emit_event("node:statuses", {
            "statuses": initial_statuses,
            "total_count": total_inferences,
        })
        
        # Run with event emission using cycle-based approach
        final_concepts = await execute_run_with_events(run_state, orchestrator, total_inferences)
        
        # Collect results
        run_state.result = {
            "run_id": run_state.run_id,
            "plan_id": run_state.plan_id,
            "status": "completed",
            "final_concepts": []
        }
        
        for fc in final_concepts:
            concept_result = {
                "name": fc.concept_name,
                "has_value": False
            }
            if fc and fc.concept and fc.concept.reference:
                concept_result["has_value"] = True
                concept_result["shape"] = list(fc.concept.reference.shape)
                # Use JSON serialization for proper frontend parsing
                try:
                    data_str = json.dumps(fc.concept.reference.tensor)
                except (TypeError, ValueError):
                    # Fallback to string representation for non-JSON-serializable data
                    data_str = str(fc.concept.reference.tensor)
                if len(data_str) > 5000:  # Increased limit for full data visibility
                    data_str = data_str[:4997] + "..."
                concept_result["value"] = data_str
            run_state.result["final_concepts"].append(concept_result)
        
        run_state.status = "completed"
        run_state.completed_at = datetime.now()
        
        # Notify websocket subscribers
        await broadcast_event(run_state.run_id, {
            "event": "run:completed",
            "run_id": run_state.run_id,
            "result": run_state.result
        })
        
    except Exception as e:
        logging.exception(f"Run {run_state.run_id} failed: {e}")
        run_state.status = "failed"
        run_state.error = str(e)
        run_state.completed_at = datetime.now()
        
        await broadcast_event(run_state.run_id, {
            "event": "run:failed",
            "run_id": run_state.run_id,
            "error": str(e)
        })
    finally:
        # Clean up run-specific logging handler
        if run_log_handler:
            logging.info(f"Run {run_state.run_id} log file saved to: {run_dir}")
            run_log_handler.close()
            logging.getLogger().removeHandler(run_log_handler)


async def execute_run_with_resume(run_state: RunState, llm_override: Optional[str], max_cycles_override: Optional[int]):
    """Execute a run resumed from a checkpoint."""
    from infra._orchest._orchestrator import Orchestrator
    
    run_state.status = "running"
    run_state.started_at = datetime.now()
    
    resume_info = getattr(run_state, '_resume_from', None)
    if not resume_info:
        run_state.status = "failed"
        run_state.error = "No resume info available"
        return
    
    cfg = get_config()
    run_dir = cfg.runs_dir / run_state.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run_log_handler = setup_run_logging(run_dir, run_state.run_id)
    
    try:
        logging.info(f"=" * 60)
        logging.info(f"Resuming Run: {run_state.run_id}")
        logging.info(f"From: {resume_info['original_run_id']} cycle={resume_info['cycle']}")
        logging.info(f"Plan: {run_state.plan_id}")
        logging.info(f"=" * 60)
        
        # Load repositories
        concept_repo, inference_repo = load_repositories(run_state.config)
        
        # Create body
        body = create_body(run_state.config, llm_override, use_deployment_tools=True)
        
        max_cycles = max_cycles_override or run_state.config.max_cycles
        
        # Create orchestrator with resume
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            body=body,
            max_cycles=max_cycles,
            db_path=str(run_dir / "run.db"),
            run_id=run_state.run_id,
        )
        
        run_state.orchestrator = orchestrator
        
        # Resume from checkpoint
        orchestrator.resume_from_checkpoint(
            db_path=resume_info['db_path'],
            run_id=resume_info['original_run_id'],
            cycle=resume_info['cycle'],
            inference_count=resume_info['inference_count'],
        )
        
        # Run
        final_concepts = await orchestrator.run_async()
        
        # Collect results (same as execute_run)
        run_state.result = {
            "run_id": run_state.run_id,
            "plan_id": run_state.plan_id,
            "status": "completed",
            "resumed_from": resume_info,
            "final_concepts": []
        }
        
        for fc in final_concepts:
            concept_result = {"name": fc.concept_name, "has_value": False}
            if fc and fc.concept and fc.concept.reference:
                concept_result["has_value"] = True
                concept_result["shape"] = list(fc.concept.reference.shape)
                try:
                    data_str = json.dumps(fc.concept.reference.tensor)
                except (TypeError, ValueError):
                    data_str = str(fc.concept.reference.tensor)
                if len(data_str) > 5000:
                    data_str = data_str[:4997] + "..."
                concept_result["value"] = data_str
            run_state.result["final_concepts"].append(concept_result)
        
        run_state.status = "completed"
        run_state.completed_at = datetime.now()
        
        await broadcast_event(run_state.run_id, {
            "event": "run:completed",
            "run_id": run_state.run_id,
            "result": run_state.result
        })
        
    except Exception as e:
        logging.exception(f"Resumed run {run_state.run_id} failed: {e}")
        run_state.status = "failed"
        run_state.error = str(e)
        run_state.completed_at = datetime.now()
        
        await broadcast_event(run_state.run_id, {
            "event": "run:failed",
            "run_id": run_state.run_id,
            "error": str(e)
        })
    finally:
        if run_log_handler:
            logging.info(f"Run {run_state.run_id} log file saved to: {run_dir}")
            run_log_handler.close()
            logging.getLogger().removeHandler(run_log_handler)

