from fastapi import APIRouter, Depends
from typing import List
import os

from schemas.concept_schemas import ConceptEntrySchema
from schemas.repository_schemas import ErrorResponse, AddConceptFromGlobalRequest
from services.concept_service import ConceptService
from services.repository_service import RepositoryService
from services.inference_service import InferenceService


# --- Constants for paths ---
EDITOR_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(EDITOR_APP_ROOT, "data")

# --- Dependency ---
def get_concept_service() -> ConceptService:
    """Dependency to get concept service instance."""
    concepts_dir = os.path.join(DATA_DIR, 'concepts')
    repositories_dir = os.path.join(DATA_DIR, 'repositories')
    return ConceptService(concepts_dir, repositories_dir)

def get_inference_service() -> InferenceService:
    """Dependency to get inference service instance."""
    inferences_dir = os.path.join(DATA_DIR, 'inferences')
    repositories_dir = os.path.join(DATA_DIR, 'repositories')
    return InferenceService(inferences_dir, repositories_dir)


def get_repository_service(
    concept_service: ConceptService = Depends(get_concept_service),
    inference_service: InferenceService = Depends(get_inference_service)
) -> RepositoryService:
    """Dependency to get repository service instance."""
    repo_storage_dir = os.path.join(DATA_DIR, 'repositories')
    return RepositoryService(repo_storage_dir, concept_service, inference_service)


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


@router.post("/from_global", response_model=ConceptEntrySchema, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def add_concept_from_global(
    name: str,
    request: AddConceptFromGlobalRequest,
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Adds a concept from global to a repository with reference data."""
    return repo_service.add_global_concept_to_repository(
        name=name,
        global_concept_id=request.global_concept_id,
        reference_data=request.reference_data,
        reference_axis_names=request.reference_axis_names,
        is_ground_concept=request.is_ground_concept,
        is_final_concept=request.is_final_concept,
        is_invariant=request.is_invariant
    )


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
