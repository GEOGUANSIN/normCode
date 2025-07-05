from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from models.graph_models import Node, Edge, GraphResponse, ErrorResponse
from services.graph_service import GraphService
from services.normcode_translator import NormCodeTranslator

router = APIRouter(prefix="/api/v1", tags=["graph"])

def get_graph_service() -> GraphService:
    """Dependency injection for GraphService"""
    return GraphService()

def get_normcode_translator() -> NormCodeTranslator:
    """Dependency injection for NormCodeTranslator"""
    return NormCodeTranslator()

@router.get("/", response_model=Dict[str, str])
async def read_root():
    """Root endpoint"""
    return {"message": "Welcome to the Flow Graph API"}

@router.get("/nodes", response_model=List[Dict[str, Any]])
async def get_nodes(graph_service: GraphService = Depends(get_graph_service)):
    """Get all nodes"""
    return graph_service.get_all_nodes()

@router.get("/edges", response_model=List[Dict[str, Any]])
async def get_edges(graph_service: GraphService = Depends(get_graph_service)):
    """Get all edges"""
    return graph_service.get_all_edges()

@router.post("/nodes", response_model=Dict[str, Any])
async def create_node(
    node: Node,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Create a new node"""
    try:
        return graph_service.create_node(node)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/edges", response_model=Dict[str, Any])
async def create_edge(
    edge: Edge,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Create a new edge"""
    try:
        return graph_service.create_edge(edge)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)}
        )

@router.delete("/nodes/{node_id}", response_model=Dict[str, str])
async def delete_node(
    node_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Delete a node and its connected edges"""
    try:
        message = graph_service.delete_node(node_id)
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/edges/{edge_id}", response_model=Dict[str, str])
async def delete_edge(
    edge_id: str,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Delete an edge"""
    try:
        message = graph_service.delete_edge(edge_id)
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/nodes/{node_id}", response_model=Node)
async def update_node(
    node_id: str,
    node: Node,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Update an existing node"""
    try:
        return graph_service.update_node(node_id, node)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save", response_model=GraphResponse)
async def save_graph(graph_service: GraphService = Depends(get_graph_service)):
    """Explicitly save the current state of the graph"""
    try:
        result = graph_service.save_graph()
        return GraphResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save graph: {str(e)}")

@router.post("/load", response_model=GraphResponse)
async def load_graph(graph_service: GraphService = Depends(get_graph_service)):
    """Explicitly load the graph from files"""
    try:
        result = graph_service.load_graph()
        return GraphResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load graph: {str(e)}")

@router.post("/normcode/translate", response_model=GraphResponse)
async def translate_normcode(
    request: Dict[str, str],
    graph_service: GraphService = Depends(get_graph_service),
    translator: NormCodeTranslator = Depends(get_normcode_translator)
):
    """Translate NormCode horizontal layout into graph data"""
    try:
        normcode_text = request.get("normcode_text", "")
        if not normcode_text:
            raise HTTPException(status_code=400, detail="normcode_text is required")
        
        # Translate NormCode to graph data
        nodes, edges = translator.parse_horizontal_layout(normcode_text)
        
        # Clear existing data and add new translated data
        graph_service.buffer_nodes = nodes
        graph_service.buffer_edges = edges
        
        # Save the translated graph
        result = graph_service.save_graph()
        
        return GraphResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to translate NormCode: {str(e)}")

@router.post("/normcode/preview", response_model=Dict[str, Any])
async def preview_normcode_translation(
    request: Dict[str, str],
    translator: NormCodeTranslator = Depends(get_normcode_translator)
):
    """Preview NormCode translation without saving to graph"""
    try:
        normcode_text = request.get("normcode_text", "")
        if not normcode_text:
            raise HTTPException(status_code=400, detail="normcode_text is required")
        
        # Translate NormCode to graph data
        nodes, edges = translator.parse_horizontal_layout(normcode_text)
        
        return {
            "message": "NormCode translation preview",
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview NormCode translation: {str(e)}") 