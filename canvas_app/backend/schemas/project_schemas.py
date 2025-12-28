"""Project-related schemas for project-based canvas management."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid

from pydantic import BaseModel, Field

# Project configuration file naming
# Old: PROJECT_CONFIG_FILE = "normcode-canvas.json" (single project per directory)
# New: {project-name}.normcode-canvas.json (multiple projects per directory)
PROJECT_CONFIG_SUFFIX = ".normcode-canvas.json"
LEGACY_PROJECT_CONFIG_FILE = "normcode-canvas.json"  # For backwards compatibility
PROJECT_REGISTRY_FILE = "project-registry.json"


def generate_project_id() -> str:
    """Generate a unique project ID."""
    return str(uuid.uuid4())[:8]


def get_project_config_filename(project_name: str) -> str:
    """
    Get the config filename for a project.
    Converts project name to a safe filename slug.
    """
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    slug = project_name.lower().strip()
    slug = slug.replace(' ', '-')
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    slug = slug.strip('-')
    return f"{slug}{PROJECT_CONFIG_SUFFIX}"


class RepositoryPaths(BaseModel):
    """Paths to repository files, relative to project root."""
    concepts: str = "concepts.json"
    inferences: str = "inferences.json"
    inputs: Optional[str] = None  # Optional inputs file


class ExecutionSettings(BaseModel):
    """Execution configuration settings."""
    llm_model: str = "demo"
    max_cycles: int = Field(default=50, ge=1, le=1000)
    db_path: str = "orchestration.db"
    base_dir: Optional[str] = None  # Base directory for file operations (auto-detected if not set)
    paradigm_dir: Optional[str] = None  # e.g., "provision/paradigm"
    agent_config: Optional[str] = None  # Path to .agent.json file (relative to project dir)


class ProjectConfig(BaseModel):
    """
    Complete project configuration.
    Stored as {project-name}.normcode-canvas.json in the project directory.
    """
    # Project identification (new)
    id: str = Field(default_factory=generate_project_id)  # Unique project ID
    
    # Project metadata
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Repository paths (relative to project root)
    repositories: RepositoryPaths = Field(default_factory=RepositoryPaths)
    
    # Execution settings
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)
    
    # Debugging state
    breakpoints: List[str] = Field(default_factory=list)  # List of flow_index strings
    
    # UI preferences (optional)
    ui_preferences: Dict[str, Any] = Field(default_factory=dict)


class RegisteredProject(BaseModel):
    """
    A registered project in the app's project registry.
    Tracks all known projects (not just recent ones).
    """
    id: str  # Unique project ID
    name: str
    directory: str  # Absolute path to project directory
    config_file: str  # Filename of the config (e.g., "gold-analysis.normcode-canvas.json")
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_opened: Optional[datetime] = None
    
    @property
    def full_config_path(self) -> str:
        """Get the full path to the config file."""
        return str(Path(self.directory) / self.config_file)


class ProjectRegistry(BaseModel):
    """
    Central registry of all known projects.
    Stored in ~/.normcode-canvas/project-registry.json
    """
    projects: List[RegisteredProject] = Field(default_factory=list)
    max_recent: int = 20  # Max projects to show in "recent" list


# Keep RecentProject for backwards compatibility during migration
class RecentProject(BaseModel):
    """A recently opened project (legacy format, for migration)."""
    path: str  # Absolute path to project directory
    name: str
    last_opened: datetime = Field(default_factory=datetime.now)


class RecentProjectsConfig(BaseModel):
    """List of recent projects (legacy format, for migration)."""
    projects: List[RecentProject] = Field(default_factory=list)
    max_recent: int = 10


# API Request/Response models

class OpenProjectRequest(BaseModel):
    """Request to open a project by ID or by directory path + config file."""
    project_id: Optional[str] = None  # Open by project ID (from registry)
    project_path: Optional[str] = None  # Path to directory
    config_file: Optional[str] = None  # Specific config file (if multiple in dir)


class CreateProjectRequest(BaseModel):
    """Request to create a new project."""
    project_path: str  # Path where to create the project
    name: str
    description: Optional[str] = None
    # Initial repository paths (relative to project_path)
    concepts_path: Optional[str] = "concepts.json"
    inferences_path: Optional[str] = "inferences.json"
    inputs_path: Optional[str] = None
    # Initial execution settings
    llm_model: str = "demo"
    max_cycles: int = 50
    paradigm_dir: Optional[str] = None


class SaveProjectRequest(BaseModel):
    """Request to save current project state."""
    # Optionally update settings when saving
    execution: Optional[ExecutionSettings] = None
    breakpoints: Optional[List[str]] = None
    ui_preferences: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    """Response containing project information."""
    id: str  # Project ID
    path: str  # Directory path
    config_file: str  # Config filename
    config: ProjectConfig
    is_loaded: bool = False  # Whether repositories are currently loaded
    repositories_exist: bool = False  # Whether repository files exist


class ProjectListResponse(BaseModel):
    """Response containing list of all registered projects."""
    projects: List[RegisteredProject]


class DirectoryProjectsResponse(BaseModel):
    """Response containing projects found in a specific directory."""
    directory: str
    projects: List[RegisteredProject]
    

class RecentProjectsResponse(BaseModel):
    """Response containing recent projects (sorted by last_opened)."""
    projects: List[RegisteredProject]


class ScanDirectoryRequest(BaseModel):
    """Request to scan a directory for project config files."""
    directory: str
    register: bool = True  # Whether to register found projects


class UpdateRepositoriesRequest(BaseModel):
    """Request to update repository paths."""
    concepts: Optional[str] = None
    inferences: Optional[str] = None
    inputs: Optional[str] = None


class DiscoverPathsRequest(BaseModel):
    """Request to discover repository files in a directory."""
    directory: str


class DiscoveredPathsResponse(BaseModel):
    """Response containing auto-discovered repository paths."""
    directory: str
    concepts: Optional[str] = None  # Relative path to concepts file
    inferences: Optional[str] = None  # Relative path to inferences file
    inputs: Optional[str] = None  # Relative path to inputs file
    paradigm_dir: Optional[str] = None  # Relative path to paradigm directory
    
    # Additional info
    concepts_exists: bool = False
    inferences_exists: bool = False
    inputs_exists: bool = False
    paradigm_dir_exists: bool = False


# =============================================================================
# Multi-Project (Tabs) Support
# =============================================================================

class OpenProjectInstance(BaseModel):
    """
    Represents an open project instance (a tab).
    Each open project has its own execution state.
    """
    id: str  # Project ID (same as ProjectConfig.id)
    name: str
    directory: str
    config_file: str
    config: ProjectConfig
    is_loaded: bool = False  # Whether repositories are loaded
    repositories_exist: bool = False
    is_active: bool = False  # Whether this is the currently focused tab
    is_read_only: bool = False  # Read-only projects can be viewed and executed, but not modified


class OpenProjectsResponse(BaseModel):
    """Response containing all open project instances."""
    projects: List[OpenProjectInstance]
    active_project_id: Optional[str] = None


class SwitchProjectRequest(BaseModel):
    """Request to switch to a different open project tab."""
    project_id: str


class CloseProjectRequest(BaseModel):
    """Request to close a specific project tab."""
    project_id: str
    
    
class OpenProjectInTabRequest(BaseModel):
    """Request to open a project as a new tab (keeping other tabs open)."""
    project_id: Optional[str] = None  # Open by project ID
    project_path: Optional[str] = None  # Or by path
    config_file: Optional[str] = None  # Specific config file
    make_active: bool = True  # Whether to switch to this tab
    is_read_only: bool = False  # Read-only projects can be viewed and executed, but not modified