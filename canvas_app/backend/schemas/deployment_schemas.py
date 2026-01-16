"""Schemas for deployment functionality."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DeploymentServer(BaseModel):
    """Configuration for a deployment server."""
    id: str = Field(..., description="Unique identifier for the server")
    name: str = Field(..., description="Display name")
    url: str = Field(..., description="Server URL (e.g., http://localhost:8080)")
    description: Optional[str] = Field(None, description="Optional description")
    is_default: bool = Field(False, description="Whether this is the default server")
    added_at: Optional[datetime] = None


class DeploymentServerList(BaseModel):
    """List of deployment servers."""
    servers: List[DeploymentServer]


class AddServerRequest(BaseModel):
    """Request to add a new deployment server."""
    name: str = Field(..., description="Display name for the server")
    url: str = Field(..., description="Server URL")
    description: Optional[str] = None
    is_default: bool = False


class UpdateServerRequest(BaseModel):
    """Request to update a deployment server."""
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None


class ServerHealthResponse(BaseModel):
    """Response from server health check."""
    server_id: str
    url: str
    is_healthy: bool
    status: str
    plans_count: Optional[int] = None
    active_runs: Optional[int] = None
    available_models: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class DeployProjectRequest(BaseModel):
    """Request to deploy a project to a server."""
    server_id: str = Field(..., description="Target server ID")
    project_id: Optional[str] = Field(None, description="Project ID to deploy (uses current if not specified)")


class DeployProjectResponse(BaseModel):
    """Response from deploying a project."""
    success: bool
    server_id: str
    server_name: str
    plan_id: str
    plan_name: str
    message: str
    deployed_at: Optional[datetime] = None


class RemotePlan(BaseModel):
    """A plan deployed on a remote server."""
    id: str
    name: str
    description: Optional[str] = None
    inputs: Dict[str, Any] = {}
    outputs: Dict[str, Any] = {}


class RemotePlanList(BaseModel):
    """List of plans on a remote server."""
    server_id: str
    server_name: str
    plans: List[RemotePlan]


class StartRemoteRunRequest(BaseModel):
    """Request to start a run on a remote server."""
    server_id: str = Field(..., description="Target server ID")
    plan_id: str = Field(..., description="Plan ID to run")
    llm_model: Optional[str] = Field(None, description="LLM model to use")
    ground_inputs: Optional[Dict[str, Any]] = Field(None, description="Input values for ground concepts")


class RemoteRunStatus(BaseModel):
    """Status of a remote run."""
    run_id: str
    plan_id: str
    server_id: str
    status: str  # pending, running, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class RemoteRunResult(BaseModel):
    """Result from a completed remote run."""
    run_id: str
    plan_id: str
    server_id: str
    status: str
    final_concepts: List[Dict[str, Any]]


# =============================================================================
# Server Building
# =============================================================================

class BuildServerRequest(BaseModel):
    """Request to build a deployment server package."""
    output_dir: Optional[str] = Field(
        None, 
        description="Output directory (default: deployment/dist/normcode-server)"
    )
    include_test_plans: bool = Field(
        False, 
        description="Include test plans in the build"
    )
    create_zip: bool = Field(
        True, 
        description="Create a zip archive of the server"
    )


class BuildServerResponse(BaseModel):
    """Response from building a deployment server."""
    success: bool
    output_dir: str
    zip_path: Optional[str] = None
    message: str
    server_name: str = "normcode-server"
    files_included: List[str] = []
