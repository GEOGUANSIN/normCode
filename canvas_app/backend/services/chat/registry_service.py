"""
Controller Registry Service - Manages available chat controller projects.

Handles:
- Scanning for built-in controller projects in built_in_projects/
- Dynamic registration of custom controllers
- Controller discovery and lookup
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from schemas.chat_schemas import ControllerInfo

logger = logging.getLogger(__name__)


# =============================================================================
# Built-in Projects Directory
# =============================================================================

# Directory containing built-in controller projects
BUILT_IN_PROJECTS_DIR = Path(__file__).parent.parent.parent.parent / "built_in_projects"

# Legacy paths (for backward compatibility during migration)
LEGACY_COMPILER_DIR = Path(__file__).parent.parent.parent.parent / "compiler"


class ControllerRegistryService:
    """
    Service for managing available chat controller projects.
    
    A chat controller is any NormCode project that:
    1. Has chat paradigms (c_ChatRead, h_Response-c_ChatWrite, etc.)
    2. Can be loaded and executed
    3. Drives the conversation via ChatTool
    
    This service handles:
    - Scanning for built-in controllers in built_in_projects/
    - Registering custom controllers dynamically
    - Looking up controllers by ID
    """
    
    def __init__(self):
        """Initialize the controller registry service."""
        self._available_controllers: List[ControllerInfo] = []
        self._scanned = False
    
    # =========================================================================
    # Controller Scanning
    # =========================================================================
    
    def _find_project_config(self, project_dir: Path) -> Optional[Path]:
        """
        Find the project config file in a directory.
        
        Looks for *.normcode-canvas.json files.
        """
        config_files = list(project_dir.glob("*.normcode-canvas.json"))
        if config_files:
            return config_files[0]
        return None
    
    def _load_controller_from_dir(self, project_dir: Path) -> Optional[ControllerInfo]:
        """
        Load a controller from a project directory.
        
        Args:
            project_dir: Path to the project directory
            
        Returns:
            ControllerInfo if valid project found, None otherwise
        """
        config_path = self._find_project_config(project_dir)
        if not config_path:
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            project_id = config.get("id", project_dir.name)
            
            return ControllerInfo(
                project_id=project_id,
                name=config.get("name", project_dir.name),
                path=str(project_dir),
                config_file=config_path.name,
                description=config.get("description"),
                is_builtin=True,
            )
        except Exception as e:
            logger.warning(f"Failed to load controller from {project_dir}: {e}")
            return None
    
    def _scan_builtin_controllers(self) -> List[ControllerInfo]:
        """
        Scan for built-in controller projects.
        
        Scans built_in_projects/ directory for NormCode projects
        that can serve as chat controllers.
        """
        controllers = []
        
        # Add placeholder/demo controller (always available as fallback)
        controllers.append(ControllerInfo(
            project_id="placeholder",
            name="Demo Assistant",
            path="",  # No actual path - virtual controller
            config_file=None,
            description="Helpful demo responses about NormCode (no execution)",
            is_builtin=True,
        ))
        
        # Scan built_in_projects directory
        if BUILT_IN_PROJECTS_DIR.exists():
            for project_dir in BUILT_IN_PROJECTS_DIR.iterdir():
                if project_dir.is_dir():
                    controller = self._load_controller_from_dir(project_dir)
                    if controller:
                        controllers.append(controller)
                        logger.debug(f"Found built-in controller: {controller.project_id} at {project_dir}")
        else:
            logger.debug(f"Built-in projects directory not found: {BUILT_IN_PROJECTS_DIR}")
        
        # Check legacy compiler location for backward compatibility
        if LEGACY_COMPILER_DIR.exists():
            controller = self._load_controller_from_dir(LEGACY_COMPILER_DIR)
            if controller:
                # Check if we already have this ID
                existing_ids = {c.project_id for c in controllers}
                if controller.project_id not in existing_ids:
                    controllers.append(controller)
                    logger.debug(f"Found legacy controller: {controller.project_id}")
        
        return controllers
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def get_available_controllers(self, refresh: bool = False) -> List[ControllerInfo]:
        """
        Get list of available chat controller projects.
        
        Args:
            refresh: Force rescan of available controllers
            
        Returns:
            List of ControllerInfo objects
        """
        if not self._scanned or refresh:
            self._available_controllers = self._scan_builtin_controllers()
            self._scanned = True
        
        return self._available_controllers.copy()
    
    def get_controller(self, controller_id: str) -> Optional[ControllerInfo]:
        """
        Get a controller by ID.
        
        Args:
            controller_id: The controller's project ID
            
        Returns:
            ControllerInfo if found, None otherwise
        """
        # Ensure controllers are scanned
        if not self._scanned:
            self.get_available_controllers()
        
        for controller in self._available_controllers:
            if controller.project_id == controller_id:
                return controller
        
        return None
    
    def register_controller(
        self,
        project_id: str,
        name: str,
        path: str,
        config_file: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ControllerInfo:
        """
        Register a new chat controller project.
        
        Args:
            project_id: Unique identifier for the controller
            name: Display name
            path: Path to the project directory
            config_file: Config file name (if any)
            description: Optional description
            
        Returns:
            The registered ControllerInfo
        """
        info = ControllerInfo(
            project_id=project_id,
            name=name,
            path=path,
            config_file=config_file,
            description=description,
            is_builtin=False,
        )
        
        # Remove existing with same ID
        self._available_controllers = [
            c for c in self._available_controllers 
            if c.project_id != project_id
        ]
        self._available_controllers.append(info)
        
        logger.info(f"Registered controller: {project_id} at {path}")
        
        return info
    
    def unregister_controller(self, project_id: str) -> bool:
        """
        Unregister a controller by ID.
        
        Built-in controllers cannot be unregistered.
        
        Args:
            project_id: The controller's project ID
            
        Returns:
            True if unregistered, False if not found or is builtin
        """
        original_count = len(self._available_controllers)
        
        self._available_controllers = [
            c for c in self._available_controllers 
            if c.project_id != project_id or c.is_builtin
        ]
        
        return len(self._available_controllers) < original_count
    
    def get_default_controller_id(self) -> Optional[str]:
        """
        Get the ID of the default controller.
        
        Prefers 'canvas-assistant' as default, falls back to first non-placeholder.
        
        Returns:
            The default controller ID, or None if no controllers available
        """
        controllers = self.get_available_controllers()
        if not controllers:
            return None
        
        # Prefer canvas-assistant as default
        for c in controllers:
            if c.project_id == "canvas-assistant":
                return c.project_id
        
        # Fall back to first non-placeholder controller
        for c in controllers:
            if c.project_id != "placeholder":
                return c.project_id
        
        # Last resort: placeholder
        return controllers[0].project_id
