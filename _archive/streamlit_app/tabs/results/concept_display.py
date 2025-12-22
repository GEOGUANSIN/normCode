"""
Enhanced concept display for Results tab.
Reuses tensor display components from execute/preview.
"""

import streamlit as st
from typing import Any, Optional

# Import tensor display components from execute/preview
import sys
from pathlib import Path

# Add execute/preview to path for importing (in case of import issues)
preview_path = Path(__file__).parent.parent / 'execute' / 'preview'
if str(preview_path) not in sys.path:
    sys.path.insert(0, str(preview_path))

from ..execute.preview.tensor_display import render_tensor_display
from ..execute.preview.utils import (
    get_concept_category,
    get_category_style,
    get_tensor_shape_str
)


def display_concept_result_enhanced(concept_entry, filter_option="All Concepts"):
    """
    Display a single concept result with enhanced tensor visualization.
    
    Args:
        concept_entry: ConceptEntry object
        filter_option: Filter to apply ("All Concepts", "Only Completed", "Only Empty")
    
    Returns:
        True if displayed, False if filtered out
    """
    if not concept_entry:
        return False
    
    has_reference = concept_entry.concept and concept_entry.concept.reference
    
    # Apply filter
    if filter_option == "Only Completed" and not has_reference:
        return False
    elif filter_option == "Only Empty" and has_reference:
        return False
    
    # Get concept category and styling
    category = get_concept_category(concept_entry.concept_name)
    emoji, color, category_label = get_category_style(category)
    
    # Display concept
    if has_reference:
        # Concept with reference data
        reference = concept_entry.concept.reference
        shape_str = get_tensor_shape_str(reference.tensor)
        
        # Create expander with category emoji and status
        expander_label = f"✅ {emoji} {concept_entry.concept_name}"
        
        with st.expander(expander_label, expanded=False):
            # Header with metadata
            _render_concept_metadata(concept_entry, category_label, color, shape_str)
            
            st.divider()
            
            # Tensor visualization using execute/preview components
            _render_tensor_visualization(
                concept_entry.concept_name,
                reference.tensor,
                reference.axes,
                reference.shape
            )
    else:
        # Concept without reference data
        expander_label = f"⚠️ {emoji} {concept_entry.concept_name} (no reference)"
        
        with st.expander(expander_label, expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Category:** {category_label}")
                st.write(f"**Type:** `{concept_entry.type}`")
            
            with col2:
                st.warning("No reference data available")
    
    return True


def _render_concept_metadata(
    concept_entry,
    category_label: str,
    color: str,
    shape_str: str
):
    """Render metadata section for a concept with reference."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"<div style='background: {color}15; border-left: 3px solid {color}; "
            f"padding: 8px; border-radius: 4px;'>"
            f"<div style='font-size: 0.7em; color: #666; margin-bottom: 4px;'>CATEGORY</div>"
            f"<div style='font-weight: 600; color: {color};'>{category_label}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"<div style='background: #f8fafc; border-left: 3px solid #64748b; "
            f"padding: 8px; border-radius: 4px;'>"
            f"<div style='font-size: 0.7em; color: #666; margin-bottom: 4px;'>TYPE</div>"
            f"<div style='font-weight: 600; color: #334155;'>{concept_entry.type}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"<div style='background: #fef3c7; border-left: 3px solid #f59e0b; "
            f"padding: 8px; border-radius: 4px;'>"
            f"<div style='font-size: 0.7em; color: #666; margin-bottom: 4px;'>SHAPE</div>"
            f"<div style='font-weight: 600; color: #92400e;'>{shape_str}</div>"
            f"</div>",
            unsafe_allow_html=True
        )


def _render_tensor_visualization(
    concept_name: str,
    tensor_data: Any,
    axes: Optional[list],
    shape: Optional[tuple]
):
    """Render tensor data using the execute/preview tensor display components."""
    st.markdown("#### 📊 Tensor Data")
    
    # Use the tensor display from execute/preview
    # Note: editable=False for results view (read-only)
    render_tensor_display(
        concept_name=concept_name,
        data=tensor_data,
        axes=axes,
        source="repo",  # Mark as repo data (not input)
        is_invariant=False,
        description="",
        editable=False  # Results are read-only
    )
    
    # Additional metadata
    if axes and shape:
        st.caption(f"📐 Axes: {' × '.join(axes)}")
        st.caption(f"📏 Dimensions: {' × '.join(str(s) for s in shape)}")

