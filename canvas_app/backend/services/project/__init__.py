"""
Project management services module.

This package provides modular project management functionality:
- discovery: File and path discovery utilities
- registry: Project registry management (persistent storage of known projects)
- tabs: Multi-project tab state management
- config: Project configuration CRUD operations

For backwards compatibility, the main ProjectService facade is available
from services.project_service.
"""

from .discovery import (
    SKIP_DIRS,
    MAX_SEARCH_DEPTH,
    DiscoveredPaths,
    discover_files_recursive,
    discover_paradigm_directories,
    discover_project_paths,
)

from .registry_service import (
    ProjectRegistryService,
    get_app_data_dir,
)

from .tabs_service import (
    ProjectTabsService,
)

from .config_service import (
    ProjectConfigService,
)

__all__ = [
    # Discovery
    'SKIP_DIRS',
    'MAX_SEARCH_DEPTH',
    'DiscoveredPaths',
    'discover_files_recursive',
    'discover_paradigm_directories',
    'discover_project_paths',
    # Registry
    'ProjectRegistryService',
    'get_app_data_dir',
    # Tabs
    'ProjectTabsService',
    # Config
    'ProjectConfigService',
]

