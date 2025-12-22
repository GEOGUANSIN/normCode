from fastapi import APIRouter, Depends, HTTPException
import os

from schemas.repository_schemas import (
    RunRepositorySetRequest,
    RunResponse,
    LogContentResponse,
    ErrorResponse
)
from services.repository_service import RepositoryService
from services.normcode_execution_service import NormcodeExecutionService
from services.concept_service import ConceptService
from services.inference_service import InferenceService


# --- Constants for paths ---
EDITOR_APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_DIR = os.path.join(EDITOR_APP_ROOT, "data")


# --- Dependencies ---
def get_concept_service() -> ConceptService:
    """Dependency to get concept service instance."""
    storage_dir = os.path.join(DATA_DIR, 'concepts')
    repositories_dir = os.path.join(DATA_DIR, 'repositories')
    return ConceptService(storage_dir, repositories_dir)

def get_inference_service() -> InferenceService:
    """Dependency to get inference service instance."""
    storage_dir = os.path.join(DATA_DIR, 'inferences')
    repositories_dir = os.path.join(DATA_DIR, 'repositories')
    return InferenceService(storage_dir, repositories_dir)

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
    logs_dir = os.path.join(DATA_DIR, 'logs')
    return NormcodeExecutionService(project_root, logs_dir)


router = APIRouter(prefix="/api/repositories", tags=["execution"])


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
