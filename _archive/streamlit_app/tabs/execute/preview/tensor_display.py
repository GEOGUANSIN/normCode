"""
Tensor display components for preview.
Handles rendering of scalar, 1D, 2D, and N-D tensors with editing support.
"""

import streamlit as st
import json
from typing import Any, Optional, List, Tuple

from .utils import (
    get_tensor_shape, 
    format_cell_value,
    slice_tensor,
    get_slice_description
)


# =============================================================================
# MAIN TENSOR DISPLAY
# =============================================================================

def render_tensor_input(
    key: str, 
    value: Any, 
    source: str = "input", 
    is_invariant: bool = False, 
    description: str = "", 
    editable: bool = False
):
    """
    Render a single input item with special handling for tensor data.
    
    Args:
        key: Concept name
        value: The reference value (tensor format: {"data": [[...]], "axes": ["axis1", "axis2"]})
        source: "input" for inputs.json, "repo" for concept repo
        is_invariant: Whether this is an invariant reference
        description: Optional description of the concept
        editable: Whether the value can be edited
    
    Tensor format: {"data": [[...]], "axes": ["axis1", "axis2"]}
    """
    # Check if this is a tensor with data and axes
    if isinstance(value, dict) and 'data' in value and 'axes' in value:
        render_tensor_display(
            key, value['data'], value['axes'], 
            source=source, is_invariant=is_invariant, 
            description=description, editable=editable
        )
    elif isinstance(value, dict) and 'data' in value:
        # Has data but no axes - treat as simple tensor
        render_tensor_display(
            key, value['data'], None, 
            source=source, is_invariant=is_invariant, 
            description=description, editable=editable
        )
    else:
        # Simple value - render as before
        render_simple_input(
            key, value, 
            source=source, is_invariant=is_invariant, 
            description=description, editable=editable
        )


def render_simple_input(
    key: str, 
    value: Any, 
    source: str = "input", 
    is_invariant: bool = False, 
    description: str = "", 
    editable: bool = False
):
    """Render a simple (non-tensor) input value, optionally editable."""
    # Choose color based on source
    border_color = "#22c55e" if source == "input" else "#6366f1"  # Green for input, Indigo for repo
    icon = "📥" if source == "input" else "📚"
    
    # Build badges
    badges = []
    if is_invariant:
        badges.append("<span style='background: #fef3c7; color: #92400e; padding: 1px 6px; border-radius: 3px; font-size: 0.7em;'>🔒 Invariant</span>")
    if editable:
        badges.append("<span style='background: #dbeafe; color: #1d4ed8; padding: 1px 6px; border-radius: 3px; font-size: 0.7em;'>✏️ Editable</span>")
    
    badge_html = " ".join(badges)
    
    # Description line
    desc_html = f"<div style='font-size: 0.75em; color: #888; font-style: italic;'>{description}</div>" if description else ""
    
    # Header
    st.markdown(
        f"<div style='border-left: 3px solid {border_color}; padding-left: 8px; margin-bottom: 8px; background: #fafafa; border-radius: 0 4px 4px 0; padding: 8px;'>"
        f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
        f"<span style='font-size: 0.9em;'>{icon} <code>{key}</code></span>"
        f"<span>{badge_html}</span>"
        f"</div>"
        f"{desc_html}"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Editable or display mode
    if editable and source == "input":  # Only allow editing input data, not repo data
        edit_key = f"edit_simple_{key.replace(' ', '_').replace('{', '').replace('}', '')}"
        
        # Get current value (edited or original)
        current_value = st.session_state.edited_inputs.get(key, value)
        
        if isinstance(value, (list, dict)):
            # JSON editor for complex values
            new_value = st.text_area(
                "Value (JSON)",
                value=json.dumps(current_value, ensure_ascii=False, indent=2),
                key=edit_key,
                height=100,
                label_visibility="collapsed"
            )
            try:
                parsed = json.loads(new_value)
                if parsed != value:
                    st.session_state.edited_inputs[key] = parsed
                elif key in st.session_state.edited_inputs:
                    del st.session_state.edited_inputs[key]
            except json.JSONDecodeError:
                st.error("Invalid JSON")
        else:
            # Simple text input
            new_value = st.text_input(
                "Value",
                value=str(current_value),
                key=edit_key,
                label_visibility="collapsed"
            )
            if new_value != str(value):
                st.session_state.edited_inputs[key] = new_value
            elif key in st.session_state.edited_inputs:
                del st.session_state.edited_inputs[key]
    else:
        # Display-only mode
        if isinstance(value, (list, dict)):
            preview = json.dumps(value, ensure_ascii=False)
            if len(preview) > 100:
                preview = preview[:97] + "..."
        else:
            preview = str(value)
            if len(preview) > 100:
                preview = preview[:97] + "..."
        
        st.markdown(
            f"<div style='font-size: 0.85em; color: #444; font-family: monospace; background: white; padding: 4px 8px; border-radius: 4px;'>{preview}</div>",
            unsafe_allow_html=True
        )


def render_tensor_display(
    concept_name: str, 
    data: Any, 
    axes: Optional[List[str]],
    source: str = "input",
    is_invariant: bool = False,
    description: str = "",
    editable: bool = False
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
        editable: Whether the tensor can be edited
    """
    # Calculate shape and dimensions
    shape = get_tensor_shape(data)
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
        badges_html += "<span style='font-size: 0.65em; background: #fef3c7; color: #92400e; padding: 2px 6px; border-radius: 3px; margin-right: 4px;'>🔒 Invariant</span>"
    if editable and source == "input":
        badges_html += "<span style='font-size: 0.65em; background: #dbeafe; color: #1d4ed8; padding: 2px 6px; border-radius: 3px;'>✏️ Editable</span>"
    
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
        
        # Check if we should use edit mode
        can_edit = editable and source == "input"
        
        # Display based on dimensions
        if dims == 0:
            # Scalar - editable as text input
            if can_edit:
                render_editable_scalar(concept_name, data, viewer_key)
            else:
                render_scalar_value(data)
        elif dims == 1:
            # 1D tensor - show as list
            if can_edit:
                render_editable_1d_tensor(concept_name, data, axes[0] if axes else "index", viewer_key)
            else:
                render_1d_tensor(data, axes[0] if axes else "index")
        elif dims == 2:
            # 2D tensor - show as editable table
            if can_edit:
                render_editable_2d_tensor(concept_name, data, axes, viewer_key)
            else:
                render_2d_tensor(data, axes)
        else:
            # Higher dimensional - show interactive slicer (editing not supported yet)
            if can_edit:
                st.caption("⚠️ Editing 3D+ tensors: Edit the JSON directly")
                render_editable_nd_tensor(concept_name, data, axes, viewer_key)
            else:
                render_interactive_tensor_viewer(data, axes, shape, viewer_key)


# =============================================================================
# DISPLAY-ONLY TENSOR RENDERERS
# =============================================================================

def render_scalar_value(data: Any):
    """Render a scalar (0D) value."""
    formatted = format_cell_value(data)
    st.markdown(
        f"<div style='background: white; border: 1px solid #d1d5db; border-radius: 6px; "
        f"padding: 16px; text-align: center; font-size: 1.2em;'>"
        f"<span style='color: #6b7280; font-size: 0.7em;'>Value:</span><br/>"
        f"<strong>{formatted}</strong>"
        f"</div>",
        unsafe_allow_html=True
    )


def render_1d_tensor(data: List[Any], axis_name: str):
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
                    f"<div style='font-weight: 500;'>{format_cell_value(item)}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
    else:
        # For longer lists, show as vertical list with scrolling
        items_html = "".join(
            f"<div style='display: flex; gap: 8px; padding: 4px 0; border-bottom: 1px solid #e5e7eb;'>"
            f"<span style='color: #9ca3af; min-width: 60px;'>[{i}]</span>"
            f"<span>{format_cell_value(item)}</span>"
            f"</div>"
            for i, item in enumerate(data)
        )
        st.markdown(
            f"<div style='max-height: 200px; overflow-y: auto; background: white; "
            f"border-radius: 4px; padding: 8px;'>{items_html}</div>",
            unsafe_allow_html=True
        )


def render_2d_tensor(data: List[List[Any]], axes: Optional[List[str]]):
    """Render a 2D tensor as a styled table."""
    render_2d_tensor_html(data, axes)


def render_2d_tensor_html(data: List[List[Any]], axes: Optional[List[str]]):
    """Render a 2D tensor as an HTML table."""
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
            formatted = format_cell_value(cell_value, html=True)
            table_html += f"<td style='padding: 8px; border: 1px solid #e2e8f0; text-align: center;'>{formatted}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"
    
    st.markdown(table_html, unsafe_allow_html=True)


# =============================================================================
# EDITABLE TENSOR RENDERERS
# =============================================================================

def render_editable_scalar(concept_name: str, data: Any, viewer_key: str):
    """Render an editable scalar value."""
    edit_key = f"{viewer_key}_scalar"
    
    # Get current value (edited or original)
    current_value = st.session_state.edited_inputs.get(concept_name, data)
    
    # Determine if it's a special value like %(...)
    if isinstance(current_value, str) and current_value.startswith('%(') and current_value.endswith(')'):
        inner = current_value[2:-1]
        st.caption("📌 Value wrapped in %() syntax")
        new_inner = st.text_input("Value", value=inner, key=edit_key, label_visibility="collapsed")
        new_value = f"%({new_inner})"
    else:
        new_value = st.text_input("Value", value=str(current_value), key=edit_key, label_visibility="collapsed")
    
    # Store if changed
    if new_value != str(data) and new_value != data:
        st.session_state.edited_inputs[concept_name] = new_value
    elif concept_name in st.session_state.edited_inputs and new_value == str(data):
        del st.session_state.edited_inputs[concept_name]


def render_editable_1d_tensor(concept_name: str, data: List[Any], axis_name: str, viewer_key: str):
    """Render an editable 1D tensor."""
    # Get current data (edited or original)
    current_data = st.session_state.edited_inputs.get(concept_name, {}).get('data', data)
    if isinstance(current_data, dict):
        current_data = current_data.get('data', data)
    
    st.caption(f"📝 Edit values for {axis_name}")
    
    # Create columns for each value
    num_items = len(current_data)
    edited_values = []
    
    if num_items <= 6:
        cols = st.columns(num_items)
        for i, (col, item) in enumerate(zip(cols, current_data)):
            with col:
                # Handle %(value) syntax
                if isinstance(item, str) and item.startswith('%(') and item.endswith(')'):
                    inner = item[2:-1]
                    new_val = st.text_input(f"{axis_name}[{i}]", value=inner, key=f"{viewer_key}_1d_{i}")
                    edited_values.append(f"%({new_val})")
                else:
                    new_val = st.text_input(f"{axis_name}[{i}]", value=str(item), key=f"{viewer_key}_1d_{i}")
                    edited_values.append(new_val)
    else:
        # For longer lists, use two columns
        for i in range(0, num_items, 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < num_items:
                    item = current_data[idx]
                    with col:
                        if isinstance(item, str) and item.startswith('%(') and item.endswith(')'):
                            inner = item[2:-1]
                            new_val = st.text_input(f"{axis_name}[{idx}]", value=inner, key=f"{viewer_key}_1d_{idx}")
                            edited_values.append(f"%({new_val})")
                        else:
                            new_val = st.text_input(f"{axis_name}[{idx}]", value=str(item), key=f"{viewer_key}_1d_{idx}")
                            edited_values.append(new_val)
    
    # Check if values changed
    if edited_values != data:
        # Store the edited tensor
        original_input = st.session_state.loaded_repo_files.get('inputs', {})
        if isinstance(original_input, dict) and 'content' in original_input:
            try:
                orig_data = json.loads(original_input['content'])
                if concept_name in orig_data:
                    orig_tensor = orig_data[concept_name]
                    if isinstance(orig_tensor, dict):
                        st.session_state.edited_inputs[concept_name] = {
                            'data': [edited_values],
                            'axes': orig_tensor.get('axes', [axis_name])
                        }
            except:
                st.session_state.edited_inputs[concept_name] = {'data': [edited_values], 'axes': [axis_name]}
        else:
            st.session_state.edited_inputs[concept_name] = {'data': [edited_values], 'axes': [axis_name]}


def render_editable_2d_tensor(concept_name: str, data: List[List[Any]], axes: Optional[List[str]], viewer_key: str):
    """Render an editable 2D tensor using text inputs in a grid."""
    row_axis = axes[0] if axes and len(axes) > 0 else "row"
    col_axis = axes[1] if axes and len(axes) > 1 else "col"
    
    # Get current data
    current_data = st.session_state.edited_inputs.get(concept_name, {}).get('data', data)
    if not isinstance(current_data, list):
        current_data = data
    
    st.caption(f"📝 Edit tensor values ({row_axis} × {col_axis})")
    
    max_cols = max(len(row) for row in current_data) if current_data else 0
    num_rows = len(current_data)
    
    # Create editable grid using columns
    edited_tensor = []
    
    for i in range(num_rows):
        row = current_data[i] if i < len(current_data) else []
        
        # Create row header + value columns
        cols = st.columns([1] + [2] * max_cols)
        
        # Row header
        with cols[0]:
            st.markdown(
                f"<div style='padding: 8px; background: #f1f5f9; border-radius: 4px; text-align: center; font-size: 0.8em; color: #64748b;'>{row_axis}[{i}]</div>",
                unsafe_allow_html=True
            )
        
        edited_row = []
        for j in range(max_cols):
            with cols[j + 1]:
                # Get cell value
                cell = row[j] if j < len(row) else ""
                
                # Handle %(value) syntax
                if isinstance(cell, str) and cell.startswith('%(') and cell.endswith(')'):
                    inner = cell[2:-1]
                    new_val = st.text_input(
                        f"{col_axis}[{j}]",
                        value=inner,
                        key=f"{viewer_key}_2d_{i}_{j}",
                        label_visibility="collapsed"
                    )
                    edited_row.append(f"%({new_val})")
                else:
                    new_val = st.text_input(
                        f"{col_axis}[{j}]",
                        value=str(cell) if cell is not None else "",
                        key=f"{viewer_key}_2d_{i}_{j}",
                        label_visibility="collapsed"
                    )
                    edited_row.append(new_val)
        
        edited_tensor.append(edited_row)
    
    # Column headers (show after first row to indicate column names)
    if num_rows > 0:
        header_cols = st.columns([1] + [2] * max_cols)
        with header_cols[0]:
            st.caption("")
        for j in range(max_cols):
            with header_cols[j + 1]:
                st.caption(f"{col_axis}[{j}]")
    
    # Store if changed
    if edited_tensor != data:
        st.session_state.edited_inputs[concept_name] = {
            'data': edited_tensor,
            'axes': axes or [row_axis, col_axis]
        }
    elif concept_name in st.session_state.edited_inputs:
        del st.session_state.edited_inputs[concept_name]


def render_editable_nd_tensor(concept_name: str, data: Any, axes: List[str], viewer_key: str):
    """Render an editable higher-dimensional tensor as JSON."""
    # Get current data
    current_data = st.session_state.edited_inputs.get(concept_name, {}).get('data', data)
    
    st.caption("📝 Edit tensor as JSON")
    
    json_str = json.dumps(current_data, ensure_ascii=False, indent=2)
    
    edited_json = st.text_area(
        "Tensor Data (JSON)",
        value=json_str,
        height=200,
        key=f"{viewer_key}_nd_json",
        label_visibility="collapsed"
    )
    
    try:
        parsed = json.loads(edited_json)
        if parsed != data:
            st.session_state.edited_inputs[concept_name] = {
                'data': parsed,
                'axes': axes
            }
        elif concept_name in st.session_state.edited_inputs:
            del st.session_state.edited_inputs[concept_name]
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {e}")


# =============================================================================
# INTERACTIVE N-D TENSOR VIEWER
# =============================================================================

def render_interactive_tensor_viewer(
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
        # Filter out axes with only 1 element (no slider needed, always index 0)
        sliceable_axes = [ax for ax in slice_axes if shape[ax] > 1]
        fixed_axes = [ax for ax in slice_axes if shape[ax] <= 1]
        
        # Set fixed axes to index 0
        slice_indices = {ax: 0 for ax in fixed_axes}
        
        if sliceable_axes:
            st.markdown("**🔢 Slice Indices** (for non-displayed axes)")
            
            # Create columns for slice selectors
            num_slicers = len(sliceable_axes)
            cols = st.columns(min(num_slicers, 4))
            
            for idx, axis_idx in enumerate(sliceable_axes):
                with cols[idx % 4]:
                    axis_name = axes[axis_idx]
                    axis_size = shape[axis_idx]
                    
                    current_idx = viewer_state['slice_indices'].get(axis_idx, 0)
                    current_idx = min(current_idx, max(0, axis_size - 1))  # Ensure valid
                    
                    selected_idx = st.slider(
                        f"{axis_name}",
                        min_value=0,
                        max_value=axis_size - 1,
                        value=current_idx,
                        key=f"{viewer_key}_slice_{axis_idx}",
                        help=f"Select index for {axis_name} axis (0 to {axis_size - 1})"
                    )
                    slice_indices[axis_idx] = selected_idx
        elif fixed_axes:
            # Show a note about fixed axes
            fixed_names = ", ".join(f"{axes[ax]}[0]" for ax in fixed_axes)
            st.caption(f"📌 Fixed indices (single-element axes): {fixed_names}")
        
        viewer_state['slice_indices'].update(slice_indices)
    
    # === SLICE THE DATA ===
    sliced_data = slice_tensor(data, display_axes, viewer_state['slice_indices'], dims)
    
    # === DISPLAY THE SLICE ===
    st.markdown("---")
    
    # Show what slice we're viewing
    slice_desc = get_slice_description(axes, shape, display_axes, viewer_state['slice_indices'])
    st.caption(f"📍 Viewing: {slice_desc}")
    
    if view_mode == "JSON":
        st.json(sliced_data)
    elif view_mode == "List" or len(display_axes) == 1:
        if isinstance(sliced_data, list):
            render_1d_tensor(sliced_data, axes[display_axes[0]])
        else:
            render_scalar_value(sliced_data)
    else:  # Table view
        if isinstance(sliced_data, list) and len(sliced_data) > 0 and isinstance(sliced_data[0], list):
            display_axes_names = [axes[i] for i in display_axes]
            render_2d_tensor(sliced_data, display_axes_names)
        elif isinstance(sliced_data, list):
            render_1d_tensor(sliced_data, axes[display_axes[0]])
        else:
            render_scalar_value(sliced_data)

