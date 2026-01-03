"""Graph data endpoints with layout mode support."""
from typing import Optional, Dict, Any
import logging
from fastapi import APIRouter, HTTPException

from services.graph_service import graph_service
from services.project_service import project_service
from services.execution_service import get_execution_controller, execution_controller_registry
from schemas.graph_schemas import GraphData, GraphNode

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=GraphData)
async def get_graph():
    """Get current graph data for visualization."""
    if graph_service.current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Load repositories first.")
    return graph_service.current_graph


@router.post("/reload", response_model=GraphData)
async def reload_graph():
    """
    Reload the graph for the current project.
    
    DEPRECATED: Use /graph/swap/{project_id} for tab switching instead.
    This endpoint re-reads from disk and should only be used for actual file changes.
    """
    if not project_service.is_project_open:
        raise HTTPException(status_code=400, detail="No project is currently open")
    
    if not project_service.check_repositories_exist():
        raise HTTPException(
            status_code=404,
            detail="Repository files not found for current project"
        )
    
    try:
        paths = project_service.get_absolute_repo_paths()
        project_id = project_service.current_config.id if project_service.current_config else None
        graph_service.load_from_files(
            paths['concepts'],
            paths['inferences'],
            project_id=project_id
        )
        logger.info(f"Reloaded graph from files for project '{project_service.current_config.name}'")
        return graph_service.current_graph
    except Exception as e:
        logger.exception(f"Failed to reload graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/swap/{project_id}", response_model=GraphData)
async def swap_to_project_graph(project_id: str):
    """
    Swap to the cached graph for a specific project.
    
    This is used when switching tabs - it uses the cached graph data from
    the ExecutionController instead of re-reading from disk files.
    
    If the project's controller doesn't have cached graph data, it will
    fall back to loading from files.
    
    Args:
        project_id: The project ID to swap to
    """
    logger.info(f"[swap] Request to swap to project {project_id}")
    
    # Check if the graph is already loaded for this project
    current_project_id = graph_service.get_current_project_id()
    logger.info(f"[swap] Current graph project_id={current_project_id}, requested={project_id}")
    
    if current_project_id == project_id and graph_service.current_graph is not None:
        logger.info(f"[swap] Graph already loaded for project {project_id}, skipping swap")
        return graph_service.current_graph
    
    # Try to get cached graph from ExecutionController (user project)
    try:
        has_controller = execution_controller_registry.has_controller(project_id)
        logger.info(f"[swap] Has user controller for {project_id}: {has_controller}")
        
        if has_controller:
            controller = get_execution_controller(project_id)
            has_graph = getattr(controller, 'graph_data', None) is not None
            logger.info(f"[swap] User controller has graph_data: {has_graph}")
            
            if has_graph:
                # Use cached graph - no disk I/O needed!
                graph_nodes = len(controller.graph_data.nodes) if hasattr(controller.graph_data, 'nodes') else 0
                logger.info(f"[swap] Using cached graph from user controller ({graph_nodes} nodes)")
                return graph_service.swap_to_cached(
                    graph_data=controller.graph_data,
                    concepts_data=getattr(controller, 'concepts_data', []) or [],
                    inferences_data=getattr(controller, 'inferences_data', []) or [],
                    project_id=project_id,
                    layout_mode=graph_service.get_layout_mode()
                )
    except Exception as e:
        logger.exception(f"[swap] Error checking user controller for project {project_id}: {e}")
    
    # Try to get cached graph from chat/assistant worker (for controller projects)
    try:
        from services.execution.worker_registry import get_worker_registry
        registry = get_worker_registry()
        
        # Check for chat worker (e.g., "chat-canvas-assistant" for project "canvas-assistant")
        chat_worker_id = f"chat-{project_id}"
        chat_worker = registry.get_worker(chat_worker_id)
        
        logger.info(f"[swap] Checking chat worker {chat_worker_id}: exists={chat_worker is not None}")
        
        if chat_worker and chat_worker.controller:
            has_graph = getattr(chat_worker.controller, 'graph_data', None) is not None
            logger.info(f"[swap] Chat worker {chat_worker_id} has graph_data: {has_graph}")
            
            if has_graph:
                graph_nodes = len(chat_worker.controller.graph_data.nodes) if hasattr(chat_worker.controller.graph_data, 'nodes') else 0
                logger.info(f"[swap] Using cached graph from chat worker {chat_worker_id} ({graph_nodes} nodes)")
                return graph_service.swap_to_cached(
                    graph_data=chat_worker.controller.graph_data,
                    concepts_data=getattr(chat_worker.controller, 'concepts_data', []) or [],
                    inferences_data=getattr(chat_worker.controller, 'inferences_data', []) or [],
                    project_id=project_id,
                    layout_mode=graph_service.get_layout_mode()
                )
    except Exception as e:
        logger.exception(f"[swap] Error checking chat worker for project {project_id}: {e}")
    
    # Fall back to loading from files if no cached data
    logger.info(f"No cached graph for project {project_id}, attempting to load from files")
    
    if not project_service.is_project_open:
        raise HTTPException(
            status_code=400, 
            detail=f"No project is currently open. Cannot load graph for project {project_id}."
        )
    
    # IMPORTANT: Only load from files if the current project matches the requested project
    # Otherwise we'd be loading the wrong project's files
    current_project = project_service.current_config
    if current_project and current_project.id != project_id:
        # The requested project is different from the current project
        # This can happen for chat controller projects that aren't the "current" user project
        logger.warning(
            f"[swap] Requested project {project_id} differs from current project {current_project.id}. "
            f"No cached graph available for {project_id}."
        )
        raise HTTPException(
            status_code=404, 
            detail=f"No cached graph available for project {project_id}. "
                   f"The project may need to be loaded first."
        )
    
    if not project_service.check_repositories_exist():
        raise HTTPException(
            status_code=404,
            detail="Repository files not found for current project"
        )
    
    try:
        paths = project_service.get_absolute_repo_paths()
        graph_service.load_from_files(
            paths['concepts'],
            paths['inferences'],
            project_id=project_id
        )
        return graph_service.current_graph
    except Exception as e:
        logger.exception(f"Failed to load graph for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}")
async def get_node(node_id: str):
    """Get detailed information for a specific node."""
    node = graph_service.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
    return node


@router.get("/node/{node_id}/data")
async def get_node_data(node_id: str):
    """Get detailed data for a node including reference data."""
    data = graph_service.get_node_data(node_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Node not found: {node_id}")
    return data


@router.get("/stats")
async def get_graph_stats():
    """Get statistics about the current graph."""
    if graph_service.current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded")
    
    graph = graph_service.current_graph
    
    # Count by category
    category_counts = {}
    type_counts = {"value": 0, "function": 0}
    ground_count = 0
    final_count = 0
    
    for node in graph.nodes:
        category_counts[node.category] = category_counts.get(node.category, 0) + 1
        type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1
        if node.data.get("is_ground"):
            ground_count += 1
        if node.data.get("is_final"):
            final_count += 1
    
    # Count edge types
    edge_type_counts = {}
    for edge in graph.edges:
        edge_type_counts[edge.edge_type] = edge_type_counts.get(edge.edge_type, 0) + 1
    
    return {
        "total_nodes": len(graph.nodes),
        "total_edges": len(graph.edges),
        "category_counts": category_counts,
        "type_counts": type_counts,
        "ground_concepts": ground_count,
        "final_concepts": final_count,
        "edge_type_counts": edge_type_counts,
        "layout_mode": graph_service.get_layout_mode(),
    }


@router.get("/layout")
async def get_layout_mode():
    """Get the current layout mode."""
    return {"layout_mode": graph_service.get_layout_mode()}


@router.post("/layout/{layout_mode}", response_model=GraphData)
async def set_layout_mode(layout_mode: str):
    """Set the layout mode and recalculate positions.
    
    Args:
        layout_mode: "hierarchical" or "flow_aligned"
    """
    if layout_mode not in ["hierarchical", "flow_aligned"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid layout mode: {layout_mode}. Must be 'hierarchical' or 'flow_aligned'"
        )
    
    result = graph_service.set_layout_mode(layout_mode)
    if result is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Load repositories first.")
    
    return result
