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

This file provides backward-compatible exports and the ExecutionControllerRegistry.
"""

import logging
from typing import Optional, Dict, List

from schemas.execution_schemas import ExecutionStatus, NodeStatus

# Import from modular sub-package
from services.execution import (
    ExecutionController,
    OrchestratorLogHandler,
    CustomParadigmTool,
    wrap_body_with_monitoring,
    inject_canvas_tools,
    CheckpointService,
    ValueService,
)

logger = logging.getLogger(__name__)


class ExecutionControllerRegistry:
    """
    Registry for managing multiple ExecutionController instances.
    
    Enables multiple projects to execute simultaneously, each with its own
    controller maintaining independent execution state.
    """
    
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
        
        return self._controllers[project_id]
    
    def get_or_create(self, project_id: str) -> ExecutionController:
        """Get existing controller or create a new one for the project."""
        return self.get_controller(project_id)
    
    def set_active(self, project_id: Optional[str]):
        """Set the active project for the registry."""
        self._active_project_id = project_id
        logger.info(f"Active project set to: {project_id}")
    
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
            # Clean up the controller
            if controller._run_task:
                controller._run_task.cancel()
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
]
