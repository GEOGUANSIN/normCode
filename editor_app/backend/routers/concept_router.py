from fastapi import APIRouter, Depends
from typing import List
import os

from schemas.concept_schemas import ConceptEntrySchema
from schemas.repository_schemas import ErrorResponse
from services.concept_service import ConceptService

# --- Constants for paths ---
EDITOR_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(EDITOR_APP_ROOT, "data")

# --- Dependency ---
def get_concept_service() -> ConceptService:
    """Dependency to get concept service instance."""
    storage_dir = os.path.join(DATA_DIR, 'concepts')
    return ConceptService(storage_dir)

router = APIRouter(prefix="/api/repositories/{name}/concepts", tags=["concepts"])

@router.get("/", response_model=List[ConceptEntrySchema])
async def get_concepts(
    name: str,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Retrieves all concepts from a repository set."""
    return concept_service.get_concepts(name)

@router.get("/{concept_id}", response_model=ConceptEntrySchema)
async def get_concept(
    name: str,
    concept_id: str,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Retrieves a single concept by its ID."""
    return concept_service.get_concept(name, concept_id)

@router.post("/", response_model=ConceptEntrySchema)
async def add_concept(
    name: str,
    concept: ConceptEntrySchema,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Adds a new concept to a repository set."""
    return concept_service.add_concept(name, concept)

@router.put("/{concept_id}", response_model=ConceptEntrySchema)
async def update_concept(
    name: str,
    concept_id: str,
    concept_update: ConceptEntrySchema,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Updates an existing concept in a repository set."""
    return concept_service.update_concept(name, concept_id, concept_update)

@router.delete("/{concept_id}")
async def delete_concept(
    name: str,
    concept_id: str,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Deletes a concept from a repository set."""
    return concept_service.delete_concept(name, concept_id)
