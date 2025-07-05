import json
import os
from typing import List, Dict, Any, Tuple
from models.graph_models import Node, Edge
from schemas.config import settings

class GraphService:
    """Service class for handling graph operations and data persistence"""
    
    def __init__(self):
        # Data storage configuration
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', settings.data_dir)
        self.nodes_file = os.path.join(self.data_dir, settings.nodes_file)
        self.edges_file = os.path.join(self.data_dir, settings.edges_file)
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Buffer for storing changes
        self.buffer_nodes: List[Dict[str, Any]] = []
        self.buffer_edges: List[Dict[str, Any]] = []
        
        # Initialize data
        self.load_data()
    
    def validate_node_type(self, node_type: str) -> str:
        """Validate and normalize node type"""
        valid_types = settings.valid_node_types
        if node_type in valid_types:
            return node_type
        # Try to convert numeric type
        try:
            type_value = int(node_type)
            if 0 <= type_value <= len(valid_types) - 1:
                return valid_types[type_value]
        except (ValueError, TypeError):
            pass
        return 'red'  # Default to red if invalid
    
    def load_data(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Load nodes and edges from JSON files"""
        nodes = []
        edges = []
        
        # Load nodes
        if os.path.exists(self.nodes_file):
            try:
                with open(self.nodes_file, 'r') as f:
                    nodes = json.load(f)
            except json.JSONDecodeError:
                print("Error reading nodes file, starting with empty nodes")
        
        # Load edges
        if os.path.exists(self.edges_file):
            try:
                with open(self.edges_file, 'r') as f:
                    edges = json.load(f)
            except json.JSONDecodeError:
                print("Error reading edges file, starting with empty edges")
        
        # Initialize buffer with loaded data
        self.buffer_nodes = nodes.copy()
        self.buffer_edges = edges.copy()
        
        return nodes, edges
    
    def save_data(self, nodes: List[Node], edges: List[Edge]) -> None:
        """Save nodes and edges to JSON files"""
        # Validate and normalize node types before saving
        validated_nodes = []
        for node in nodes:
            node_dict = node if isinstance(node, dict) else node.model_dump()
            validated_node = {
                **node_dict,
                'type': self.validate_node_type(node_dict['type']),
                'data': {
                    **node_dict.get('data', {}),
                    'type': self.validate_node_type(node_dict.get('type', 'red'))
                }
            }
            validated_nodes.append(validated_node)
        
        # Save nodes
        with open(self.nodes_file, 'w') as f:
            json.dump(validated_nodes, f, indent=2)
        
        # Save edges
        with open(self.edges_file, 'w') as f:
            json.dump(edges, f, indent=2)
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes from buffer"""
        return self.buffer_nodes
    
    def get_all_edges(self) -> List[Dict[str, Any]]:
        """Get all edges from buffer"""
        return self.buffer_edges
    
    def create_node(self, node: Node) -> Dict[str, Any]:
        """Create a new node"""
        node_dict = node.model_dump()
        node_dict['type'] = str(node_dict['type'])
        self.buffer_nodes.append(node_dict)
        return node_dict
    
    def create_edge(self, edge: Edge) -> Dict[str, Any]:
        """Create a new edge with validation"""
        # Check if edge already exists
        if any(e["source"] == edge.source and e["target"] == edge.target for e in self.buffer_edges):
            raise ValueError("Edge already exists")
        
        # Validate that source and target nodes exist
        if not any(n["id"] == edge.source for n in self.buffer_nodes):
            raise ValueError(f"Source node {edge.source} does not exist")
        if not any(n["id"] == edge.target for n in self.buffer_nodes):
            raise ValueError(f"Target node {edge.target} does not exist")
        
        edge_dict = edge.model_dump()
        self.buffer_edges.append(edge_dict)
        return edge_dict
    
    def delete_node(self, node_id: str) -> str:
        """Delete a node and its connected edges"""
        # Remove node from buffer
        self.buffer_nodes = [n for n in self.buffer_nodes if n["id"] != node_id]
        # Remove connected edges from buffer
        self.buffer_edges = [e for e in self.buffer_edges if e["source"] != node_id and e["target"] != node_id]
        return f"Node {node_id} and its edges deleted"
    
    def delete_edge(self, edge_id: str) -> str:
        """Delete an edge"""
        self.buffer_edges = [e for e in self.buffer_edges if e["id"] != edge_id]
        return f"Edge {edge_id} deleted"
    
    def update_node(self, node_id: str, node: Node) -> Node:
        """Update an existing node"""
        for i, n in enumerate(self.buffer_nodes):
            if n["id"] == node_id:
                self.buffer_nodes[i] = node.model_dump()
                return node
        raise ValueError("Node not found")
    
    def save_graph(self) -> Dict[str, Any]:
        """Explicitly save the current state of the graph"""
        self.save_data(self.buffer_nodes, self.buffer_edges)
        return {
            "message": "Graph saved successfully",
            "nodes": self.buffer_nodes,
            "edges": self.buffer_edges
        }
    
    def load_graph(self) -> Dict[str, Any]:
        """Explicitly load the graph from files"""
        nodes, edges = self.load_data()
        # Validate types after loading
        self.buffer_nodes = [{
            **node,
            'type': self.validate_node_type(node['type']),
            'data': {
                **node.get('data', {}),
                'type': self.validate_node_type(node.get('type', 'red'))
            }
        } for node in nodes]
        self.buffer_edges = edges
        return {
            "message": "Graph loaded successfully",
            "nodes": self.buffer_nodes,
            "edges": self.buffer_edges
        } 