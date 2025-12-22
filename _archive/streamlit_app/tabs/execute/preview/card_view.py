"""
Card view components for preview.
Handles rendering of concepts, inferences, inputs, and concept repo references.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional, List

from .utils import get_concept_category, get_category_style
from .tensor_display import render_tensor_input


# =============================================================================
# MAIN CARD VIEW
# =============================================================================

def render_card_view(
    concepts_data: Optional[List[Dict[str, Any]]],
    inferences_data: Optional[List[Dict[str, Any]]],
    inputs_data: Optional[Dict[str, Any]]
):
    """Render the card-based preview with visual enhancements."""
    col1, col2 = st.columns(2)
    
    with col1:
        if concepts_data:
            render_concepts_preview(concepts_data)
        else:
            st.warning("No concepts data available")
    
    with col2:
        if inferences_data:
            render_inferences_preview(inferences_data)
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
                render_inputs_preview(inputs_data)
            else:
                st.info("No input data file provided")
        
        with ref_tabs[1]:
            if concept_refs:
                render_concept_repo_references(concept_refs)
            else:
                st.info("No concepts with pre-defined reference data in concept repo")


# =============================================================================
# CONCEPTS PREVIEW
# =============================================================================

def render_concepts_preview(concepts_data: List[Dict[str, Any]]):
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
        category = get_concept_category(concept.get('concept_name', ''))
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
                render_concept_card(concept)


def render_concept_card(concept: Dict[str, Any]):
    """Render a single concept as a mini card."""
    name = concept.get('concept_name', 'Unknown')
    category = get_concept_category(name)
    emoji, color, _ = get_category_style(category)
    
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


# =============================================================================
# INFERENCES PREVIEW
# =============================================================================

def render_inferences_preview(inferences_data: List[Dict[str, Any]]):
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
                render_inference_card(inference)


def render_inference_card(inference: Dict[str, Any]):
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


# =============================================================================
# INPUTS PREVIEW
# =============================================================================

def render_inputs_preview(inputs_data: Dict[str, Any]):
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
                        render_tensor_input(
                            item.get('concept_name', 'Unknown'),
                            item.get('reference_data', item.get('value', '')),
                            source="input",
                            editable=False
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
    
    # Edit mode toggle and metrics row
    col_toggle, col1, col2, col3 = st.columns([1.5, 1, 1, 1])
    
    with col_toggle:
        edit_mode = st.toggle("✏️ Edit Mode", key="input_edit_mode", help="Enable editing of input values")
    with col1:
        st.metric("Ground Concepts", len(concept_inputs))
    with col2:
        st.metric("Metadata Fields", len(metadata))
    with col3:
        # Count tensor inputs
        tensor_count = sum(1 for v in concept_inputs.values() 
                          if isinstance(v, dict) and 'data' in v and 'axes' in v)
        st.metric("Tensor Inputs", tensor_count)
    
    # Initialize edited inputs storage in session state
    if 'edited_inputs' not in st.session_state:
        st.session_state.edited_inputs = {}
    
    # Render metadata section (if any)
    if metadata:
        with st.expander("📝 Input File Metadata", expanded=False):
            render_metadata_section(metadata)
    
    # Render concept inputs
    if concept_inputs:
        with st.expander(f"🌱 Ground Concept References ({len(concept_inputs)} concepts)", expanded=True):
            for key, value in concept_inputs.items():
                render_tensor_input(key, value, source="input", editable=edit_mode)
    
    # Show apply button when in edit mode and changes exist
    if edit_mode and st.session_state.edited_inputs:
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📝 {len(st.session_state.edited_inputs)} concept(s) modified")
        with col2:
            if st.button("🔄 Reset Changes", use_container_width=True):
                st.session_state.edited_inputs = {}
                st.rerun()


def render_metadata_section(metadata: Dict[str, Any]):
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


# =============================================================================
# CONCEPT REPO REFERENCES
# =============================================================================

def render_concept_repo_references(concepts_with_refs: List[Dict[str, Any]]):
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
            
            render_tensor_input(name, value, source="repo", is_invariant=is_invariant, description=description)

