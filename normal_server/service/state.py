"""
Run State Management

Tracks the state of active and historical runs.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Set, TYPE_CHECKING

from .schemas import RunStatus

if TYPE_CHECKING:
    from runner import PlanConfig

logger = logging.getLogger(__name__)


class RunState:
    """Tracks the state of an active run."""
    
    def __init__(self, run_id: str, plan_id: str, config: "PlanConfig"):
        self.run_id = run_id
        self.plan_id = plan_id
        self.config = config
        self.status = "pending"
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.orchestrator = None
        self._task: Optional[asyncio.Task] = None
        
        # Event queue for SSE streaming
        self._event_queues: List[asyncio.Queue] = []
        self._node_statuses: Dict[str, str] = {}  # flow_index -> status
        
        # Execution control for pause/resume/step
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused by default
        self._step_mode = False  # Single-step mode
        self._step_requested = False  # Step once then pause
        self._stop_requested = False  # Graceful stop request
        
        # IDE-level debugging features
        self.breakpoints: Set[str] = set()  # flow_indices with breakpoints
        self._run_to_target: Optional[str] = None  # Run until this flow_index
        self.current_inference: Optional[str] = None  # Currently executing inference
        
        # Progress tracking (cached for easy access)
        self._completed_count: int = 0
        self._total_count: int = 0
        self._cycle_count: int = 0
        
        # Execution logs for debugging
        self.logs: List[Dict[str, Any]] = []
    
    def request_pause(self):
        """Pause execution at next opportunity."""
        self._pause_event.clear()
        self.status = "paused"
    
    def request_resume(self):
        """Resume paused execution."""
        self._pause_event.set()
        self._step_mode = False
        self.status = "running"
    
    def request_step(self):
        """Execute one inference then pause."""
        self._step_mode = True
        self._step_requested = True
        self._pause_event.set()  # Allow one step
        self.status = "stepping"
    
    def request_stop(self):
        """Request graceful stop."""
        self._stop_requested = True
        self._pause_event.set()  # Unblock if paused
        self.status = "stopping"
    
    async def wait_if_paused(self) -> bool:
        """Wait if execution is paused. Returns False if stop was requested."""
        await self._pause_event.wait()
        if self._stop_requested:
            return False
        return True
    
    def complete_step(self):
        """Called after completing one inference in step mode."""
        if self._step_mode and self._step_requested:
            self._step_requested = False
            self._pause_event.clear()  # Pause after step
            self.status = "paused"
    
    def add_event_subscriber(self, queue: asyncio.Queue):
        """Add a subscriber for execution events."""
        self._event_queues.append(queue)
    
    def remove_event_subscriber(self, queue: asyncio.Queue):
        """Remove an event subscriber."""
        if queue in self._event_queues:
            self._event_queues.remove(queue)
    
    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all subscribers and websocket connections."""
        from .globals import broadcast_event
        
        event = {"event": event_type, "run_id": self.run_id, **data}
        
        # Send to SSE subscribers
        for queue in self._event_queues:
            try:
                await queue.put(event)
            except Exception:
                pass
        
        # Also broadcast via WebSocket
        await broadcast_event(self.run_id, event)
    
    def set_node_status(self, flow_index: str, status: str):
        """Update node status and prepare for emission."""
        self._node_statuses[flow_index] = status
    
    # =========================================================================
    # Progress Properties (for SSE streaming)
    # =========================================================================
    
    @property
    def completed_count(self) -> int:
        """Get count of completed inferences."""
        return self._completed_count
    
    @property
    def total_count(self) -> int:
        """Get total count of inferences."""
        return self._total_count
    
    @property
    def cycle_count(self) -> int:
        """Get current cycle count."""
        return self._cycle_count
    
    def update_progress(self, completed: int = None, total: int = None, cycle: int = None):
        """Update progress counters."""
        if completed is not None:
            self._completed_count = completed
        if total is not None:
            self._total_count = total
        if cycle is not None:
            self._cycle_count = cycle
    
    def sync_progress_from_orchestrator(self):
        """Sync progress from the orchestrator if available."""
        if not self.orchestrator:
            return
        
        try:
            bb = self.orchestrator.blackboard
            tracker = getattr(self.orchestrator, 'tracker', None)
            
            # Count completed vs total inferences
            completed = 0
            total = 0
            
            for item in self.orchestrator.waitlist.items:
                flow_index = item.inference_entry.flow_info.get('flow_index', '')
                if flow_index:
                    total += 1
                    status = bb.get_item_status(flow_index)
                    if status == 'completed':
                        completed += 1
            
            self._completed_count = completed
            self._total_count = total
            self._cycle_count = tracker.cycle_count if tracker else 0
        except Exception as e:
            logger.debug(f"Could not sync progress from orchestrator: {e}")
    
    # =========================================================================
    # Breakpoint Management
    # =========================================================================
    
    def add_breakpoint(self, flow_index: str):
        """Add a breakpoint at flow_index."""
        self.breakpoints.add(flow_index)
        logger.info(f"Breakpoint set at {flow_index}")
    
    def remove_breakpoint(self, flow_index: str):
        """Remove breakpoint from flow_index."""
        self.breakpoints.discard(flow_index)
        logger.info(f"Breakpoint cleared at {flow_index}")
    
    def clear_all_breakpoints(self):
        """Clear all breakpoints."""
        self.breakpoints.clear()
    
    def set_run_to_target(self, flow_index: str):
        """Set a one-time target to run to and pause."""
        self._run_to_target = flow_index
        logger.info(f"Run-to target set: {flow_index}")
    
    def check_breakpoint(self, flow_index: str) -> bool:
        """
        Check if execution should pause at this flow_index.
        
        Returns True if:
        - flow_index has a breakpoint, OR
        - flow_index is the run-to target (clears target after hit)
        """
        # Check run-to target first (one-time)
        if self._run_to_target and flow_index == self._run_to_target:
            self._run_to_target = None
            logger.info(f"Run-to target reached: {flow_index}")
            return True
        
        # Check breakpoints
        if flow_index in self.breakpoints:
            logger.info(f"Breakpoint hit: {flow_index}")
            return True
        
        return False
    
    # =========================================================================
    # Logging
    # =========================================================================
    
    def add_log(self, level: str, flow_index: str, message: str):
        """Add a log entry."""
        import time
        log_entry = {
            "level": level,
            "flow_index": flow_index,
            "message": message,
            "timestamp": time.time()
        }
        self.logs.append(log_entry)
        # Keep logs bounded
        if len(self.logs) > 1000:
            self.logs = self.logs[-500:]
    
    def get_logs(self, limit: int = 100, flow_index: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get execution logs, optionally filtered by flow_index."""
        logs = self.logs
        if flow_index:
            logs = [l for l in logs if l.get('flow_index') == flow_index or l.get('flow_index') == '']
        return logs[-limit:]
    
    # =========================================================================
    # Reference Data Access
    # =========================================================================
    
    def get_reference_data(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Get reference data for a concept from the orchestrator."""
        if not self.orchestrator or not self.orchestrator.concept_repo:
            return None
        
        try:
            concept_entry = self.orchestrator.concept_repo.get_concept(concept_name)
            if concept_entry and concept_entry.concept and concept_entry.concept.reference:
                ref = concept_entry.concept.reference
                return {
                    "concept_name": concept_name,
                    "has_reference": True,
                    "data": ref.tensor,
                    "shape": list(ref.shape) if hasattr(ref, 'shape') else [],
                    "axes": ref.axes if hasattr(ref, 'axes') else [],
                }
        except Exception as e:
            logger.warning(f"Failed to get reference for {concept_name}: {e}")
        
        return {"concept_name": concept_name, "has_reference": False}
    
    def get_all_reference_data(self) -> Dict[str, Dict[str, Any]]:
        """Get reference data for all concepts that have values."""
        if not self.orchestrator or not self.orchestrator.concept_repo:
            return {}
        
        result = {}
        try:
            for concept_entry in self.orchestrator.concept_repo.get_all_concepts():
                if concept_entry.concept and concept_entry.concept.reference:
                    ref = concept_entry.concept.reference
                    result[concept_entry.concept_name] = {
                        "has_reference": True,
                        "data": ref.tensor,
                        "shape": list(ref.shape) if hasattr(ref, 'shape') else [],
                        "axes": ref.axes if hasattr(ref, 'axes') else [],
                    }
        except Exception as e:
            logger.warning(f"Failed to get all references: {e}")
        
        return result
    
    def to_status(self) -> RunStatus:
        """Convert to RunStatus response model."""
        # Sync progress from orchestrator
        self.sync_progress_from_orchestrator()
        
        progress = {
            "completed_count": self._completed_count,
            "total_count": self._total_count,
            "cycle_count": self._cycle_count,
            "current_inference": self.current_inference,
        }
        
        return RunStatus(
            run_id=self.run_id,
            plan_id=self.plan_id,
            status=self.status,
            started_at=self.started_at.isoformat() if self.started_at else None,
            completed_at=self.completed_at.isoformat() if self.completed_at else None,
            progress=progress,
            error=self.error,
            breakpoints=list(self.breakpoints),
        )

