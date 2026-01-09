"""
Worker Manager - Unified management of all execution workers.

DEPRECATED: This module is deprecated. Use worker_registry.py instead.

The WorkerRegistry provides a more flexible architecture:
- Workers are normalized entities independent of UI
- Panels can be bound to any worker
- Multiple panels can view the same worker
- Workers can be hidden (no panel bindings)

This module is kept for backward compatibility but will be removed in a future version.

Original description:
This module provides centralized management for all execution workers in the system:
- User project workers (foreground, one per open project)
- Chat controller worker (background, runs the canvas assistant)
- Background workers (future: scheduled tasks, etc.)

Key concepts:
- Worker: An ExecutionController running a NormCode plan
- Focused worker: The user project currently being viewed/edited
- Background worker: Runs independently (e.g., chat controller)

This solves the multi-project execution management problem by:
1. Tracking all workers in one place
2. Categorizing workers by type
3. Properly linking chat tools to the focused user project
4. Supporting event routing based on worker type
"""

import warnings

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from services.execution.controller import ExecutionController

logger = logging.getLogger(__name__)


class WorkerType(str, Enum):
    """Types of execution workers."""
    USER_PROJECT = "user_project"  # User's NormCode project
    CHAT_CONTROLLER = "chat_controller"  # Chat assistant controller
    BACKGROUND = "background"  # Background tasks


class WorkerStatus(str, Enum):
    """Status of a worker."""
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class WorkerInfo:
    """Information about a registered worker."""
    worker_id: str
    worker_type: WorkerType
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    controller: Optional["ExecutionController"] = None
    status: WorkerStatus = WorkerStatus.IDLE
    is_focused: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkerManager:
    """
    Centralized manager for all execution workers.
    
    DEPRECATED: Use WorkerRegistry from worker_registry.py instead.
    
    The WorkerRegistry provides:
    - Flexible panel-to-worker bindings (not just "focused")
    - Multiple panels viewing the same worker
    - Hidden workers (running without UI)
    - Normalized worker state
    
    Responsibilities:
    - Register/unregister workers
    - Track worker status
    - Manage focused worker (for UI)
    - Provide correct controller for chat/canvas tool queries
    - Support event routing by worker type
    """
    
    def __init__(self):
        warnings.warn(
            "WorkerManager is deprecated. Use WorkerRegistry from worker_registry.py instead.",
            DeprecationWarning,
            stacklevel=2
        )
        """Initialize the worker manager."""
        self._workers: Dict[str, WorkerInfo] = {}
        self._focused_user_project: Optional[str] = None
        self._chat_controller_id: Optional[str] = None
        
        # Callbacks for worker state changes
        self._on_worker_change: List[Callable[[str, WorkerInfo], None]] = []
        self._on_focus_change: List[Callable[[Optional[str], Optional[str]], None]] = []
    
    # =========================================================================
    # Worker Registration
    # =========================================================================
    
    def register_worker(
        self,
        worker_id: str,
        worker_type: WorkerType,
        controller: "ExecutionController",
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkerInfo:
        """
        Register a new worker.
        
        Args:
            worker_id: Unique identifier for this worker
            worker_type: Type of worker (user_project, chat_controller, etc.)
            controller: The ExecutionController for this worker
            project_id: Optional project ID
            project_name: Optional project name
            metadata: Optional additional metadata
            
        Returns:
            The created WorkerInfo
        """
        info = WorkerInfo(
            worker_id=worker_id,
            worker_type=worker_type,
            project_id=project_id,
            project_name=project_name,
            controller=controller,
            status=WorkerStatus.READY,
            metadata=metadata or {},
        )
        
        self._workers[worker_id] = info
        
        # Track chat controller specially
        if worker_type == WorkerType.CHAT_CONTROLLER:
            self._chat_controller_id = worker_id
        
        logger.info(f"Registered worker: {worker_id} (type={worker_type.value})")
        self._notify_worker_change(worker_id, info)
        
        return info
    
    def unregister_worker(self, worker_id: str) -> bool:
        """
        Unregister a worker.
        
        Args:
            worker_id: The worker to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if worker_id not in self._workers:
            return False
        
        info = self._workers.pop(worker_id)
        
        # Update special tracking
        if worker_id == self._chat_controller_id:
            self._chat_controller_id = None
        if worker_id == self._focused_user_project:
            self._focused_user_project = None
            self._notify_focus_change(worker_id, None)
        
        logger.info(f"Unregistered worker: {worker_id}")
        return True
    
    def get_worker(self, worker_id: str) -> Optional[WorkerInfo]:
        """Get a worker by ID."""
        return self._workers.get(worker_id)
    
    def get_worker_controller(self, worker_id: str) -> Optional["ExecutionController"]:
        """Get the ExecutionController for a worker."""
        info = self._workers.get(worker_id)
        return info.controller if info else None
    
    # =========================================================================
    # Worker Status
    # =========================================================================
    
    def update_worker_status(self, worker_id: str, status: WorkerStatus):
        """Update a worker's status."""
        if worker_id in self._workers:
            self._workers[worker_id].status = status
            self._notify_worker_change(worker_id, self._workers[worker_id])
    
    def get_workers_by_type(self, worker_type: WorkerType) -> List[WorkerInfo]:
        """Get all workers of a specific type."""
        return [w for w in self._workers.values() if w.worker_type == worker_type]
    
    def get_running_workers(self) -> List[WorkerInfo]:
        """Get all currently running workers."""
        return [w for w in self._workers.values() if w.status == WorkerStatus.RUNNING]
    
    def get_all_workers(self) -> Dict[str, WorkerInfo]:
        """Get all registered workers."""
        return self._workers.copy()
    
    # =========================================================================
    # Focus Management (for UI)
    # =========================================================================
    
    def set_focused_project(self, worker_id: Optional[str]):
        """
        Set the focused user project.
        
        The focused project is the one the user is currently viewing/editing.
        Chat controller's canvas tool will query this project's state.
        
        Args:
            worker_id: Worker ID to focus, or None to clear focus
        """
        old_focus = self._focused_user_project
        
        # Clear old focus
        if old_focus and old_focus in self._workers:
            self._workers[old_focus].is_focused = False
        
        # Set new focus
        if worker_id and worker_id in self._workers:
            info = self._workers[worker_id]
            if info.worker_type == WorkerType.USER_PROJECT:
                info.is_focused = True
                self._focused_user_project = worker_id
            else:
                logger.warning(f"Cannot focus non-user-project worker: {worker_id}")
                self._focused_user_project = None
        else:
            self._focused_user_project = None
        
        if old_focus != self._focused_user_project:
            logger.info(f"Focus changed: {old_focus} -> {self._focused_user_project}")
            self._notify_focus_change(old_focus, self._focused_user_project)
    
    def get_focused_project_id(self) -> Optional[str]:
        """Get the ID of the focused user project worker."""
        return self._focused_user_project
    
    def get_focused_controller(self) -> Optional["ExecutionController"]:
        """
        Get the ExecutionController for the focused user project.
        
        This is what the chat controller's canvas tool should use
        to query/explain user project execution state.
        """
        if self._focused_user_project:
            info = self._workers.get(self._focused_user_project)
            if info:
                return info.controller
        return None
    
    # =========================================================================
    # Chat Controller Access
    # =========================================================================
    
    def get_chat_controller(self) -> Optional["ExecutionController"]:
        """Get the chat controller's ExecutionController."""
        if self._chat_controller_id:
            info = self._workers.get(self._chat_controller_id)
            if info:
                return info.controller
        return None
    
    def get_chat_controller_id(self) -> Optional[str]:
        """Get the chat controller's worker ID."""
        return self._chat_controller_id
    
    def is_chat_controller_running(self) -> bool:
        """Check if the chat controller is running."""
        if self._chat_controller_id:
            info = self._workers.get(self._chat_controller_id)
            return info and info.status == WorkerStatus.RUNNING
        return False
    
    # =========================================================================
    # Worker by Project
    # =========================================================================
    
    def get_worker_for_project(self, project_id: str) -> Optional[WorkerInfo]:
        """Get the worker associated with a specific project ID."""
        for info in self._workers.values():
            if info.project_id == project_id:
                return info
        return None
    
    def get_controller_for_project(self, project_id: str) -> Optional["ExecutionController"]:
        """Get the ExecutionController for a specific project ID."""
        info = self.get_worker_for_project(project_id)
        return info.controller if info else None
    
    # =========================================================================
    # Event Routing
    # =========================================================================
    
    def should_route_event_to_main(self, worker_id: str) -> bool:
        """Check if events from this worker should go to main execution UI."""
        info = self._workers.get(worker_id)
        if not info:
            return False
        return info.worker_type == WorkerType.USER_PROJECT and info.is_focused
    
    def should_route_event_to_chat(self, worker_id: str) -> bool:
        """Check if events from this worker should go to chat panel."""
        info = self._workers.get(worker_id)
        if not info:
            return False
        return info.worker_type == WorkerType.CHAT_CONTROLLER
    
    def get_event_routing(self, worker_id: str) -> Dict[str, bool]:
        """
        Get event routing configuration for a worker.
        
        Returns:
            Dict with 'main' and 'chat' booleans indicating where to route
        """
        return {
            "main": self.should_route_event_to_main(worker_id),
            "chat": self.should_route_event_to_chat(worker_id),
        }
    
    # =========================================================================
    # Callbacks
    # =========================================================================
    
    def on_worker_change(self, callback: Callable[[str, WorkerInfo], None]):
        """Register callback for worker state changes."""
        self._on_worker_change.append(callback)
    
    def on_focus_change(self, callback: Callable[[Optional[str], Optional[str]], None]):
        """Register callback for focus changes (old_id, new_id)."""
        self._on_focus_change.append(callback)
    
    def _notify_worker_change(self, worker_id: str, info: WorkerInfo):
        """Notify listeners of worker change."""
        for callback in self._on_worker_change:
            try:
                callback(worker_id, info)
            except Exception as e:
                logger.error(f"Worker change callback error: {e}")
    
    def _notify_focus_change(self, old_id: Optional[str], new_id: Optional[str]):
        """Notify listeners of focus change."""
        for callback in self._on_focus_change:
            try:
                callback(old_id, new_id)
            except Exception as e:
                logger.error(f"Focus change callback error: {e}")
    
    # =========================================================================
    # Cleanup
    # =========================================================================
    
    async def stop_all_workers(self):
        """Stop all running workers."""
        for worker_id, info in self._workers.items():
            if info.status == WorkerStatus.RUNNING and info.controller:
                try:
                    await info.controller.stop()
                    info.status = WorkerStatus.STOPPED
                    logger.info(f"Stopped worker: {worker_id}")
                except Exception as e:
                    logger.error(f"Failed to stop worker {worker_id}: {e}")
    
    def clear_all(self):
        """Clear all workers (for testing/reset)."""
        self._workers.clear()
        self._focused_user_project = None
        self._chat_controller_id = None


# =============================================================================
# Global Instance
# =============================================================================

worker_manager = WorkerManager()


def get_worker_manager() -> WorkerManager:
    """Get the global WorkerManager instance."""
    return worker_manager

