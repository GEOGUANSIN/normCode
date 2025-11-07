from pydantic import BaseModel, validator
from typing import Dict, Any, Optional
from schemas.config import settings

class Position(BaseModel):
    """Position model for node coordinates"""
    x: float
    y: float

class NodeData(BaseModel):
    """Data model for node content"""
    label: str

class Node(BaseModel):
    """Node model representing a vertex in the graph"""
    id: str
    type: str  # This will always be a string like 'red', 'pink', etc.
    data: NodeData
    position: Position

    @validator('type')
    def validate_type(cls, v):
        valid_types = settings.valid_node_types
        if v not in valid_types:
            raise ValueError(f'Invalid node type: {v}. Must be one of {valid_types}')
        return v

class Edge(BaseModel):
    """Edge model representing a connection between nodes"""
    id: str
    source: str
    target: str
    type: str = "custom"
    style: Dict[str, Any] = {"stroke": "#34495e", "strokeWidth": 1.5}
    markerEnd: str = "url(#arrowhead)"
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    data: Optional[Dict[str, Any]] = {"styleType": "solid"}

    class Config:
        extra = "allow"  # Allow extra fields in the model

class GraphResponse(BaseModel):
    """Response model for graph operations"""
    message: str
    nodes: Optional[list] = None
    edges: Optional[list] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str 