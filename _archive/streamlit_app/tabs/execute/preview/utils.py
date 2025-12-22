"""
Utility functions for preview components.
Handles categorization, formatting, and tensor shape calculations.
"""

from typing import Any, Tuple


# =============================================================================
# CONCEPT CATEGORIZATION
# =============================================================================

def get_concept_category(concept_name: str) -> str:
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


def get_category_style(category: str) -> Tuple[str, str, str]:
    """Get (emoji, color_name, description) for a category."""
    styles = {
        'semantic-function': ('🟣', '#7b68ee', 'Semantic Function'),
        'semantic-value': ('🔵', '#3b82f6', 'Semantic Value'),
        'syntactic-function': ('⚫', '#64748b', 'Syntactic Function'),
    }
    return styles.get(category, ('⚪', '#888', 'Unknown'))


# =============================================================================
# TENSOR SHAPE UTILITIES
# =============================================================================

def get_tensor_shape(data: Any) -> Tuple[int, ...]:
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


def get_tensor_shape_str(data: Any) -> str:
    """Get a string representation of tensor shape."""
    shape = get_tensor_shape(data)
    if not shape:
        return "scalar"
    return "×".join(str(s) for s in shape)


def count_dimensions(data: Any) -> int:
    """Count the number of dimensions in nested list data."""
    return len(get_tensor_shape(data))


# =============================================================================
# VALUE FORMATTING
# =============================================================================

def format_cell_value(value: Any, html: bool = True) -> str:
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
# TENSOR SLICING
# =============================================================================

def slice_tensor(
    data: Any, 
    display_axes: list[int], 
    slice_indices: dict[int, int],
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
    
    # Recursively extract the slice
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


def get_slice_description(
    axes: list[str], 
    shape: Tuple[int, ...], 
    display_axes: list[int],
    slice_indices: dict[int, int]
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

