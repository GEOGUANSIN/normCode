"""
Preview components for Execute tab.
Handles rendering of concepts, inferences, and inputs file previews.
Enhanced with visual categorization and graph visualization (hybrid approach).
"""

import streamlit as st
import json
from typing import Dict, Any, Optional, List, Tuple

from core.file_utils import get_file_content


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def render_file_previews(
    config: Dict[str, Any],
    loaded_concepts: Optional[Dict],
    loaded_inferences: Optional[Dict],
    loaded_inputs: Optional[Dict]
):
    """
    Render enhanced file preview sections with visual categorization.
    
    Args:
        config: Configuration dictionary from sidebar
        loaded_concepts: Loaded concepts data (if any)
        loaded_inferences: Loaded inferences data (if any)
        loaded_inputs: Loaded inputs data (if any)
    """
    # Load data once
    concepts_data = None
    inferences_data = None
    inputs_data = None
    
    try:
        concepts_content = get_file_content(config['concepts_file'], loaded_concepts)
        concepts_data = json.loads(concepts_content)
    except Exception as e:
        st.error(f"Error loading concepts: {e}")
    
    try:
        inferences_content = get_file_content(config['inferences_file'], loaded_inferences)
        inferences_data = json.loads(inferences_content)
    except Exception as e:
        st.error(f"Error loading inferences: {e}")
    
    has_inputs = config['inputs_file'] is not None or loaded_inputs is not None
    if has_inputs:
        try:
            inputs_content = get_file_content(config['inputs_file'], loaded_inputs)
            inputs_data = json.loads(inputs_content)
        except Exception as e:
            st.error(f"Error loading inputs: {e}")
    
    # View toggle
    view_mode = st.radio(
        "Preview Mode",
        ["📋 Card View", "🔀 Graph View"],
        horizontal=True,
        key="preview_mode_toggle"
    )
    
    if view_mode == "📋 Card View":
        _render_card_view(concepts_data, inferences_data, inputs_data)
    else:
        _render_graph_view(concepts_data, inferences_data)


# =============================================================================
# CARD VIEW (Default)
# =============================================================================

def _render_card_view(
    concepts_data: Optional[List[Dict[str, Any]]],
    inferences_data: Optional[List[Dict[str, Any]]],
    inputs_data: Optional[Dict[str, Any]]
):
    """Render the card-based preview with visual enhancements."""
    col1, col2 = st.columns(2)
    
    with col1:
        if concepts_data:
            _render_concepts_preview(concepts_data)
        else:
            st.warning("No concepts data available")
    
    with col2:
        if inferences_data:
            _render_inferences_preview(inferences_data)
        else:
            st.warning("No inferences data available")
    
    # References section - show both input data and concept repo references
    st.divider()
    
    # Get concept repo references (concepts with reference_data defined)
    concept_refs = []
    if concepts_data:
        concept_refs = [c for c in concepts_data if c.get('reference_data') is not None]
    
    # Display tabs for different reference sources
    if inputs_data or concept_refs:
        ref_tabs = st.tabs(["📥 Input Data References", "📚 Concept Repo References"])
        
        with ref_tabs[0]:
            if inputs_data:
                _render_inputs_preview(inputs_data)
            else:
                st.info("No input data file provided")
        
        with ref_tabs[1]:
            if concept_refs:
                _render_concept_repo_references(concept_refs)
            else:
                st.info("No concepts with pre-defined reference data in concept repo")


def _get_concept_category(concept_name: str) -> str:
    """
    Categorize concept by name pattern (matching editor app logic).
    
    - Semantic Functions: ::({}) and <{}>
    - Semantic Values: {}, <>, []
    - Syntactic Functions: everything else
    """
    if ':(' in concept_name or ':<' in concept_name:
        return "semantic-function"
    elif ((concept_name.startswith('{') and concept_name.rstrip('?').endswith('}')) or 
          (concept_name.startswith('<') and concept_name.endswith('>')) or 
          (concept_name.startswith('[') and concept_name.endswith(']'))):
        return "semantic-value"
    else:
        return "syntactic-function"


def _get_category_style(category: str) -> Tuple[str, str, str]:
    """Get (emoji, color_name, description) for a category."""
    styles = {
        'semantic-function': ('🟣', '#7b68ee', 'Semantic Function'),
        'semantic-value': ('🔵', '#3b82f6', 'Semantic Value'),
        'syntactic-function': ('⚫', '#64748b', 'Syntactic Function'),
    }
    return styles.get(category, ('⚪', '#888', 'Unknown'))


def _render_concepts_preview(concepts_data: List[Dict[str, Any]]):
    """Render concepts with color-coded categories and badges."""
    st.subheader("📦 Concepts")
    
    # Category counts
    categories = {
        'semantic-function': 0,
        'semantic-value': 0,
        'syntactic-function': 0
    }
    ground_count = sum(1 for c in concepts_data if c.get('is_ground_concept', False))
    final_count = sum(1 for c in concepts_data if c.get('is_final_concept', False))
    
    for concept in concepts_data:
        category = _get_concept_category(concept.get('concept_name', ''))
        categories[category] += 1
    
    # Summary metrics in a compact row
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total", len(concepts_data))
    with cols[1]:
        st.metric("Ground", ground_count)
    with cols[2]:
        st.metric("Final", final_count)
    with cols[3]:
        invariant_count = sum(1 for c in concepts_data if c.get('is_invariant', False))
        st.metric("Invariant", invariant_count)
    
    # Visual legend (collapsed by default)
    with st.expander("🎨 Visual Legend", expanded=False):
        st.markdown(f"""
| Icon | Category | Count | Pattern |
|:----:|----------|:-----:|---------|
| 🟣 | Semantic Function | {categories['semantic-function']} | `::({{}})`, `<{{}}>` |
| 🔵 | Semantic Value | {categories['semantic-value']} | `{{}}`, `<>`, `[]` |
| ⚫ | Syntactic Function | {categories['syntactic-function']} | Other patterns |
        """)
        st.caption("**Badges:** 🌱 Ground • 🎯 Final • 🔒 Invariant")
    
    # Concept list with visual indicators
    with st.expander(f"📋 Concept List ({len(concepts_data)} total)", expanded=True):
        # Use container with fixed height for scrolling
        container = st.container(height=250)
        with container:
            for concept in concepts_data:
                _render_concept_card(concept)


def _render_concept_card(concept: Dict[str, Any]):
    """Render a single concept as a mini card."""
    name = concept.get('concept_name', 'Unknown')
    category = _get_concept_category(name)
    emoji, color, _ = _get_category_style(category)
    
    # Build badges
    badges = []
    if concept.get('is_ground_concept'):
        badges.append("🌱")
    if concept.get('is_final_concept'):
        badges.append("🎯")
    if concept.get('is_invariant'):
        badges.append("🔒")
    
    badge_str = " ".join(badges)
    
    # Truncate long names
    display_name = name if len(name) <= 35 else name[:32] + "..."
    
    # Format with colored bar using markdown
    st.markdown(
        f"<div style='border-left: 3px solid {color}; padding-left: 8px; margin-bottom: 4px;'>"
        f"<span style='font-size: 0.85em;'>{emoji} <code>{display_name}</code> {badge_str}</span>"
        f"</div>",
        unsafe_allow_html=True
    )


def _render_inferences_preview(inferences_data: List[Dict[str, Any]]):
    """Render inferences with relationship arrows."""
    st.subheader("⚡ Inferences")
    
    # Metrics
    cols = st.columns(3)
    with cols[0]:
        st.metric("Total", len(inferences_data))
    with cols[1]:
        with_flow = sum(1 for i in inferences_data if i.get('flow_info'))
        st.metric("With Flow", with_flow)
    with cols[2]:
        # Count unique sequences
        sequences = set(i.get('inference_sequence', '') for i in inferences_data)
        st.metric("Sequences", len(sequences))
    
    # Legend
    with st.expander("🔗 Relationship Legend", expanded=False):
        st.markdown("""
| Symbol | Meaning |
|:------:|---------|
| ⬅️ | **Function**: Target concept inferred by function |
| 📥 | **Values**: Input value concepts |
        """)
    
    # Inference list
    with st.expander(f"📋 Inference List ({len(inferences_data)} total)", expanded=True):
        container = st.container(height=250)
        with container:
            for inference in inferences_data:
                _render_inference_card(inference)


def _render_inference_card(inference: Dict[str, Any]):
    """Render a single inference as a mini card."""
    concept_to_infer = inference.get('concept_to_infer', '?')
    function_concept = inference.get('function_concept', '?')
    value_concepts = inference.get('value_concepts', [])
    sequence = inference.get('inference_sequence', '?')
    
    # Truncate names
    def trunc(s, max_len=20):
        return s if len(s) <= max_len else s[:max_len-3] + "..."
    
    # Build value string
    if value_concepts:
        if len(value_concepts) <= 2:
            value_str = ", ".join(trunc(v, 15) for v in value_concepts)
        else:
            value_str = f"{trunc(value_concepts[0], 15)}, ... (+{len(value_concepts)-1})"
    else:
        value_str = None
    
    # Render with flow-like appearance
    # Build value HTML separately to avoid f-string escaping issues
    value_html = ""
    if value_str:
        value_html = f"<br/><span style='font-size: 0.8em; color: #7b68ee;'>📥 {value_str}</span>"
    
    html = (
        f"<div style='border-left: 3px solid #4a90e2; padding-left: 8px; margin-bottom: 6px;'>"
        f"<span style='font-size: 0.75em; color: #888;'>[{sequence}]</span><br/>"
        f"<code style='font-size: 0.85em;'>{trunc(concept_to_infer)}</code> "
        f"<span style='color: #4a90e2;'>⬅️</span> "
        f"<code style='font-size: 0.85em;'>{trunc(function_concept)}</code>"
        f"{value_html}"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_inputs_preview(inputs_data: Dict[str, Any]):
    """Render inputs with data preview, separating metadata from concept data."""
    st.subheader("📥 References (Input Data)")
    st.caption("Ground concept values provided in the input file")
    
    if not isinstance(inputs_data, dict):
        # Handle list format
        if isinstance(inputs_data, list):
            st.metric("Input Items", len(inputs_data))
            with st.expander("📋 Input List", expanded=True):
                for item in inputs_data:
                    if isinstance(item, dict) and 'concept_name' in item:
                        _render_tensor_input(
                            item.get('concept_name', 'Unknown'),
                            item.get('reference_data', item.get('value', '')),
                            source="input"
                        )
        return
    
    # Separate metadata keys (starting with _) from concept data
    metadata = {}
    concept_inputs = {}
    
    for key, value in inputs_data.items():
        if key.startswith('_'):
            metadata[key] = value
        else:
            concept_inputs[key] = value
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ground Concepts", len(concept_inputs))
    with col2:
        st.metric("Metadata Fields", len(metadata))
    with col3:
        # Count tensor inputs
        tensor_count = sum(1 for v in concept_inputs.values() 
                          if isinstance(v, dict) and 'data' in v and 'axes' in v)
        st.metric("Tensor Inputs", tensor_count)
    
    # Render metadata section (if any)
    if metadata:
        with st.expander("📝 Input File Metadata", expanded=False):
            _render_metadata_section(metadata)
    
    # Render concept inputs
    if concept_inputs:
        with st.expander(f"🌱 Ground Concept References ({len(concept_inputs)} concepts)", expanded=True):
            for key, value in concept_inputs.items():
                _render_tensor_input(key, value, source="input")


def _render_metadata_section(metadata: Dict[str, Any]):
    """Render metadata fields (_comment, _instructions, _note, etc.)."""
    # Define icons for known metadata types
    icons = {
        '_comment': '💬',
        '_comments': '💬',
        '_instruction': '📋',
        '_instructions': '📋',
        '_note': '📌',
        '_notes': '📌',
        '_description': '📖',
        '_version': '🏷️',
        '_author': '👤',
    }
    
    for key, value in metadata.items():
        icon = icons.get(key, '📎')
        display_key = key.lstrip('_').replace('_', ' ').title()
        
        st.markdown(
            f"<div style='background: #f8f9fa; border-radius: 6px; padding: 10px; margin-bottom: 8px;'>"
            f"<span style='font-weight: 600; color: #495057;'>{icon} {display_key}</span><br/>"
            f"<span style='color: #6c757d; font-size: 0.9em;'>{value}</span>"
            f"</div>",
            unsafe_allow_html=True
        )


def _render_concept_repo_references(concepts_with_refs: List[Dict[str, Any]]):
    """Render references defined in the concept repository."""
    st.subheader("📚 References (Concept Repo)")
    st.caption("Pre-defined reference data in concept definitions")
    
    # Metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Concepts with References", len(concepts_with_refs))
    with col2:
        # Count different types
        invariant_count = sum(1 for c in concepts_with_refs if c.get('is_invariant', False))
        st.metric("Invariant References", invariant_count)
    
    with st.expander(f"📋 Concept References ({len(concepts_with_refs)} total)", expanded=True):
        for concept in concepts_with_refs:
            name = concept.get('concept_name', 'Unknown')
            ref_data = concept.get('reference_data')
            ref_axes = concept.get('reference_axis_names')
            is_invariant = concept.get('is_invariant', False)
            description = concept.get('description', '')
            
            # Build value dict for tensor display
            if ref_axes:
                value = {'data': ref_data if isinstance(ref_data, list) else [ref_data], 'axes': ref_axes}
            else:
                value = ref_data
            
            _render_tensor_input(name, value, source="repo", is_invariant=is_invariant, description=description)


def _render_tensor_input(key: str, value: Any, source: str = "input", is_invariant: bool = False, description: str = ""):
    """
    Render a single input item with special handling for tensor data.
    
    Args:
        key: Concept name
        value: The reference value (tensor format: {"data": [[...]], "axes": ["axis1", "axis2"]})
        source: "input" for inputs.json, "repo" for concept repo
        is_invariant: Whether this is an invariant reference
        description: Optional description of the concept
    
    Tensor format: {"data": [[...]], "axes": ["axis1", "axis2"]}
    """
    # Check if this is a tensor with data and axes
    if isinstance(value, dict) and 'data' in value and 'axes' in value:
        _render_tensor_display(key, value['data'], value['axes'], source=source, is_invariant=is_invariant, description=description)
    elif isinstance(value, dict) and 'data' in value:
        # Has data but no axes - treat as simple tensor
        _render_tensor_display(key, value['data'], None, source=source, is_invariant=is_invariant, description=description)
    else:
        # Simple value - render as before
        _render_simple_input(key, value, source=source, is_invariant=is_invariant, description=description)


def _render_simple_input(key: str, value: Any, source: str = "input", is_invariant: bool = False, description: str = ""):
    """Render a simple (non-tensor) input value."""
    if isinstance(value, (list, dict)):
        preview = json.dumps(value, ensure_ascii=False)
        if len(preview) > 100:
            preview = preview[:97] + "..."
    else:
        preview = str(value)
        if len(preview) > 100:
            preview = preview[:97] + "..."
    
    # Choose color based on source
    border_color = "#22c55e" if source == "input" else "#6366f1"  # Green for input, Indigo for repo
    icon = "📥" if source == "input" else "📚"
    
    # Build badges
    badges = []
    if is_invariant:
        badges.append("<span style='background: #fef3c7; color: #92400e; padding: 1px 6px; border-radius: 3px; font-size: 0.7em;'>🔒 Invariant</span>")
    
    badge_html = " ".join(badges)
    
    # Description line
    desc_html = f"<div style='font-size: 0.75em; color: #888; font-style: italic;'>{description}</div>" if description else ""
    
    st.markdown(
        f"<div style='border-left: 3px solid {border_color}; padding-left: 8px; margin-bottom: 8px; background: #fafafa; border-radius: 0 4px 4px 0; padding: 8px;'>"
        f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
        f"<span style='font-size: 0.9em;'>{icon} <code>{key}</code></span>"
        f"<span>{badge_html}</span>"
        f"</div>"
        f"{desc_html}"
        f"<div style='font-size: 0.85em; color: #444; margin-top: 4px; font-family: monospace; background: white; padding: 4px 8px; border-radius: 4px;'>{preview}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


def _render_tensor_display(
    concept_name: str, 
    data: Any, 
    axes: Optional[List[str]],
    source: str = "input",
    is_invariant: bool = False,
    description: str = ""
):
    """
    Render tensor data with an interactive viewer.
    
    For tensors with >2 dimensions, provides axis selectors to slice through
    the data while displaying up to 2 axes as a table/list.
    
    Args:
        concept_name: Name of the concept
        data: Tensor data (nested list structure)
        axes: List of axis names
        source: "input" for inputs.json, "repo" for concept repo
        is_invariant: Whether this is an invariant reference
        description: Optional description
    """
    # Calculate shape and dimensions
    shape = _get_tensor_shape(data)
    dims = len(shape)
    
    # Generate axis names if not provided
    if axes is None or len(axes) < dims:
        axes = axes or []
        axes = axes + [f"axis_{i}" for i in range(len(axes), dims)]
    
    # Create a unique key for this tensor viewer
    viewer_key = f"tensor_{concept_name.replace(' ', '_').replace('{', '').replace('}', '').replace(':', '_')}"
    
    # Choose colors based on source
    if source == "input":
        border_color = "#22c55e"  # Green
        bg_gradient = "linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)"
        text_color = "#166534"
        badge_bg = "#16a34a"
        icon = "📥"
        source_label = "Input Data"
    else:
        border_color = "#6366f1"  # Indigo
        bg_gradient = "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)"
        text_color = "#4338ca"
        badge_bg = "#6366f1"
        icon = "📚"
        source_label = "Concept Repo"
    
    # Build badges
    badges_html = f"<span style='font-size: 0.65em; color: white; background: {badge_bg}; padding: 2px 6px; border-radius: 3px; margin-right: 4px;'>{source_label}</span>"
    if is_invariant:
        badges_html += "<span style='font-size: 0.65em; background: #fef3c7; color: #92400e; padding: 2px 6px; border-radius: 3px;'>🔒 Invariant</span>"
    
    # Container with styled border
    with st.container():
        # Header with concept name and shape info
        axes_str = " × ".join(f"{ax}[{s}]" for ax, s in zip(axes, shape)) if shape else "scalar"
        shape_str = "×".join(str(s) for s in shape) if shape else "scalar"
        
        # Description line
        desc_html = f"<div style='font-size: 0.75em; color: {text_color}; font-style: italic; margin-bottom: 8px;'>{description}</div>" if description else ""
        
        st.markdown(
            f"<div style='border: 2px solid {border_color}; border-radius: 8px; padding: 12px; margin-bottom: 12px; background: {bg_gradient};'>"
            f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>"
            f"<span style='font-size: 1em; font-weight: 600;'>{icon} <code>{concept_name}</code></span>"
            f"<span>{badges_html}</span>"
            f"</div>"
            f"{desc_html}"
            f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
            f"<span style='font-size: 0.8em; color: {text_color};'>Axes: <code>{axes_str}</code></span>"
            f"<span style='font-size: 0.75em; color: {text_color}; background: white; padding: 2px 8px; border-radius: 4px;'>📐 Shape: {shape_str}</span>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Display based on dimensions
        if dims == 0:
            # Scalar
            _render_scalar_value(data)
        elif dims == 1:
            # 1D tensor - show as list
            _render_1d_tensor(data, axes[0] if axes else "index")
        elif dims == 2:
            # 2D tensor - show as table
            _render_2d_tensor(data, axes)
        else:
            # Higher dimensional - show interactive slicer
            _render_interactive_tensor_viewer(data, axes, shape, viewer_key)


def _get_tensor_shape(data: Any) -> Tuple[int, ...]:
    """Get the shape of tensor data as a tuple."""
    if not isinstance(data, list):
        return ()
    
    shape = []
    current = data
    while isinstance(current, list):
        shape.append(len(current))
        if len(current) > 0:
            current = current[0]
        else:
            break
    
    return tuple(shape)


def _get_tensor_shape_str(data: Any) -> str:
    """Get a string representation of tensor shape."""
    shape = _get_tensor_shape(data)
    if not shape:
        return "scalar"
    return "×".join(str(s) for s in shape)


def _count_dimensions(data: Any) -> int:
    """Count the number of dimensions in nested list data."""
    return len(_get_tensor_shape(data))


def _render_scalar_value(data: Any):
    """Render a scalar (0D) value."""
    formatted = _format_cell_value(data)
    st.markdown(
        f"<div style='background: white; border: 1px solid #d1d5db; border-radius: 6px; "
        f"padding: 16px; text-align: center; font-size: 1.2em;'>"
        f"<span style='color: #6b7280; font-size: 0.7em;'>Value:</span><br/>"
        f"<strong>{formatted}</strong>"
        f"</div>",
        unsafe_allow_html=True
    )


def _render_1d_tensor(data: List[Any], axis_name: str):
    """Render a 1D tensor as a styled list."""
    # For short lists, show inline
    if len(data) <= 5:
        cols = st.columns(len(data))
        for i, (col, item) in enumerate(zip(cols, data)):
            with col:
                st.markdown(
                    f"<div style='text-align: center; background: white; border: 1px solid #d1d5db; "
                    f"border-radius: 4px; padding: 8px;'>"
                    f"<div style='font-size: 0.7em; color: #9ca3af;'>{axis_name}[{i}]</div>"
                    f"<div style='font-weight: 500;'>{_format_cell_value(item)}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    else:
        # For longer lists, show as vertical list with scrolling
        items_html = "".join(
            f"<div style='display: flex; gap: 8px; padding: 4px 0; border-bottom: 1px solid #e5e7eb;'>"
            f"<span style='color: #9ca3af; min-width: 60px;'>[{i}]</span>"
            f"<span>{_format_cell_value(item)}</span>"
            f"</div>"
            for i, item in enumerate(data)
        )
        st.markdown(
            f"<div style='max-height: 200px; overflow-y: auto; background: white; "
            f"border-radius: 4px; padding: 8px;'>{items_html}</div>",
            unsafe_allow_html=True
        )


def _render_2d_tensor(data: List[List[Any]], axes: Optional[List[str]]):
    """Render a 2D tensor as a styled table."""
    import pandas as pd
    
    row_axis = axes[0] if axes and len(axes) > 0 else "row"
    col_axis = axes[1] if axes and len(axes) > 1 else "col"
    
    # For small tensors, use HTML table for better formatting
    max_cols = max(len(row) for row in data) if data else 0
    
    # Use HTML table for better control over styling
    if len(data) <= 20 and max_cols <= 10:
        _render_2d_tensor_html(data, axes)
        return
    
    # For larger tensors, use pandas DataFrame
    try:
        col_headers = [f"{col_axis}[{i}]" for i in range(max_cols)]
        row_headers = [f"{row_axis}[{i}]" for i in range(len(data))]
        
        # Format data (use plain text for DataFrame)
        formatted_data = []
        for row in data:
            formatted_row = [_format_cell_value(cell, html=False) for cell in row]
            # Pad if needed
            formatted_row.extend([''] * (max_cols - len(formatted_row)))
            formatted_data.append(formatted_row)
        
        df = pd.DataFrame(formatted_data, columns=col_headers, index=row_headers)
        
        # Display dataframe
        st.dataframe(
            df,
            use_container_width=True,
            height=min(400, 40 + len(data) * 35)
        )
    except Exception as e:
        # Fallback to custom HTML table
        _render_2d_tensor_html(data, axes)


def _render_2d_tensor_html(data: List[List[Any]], axes: Optional[List[str]]):
    """Render a 2D tensor as an HTML table (fallback when pandas fails)."""
    row_axis = axes[0] if axes and len(axes) > 0 else "row"
    col_axis = axes[1] if axes and len(axes) > 1 else "col"
    
    max_cols = max(len(row) for row in data) if data else 0
    
    # Build HTML table
    table_html = "<table style='width: 100%; border-collapse: collapse; font-size: 0.9em;'>"
    
    # Header row
    table_html += "<thead><tr style='background: #f1f5f9;'>"
    table_html += "<th style='padding: 8px; border: 1px solid #e2e8f0;'></th>"  # Corner cell
    for j in range(max_cols):
        table_html += f"<th style='padding: 8px; border: 1px solid #e2e8f0; color: #64748b;'>{col_axis}[{j}]</th>"
    table_html += "</tr></thead>"
    
    # Data rows
    table_html += "<tbody>"
    for i, row in enumerate(data):
        table_html += "<tr>"
        table_html += f"<td style='padding: 8px; border: 1px solid #e2e8f0; background: #f8fafc; color: #64748b; font-weight: 500;'>{row_axis}[{i}]</td>"
        for j in range(max_cols):
            cell_value = row[j] if j < len(row) else ""
            formatted = _format_cell_value(cell_value, html=True)
            table_html += f"<td style='padding: 8px; border: 1px solid #e2e8f0; text-align: center;'>{formatted}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"
    
    st.markdown(table_html, unsafe_allow_html=True)


def _render_interactive_tensor_viewer(
    data: Any, 
    axes: List[str], 
    shape: Tuple[int, ...], 
    viewer_key: str
):
    """
    Render an interactive tensor viewer for 3D+ tensors.
    
    Allows users to:
    - Select which axes to display as rows/columns (up to 2)
    - Choose indices for other axes via sliders
    - View slices of the tensor data
    """
    dims = len(shape)
    
    st.markdown("#### 🎛️ Tensor Slicer")
    st.caption("Select axes to display and indices for other dimensions")
    
    # Initialize session state for this viewer
    state_key = f"tensor_viewer_state_{viewer_key}"
    if state_key not in st.session_state:
        # Default: display first 2 axes, set other indices to 0
        st.session_state[state_key] = {
            'display_axes': list(range(min(2, dims))),  # Which axes to display
            'slice_indices': {i: 0 for i in range(dims)},  # Index for each axis
            'view_mode': 'table' if dims >= 2 else 'list'
        }
    
    viewer_state = st.session_state[state_key]
    
    # === AXIS SELECTION ===
    with st.container():
        st.markdown("**📊 Display Axes**")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Row axis selector
            row_axis_options = list(range(dims))
            current_row = viewer_state['display_axes'][0] if viewer_state['display_axes'] else 0
            row_axis = st.selectbox(
                "Row Axis",
                options=row_axis_options,
                format_func=lambda i: f"{axes[i]} (size {shape[i]})",
                index=current_row,
                key=f"{viewer_key}_row_axis"
            )
        
        with col2:
            # Column axis selector (for 2D+ display)
            if dims >= 2:
                col_axis_options = [i for i in range(dims) if i != row_axis]
                current_col = viewer_state['display_axes'][1] if len(viewer_state['display_axes']) > 1 else (1 if 1 != row_axis else 0)
                if current_col == row_axis:
                    current_col = col_axis_options[0] if col_axis_options else 0
                
                col_axis = st.selectbox(
                    "Column Axis",
                    options=col_axis_options,
                    format_func=lambda i: f"{axes[i]} (size {shape[i]})",
                    index=col_axis_options.index(current_col) if current_col in col_axis_options else 0,
                    key=f"{viewer_key}_col_axis"
                )
            else:
                col_axis = None
        
        with col3:
            # View mode toggle
            view_mode = st.radio(
                "View",
                ["Table", "List", "JSON"],
                key=f"{viewer_key}_view_mode",
                horizontal=False
            )
    
    # Update display axes
    display_axes = [row_axis]
    if col_axis is not None:
        display_axes.append(col_axis)
    viewer_state['display_axes'] = display_axes
    
    # === SLICE INDEX SELECTORS ===
    # For axes not being displayed, show index selectors
    slice_axes = [i for i in range(dims) if i not in display_axes]
    
    if slice_axes:
        st.markdown("**🔢 Slice Indices** (for non-displayed axes)")
        
        # Create columns for slice selectors
        num_slicers = len(slice_axes)
        cols = st.columns(min(num_slicers, 4))
        
        slice_indices = {}
        for idx, axis_idx in enumerate(slice_axes):
            with cols[idx % 4]:
                axis_name = axes[axis_idx]
                axis_size = shape[axis_idx]
                
                current_idx = viewer_state['slice_indices'].get(axis_idx, 0)
                current_idx = min(current_idx, axis_size - 1)  # Ensure valid
                
                selected_idx = st.slider(
                    f"{axis_name}",
                    min_value=0,
                    max_value=max(0, axis_size - 1),
                    value=current_idx,
                    key=f"{viewer_key}_slice_{axis_idx}",
                    help=f"Select index for {axis_name} axis (0 to {axis_size - 1})"
                )
                slice_indices[axis_idx] = selected_idx
        
        viewer_state['slice_indices'].update(slice_indices)
    
    # === SLICE THE DATA ===
    sliced_data = _slice_tensor(data, display_axes, viewer_state['slice_indices'], dims)
    
    # === DISPLAY THE SLICE ===
    st.markdown("---")
    
    # Show what slice we're viewing
    slice_desc = _get_slice_description(axes, shape, display_axes, viewer_state['slice_indices'])
    st.caption(f"📍 Viewing: {slice_desc}")
    
    if view_mode == "JSON":
        st.json(sliced_data)
    elif view_mode == "List" or len(display_axes) == 1:
        if isinstance(sliced_data, list):
            _render_1d_tensor(sliced_data, axes[display_axes[0]])
        else:
            _render_scalar_value(sliced_data)
    else:  # Table view
        if isinstance(sliced_data, list) and len(sliced_data) > 0 and isinstance(sliced_data[0], list):
            display_axes_names = [axes[i] for i in display_axes]
            _render_2d_tensor(sliced_data, display_axes_names)
        elif isinstance(sliced_data, list):
            _render_1d_tensor(sliced_data, axes[display_axes[0]])
        else:
            _render_scalar_value(sliced_data)


def _slice_tensor(
    data: Any, 
    display_axes: List[int], 
    slice_indices: Dict[int, int],
    total_dims: int
) -> Any:
    """
    Slice a tensor to extract a 2D (or lower) view.
    
    Args:
        data: The full tensor data
        display_axes: Which axes to keep (display)
        slice_indices: Index values for axes not in display_axes
        total_dims: Total number of dimensions
    
    Returns:
        Sliced data (2D or lower)
    """
    if total_dims <= 2:
        return data
    
    # Build the slice path
    # We need to iterate through dimensions and either:
    # - Keep the whole axis (if it's in display_axes)
    # - Select a single index (if it's in slice_indices)
    
    result = data
    
    # Process from outermost to innermost dimension
    # But we need to account for how axes shift as we slice
    
    # Simpler approach: recursively extract the slice
    def extract_slice(d: Any, dim: int) -> Any:
        if dim >= total_dims:
            return d
        
        if not isinstance(d, list):
            return d
        
        if dim in display_axes:
            # Keep this dimension - recurse into each element
            return [extract_slice(item, dim + 1) for item in d]
        else:
            # Slice this dimension - take single index
            idx = slice_indices.get(dim, 0)
            if idx < len(d):
                return extract_slice(d[idx], dim + 1)
            else:
                return None
    
    return extract_slice(data, 0)


def _get_slice_description(
    axes: List[str], 
    shape: Tuple[int, ...], 
    display_axes: List[int],
    slice_indices: Dict[int, int]
) -> str:
    """Generate a human-readable description of the current slice."""
    parts = []
    for i in range(len(shape)):
        if i in display_axes:
            parts.append(f"{axes[i]}[:]")
        else:
            idx = slice_indices.get(i, 0)
            parts.append(f"{axes[i]}[{idx}]")
    
    return " × ".join(parts)


def _format_cell_value(value: Any, html: bool = True) -> str:
    """
    Format a cell value for display.
    
    Args:
        value: The value to format
        html: If True, return HTML-formatted string. If False, return plain text.
    """
    if value is None:
        return "∅"
    if isinstance(value, str):
        # Check for special syntax like %(...)
        if value.startswith('%(') and value.endswith(')'):
            # Extract the inner value
            inner = value[2:-1]
            if html:
                return f"<code style='background: #fef3c7; padding: 2px 4px; border-radius: 3px;'>{inner}</code>"
            else:
                return f"📌 {inner}"  # Use emoji to indicate special value in plain text
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, bool):
        return "✓" if value else "✗"
    if isinstance(value, list):
        return f"[{len(value)} items]"
    if isinstance(value, dict):
        return f"{{{len(value)} keys}}"
    return str(value)


# =============================================================================
# GRAPH VIEW
# =============================================================================

def _render_graph_view(
    concepts_data: Optional[List[Dict[str, Any]]],
    inferences_data: Optional[List[Dict[str, Any]]]
):
    """Render the graph visualization of concept dependencies."""
    if not concepts_data or not inferences_data:
        st.warning("Both concepts and inferences are required for graph view")
        return
    
    st.subheader("🔀 Dependency Graph")
    
    # Info about the graph
    with st.expander("ℹ️ Graph Legend", expanded=False):
        st.markdown("""
**Node Colors:**
- 🟣 **Purple** (ellipse): Semantic Functions (`::({})`, `<{}>`)
- 🔵 **Blue** (box): Semantic Values (`{}`, `<>`, `[]`)
- ⚫ **Gray** (box): Syntactic Functions

**Edge Types:**
- **Solid blue arrow**: Function relationship (`<=`)
- **Dashed purple arrow**: Value relationship (`<-`)

**Node Shapes:**
- 🔶 **Double circle**: Ground concepts (inputs)
- 🎯 **Bold border**: Final concepts (outputs)
        """)
    
    # Build and render the graph
    try:
        graph_source = _build_graphviz_source(concepts_data, inferences_data)
        st.graphviz_chart(graph_source, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering graph: {e}")
        st.info("💡 Make sure graphviz is installed: `pip install graphviz`")
        
        # Fallback: show text-based representation
        st.markdown("### Text-based Flow")
        _render_text_flow(inferences_data)


def _build_graphviz_source(
    concepts_data: List[Dict[str, Any]],
    inferences_data: List[Dict[str, Any]]
) -> str:
    """Build Graphviz DOT source for the dependency graph."""
    
    # Build concept lookup for attributes
    concept_attrs = {}
    for c in concepts_data:
        name = c.get('concept_name', '')
        concept_attrs[name] = {
            'is_ground': c.get('is_ground_concept', False),
            'is_final': c.get('is_final_concept', False),
            'is_invariant': c.get('is_invariant', False),
            'category': _get_concept_category(name)
        }
    
    # Start building DOT
    lines = [
        'digraph G {',
        '    rankdir=LR;',  # Left to right flow
        '    bgcolor="transparent";',
        '    node [fontname="Arial", fontsize=10];',
        '    edge [fontname="Arial", fontsize=8];',
        ''
    ]
    
    # Track all referenced concepts
    all_concepts = set()
    
    # Add edges from inferences
    for inf in inferences_data:
        target = inf.get('concept_to_infer', '')
        func = inf.get('function_concept', '')
        values = inf.get('value_concepts', [])
        seq = inf.get('inference_sequence', '')
        
        if target:
            all_concepts.add(target)
        if func:
            all_concepts.add(func)
            # Function edge (solid blue)
            lines.append(f'    "{_escape_dot(func)}" -> "{_escape_dot(target)}" '
                        f'[color="#4a90e2", penwidth=1.5, label="{seq}"];')
        
        for val in values:
            if val:
                all_concepts.add(val)
                # Value edge (dashed purple)
                lines.append(f'    "{_escape_dot(val)}" -> "{_escape_dot(target)}" '
                            f'[color="#7b68ee", style=dashed, penwidth=1.0];')
    
    lines.append('')
    
    # Add node styling
    for concept_name in all_concepts:
        attrs = concept_attrs.get(concept_name, {
            'is_ground': False,
            'is_final': False,
            'is_invariant': False,
            'category': _get_concept_category(concept_name)
        })
        
        node_style = _get_node_style(attrs)
        # Truncate label for display
        label = concept_name if len(concept_name) <= 25 else concept_name[:22] + "..."
        lines.append(f'    "{_escape_dot(concept_name)}" [{node_style}, label="{_escape_dot(label)}"];')
    
    lines.append('}')
    
    return '\n'.join(lines)


def _escape_dot(s: str) -> str:
    """Escape special characters for DOT format."""
    return s.replace('"', '\\"').replace('\n', '\\n')


def _get_node_style(attrs: Dict[str, Any]) -> str:
    """Get Graphviz node style based on concept attributes."""
    category = attrs.get('category', 'syntactic-function')
    is_ground = attrs.get('is_ground', False)
    is_final = attrs.get('is_final', False)
    
    # Base colors by category
    colors = {
        'semantic-function': ('#ede7f6', '#7b68ee'),  # fill, border
        'semantic-value': ('#dbeafe', '#3b82f6'),
        'syntactic-function': ('#f1f5f9', '#64748b'),
    }
    fill, border = colors.get(category, ('#ffffff', '#888888'))
    
    # Base shape by category
    if category == 'semantic-function':
        shape = 'ellipse'
    else:
        shape = 'box'
    
    # Modify for ground/final
    style_parts = ['filled']
    penwidth = '1.0'
    
    if is_ground:
        shape = 'doublecircle' if category == 'semantic-function' else 'doubleoctagon'
        penwidth = '2.0'
    
    if is_final:
        style_parts.append('bold')
        penwidth = '2.5'
        border = '#e11d48'  # Red border for final
    
    style = ','.join(style_parts)
    
    return f'shape={shape}, style="{style}", fillcolor="{fill}", color="{border}", penwidth={penwidth}'


def _render_text_flow(inferences_data: List[Dict[str, Any]]):
    """Render a text-based flow representation as fallback."""
    # Group by sequence
    by_sequence = {}
    for inf in inferences_data:
        seq = inf.get('inference_sequence', 'unknown')
        if seq not in by_sequence:
            by_sequence[seq] = []
        by_sequence[seq].append(inf)
    
    for seq in sorted(by_sequence.keys()):
        st.markdown(f"**Sequence: {seq}**")
        for inf in by_sequence[seq]:
            target = inf.get('concept_to_infer', '?')
            func = inf.get('function_concept', '?')
            values = inf.get('value_concepts', [])
            
            flow_text = f"  `{target}` ⬅️ `{func}`"
            if values:
                flow_text += f" 📥 ({', '.join(values[:3])}{'...' if len(values) > 3 else ''})"
            st.markdown(flow_text)
        st.markdown("---")
