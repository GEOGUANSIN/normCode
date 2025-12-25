"""Project management router."""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from schemas.project_schemas import (
    ProjectConfig,
    OpenProjectRequest,
    CreateProjectRequest,
    SaveProjectRequest,
    ProjectResponse,
    ProjectListResponse,
    DirectoryProjectsResponse,
    RecentProjectsResponse,
    ScanDirectoryRequest,
    ExecutionSettings,
    UpdateRepositoriesRequest,
    DiscoverPathsRequest,
    DiscoveredPathsResponse,
    # Multi-project (tabs) support
    OpenProjectInstance,
    OpenProjectsResponse,
    SwitchProjectRequest,
    CloseProjectRequest,
    OpenProjectInTabRequest,
)
from services.project_service import project_service
from services.execution_service import execution_controller, execution_controller_registry, get_execution_controller
from services.graph_service import graph_service
from schemas.execution_schemas import ExecutionStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# Migration is called when the module is first loaded
# This replaces the deprecated @router.on_event("startup") decorator
try:
    project_service.migrate_recent_projects()
except Exception as e:
    logger.warning(f"Failed to migrate recent projects: {e}")


@router.get("/current", response_model=Optional[ProjectResponse])
async def get_current_project():
    """Get the currently open project."""
    if not project_service.is_project_open:
        return None
    
    return ProjectResponse(
        id=project_service.current_config.id,
        path=str(project_service.current_project_path),
        config_file=project_service.current_config_file or "normcode-canvas.json",
        config=project_service.current_config,
        is_loaded=execution_controller.orchestrator is not None,
        repositories_exist=project_service.check_repositories_exist(),
    )


@router.post("/open", response_model=ProjectResponse)
async def open_project(request: OpenProjectRequest):
    """
    Open an existing project.
    
    Can open by:
    - project_id: Open a registered project by ID
    - project_path + config_file: Open a specific config in a directory
    - project_path only: Open first/only project config in directory
    
    This loads the project configuration but does NOT load the repositories.
    Use /api/project/load-repositories to load the repositories after opening.
    """
    try:
        config, config_file = project_service.open_project(
            project_path=request.project_path,
            config_file=request.config_file,
            project_id=request.project_id,
        )
        
        return ProjectResponse(
            id=config.id,
            path=str(project_service.current_project_path),
            config_file=config_file,
            config=config,
            is_loaded=False,
            repositories_exist=project_service.check_repositories_exist(),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to open project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=ProjectResponse)
async def create_project(request: CreateProjectRequest):
    """
    Create a new project.
    
    Creates a project configuration file named {project-name}.normcode-canvas.json
    in the specified directory. Multiple projects can exist in the same directory.
    """
    try:
        config, config_file = project_service.create_project(
            project_path=request.project_path,
            name=request.name,
            description=request.description,
            concepts_path=request.concepts_path,
            inferences_path=request.inferences_path,
            inputs_path=request.inputs_path,
            llm_model=request.llm_model,
            max_cycles=request.max_cycles,
            paradigm_dir=request.paradigm_dir,
        )
        
        return ProjectResponse(
            id=config.id,
            path=str(project_service.current_project_path),
            config_file=config_file,
            config=config,
            is_loaded=False,
            repositories_exist=project_service.check_repositories_exist(),
        )
    except Exception as e:
        logger.exception(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save", response_model=ProjectResponse)
async def save_project(request: SaveProjectRequest):
    """
    Save the current project configuration.
    
    Optionally updates execution settings, breakpoints, and UI preferences.
    """
    if not project_service.is_project_open:
        raise HTTPException(status_code=400, detail="No project is currently open")
    
    try:
        # Get current breakpoints from execution controller if not provided
        breakpoints = request.breakpoints
        if breakpoints is None and execution_controller.breakpoints:
            breakpoints = list(execution_controller.breakpoints)
        
        config = project_service.save_project(
            execution=request.execution,
            breakpoints=breakpoints,
            ui_preferences=request.ui_preferences,
        )
        
        return ProjectResponse(
            id=config.id,
            path=str(project_service.current_project_path),
            config_file=project_service.current_config_file or "normcode-canvas.json",
            config=config,
            is_loaded=execution_controller.orchestrator is not None,
            repositories_exist=project_service.check_repositories_exist(),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to save project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close")
async def close_project():
    """Close the current project."""
    project_service.close_project()
    # Also stop any running execution
    await execution_controller.stop()
    return {"status": "closed"}


@router.get("/recent", response_model=RecentProjectsResponse)
async def get_recent_projects(limit: int = 10):
    """Get list of recently opened projects."""
    projects = project_service.get_recent_projects(limit=limit)
    return RecentProjectsResponse(projects=projects)


@router.get("/all", response_model=ProjectListResponse)
async def get_all_projects():
    """Get all registered projects."""
    projects = project_service.get_all_projects()
    return ProjectListResponse(projects=projects)


@router.get("/directory", response_model=DirectoryProjectsResponse)
async def get_projects_in_directory(directory: str):
    """Get all registered projects in a specific directory."""
    projects = project_service.get_projects_in_directory(directory)
    return DirectoryProjectsResponse(directory=directory, projects=projects)


@router.post("/scan", response_model=DirectoryProjectsResponse)
async def scan_directory_for_projects(request: ScanDirectoryRequest):
    """
    Scan a directory for project config files.
    
    Finds all *.normcode-canvas.json files in the directory
    and optionally registers them.
    """
    projects = project_service.scan_directory_for_projects(
        directory=request.directory,
        register=request.register,
    )
    return DirectoryProjectsResponse(directory=request.directory, projects=projects)


@router.post("/discover", response_model=DiscoveredPathsResponse)
async def discover_paths(request: DiscoverPathsRequest):
    """
    Auto-discover repository files and paradigm directory in a directory.
    
    Searches for:
    - Concept files: *.concept.json, concepts.json
    - Inference files: *.inference.json, inferences.json
    - Input files: *.inputs.json, inputs.json
    - Paradigm directories: directories named 'paradigm' or containing paradigm files
    
    Returns relative paths that can be used for project creation.
    This is useful for populating default values when creating a new project.
    """
    from pathlib import Path
    
    directory = Path(request.directory)
    discovered = project_service.discover_paths(request.directory)
    
    # Check which discovered paths actually exist
    concepts_exists = False
    inferences_exists = False
    inputs_exists = False
    paradigm_dir_exists = False
    
    if directory.exists():
        if discovered['concepts']:
            concepts_exists = (directory / discovered['concepts']).exists()
        if discovered['inferences']:
            inferences_exists = (directory / discovered['inferences']).exists()
        if discovered['inputs']:
            inputs_exists = (directory / discovered['inputs']).exists()
        if discovered['paradigm_dir']:
            paradigm_dir_exists = (directory / discovered['paradigm_dir']).exists()
    
    return DiscoveredPathsResponse(
        directory=request.directory,
        concepts=discovered['concepts'],
        inferences=discovered['inferences'],
        inputs=discovered['inputs'],
        paradigm_dir=discovered['paradigm_dir'],
        concepts_exists=concepts_exists,
        inferences_exists=inferences_exists,
        inputs_exists=inputs_exists,
        paradigm_dir_exists=paradigm_dir_exists,
    )


@router.delete("/registry/{project_id}")
async def remove_project_from_registry(project_id: str):
    """Remove a project from the registry (does not delete files)."""
    project_service.remove_project_from_registry(project_id)
    return {"status": "removed", "project_id": project_id}


@router.delete("/registry")
async def clear_registry():
    """Clear the entire project registry."""
    project_service.clear_registry()
    return {"status": "cleared"}


@router.post("/load-repositories")
async def load_project_repositories():
    """
    Load repositories for the currently open project.
    
    This is a convenience endpoint that uses the project's configured paths
    and settings to load the repositories. Each project gets its own
    ExecutionController instance.
    """
    if not project_service.is_project_open:
        raise HTTPException(status_code=400, detail="No project is currently open")
    
    if not project_service.check_repositories_exist():
        raise HTTPException(
            status_code=404, 
            detail="Repository files not found. Check that concepts.json and inferences.json exist."
        )
    
    try:
        paths = project_service.get_absolute_repo_paths()
        config = project_service.current_config
        exec_settings = config.execution
        project_id = config.id
        
        # Load graph for visualization (must be done first!)
        graph_service.load_from_files(
            paths['concepts'],
            paths['inferences']
        )
        logger.info(f"Graph loaded with {len(graph_service.current_graph.nodes)} nodes")
        
        # Get or create the ExecutionController for this project
        controller = get_execution_controller(project_id)
        
        # Ensure the registry knows this is the active project
        execution_controller_registry.set_active(project_id)
        
        # Load repositories using project-specific execution controller
        await controller.load_repositories(
            concepts_path=paths['concepts'],
            inferences_path=paths['inferences'],
            inputs_path=paths.get('inputs'),
            llm_model=exec_settings.llm_model,
            base_dir=paths['base_dir'],
            max_cycles=exec_settings.max_cycles,
            db_path=exec_settings.db_path,
            paradigm_dir=exec_settings.paradigm_dir,
        )
        
        # Restore breakpoints from project config
        for bp in config.breakpoints:
            controller.set_breakpoint(bp)
        
        # Update the loaded state in project service
        project_service.update_open_project_loaded_state(project_id, True)
        
        logger.info(f"Loaded repositories for project '{config.name}' (id={project_id})")
        
        return {
            "status": "loaded",
            "project_id": project_id,
            "concepts_path": paths['concepts'],
            "inferences_path": paths['inferences'],
            "breakpoints_restored": len(config.breakpoints),
        }
    except Exception as e:
        logger.exception(f"Failed to load project repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paths")
async def get_project_paths():
    """Get absolute paths for the current project's repositories."""
    if not project_service.is_project_open:
        raise HTTPException(status_code=400, detail="No project is currently open")
    
    return project_service.get_absolute_repo_paths()


@router.put("/settings", response_model=ProjectResponse)
async def update_project_settings(settings: ExecutionSettings):
    """Update the execution settings for the current project."""
    if not project_service.is_project_open:
        raise HTTPException(status_code=400, detail="No project is currently open")
    
    try:
        config = project_service.save_project(execution=settings)
        
        return ProjectResponse(
            id=config.id,
            path=str(project_service.current_project_path),
            config_file=project_service.current_config_file or "normcode-canvas.json",
            config=config,
            is_loaded=execution_controller.orchestrator is not None,
            repositories_exist=project_service.check_repositories_exist(),
        )
    except Exception as e:
        logger.exception(f"Failed to update project settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/repositories", response_model=ProjectResponse)
async def update_repository_paths(request: UpdateRepositoriesRequest):
    """
    Update repository paths for the current project.
    
    Only updates paths that are provided (non-None).
    After updating, re-checks whether the repository files exist.
    """
    if not project_service.is_project_open:
        raise HTTPException(status_code=400, detail="No project is currently open")
    
    try:
        config = project_service.update_repositories(
            concepts=request.concepts,
            inferences=request.inferences,
            inputs=request.inputs,
        )
        
        return ProjectResponse(
            id=config.id,
            path=str(project_service.current_project_path),
            config_file=project_service.current_config_file or "normcode-canvas.json",
            config=config,
            is_loaded=execution_controller.orchestrator is not None,
            repositories_exist=project_service.check_repositories_exist(),
        )
    except Exception as e:
        logger.exception(f"Failed to update repository paths: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Multi-Project (Tabs) Support
# =============================================================================

@router.get("/tabs", response_model=OpenProjectsResponse)
async def get_open_projects():
    """
    Get all currently open project tabs.
    
    Returns a list of all open project instances and the active project ID.
    """
    open_projects = project_service.get_open_projects()
    active_id = project_service.get_active_project_id()
    
    return OpenProjectsResponse(
        projects=open_projects,
        active_project_id=active_id,
    )


@router.post("/tabs/open", response_model=OpenProjectInstance)
async def open_project_as_tab(request: OpenProjectInTabRequest):
    """
    Open a project as a new tab (keeping other tabs open).
    
    This differs from /open in that it:
    - Keeps other project tabs open
    - Tracks the project in the tabs list
    - Creates an ExecutionController for the project
    - Can optionally not make it the active tab
    """
    try:
        instance = project_service.open_project_as_tab(
            project_path=request.project_path,
            config_file=request.config_file,
            project_id=request.project_id,
            make_active=request.make_active,
            is_read_only=request.is_read_only,
        )
        
        # Ensure ExecutionControllers exist for ALL open projects
        # This handles the case where a project was retroactively added to tabs
        for open_project in project_service.get_open_projects():
            get_execution_controller(open_project.id)
        
        # If making active, update the registry
        if request.make_active:
            execution_controller_registry.set_active(instance.id)
        
        return instance
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to open project as tab: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tabs/switch", response_model=OpenProjectInstance)
async def switch_project_tab(request: SwitchProjectRequest):
    """
    Switch to a different open project tab.
    
    This changes which project is "active" without closing others.
    Each project has its own ExecutionController, so switching tabs
    just changes which controller is "active" for backward-compatible APIs.
    """
    try:
        # Switch the project in project_service
        instance = project_service.switch_to_project(request.project_id)
        
        # Update the active project in the execution controller registry
        execution_controller_registry.set_active(request.project_id)
        
        logger.info(f"Switched to project tab '{instance.name}' (id={request.project_id})")
        
        return instance
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to switch project tab: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tabs/close", response_model=OpenProjectsResponse)
async def close_project_tab(request: CloseProjectRequest):
    """
    Close a specific project tab.
    
    If the closed tab was active, automatically switches to another tab.
    Also stops execution and removes the controller for the closed project.
    """
    try:
        # Stop execution for the project being closed
        controller = get_execution_controller(request.project_id)
        if controller.status == ExecutionStatus.RUNNING:
            await controller.stop()
        
        # Remove the controller for this project
        execution_controller_registry.remove_controller(request.project_id)
        
        # Close the project tab
        new_active_id = project_service.close_project_tab(request.project_id)
        
        # Update the active project in the registry
        execution_controller_registry.set_active(new_active_id)
        
        return OpenProjectsResponse(
            projects=project_service.get_open_projects(),
            active_project_id=new_active_id,
        )
    except Exception as e:
        logger.exception(f"Failed to close project tab: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tabs/close-all")
async def close_all_project_tabs():
    """
    Close all open project tabs.
    
    Stops any running execution and clears all project state.
    """
    try:
        await execution_controller.stop()
        project_service.close_all_project_tabs()
        return {"status": "closed", "message": "All project tabs closed"}
    except Exception as e:
        logger.exception(f"Failed to close all project tabs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tabs/active", response_model=Optional[OpenProjectInstance])
async def get_active_project_tab():
    """
    Get the currently active project tab.
    
    Returns None if no project is currently active.
    """
    return project_service.get_active_project()
