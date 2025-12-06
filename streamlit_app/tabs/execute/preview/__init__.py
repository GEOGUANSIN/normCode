"""
Preview module for Execute tab.
Provides card and graph views of concepts, inferences, and inputs.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional

from core.file_utils import get_file_content

from .card_view import render_card_view
from .graph_view import render_graph_view


# =============================================================================
# PUBLIC API
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
        render_card_view(concepts_data, inferences_data, inputs_data)
    else:
        render_graph_view(concepts_data, inferences_data)


# Export main function
__all__ = ['render_file_previews']

