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
    RecentProjectsResponse,
    ExecutionSettings,
)
from services.project_service import project_service
from services.execution_service import execution_controller
from services.graph_service import graph_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/current", response_model=Optional[ProjectResponse])
async def get_current_project():
    """Get the currently open project."""
    if not project_service.is_project_open:
        return None
    
    return ProjectResponse(
        path=str(project_service.current_project_path),
        config=project_service.current_config,
        is_loaded=execution_controller.orchestrator is not None,
        repositories_exist=project_service.check_repositories_exist(),
    )


@router.post("/open", response_model=ProjectResponse)
async def open_project(request: OpenProjectRequest):
    """
    Open an existing project.
    
    This loads the project configuration but does NOT load the repositories.
    Use /api/repositories/load to load the repositories after opening the project.
    """
    try:
        config = project_service.open_project(request.project_path)
        
        return ProjectResponse(
            path=str(project_service.current_project_path),
            config=config,
            is_loaded=False,
            repositories_exist=project_service.check_repositories_exist(),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to open project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=ProjectResponse)
async def create_project(request: CreateProjectRequest):
    """
    Create a new project.
    
    This creates the project configuration file in the specified directory.
    """
    try:
        config = project_service.create_project(
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
            path=str(project_service.current_project_path),
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
            path=str(project_service.current_project_path),
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
async def get_recent_projects():
    """Get list of recently opened projects."""
    projects = project_service.get_recent_projects()
    return RecentProjectsResponse(projects=projects)


@router.delete("/recent")
async def clear_recent_projects():
    """Clear the recent projects list."""
    project_service.clear_recent_projects()
    return {"status": "cleared"}


@router.post("/load-repositories")
async def load_project_repositories():
    """
    Load repositories for the currently open project.
    
    This is a convenience endpoint that uses the project's configured paths
    and settings to load the repositories.
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
        
        # Load graph for visualization (must be done first!)
        graph_service.load_from_files(
            paths['concepts'],
            paths['inferences']
        )
        logger.info(f"Graph loaded with {len(graph_service.current_graph.nodes)} nodes")
        
        # Load repositories using execution controller
        await execution_controller.load_repositories(
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
            execution_controller.set_breakpoint(bp)
        
        logger.info(f"Loaded repositories for project '{config.name}'")
        
        return {
            "status": "loaded",
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
            path=str(project_service.current_project_path),
            config=config,
            is_loaded=execution_controller.orchestrator is not None,
            repositories_exist=project_service.check_repositories_exist(),
        )
    except Exception as e:
        logger.exception(f"Failed to update project settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
