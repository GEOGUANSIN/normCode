"""Graph construction service."""
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json

from schemas.graph_schemas import GraphNode, GraphEdge, GraphData

logger = logging.getLogger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Type classification constants (from infra/_core/_concept.py)
TYPE_CLASS_SYNTACTICAL = "syntactical"
TYPE_CLASS_SEMANTICAL = "semantical"
TYPE_CLASS_INFERENTIAL = "inferential"

# Node type constants
NODE_TYPE_FUNCTION = "function"
NODE_TYPE_VALUE = "value"

# Edge type constants
EDGE_TYPE_FUNCTION = "function"
EDGE_TYPE_VALUE = "value"
EDGE_TYPE_CONTEXT = "context"
EDGE_TYPE_ALIAS = "alias"

# Category constants
CATEGORY_SEMANTIC_FUNCTION = "semantic-function"
CATEGORY_SEMANTIC_VALUE = "semantic-value"
CATEGORY_PROPOSITION = "proposition"
CATEGORY_SYNTACTIC_FUNCTION = "syntactic-function"

# Concept type to category mapping
# Based on CONCEPT_TYPES in infra/_core/_concept.py
CONCEPT_TYPE_INFO = {
    # Core inference operators (INFERENTIAL -> semantic-function behavior)
    "<=": {"type_class": TYPE_CLASS_INFERENTIAL, "is_function": True},
    "<-": {"type_class": TYPE_CLASS_INFERENTIAL, "is_function": False},
    
    # Assignment operators (SYNTACTICAL)
    "$=": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "$::": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "$.": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "$%": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "$+": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "$-": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    
    # Question markers (SYNTACTICAL)
    "$what?": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": False},
    "$how?": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": False},
    "$when?": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": False},
    
    # Timing operators (SYNTACTICAL)
    "@by": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@if": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@if!": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@onlyIf": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@ifOnlyIf": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@after": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@before": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@with": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@while": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@until": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@afterstep": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@:'": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@:!": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "@.": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    
    # Grouping operators (SYNTACTICAL)
    "&in": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "&across": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "&set": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "&pair": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "&[{}]": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "&[#]": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    
    # Quantification/Looping operators (SYNTACTICAL)
    "*every": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "*some": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "*count": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    "*.": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": True},
    
    # Object and concept types (SEMANTICAL)
    "{}": {"type_class": TYPE_CLASS_SEMANTICAL, "is_function": False, "category": CATEGORY_SEMANTIC_VALUE},
    "::": {"type_class": TYPE_CLASS_SEMANTICAL, "is_function": True, "category": CATEGORY_SEMANTIC_FUNCTION},
    "<>": {"type_class": TYPE_CLASS_SEMANTICAL, "is_function": False, "category": CATEGORY_PROPOSITION},
    "<{}>": {"type_class": TYPE_CLASS_SEMANTICAL, "is_function": True, "category": CATEGORY_SEMANTIC_FUNCTION},
    "({})": {"type_class": TYPE_CLASS_SEMANTICAL, "is_function": True, "category": CATEGORY_SEMANTIC_FUNCTION},
    "::({})": {"type_class": TYPE_CLASS_SEMANTICAL, "is_function": True, "category": CATEGORY_SEMANTIC_FUNCTION},
    "[]": {"type_class": TYPE_CLASS_SEMANTICAL, "is_function": False, "category": CATEGORY_SEMANTIC_VALUE},
    ":S:": {"type_class": TYPE_CLASS_SEMANTICAL, "is_function": False, "category": CATEGORY_SEMANTIC_VALUE},
    
    # Input/Output concepts (SYNTACTICAL)
    ":>:": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": False},
    ":<:": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": False},
    
    # Template and placeholder types (SYNTACTICAL)
    "{}?": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": False},
    "<:_>": {"type_class": TYPE_CLASS_SYNTACTICAL, "is_function": False},
}


# =============================================================================
# Category Classification
# =============================================================================

def get_concept_category(concept_name: str, concept_type: Optional[str] = None) -> str:
    """Categorize concept using its type from the concept repo.
    
    Args:
        concept_name: The concept name (used as fallback for pattern matching)
        concept_type: The concept type from concept repo (e.g., "::", "{}", "<{}>")
    
    Returns:
        Category string: "semantic-function", "semantic-value", "proposition", or "syntactic-function"
    
    Categories:
    - semantic-function: functional semantical (::, <{}>, ({})) - purple
    - semantic-value: non-functional semantical ({}, [], :S:) - blue
    - proposition: boolean state values (<>) - cyan/teal
    - syntactic-function: syntactical operators ($, &, @, *) - gray
    """
    # If we have a valid concept type, use it for accurate categorization
    if concept_type and concept_type in CONCEPT_TYPE_INFO:
        info = CONCEPT_TYPE_INFO[concept_type]
        
        # Check for explicit category override first
        if "category" in info:
            return info["category"]
        
        # Otherwise derive from type_class and is_function
        type_class = info["type_class"]
        is_function = info["is_function"]
        
        if type_class in (TYPE_CLASS_SEMANTICAL, TYPE_CLASS_INFERENTIAL):
            return CATEGORY_SEMANTIC_FUNCTION if is_function else CATEGORY_SEMANTIC_VALUE
        else:  # syntactical
            return CATEGORY_SYNTACTIC_FUNCTION if is_function else CATEGORY_SEMANTIC_VALUE
    
    # Fallback: Pattern matching on concept name (for backwards compatibility)
    return _get_category_from_name_pattern(concept_name)


def _get_category_from_name_pattern(concept_name: str) -> str:
    """Derive category from concept name patterns (fallback method)."""
    if (':(' in concept_name or 
        ':<' in concept_name or 
        concept_name.startswith('::') or
        concept_name.startswith(':%')):
        return CATEGORY_SEMANTIC_FUNCTION
    
    if concept_name.startswith('<') and concept_name.endswith('>') and not concept_name.startswith('<{'):
        return CATEGORY_PROPOSITION
    
    if ((concept_name.startswith('{') and concept_name.rstrip('?').endswith('}')) or
        (concept_name.startswith('[') and concept_name.endswith(']'))):
        return CATEGORY_SEMANTIC_VALUE
    
    if (concept_name.startswith('$') or concept_name.startswith('&') or
        concept_name.startswith('@') or concept_name.startswith('*')):
        return CATEGORY_SYNTACTIC_FUNCTION
    
    return CATEGORY_SEMANTIC_VALUE


# =============================================================================
# Flow Index Utilities
# =============================================================================

def _parse_flow_index(flow_index: Optional[str]) -> Tuple[int, ...]:
    """Parse flow_index string into tuple of integers for sorting."""
    if not flow_index:
        return (999999,)
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
    clean = flow_index.replace('.func', '')
    parts = clean.split('.')
    if len(parts) <= 1:
        return None
    return '.'.join(parts[:-1])


# =============================================================================
# Flow Index Resolution
# =============================================================================

class FlowIndexResolver:
    """Resolves flow indices for concepts, prioritizing concept_repo data."""
    
    def __init__(self, concepts_data: List[Dict[str, Any]]):
        # Maps concept_name -> list of flow_indices from concept_repo
        self.concept_repo_flow_indices: Dict[str, List[str]] = {}
        for c in concepts_data:
            name = c.get('concept_name', '')
            flow_indices = c.get('flow_indices', [])
            if name and flow_indices:
                self.concept_repo_flow_indices[name] = flow_indices
        
        # Track usage for multi-occurrence concepts
        self._usage: Dict[str, int] = {}
        
        # Track which flow_indices each concept appears at (for alias edges)
        self.concept_to_flow_indices: Dict[str, List[str]] = {}
    
    def get_flow_index(
        self, 
        concept_name: str, 
        fallback_flow_index: str, 
        parent_flow_index: str
    ) -> str:
        """Get the best flow_index for a concept, prioritizing concept_repo.
        
        Strategy:
        1. If the fallback flow_index exists in concept_repo, use it (exact match)
        2. Otherwise, prefer DIRECT children (one level deeper than parent)
        3. Only then fall back to deeper descendants
        4. Otherwise use the fallback
        
        This prevents greedy matching where a deeply nested index like "1.3.1.3.1.2"
        would be selected over a direct child like "1.3.1.4".
        """
        repo_indices = self.concept_repo_flow_indices.get(concept_name, [])
        
        if not repo_indices:
            return fallback_flow_index
        
        # Priority 1: Exact match with fallback
        if fallback_flow_index in repo_indices:
            return fallback_flow_index
        
        # Find indices matching the parent pattern
        parent_prefix = f"{parent_flow_index}." if parent_flow_index else ""
        if not parent_prefix:
            return fallback_flow_index
        
        # Separate direct children from deeper descendants
        # Direct child = one level deeper (e.g., "1.3.1.4" under parent "1.3.1")
        # Deeper descendant = multiple levels deeper (e.g., "1.3.1.3.1.2" under parent "1.3.1")
        parent_depth = len(parent_flow_index.split('.'))
        expected_depth = parent_depth + 1  # Direct children are exactly one level deeper
        
        direct_children = []
        deeper_descendants = []
        
        for fi in repo_indices:
            if fi.startswith(parent_prefix):
                fi_depth = len(fi.split('.'))
                if fi_depth == expected_depth:
                    direct_children.append(fi)
                else:
                    deeper_descendants.append(fi)
        
        # Priority 2: Direct children (sorted, with usage tracking)
        if direct_children:
            direct_children.sort(key=lambda fi: _parse_flow_index(fi))
            usage_key = f"{concept_name}@{parent_flow_index}:direct"
            usage_idx = self._usage.get(usage_key, 0)
            
            if usage_idx < len(direct_children):
                selected = direct_children[usage_idx]
                self._usage[usage_key] = usage_idx + 1
                return selected
        
        # Priority 3: Deeper descendants (only if no direct children available)
        if deeper_descendants:
            deeper_descendants.sort(key=lambda fi: _parse_flow_index(fi))
            usage_key = f"{concept_name}@{parent_flow_index}:deep"
            usage_idx = self._usage.get(usage_key, 0)
            
            if usage_idx < len(deeper_descendants):
                selected = deeper_descendants[usage_idx]
                self._usage[usage_key] = usage_idx + 1
                return selected
        
        return fallback_flow_index
    
    def register_flow_index(self, concept_name: str, flow_idx: str) -> None:
        """Track flow_index for a concept to create alias edges later."""
        if concept_name not in self.concept_to_flow_indices:
            self.concept_to_flow_indices[concept_name] = []
        if flow_idx not in self.concept_to_flow_indices[concept_name]:
            self.concept_to_flow_indices[concept_name].append(flow_idx)


# =============================================================================
# Node Creation
# =============================================================================

def _create_graph_node(
    concept_name: str,
    concept_attrs: Dict[str, Any],
    node_type: str,
    flow_index: str,
    level: int,
    extra_data: Optional[Dict[str, Any]] = None
) -> GraphNode:
    """Factory for creating graph nodes with consistent structure.
    
    Args:
        concept_name: The concept's name (used as label)
        concept_attrs: Attributes from concept repository
        node_type: NODE_TYPE_FUNCTION or NODE_TYPE_VALUE
        flow_index: The node's flow index
        level: Hierarchy level
        extra_data: Additional data to merge into node.data
    
    Returns:
        Configured GraphNode instance
    """
    node_data = {
        "is_ground": concept_attrs.get('is_ground_concept', False),
        "is_final": concept_attrs.get('is_final_concept', False),
        "axes": concept_attrs.get('reference_axis_names', []),
        "reference_data": concept_attrs.get('reference_data'),
        "concept_name": concept_name,
        "natural_name": concept_attrs.get('natural_name'),
        "flow_indices_from_repo": concept_attrs.get('flow_indices', []),
    }
    
    if extra_data:
        node_data.update(extra_data)
    
    return GraphNode(
        id=f"node@{flow_index}",
        label=concept_name,
        category=get_concept_category(concept_name, concept_attrs.get('type')),
        node_type=node_type,
        flow_index=flow_index,
        level=level,
        position={"x": 0, "y": 0},
        data=node_data
    )


def _try_add_node(
    nodes: Dict[str, GraphNode],
    node_id: str,
    concept_name: str,
    concept_attrs: Dict[str, Any],
    node_type: str,
    flow_index: str,
    level: int,
    resolver: FlowIndexResolver,
    extra_data: Optional[Dict[str, Any]] = None,
    fallback_flow_index: Optional[str] = None
) -> Tuple[str, bool]:
    """Try to add a node, handling collisions gracefully.
    
    Args:
        nodes: Dict of existing nodes
        node_id: Proposed node ID
        concept_name: The concept's name
        concept_attrs: Attributes from concept repository
        node_type: NODE_TYPE_FUNCTION or NODE_TYPE_VALUE
        flow_index: The node's flow index
        level: Hierarchy level
        resolver: FlowIndexResolver for tracking
        extra_data: Additional data for the node
        fallback_flow_index: Alternative flow_index if collision occurs
    
    Returns:
        Tuple of (final_node_id, was_created)
    """
    # Check for existing node
    if node_id in nodes:
        if nodes[node_id].label == concept_name:
            # Same concept, node already exists
            return node_id, False
        
        # Collision: different concept at same ID
        logger.warning(
            f"Node collision: {node_id} exists with '{nodes[node_id].label}', "
            f"wanted '{concept_name}'. Using fallback."
        )
        
        if fallback_flow_index:
            flow_index = fallback_flow_index
            node_id = f"node@{fallback_flow_index}"
            
            if node_id in nodes:
                return node_id, False
    
    # Create the node
    node = _create_graph_node(
        concept_name=concept_name,
        concept_attrs=concept_attrs,
        node_type=node_type,
        flow_index=flow_index,
        level=level,
        extra_data=extra_data
    )
    nodes[node_id] = node
    resolver.register_flow_index(concept_name, flow_index)
    
    return node_id, True


# =============================================================================
# Inference Processing
# =============================================================================

def _process_inference(
    inf: Dict[str, Any],
    nodes: Dict[str, GraphNode],
    edges: List[GraphEdge],
    concept_attrs: Dict[str, Dict[str, Any]],
    resolver: FlowIndexResolver
) -> bool:
    """Process a single inference, creating nodes and edges.
    
    Args:
        inf: Inference data dictionary
        nodes: Dict to add nodes to
        edges: List to add edges to
        concept_attrs: Concept name -> attributes mapping
        resolver: FlowIndexResolver instance
    
    Returns:
        True if processed successfully, False if skipped due to collision
    """
    flow_info = inf.get('flow_info', {})
    base_flow_index = flow_info.get('flow_index', '0')
    base_level = len(base_flow_index.split('.')) - 1
    
    target_name = inf.get('concept_to_infer', '')
    func_name = inf.get('function_concept', '')
    value_names = inf.get('value_concepts', [])
    context_names = inf.get('context_concepts', [])
    sequence = inf.get('inference_sequence', '')
    working_interp = inf.get('working_interpretation', {})
    
    if not target_name:
        return True
    
    # Create target node (the concept being inferred)
    target_id = f"node@{base_flow_index}"
    
    if target_id in nodes and nodes[target_id].label != target_name:
        logger.warning(
            f"Target collision: {target_id} exists with '{nodes[target_id].label}', "
            f"wanted '{target_name}'. Skipping inference at {base_flow_index}."
        )
        return False
    
    target_id, _ = _try_add_node(
        nodes=nodes,
        node_id=target_id,
        concept_name=target_name,
        concept_attrs=concept_attrs.get(target_name, {}),
        node_type=NODE_TYPE_VALUE,
        flow_index=base_flow_index,
        level=base_level,
        resolver=resolver
    )
    
    input_level = base_level + 1
    child_idx = 1
    
    # Process function concept
    if func_name:
        child_idx = _process_function_concept(
            func_name=func_name,
            target_id=target_id,
            base_flow_index=base_flow_index,
            child_idx=child_idx,
            input_level=input_level,
            sequence=sequence,
            working_interp=working_interp,
            nodes=nodes,
            edges=edges,
            concept_attrs=concept_attrs,
            resolver=resolver
        )
    
    # Process value concepts
    for idx, val_name in enumerate(value_names):
        if val_name:
            child_idx = _process_value_concept(
                val_name=val_name,
                val_idx=idx,
                target_id=target_id,
                base_flow_index=base_flow_index,
                child_idx=child_idx,
                input_level=input_level,
                nodes=nodes,
                edges=edges,
                concept_attrs=concept_attrs,
                resolver=resolver
            )
        else:
            child_idx += 1
    
    # Process context concepts
    for ctx_name in context_names:
        if ctx_name:
            child_idx = _process_context_concept(
                ctx_name=ctx_name,
                target_id=target_id,
                base_flow_index=base_flow_index,
                child_idx=child_idx,
                input_level=input_level,
                nodes=nodes,
                edges=edges,
                concept_attrs=concept_attrs,
                resolver=resolver
            )
        else:
            child_idx += 1
    
    return True


def _process_function_concept(
    func_name: str,
    target_id: str,
    base_flow_index: str,
    child_idx: int,
    input_level: int,
    sequence: str,
    working_interp: Dict[str, Any],
    nodes: Dict[str, GraphNode],
    edges: List[GraphEdge],
    concept_attrs: Dict[str, Dict[str, Any]],
    resolver: FlowIndexResolver
) -> int:
    """Process a function concept, creating node and edge."""
    fallback_flow_index = f"{base_flow_index}.{child_idx}"
    func_flow_index = resolver.get_flow_index(func_name, fallback_flow_index, base_flow_index)
    func_id = f"node@{func_flow_index}"
    
    func_id, _ = _try_add_node(
        nodes=nodes,
        node_id=func_id,
        concept_name=func_name,
        concept_attrs=concept_attrs.get(func_name, {}),
        node_type=NODE_TYPE_FUNCTION,
        flow_index=func_flow_index,
        level=input_level,
        resolver=resolver,
        extra_data={
            "sequence": sequence,
            "working_interpretation": working_interp,
        },
        fallback_flow_index=fallback_flow_index
    )
    
    edges.append(GraphEdge(
        id=f"edge-func-{base_flow_index}",
        source=func_id,
        target=target_id,
        edge_type=EDGE_TYPE_FUNCTION,
        label=sequence,
        flow_index=base_flow_index
    ))
    
    return child_idx + 1


def _process_value_concept(
    val_name: str,
    val_idx: int,
    target_id: str,
    base_flow_index: str,
    child_idx: int,
    input_level: int,
    nodes: Dict[str, GraphNode],
    edges: List[GraphEdge],
    concept_attrs: Dict[str, Dict[str, Any]],
    resolver: FlowIndexResolver
) -> int:
    """Process a value concept, creating node and edge."""
    fallback_flow_index = f"{base_flow_index}.{child_idx}"
    val_flow_index = resolver.get_flow_index(val_name, fallback_flow_index, base_flow_index)
    val_id = f"node@{val_flow_index}"
    
    # Handle collision by using fallback
    if val_id in nodes and nodes[val_id].label != val_name:
        logger.warning(
            f"Value collision: {val_id} exists with '{nodes[val_id].label}', "
            f"wanted '{val_name}'. Using fallback."
        )
        val_flow_index = fallback_flow_index
        val_id = f"node@{val_flow_index}"
    
    val_id, _ = _try_add_node(
        nodes=nodes,
        node_id=val_id,
        concept_name=val_name,
        concept_attrs=concept_attrs.get(val_name, {}),
        node_type=NODE_TYPE_VALUE,
        flow_index=val_flow_index,
        level=input_level,
        resolver=resolver
    )
    
    edges.append(GraphEdge(
        id=f"edge-val-{val_flow_index}",
        source=val_id,
        target=target_id,
        edge_type=EDGE_TYPE_VALUE,
        label=f":{val_idx + 1}",
        flow_index=val_flow_index
    ))
    
    return child_idx + 1


def _process_context_concept(
    ctx_name: str,
    target_id: str,
    base_flow_index: str,
    child_idx: int,
    input_level: int,
    nodes: Dict[str, GraphNode],
    edges: List[GraphEdge],
    concept_attrs: Dict[str, Dict[str, Any]],
    resolver: FlowIndexResolver
) -> int:
    """Process a context concept, creating node and edge."""
    fallback_flow_index = f"{base_flow_index}.{child_idx}"
    ctx_flow_index = resolver.get_flow_index(ctx_name, fallback_flow_index, base_flow_index)
    ctx_id = f"node@{ctx_flow_index}"
    
    # Handle collision by using fallback
    if ctx_id in nodes and nodes[ctx_id].label != ctx_name:
        logger.warning(
            f"Context collision: {ctx_id} exists with '{nodes[ctx_id].label}', "
            f"wanted '{ctx_name}'. Using fallback."
        )
        ctx_flow_index = fallback_flow_index
        ctx_id = f"node@{ctx_flow_index}"
    
    ctx_id, _ = _try_add_node(
        nodes=nodes,
        node_id=ctx_id,
        concept_name=ctx_name,
        concept_attrs=concept_attrs.get(ctx_name, {}),
        node_type=NODE_TYPE_VALUE,
        flow_index=ctx_flow_index,
        level=input_level,
        resolver=resolver,
        extra_data={"is_context": True}
    )
    
    edges.append(GraphEdge(
        id=f"edge-ctx-{ctx_flow_index}",
        source=ctx_id,
        target=target_id,
        edge_type=EDGE_TYPE_CONTEXT,
        label="ctx",
        flow_index=ctx_flow_index
    ))
    
    return child_idx + 1


# =============================================================================
# Alias Edge Creation
# =============================================================================

def _add_alias_edges(
    nodes: Dict[str, GraphNode],
    edges: List[GraphEdge],
    resolver: FlowIndexResolver
) -> None:
    """Create alias edges for concepts appearing at multiple flow indices.
    
    These connect duplicate nodes of the same concept with dashed lines (≡).
    """
    for concept_name, flow_indices in resolver.concept_to_flow_indices.items():
        if len(flow_indices) <= 1:
            continue
        
        sorted_indices = sorted(flow_indices, key=lambda fi: _parse_flow_index(fi))
        
        for i in range(len(sorted_indices) - 1):
            source_id = f"node@{sorted_indices[i]}"
            target_id = f"node@{sorted_indices[i + 1]}"
            
            if source_id in nodes and target_id in nodes:
                edges.append(GraphEdge(
                    id=f"edge-alias-{concept_name}-{i}",
                    source=source_id,
                    target=target_id,
                    edge_type=EDGE_TYPE_ALIAS,
                    label="≡",
                    flow_index=sorted_indices[i]
                ))


# =============================================================================
# Layout Calculation
# =============================================================================

def _calculate_positions(
    nodes: List[GraphNode], 
    h_spacing: int = 300, 
    v_spacing: int = 100, 
    layout_mode: str = "hierarchical"
) -> None:
    """Calculate x, y positions for nodes.
    
    Args:
        nodes: List of graph nodes to position
        h_spacing: Horizontal spacing between levels
        v_spacing: Vertical spacing between nodes
        layout_mode: "hierarchical" or "flow_aligned"
    """
    if not nodes:
        return
    
    if layout_mode == "flow_aligned":
        _calculate_positions_flow_aligned(nodes, h_spacing, v_spacing)
    else:
        _calculate_positions_hierarchical(nodes, h_spacing, v_spacing)


def _calculate_positions_hierarchical(
    nodes: List[GraphNode], 
    h_spacing: int = 300, 
    v_spacing: int = 100
) -> None:
    """Calculate positions using hierarchical layout (left-to-right data flow).
    
    Layout flows LEFT to RIGHT (children/inputs on left, parents/outputs on right):
    - x = (max_level - level) * horizontal_spacing
    - y = sorted by full flow_index to preserve parent-child hierarchy
    """
    if not nodes:
        return
    
    max_level = max(node.level for node in nodes)
    
    # Group nodes by level
    level_groups: Dict[int, List[GraphNode]] = {}
    for node in nodes:
        level_groups.setdefault(node.level, []).append(node)
    
    # Sort and position nodes within each level
    for level, level_nodes in level_groups.items():
        level_nodes.sort(key=lambda n: _parse_flow_index(n.flow_index))
        x = (max_level - level) * h_spacing
        
        for idx, node in enumerate(level_nodes):
            node.position = {"x": x, "y": idx * v_spacing}


def _calculate_positions_flow_aligned(
    nodes: List[GraphNode], 
    h_spacing: int = 300, 
    v_spacing: int = 120
) -> None:
    """Calculate positions with flow-aligned layout.
    
    Each unique flow_index gets its own horizontal line (y-position).
    - x = (max_level - level) * horizontal_spacing (preserves depth)
    - y = determined by flow_index (each flow_index on its own line)
    """
    if not nodes:
        return
    
    max_level = max(node.level for node in nodes)
    
    # Collect and sort unique flow_indices
    all_flow_indices = sorted(
        set(node.flow_index for node in nodes if node.flow_index),
        key=lambda fi: _parse_flow_index(fi)
    )
    
    # Map flow_index -> row number
    flow_index_to_row = {fi: idx for idx, fi in enumerate(all_flow_indices)}
    
    # Assign positions
    for node in nodes:
        x = (max_level - node.level) * h_spacing
        row = flow_index_to_row.get(node.flow_index, len(all_flow_indices))
        node.position = {"x": x, "y": row * v_spacing}


# =============================================================================
# Main Graph Building Function
# =============================================================================

def build_graph_from_repositories(
    concepts_data: List[Dict[str, Any]],
    inferences_data: List[Dict[str, Any]],
    layout_mode: str = "hierarchical"
) -> GraphData:
    """Build graph model from concept and inference repositories.
    
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
        layout_mode: "hierarchical" or "flow_aligned"
        
    Returns:
        GraphData with nodes and edges for visualization
    """
    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []
    
    # Build concept lookup
    concept_attrs = {c.get('concept_name', ''): c for c in concepts_data}
    
    # Initialize flow index resolver
    resolver = FlowIndexResolver(concepts_data)
    
    # Process each inference
    for inf in inferences_data:
        _process_inference(inf, nodes, edges, concept_attrs, resolver)
    
    # Create alias edges for multi-occurrence concepts
    _add_alias_edges(nodes, edges, resolver)
    
    # Calculate positions
    node_list = list(nodes.values())
    _calculate_positions(node_list, layout_mode=layout_mode)
    
    return GraphData(nodes=node_list, edges=edges)


# =============================================================================
# GraphService Class
# =============================================================================

class GraphService:
    """Service for managing graph state."""
    
    def __init__(self):
        self.current_graph: Optional[GraphData] = None
        self.concepts_data: List[Dict[str, Any]] = []
        self.inferences_data: List[Dict[str, Any]] = []
        self.current_layout_mode: str = "hierarchical"
    
    def load_from_files(
        self, 
        concepts_path: str, 
        inferences_path: str, 
        layout_mode: str = "hierarchical"
    ) -> GraphData:
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
