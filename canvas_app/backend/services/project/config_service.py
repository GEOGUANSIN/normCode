"""
Project configuration CRUD service.

Handles creating, reading, updating, and saving project configuration files.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple

from schemas.project_schemas import (
    ProjectConfig,
    RepositoryPaths,
    ExecutionSettings,
    PROJECT_CONFIG_SUFFIX,
    LEGACY_PROJECT_CONFIG_FILE,
    get_project_config_filename,
    generate_project_id,
)

from .discovery import discover_project_paths

logger = logging.getLogger(__name__)


def save_config_to_file(config: ProjectConfig, config_path: Path):
    """
    Save a project configuration to a file.
    
    Args:
        config: The configuration to save
        config_path: Path to the config file
    """
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config.model_dump(mode='json'), f, indent=2, default=str)


def load_config_from_file(config_path: Path) -> ProjectConfig:
    """
    Load a project configuration from a file.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        The loaded ProjectConfig
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Project config not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle legacy configs without ID
    if 'id' not in data:
        data['id'] = generate_project_id()
        # Save updated config with ID
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    return ProjectConfig(**data)


class ProjectConfigService:
    """
    Service for managing project configuration files.
    
    This handles the CRUD operations for project configs, including
    auto-discovery of repository paths and base directory detection.
    """
    
    def get_project_config_path(
        self, 
        project_dir: Path, 
        config_file: Optional[str] = None
    ) -> Path:
        """
        Get the path to a project config file.
        
        Args:
            project_dir: The project directory
            config_file: Specific config filename, or None to look for legacy file
        """
        if config_file:
            return project_dir / config_file
        # Legacy: single config file per directory
        return project_dir / LEGACY_PROJECT_CONFIG_FILE
    
    def find_project_configs(self, project_dir: Path) -> List[str]:
        """
        Find all project config files in a directory.
        
        Returns:
            List of config filenames
        """
        if not project_dir.exists():
            return []
        
        configs = []
        
        # Check for new-style named configs
        for f in project_dir.iterdir():
            if f.is_file() and f.name.endswith(PROJECT_CONFIG_SUFFIX):
                configs.append(f.name)
        
        # Check for legacy config (if not already captured by suffix match)
        legacy_path = project_dir / LEGACY_PROJECT_CONFIG_FILE
        if legacy_path.exists() and LEGACY_PROJECT_CONFIG_FILE not in configs:
            configs.append(LEGACY_PROJECT_CONFIG_FILE)
        
        return sorted(configs)
    
    def project_exists(
        self, 
        project_dir: Path, 
        config_file: Optional[str] = None
    ) -> bool:
        """Check if a project config exists in the directory."""
        if config_file:
            return self.get_project_config_path(project_dir, config_file).exists()
        # Check for any project config
        return len(self.find_project_configs(project_dir)) > 0
    
    def create_project(
        self,
        project_path: str,
        name: str,
        description: Optional[str] = None,
        concepts_path: Optional[str] = None,
        inferences_path: Optional[str] = None,
        inputs_path: Optional[str] = None,
        max_cycles: int = 50,
        auto_discover: bool = True,
    ) -> Tuple[ProjectConfig, str, Path]:
        """
        Create a new project configuration file.
        
        Agent-centric approach: Also creates a default agent config file.
        LLM model, paradigm_dir, and base_dir are configured per-agent in the .agent.json file.
        
        Args:
            project_path: Directory where to create the project
            name: Project name
            description: Optional description
            concepts_path: Relative path to concepts.json (auto-discovered if None)
            inferences_path: Relative path to inferences.json (auto-discovered if None)
            inputs_path: Optional relative path to inputs.json (auto-discovered if None)
            max_cycles: Max execution cycles
            auto_discover: Whether to auto-discover paths if not provided
            
        Returns:
            Tuple of (ProjectConfig, config_filename, project_dir)
        """
        project_dir = Path(project_path)
        
        # Create directory if it doesn't exist
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-discover paths if not provided
        if auto_discover:
            discovered = discover_project_paths(project_dir)
            
            # Use discovered paths as defaults (but explicit params take precedence)
            if concepts_path is None:
                concepts_path = discovered.concepts or "concepts.json"
            if inferences_path is None:
                inferences_path = discovered.inferences or "inferences.json"
            if inputs_path is None:
                inputs_path = discovered.inputs  # Can remain None
            # paradigm_dir is now part of agent config
            paradigm_dir = discovered.paradigm_dir  # Pass to agent config
        else:
            paradigm_dir = None
            # Use defaults if not auto-discovering
            concepts_path = concepts_path or "concepts.json"
            inferences_path = inferences_path or "inferences.json"
        
        # Generate config filename from project name
        config_filename = get_project_config_filename(name)
        
        # Check if this config already exists
        config_path = project_dir / config_filename
        if config_path.exists():
            # Append ID to make unique
            project_id = generate_project_id()
            base_name = config_filename.replace(PROJECT_CONFIG_SUFFIX, '')
            config_filename = f"{base_name}-{project_id}{PROJECT_CONFIG_SUFFIX}"
        
        # =====================================================================
        # Agent-Centric: Create default agent config file
        # All tool settings (LLM, paradigm, file_system) are in the agent config
        # =====================================================================
        from services.agent.project_config import project_agent_config_service
        from services.agent.config import get_agent_config_filename
        
        # Create the agent config file with discovered paradigm_dir
        agent_config, agent_config_path = project_agent_config_service.create_default_config(
            project_dir=project_dir,
            project_name=name,
            default_llm_model="demo",  # Default LLM model for new agents
            paradigm_dir=paradigm_dir,  # Pass discovered paradigm dir
        )
        
        # Get relative path to agent config
        agent_config_filename = agent_config_path.name
        
        logger.info(f"Created agent config: {agent_config_filename}")
        
        # Create project config with new ID
        project_id = generate_project_id()
        config = ProjectConfig(
            id=project_id,
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
                max_cycles=max_cycles,
                agent_config=agent_config_filename,  # Agent tools config
            ),
        )
        
        # Save to file
        config_path = project_dir / config_filename
        save_config_to_file(config, config_path)
        
        logger.info(f"Created project '{name}' at {project_dir}/{config_filename}")
        
        return config, config_filename, project_dir
    
    def open_project(
        self,
        project_dir: Path,
        config_file: str,
    ) -> Tuple[ProjectConfig, bool]:
        """
        Open an existing project configuration.
        
        This loads the config and auto-discovers/updates any missing paths.
        
        Args:
            project_dir: Project directory
            config_file: Config filename
            
        Returns:
            Tuple of (ProjectConfig, was_updated) - was_updated indicates if
            the config was modified and saved
        """
        config_path = project_dir / config_file
        config = load_config_from_file(config_path)
        
        # Auto-discover and fill in missing paths
        config_updated = False
        discovered = discover_project_paths(project_dir)
        
        # Check if concepts path exists, if not try discovered
        concepts_path = project_dir / config.repositories.concepts
        if not concepts_path.exists() and discovered.concepts:
            logger.info(f"Updating concepts path from '{config.repositories.concepts}' to discovered '{discovered.concepts}'")
            config.repositories.concepts = discovered.concepts
            config_updated = True
        
        # Check if inferences path exists, if not try discovered
        inferences_path = project_dir / config.repositories.inferences
        if not inferences_path.exists() and discovered.inferences:
            logger.info(f"Updating inferences path from '{config.repositories.inferences}' to discovered '{discovered.inferences}'")
            config.repositories.inferences = discovered.inferences
            config_updated = True
        
        # Check if inputs path exists (if set), if not try discovered
        if config.repositories.inputs:
            inputs_path = project_dir / config.repositories.inputs
            if not inputs_path.exists() and discovered.inputs:
                logger.info(f"Updating inputs path from '{config.repositories.inputs}' to discovered '{discovered.inputs}'")
                config.repositories.inputs = discovered.inputs
                config_updated = True
        elif discovered.inputs:
            # No inputs set, but we found some
            config.repositories.inputs = discovered.inputs
            config_updated = True
        
        # Note: paradigm_dir and base_dir are now configured per-agent in .agent.json
        # They are no longer stored in ExecutionSettings
        
        # Save updated config if we made changes
        if config_updated:
            config.updated_at = datetime.now()
            save_config_to_file(config, config_path)
            logger.info(f"Updated project config with discovered paths")
        
        return config, config_updated
    
    def _detect_base_dir(
        self, 
        project_dir: Path, 
        repos: RepositoryPaths
    ) -> Optional[Path]:
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
        project_dir: Path,
        config_file: str,
        config: ProjectConfig,
        execution: Optional[ExecutionSettings] = None,
        breakpoints: Optional[List[str]] = None,
        ui_preferences: Optional[dict] = None,
    ) -> ProjectConfig:
        """
        Save a project configuration.
        
        Args:
            project_dir: Project directory
            config_file: Config filename
            config: Current project config
            execution: Optional updated execution settings
            breakpoints: Optional updated breakpoints list
            ui_preferences: Optional updated UI preferences
            
        Returns:
            The saved ProjectConfig
        """
        # Update config with provided values
        if execution is not None:
            config.execution = execution
        if breakpoints is not None:
            config.breakpoints = breakpoints
        if ui_preferences is not None:
            config.ui_preferences = ui_preferences
        
        config.updated_at = datetime.now()
        
        # Save to file
        config_path = project_dir / config_file
        save_config_to_file(config, config_path)
        
        logger.info(f"Saved project '{config.name}'")
        
        return config
    
    def update_repositories(
        self,
        project_dir: Path,
        config_file: str,
        config: ProjectConfig,
        concepts: Optional[str] = None,
        inferences: Optional[str] = None,
        inputs: Optional[str] = None,
    ) -> ProjectConfig:
        """
        Update repository paths for a project.
        
        Only updates paths that are provided (non-None).
        
        Args:
            project_dir: Project directory
            config_file: Config filename
            config: Current project config
            concepts: New path to concepts file (relative to project dir)
            inferences: New path to inferences file (relative to project dir)
            inputs: New path to inputs file (relative to project dir, or None to remove)
            
        Returns:
            The updated ProjectConfig
        """
        # Update repository paths
        if concepts is not None:
            config.repositories.concepts = concepts
        if inferences is not None:
            config.repositories.inferences = inferences
        if inputs is not None:
            # Empty string means clear the inputs path
            config.repositories.inputs = inputs if inputs else None
        
        config.updated_at = datetime.now()
        
        # Save to file
        config_path = project_dir / config_file
        save_config_to_file(config, config_path)
        
        logger.info(f"Updated repository paths for project '{config.name}'")
        
        return config
    
    def get_absolute_repo_paths(
        self, 
        project_dir: Path, 
        repos: RepositoryPaths
    ) -> Dict[str, str]:
        """
        Get absolute paths to repository files.
        
        Args:
            project_dir: Project directory
            repos: Repository paths configuration
            
        Returns:
            Dict with 'concepts', 'inferences', 'inputs' (if set), 'base_dir' keys
        """
        paths = {
            'concepts': str(project_dir / repos.concepts),
            'inferences': str(project_dir / repos.inferences),
            'base_dir': str(project_dir),
        }
        
        if repos.inputs:
            paths['inputs'] = str(project_dir / repos.inputs)
        
        return paths
    
    def check_repositories_exist(
        self, 
        project_dir: Path, 
        repos: RepositoryPaths
    ) -> bool:
        """Check if the repository files exist."""
        paths = self.get_absolute_repo_paths(project_dir, repos)
        concepts_exist = Path(paths['concepts']).exists()
        inferences_exist = Path(paths['inferences']).exists()
        return concepts_exist and inferences_exist
    
    def discover_paths(self, directory: str) -> Dict[str, Optional[str]]:
        """
        Discover repository files and paradigm directory in a directory.
        
        This is a public method that can be called to preview what paths
        would be auto-discovered for a given directory.
        
        Args:
            directory: Directory to scan
            
        Returns:
            Dict with keys: concepts, inferences, inputs, paradigm_dir
        """
        project_dir = Path(directory)
        if not project_dir.exists():
            return {
                'concepts': None,
                'inferences': None,
                'inputs': None,
                'paradigm_dir': None,
            }
        
        discovered = discover_project_paths(project_dir)
        return discovered.to_dict()
    
    def scan_directory_for_projects(
        self, 
        directory: str,
    ) -> List[Tuple[ProjectConfig, str]]:
        """
        Scan a directory for project config files.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of (ProjectConfig, config_filename) tuples
        """
        project_dir = Path(directory)
        if not project_dir.exists():
            return []
        
        config_files = self.find_project_configs(project_dir)
        found_projects = []
        
        for config_file in config_files:
            try:
                config_path = project_dir / config_file
                config = load_config_from_file(config_path)
                found_projects.append((config, config_file))
            except Exception as e:
                logger.warning(f"Failed to load project config {config_file}: {e}")
        
        return found_projects

