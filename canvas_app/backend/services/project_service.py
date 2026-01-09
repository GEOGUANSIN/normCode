"""
Project management service for project-based canvas.

This module provides the main ProjectService facade that delegates to
modular sub-services for specific functionality:
- ProjectConfigService: CRUD operations for project configs
- ProjectRegistryService: Persistent registry of known projects
- ProjectTabsService: Multi-project tab state management

For backwards compatibility, this module exports the same API as before.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple

from schemas.project_schemas import (
    ProjectConfig,
    RepositoryPaths,
    ExecutionSettings,
    RegisteredProject,
    ProjectRegistry,
    OpenProjectInstance,
    PROJECT_CONFIG_SUFFIX,
    LEGACY_PROJECT_CONFIG_FILE,
    PROJECT_REGISTRY_FILE,
    get_project_config_filename,
    generate_project_id,
)

# Import from modular sub-services
from .project.discovery import (
    SKIP_DIRS,
    MAX_SEARCH_DEPTH,
    DiscoveredPaths,
    discover_files_recursive,
    discover_paradigm_directories,
    discover_project_paths,
)
from .project.config_service import ProjectConfigService
from .project.registry_service import ProjectRegistryService, get_app_data_dir
from .project.tabs_service import ProjectTabsService

logger = logging.getLogger(__name__)

# Re-export for backwards compatibility
__all__ = [
    'ProjectService',
    'project_service',
    # Discovery exports
    'SKIP_DIRS',
    'MAX_SEARCH_DEPTH',
    'DiscoveredPaths',
    'discover_files_recursive',
    'discover_paradigm_directories',
    'discover_project_paths',
    'get_app_data_dir',
]


class ProjectService:
    """
    Service for managing NormCode Canvas projects.
    
    This is a facade that coordinates between:
    - ProjectConfigService: Project config file operations
    - ProjectRegistryService: Global project registry
    - ProjectTabsService: Multi-tab UI state
    
    The API is maintained for backwards compatibility.
    """
    
    def __init__(self):
        # Sub-services
        self._config_service = ProjectConfigService()
        self._registry_service = ProjectRegistryService()
        self._tabs_service = ProjectTabsService()
        
        # Current project state (for backwards compatibility)
        self.current_project_path: Optional[Path] = None
        self.current_config: Optional[ProjectConfig] = None
        self.current_config_file: Optional[str] = None
    
    @property
    def is_project_open(self) -> bool:
        """Check if a project is currently open."""
        return self.current_project_path is not None and self.current_config is not None
    
    # =========================================================================
    # Config Service Delegation
    # =========================================================================
    
    def get_project_config_path(
        self, 
        project_dir: Path, 
        config_file: Optional[str] = None
    ) -> Path:
        """Get the path to a project config file."""
        return self._config_service.get_project_config_path(project_dir, config_file)
    
    def find_project_configs(self, project_dir: Path) -> List[str]:
        """Find all project config files in a directory."""
        return self._config_service.find_project_configs(project_dir)
    
    def project_exists(
        self, 
        project_dir: Path, 
        config_file: Optional[str] = None
    ) -> bool:
        """Check if a project config exists in the directory."""
        return self._config_service.project_exists(project_dir, config_file)
    
    def create_project(
        self,
        project_path: str,
        name: str,
        description: Optional[str] = None,
        concepts_path: Optional[str] = None,
        inferences_path: Optional[str] = None,
        inputs_path: Optional[str] = None,
        llm_model: str = "demo",
        max_cycles: int = 50,
        paradigm_dir: Optional[str] = None,
        auto_discover: bool = True,
    ) -> Tuple[ProjectConfig, str]:
        """
        Create a new project configuration file.
        
        Args:
            project_path: Directory where to create the project
            name: Project name
            description: Optional description
            concepts_path: Relative path to concepts.json (auto-discovered if None)
            inferences_path: Relative path to inferences.json (auto-discovered if None)
            inputs_path: Optional relative path to inputs.json (auto-discovered if None)
            llm_model: LLM model to use
            max_cycles: Max execution cycles
            paradigm_dir: Optional paradigm directory (auto-discovered if None)
            auto_discover: Whether to auto-discover paths if not provided
            
        Returns:
            Tuple of (ProjectConfig, config_filename)
        """
        config, config_filename, project_dir = self._config_service.create_project(
            project_path=project_path,
            name=name,
            description=description,
            concepts_path=concepts_path,
            inferences_path=inferences_path,
            inputs_path=inputs_path,
            llm_model=llm_model,
            max_cycles=max_cycles,
            paradigm_dir=paradigm_dir,
            auto_discover=auto_discover,
        )
        
        # Set as current project
        self.current_project_path = project_dir
        self.current_config = config
        self.current_config_file = config_filename
        
        # Register the project
        self._registry_service.register_project(project_dir, config_filename, config)
        
        return config, config_filename
    
    def open_project(
        self, 
        project_path: Optional[str] = None,
        config_file: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[ProjectConfig, str]:
        """
        Open an existing project.
        
        Can open by:
        1. project_id - looks up in registry
        2. project_path + config_file - opens specific config
        3. project_path only - opens first/only config in directory
        
        Args:
            project_path: Path to project directory
            config_file: Specific config file name
            project_id: Project ID (from registry)
            
        Returns:
            Tuple of (ProjectConfig, config_filename)
            
        Raises:
            FileNotFoundError: If project config doesn't exist
            ValueError: If no valid project identification provided
        """
        # If opening by project ID, look up in registry
        if project_id:
            registered = self._registry_service.get_project_by_id(project_id)
            if not registered:
                raise FileNotFoundError(f"No project found with ID: {project_id}")
            project_path = registered.directory
            config_file = registered.config_file
        
        if not project_path:
            raise ValueError("Either project_path or project_id must be provided")
        
        project_dir = Path(project_path)
        
        # If no specific config file, find available configs
        if not config_file:
            configs = self._config_service.find_project_configs(project_dir)
            if not configs:
                raise FileNotFoundError(
                    f"No project config found at {project_dir}. "
                    f"Expected *{PROJECT_CONFIG_SUFFIX} or {LEGACY_PROJECT_CONFIG_FILE}"
                )
            config_file = configs[0]
        
        # Open the project
        config, _ = self._config_service.open_project(project_dir, config_file)
        
        # Set as current project
        self.current_project_path = project_dir
        self.current_config = config
        self.current_config_file = config_file
        
        # Register/update the project in registry
        self._registry_service.register_project(project_dir, config_file, config)
        
        logger.info(f"Opened project '{config.name}' from {project_dir}/{config_file}")
        
        return config, config_file
    
    def save_project(
        self,
        execution: Optional[ExecutionSettings] = None,
        breakpoints: Optional[List[str]] = None,
        ui_preferences: Optional[dict] = None,
    ) -> ProjectConfig:
        """
        Save the current project configuration.
        
        Args:
            execution: Optional updated execution settings
            breakpoints: Optional updated breakpoints list
            ui_preferences: Optional updated UI preferences
            
        Returns:
            ProjectConfig: The saved configuration
            
        Raises:
            RuntimeError: If no project is open
        """
        if not self.is_project_open:
            raise RuntimeError("No project is currently open")
        
        self.current_config = self._config_service.save_project(
            project_dir=self.current_project_path,
            config_file=self.current_config_file,
            config=self.current_config,
            execution=execution,
            breakpoints=breakpoints,
            ui_preferences=ui_preferences,
        )
        
        # Update tabs service if project is open as a tab
        if self._tabs_service.is_project_open(self.current_config.id):
            self._tabs_service.update_project_config(
                self.current_config.id, 
                self.current_config
            )
        
        return self.current_config
    
    def update_repositories(
        self,
        concepts: Optional[str] = None,
        inferences: Optional[str] = None,
        inputs: Optional[str] = None,
    ) -> ProjectConfig:
        """
        Update repository paths for the current project.
        
        Only updates paths that are provided (non-None).
        
        Args:
            concepts: New path to concepts file (relative to project dir)
            inferences: New path to inferences file (relative to project dir)
            inputs: New path to inputs file (relative to project dir, or None to remove)
            
        Returns:
            ProjectConfig: The updated configuration
            
        Raises:
            RuntimeError: If no project is open
        """
        if not self.is_project_open:
            raise RuntimeError("No project is currently open")
        
        self.current_config = self._config_service.update_repositories(
            project_dir=self.current_project_path,
            config_file=self.current_config_file,
            config=self.current_config,
            concepts=concepts,
            inferences=inferences,
            inputs=inputs,
        )
        
        return self.current_config
    
    def close_project(self):
        """Close the current project."""
        if self.is_project_open:
            logger.info(f"Closed project '{self.current_config.name}'")
        self.current_project_path = None
        self.current_config = None
        self.current_config_file = None
    
    def get_current_project(self) -> Optional[ProjectConfig]:
        """Get the current project configuration."""
        return self.current_config
    
    def get_current_project_path(self) -> Optional[Path]:
        """Get the current project directory path."""
        return self.current_project_path
    
    def get_current_config_file(self) -> Optional[str]:
        """Get the current project config filename."""
        return self.current_config_file
    
    def get_absolute_repo_paths(self) -> dict:
        """Get absolute paths to repository files for the current project."""
        if not self.is_project_open:
            return {}
        return self._config_service.get_absolute_repo_paths(
            self.current_project_path,
            self.current_config.repositories,
        )
    
    def check_repositories_exist(self) -> bool:
        """Check if the repository files exist for the current project."""
        if not self.is_project_open:
            return False
        return self._config_service.check_repositories_exist(
            self.current_project_path,
            self.current_config.repositories,
        )
    
    def discover_paths(self, directory: str) -> Dict[str, Optional[str]]:
        """Discover repository files and paradigm directory in a directory."""
        return self._config_service.discover_paths(directory)
    
    # =========================================================================
    # Registry Service Delegation
    # =========================================================================
    
    def get_project_by_id(self, project_id: str) -> Optional[RegisteredProject]:
        """Get a registered project by its ID."""
        return self._registry_service.get_project_by_id(project_id)
    
    def get_projects_in_directory(self, directory: str) -> List[RegisteredProject]:
        """Get all registered projects in a specific directory."""
        return self._registry_service.get_projects_in_directory(directory)
    
    def get_all_projects(self) -> List[RegisteredProject]:
        """Get all registered projects."""
        return self._registry_service.get_all_projects()
    
    def get_recent_projects(self, limit: int = 10) -> List[RegisteredProject]:
        """Get most recently opened projects."""
        return self._registry_service.get_recent_projects(limit=limit)
    
    def scan_directory_for_projects(
        self, 
        directory: str, 
        register: bool = True
    ) -> List[RegisteredProject]:
        """
        Scan a directory for project config files and optionally register them.
        
        Args:
            directory: Directory to scan
            register: Whether to register found projects
            
        Returns:
            List of found/registered projects
        """
        project_dir = Path(directory)
        found_configs = self._config_service.scan_directory_for_projects(directory)
        
        found_projects = []
        for config, config_file in found_configs:
            registered = RegisteredProject(
                id=config.id,
                name=config.name,
                directory=str(project_dir.absolute()),
                config_file=config_file,
                description=config.description,
                created_at=config.created_at,
            )
            
            if register:
                self._registry_service.register_project(project_dir, config_file, config)
            
            found_projects.append(registered)
        
        return found_projects
    
    def remove_project_from_registry(self, project_id: str):
        """Remove a project from the registry (does not delete files)."""
        self._registry_service.remove_project(project_id)
    
    def clear_registry(self):
        """Clear the entire project registry."""
        self._registry_service.clear_registry()
    
    def migrate_recent_projects(self):
        """Migrate legacy recent-projects.json to new registry format."""
        self._registry_service.migrate_recent_projects(
            find_project_configs_fn=self.find_project_configs,
            open_project_fn=self.open_project,
            close_project_fn=self.close_project,
        )
    
    # =========================================================================
    # Tabs Service Delegation (Multi-Project Support)
    # =========================================================================
    
    def open_project_as_tab(
        self, 
        project_path: Optional[str] = None,
        config_file: Optional[str] = None,
        project_id: Optional[str] = None,
        make_active: bool = True,
        is_read_only: bool = False,
    ) -> OpenProjectInstance:
        """
        Open a project as a new tab (keeping other tabs open).
        
        Args:
            project_path: Path to project directory
            config_file: Specific config file name
            project_id: Project ID (from registry)
            make_active: Whether to switch to this tab after opening
            is_read_only: Whether the project is read-only (view/execute only)
            
        Returns:
            OpenProjectInstance representing the opened tab
            
        Raises:
            FileNotFoundError: If project doesn't exist
        """
        # If there's a current project that's NOT in tabs, add it first
        if (self.current_config is not None and 
            self.current_project_path is not None and
            not self._tabs_service.is_project_open(self.current_config.id)):
            
            # Check if the project was already loaded (has ExecutionController with orchestrator)
            current_is_loaded = False
            try:
                from services.execution_service import execution_controller_registry
                if execution_controller_registry.has_controller(self.current_config.id):
                    from services.execution_service import get_execution_controller
                    controller = get_execution_controller(self.current_config.id)
                    current_is_loaded = controller.orchestrator is not None
            except Exception as e:
                logger.debug(f"Could not check loaded state: {e}")
            
            self._tabs_service.add_project_tab(
                project_id=self.current_config.id,
                name=self.current_config.name,
                directory=str(self.current_project_path.absolute()),
                config_file=self.current_config_file or "normcode-canvas.json",
                config=self.current_config,
                repositories_exist=self.check_repositories_exist(),
                make_active=False,
                is_read_only=False,
                is_loaded=current_is_loaded,
            )
            logger.info(f"Added existing project '{self.current_config.name}' to tabs (id={self.current_config.id}, is_loaded={current_is_loaded})")
        
        # Open the project using existing logic
        config, config_filename = self.open_project(
            project_path=project_path,
            config_file=config_file,
            project_id=project_id,
        )
        
        # Check if already open as a tab
        if self._tabs_service.is_project_open(config.id):
            if make_active:
                instance = self._tabs_service.switch_to_project(config.id)
                # Update "current" project references
                self.current_project_path = Path(instance.directory)
                self.current_config = instance.config
                self.current_config_file = instance.config_file
            return self._tabs_service.get_project(config.id)
        
        # Add as new tab
        instance = self._tabs_service.add_project_tab(
            project_id=config.id,
            name=config.name,
            directory=str(self.current_project_path.absolute()),
            config_file=config_filename,
            config=config,
            repositories_exist=self.check_repositories_exist(),
            make_active=make_active,
            is_read_only=is_read_only,
        )
        
        logger.info(f"Opened project '{config.name}' as tab (id={config.id}, active={make_active})")
        
        return instance
    
    def switch_to_project(self, project_id: str) -> OpenProjectInstance:
        """
        Switch to a different open project tab.
        
        Args:
            project_id: ID of the project to switch to
            
        Returns:
            OpenProjectInstance of the newly active project
            
        Raises:
            KeyError: If project is not currently open
        """
        instance = self._tabs_service.switch_to_project(project_id)
        
        # Update "current" project references
        self.current_project_path = Path(instance.directory)
        self.current_config = instance.config
        self.current_config_file = instance.config_file
        
        return instance
    
    def close_project_tab(self, project_id: str) -> Optional[str]:
        """
        Close a specific project tab.
        
        Args:
            project_id: ID of the project to close
            
        Returns:
            The ID of the new active project (if any), or None if no tabs remain
        """
        new_active_id = self._tabs_service.close_project_tab(project_id)
        
        # Update current project state
        if new_active_id:
            active_project = self._tabs_service.get_project(new_active_id)
            if active_project:
                self.current_project_path = Path(active_project.directory)
                self.current_config = active_project.config
                self.current_config_file = active_project.config_file
        else:
            self.current_project_path = None
            self.current_config = None
            self.current_config_file = None
        
        return new_active_id
    
    def get_open_projects(self) -> List[OpenProjectInstance]:
        """Get all currently open project instances (tabs)."""
        return self._tabs_service.get_open_projects()
    
    def get_active_project_id(self) -> Optional[str]:
        """Get the ID of the currently active project."""
        return self._tabs_service.active_project_id
    
    def get_active_project(self) -> Optional[OpenProjectInstance]:
        """Get the currently active project instance."""
        return self._tabs_service.get_active_project()
    
    def update_open_project_loaded_state(self, project_id: str, is_loaded: bool):
        """Update the is_loaded state for an open project."""
        self._tabs_service.update_loaded_state(project_id, is_loaded)
    
    def close_all_project_tabs(self):
        """Close all open project tabs."""
        self._tabs_service.close_all_tabs()
        self.current_project_path = None
        self.current_config = None
        self.current_config_file = None


# Global project service instance
project_service = ProjectService()
