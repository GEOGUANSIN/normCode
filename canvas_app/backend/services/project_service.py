"""Project management service for project-based canvas."""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import os

from schemas.project_schemas import (
    ProjectConfig,
    RepositoryPaths,
    ExecutionSettings,
    RecentProject,
    RecentProjectsConfig,
    PROJECT_CONFIG_FILE,
    RECENT_PROJECTS_FILE,
)

logger = logging.getLogger(__name__)


def get_app_data_dir() -> Path:
    """Get the application data directory for storing recent projects etc."""
    # Use user's home directory / .normcode-canvas
    app_data = Path.home() / ".normcode-canvas"
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data


class ProjectService:
    """Service for managing NormCode Canvas projects."""
    
    def __init__(self):
        self.current_project_path: Optional[Path] = None
        self.current_config: Optional[ProjectConfig] = None
        self._app_data_dir = get_app_data_dir()
    
    @property
    def is_project_open(self) -> bool:
        """Check if a project is currently open."""
        return self.current_project_path is not None and self.current_config is not None
    
    def get_project_config_path(self, project_dir: Path) -> Path:
        """Get the path to the project config file."""
        return project_dir / PROJECT_CONFIG_FILE
    
    def project_exists(self, project_dir: Path) -> bool:
        """Check if a project config exists in the directory."""
        return self.get_project_config_path(project_dir).exists()
    
    def create_project(
        self,
        project_path: str,
        name: str,
        description: Optional[str] = None,
        concepts_path: str = "concepts.json",
        inferences_path: str = "inferences.json",
        inputs_path: Optional[str] = None,
        llm_model: str = "demo",
        max_cycles: int = 50,
        paradigm_dir: Optional[str] = None,
    ) -> ProjectConfig:
        """
        Create a new project configuration file.
        
        Args:
            project_path: Directory where to create the project
            name: Project name
            description: Optional description
            concepts_path: Relative path to concepts.json
            inferences_path: Relative path to inferences.json
            inputs_path: Optional relative path to inputs.json
            llm_model: LLM model to use
            max_cycles: Max execution cycles
            paradigm_dir: Optional paradigm directory
            
        Returns:
            ProjectConfig: The created project configuration
        """
        project_dir = Path(project_path)
        
        # Create directory if it doesn't exist
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project config
        config = ProjectConfig(
            name=name,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            repositories=RepositoryPaths(
                concepts=concepts_path,
                inferences=inferences_path,
                inputs=inputs_path,
            ),
            execution=ExecutionSettings(
                llm_model=llm_model,
                max_cycles=max_cycles,
                paradigm_dir=paradigm_dir,
            ),
        )
        
        # Save to file
        config_path = self.get_project_config_path(project_dir)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.info(f"Created project '{name}' at {project_dir}")
        
        # Set as current project
        self.current_project_path = project_dir
        self.current_config = config
        
        # Add to recent projects
        self._add_to_recent_projects(project_dir, name)
        
        return config
    
    def open_project(self, project_path: str) -> ProjectConfig:
        """
        Open an existing project.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            ProjectConfig: The loaded project configuration
            
        Raises:
            FileNotFoundError: If project config doesn't exist
        """
        project_dir = Path(project_path)
        config_path = self.get_project_config_path(project_dir)
        
        if not config_path.exists():
            raise FileNotFoundError(f"No project found at {project_dir}. Expected {PROJECT_CONFIG_FILE}")
        
        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = ProjectConfig(**data)
        
        # Auto-detect base_dir if not set
        if not config.execution.base_dir:
            base_dir = self._detect_base_dir(project_dir, config.repositories)
            if base_dir:
                config.execution.base_dir = str(base_dir)
        
        # Set as current project
        self.current_project_path = project_dir
        self.current_config = config
        
        # Update recent projects
        self._add_to_recent_projects(project_dir, config.name)
        
        logger.info(f"Opened project '{config.name}' from {project_dir}")
        
        return config
    
    def _detect_base_dir(self, project_dir: Path, repos: RepositoryPaths) -> Optional[Path]:
        """
        Auto-detect the base directory from repository paths.
        
        Args:
            project_dir: The project directory
            repos: Repository paths configuration
            
        Returns:
            Path to the detected base directory, or None
        """
        # Try to find common parent of repository files
        paths = []
        
        concepts_path = Path(repos.concepts)
        if concepts_path.is_absolute():
            paths.append(concepts_path.parent)
        else:
            paths.append(project_dir / repos.concepts)
        
        inferences_path = Path(repos.inferences)
        if inferences_path.is_absolute():
            paths.append(inferences_path.parent)
        else:
            paths.append(project_dir / repos.inferences)
        
        if not paths:
            return project_dir
        
        # Find common parent
        common = paths[0]
        for p in paths[1:]:
            # Find common ancestor
            while common not in p.parents and common != p:
                common = common.parent
        
        # Return the common parent (but not the root)
        if common and len(common.parts) > 1:
            return common
        
        return project_dir
    
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
        
        # Update config with provided values
        if execution is not None:
            self.current_config.execution = execution
        if breakpoints is not None:
            self.current_config.breakpoints = breakpoints
        if ui_preferences is not None:
            self.current_config.ui_preferences = ui_preferences
        
        self.current_config.updated_at = datetime.now()
        
        # Save to file
        config_path = self.get_project_config_path(self.current_project_path)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_config.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.info(f"Saved project '{self.current_config.name}'")
        
        return self.current_config
    
    def close_project(self):
        """Close the current project."""
        if self.is_project_open:
            logger.info(f"Closed project '{self.current_config.name}'")
        self.current_project_path = None
        self.current_config = None
    
    def get_current_project(self) -> Optional[ProjectConfig]:
        """Get the current project configuration."""
        return self.current_config
    
    def get_current_project_path(self) -> Optional[Path]:
        """Get the current project directory path."""
        return self.current_project_path
    
    def get_absolute_repo_paths(self) -> dict:
        """
        Get absolute paths to repository files for the current project.
        
        Returns:
            dict with 'concepts', 'inferences', 'inputs' (if set) keys
        """
        if not self.is_project_open:
            return {}
        
        base = self.current_project_path
        repos = self.current_config.repositories
        
        paths = {
            'concepts': str(base / repos.concepts),
            'inferences': str(base / repos.inferences),
            'base_dir': str(base),
        }
        
        if repos.inputs:
            paths['inputs'] = str(base / repos.inputs)
        
        return paths
    
    def check_repositories_exist(self) -> bool:
        """Check if the repository files exist for the current project."""
        if not self.is_project_open:
            return False
        
        paths = self.get_absolute_repo_paths()
        concepts_exist = Path(paths['concepts']).exists()
        inferences_exist = Path(paths['inferences']).exists()
        
        return concepts_exist and inferences_exist
    
    # Recent projects management
    
    def _get_recent_projects_path(self) -> Path:
        """Get path to recent projects file."""
        return self._app_data_dir / RECENT_PROJECTS_FILE
    
    def _load_recent_projects(self) -> RecentProjectsConfig:
        """Load recent projects list."""
        path = self._get_recent_projects_path()
        if not path.exists():
            return RecentProjectsConfig()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return RecentProjectsConfig(**data)
        except Exception as e:
            logger.warning(f"Failed to load recent projects: {e}")
            return RecentProjectsConfig()
    
    def _save_recent_projects(self, config: RecentProjectsConfig):
        """Save recent projects list."""
        path = self._get_recent_projects_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(mode='json'), f, indent=2, default=str)
    
    def _add_to_recent_projects(self, project_dir: Path, name: str):
        """Add a project to the recent projects list."""
        config = self._load_recent_projects()
        
        # Remove if already exists (we'll re-add at top)
        project_path_str = str(project_dir.absolute())
        config.projects = [p for p in config.projects if p.path != project_path_str]
        
        # Add at the beginning
        config.projects.insert(0, RecentProject(
            path=project_path_str,
            name=name,
            last_opened=datetime.now(),
        ))
        
        # Trim to max
        config.projects = config.projects[:config.max_recent]
        
        self._save_recent_projects(config)
    
    def get_recent_projects(self) -> List[RecentProject]:
        """Get list of recent projects."""
        config = self._load_recent_projects()
        
        # Filter out projects that no longer exist
        valid_projects = []
        for project in config.projects:
            if Path(project.path).exists() and self.project_exists(Path(project.path)):
                valid_projects.append(project)
        
        # Update if we removed any
        if len(valid_projects) != len(config.projects):
            config.projects = valid_projects
            self._save_recent_projects(config)
        
        return valid_projects
    
    def clear_recent_projects(self):
        """Clear the recent projects list."""
        config = RecentProjectsConfig()
        self._save_recent_projects(config)


# Global project service instance
project_service = ProjectService()
