"""
Paradigms Tab - Main Entry Point

Provides a full-featured interface for viewing, creating, editing, and managing
composition paradigms.
"""

import streamlit as st
from typing import Optional
from .paradigm_loader import ParadigmLoader, ParadigmInfo
from .ui_components import (
    render_paradigm_card,
    render_paradigm_info_header,
    render_json_editor,
    render_structured_editor,
    render_step_visualizer,
    render_paradigm_actions,
    render_create_paradigm_form
)


def init_session_state():
    """Initialize session state for paradigms tab"""
    if 'paradigm_selected' not in st.session_state:
        st.session_state.paradigm_selected = None
    if 'paradigm_view_mode' not in st.session_state:
        st.session_state.paradigm_view_mode = 'list'  # 'list', 'view', 'create'
    if 'paradigm_search' not in st.session_state:
        st.session_state.paradigm_search = ''
    if 'paradigm_filter' not in st.session_state:
        st.session_state.paradigm_filter = 'all'


def render_paradigms_tab():
    """
    Main render function for the Paradigms tab.
    """
    init_session_state()
    
    # Create loader instance
    loader = ParadigmLoader()
    
    # Header
    st.title("🎨 Customize Paradigms")
    st.markdown("""
    Manage composition paradigms for the NormCode orchestration engine. 
    View built-in paradigms or create your own custom workflows.
    """)
    
    # Navigation based on view mode
    view_mode = st.session_state.paradigm_view_mode
    
    if view_mode == 'list':
        render_list_view(loader)
    elif view_mode == 'view':
        render_detail_view(loader)
    elif view_mode == 'create':
        render_create_view(loader)


def render_list_view(loader: ParadigmLoader):
    """
    Render the list view of all paradigms.
    
    Args:
        loader: ParadigmLoader instance
    """
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        
        # Filter by source
        filter_option = st.radio(
            "Show:",
            ["All", "Built-in Only", "Custom Only"],
            key="paradigm_filter_radio"
        )
        
        # Search
        search_query = st.text_input(
            "🔎 Search paradigms",
            value=st.session_state.paradigm_search,
            placeholder="Type to search...",
            key="paradigm_search_input"
        )
        st.session_state.paradigm_search = search_query
        
        # Create button
        st.markdown("---")
        if st.button("➕ Create New Paradigm", use_container_width=True, type="primary"):
            st.session_state.paradigm_view_mode = 'create'
            st.rerun()
    
    # Load paradigms based on filter
    include_builtin = filter_option in ["All", "Built-in Only"]
    include_custom = filter_option in ["All", "Custom Only"]
    paradigms = loader.list_paradigms(include_builtin=include_builtin, include_custom=include_custom)
    
    # Apply search filter
    if search_query:
        query_lower = search_query.lower()
        paradigms = [
            p for p in paradigms
            if query_lower in p.display_name.lower() or
               query_lower in p.inputs.lower() or
               query_lower in p.composition.lower() or
               query_lower in p.outputs.lower()
        ]
    
    # Display count
    st.markdown(f"### 📦 Paradigms ({len(paradigms)})")
    
    if not paradigms:
        st.info("No paradigms found matching your criteria.")
        return
    
    # Display paradigms in a grid-like layout
    for paradigm in paradigms:
        render_paradigm_card(
            paradigm,
            on_select=lambda p=paradigm: select_paradigm(p)
        )


def render_detail_view(loader: ParadigmLoader):
    """
    Render the detail view for a selected paradigm.
    
    Args:
        loader: ParadigmLoader instance
    """
    paradigm_info = st.session_state.paradigm_selected
    
    if not paradigm_info:
        st.warning("No paradigm selected")
        if st.button("← Back to List"):
            st.session_state.paradigm_view_mode = 'list'
            st.rerun()
        return
    
    # Load paradigm content
    try:
        content = loader.load_paradigm(paradigm_info)
    except Exception as e:
        st.error(f"Error loading paradigm: {str(e)}")
        if st.button("← Back to List"):
            st.session_state.paradigm_view_mode = 'list'
            st.rerun()
        return
    
    # Render info header
    render_paradigm_info_header(paradigm_info)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📝 JSON View", "🔧 Structured View", "📊 Flow Diagram"])
    
    edited_content = None
    
    with tab1:
        # JSON editor (read-only for built-in, editable for custom)
        edited_content = render_json_editor(
            content,
            key=f"json_edit_{paradigm_info.name}",
            read_only=paradigm_info.is_builtin
        )
    
    with tab2:
        # Structured view
        render_structured_editor(content, key=f"struct_view_{paradigm_info.name}")
    
    with tab3:
        # Flow visualization
        render_step_visualizer(content)
    
    # Actions
    action = render_paradigm_actions(
        paradigm_info,
        loader,
        content=edited_content if not paradigm_info.is_builtin else None
    )
    
    # Handle actions
    if action:
        handle_paradigm_action(action, paradigm_info, loader, edited_content)


def render_create_view(loader: ParadigmLoader):
    """
    Render the create view for a new paradigm.
    
    Args:
        loader: ParadigmLoader instance
    """
    # Back button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Back"):
            st.session_state.paradigm_view_mode = 'list'
            st.rerun()
    
    # Create form
    name, content, should_create = render_create_paradigm_form(loader)
    
    if should_create:
        # Validate
        is_valid, errors = loader.validate_paradigm(content)
        
        if not is_valid:
            st.error("Invalid paradigm structure:")
            for error in errors:
                st.error(f"  • {error}")
        else:
            # Save
            success, message = loader.save_paradigm(name, content, overwrite=False)
            
            if success:
                st.success(message)
                st.balloons()
                # Wait a moment then go back to list
                import time
                time.sleep(1)
                st.session_state.paradigm_view_mode = 'list'
                st.rerun()
            else:
                st.error(message)


def select_paradigm(paradigm_info: ParadigmInfo):
    """
    Select a paradigm for detailed view.
    
    Args:
        paradigm_info: ParadigmInfo object
    """
    st.session_state.paradigm_selected = paradigm_info
    st.session_state.paradigm_view_mode = 'view'
    st.rerun()


def handle_paradigm_action(action: str, paradigm_info: ParadigmInfo, loader: ParadigmLoader, content: Optional[dict] = None):
    """
    Handle paradigm actions (clone, save, delete, back).
    
    Args:
        action: Action to perform
        paradigm_info: ParadigmInfo object
        loader: ParadigmLoader instance
        content: Optional edited content
    """
    if action == 'back':
        st.session_state.paradigm_view_mode = 'list'
        st.session_state.paradigm_selected = None
        st.rerun()
    
    elif action == 'clone':
        # Show clone dialog
        with st.form(key=f"clone_form_{paradigm_info.name}"):
            st.markdown("### 🔄 Clone Paradigm")
            new_name = st.text_input(
                "New paradigm name:",
                value=f"{paradigm_info.display_name}_copy",
                help="Enter a name for the cloned paradigm"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Clone", type="primary", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit and new_name:
                success, message = loader.clone_paradigm(paradigm_info, new_name)
                if success:
                    st.success(message)
                    st.balloons()
                    import time
                    time.sleep(1)
                    st.session_state.paradigm_view_mode = 'list'
                    st.rerun()
                else:
                    st.error(message)
            elif cancel:
                st.rerun()
    
    elif action == 'save':
        if not content:
            st.error("No valid content to save")
            return
        
        # Validate before saving
        is_valid, errors = loader.validate_paradigm(content)
        
        if not is_valid:
            st.error("Cannot save invalid paradigm:")
            for error in errors:
                st.error(f"  • {error}")
        else:
            success, message = loader.save_paradigm(paradigm_info.name, content, overwrite=True)
            if success:
                st.success(message)
                st.balloons()
            else:
                st.error(message)
    
    elif action == 'delete':
        # Show confirmation dialog
        with st.form(key=f"delete_form_{paradigm_info.name}"):
            st.markdown("### 🗑️ Delete Paradigm")
            st.warning(f"Are you sure you want to delete **{paradigm_info.display_name}**? This action cannot be undone.")
            
            col1, col2 = st.columns(2)
            with col1:
                confirm = st.form_submit_button("⚠️ Delete", type="primary", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if confirm:
                success, message = loader.delete_paradigm(paradigm_info)
                if success:
                    st.success(message)
                    import time
                    time.sleep(1)
                    st.session_state.paradigm_view_mode = 'list'
                    st.session_state.paradigm_selected = None
                    st.rerun()
                else:
                    st.error(message)
            elif cancel:
                st.rerun()

