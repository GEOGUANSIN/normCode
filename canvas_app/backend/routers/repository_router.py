"""Repository management endpoints."""
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from services.graph_service import graph_service
from services.execution_service import execution_controller, get_execution_controller
from schemas.execution_schemas import LoadRepositoryRequest

router = APIRouter()


class RepositoryInfo(BaseModel):
    """Information about a repository set."""
    name: str
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None


class LoadResponse(BaseModel):
    """Response after loading repositories."""
    success: bool
    message: str
    run_id: Optional[str] = None
    total_inferences: int = 0
    concepts_count: int = 0


@router.post("/load", response_model=LoadResponse)
async def load_repositories(request: LoadRepositoryRequest):
    """Load concept and inference repository files."""
    try:
        # Validate paths exist
        concepts_path = Path(request.concepts_path)
        inferences_path = Path(request.inferences_path)
        
        if not concepts_path.exists():
            raise HTTPException(status_code=404, detail=f"Concepts file not found: {request.concepts_path}")
        if not inferences_path.exists():
            raise HTTPException(status_code=404, detail=f"Inferences file not found: {request.inferences_path}")
        
        if request.inputs_path:
            inputs_path = Path(request.inputs_path)
            if not inputs_path.exists():
                raise HTTPException(status_code=404, detail=f"Inputs file not found: {request.inputs_path}")
        
        # Load graph for visualization
        graph_service.load_from_files(
            str(concepts_path),
            str(inferences_path)
        )
        
        # Load into execution controller
        result = await execution_controller.load_repositories(
            concepts_path=str(concepts_path),
            inferences_path=str(inferences_path),
            inputs_path=request.inputs_path,
            llm_model=request.llm_model,
            base_dir=request.base_dir,
            max_cycles=request.max_cycles,
            db_path=request.db_path,
            paradigm_dir=request.paradigm_dir,
        )
        
        return LoadResponse(
            success=True,
            message="Repositories loaded successfully",
            run_id=result.get("run_id"),
            total_inferences=result.get("total_inferences", 0),
            concepts_count=result.get("concepts_count", 0),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
async def list_example_repositories():
    """List available example repository sets."""
    # Look for example repositories in the project
    project_root = Path(__file__).parent.parent.parent.parent
    examples_dir = project_root / "streamlit_app" / "repository_sets"
    
    examples = []
    if examples_dir.exists():
        for subdir in examples_dir.iterdir():
            if subdir.is_dir():
                concept_file = subdir / "concept_repo.json"
                inference_file = subdir / "inference_repo.json"
                if concept_file.exists() and inference_file.exists():
                    examples.append({
                        "name": subdir.name,
                        "concepts_path": str(concept_file),
                        "inferences_path": str(inference_file),
                    })
    
    return {"examples": examples}
