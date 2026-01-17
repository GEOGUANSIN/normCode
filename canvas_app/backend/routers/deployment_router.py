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
# Remote Graph & Project Loading
# =============================================================================

@router.get("/servers/{server_id}/plans/{plan_id}/graph")
async def get_remote_plan_graph(server_id: str, plan_id: str):
    """
    Get the full graph data (concepts + inferences) for a remote plan.
    Enables Canvas to load and render a plan from a remote server.
    """
    try:
        return deployment_service.get_remote_plan_graph(server_id, plan_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get plan graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/plans/{plan_id}/canvas-graph")
async def get_remote_plan_canvas_graph(server_id: str, plan_id: str):
    """
    Get the remote plan graph in Canvas-ready GraphData format (nodes + edges).
    
    This fetches the raw concepts/inferences from the remote server and
    transforms them into the GraphData format used by the Canvas visualization.
    
    Returns:
        GraphData-compatible dict with nodes and edges ready for canvas rendering
    """
    from services.graph_service import build_graph_from_repositories
    
    try:
        # Fetch raw data from remote server
        raw_graph = deployment_service.get_remote_plan_graph(server_id, plan_id)
        
        concepts = raw_graph.get('concepts', [])
        inferences = raw_graph.get('inferences', [])
        
        # Transform to GraphData format
        graph_data = build_graph_from_repositories(concepts, inferences)
        
        return {
            "plan_id": plan_id,
            "plan_name": raw_graph.get('plan_name', plan_id),
            "server_id": server_id,
            "nodes": [node.model_dump() for node in graph_data.nodes],
            "edges": [edge.model_dump() for edge in graph_data.edges],
            # Include raw data for execution context
            "concepts_count": len(concepts),
            "inferences_count": len(inferences),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get canvas graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/plans/{plan_id}/files/{file_path:path}")
async def get_remote_plan_file(server_id: str, plan_id: str, file_path: str):
    """Get a specific file from a remote plan's directory."""
    try:
        return deployment_service.get_remote_plan_file(server_id, plan_id, file_path)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get plan file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/runs")
async def list_remote_runs(server_id: str, include_historical: bool = True):
    """List all runs on a remote server (active + historical)."""
    try:
        return deployment_service.list_remote_runs(server_id, include_historical)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to list remote runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Remote Run Database Inspection
# =============================================================================

@router.get("/runs/{server_id}/{run_id}/db/overview")
async def get_remote_run_db_overview(server_id: str, run_id: str):
    """Get database overview for a remote run."""
    try:
        return deployment_service.get_remote_run_db_overview(server_id, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get DB overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{server_id}/{run_id}/db/executions")
async def get_remote_run_executions(
    server_id: str,
    run_id: str,
    include_logs: bool = False,
    limit: int = 500,
    offset: int = 0,
):
    """Get execution history for a remote run."""
    try:
        return deployment_service.get_remote_run_executions(
            server_id, run_id, include_logs, limit, offset
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get executions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{server_id}/{run_id}/db/executions/{execution_id}/logs")
async def get_remote_execution_logs(server_id: str, run_id: str, execution_id: int):
    """Get logs for a specific execution in a remote run."""
    try:
        return deployment_service.get_remote_execution_logs(server_id, run_id, execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get execution logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{server_id}/{run_id}/db/statistics")
async def get_remote_run_statistics(server_id: str, run_id: str):
    """Get statistics for a remote run."""
    try:
        return deployment_service.get_remote_run_statistics(server_id, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get run statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{server_id}/{run_id}/db/checkpoints")
async def list_remote_run_checkpoints(server_id: str, run_id: str):
    """List checkpoints for a remote run."""
    try:
        return deployment_service.list_remote_run_checkpoints(server_id, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to list checkpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{server_id}/{run_id}/db/checkpoints/{cycle}")
async def get_remote_checkpoint_state(
    server_id: str,
    run_id: str,
    cycle: int,
    inference_count: Optional[int] = None,
):
    """Get checkpoint state for a remote run."""
    try:
        return deployment_service.get_remote_checkpoint_state(
            server_id, run_id, cycle, inference_count
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get checkpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{server_id}/{run_id}/db/blackboard")
async def get_remote_blackboard_summary(
    server_id: str,
    run_id: str,
    cycle: Optional[int] = None,
):
    """Get blackboard summary for a remote run."""
    try:
        return deployment_service.get_remote_blackboard_summary(server_id, run_id, cycle)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get blackboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{server_id}/{run_id}/db/concepts")
async def get_remote_completed_concepts(
    server_id: str,
    run_id: str,
    cycle: Optional[int] = None,
):
    """Get completed concepts for a remote run."""
    try:
        return deployment_service.get_remote_completed_concepts(server_id, run_id, cycle)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to get concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{server_id}/{run_id}/resume")
async def resume_remote_run(
    server_id: str,
    run_id: str,
    cycle: Optional[int] = None,
    inference_count: Optional[int] = None,
    llm_model: Optional[str] = None,
    fork: bool = False,
):
    """Resume a run from a checkpoint on a remote server."""
    try:
        return deployment_service.resume_remote_run(
            server_id, run_id, cycle, inference_count, llm_model, fork
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to resume run: {e}")
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


# =============================================================================
# Remote Run Binding (Mirror remote execution to local canvas)
# =============================================================================

@router.post("/runs/{server_id}/{run_id}/bind")
async def bind_remote_run(server_id: str, run_id: str, plan_id: str = "", plan_name: str = ""):
    """
    Bind a remote run to the local canvas.
    
    This starts streaming execution events from the remote server and relaying
    them to the local frontend via WebSocket. The canvas will show real-time
    updates of node statuses, progress, and logs from the remote execution.
    
    Args:
        server_id: ID of the deployment server
        run_id: ID of the run to bind
        plan_id: Optional plan ID for display
        plan_name: Optional plan name for display
    """
    from services.remote_run_service import remote_run_service
    
    try:
        server = deployment_service._servers.get(server_id)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server not found: {server_id}")
        
        success = await remote_run_service.bind_run(
            server_id=server_id,
            server_url=server.url,
            run_id=run_id,
            plan_id=plan_id,
            plan_name=plan_name or plan_id,
        )
        
        if success:
            return {
                "status": "bound",
                "run_id": run_id,
                "server_id": server_id,
                "message": f"Remote run bound to canvas. Events will be streamed.",
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to bind remote run")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to bind remote run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{server_id}/{run_id}/unbind")
async def unbind_remote_run(server_id: str, run_id: str):
    """
    Unbind a remote run from the local canvas.
    
    Stops streaming events from the remote server for this run.
    """
    from services.remote_run_service import remote_run_service
    
    try:
        success = await remote_run_service.unbind_run(run_id)
        
        if success:
            return {
                "status": "unbound",
                "run_id": run_id,
                "server_id": server_id,
            }
        else:
            raise HTTPException(status_code=404, detail=f"Run not bound: {run_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to unbind remote run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bound-runs")
async def list_bound_runs():
    """List all remote runs currently bound to the canvas."""
    from services.remote_run_service import remote_run_service
    
    return {
        "bound_runs": remote_run_service.list_bound_runs(),
    }


# =============================================================================
# Remote Execution Control (for bound runs)
# =============================================================================

@router.post("/runs/{server_id}/{run_id}/pause")
async def pause_remote_run(server_id: str, run_id: str):
    """Pause a running remote execution."""
    try:
        return deployment_service.control_remote_run(server_id, run_id, "pause")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to pause remote run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{server_id}/{run_id}/continue")
async def continue_remote_run(server_id: str, run_id: str):
    """Resume a paused remote execution."""
    try:
        return deployment_service.control_remote_run(server_id, run_id, "continue")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to resume remote run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{server_id}/{run_id}/step")
async def step_remote_run(server_id: str, run_id: str):
    """Execute one inference on a remote run then pause."""
    try:
        return deployment_service.control_remote_run(server_id, run_id, "step")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to step remote run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{server_id}/{run_id}/stop")
async def stop_remote_run(server_id: str, run_id: str):
    """Stop a remote execution gracefully."""
    try:
        return deployment_service.control_remote_run(server_id, run_id, "stop")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to stop remote run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

