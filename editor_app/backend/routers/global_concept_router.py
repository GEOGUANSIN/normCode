from fastapi import APIRouter, Depends
from typing import List
import os

from schemas.concept_schemas import ConceptEntrySchema
from schemas.repository_schemas import ErrorResponse
from services.concept_service import ConceptService

# --- Constants for paths ---
EDITOR_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(EDITOR_APP_ROOT, "data")
GLOBAL_CONCEPTS_NAME = "_global"  # Special name for global concepts storage

# --- Dependency ---
def get_concept_service() -> ConceptService:
    """Dependency to get concept service instance."""
    storage_dir = os.path.join(DATA_DIR, 'concepts')
    return ConceptService(storage_dir)

router = APIRouter(prefix="/api/concepts", tags=["global-concepts"])

@router.get("/", response_model=List[ConceptEntrySchema])
async def get_global_concepts(
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Retrieves all global concepts."""
    return concept_service.get_concepts(GLOBAL_CONCEPTS_NAME)

@router.get("/{concept_id}", response_model=ConceptEntrySchema)
async def get_global_concept(
    concept_id: str,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Retrieves a single global concept by its ID."""
    return concept_service.get_concept(GLOBAL_CONCEPTS_NAME, concept_id)

@router.post("/", response_model=ConceptEntrySchema)
async def add_global_concept(
    concept: ConceptEntrySchema,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Adds a new global concept."""
    return concept_service.add_concept(GLOBAL_CONCEPTS_NAME, concept)

@router.put("/{concept_id}", response_model=ConceptEntrySchema)
async def update_global_concept(
    concept_id: str,
    concept_update: ConceptEntrySchema,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Updates an existing global concept."""
    return concept_service.update_concept(GLOBAL_CONCEPTS_NAME, concept_id, concept_update)

@router.delete("/{concept_id}")
async def delete_global_concept(
    concept_id: str,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Deletes a global concept."""
    return concept_service.delete_concept(GLOBAL_CONCEPTS_NAME, concept_id)


@router.get("/health")
async def health_check():
    return {"status": "ok"}

