"""Graph data schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class GraphNode(BaseModel):
    """A node in the graph."""
    id: str                     # f"{concept_name}@{level}"
    label: str                  # Concept name
    category: str               # "semantic-function" | "semantic-value" | "syntactic-function"
    node_type: str              # "value" | "function"
    flow_index: Optional[str] = None
    level: int
    position: Dict[str, float]  # {x, y}
    data: Dict[str, Any] = {}   # Additional data for expansion


class GraphEdge(BaseModel):
    """An edge in the graph."""
    id: str
    source: str
    target: str
    edge_type: str              # "function" | "value"
    label: Optional[str] = None # Inference sequence
    flow_index: str


class GraphData(BaseModel):
    """Complete graph data."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
