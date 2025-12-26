"""
Multi-project tab state management service.

Handles the state for having multiple projects open as "tabs" in the UI,
tracking which project is active, and switching between them.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict

from schemas.project_schemas import (
    ProjectConfig,
    OpenProjectInstance,
)

logger = logging.getLogger(__name__)


class ProjectTabsService:
    """
    Service for managing multiple open project instances (tabs).
    
    This is UI-level state that tracks which projects are currently open
    and which one is active. Each project tab has its own execution state.
    """
    
    def __init__(self):
        """Initialize the tabs service."""
        self._open_projects: Dict[str, OpenProjectInstance] = {}  # project_id -> instance
        self._active_project_id: Optional[str] = None  # Currently focused project
    
    @property
    def active_project_id(self) -> Optional[str]:
        """Get the ID of the currently active project."""
        return self._active_project_id
    
    @property
    def has_open_projects(self) -> bool:
        """Check if there are any open project tabs."""
        return len(self._open_projects) > 0
    
    def is_project_open(self, project_id: str) -> bool:
        """Check if a specific project is currently open as a tab."""
        return project_id in self._open_projects
    
    def add_project_tab(
        self,
        project_id: str,
        name: str,
        directory: str,
        config_file: str,
        config: ProjectConfig,
        repositories_exist: bool = False,
        make_active: bool = True,
        is_read_only: bool = False,
    ) -> OpenProjectInstance:
        """
        Add a new project tab.
        
        If the project is already open, returns the existing instance.
        
        Args:
            project_id: Unique project ID
            name: Project name
            directory: Absolute path to project directory
            config_file: Config filename
            config: Project configuration
            repositories_exist: Whether repository files exist
            make_active: Whether to switch to this tab
            is_read_only: Whether the project is read-only
            
        Returns:
            OpenProjectInstance for the tab
        """
        # Check if already open
        if project_id in self._open_projects:
            instance = self._open_projects[project_id]
            if make_active:
                self._set_active(project_id)
            return instance
        
        # Create new instance
        instance = OpenProjectInstance(
            id=project_id,
            name=name,
            directory=directory,
            config_file=config_file,
            config=config,
            is_loaded=False,  # Not loaded until repositories are loaded
            repositories_exist=repositories_exist,
            is_active=make_active,
            is_read_only=is_read_only,
        )
        
        self._open_projects[project_id] = instance
        
        if make_active:
            self._set_active(project_id)
        
        logger.info(f"Added project tab '{name}' (id={project_id}, active={make_active})")
        
        return instance
    
    def _set_active(self, project_id: str):
        """Set a project as the active tab."""
        # Mark previous active as not active
        if self._active_project_id and self._active_project_id in self._open_projects:
            self._open_projects[self._active_project_id].is_active = False
        
        # Set new active
        self._active_project_id = project_id
        if project_id in self._open_projects:
            self._open_projects[project_id].is_active = True
    
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
        if project_id not in self._open_projects:
            raise KeyError(f"Project {project_id} is not currently open as a tab")
        
        self._set_active(project_id)
        instance = self._open_projects[project_id]
        
        logger.info(f"Switched to project tab '{instance.name}' (id={project_id})")
        
        return instance
    
    def close_project_tab(self, project_id: str) -> Optional[str]:
        """
        Close a specific project tab.
        
        Args:
            project_id: ID of the project to close
            
        Returns:
            The ID of the new active project (if any), or None if no tabs remain
        """
        if project_id not in self._open_projects:
            logger.warning(f"Cannot close project {project_id}: not open as a tab")
            return self._active_project_id
        
        closed_project = self._open_projects.pop(project_id)
        logger.info(f"Closed project tab '{closed_project.name}' (id={project_id})")
        
        # If we closed the active project, switch to another tab
        new_active_id = None
        if self._active_project_id == project_id:
            self._active_project_id = None
            
            # Switch to another open project if any
            if self._open_projects:
                # Pick the first available
                new_active_id = next(iter(self._open_projects.keys()))
                self._set_active(new_active_id)
        else:
            new_active_id = self._active_project_id
        
        return new_active_id
    
    def get_open_projects(self) -> List[OpenProjectInstance]:
        """Get all currently open project instances (tabs)."""
        return list(self._open_projects.values())
    
    def get_project(self, project_id: str) -> Optional[OpenProjectInstance]:
        """Get a specific open project by ID."""
        return self._open_projects.get(project_id)
    
    def get_active_project(self) -> Optional[OpenProjectInstance]:
        """Get the currently active project instance."""
        if self._active_project_id and self._active_project_id in self._open_projects:
            return self._open_projects[self._active_project_id]
        return None
    
    def update_loaded_state(self, project_id: str, is_loaded: bool):
        """
        Update the is_loaded state for an open project.
        
        Called after repositories are loaded/unloaded.
        """
        if project_id in self._open_projects:
            self._open_projects[project_id].is_loaded = is_loaded
    
    def update_project_config(self, project_id: str, config: ProjectConfig):
        """
        Update the config for an open project.
        
        Called after project config is modified.
        """
        if project_id in self._open_projects:
            self._open_projects[project_id].config = config
            self._open_projects[project_id].name = config.name
    
    def close_all_tabs(self):
        """Close all open project tabs."""
        self._open_projects.clear()
        self._active_project_id = None
        logger.info("Closed all project tabs")

