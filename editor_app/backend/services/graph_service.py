"""
Service for computing graph data from flow structures.
"""
from typing import List, Dict, Any, Set
import json


class GraphNode:
    """Represents a node in the flow graph."""
    def __init__(self, id: str, label: str, type: str, level: int, flow_index_tuple: tuple):
        self.id = id
        self.label = label
        self.type = type
        self.level = level
        self.flow_index_tuple = flow_index_tuple
        self.x = 0
        self.y = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "level": self.level,
            "x": self.x,
            "y": self.y
        }


class GraphEdge:
    """Represents an edge in the flow graph."""
    def __init__(self, id: str, source: str, target: str, label: str, 
                 edge_type: str, inference_sequence: str, flow_index: str):
        self.id = id
        self.source = source
        self.target = target
        self.label = label
        self.edge_type = edge_type
        self.inference_sequence = inference_sequence
        self.flow_index = flow_index
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "type": self.edge_type,
            "inferenceSequence": self.inference_sequence,
            "flowIndex": self.flow_index
        }


class GraphService:
    """Service for computing graph structures from flow data."""

    @staticmethod
    def compute_graph_from_flow(flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute graph structure from flow data, allowing concepts to appear at multiple
        levels to ensure arrows always point from right to left between adjacent levels.

        Args:
            flow_data: The flow data containing inference nodes.

        Returns:
            Dictionary with nodes and edges for graph visualization.
        """
        if not flow_data or "nodes" not in flow_data:
            return {"nodes": [], "edges": []}

        inference_nodes = flow_data.get("nodes", [])
        if not inference_nodes:
            return {"nodes": [], "edges": []}

        sorted_nodes = sorted(
            inference_nodes,
            key=lambda n: GraphService._parse_flow_index(
                n.get("data", {}).get("flow_info", {}).get("flow_index", "0")
            )
        )

        nodes: Dict[str, GraphNode] = {}
        edges: List[GraphEdge] = []

        for idx, node in enumerate(sorted_nodes):
            node_data = node.get("data", {})
            if not node_data:
                continue

            flow_info = node_data.get("flow_info", {})
            flow_index_str = flow_info.get("flow_index", "0")
            flow_index_tuple = GraphService._parse_flow_index(flow_index_str)
            inference_sequence = node_data.get("inference_sequence", "")
            concept_to_infer = node_data.get("concept_to_infer")

            if not concept_to_infer:
                continue

            # Assign level based on flow_index depth
            level = len(flow_index_tuple) - 1

            # Create target node for the inferred concept
            target_id = f"{concept_to_infer}@{level}"
            if target_id not in nodes:
                nodes[target_id] = GraphNode(
                    id=target_id, label=concept_to_infer, type="concept",
                    level=level, flow_index_tuple=flow_index_tuple
                )

            input_level = level + 1

            # Process function concept
            function_concept = node_data.get("function_concept")
            if function_concept:
                source_id = f"{function_concept}@{input_level}"
                if source_id not in nodes:
                    nodes[source_id] = GraphNode(
                        id=source_id, label=function_concept, type="concept",
                        level=input_level, flow_index_tuple=flow_index_tuple
                    )
                edges.append(GraphEdge(
                    id=f"edge-func-{node.get('id', idx)}", source=source_id, target=target_id,
                    label=inference_sequence, edge_type="function", inference_sequence=inference_sequence,
                    flow_index=flow_index_str
                ))

            # Process value concepts
            value_concepts = node_data.get("value_concepts", [])
            if isinstance(value_concepts, list):
                for v_idx, value_concept in enumerate(value_concepts):
                    source_id = f"{value_concept}@{input_level}"
                    if source_id not in nodes:
                        nodes[source_id] = GraphNode(
                            id=source_id, label=value_concept, type="concept",
                            level=input_level, flow_index_tuple=flow_index_tuple
                        )
                    edges.append(GraphEdge(
                        id=f"edge-value-{node.get('id', idx)}-{v_idx}", source=source_id, target=target_id,
                        label=inference_sequence, edge_type="value", inference_sequence=inference_sequence,
                        flow_index=flow_index_str
                    ))

        positioned_nodes = GraphService._calculate_positions(list(nodes.values()))

        return {
            "nodes": [node.to_dict() for node in positioned_nodes],
            "edges": [edge.to_dict() for edge in edges]
        }

    @staticmethod
    def _parse_flow_index(index_str: str) -> tuple:
        """Parse flow index string into tuple for sorting."""
        try:
            return tuple(int(x) for x in index_str.split('.'))
        except (ValueError, AttributeError):
            return (0,)

    @staticmethod
    def _calculate_positions(nodes: List[GraphNode]) -> List[GraphNode]:
        """Calculate x, y positions for nodes."""
        level_groups: Dict[int, List[GraphNode]] = {}
        for node in nodes:
            if node.level not in level_groups:
                level_groups[node.level] = []
            level_groups[node.level].append(node)

        for level in level_groups:
            level_groups[level].sort(
                key=lambda n: n.flow_index_tuple
            )

        horizontal_spacing = 250
        vertical_spacing = 100
        start_x = 150
        start_y = 100

        positioned_nodes = []
        sorted_levels = sorted(level_groups.keys())

        max_level_height = 0
        if level_groups:
            max_nodes_in_level = max(len(nodes) for nodes in level_groups.values())
            max_level_height = max_nodes_in_level * vertical_spacing

        for level in sorted_levels:
            level_nodes = level_groups[level]
            total_height = len(level_nodes) * vertical_spacing

            start_y_for_level = start_y + (max_level_height - total_height) / 2

            for idx, node in enumerate(level_nodes):
                node.x = start_x + (level * horizontal_spacing)
                node.y = start_y_for_level + (idx * vertical_spacing)
                positioned_nodes.append(node)

        return positioned_nodes

