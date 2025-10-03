from fastapi import APIRouter, Depends
from typing import List
import os

from schemas.inference_schemas import InferenceEntrySchema
from services.inference_service import InferenceService

# --- Constants for paths ---
EDITOR_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(EDITOR_APP_ROOT, "data")
GLOBAL_INFERENCES_NAME = "_global"  # Special name for global inferences storage

# --- Dependency ---
def get_inference_service() -> InferenceService:
    """Dependency to get inference service instance."""
    storage_dir = os.path.join(DATA_DIR, 'inferences')
    return InferenceService(storage_dir)

router = APIRouter(prefix="/api/inferences", tags=["global-inferences"])

@router.get("/", response_model=List[InferenceEntrySchema])
async def get_global_inferences(
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Retrieves all global inferences."""
    return inference_service.get_inferences(GLOBAL_INFERENCES_NAME)

@router.get("/{inference_id}", response_model=InferenceEntrySchema)
async def get_global_inference(
    inference_id: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Retrieves a single global inference by its ID."""
    return inference_service.get_inference(GLOBAL_INFERENCES_NAME, inference_id)

@router.post("/", response_model=InferenceEntrySchema)
async def add_global_inference(
    inference: InferenceEntrySchema,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Adds a new global inference."""
    return inference_service.add_inference(GLOBAL_INFERENCES_NAME, inference)

@router.put("/{inference_id}", response_model=InferenceEntrySchema)
async def update_global_inference(
    inference_id: str,
    inference_update: InferenceEntrySchema,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Updates an existing global inference."""
    return inference_service.update_inference(GLOBAL_INFERENCES_NAME, inference_id, inference_update)

@router.delete("/{inference_id}")
async def delete_global_inference(
    inference_id: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Deletes a global inference."""
    return inference_service.delete_inference(GLOBAL_INFERENCES_NAME, inference_id)

