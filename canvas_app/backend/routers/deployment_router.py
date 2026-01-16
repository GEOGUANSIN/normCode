"""Deployment management router."""
import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException

from schemas.deployment_schemas import (
    DeploymentServer,
    DeploymentServerList,
    AddServerRequest,
    UpdateServerRequest,
    ServerHealthResponse,
    DeployProjectRequest,
    DeployProjectResponse,
    RemotePlan,
    RemotePlanList,
    StartRemoteRunRequest,
    RemoteRunStatus,
    RemoteRunResult,
    BuildServerRequest,
    BuildServerResponse,
)
from services.deployment_service import deployment_service

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Server Management
# =============================================================================

@router.get("/servers", response_model=DeploymentServerList)
async def list_servers():
    """Get all registered deployment servers."""
    servers = deployment_service.get_servers()
    return DeploymentServerList(servers=servers)


@router.get("/servers/{server_id}", response_model=DeploymentServer)
async def get_server(server_id: str):
    """Get a specific deployment server."""
    server = deployment_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")
    return server


@router.post("/servers", response_model=DeploymentServer)
async def add_server(request: AddServerRequest):
    """Add a new deployment server."""
    try:
        server = deployment_service.add_server(
            name=request.name,
            url=request.url,
            description=request.description,
            is_default=request.is_default,
        )
        return server
    except Exception as e:
        logger.exception(f"Failed to add server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/servers/{server_id}", response_model=DeploymentServer)
async def update_server(server_id: str, request: UpdateServerRequest):
    """Update a deployment server."""
    try:
        server = deployment_service.update_server(
            server_id=server_id,
            name=request.name,
            url=request.url,
            description=request.description,
            is_default=request.is_default,
        )
        return server
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to update server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/servers/{server_id}")
async def remove_server(server_id: str):
    """Remove a deployment server."""
    deployment_service.remove_server(server_id)
    return {"status": "removed", "server_id": server_id}


# =============================================================================
# Server Health & Info
# =============================================================================

@router.get("/servers/{server_id}/health", response_model=ServerHealthResponse)
async def check_server_health(server_id: str):
    """Check the health of a deployment server."""
    return deployment_service.check_server_health(server_id)


@router.post("/servers/test-connection", response_model=ServerHealthResponse)
async def test_server_connection(url: str):
    """
    Test connection to a server URL without adding it.
    
    Useful for validating a server URL before adding.
    """
    import uuid
    
    # Create a temporary server entry for testing
    temp_id = f"temp-{uuid.uuid4().hex[:8]}"
    try:
        deployment_service._servers[temp_id] = DeploymentServer(
            id=temp_id,
            name="Test",
            url=url.rstrip('/'),
        )
        result = deployment_service.check_server_health(temp_id)
        return result
    finally:
        # Remove temporary entry
        if temp_id in deployment_service._servers:
            del deployment_service._servers[temp_id]


# =============================================================================
# Deployment
# =============================================================================

@router.post("/deploy", response_model=DeployProjectResponse)
async def deploy_project(request: DeployProjectRequest):
    """
    Deploy a project to a remote server.
    
    Packages the project and uploads it to the specified deployment server.
    """
    try:
        result = deployment_service.deploy_project(
            server_id=request.server_id,
            project_id=request.project_id,
        )
        return DeployProjectResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception(f"Deployment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Remote Plans
# =============================================================================

@router.get("/servers/{server_id}/plans", response_model=RemotePlanList)
async def list_remote_plans(server_id: str):
    """List plans deployed on a remote server."""
    server = deployment_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")
    
    plans = deployment_service.list_remote_plans(server_id)
    return RemotePlanList(
        server_id=server_id,
        server_name=server.name,
        plans=plans,
    )


# =============================================================================
# Remote Runs
# =============================================================================

@router.post("/runs", response_model=RemoteRunStatus)
async def start_remote_run(request: StartRemoteRunRequest):
    """Start a run on a remote server."""
    try:
        return deployment_service.start_remote_run(
            server_id=request.server_id,
            plan_id=request.plan_id,
            llm_model=request.llm_model,
            ground_inputs=request.ground_inputs,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to start remote run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{server_id}/{run_id}", response_model=RemoteRunStatus)
async def get_remote_run_status(server_id: str, run_id: str):
    """Get status of a remote run."""
    try:
        return deployment_service.get_remote_run_status(server_id, run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{server_id}/{run_id}/result")
async def get_remote_run_result(server_id: str, run_id: str):
    """Get result of a completed remote run."""
    try:
        return deployment_service.get_remote_run_result(server_id, run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Server Building
# =============================================================================

@router.post("/build-server", response_model=BuildServerResponse)
async def build_server(request: BuildServerRequest):
    """
    Build a self-contained deployment server package.
    
    Creates a standalone server that can run anywhere to execute NormCode plans.
    The built server includes all necessary components: runner, tools, infra library,
    and test clients.
    
    After building, you can:
    1. Navigate to the output directory
    2. Install dependencies: pip install -r requirements.txt
    3. Start the server: python start_server.py
    """
    from pathlib import Path
    
    try:
        output_dir = Path(request.output_dir) if request.output_dir else None
        result = deployment_service.build_server(
            output_dir=output_dir,
            include_test_plans=request.include_test_plans,
            create_zip=request.create_zip,
        )
        return result
    except Exception as e:
        logger.exception(f"Failed to build server: {e}")
        raise HTTPException(status_code=500, detail=str(e))

