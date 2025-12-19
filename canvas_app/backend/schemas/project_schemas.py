"""Project-related schemas for project-based canvas management."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

# Project configuration file name
PROJECT_CONFIG_FILE = "normcode-canvas.json"
RECENT_PROJECTS_FILE = "recent-projects.json"


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


class ProjectConfig(BaseModel):
    """
    Complete project configuration.
    Stored as normcode-canvas.json in the project directory.
    """
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


class RecentProject(BaseModel):
    """A recently opened project for the recent projects list."""
    path: str  # Absolute path to project directory
    name: str
    last_opened: datetime = Field(default_factory=datetime.now)


class RecentProjectsConfig(BaseModel):
    """List of recent projects, stored in app data directory."""
    projects: List[RecentProject] = Field(default_factory=list)
    max_recent: int = 10


# API Request/Response models

class OpenProjectRequest(BaseModel):
    """Request to open a project directory."""
    project_path: str  # Path to directory containing normcode-canvas.json


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
    path: str
    config: ProjectConfig
    is_loaded: bool = False  # Whether repositories are currently loaded
    repositories_exist: bool = False  # Whether repository files exist


class RecentProjectsResponse(BaseModel):
    """Response containing recent projects list."""
    projects: List[RecentProject]
