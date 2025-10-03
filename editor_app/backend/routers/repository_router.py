from fastapi import APIRouter, Depends
from typing import List
import os

from schemas.repository_schemas import (
    RepositorySetSchema,
    RepositorySetData,
    ErrorResponse
)
from services.repository_service import RepositoryService
from services.concept_service import ConceptService
from services.inference_service import InferenceService


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
