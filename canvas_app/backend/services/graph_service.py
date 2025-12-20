"""Graph construction service."""
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

from schemas.graph_schemas import GraphNode, GraphEdge, GraphData


def get_concept_category(concept_name: str) -> str:
    """Categorize concept by name pattern.
    
    Categories:
    - semantic-function: ::() and :<> patterns (imperative and judgement)
    - semantic-value: {}, <>, [] patterns (objects, attributes, collections)
    - syntactic-function: $, &, @, * patterns (assigning, grouping, timing, looping)
    """
    if ':(' in concept_name or ':<' in concept_name or concept_name.startswith('::'):
        return "semantic-function"
    elif ((concept_name.startswith('{') and concept_name.rstrip('?').endswith('}')) or 
          (concept_name.startswith('<') and concept_name.endswith('>')) or 
          (concept_name.startswith('[') and concept_name.endswith(']'))):
        return "semantic-value"
    elif (concept_name.startswith('$') or concept_name.startswith('&') or 
          concept_name.startswith('@') or concept_name.startswith('*')):
        return "syntactic-function"
    else:
        # Default to semantic-value for unknown patterns
        return "semantic-value"


def _parse_flow_index(flow_index: Optional[str]) -> Tuple[int, ...]:
    """Parse flow_index string into tuple of integers for sorting."""
    if not flow_index:
        return (999999,)  # Put nodes without flow_index at the end
    # Remove .func suffix if present
    clean = flow_index.replace('.func', '')
    try:
        return tuple(int(x) for x in clean.split('.'))
    except ValueError:
        return (999999,)


def _get_parent_flow_index(flow_index: Optional[str]) -> Optional[str]:
    """Get the parent's flow_index from a child's flow_index.
    
    Example: '1.2.1' -> '1.2', '1.2' -> '1', '1' -> None
    """
    if not flow_index:
        return None
    # Remove .func suffix if present
    clean = flow_index.replace('.func', '')
    parts = clean.split('.')
    if len(parts) <= 1:
        return None
    return '.'.join(parts[:-1])


def _calculate_positions(nodes: List[GraphNode], h_spacing: int = 300, v_spacing: int = 100, layout_mode: str = "hierarchical"):
    """Calculate x, y positions for nodes.
    
    Args:
        nodes: List of graph nodes to position
        h_spacing: Horizontal spacing between levels
        v_spacing: Vertical spacing between nodes
        layout_mode: Layout mode - "hierarchical" or "flow_aligned"
    """
    if not nodes:
        return
    
    if layout_mode == "flow_aligned":
        _calculate_positions_flow_aligned(nodes, h_spacing, v_spacing)
    else:
        _calculate_positions_hierarchical(nodes, h_spacing, v_spacing)


def _calculate_positions_hierarchical(nodes: List[GraphNode], h_spacing: int = 300, v_spacing: int = 100):
    """Calculate x, y positions using hierarchical layout with left-to-right data flow.
    
    Layout flows LEFT to RIGHT (children/inputs on left, parents/outputs on right):
    - x = (max_level - level) * horizontal_spacing (leaves on left, root on right)
    - y = sorted by full flow_index to preserve parent-child hierarchy
    
    Sorting by full flow_index ensures:
    - 1.1.x nodes come before 1.2.x nodes (parent 1.1 < parent 1.2)
    - 1.2.1 comes before 1.3.1 (lexicographic order)
    - Children of the same parent are grouped together
    """
    if not nodes:
        return
    
    # Find max level for x-coordinate calculation
    max_level = max(node.level for node in nodes)
    
    # Group nodes by level
    level_groups: Dict[int, List[GraphNode]] = {}
    for node in nodes:
        if node.level not in level_groups:
            level_groups[node.level] = []
        level_groups[node.level].append(node)
    
    # Sort nodes within each level by FULL flow_index (lexicographic tuple order)
    # This ensures: 1.1.3 < 1.2.1 because (1,1,3) < (1,2,1)
    for level in level_groups:
        level_groups[level].sort(key=lambda n: _parse_flow_index(n.flow_index))
    
    # Assign y positions sequentially within each level based on sorted order
    # This preserves the hierarchical structure: children of earlier parents come first
    for level, level_nodes in level_groups.items():
        # Calculate x position: leaves/children on left (x=0), root/parent on right (x=max)
        x = (max_level - level) * h_spacing
        
        for idx, node in enumerate(level_nodes):
            y = idx * v_spacing
            node.position = {"x": x, "y": y}


def _calculate_positions_flow_aligned(nodes: List[GraphNode], h_spacing: int = 300, v_spacing: int = 120):
    """Calculate x, y positions with flow-aligned layout.
    
    Each unique flow_index gets its own horizontal line (y-position).
    This allows tracing a concept's flow across the graph.
    
    Layout:
    - x = (max_level - level) * horizontal_spacing (preserves depth)
    - y = determined by flow_index (each flow_index on its own line)
    
    Flow indices are sorted to create logical ordering:
    - 1 < 1.1 < 1.2 < 1.2.1 < 1.2.2 < 1.3 < 2
    """
    if not nodes:
        return
    
    # Find max level for x-coordinate calculation
    max_level = max(node.level for node in nodes)
    
    # Collect all unique flow_indices and sort them
    all_flow_indices = sorted(
        set(node.flow_index for node in nodes if node.flow_index),
        key=lambda fi: _parse_flow_index(fi)
    )
    
    # Create mapping from flow_index to y-position (row number)
    flow_index_to_row: Dict[str, int] = {
        fi: idx for idx, fi in enumerate(all_flow_indices)
    }
    
    # Assign positions based on level (x) and flow_index (y)
    for node in nodes:
        # x position based on level (depth preserved)
        x = (max_level - node.level) * h_spacing
        
        # y position based on flow_index row
        row = flow_index_to_row.get(node.flow_index, len(all_flow_indices))
        y = row * v_spacing
        
        node.position = {"x": x, "y": y}


def build_graph_from_repositories(
    concepts_data: List[Dict[str, Any]],
    inferences_data: List[Dict[str, Any]],
    layout_mode: str = "hierarchical"
) -> GraphData:
    """Build graph model from concept and inference repositories.
    
    PRIORITY: Uses flow_indices from concept_repo when available, falling back to
    inference-based generation only when concept_repo doesn't provide flow_indices.
    
    Each concept in an inference gets a proper flow_index following NormCode pattern:
    - concept_to_infer: base flow_index (e.g., "1")
    - function_concept: flow_index + ".1" (e.g., "1.1")
    - value_concepts[0]: flow_index + ".2" (e.g., "1.2")
    - value_concepts[1]: flow_index + ".3" (e.g., "1.3")
    - context_concepts continue the numbering
    
    When a concept appears at multiple flow indices, duplicate nodes are created
    and connected with "alias" edges (dashed lines).
    
    Args:
        concepts_data: List of concept definitions from .concept.json
        inferences_data: List of inference definitions from .inference.json
        layout_mode: Layout mode - "hierarchical" or "flow_aligned"
        
    Returns:
        GraphData with nodes and edges for visualization
    """
    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []
    
    # Build concept lookup for attributes
    concept_attrs = {c.get('concept_name', ''): c for c in concepts_data}
    
    # Build lookup for concept flow_indices from concept_repo (authoritative source)
    # Maps concept_name -> list of flow_indices from concept_repo
    concept_repo_flow_indices: Dict[str, List[str]] = {}
    for c in concepts_data:
        name = c.get('concept_name', '')
        flow_indices = c.get('flow_indices', [])
        if name and flow_indices:
            concept_repo_flow_indices[name] = flow_indices
    
    # Track which flow_indices have been used for each concept (for multi-occurrence concepts)
    concept_flow_usage: Dict[str, int] = {}  # concept_name -> next index to use
    
    def get_flow_index_for_concept(concept_name: str, fallback_flow_index: str, parent_flow_index: str) -> str:
        """Get the best flow_index for a concept, prioritizing concept_repo.
        
        Strategy:
        1. If concept has flow_indices in concept_repo, find one that matches the parent pattern
        2. If exact match found (starts with parent.), use it
        3. Otherwise fall back to generated flow_index
        
        Args:
            concept_name: The concept's name
            fallback_flow_index: Generated flow_index based on inference structure
            parent_flow_index: The parent inference's base flow_index
            
        Returns:
            The best flow_index to use
        """
        repo_indices = concept_repo_flow_indices.get(concept_name, [])
        
        if not repo_indices:
            # No flow_indices in concept_repo, use fallback
            return fallback_flow_index
        
        # Find a flow_index that matches the parent pattern
        # For child concepts (function/value/context), look for indices starting with parent_flow_index + "."
        # NOTE: We do NOT match fi == parent_flow_index because the child's flow_index
        # should always be a sub-index of the parent (e.g., "1.2" under parent "1")
        # Matching the parent exactly would conflate the child with the parent node!
        parent_prefix = f"{parent_flow_index}." if parent_flow_index else ""
        
        matching_indices = [
            fi for fi in repo_indices 
            if parent_prefix and fi.startswith(parent_prefix)
        ]
        
        if matching_indices:
            # Sort to get consistent ordering
            matching_indices.sort(key=lambda fi: _parse_flow_index(fi))
            
            # Track usage to handle multiple occurrences under same parent
            usage_key = f"{concept_name}@{parent_flow_index}"
            usage_idx = concept_flow_usage.get(usage_key, 0)
            
            if usage_idx < len(matching_indices):
                selected = matching_indices[usage_idx]
                concept_flow_usage[usage_key] = usage_idx + 1
                return selected
        
        # Check if fallback matches any repo index (confirms our generation)
        if fallback_flow_index in repo_indices:
            return fallback_flow_index
        
        # No matching pattern, use fallback
        return fallback_flow_index
    
    # Track which concepts appear at which flow indices (for alias edges)
    concept_to_flow_indices: Dict[str, List[str]] = {}
    
    def register_concept_flow_index(concept_name: str, flow_idx: str):
        """Track flow_index for a concept to create alias edges later."""
        if concept_name not in concept_to_flow_indices:
            concept_to_flow_indices[concept_name] = []
        if flow_idx not in concept_to_flow_indices[concept_name]:
            concept_to_flow_indices[concept_name].append(flow_idx)
    
    for inf in inferences_data:
        flow_info = inf.get('flow_info', {})
        base_flow_index = flow_info.get('flow_index', '0')
        base_level = len(base_flow_index.split('.')) - 1
        
        target_name = inf.get('concept_to_infer', '')
        func_name = inf.get('function_concept', '')
        value_names = inf.get('value_concepts', [])
        context_names = inf.get('context_concepts', [])
        sequence = inf.get('inference_sequence', '')
        working_interp = inf.get('working_interpretation', {})
        
        # Child index counter for this inference (starts at 1)
        child_idx = 1
        
        # Create target node (the concept being inferred)
        # IMPORTANT: The target (concept_to_infer) MUST use the inference's base_flow_index
        # This is the defining node for this inference - we don't look it up from concept_repo
        # because the inference's flow_index IS the authoritative source for where it's inferred.
        target_flow_index = base_flow_index
        target_id = f"node@{target_flow_index}"
        
        if target_name:
            if target_id not in nodes:
                attrs = concept_attrs.get(target_name, {})
                nodes[target_id] = GraphNode(
                    id=target_id,
                    label=target_name,
                    category=get_concept_category(target_name),
                    node_type="value",
                    flow_index=target_flow_index,
                    level=base_level,
                    position={"x": 0, "y": 0},
                    data={
                        "is_ground": attrs.get('is_ground_concept', False),
                        "is_final": attrs.get('is_final_concept', False),
                        "axes": attrs.get('reference_axis_names', []),
                        "reference_data": attrs.get('reference_data'),
                        "concept_name": target_name,
                        "flow_indices_from_repo": attrs.get('flow_indices', []),
                    }
                )
                register_concept_flow_index(target_name, target_flow_index)
            elif nodes[target_id].label != target_name:
                # COLLISION: Node ID exists but has different concept name!
                # This indicates a bug in flow_index assignment or inference data.
                # Log a warning and skip this inference to avoid corrupting the graph.
                import logging
                logging.warning(
                    f"Node ID collision: {target_id} already exists with label "
                    f"'{nodes[target_id].label}', but trying to create with '{target_name}'. "
                    f"Skipping inference at flow_index {base_flow_index}."
                )
                continue
        
        input_level = base_level + 1
        
        # Create function node - prioritize concept_repo flow_indices
        if func_name:
            fallback_func_flow_index = f"{base_flow_index}.{child_idx}"
            func_flow_index = get_flow_index_for_concept(func_name, fallback_func_flow_index, base_flow_index)
            child_idx += 1
            func_id = f"node@{func_flow_index}"
            
            if func_id not in nodes:
                func_attrs = concept_attrs.get(func_name, {})
                nodes[func_id] = GraphNode(
                    id=func_id,
                    label=func_name,
                    category=get_concept_category(func_name),
                    node_type="function",
                    flow_index=func_flow_index,
                    level=input_level,
                    position={"x": 0, "y": 0},
                    data={
                        "sequence": sequence,
                        "working_interpretation": working_interp,
                        "concept_name": func_name,
                        "flow_indices_from_repo": func_attrs.get('flow_indices', []),
                    }
                )
                register_concept_flow_index(func_name, func_flow_index)
            elif nodes[func_id].label != func_name:
                # COLLISION: Different concept at same flow_index!
                # Generate a unique ID by appending ".func" suffix
                import logging
                logging.warning(
                    f"Function node collision: {func_id} exists with '{nodes[func_id].label}', "
                    f"wanted '{func_name}'. Using fallback ID."
                )
                func_id = f"node@{fallback_func_flow_index}"
                if func_id not in nodes:
                    func_attrs = concept_attrs.get(func_name, {})
                    nodes[func_id] = GraphNode(
                        id=func_id,
                        label=func_name,
                        category=get_concept_category(func_name),
                        node_type="function",
                        flow_index=fallback_func_flow_index,
                        level=input_level,
                        position={"x": 0, "y": 0},
                        data={
                            "sequence": sequence,
                            "working_interpretation": working_interp,
                            "concept_name": func_name,
                        }
                    )
                    register_concept_flow_index(func_name, fallback_func_flow_index)
            
            # Edge from function to target (produces)
            edges.append(GraphEdge(
                id=f"edge-func-{base_flow_index}",
                source=func_id,
                target=target_id,
                edge_type="function",
                label=sequence,
                flow_index=base_flow_index
            ))
        
        # Create value input nodes - prioritize concept_repo flow_indices
        for idx, val_name in enumerate(value_names):
            if not val_name:
                child_idx += 1
                continue
            
            fallback_val_flow_index = f"{base_flow_index}.{child_idx}"
            val_flow_index = get_flow_index_for_concept(val_name, fallback_val_flow_index, base_flow_index)
            child_idx += 1
            val_id = f"node@{val_flow_index}"
            
            # Check for collision: if node exists with different concept, use fallback
            if val_id in nodes and nodes[val_id].label != val_name:
                import logging
                logging.warning(
                    f"Value node collision: {val_id} exists with '{nodes[val_id].label}', "
                    f"wanted '{val_name}'. Using fallback ID."
                )
                val_flow_index = fallback_val_flow_index
                val_id = f"node@{val_flow_index}"
            
            if val_id not in nodes:
                val_attrs = concept_attrs.get(val_name, {})
                nodes[val_id] = GraphNode(
                    id=val_id,
                    label=val_name,
                    category=get_concept_category(val_name),
                    node_type="value",
                    flow_index=val_flow_index,
                    level=input_level,
                    position={"x": 0, "y": 0},
                    data={
                        "is_ground": val_attrs.get('is_ground_concept', False),
                        "is_final": val_attrs.get('is_final_concept', False),
                        "axes": val_attrs.get('reference_axis_names', []),
                        "concept_name": val_name,
                        "flow_indices_from_repo": val_attrs.get('flow_indices', []),
                    }
                )
                register_concept_flow_index(val_name, val_flow_index)
            
            # Edge from value to target (data flow)
            edges.append(GraphEdge(
                id=f"edge-val-{val_flow_index}",
                source=val_id,
                target=target_id,
                edge_type="value",
                label=f":{idx+1}",
                flow_index=val_flow_index
            ))
        
        # Create context nodes - prioritize concept_repo flow_indices
        for idx, ctx_name in enumerate(context_names):
            if not ctx_name:
                child_idx += 1
                continue
            
            fallback_ctx_flow_index = f"{base_flow_index}.{child_idx}"
            ctx_flow_index = get_flow_index_for_concept(ctx_name, fallback_ctx_flow_index, base_flow_index)
            child_idx += 1
            ctx_id = f"node@{ctx_flow_index}"
            
            # Check for collision: if node exists with different concept, use fallback
            if ctx_id in nodes and nodes[ctx_id].label != ctx_name:
                import logging
                logging.warning(
                    f"Context node collision: {ctx_id} exists with '{nodes[ctx_id].label}', "
                    f"wanted '{ctx_name}'. Using fallback ID."
                )
                ctx_flow_index = fallback_ctx_flow_index
                ctx_id = f"node@{ctx_flow_index}"
            
            if ctx_id not in nodes:
                ctx_attrs = concept_attrs.get(ctx_name, {})
                nodes[ctx_id] = GraphNode(
                    id=ctx_id,
                    label=ctx_name,
                    category=get_concept_category(ctx_name),
                    node_type="value",
                    flow_index=ctx_flow_index,
                    level=input_level,
                    position={"x": 0, "y": 0},
                    data={
                        "is_context": True,
                        "axes": ctx_attrs.get('reference_axis_names', []),
                        "concept_name": ctx_name,
                        "flow_indices_from_repo": ctx_attrs.get('flow_indices', []),
                    }
                )
                register_concept_flow_index(ctx_name, ctx_flow_index)
            
            # Edge from context to target (context flow)
            edges.append(GraphEdge(
                id=f"edge-ctx-{ctx_flow_index}",
                source=ctx_id,
                target=target_id,
                edge_type="context",
                label="ctx",
                flow_index=ctx_flow_index
            ))
    
    # Create alias edges for concepts that appear at multiple flow indices
    # These connect duplicate nodes of the same concept with dashed lines
    for concept_name, flow_indices in concept_to_flow_indices.items():
        if len(flow_indices) > 1:
            # Sort by flow_index to create consistent alias chains
            sorted_indices = sorted(flow_indices, key=lambda fi: _parse_flow_index(fi))
            # Connect each pair of adjacent duplicates
            for i in range(len(sorted_indices) - 1):
                source_id = f"node@{sorted_indices[i]}"
                target_id = f"node@{sorted_indices[i + 1]}"
                if source_id in nodes and target_id in nodes:
                    edges.append(GraphEdge(
                        id=f"edge-alias-{concept_name}-{i}",
                        source=source_id,
                        target=target_id,
                        edge_type="alias",
                        label="≡",  # Equivalence symbol
                        flow_index=sorted_indices[i]
                    ))
    
    # Calculate positions using specified layout mode
    node_list = list(nodes.values())
    _calculate_positions(node_list, layout_mode=layout_mode)
    
    return GraphData(nodes=node_list, edges=edges)


class GraphService:
    """Service for managing graph state."""
    
    def __init__(self):
        self.current_graph: Optional[GraphData] = None
        self.concepts_data: List[Dict[str, Any]] = []
        self.inferences_data: List[Dict[str, Any]] = []
        self.current_layout_mode: str = "hierarchical"
    
    def load_from_files(self, concepts_path: str, inferences_path: str, layout_mode: str = "hierarchical") -> GraphData:
        """Load repositories from files and build graph."""
        with open(concepts_path, 'r', encoding='utf-8') as f:
            self.concepts_data = json.load(f)
        with open(inferences_path, 'r', encoding='utf-8') as f:
            self.inferences_data = json.load(f)
        
        self.current_layout_mode = layout_mode
        self.current_graph = build_graph_from_repositories(
            self.concepts_data,
            self.inferences_data,
            layout_mode=layout_mode
        )
        return self.current_graph
    
    def load_from_data(
        self, 
        concepts_data: List[Dict[str, Any]], 
        inferences_data: List[Dict[str, Any]],
        layout_mode: str = "hierarchical"
    ) -> GraphData:
        """Build graph from in-memory data."""
        self.concepts_data = concepts_data
        self.inferences_data = inferences_data
        self.current_layout_mode = layout_mode
        self.current_graph = build_graph_from_repositories(
            concepts_data, 
            inferences_data,
            layout_mode=layout_mode
        )
        return self.current_graph
    
    def set_layout_mode(self, layout_mode: str) -> Optional[GraphData]:
        """Change the layout mode and recalculate positions.
        
        Args:
            layout_mode: "hierarchical" or "flow_aligned"
            
        Returns:
            Updated GraphData with new positions, or None if no data loaded
        """
        if not self.concepts_data or not self.inferences_data:
            return None
        
        self.current_layout_mode = layout_mode
        self.current_graph = build_graph_from_repositories(
            self.concepts_data,
            self.inferences_data,
            layout_mode=layout_mode
        )
        return self.current_graph
    
    def get_layout_mode(self) -> str:
        """Get the current layout mode."""
        return self.current_layout_mode
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a specific node by ID."""
        if not self.current_graph:
            return None
        for node in self.current_graph.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_node_data(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed data for a node including reference data."""
        node = self.get_node(node_id)
        if not node:
            return None
        
        # Find the concept in concepts_data
        concept_name = node.label
        for concept in self.concepts_data:
            if concept.get('concept_name') == concept_name:
                return {
                    "node": node.model_dump(),
                    "concept": concept,
                }
        
        return {"node": node.model_dump(), "concept": None}


# Global service instance
graph_service = GraphService()
