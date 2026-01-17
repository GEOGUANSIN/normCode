"""
Portable project schemas for export/import functionality.

This module defines the data structures for creating portable project archives
that include all project data, databases, and run history.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ExportScope(str, Enum):
    """What to include in the export."""
    FULL = "full"              # Everything: project + all runs + all databases
    PROJECT_ONLY = "project"   # Just the project structure (no run history)
    SELECTED_RUNS = "selected" # Project + specific runs only


class PortableManifest(BaseModel):
    """
    Manifest file stored in the portable project archive.
    
    This contains all metadata needed to import the project elsewhere.
    """
    # Format version for future compatibility
    format_version: str = "1.0.0"
    
    # Export metadata
    exported_at: datetime = Field(default_factory=datetime.now)
    export_scope: ExportScope = ExportScope.FULL
    source_path: Optional[str] = None  # Original project path (for reference)
    
    # Project info
    project_id: str
    project_name: str
    project_description: Optional[str] = None
    config_file: str  # The project config filename
    
    # Content inventory
    files: List[str] = Field(default_factory=list)  # All included files (relative paths)
    
    # Database info
    has_database: bool = False
    database_file: Optional[str] = None  # Relative path in archive
    runs_count: int = 0
    runs_included: List[str] = Field(default_factory=list)  # Run IDs included
    
    # Provisions info
    provisions_included: Dict[str, str] = Field(default_factory=dict)
    # e.g., {"paradigms": "provisions/paradigms", "prompts": "provisions/prompts"}
    
    # Optional: agent configuration
    agent_config_included: bool = False


class ExportOptions(BaseModel):
    """Options for exporting a portable project."""
    scope: ExportScope = ExportScope.FULL
    
    # Run selection (only used if scope == SELECTED_RUNS)
    selected_run_ids: List[str] = Field(default_factory=list)
    
    # Database options
    include_database: bool = True
    include_logs: bool = True  # Include run log files
    
    # What to include
    include_provisions: bool = True
    include_agent_config: bool = True
    
    # Output options
    output_dir: Optional[str] = None  # Custom output directory
    output_filename: Optional[str] = None  # Custom filename (without extension)
    create_zip: bool = True  # Create zip archive (vs just folder)


class ImportOptions(BaseModel):
    """Options for importing a portable project."""
    # Where to import
    target_directory: str  # Directory where to create/import the project
    
    # Project options
    new_project_name: Optional[str] = None  # Rename project on import
    overwrite_existing: bool = False  # Overwrite if project already exists
    
    # Database options
    import_database: bool = True
    import_runs: bool = True  # Import run history
    
    # Conflict resolution
    merge_with_existing: bool = False  # If project exists, merge runs


class ExportResult(BaseModel):
    """Result of a project export operation."""
    success: bool
    message: str
    
    # Output info
    output_path: Optional[str] = None  # Path to created archive/folder
    archive_size: Optional[int] = None  # Size in bytes
    
    # Content summary
    manifest: Optional[PortableManifest] = None
    files_count: int = 0
    runs_exported: int = 0


class ImportResult(BaseModel):
    """Result of a project import operation."""
    success: bool
    message: str
    
    # Project info
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    project_path: Optional[str] = None
    config_file: Optional[str] = None
    
    # Import summary
    files_imported: int = 0
    runs_imported: int = 0
    
    # Warnings/notes
    warnings: List[str] = Field(default_factory=list)


class PortableProjectInfo(BaseModel):
    """Information about a portable project archive (for preview before import)."""
    # From manifest
    format_version: str
    exported_at: datetime
    export_scope: ExportScope
    source_path: Optional[str] = None
    
    # Project info
    project_id: str
    project_name: str
    project_description: Optional[str] = None
    
    # Content summary
    files_count: int = 0
    has_database: bool = False
    runs_count: int = 0
    provisions: Dict[str, str] = Field(default_factory=dict)
    
    # Archive info
    archive_path: str
    archive_size: int = 0


# =============================================================================
# API Request/Response Models
# =============================================================================

class ExportProjectRequest(BaseModel):
    """Request to export a project as portable archive."""
    project_id: Optional[str] = None  # Export by project ID (uses current if None)
    options: ExportOptions = Field(default_factory=ExportOptions)


class ImportProjectRequest(BaseModel):
    """Request to import a portable project archive."""
    archive_path: str  # Path to the .zip or folder
    options: ImportOptions


class PreviewImportRequest(BaseModel):
    """Request to preview a portable project before importing."""
    archive_path: str


class ListRunsForExportRequest(BaseModel):
    """Request to list available runs for selective export."""
    project_id: Optional[str] = None  # Uses current project if None


class RunInfo(BaseModel):
    """Information about a run for export selection."""
    run_id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "unknown"
    execution_count: int = 0
    max_cycle: int = 0
    has_checkpoints: bool = False

