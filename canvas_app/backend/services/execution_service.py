"""
Execution control service with Orchestrator integration for Phase 2.

This module provides the public API for execution control. The implementation
is organized into sub-modules in the `execution/` directory:

- execution/controller.py: Core ExecutionController class
- execution/log_handler.py: Orchestrator log capture and parsing
- execution/paradigm_tool.py: Custom paradigm loading
- execution/tool_injection.py: Tool monitoring and injection
- execution/checkpoint_service.py: Checkpoint management
- execution/value_service.py: Value override and dependency tracking
- execution/worker_registry.py: Normalized worker management (NEW)

This file provides backward-compatible exports and the ExecutionControllerRegistry.
The registry now uses WorkerRegistry internally for unified worker management.
"""

import logging
from typing import Optional, Dict, List

from schemas.execution_schemas import ExecutionStatus, NodeStatus, RunMode

# Import from modular sub-package
from services.execution import (
    ExecutionController,
    OrchestratorLogHandler,
    CustomParadigmTool,
    wrap_body_with_monitoring,
    inject_canvas_tools,
    CheckpointService,
    ValueService,
    # New worker registry
    WorkerRegistry,
    WorkerCategory,
    WorkerVisibility,
    PanelType,
    worker_registry,
    get_worker_registry,
)

logger = logging.getLogger(__name__)


class ExecutionControllerRegistry:
    """
    Registry for managing multiple ExecutionController instances.
    
    Enables multiple projects to execute simultaneously, each with its own
    controller maintaining independent execution state.
    
    This registry uses WorkerRegistry internally for unified worker management.
    It provides a facade for the common case of user project workers.
    """
    
    # Default panel ID for the main execution panel
    MAIN_PANEL_ID = "main_panel"
    
    def __init__(self):
        self._controllers: Dict[str, ExecutionController] = {}
        self._default_controller: Optional[ExecutionController] = None
        self._active_project_id: Optional[str] = None
    
    def get_controller(self, project_id: Optional[str] = None) -> ExecutionController:
        """
        Get an ExecutionController for a project.
        
        Args:
            project_id: Project ID. If None, returns the active controller.
            
        Returns:
            ExecutionController for the project
        """
        if project_id is None:
            project_id = self._active_project_id
        
        if project_id is None:
            # No project context - use/create default controller
            if self._default_controller is None:
                self._default_controller = ExecutionController()
            return self._default_controller
        
        if project_id not in self._controllers:
            # Create new controller for this project
            controller = ExecutionController(project_id=project_id)
            self._controllers[project_id] = controller
            logger.info(f"Created new ExecutionController for project {project_id}")
            
            # Register with WorkerRegistry (primary)
            self._register_with_worker_registry(project_id, controller)
            
            # Also register with legacy WorkerManager for backward compat
            self._register_with_worker_manager(project_id, controller)
        
        return self._controllers[project_id]
    
    def _register_with_worker_registry(self, project_id: str, controller: ExecutionController):
        """Register a controller with the global WorkerRegistry."""
        try:
            registry = get_worker_registry()
            worker_id = f"user-{project_id}"
            
            # Register the worker
            registry.register_worker(
                worker_id=worker_id,
                controller=controller,
                category=WorkerCategory.PROJECT,
                name=f"Project {project_id}",
                project_id=project_id,
            )
            logger.debug(f"Registered worker {worker_id} with WorkerRegistry")
        except Exception as e:
            logger.warning(f"Failed to register with WorkerRegistry: {e}")
    
    def _register_with_worker_manager(self, project_id: str, controller: ExecutionController):
        """Register a controller with the legacy WorkerManager (deprecated)."""
        try:
            from services.execution.worker_manager import get_worker_manager, WorkerType
            wm = get_worker_manager()
            wm.register_worker(
                worker_id=f"user-{project_id}",
                worker_type=WorkerType.USER_PROJECT,
                controller=controller,
                project_id=project_id,
            )
        except Exception as e:
            logger.warning(f"Failed to register with WorkerManager: {e}")
    
    def get_or_create(self, project_id: str) -> ExecutionController:
        """Get existing controller or create a new one for the project."""
        return self.get_controller(project_id)
    
    def set_active(self, project_id: Optional[str]):
        """
        Set the active project for the registry.
        
        This also binds the main panel to view this project's worker.
        
        Worker selection priority:
        1. Chat worker (chat-{project_id}) if it exists and has activity/graph_data
        2. User worker (user-{project_id}) otherwise
        
        This ensures that chat controller projects show the correct execution state.
        """
        self._active_project_id = project_id
        logger.info(f"Active project set to: {project_id}")
        
        if project_id:
            user_worker_id = f"user-{project_id}"
            chat_worker_id = f"chat-{project_id}"
            
            # Determine which worker to bind to
            try:
                registry = get_worker_registry()
                
                # Check if chat worker exists and has activity
                chat_worker = registry.get_worker(chat_worker_id)
                user_worker = registry.get_worker(user_worker_id)
                
                # Prefer chat worker if it has graph_data or activity
                prefer_chat = False
                if chat_worker and chat_worker.controller:
                    has_graph = getattr(chat_worker.controller, 'graph_data', None) is not None
                    has_activity = (
                        chat_worker.state.status in ('running', 'paused', 'stepping') or
                        chat_worker.state.completed_count > 0
                    )
                    prefer_chat = has_graph or has_activity
                    logger.debug(f"Chat worker {chat_worker_id}: has_graph={has_graph}, has_activity={has_activity}")
                
                # Select the appropriate worker
                if prefer_chat:
                    target_worker_id = chat_worker_id
                    logger.info(f"Preferring chat worker {chat_worker_id} for main panel (has graph/activity)")
                elif user_worker:
                    target_worker_id = user_worker_id
                else:
                    target_worker_id = None
                    logger.warning(f"No worker found for project {project_id}")
                
                # Bind main panel to the selected worker
                if target_worker_id and registry.get_worker(target_worker_id):
                    registry.bind_panel(
                        panel_id=self.MAIN_PANEL_ID,
                        panel_type=PanelType.MAIN,
                        worker_id=target_worker_id,
                    )
            except Exception as e:
                logger.warning(f"Failed to bind main panel to worker: {e}")
            
            # Also set as focused in legacy WorkerManager
            try:
                from services.execution.worker_manager import get_worker_manager
                wm = get_worker_manager()
                wm.set_focused_project(user_worker_id)  # Legacy uses user worker id
            except Exception as e:
                logger.warning(f"Failed to set focused project in WorkerManager: {e}")
    
    def get_active_project_id(self) -> Optional[str]:
        """Get the currently active project ID."""
        return self._active_project_id
    
    def get_active_controller(self) -> ExecutionController:
        """Get the controller for the active project."""
        return self.get_controller(self._active_project_id)
    
    def has_controller(self, project_id: str) -> bool:
        """Check if a controller exists for a project."""
        return project_id in self._controllers
    
    def remove_controller(self, project_id: str) -> bool:
        """
        Remove and clean up a controller for a project.
        
        Returns True if a controller was removed.
        """
        if project_id in self._controllers:
            controller = self._controllers.pop(project_id)
            worker_id = f"user-{project_id}"
            
            # Clean up the controller
            if controller._run_task:
                controller._run_task.cancel()
            
            # Unregister from WorkerRegistry
            try:
                registry = get_worker_registry()
                registry.unregister_worker(worker_id)
            except Exception as e:
                logger.warning(f"Failed to unregister from WorkerRegistry: {e}")
            
            # Unregister from legacy WorkerManager
            try:
                from services.execution.worker_manager import get_worker_manager
                wm = get_worker_manager()
                wm.unregister_worker(worker_id)
            except Exception as e:
                logger.warning(f"Failed to unregister from WorkerManager: {e}")
            
            logger.info(f"Removed ExecutionController for project {project_id}")
            return True
        return False
    
    def get_all_controllers(self) -> Dict[str, ExecutionController]:
        """Get all registered controllers."""
        return self._controllers.copy()
    
    def get_running_projects(self) -> List[str]:
        """Get list of project IDs that are currently running."""
        running = []
        for project_id, controller in self._controllers.items():
            if controller.status == ExecutionStatus.RUNNING:
                running.append(project_id)
        return running
    
    async def stop_all(self):
        """Stop execution on all controllers."""
        for project_id, controller in self._controllers.items():
            if controller.status == ExecutionStatus.RUNNING:
                await controller.stop()
                logger.info(f"Stopped execution for project {project_id}")
    
    # =========================================================================
    # WorkerRegistry Convenience Methods
    # =========================================================================
    
    def bind_panel_to_project(
        self,
        panel_id: str,
        panel_type: PanelType,
        project_id: str,
    ) -> bool:
        """
        Bind a panel to view a project's worker.
        
        This is the new flexible way to connect UI panels to workers.
        
        Args:
            panel_id: Unique ID for the panel
            panel_type: Type of panel (main, chat, secondary, etc.)
            project_id: Project ID to view
            
        Returns:
            True if binding succeeded
        """
        worker_id = f"user-{project_id}"
        try:
            registry = get_worker_registry()
            if not registry.get_worker(worker_id):
                # Ensure controller exists
                self.get_controller(project_id)
            
            registry.bind_panel(
                panel_id=panel_id,
                panel_type=panel_type,
                worker_id=worker_id,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to bind panel {panel_id} to project {project_id}: {e}")
            return False
    
    def unbind_panel(self, panel_id: str) -> bool:
        """
        Unbind a panel from its current worker.
        
        Args:
            panel_id: The panel to unbind
            
        Returns:
            True if was bound and is now unbound
        """
        try:
            registry = get_worker_registry()
            return registry.unbind_panel(panel_id)
        except Exception as e:
            logger.error(f"Failed to unbind panel {panel_id}: {e}")
            return False
    
    def get_controller_for_panel(self, panel_id: str) -> Optional[ExecutionController]:
        """
        Get the controller bound to a specific panel.
        
        Args:
            panel_id: The panel ID
            
        Returns:
            The ExecutionController, or None if panel not bound
        """
        try:
            registry = get_worker_registry()
            return registry.get_controller_for_panel(panel_id)
        except Exception as e:
            logger.warning(f"Failed to get controller for panel {panel_id}: {e}")
            return None
    
    def get_registry_state(self) -> Dict:
        """Get the complete WorkerRegistry state for debugging."""
        try:
            registry = get_worker_registry()
            return registry.get_registry_state()
        except Exception as e:
            logger.error(f"Failed to get registry state: {e}")
            return {}


# Global execution controller registry
execution_controller_registry = ExecutionControllerRegistry()


def get_execution_controller(project_id: Optional[str] = None) -> ExecutionController:
    """
    Get the ExecutionController for a project.
    
    This is the primary way to access execution controllers.
    If project_id is None, returns the controller for the active project.
    
    Args:
        project_id: Project ID, or None for the active project
        
    Returns:
        ExecutionController instance for the project
    """
    return execution_controller_registry.get_controller(project_id)


# Backward compatibility: Create a proxy object that delegates to the active controller
class _ExecutionControllerProxy:
    """
    Proxy that delegates all attribute access to the active ExecutionController.
    
    This maintains backward compatibility with code that imports execution_controller
    and uses it directly without specifying a project_id.
    """
    
    def __getattr__(self, name):
        # Delegate to active controller
        controller = execution_controller_registry.get_active_controller()
        return getattr(controller, name)
    
    def __setattr__(self, name, value):
        # Delegate to active controller
        controller = execution_controller_registry.get_active_controller()
        setattr(controller, name, value)


# Backward compatibility: execution_controller is a proxy to the active controller
execution_controller = _ExecutionControllerProxy()


# Re-export all public classes for backward compatibility
__all__ = [
    # Main classes
    'ExecutionController',
    'ExecutionControllerRegistry',
    
    # Worker Registry (NEW - preferred for flexible worker/panel binding)
    'WorkerRegistry',
    'WorkerCategory',
    'WorkerVisibility',
    'PanelType',
    'worker_registry',
    'get_worker_registry',
    
    # Helper classes
    'OrchestratorLogHandler',
    'CustomParadigmTool',
    'CheckpointService',
    'ValueService',
    
    # Functions
    'wrap_body_with_monitoring',
    'inject_canvas_tools',
    'get_execution_controller',
    
    # Instances
    'execution_controller_registry',
    'execution_controller',
    
    # Enums (re-exported from schemas)
    'ExecutionStatus',
    'NodeStatus',
    'RunMode',
]
