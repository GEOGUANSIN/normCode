"""
Project registry management service.

Handles persistent storage of known projects in ~/.normcode-canvas/project-registry.json.
This allows the app to remember and list all projects the user has worked with.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from schemas.project_schemas import (
    ProjectConfig,
    RegisteredProject,
    ProjectRegistry,
    RecentProject,
    RecentProjectsConfig,
    PROJECT_REGISTRY_FILE,
    generate_project_id,
)

logger = logging.getLogger(__name__)


def get_app_data_dir() -> Path:
    """Get the application data directory for storing recent projects etc."""
    # Use user's home directory / .normcode-canvas
    app_data = Path.home() / ".normcode-canvas"
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data


class ProjectRegistryService:
    """
    Service for managing the project registry.
    
    The registry tracks all known projects (not just recent ones) and stores
    metadata like last opened time, description, etc.
    """
    
    def __init__(self, app_data_dir: Optional[Path] = None):
        """
        Initialize the registry service.
        
        Args:
            app_data_dir: Optional override for app data directory (useful for testing)
        """
        self._app_data_dir = app_data_dir or get_app_data_dir()
        self._registry: Optional[ProjectRegistry] = None
    
    def _get_registry_path(self) -> Path:
        """Get path to project registry file."""
        return self._app_data_dir / PROJECT_REGISTRY_FILE
    
    def _load_registry(self) -> ProjectRegistry:
        """Load project registry from disk."""
        if self._registry is not None:
            return self._registry
        
        path = self._get_registry_path()
        if not path.exists():
            self._registry = ProjectRegistry()
            return self._registry
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._registry = ProjectRegistry(**data)
        except Exception as e:
            logger.warning(f"Failed to load project registry: {e}")
            self._registry = ProjectRegistry()
        
        return self._registry
    
    def _save_registry(self):
        """Save project registry to disk."""
        if self._registry is None:
            return
        
        path = self._get_registry_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._registry.model_dump(mode='json'), f, indent=2, default=str)
    
    def register_project(
        self, 
        project_dir: Path, 
        config_file: str, 
        config: ProjectConfig
    ):
        """
        Register a project in the registry.
        
        If the project already exists (by directory+config_file or by ID),
        it will be updated and moved to the front of the list.
        
        Args:
            project_dir: Project directory path
            config_file: Config filename within the directory
            config: The project configuration
        """
        registry = self._load_registry()
        
        project_dir_str = str(project_dir.absolute())
        
        # Remove if already exists (we'll re-add with updated info)
        registry.projects = [
            p for p in registry.projects 
            if not (p.directory == project_dir_str and p.config_file == config_file)
        ]
        
        # Also update by ID if same ID exists elsewhere (shouldn't happen but handle it)
        registry.projects = [p for p in registry.projects if p.id != config.id]
        
        # Add at the beginning (most recently opened)
        registry.projects.insert(0, RegisteredProject(
            id=config.id,
            name=config.name,
            directory=project_dir_str,
            config_file=config_file,
            description=config.description,
            created_at=config.created_at,
            last_opened=datetime.now(),
        ))
        
        self._save_registry()
    
    def get_project_by_id(self, project_id: str) -> Optional[RegisteredProject]:
        """Get a registered project by its ID."""
        registry = self._load_registry()
        for project in registry.projects:
            if project.id == project_id:
                return project
        return None
    
    def get_projects_in_directory(self, directory: str) -> List[RegisteredProject]:
        """Get all registered projects in a specific directory."""
        registry = self._load_registry()
        dir_path = str(Path(directory).absolute())
        return [p for p in registry.projects if p.directory == dir_path]
    
    def get_all_projects(self) -> List[RegisteredProject]:
        """
        Get all registered projects.
        
        Also validates that projects still exist on disk and removes any that don't.
        """
        registry = self._load_registry()
        
        # Validate that projects still exist
        valid_projects = []
        for project in registry.projects:
            config_path = Path(project.directory) / project.config_file
            if config_path.exists():
                valid_projects.append(project)
        
        # Update registry if we removed any invalid projects
        if len(valid_projects) != len(registry.projects):
            registry.projects = valid_projects
            self._save_registry()
        
        return valid_projects
    
    def get_recent_projects(self, limit: int = 10) -> List[RegisteredProject]:
        """Get most recently opened projects."""
        all_projects = self.get_all_projects()
        # Sort by last_opened (most recent first)
        sorted_projects = sorted(
            all_projects, 
            key=lambda p: p.last_opened or datetime.min, 
            reverse=True
        )
        return sorted_projects[:limit]
    
    def remove_project(self, project_id: str):
        """Remove a project from the registry (does not delete files)."""
        registry = self._load_registry()
        registry.projects = [p for p in registry.projects if p.id != project_id]
        self._save_registry()
    
    def clear_registry(self):
        """Clear the entire project registry."""
        self._registry = ProjectRegistry()
        self._save_registry()
    
    def migrate_recent_projects(self, find_project_configs_fn, open_project_fn, close_project_fn):
        """
        Migrate legacy recent-projects.json to new registry format.
        
        Args:
            find_project_configs_fn: Function to find project configs in a directory
            open_project_fn: Function to open a project
            close_project_fn: Function to close a project
        """
        legacy_path = self._app_data_dir / "recent-projects.json"
        if not legacy_path.exists():
            return
        
        try:
            with open(legacy_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            legacy_config = RecentProjectsConfig(**data)
            
            for recent in legacy_config.projects:
                # Try to open and register each legacy project
                try:
                    project_dir = Path(recent.path)
                    if project_dir.exists():
                        configs = find_project_configs_fn(project_dir)
                        if configs:
                            open_project_fn(project_path=recent.path, config_file=configs[0])
                            close_project_fn()
                except Exception as e:
                    logger.warning(f"Failed to migrate legacy project {recent.path}: {e}")
            
            # Rename legacy file to indicate migration
            legacy_path.rename(legacy_path.with_suffix('.json.migrated'))
            logger.info("Migrated legacy recent projects to new registry")
            
        except Exception as e:
            logger.warning(f"Failed to migrate legacy projects: {e}")

