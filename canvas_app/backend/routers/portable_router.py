"""
Portable Project Router - API endpoints for export/import functionality.

This router provides endpoints for:
- Exporting projects as portable archives
- Importing portable archives
- Previewing archives before import
- Listing available exports
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from schemas.portable_schemas import (
    ExportOptions,
    ImportOptions,
    ExportResult,
    ImportResult,
    PortableProjectInfo,
    RunInfo,
    ExportProjectRequest,
    ImportProjectRequest,
    PreviewImportRequest,
    ListRunsForExportRequest,
)
from services.portable_project_service import portable_project_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portable", tags=["portable"])


# =============================================================================
# Export Endpoints
# =============================================================================

@router.post("/export", response_model=ExportResult)
async def export_project(request: ExportProjectRequest):
    """
    Export a project as a portable archive.
    
    Creates a self-contained archive containing:
    - Project configuration
    - Repository files (concepts, inferences, inputs)
    - Provisions (paradigms, prompts, scripts, data)
    - Execution database (orchestration.db)
    - Run history and checkpoints
    - Log files (optional)
    
    The archive can be imported on a different machine to fully restore
    the project including all run history.
    """
    try:
        result = portable_project_service.export_project(
            project_id=request.project_id,
            options=request.options,
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except Exception as e:
        logger.exception(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/runs", response_model=list[RunInfo])
async def list_runs_for_export(request: ListRunsForExportRequest):
    """
    List available runs for selective export.
    
    Use this to get a list of runs when you want to export only
    specific runs instead of the full project history.
    """
    try:
        runs = portable_project_service.list_runs_for_export(
            project_id=request.project_id
        )
        return runs
        
    except Exception as e:
        logger.exception(f"Failed to list runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exports")
async def list_exports():
    """
    List available exported archives in the default exports directory.
    
    Returns information about each export including project name,
    export date, size, and run count.
    """
    try:
        exports = portable_project_service.list_exports()
        return {"exports": exports}
        
    except Exception as e:
        logger.exception(f"Failed to list exports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Import Endpoints
# =============================================================================

@router.post("/import/preview", response_model=PortableProjectInfo)
async def preview_import(request: PreviewImportRequest):
    """
    Preview a portable project archive before importing.
    
    Returns information about the archive contents including:
    - Project metadata
    - Files count
    - Database status
    - Run count
    - Provisions included
    
    Use this to inspect an archive before deciding to import it.
    """
    try:
        info = portable_project_service.preview_import(request.archive_path)
        return info
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=ImportResult)
async def import_project(request: ImportProjectRequest):
    """
    Import a portable project archive.
    
    Restores a project from a portable archive including:
    - Project configuration
    - Repository files
    - Provisions
    - Execution database (optional)
    - Run history (optional)
    
    Options:
    - target_directory: Where to create/import the project
    - new_project_name: Rename project on import (optional)
    - overwrite_existing: Overwrite if project exists
    - merge_with_existing: Merge run history with existing project
    """
    try:
        result = portable_project_service.import_project(
            archive_path=request.archive_path,
            options=request.options,
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Quick Export/Import (simplified endpoints)
# =============================================================================

class QuickExportRequest(BaseModel):
    """Simplified export request."""
    project_id: Optional[str] = None
    include_database: bool = True
    output_dir: Optional[str] = None


class QuickImportRequest(BaseModel):
    """Simplified import request."""
    archive_path: str
    target_directory: str
    overwrite: bool = False


@router.post("/quick-export", response_model=ExportResult)
async def quick_export(request: QuickExportRequest):
    """
    Quick export with sensible defaults.
    
    Exports the current (or specified) project with all data.
    """
    options = ExportOptions(
        include_database=request.include_database,
        output_dir=request.output_dir,
    )
    
    try:
        result = portable_project_service.export_project(
            project_id=request.project_id,
            options=options,
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except Exception as e:
        logger.exception(f"Quick export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-import", response_model=ImportResult)
async def quick_import(request: QuickImportRequest):
    """
    Quick import with sensible defaults.
    
    Imports a portable archive to the specified directory.
    """
    options = ImportOptions(
        target_directory=request.target_directory,
        overwrite_existing=request.overwrite,
        import_database=True,
        import_runs=True,
    )
    
    try:
        result = portable_project_service.import_project(
            archive_path=request.archive_path,
            options=options,
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
        
    except Exception as e:
        logger.exception(f"Quick import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

