"""
UI components and styling for NormCode Orchestrator Streamlit App.
"""

import streamlit as st
from datetime import datetime


# Custom CSS for better styling
CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box { background-color: #d4edda; border: 1px solid #c3e6cb; }
    .error-box { background-color: #f8d7da; border: 1px solid #f5c6cb; }
    .info-box { background-color: #d1ecf1; border: 1px solid #bee5eb; }
    
    /* Compact log display */
    .stCodeBlock {
        font-size: 0.7rem !important;
        line-height: 1.25 !important;
    }
    .stCodeBlock code {
        font-size: 0.7rem !important;
        line-height: 1.25 !important;
        padding: 0.5rem !important;
    }
    .stCodeBlock pre {
        font-size: 0.7rem !important;
        line-height: 1.25 !important;
        margin: 0.25rem 0 !important;
        padding: 0.5rem !important;
    }
    /* Make log content more compact */
    div[data-testid="stVerticalBlock"] > div:has(code) {
        margin-bottom: 0.2rem !important;
    }
    /* Compact markdown in logs */
    .element-container:has(small) {
        margin-bottom: 0.25rem !important;
    }
    /* Reduce spacing around code blocks */
    .element-container:has(pre) {
        margin-top: 0 !important;
        margin-bottom: 0.25rem !important;
    }
</style>
"""


def apply_custom_styling():
    """Apply custom CSS styling to the app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_main_header():
    """Render the main app header."""
    st.markdown(
        '<h1 class="main-header">🧠 NormCode Orchestrator</h1>',
        unsafe_allow_html=True
    )


def render_footer():
    """Render the app footer."""
    st.divider()
    st.caption(
        "NormCode Orchestrator v1.3.1 | Powered by Streamlit | "
        "📋 Load complete setups (config + files + database)!"
    )


def display_execution_summary(run_data, duration=None):
    """
    Display execution summary metrics.
    
    Args:
        run_data: Dictionary with run information
        duration: Optional duration in seconds (if not in run_data)
    """
    st.subheader("📊 Execution Summary")
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        run_id = run_data.get('run_id', 'unknown')
        st.metric("Run ID", run_id[:8] + "..." if len(run_id) > 8 else run_id)
    
    with summary_col2:
        dur = duration if duration is not None else run_data.get('duration', 0)
        st.metric("Duration", f"{dur:.2f}s")
    
    with summary_col3:
        final_concepts = run_data.get('final_concepts', [])
        completed_concepts = sum(
            1 for fc in final_concepts
            if fc and fc.concept and fc.concept.reference
        )
        st.metric("Completed Concepts", f"{completed_concepts}/{len(final_concepts)}")


def display_log_entry(log, show_divider=True):
    """
    Display a single log entry with compact formatting.
    
    Args:
        log: Dictionary with log information (cycle, flow_index, status, log_content)
        show_divider: Whether to show a divider after the log
    """
    st.markdown(
        f"<small><b>Cycle {log['cycle']} | Flow {log['flow_index']} | "
        f"Status: {log['status']}</b></small>",
        unsafe_allow_html=True
    )
    st.code(log['log_content'], language="text")
    
    if show_divider:
        st.markdown(
            "<hr style='margin: 0.5rem 0; border: 0; border-top: 1px solid #ddd;'>",
            unsafe_allow_html=True
        )


def display_concept_preview(concepts_data):
    """
    Display a preview of concepts data.
    
    Args:
        concepts_data: List of concept dictionaries
    """
    st.subheader("📦 Concepts Preview")
    st.metric("Total Concepts", len(concepts_data))
    
    if concepts_data:
        with st.expander("View Sample Concept"):
            st.json(concepts_data[0], expanded=False)


def display_inference_preview(inferences_data):
    """
    Display a preview of inferences data.
    
    Args:
        inferences_data: List of inference dictionaries
    """
    st.subheader("🔗 Inferences Preview")
    st.metric("Total Inferences", len(inferences_data))
    
    if inferences_data:
        with st.expander("View Sample Inference"):
            st.json(inferences_data[0], expanded=False)


def display_inputs_preview(inputs_data):
    """
    Display a preview of inputs data.
    
    Args:
        inputs_data: Dictionary of input concepts
    """
    st.subheader("📥 Inputs Preview")
    st.write(f"**{len(inputs_data)} input concept(s) will be injected:**")
    for concept_name in inputs_data.keys():
        st.write(f"- `{concept_name}`")


def display_run_info_header(run_data):
    """
    Display run information header with metadata.
    
    Args:
        run_data: Dictionary with run information
    """
    st.subheader(f"🔖 Run: {run_data['run_id']}")
    
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    
    with info_col1:
        st.caption("⏰ Completed")
        timestamp = datetime.fromisoformat(run_data['timestamp'])
        st.write(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
    
    with info_col2:
        st.caption("⏱️ Duration")
        st.write(f"{run_data['duration']:.2f}s")
    
    with info_col3:
        st.caption("🤖 LLM Model")
        st.write(run_data['llm_model'])
    
    with info_col4:
        st.caption("🔄 Max Cycles")
        st.write(run_data['max_cycles'])
    
    # Show base directory if available
    if 'base_dir' in run_data:
        st.caption(f"📂 Base Directory: `{run_data['base_dir']}`")


def display_concept_result(concept_entry, filter_option="All Concepts"):
    """
    Display a single concept result based on filter option.
    
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
    
    # Display concept
    if has_reference:
        with st.expander(f"✅ {concept_entry.concept_name}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** `{concept_entry.type}`")
                st.write(f"**Axes:** `{concept_entry.concept.reference.axes}`")
                st.write(f"**Shape:** `{concept_entry.concept.reference.shape}`")
            
            with col2:
                st.write("**Tensor:**")
                st.code(str(concept_entry.concept.reference.tensor), language="python")
    else:
        with st.expander(f"⚠️ {concept_entry.concept_name} (no reference)", expanded=False):
            st.warning(f"This concept has type `{concept_entry.type}` but no reference data.")
    
    return True

