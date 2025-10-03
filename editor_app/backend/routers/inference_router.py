from fastapi import APIRouter, Depends
from typing import List
import os

from schemas.inference_schemas import InferenceEntrySchema
from services.inference_service import InferenceService

# --- Constants for paths ---
EDITOR_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(EDITOR_APP_ROOT, "data")

# --- Dependency ---
def get_inference_service() -> InferenceService:
    """Dependency to get inference service instance."""
    storage_dir = os.path.join(DATA_DIR, 'inferences')
    return InferenceService(storage_dir)

router = APIRouter(prefix="/api/repositories/{name}/inferences", tags=["inferences"])

@router.get("/", response_model=List[InferenceEntrySchema])
async def get_inferences(
    name: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Retrieves all inferences from a repository set."""
    return inference_service.get_inferences(name)

@router.get("/{inference_id}", response_model=InferenceEntrySchema)
async def get_inference(
    name: str,
    inference_id: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Retrieves a single inference by its ID."""
    return inference_service.get_inference(name, inference_id)

@router.post("/", response_model=InferenceEntrySchema)
async def add_inference(
    name: str,
    inference: InferenceEntrySchema,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Adds a new inference to a repository set."""
    return inference_service.add_inference(name, inference)

@router.put("/{inference_id}", response_model=InferenceEntrySchema)
async def update_inference(
    name: str,
    inference_id: str,
    inference_update: InferenceEntrySchema,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Updates an existing inference in a repository set."""
    return inference_service.update_inference(name, inference_id, inference_update)

@router.delete("/{inference_id}")
async def delete_inference(
    name: str,
    inference_id: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Deletes an inference from a repository set."""
    return inference_service.delete_inference(name, inference_id)
