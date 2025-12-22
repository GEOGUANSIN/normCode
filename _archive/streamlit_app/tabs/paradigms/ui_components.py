"""
UI components for the Paradigms tab.
Reusable components for displaying and editing paradigms.
"""

import streamlit as st
import json
from typing import Dict, Any, Optional
from .paradigm_loader import ParadigmInfo


def render_paradigm_card(paradigm_info: ParadigmInfo, on_select=None):
    """
    Render a card for a single paradigm.
    
    Args:
        paradigm_info: ParadigmInfo object
        on_select: Callback function when card is clicked
    """
    # Determine card styling based on source
    border_color = "#4CAF50" if not paradigm_info.is_builtin else "#2196F3"
    
    # Create a container for the card
    with st.container():
        # Use custom CSS for card styling
        st.markdown(f"""
        <div style="
            border: 2px solid {border_color};
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            background-color: rgba(255, 255, 255, 0.05);
            cursor: pointer;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h4 style="margin: 0; color: {border_color};">📦 {paradigm_info.display_name}</h4>
                <span style="
                    background-color: {border_color};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.85em;
                    font-weight: bold;
                ">{paradigm_info.source_label}</span>
            </div>
            <div style="font-size: 0.9em; color: #888; margin-top: 8px;">
                <strong>Inputs:</strong> {paradigm_info.inputs}<br>
                <strong>Process:</strong> {paradigm_info.composition}<br>
                <strong>Outputs:</strong> {paradigm_info.outputs}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Button to select this paradigm
        if st.button(
            "View/Edit" if not paradigm_info.is_builtin else "View",
            key=f"select_{paradigm_info.name}",
            use_container_width=True
        ):
            if on_select:
                on_select(paradigm_info)


def render_json_editor(content: Dict[str, Any], key: str = "json_editor", read_only: bool = False) -> Optional[Dict[str, Any]]:
    """
    Render a JSON editor with syntax highlighting.
    
    Args:
        content: JSON content to edit
        key: Unique key for the editor
        read_only: Whether the editor is read-only
        
    Returns:
        Updated JSON content if edited, None if read-only or invalid
    """
    st.markdown("#### JSON Editor")
    
    # Convert to pretty JSON string
    json_str = json.dumps(content, indent=2, ensure_ascii=False)
    
    if read_only:
        st.code(json_str, language="json")
        return None
    else:
        # Editable text area with JSON
        edited_str = st.text_area(
            "Edit JSON (be careful with syntax)",
            value=json_str,
            height=400,
            key=key,
            help="Edit the paradigm JSON structure. Make sure to maintain valid JSON syntax."
        )
        
        # Try to parse the edited JSON
        try:
            edited_content = json.loads(edited_str)
            st.success("✅ Valid JSON")
            return edited_content
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {str(e)}")
            return None


def render_structured_editor(content: Dict[str, Any], key: str = "struct_editor") -> Dict[str, Any]:
    """
    Render a structured form editor for paradigm components.
    
    Args:
        content: Paradigm content
        key: Unique key for the editor
        
    Returns:
        Updated paradigm content
    """
    st.markdown("#### Structured Editor")
    
    # Create tabs for different sections
    tab1, tab2 = st.tabs(["🔧 Environment Spec", "📋 Sequence Spec"])
    
    with tab1:
        st.markdown("##### Tools Configuration")
        env_spec = content.get('env_spec', {})
        tools = env_spec.get('tools', [])
        
        st.info(f"📊 {len(tools)} tool(s) configured")
        
        # Display tools in an expandable format
        for i, tool in enumerate(tools):
            with st.expander(f"Tool {i+1}: {tool.get('tool_name', 'Unnamed')}", expanded=False):
                st.code(json.dumps(tool, indent=2), language="json")
    
    with tab2:
        st.markdown("##### Execution Steps")
        seq_spec = content.get('sequence_spec', {})
        steps = seq_spec.get('steps', [])
        
        st.info(f"📊 {len(steps)} step(s) configured")
        
        # Display steps with visual indicators
        for i, step in enumerate(steps):
            with st.expander(
                f"Step {step.get('step_index', i+1)}: {step.get('affordance', 'Unknown')}",
                expanded=False
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Affordance:** `{step.get('affordance', 'N/A')}`")
                    st.markdown(f"**Result Key:** `{step.get('result_key', 'N/A')}`")
                with col2:
                    st.markdown("**Parameters:**")
                    st.code(json.dumps(step.get('params', {}), indent=2), language="json")
    
    return content


def render_paradigm_info_header(paradigm_info: ParadigmInfo):
    """
    Render info header for a paradigm.
    
    Args:
        paradigm_info: ParadigmInfo object
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"### 📦 {paradigm_info.display_name}")
        st.caption(f"Source: **{paradigm_info.source_label}** | File: `{paradigm_info.name}`")
    
    with col2:
        if paradigm_info.is_builtin:
            st.info("🔒 Read-Only")
        else:
            st.success("✏️ Editable")
    
    # Display parsed components
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📥 Inputs**")
        st.info(paradigm_info.inputs)
    
    with col2:
        st.markdown("**⚙️ Process**")
        st.info(paradigm_info.composition)
    
    with col3:
        st.markdown("**📤 Outputs**")
        st.info(paradigm_info.outputs)
    
    st.markdown("---")


def render_step_visualizer(content: Dict[str, Any]):
    """
    Render a visual flowchart of paradigm steps.
    
    Args:
        content: Paradigm content
    """
    st.markdown("#### 📊 Step Flow Visualization")
    
    seq_spec = content.get('sequence_spec', {})
    steps = seq_spec.get('steps', [])
    
    if not steps:
        st.warning("No steps defined in this paradigm")
        return
    
    # Create a simple visual flow
    st.markdown("```")
    st.markdown("Execution Flow:")
    st.markdown("=" * 60)
    
    for i, step in enumerate(steps):
        step_idx = step.get('step_index', i + 1)
        affordance = step.get('affordance', 'Unknown')
        result_key = step.get('result_key', 'N/A')
        
        # Draw connection
        if i > 0:
            st.markdown("    ⬇️")
        
        # Draw step box
        st.markdown(f"[Step {step_idx}] {affordance}")
        st.markdown(f"    └─> Result: {result_key}")
    
    st.markdown("=" * 60)
    st.markdown("```")


def render_paradigm_actions(paradigm_info: ParadigmInfo, loader, content: Optional[Dict[str, Any]] = None):
    """
    Render action buttons for paradigm operations.
    
    Args:
        paradigm_info: ParadigmInfo object
        loader: ParadigmLoader instance
        content: Optional edited content for save operation
        
    Returns:
        Action performed (if any)
    """
    st.markdown("---")
    st.markdown("### 🎯 Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    action = None
    
    with col1:
        if st.button("🔄 Clone", use_container_width=True, key=f"clone_{paradigm_info.name}"):
            action = "clone"
    
    with col2:
        if not paradigm_info.is_builtin and content:
            if st.button("💾 Save", use_container_width=True, key=f"save_{paradigm_info.name}"):
                action = "save"
    
    with col3:
        if not paradigm_info.is_builtin:
            if st.button("🗑️ Delete", use_container_width=True, key=f"delete_{paradigm_info.name}"):
                action = "delete"
    
    with col4:
        if st.button("🔙 Back", use_container_width=True, key=f"back_{paradigm_info.name}"):
            action = "back"
    
    return action


def render_create_paradigm_form(loader):
    """
    Render form for creating a new paradigm.
    
    Args:
        loader: ParadigmLoader instance
        
    Returns:
        Tuple of (name, content, should_create)
    """
    st.markdown("### ➕ Create New Paradigm")
    
    # Name input
    name = st.text_input(
        "Paradigm Name",
        placeholder="h_YourInput-c_YourProcess-o_YourOutput",
        help="Follow the naming convention: [inputs]-[composition]-[outputs].json"
    )
    
    # Template selection
    template_option = st.radio(
        "Start from:",
        ["Blank Template", "Clone Existing"],
        horizontal=True
    )
    
    content = None
    
    if template_option == "Blank Template":
        content = loader.create_blank_paradigm()
        st.info("📝 Starting with a blank paradigm template")
    else:
        # List paradigms for cloning
        paradigms = loader.list_paradigms()
        if paradigms:
            selected_paradigm = st.selectbox(
                "Select paradigm to clone:",
                options=paradigms,
                format_func=lambda p: f"{p.display_name} ({p.source_label})"
            )
            if selected_paradigm:
                content = loader.load_paradigm(selected_paradigm)
                st.success(f"📋 Cloning from: {selected_paradigm.display_name}")
        else:
            st.warning("No paradigms available to clone")
            content = loader.create_blank_paradigm()
    
    # JSON editor
    if content:
        edited_content = render_json_editor(content, key="create_editor", read_only=False)
        
        # Create button
        col1, col2 = st.columns([1, 3])
        with col1:
            create_clicked = st.button("✨ Create Paradigm", use_container_width=True, type="primary")
        
        if create_clicked and edited_content and name:
            return (name, edited_content, True)
    
    return (None, None, False)

