from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
from fastapi.responses import JSONResponse

app = FastAPI()
# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://192.168.113.18:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Data models
class Position(BaseModel):
    x: float
    y: float

class NodeData(BaseModel):
    label: str

class Node(BaseModel):
    id: str
    type: str  # This will always be a string like 'red', 'pink', etc.
    data: NodeData
    position: Position

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['red', 'pink', 'purple', 'blue', 'teal', 'green', 'yellow', 'orange', 'brown', 'grey']
        if v not in valid_types:
            raise ValueError(f'Invalid node type: {v}. Must be one of {valid_types}')
        return v

class Edge(BaseModel):
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

# Data storage configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
NODES_FILE = os.path.join(DATA_DIR, 'nodes.json')
EDGES_FILE = os.path.join(DATA_DIR, 'edges.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Buffer for storing changes
buffer_nodes = []
buffer_edges = []

def load_data():
    """Load nodes and edges from JSON files"""
    global buffer_nodes, buffer_edges
    nodes = []
    edges = []
    
    # Load nodes
    if os.path.exists(NODES_FILE):
        try:
            with open(NODES_FILE, 'r') as f:
                nodes = json.load(f)
        except json.JSONDecodeError:
            print("Error reading nodes file, starting with empty nodes")
    
    # Load edges
    if os.path.exists(EDGES_FILE):
        try:
            with open(EDGES_FILE, 'r') as f:
                edges = json.load(f)
        except json.JSONDecodeError:
            print("Error reading edges file, starting with empty edges")
    
    # Initialize buffer with loaded data
    buffer_nodes = nodes.copy()
    buffer_edges = edges.copy()
    
    return nodes, edges

def validate_node_type(node_type: str) -> str:
    """Validate and normalize node type"""
    valid_types = ['red', 'pink', 'purple', 'blue', 'teal', 'green', 'yellow', 'orange', 'brown', 'grey']
    if node_type in valid_types:
        return node_type
    # Try to convert numeric type
    try:
        type_value = int(node_type)
        if 0 <= type_value <= 9:
            return valid_types[type_value]
    except (ValueError, TypeError):
        pass
    return 'red'  # Default to red if invalid

def save_data(nodes: List[Node], edges: List[Edge]):
    """Save nodes and edges to JSON files"""
    # Validate and normalize node types before saving
    validated_nodes = []
    for node in nodes:
        node_dict = node if isinstance(node, dict) else node.model_dump()
        validated_node = {
            **node_dict,
            'type': validate_node_type(node_dict['type']),
            'data': {
                **node_dict.get('data', {}),
                'type': validate_node_type(node_dict.get('type', 'red'))
            }
        }
        validated_nodes.append(validated_node)
    
    # Save nodes
    with open(NODES_FILE, 'w') as f:
        json.dump(validated_nodes, f, indent=2)
    
    # Save edges
    with open(EDGES_FILE, 'w') as f:
        json.dump(edges, f, indent=2)

# Initialize data
nodes, edges = load_data()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Flow Graph API"}

@app.get("/nodes")
async def get_nodes():
    return buffer_nodes

@app.get("/edges")
async def get_edges():
    return buffer_edges

@app.post("/nodes")
async def create_node(node: Node):
    # Ensure type is a string
    node_dict = node.model_dump()
    node_dict['type'] = str(node_dict['type'])
    buffer_nodes.append(node_dict)
    return node_dict

@app.post("/edges")
async def create_edge(edge: Edge):
    try:
        # Check if edge already exists
        if any(e["source"] == edge.source and e["target"] == edge.target for e in buffer_edges):
            return JSONResponse(
                status_code=400,
                content={"detail": "Edge already exists"}
            )
        
        # Validate that source and target nodes exist
        if not any(n["id"] == edge.source for n in buffer_nodes):
            return JSONResponse(
                status_code=400,
                content={"detail": f"Source node {edge.source} does not exist"}
            )
        if not any(n["id"] == edge.target for n in buffer_nodes):
            return JSONResponse(
                status_code=400,
                content={"detail": f"Target node {edge.target} does not exist"}
            )
        
        edge_dict = edge.model_dump()
        buffer_edges.append(edge_dict)
        return edge_dict
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)}
        )

@app.delete("/nodes/{node_id}")
async def delete_node(node_id: str):
    global buffer_nodes, buffer_edges
    # Remove node from buffer
    buffer_nodes = [n for n in buffer_nodes if n["id"] != node_id]
    # Remove connected edges from buffer
    buffer_edges = [e for e in buffer_edges if e["source"] != node_id and e["target"] != node_id]
    return {"message": f"Node {node_id} and its edges deleted"}

@app.delete("/edges/{edge_id}")
async def delete_edge(edge_id: str):
    global buffer_edges
    buffer_edges = [e for e in buffer_edges if e["id"] != edge_id]
    return {"message": f"Edge {edge_id} deleted"}

@app.put("/nodes/{node_id}")
async def update_node(node_id: str, node: Node):
    for i, n in enumerate(buffer_nodes):
        if n["id"] == node_id:
            buffer_nodes[i] = node.model_dump()
            return node
    raise HTTPException(status_code=404, detail="Node not found")

@app.post("/save")
async def save_graph():
    """Explicitly save the current state of the graph"""
    try:
        save_data(buffer_nodes, buffer_edges)
        return {"message": "Graph saved successfully", "nodes": buffer_nodes, "edges": buffer_edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save graph: {str(e)}")

@app.post("/load")
async def load_graph():
    """Explicitly load the graph from files"""
    global buffer_nodes, buffer_edges
    try:
        nodes, edges = load_data()
        # Validate types after loading
        buffer_nodes = [{
            **node,
            'type': validate_node_type(node['type']),
            'data': {
                **node.get('data', {}),
                'type': validate_node_type(node.get('type', 'red'))
            }
        } for node in nodes]
        buffer_edges = edges
        return {"message": "Graph loaded successfully", "nodes": buffer_nodes, "edges": buffer_edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load graph: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 