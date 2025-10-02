from fastapi import APIRouter, Depends, HTTPException
from typing import List
import os

from schemas.repository_schemas import (
    RepositorySetSchema,
    RepositorySetData,
    RepositorySetListResponse,
    RepositorySetResponse,
    RepositorySetSaveResponse,
    RunRepositorySetRequest,
    RunResponse,
    LogContentResponse,
    ErrorResponse,
    ConceptEntrySchema,
    InferenceEntrySchema
)
from services.repository_service import RepositoryService
from services.concept_service import ConceptService
from services.inference_service import InferenceService
from services.normcode_execution_service import NormcodeExecutionService


# --- Constants for paths ---
EDITOR_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(EDITOR_APP_ROOT, "data")


# --- Dependencies ---
def get_concept_service() -> ConceptService:
    """Dependency to get concept service instance."""
    storage_dir = os.path.join(DATA_DIR, 'concepts')
    return ConceptService(storage_dir)


def get_inference_service() -> InferenceService:
    """Dependency to get inference service instance."""
    storage_dir = os.path.join(DATA_DIR, 'inferences')
    return InferenceService(storage_dir)


def get_repository_service(
    concept_service: ConceptService = Depends(get_concept_service),
    inference_service: InferenceService = Depends(get_inference_service)
) -> RepositoryService:
    """Dependency to get repository service instance."""
    repo_storage_dir = os.path.join(DATA_DIR, 'repositories')
    return RepositoryService(repo_storage_dir, concept_service, inference_service)


def get_normcode_execution_service() -> NormcodeExecutionService:
    """Dependency to get normcode execution service instance."""
    project_root = os.path.abspath(os.path.join(EDITOR_APP_ROOT, '..'))
    # Logs directory for normcode execution logs (e.g., in 'logs' subdirectory within repo_storage_dir)
    logs_dir = os.path.join(DATA_DIR, 'logs')
    return NormcodeExecutionService(project_root, logs_dir)


router = APIRouter(prefix="/api/repositories", tags=["repositories"])


# --- Repository Management Endpoints ---

@router.post("/", response_model=RepositorySetSchema, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def create_repository_set(
    repo_set: RepositorySetSchema,
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Creates a new RepositorySet."""
    return repo_service.create_repository_set(repo_set)


@router.get("/", response_model=List[RepositorySetSchema], responses={500: {"model": ErrorResponse}})
async def list_repository_sets(
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Lists all available RepositorySets."""
    return repo_service.get_all_repository_sets()


@router.get("/{name}", response_model=RepositorySetSchema, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_repository_set(
    name: str,
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Retrieves a specific RepositorySet by name."""
    return repo_service.get_repository_set(name)


@router.get("/{name}/data", response_model=RepositorySetData, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_repository_set_data(
    name: str,
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Retrieves the full data for a specific RepositorySet by name."""
    return repo_service.get_repository_set_data(name)


@router.delete("/{name}", responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def delete_repository_set(
    name: str,
    repo_service: RepositoryService = Depends(get_repository_service)
):
    """Deletes a specific RepositorySet by name."""
    return repo_service.delete_repository_set(name)


# --- Concept Management Endpoints ---

@router.get("/{name}/concepts", response_model=List[ConceptEntrySchema])
async def get_concepts(
    name: str,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Retrieves all concepts from a repository set."""
    return concept_service.get_concepts(name)

@router.get("/{name}/concepts/{concept_id}", response_model=ConceptEntrySchema)
async def get_concept(
    name: str,
    concept_id: str,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Retrieves a single concept by its ID."""
    return concept_service.get_concept(name, concept_id)

@router.post("/{name}/concepts", response_model=ConceptEntrySchema)
async def add_concept(
    name: str,
    concept: ConceptEntrySchema,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Adds a new concept to a repository set."""
    return concept_service.add_concept(name, concept)

@router.put("/{name}/concepts/{concept_id}", response_model=ConceptEntrySchema)
async def update_concept(
    name: str,
    concept_id: str,
    concept_update: ConceptEntrySchema,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Updates an existing concept in a repository set."""
    return concept_service.update_concept(name, concept_id, concept_update)

@router.delete("/{name}/concepts/{concept_id}")
async def delete_concept(
    name: str,
    concept_id: str,
    concept_service: ConceptService = Depends(get_concept_service)
):
    """Deletes a concept from a repository set."""
    return concept_service.delete_concept(name, concept_id)


# --- Inference Management Endpoints ---

@router.get("/{name}/inferences", response_model=List[InferenceEntrySchema])
async def get_inferences(
    name: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Retrieves all inferences from a repository set."""
    return inference_service.get_inferences(name)

@router.get("/{name}/inferences/{inference_id}", response_model=InferenceEntrySchema)
async def get_inference(
    name: str,
    inference_id: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Retrieves a single inference by its ID."""
    return inference_service.get_inference(name, inference_id)

@router.post("/{name}/inferences", response_model=InferenceEntrySchema)
async def add_inference(
    name: str,
    inference: InferenceEntrySchema,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Adds a new inference to a repository set."""
    return inference_service.add_inference(name, inference)

@router.put("/{name}/inferences/{inference_id}", response_model=InferenceEntrySchema)
async def update_inference(
    name: str,
    inference_id: str,
    inference_update: InferenceEntrySchema,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Updates an existing inference in a repository set."""
    return inference_service.update_inference(name, inference_id, inference_update)

@router.delete("/{name}/inferences/{inference_id}")
async def delete_inference(
    name: str,
    inference_id: str,
    inference_service: InferenceService = Depends(get_inference_service)
):
    """Deletes an inference from a repository set."""
    return inference_service.delete_inference(name, inference_id)


# --- Normcode Execution Endpoints ---

@router.post("/run", response_model=RunResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def run_normcode_repository_set(
    request: RunRepositorySetRequest,
    repo_service: RepositoryService = Depends(get_repository_service),
    exec_service: NormcodeExecutionService = Depends(get_normcode_execution_service)
):
    """Runs a specified RepositorySet using the normcode engine."""
    repo_set_data = repo_service.get_repository_set_data(request.repository_set_name)
    log_file = exec_service.run_repository_set(repo_set_data)
    return RunResponse(status="started", log_file=log_file)


@router.get("/logs/{log_filename}", response_model=LogContentResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_normcode_logs(
    log_filename: str,
    exec_service: NormcodeExecutionService = Depends(get_normcode_execution_service)
):
    """Retrieves the content of a specific normcode execution log file."""
    content = exec_service.get_log_content(log_filename)
    return LogContentResponse(content=content)
