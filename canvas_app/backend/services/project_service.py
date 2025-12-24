"""Project management service for project-based canvas."""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import os

from schemas.project_schemas import (
    ProjectConfig,
    RepositoryPaths,
    ExecutionSettings,
    RegisteredProject,
    ProjectRegistry,
    RecentProject,
    RecentProjectsConfig,
    PROJECT_CONFIG_SUFFIX,
    LEGACY_PROJECT_CONFIG_FILE,
    PROJECT_REGISTRY_FILE,
    get_project_config_filename,
    generate_project_id,
)

logger = logging.getLogger(__name__)

# Directories to skip during file discovery
SKIP_DIRS = {
    '.git', '.svn', '.hg', '__pycache__', 'node_modules', '.venv', 'venv',
    '.idea', '.vscode', '.cursor', 'dist', 'build', '.tox', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', 'egg-info', '.eggs', '.conda',
}

# Max depth for recursive file search
MAX_SEARCH_DEPTH = 5


def get_app_data_dir() -> Path:
    """Get the application data directory for storing recent projects etc."""
    # Use user's home directory / .normcode-canvas
    app_data = Path.home() / ".normcode-canvas"
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data


def discover_files_recursive(
    root_dir: Path,
    patterns: List[str],
    max_depth: int = MAX_SEARCH_DEPTH,
    skip_dirs: set = SKIP_DIRS,
) -> List[Path]:
    """
    Recursively search for files matching patterns within a directory.
    
    Args:
        root_dir: Directory to start search from
        patterns: List of glob patterns to match (e.g., ['*.concept.json', 'concepts.json'])
        max_depth: Maximum directory depth to search
        skip_dirs: Set of directory names to skip
        
    Returns:
        List of matching file paths, sorted by depth (shallower first)
    """
    found = []
    
    def _search(current_dir: Path, depth: int):
        if depth > max_depth:
            return
        
        try:
            for item in current_dir.iterdir():
                if item.is_file():
                    for pattern in patterns:
                        if item.match(pattern):
                            found.append(item)
                            break
                elif item.is_dir() and item.name not in skip_dirs:
                    _search(item, depth + 1)
        except PermissionError:
            pass  # Skip directories we can't access
    
    _search(root_dir, 0)
    
    # Sort by path depth (shallower = better), then alphabetically
    found.sort(key=lambda p: (len(p.relative_to(root_dir).parts), str(p)))
    return found


def discover_paradigm_directories(
    root_dir: Path,
    max_depth: int = MAX_SEARCH_DEPTH,
    skip_dirs: set = SKIP_DIRS,
) -> List[Path]:
    """
    Search for directories containing paradigm JSON files.
    
    Paradigm directories typically:
    - Are named 'paradigm' or 'paradigms'
    - OR contain files matching paradigm naming patterns (e.g., 'h_*-c_*.json', 'v_*-h_*.json')
    
    Args:
        root_dir: Directory to start search from
        max_depth: Maximum directory depth to search
        skip_dirs: Set of directory names to skip
        
    Returns:
        List of directory paths that appear to contain paradigms
    """
    found = []
    
    def _is_paradigm_file(filename: str) -> bool:
        """Check if a filename looks like a paradigm file."""
        name = filename.lower()
        # Common paradigm file patterns
        if name.endswith('.json'):
            # Pattern: h_Something-c_Something.json or v_Something-h_Something.json
            if ('-c_' in name and 'h_' in name) or ('-h_' in name and 'v_' in name):
                return True
            # Pattern: c_Something-o_Something.json
            if '-c_' in name and '-o_' in name:
                return True
        return False
    
    def _search(current_dir: Path, depth: int):
        if depth > max_depth:
            return
        
        try:
            # Check if this directory is a paradigm directory
            is_paradigm_dir = False
            
            # Check by name
            if current_dir.name.lower() in ('paradigm', 'paradigms'):
                is_paradigm_dir = True
            else:
                # Check if contains paradigm-like files
                paradigm_file_count = 0
                for item in current_dir.iterdir():
                    if item.is_file() and _is_paradigm_file(item.name):
                        paradigm_file_count += 1
                        if paradigm_file_count >= 2:  # At least 2 paradigm files
                            is_paradigm_dir = True
                            break
            
            if is_paradigm_dir:
                found.append(current_dir)
            
            # Continue searching subdirectories
            for item in current_dir.iterdir():
                if item.is_dir() and item.name not in skip_dirs:
                    _search(item, depth + 1)
                    
        except PermissionError:
            pass
    
    _search(root_dir, 0)
    
    # Sort by path depth (shallower = better)
    found.sort(key=lambda p: (len(p.relative_to(root_dir).parts), str(p)))
    return found


class DiscoveredPaths:
    """Container for auto-discovered repository paths."""
    
    def __init__(
        self,
        concepts: Optional[str] = None,
        inferences: Optional[str] = None,
        inputs: Optional[str] = None,
        paradigm_dir: Optional[str] = None,
    ):
        self.concepts = concepts
        self.inferences = inferences
        self.inputs = inputs
        self.paradigm_dir = paradigm_dir
    
    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            'concepts': self.concepts,
            'inferences': self.inferences,
            'inputs': self.inputs,
            'paradigm_dir': self.paradigm_dir,
        }
    
    def __repr__(self):
        return f"DiscoveredPaths({self.to_dict()})"


def discover_project_paths(project_dir: Path) -> DiscoveredPaths:
    """
    Auto-discover repository files and paradigm directory within a project directory.
    
    Searches for:
    - Concept files: *.concept.json, concepts.json
    - Inference files: *.inference.json, inferences.json
    - Input files: *.inputs.json, inputs.json
    - Paradigm directories: directories named 'paradigm' or containing paradigm files
    
    Args:
        project_dir: The project directory to search
        
    Returns:
        DiscoveredPaths with relative paths to discovered files
    """
    discovered = DiscoveredPaths()
    
    # Search for concept files
    concept_patterns = ['*.concept.json', 'concepts.json', '*_concept.json', 'concept_*.json']
    concept_files = discover_files_recursive(project_dir, concept_patterns)
    if concept_files:
        # Prefer files in 'repos' or 'repository' subdirectories
        for f in concept_files:
            parent_name = f.parent.name.lower()
            if parent_name in ('repos', 'repo', 'repository', 'repositories'):
                discovered.concepts = str(f.relative_to(project_dir))
                break
        # If not found in preferred dirs, use first match
        if not discovered.concepts:
            discovered.concepts = str(concept_files[0].relative_to(project_dir))
    
    # Search for inference files
    inference_patterns = ['*.inference.json', 'inferences.json', '*_inference.json', 'inference_*.json']
    inference_files = discover_files_recursive(project_dir, inference_patterns)
    if inference_files:
        # Prefer files in same directory as concepts
        if discovered.concepts:
            concepts_dir = Path(discovered.concepts).parent
            for f in inference_files:
                if f.relative_to(project_dir).parent == concepts_dir:
                    discovered.inferences = str(f.relative_to(project_dir))
                    break
        # If not found, prefer 'repos' directories
        if not discovered.inferences:
            for f in inference_files:
                parent_name = f.parent.name.lower()
                if parent_name in ('repos', 'repo', 'repository', 'repositories'):
                    discovered.inferences = str(f.relative_to(project_dir))
                    break
        # Fallback to first match
        if not discovered.inferences:
            discovered.inferences = str(inference_files[0].relative_to(project_dir))
    
    # Search for input files (optional)
    input_patterns = ['*.inputs.json', 'inputs.json', '*_inputs.json', 'input_*.json']
    input_files = discover_files_recursive(project_dir, input_patterns)
    if input_files:
        # Prefer files in same directory as concepts
        if discovered.concepts:
            concepts_dir = Path(discovered.concepts).parent
            for f in input_files:
                if f.relative_to(project_dir).parent == concepts_dir:
                    discovered.inputs = str(f.relative_to(project_dir))
                    break
        if not discovered.inputs:
            discovered.inputs = str(input_files[0].relative_to(project_dir))
    
    # Search for paradigm directories
    paradigm_dirs = discover_paradigm_directories(project_dir)
    if paradigm_dirs:
        discovered.paradigm_dir = str(paradigm_dirs[0].relative_to(project_dir))
    
    logger.info(f"Discovered paths in {project_dir}: {discovered}")
    return discovered


class ProjectService:
    """Service for managing NormCode Canvas projects."""
    
    def __init__(self):
        self.current_project_path: Optional[Path] = None
        self.current_config: Optional[ProjectConfig] = None
        self.current_config_file: Optional[str] = None  # The filename of current project config
        self._app_data_dir = get_app_data_dir()
        self._registry: Optional[ProjectRegistry] = None
    
    @property
    def is_project_open(self) -> bool:
        """Check if a project is currently open."""
        return self.current_project_path is not None and self.current_config is not None
    
    def get_project_config_path(self, project_dir: Path, config_file: Optional[str] = None) -> Path:
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
        Returns list of config filenames.
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
    
    def project_exists(self, project_dir: Path, config_file: Optional[str] = None) -> bool:
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
        llm_model: str = "demo",
        max_cycles: int = 50,
        paradigm_dir: Optional[str] = None,
        auto_discover: bool = True,
    ) -> tuple[ProjectConfig, str]:
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
            if paradigm_dir is None:
                paradigm_dir = discovered.paradigm_dir  # Can remain None
        else:
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
                llm_model=llm_model,
                max_cycles=max_cycles,
                paradigm_dir=paradigm_dir,
            ),
        )
        
        # Save to file
        config_path = project_dir / config_filename
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.info(f"Created project '{name}' at {project_dir}/{config_filename}")
        
        # Set as current project
        self.current_project_path = project_dir
        self.current_config = config
        self.current_config_file = config_filename
        
        # Register the project
        self._register_project(project_dir, config_filename, config)
        
        return config, config_filename
    
    def open_project(
        self, 
        project_path: Optional[str] = None,
        config_file: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> tuple[ProjectConfig, str]:
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
            registered = self.get_project_by_id(project_id)
            if not registered:
                raise FileNotFoundError(f"No project found with ID: {project_id}")
            project_path = registered.directory
            config_file = registered.config_file
        
        if not project_path:
            raise ValueError("Either project_path or project_id must be provided")
        
        project_dir = Path(project_path)
        
        # If no specific config file, find available configs
        if not config_file:
            configs = self.find_project_configs(project_dir)
            if not configs:
                raise FileNotFoundError(
                    f"No project config found at {project_dir}. "
                    f"Expected *{PROJECT_CONFIG_SUFFIX} or {LEGACY_PROJECT_CONFIG_FILE}"
                )
            # Use first config (or the only one)
            config_file = configs[0]
        
        config_path = project_dir / config_file
        
        if not config_path.exists():
            raise FileNotFoundError(f"Project config not found: {config_path}")
        
        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle legacy configs without ID
        if 'id' not in data:
            data['id'] = generate_project_id()
            # Save updated config with ID
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        
        config = ProjectConfig(**data)
        
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
        
        # Check if paradigm_dir exists, if not try discovered
        if config.execution.paradigm_dir:
            paradigm_path = project_dir / config.execution.paradigm_dir
            if not paradigm_path.exists() and discovered.paradigm_dir:
                logger.info(f"Updating paradigm_dir from '{config.execution.paradigm_dir}' to discovered '{discovered.paradigm_dir}'")
                config.execution.paradigm_dir = discovered.paradigm_dir
                config_updated = True
        elif discovered.paradigm_dir:
            # No paradigm_dir set, but we found one
            config.execution.paradigm_dir = discovered.paradigm_dir
            config_updated = True
        
        # Auto-detect base_dir if not set
        if not config.execution.base_dir:
            base_dir = self._detect_base_dir(project_dir, config.repositories)
            if base_dir:
                config.execution.base_dir = str(base_dir)
                config_updated = True
        
        # Save updated config if we made changes
        if config_updated:
            config.updated_at = datetime.now()
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config.model_dump(mode='json'), f, indent=2, default=str)
            logger.info(f"Updated project config with discovered paths")
        
        # Set as current project
        self.current_project_path = project_dir
        self.current_config = config
        self.current_config_file = config_file
        
        # Register/update the project in registry
        self._register_project(project_dir, config_file, config)
        
        logger.info(f"Opened project '{config.name}' from {project_dir}/{config_file}")
        
        return config, config_file
    
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
        
        # Save to file (use current_config_file if set)
        config_path = self.get_project_config_path(self.current_project_path, self.current_config_file)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_config.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.info(f"Saved project '{self.current_config.name}'")
        
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
        
        # Update repository paths
        if concepts is not None:
            self.current_config.repositories.concepts = concepts
        if inferences is not None:
            self.current_config.repositories.inferences = inferences
        if inputs is not None:
            # Empty string means clear the inputs path
            self.current_config.repositories.inputs = inputs if inputs else None
        
        self.current_config.updated_at = datetime.now()
        
        # Save to file
        config_path = self.get_project_config_path(self.current_project_path, self.current_config_file)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_config.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.info(f"Updated repository paths for project '{self.current_config.name}'")
        
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
    
    # Project Registry Management
    
    def _get_registry_path(self) -> Path:
        """Get path to project registry file."""
        return self._app_data_dir / PROJECT_REGISTRY_FILE
    
    def _load_registry(self) -> ProjectRegistry:
        """Load project registry."""
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
        """Save project registry."""
        if self._registry is None:
            return
        
        path = self._get_registry_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._registry.model_dump(mode='json'), f, indent=2, default=str)
    
    def _register_project(self, project_dir: Path, config_file: str, config: ProjectConfig):
        """Register a project in the registry."""
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
        """Get all registered projects."""
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
    
    def scan_directory_for_projects(self, directory: str, register: bool = True) -> List[RegisteredProject]:
        """
        Scan a directory for project config files and optionally register them.
        
        Args:
            directory: Directory to scan
            register: Whether to register found projects
            
        Returns:
            List of found/registered projects
        """
        project_dir = Path(directory)
        if not project_dir.exists():
            return []
        
        config_files = self.find_project_configs(project_dir)
        found_projects = []
        
        for config_file in config_files:
            try:
                config_path = project_dir / config_file
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle legacy configs without ID
                if 'id' not in data:
                    data['id'] = generate_project_id()
                    # Optionally save the updated config
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, default=str)
                
                config = ProjectConfig(**data)
                
                registered = RegisteredProject(
                    id=config.id,
                    name=config.name,
                    directory=str(project_dir.absolute()),
                    config_file=config_file,
                    description=config.description,
                    created_at=config.created_at,
                )
                
                if register:
                    self._register_project(project_dir, config_file, config)
                
                found_projects.append(registered)
                
            except Exception as e:
                logger.warning(f"Failed to load project config {config_file}: {e}")
        
        return found_projects
    
    def remove_project_from_registry(self, project_id: str):
        """Remove a project from the registry (does not delete files)."""
        registry = self._load_registry()
        registry.projects = [p for p in registry.projects if p.id != project_id]
        self._save_registry()
    
    def clear_registry(self):
        """Clear the entire project registry."""
        self._registry = ProjectRegistry()
        self._save_registry()
    
    # Legacy support for migration
    def migrate_recent_projects(self):
        """Migrate legacy recent-projects.json to new registry format."""
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
                        configs = self.find_project_configs(project_dir)
                        if configs:
                            self.open_project(project_path=recent.path, config_file=configs[0])
                            self.close_project()
                except Exception as e:
                    logger.warning(f"Failed to migrate legacy project {recent.path}: {e}")
            
            # Rename legacy file to indicate migration
            legacy_path.rename(legacy_path.with_suffix('.json.migrated'))
            logger.info("Migrated legacy recent projects to new registry")
            
        except Exception as e:
            logger.warning(f"Failed to migrate legacy projects: {e}")


# Global project service instance
project_service = ProjectService()
