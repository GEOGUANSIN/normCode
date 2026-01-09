"""
Worker Registry - Normalized worker management with flexible UI bindings.

This module provides a normalized worker registry that decouples workers from
their UI presentation. Key concepts:

- Worker: An ExecutionController with normalized state, independent of UI
- Panel: A UI view that can subscribe to any worker's events
- Binding: A connection between a panel and a worker
- Visibility: Whether a worker is visible (has panel bindings) or hidden

Design principles:
1. Workers are first-class entities with their own lifecycle
2. Panels subscribe to workers, not the other way around
3. Multiple panels can subscribe to the same worker
4. Workers can exist without any panel viewing them (hidden/background)
5. Any panel can switch which worker it's viewing at runtime

This replaces the rigid WorkerType → Panel routing with flexible bindings.
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from services.execution.controller import ExecutionController

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class WorkerVisibility(str, Enum):
    """Visibility state of a worker."""
    VISIBLE = "visible"      # Has at least one panel binding
    HIDDEN = "hidden"        # No panel bindings, runs in background
    MINIMIZED = "minimized"  # Collapsed/minimized view


class WorkerCategory(str, Enum):
    """
    Category of worker (informational, not routing).
    
    Unlike the old WorkerType, this doesn't determine UI routing.
    It's metadata about the worker's purpose.
    """
    PROJECT = "project"           # User NormCode project
    ASSISTANT = "assistant"       # AI assistant controller
    BACKGROUND = "background"     # Background/scheduled tasks
    EPHEMERAL = "ephemeral"       # Temporary workers (e.g., one-shot runs)


class PanelType(str, Enum):
    """Types of UI panels that can display workers."""
    MAIN = "main"           # Main execution panel
    CHAT = "chat"           # Chat/assistant panel
    SECONDARY = "secondary" # Secondary execution panel
    FLOATING = "floating"   # Floating/popup panel
    DEBUG = "debug"         # Debug/inspector panel


class WorkerStatus(str, Enum):
    """Execution status of a worker."""
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class WorkerState:
    """
    Normalized state of a worker.
    
    This captures the complete state of a worker independent of UI.
    """
    worker_id: str
    category: WorkerCategory
    status: WorkerStatus = WorkerStatus.IDLE
    visibility: WorkerVisibility = WorkerVisibility.HIDDEN
    
    # Identity
    name: str = ""
    project_id: Optional[str] = None
    project_path: Optional[str] = None
    
    # Execution state
    current_inference: Optional[str] = None
    completed_count: int = 0
    total_count: int = 0
    cycle_count: int = 0
    run_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    # Metadata (extensible)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for API/WebSocket."""
        return {
            "worker_id": self.worker_id,
            "category": self.category.value,
            "status": self.status.value,
            "visibility": self.visibility.value,
            "name": self.name,
            "project_id": self.project_id,
            "project_path": self.project_path,
            "current_inference": self.current_inference,
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "cycle_count": self.cycle_count,
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "metadata": self.metadata,
        }


@dataclass
class PanelBinding:
    """
    Represents a binding between a panel and a worker.
    
    A panel can only be bound to one worker at a time,
    but a worker can have multiple panel bindings.
    """
    panel_id: str
    panel_type: PanelType
    worker_id: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Panel-specific settings
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegisteredWorker:
    """
    A registered worker with its controller and state.
    """
    state: WorkerState
    controller: "ExecutionController"
    
    # Panel bindings (which panels are viewing this worker)
    bindings: Set[str] = field(default_factory=set)  # Set of panel_ids


# =============================================================================
# Worker Registry
# =============================================================================

class WorkerRegistry:
    """
    Centralized registry for all workers with flexible UI bindings.
    
    Key capabilities:
    - Register/unregister workers
    - Bind/unbind panels to workers
    - Query workers by various criteria
    - Emit events for state changes
    
    This replaces WorkerManager with a more flexible architecture.
    """
    
    def __init__(self):
        """Initialize the registry."""
        # Workers indexed by worker_id
        self._workers: Dict[str, RegisteredWorker] = {}
        
        # Panel bindings indexed by panel_id
        self._panel_bindings: Dict[str, PanelBinding] = {}
        
        # Event callbacks
        self._on_worker_state_change: List[Callable[[str, WorkerState], None]] = []
        self._on_binding_change: List[Callable[[str, Optional[str], Optional[str]], None]] = []
        self._on_worker_event: List[Callable[[str, str, Dict[str, Any]], None]] = []
    
    # =========================================================================
    # Worker Management
    # =========================================================================
    
    def register_worker(
        self,
        worker_id: str,
        controller: "ExecutionController",
        category: WorkerCategory,
        name: str = "",
        project_id: Optional[str] = None,
        project_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RegisteredWorker:
        """
        Register a new worker.
        
        Workers start as HIDDEN (no panel bindings).
        Bind a panel to make them VISIBLE.
        """
        if worker_id in self._workers:
            raise ValueError(f"Worker '{worker_id}' already registered")
        
        state = WorkerState(
            worker_id=worker_id,
            category=category,
            name=name or worker_id,
            project_id=project_id,
            project_path=project_path,
            visibility=WorkerVisibility.HIDDEN,
            metadata=metadata or {},
        )
        
        worker = RegisteredWorker(
            state=state,
            controller=controller,
        )
        
        self._workers[worker_id] = worker
        
        # Link controller's project_id
        controller.project_id = project_id
        
        logger.info(f"Registered worker: {worker_id} (category={category.value})")
        self._notify_state_change(worker_id, state)
        
        return worker
    
    def unregister_worker(self, worker_id: str) -> bool:
        """
        Unregister a worker.
        
        This also unbinds all panels from this worker.
        """
        if worker_id not in self._workers:
            return False
        
        # Unbind all panels viewing this worker
        panels_to_unbind = [
            panel_id for panel_id, binding in self._panel_bindings.items()
            if binding.worker_id == worker_id
        ]
        for panel_id in panels_to_unbind:
            self.unbind_panel(panel_id)
        
        del self._workers[worker_id]
        logger.info(f"Unregistered worker: {worker_id}")
        return True
    
    def get_worker(self, worker_id: str) -> Optional[RegisteredWorker]:
        """Get a worker by ID."""
        return self._workers.get(worker_id)
    
    def get_controller(self, worker_id: str) -> Optional["ExecutionController"]:
        """Get the controller for a worker."""
        worker = self._workers.get(worker_id)
        return worker.controller if worker else None
    
    def get_all_workers(self) -> List[RegisteredWorker]:
        """Get all registered workers."""
        return list(self._workers.values())
    
    # =========================================================================
    # State Updates
    # =========================================================================
    
    def update_status(self, worker_id: str, status: WorkerStatus):
        """Update a worker's execution status."""
        worker = self._workers.get(worker_id)
        if not worker:
            return
        
        worker.state.status = status
        worker.state.last_activity = datetime.now()
        
        if status == WorkerStatus.RUNNING:
            worker.state.started_at = datetime.now()
        
        self._notify_state_change(worker_id, worker.state)
    
    def update_progress(
        self,
        worker_id: str,
        current_inference: Optional[str] = None,
        completed_count: Optional[int] = None,
        total_count: Optional[int] = None,
        cycle_count: Optional[int] = None,
    ):
        """Update a worker's execution progress."""
        worker = self._workers.get(worker_id)
        if not worker:
            return
        
        if current_inference is not None:
            worker.state.current_inference = current_inference
        if completed_count is not None:
            worker.state.completed_count = completed_count
        if total_count is not None:
            worker.state.total_count = total_count
        if cycle_count is not None:
            worker.state.cycle_count = cycle_count
        
        worker.state.last_activity = datetime.now()
        self._notify_state_change(worker_id, worker.state)
    
    def set_run_id(self, worker_id: str, run_id: str):
        """Set the run_id for a worker."""
        worker = self._workers.get(worker_id)
        if worker:
            worker.state.run_id = run_id
            self._notify_state_change(worker_id, worker.state)
    
    # =========================================================================
    # Panel Bindings
    # =========================================================================
    
    def bind_panel(
        self,
        panel_id: str,
        panel_type: PanelType,
        worker_id: str,
        settings: Optional[Dict[str, Any]] = None,
    ) -> PanelBinding:
        """
        Bind a panel to a worker.
        
        A panel can only be bound to one worker at a time.
        If already bound, it will be unbound from the previous worker first.
        """
        # Check worker exists
        worker = self._workers.get(worker_id)
        if not worker:
            raise ValueError(f"Worker '{worker_id}' not found")
        
        # Get old binding if exists
        old_worker_id = None
        if panel_id in self._panel_bindings:
            old_worker_id = self._panel_bindings[panel_id].worker_id
            self.unbind_panel(panel_id)
        
        # Create new binding
        binding = PanelBinding(
            panel_id=panel_id,
            panel_type=panel_type,
            worker_id=worker_id,
            settings=settings or {},
        )
        
        self._panel_bindings[panel_id] = binding
        worker.bindings.add(panel_id)
        
        # Update visibility
        self._update_visibility(worker_id)
        
        logger.info(f"Bound panel '{panel_id}' ({panel_type.value}) to worker '{worker_id}'")
        self._notify_binding_change(panel_id, old_worker_id, worker_id)
        
        return binding
    
    def unbind_panel(self, panel_id: str) -> bool:
        """
        Unbind a panel from its worker.
        
        Returns True if was bound, False otherwise.
        """
        if panel_id not in self._panel_bindings:
            return False
        
        binding = self._panel_bindings.pop(panel_id)
        worker_id = binding.worker_id
        
        # Remove from worker's binding set
        worker = self._workers.get(worker_id)
        if worker:
            worker.bindings.discard(panel_id)
            self._update_visibility(worker_id)
        
        logger.info(f"Unbound panel '{panel_id}' from worker '{worker_id}'")
        self._notify_binding_change(panel_id, worker_id, None)
        
        return True
    
    def switch_panel_worker(
        self,
        panel_id: str,
        new_worker_id: str,
    ) -> PanelBinding:
        """
        Switch a panel to view a different worker.
        
        Convenience method that unbinds from current and binds to new.
        """
        # Get current panel type if exists
        current_binding = self._panel_bindings.get(panel_id)
        panel_type = current_binding.panel_type if current_binding else PanelType.MAIN
        settings = current_binding.settings if current_binding else {}
        
        return self.bind_panel(panel_id, panel_type, new_worker_id, settings)
    
    def get_panel_binding(self, panel_id: str) -> Optional[PanelBinding]:
        """Get the binding for a panel."""
        return self._panel_bindings.get(panel_id)
    
    def get_worker_for_panel(self, panel_id: str) -> Optional[RegisteredWorker]:
        """Get the worker bound to a panel."""
        binding = self._panel_bindings.get(panel_id)
        if binding:
            return self._workers.get(binding.worker_id)
        return None
    
    def get_controller_for_panel(self, panel_id: str) -> Optional["ExecutionController"]:
        """Get the controller for the worker bound to a panel."""
        worker = self.get_worker_for_panel(panel_id)
        return worker.controller if worker else None
    
    def get_panels_for_worker(self, worker_id: str) -> List[PanelBinding]:
        """Get all panels bound to a worker."""
        return [
            binding for binding in self._panel_bindings.values()
            if binding.worker_id == worker_id
        ]
    
    # =========================================================================
    # Visibility Management
    # =========================================================================
    
    def _update_visibility(self, worker_id: str):
        """Update worker visibility based on bindings."""
        worker = self._workers.get(worker_id)
        if not worker:
            return
        
        old_visibility = worker.state.visibility
        new_visibility = (
            WorkerVisibility.VISIBLE if worker.bindings
            else WorkerVisibility.HIDDEN
        )
        
        if old_visibility != new_visibility:
            worker.state.visibility = new_visibility
            logger.debug(f"Worker '{worker_id}' visibility: {old_visibility} -> {new_visibility}")
            self._notify_state_change(worker_id, worker.state)
    
    def set_visibility(self, worker_id: str, visibility: WorkerVisibility):
        """Manually set worker visibility (e.g., for MINIMIZED state)."""
        worker = self._workers.get(worker_id)
        if worker:
            worker.state.visibility = visibility
            self._notify_state_change(worker_id, worker.state)
    
    # =========================================================================
    # Query Methods
    # =========================================================================
    
    def get_workers_by_category(self, category: WorkerCategory) -> List[RegisteredWorker]:
        """Get all workers of a specific category."""
        return [w for w in self._workers.values() if w.state.category == category]
    
    def get_visible_workers(self) -> List[RegisteredWorker]:
        """Get all visible workers (have panel bindings)."""
        return [
            w for w in self._workers.values()
            if w.state.visibility == WorkerVisibility.VISIBLE
        ]
    
    def get_hidden_workers(self) -> List[RegisteredWorker]:
        """Get all hidden workers (no panel bindings)."""
        return [
            w for w in self._workers.values()
            if w.state.visibility == WorkerVisibility.HIDDEN
        ]
    
    def get_running_workers(self) -> List[RegisteredWorker]:
        """Get all currently running workers."""
        return [
            w for w in self._workers.values()
            if w.state.status == WorkerStatus.RUNNING
        ]
    
    def get_worker_by_project(self, project_id: str) -> Optional[RegisteredWorker]:
        """Get the worker for a specific project."""
        for worker in self._workers.values():
            if worker.state.project_id == project_id:
                return worker
        return None
    
    def find_workers(
        self,
        category: Optional[WorkerCategory] = None,
        status: Optional[WorkerStatus] = None,
        visibility: Optional[WorkerVisibility] = None,
        project_id: Optional[str] = None,
    ) -> List[RegisteredWorker]:
        """Find workers matching criteria."""
        results = list(self._workers.values())
        
        if category is not None:
            results = [w for w in results if w.state.category == category]
        if status is not None:
            results = [w for w in results if w.state.status == status]
        if visibility is not None:
            results = [w for w in results if w.state.visibility == visibility]
        if project_id is not None:
            results = [w for w in results if w.state.project_id == project_id]
        
        return results
    
    # =========================================================================
    # Event Routing
    # =========================================================================
    
    def route_event(self, worker_id: str, event_type: str, data: Dict[str, Any]):
        """
        Route an event from a worker to its bound panels.
        
        This adds panel routing info to the event data.
        """
        worker = self._workers.get(worker_id)
        if not worker:
            return
        
        # Get all panels bound to this worker
        panel_ids = list(worker.bindings)
        panel_types = [
            self._panel_bindings[pid].panel_type.value
            for pid in panel_ids
            if pid in self._panel_bindings
        ]
        
        # Enrich event data with routing info
        enriched_data = {
            **data,
            "worker_id": worker_id,
            "worker_category": worker.state.category.value,
            "target_panels": panel_ids,
            "target_panel_types": panel_types,
        }
        
        # Notify listeners
        for callback in self._on_worker_event:
            try:
                callback(worker_id, event_type, enriched_data)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    def get_event_targets(self, worker_id: str) -> Dict[str, List[str]]:
        """
        Get event routing targets for a worker.
        
        Returns dict with panel_ids and panel_types.
        """
        worker = self._workers.get(worker_id)
        if not worker:
            return {"panel_ids": [], "panel_types": []}
        
        panel_ids = list(worker.bindings)
        panel_types = [
            self._panel_bindings[pid].panel_type.value
            for pid in panel_ids
            if pid in self._panel_bindings
        ]
        
        return {
            "panel_ids": panel_ids,
            "panel_types": panel_types,
        }
    
    # =========================================================================
    # Callbacks
    # =========================================================================
    
    def on_worker_state_change(self, callback: Callable[[str, WorkerState], None]):
        """Register callback for worker state changes."""
        self._on_worker_state_change.append(callback)
    
    def on_binding_change(self, callback: Callable[[str, Optional[str], Optional[str]], None]):
        """Register callback for binding changes (panel_id, old_worker, new_worker)."""
        self._on_binding_change.append(callback)
    
    def on_worker_event(self, callback: Callable[[str, str, Dict[str, Any]], None]):
        """Register callback for worker events (worker_id, event_type, data)."""
        self._on_worker_event.append(callback)
    
    def _notify_state_change(self, worker_id: str, state: WorkerState):
        """Notify listeners of state change."""
        for callback in self._on_worker_state_change:
            try:
                callback(worker_id, state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def _notify_binding_change(
        self,
        panel_id: str,
        old_worker: Optional[str],
        new_worker: Optional[str],
    ):
        """Notify listeners of binding change."""
        for callback in self._on_binding_change:
            try:
                callback(panel_id, old_worker, new_worker)
            except Exception as e:
                logger.error(f"Binding change callback error: {e}")
    
    # =========================================================================
    # Cleanup
    # =========================================================================
    
    async def stop_all_workers(self):
        """Stop all running workers."""
        for worker in self._workers.values():
            if worker.state.status == WorkerStatus.RUNNING:
                try:
                    await worker.controller.stop()
                    worker.state.status = WorkerStatus.STOPPED
                except Exception as e:
                    logger.error(f"Failed to stop worker {worker.state.worker_id}: {e}")
    
    async def stop_hidden_workers(self):
        """Stop all hidden workers (cleanup background tasks)."""
        for worker in self.get_hidden_workers():
            if worker.state.status == WorkerStatus.RUNNING:
                try:
                    await worker.controller.stop()
                    worker.state.status = WorkerStatus.STOPPED
                except Exception as e:
                    logger.error(f"Failed to stop hidden worker: {e}")
    
    def clear_all(self):
        """Clear all workers and bindings (for testing/reset)."""
        self._workers.clear()
        self._panel_bindings.clear()
    
    # =========================================================================
    # Serialization
    # =========================================================================
    
    def get_registry_state(self) -> Dict[str, Any]:
        """Get complete registry state for debugging/API."""
        return {
            "workers": {
                wid: {
                    "state": w.state.to_dict(),
                    "bindings": list(w.bindings),
                }
                for wid, w in self._workers.items()
            },
            "panel_bindings": {
                pid: {
                    "panel_type": b.panel_type.value,
                    "worker_id": b.worker_id,
                }
                for pid, b in self._panel_bindings.items()
            },
        }


# =============================================================================
# Global Instance
# =============================================================================

worker_registry = WorkerRegistry()


def get_worker_registry() -> WorkerRegistry:
    """Get the global WorkerRegistry instance."""
    return worker_registry

