"""Graph data endpoints with layout mode support."""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException

from services.graph_service import graph_service
from schemas.graph_schemas import GraphData, GraphNode

router = APIRouter()


@router.get("", response_model=GraphData)
async def get_graph():
    """Get current graph data for visualization."""
    if graph_service.current_graph is None:
        raise HTTPException(status_code=404, detail="No graph loaded. Load repositories first.")
    return graph_service.current_graph


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
