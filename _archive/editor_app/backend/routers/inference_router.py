from fastapi import APIRouter, Depends
from typing import List
import os

from schemas.inference_schemas import InferenceEntrySchema
from services.inference_service import InferenceService
from schemas.repository_schemas import AddInferenceFromGlobalRequest, ErrorResponse
from services.repository_service import RepositoryService
from services.concept_service import ConceptService

# --- Constants for paths ---
EDITOR_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(EDITOR_APP_ROOT, "data")

# --- Dependency ---
def get_inference_service() -> InferenceService:
    """Dependency to get inference service instance."""
    inferences_dir = os.path.join(DATA_DIR, 'inferences')
    repositories_dir = os.path.join(DATA_DIR, 'repositories')
    return InferenceService(inferences_dir, repositories_dir)

def get_concept_service() -> ConceptService:
    """Dependency to get concept service instance."""
    concepts_dir = os.path.join(DATA_DIR, 'concepts')
    repositories_dir = os.path.join(DATA_DIR, 'repositories')
    return ConceptService(concepts_dir, repositories_dir)

def get_repository_service(
    concept_service: ConceptService = Depends(get_concept_service),
    inference_service: InferenceService = Depends(get_inference_service)
) -> RepositoryService:
    """Dependency to get repository service instance."""
    repo_storage_dir = os.path.join(DATA_DIR, 'repositories')
    return RepositoryService(repo_storage_dir, concept_service, inference_service)


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


@router.post("/from_global", response_model=InferenceEntrySchema, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def add_inference_from_global(
    name: str,
    request: AddInferenceFromGlobalRequest,
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Adds an inference from global to a repository with specific data."""
    return repo_service.add_global_inference_to_repository(
        name=name,
        global_inference_id=request.global_inference_id,
        flow_info=request.flow_info,
        working_interpretation=request.working_interpretation,
        start_without_value=request.start_without_value,
        start_without_value_only_once=request.start_without_value_only_once,
        start_without_function=request.start_without_function,
        start_without_function_only_once=request.start_without_function_only_once,
        start_with_support_reference_only=request.start_with_support_reference_only
    )


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
