"""
NormCode Files Editor Tab

Provides UI for editing .ncd, .nc, and .ncn files with:
- Line-by-line structured editing
- Bidirectional sync between formats
- Version control

Supports both structured mode (per-line editing) and text mode (bulk editing).
"""

import streamlit as st
from pathlib import Path
import os
import sys

# Import core functionality
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.manifest import ManifestManager
from core.version_control import VersionControl
from core.syntax_highlighter import SyntaxHighlighter
from core.converters import FormatConverter
from core.line_editor import LineManager, EditableLine, LineType

# Import structured editor component
from .structured_editor import (
    init_structured_editor_state,
    load_content,
    get_content,
    render_structured_editor,
    render_quick_actions_panel,
    COLORS
)


def render_normcode_editor_tab():
    """Render the NormCode files editor tab."""
    st.header("📝 NormCode Files Editor")
    st.markdown("""
    Edit `.ncd`, `.nc`, and `.ncn` files with **line-by-line structured editing**.
    
    Each line is independently editable with controls for indentation, operators, and metadata.
    """)
    
    # Initialize session state
    _init_session_state()
    
    # Initialize managers
    manifest_mgr = ManifestManager()
    version_ctrl = VersionControl()
    
    # Project Management Section
    _render_project_management(manifest_mgr)
    
    # Only show editor if a manifest is loaded
    if not st.session_state.nc_editor_manifest:
        st.info("👆 Load or create a project to get started")
        return
    
    manifest = st.session_state.nc_editor_manifest
    
    # Display current project info
    st.divider()
    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        st.markdown(f"### 📂 {manifest['project_name']}")
        if manifest['metadata'].get('description'):
            st.caption(manifest['metadata']['description'])
    with col_info2:
        if st.button("💾 Save All", key='nc_save_all'):
            _save_all_files(manifest, version_ctrl)
    
    # Unified Editor - single source that can be exported to any format
    st.divider()
    
    # Main unified editor using 'draft' as the canonical format
    _render_unified_editor(manifest, version_ctrl)
    
    # Export panel for saving to specific formats
    st.divider()
    _render_export_panel(manifest, version_ctrl)


def _init_session_state():
    """Initialize session state for the editor."""
    if 'nc_editor_manifest' not in st.session_state:
        st.session_state.nc_editor_manifest = None
    if 'nc_editor_modified' not in st.session_state:
        st.session_state.nc_editor_modified = False
    if 'nc_sync_preview' not in st.session_state:
        st.session_state.nc_sync_preview = None
    if 'nc_show_create_form' not in st.session_state:
        st.session_state.nc_show_create_form = False
    
    # Initialize single unified structured editor (using 'draft' as the canonical key)
    # This single editor can display all three formats via per-line format toggles
    init_structured_editor_state('draft')


def _render_project_management(manifest_mgr: ManifestManager):
    """Render project management section."""
    st.subheader("Project Management")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        available_manifests = manifest_mgr.list_manifests()
        
        if available_manifests:
            selected_manifest = st.selectbox(
                "Load Existing Project",
                options=[''] + available_manifests,
                key='nc_manifest_selector'
            )
            
            if selected_manifest and st.button("Load Project"):
                manifest = manifest_mgr.load(selected_manifest)
                if manifest:
                    st.session_state.nc_editor_manifest = manifest
                    # Load file contents into structured editors
                    _load_manifest_files_structured(manifest)
                    st.success(f"Loaded project: {selected_manifest}")
                    st.rerun()
        else:
            st.info("No projects found. Create a new one below.")
    
    with col2:
        if st.button("➕ Create New"):
            st.session_state.nc_show_create_form = True
    
    with col3:
        if st.session_state.nc_editor_manifest and st.button("💾 Save Manifest"):
            manifest_mgr.save(st.session_state.nc_editor_manifest)
            st.success("Manifest saved!")
    
    # Create new project form
    if st.session_state.nc_show_create_form:
        _render_create_project_form(manifest_mgr)


def _render_create_project_form(manifest_mgr: ManifestManager):
    """Render the create new project form."""
    with st.expander("Create New Project", expanded=True):
        project_name = st.text_input("Project Name", key='nc_new_project_name')
        description = st.text_area("Description (optional)", key='nc_new_project_desc')
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Create"):
                if project_name:
                    manifest = manifest_mgr.create(
                        project_name=project_name,
                        draft_path=f"examples/{project_name}.ncd",
                        formal_path=f"examples/{project_name}.nc",
                        natural_path=f"examples/{project_name}.ncn",
                        description=description
                    )
                    st.session_state.nc_editor_manifest = manifest
                    st.session_state.nc_show_create_form = False
                    
                    # Initialize empty single editor
                    load_content('draft', "")
                    
                    st.success(f"Created project: {project_name}")
                    st.rerun()
        with col_b:
            if st.button("Cancel"):
                st.session_state.nc_show_create_form = False
                st.rerun()


def _render_unified_editor(manifest: dict, version_ctrl: VersionControl):
    """Render the unified structured editor with per-line format toggles."""
    
    # Use 'draft' as the canonical internal representation (single source of truth)
    file_type = 'draft'
    key_prefix = f'struct_editor_{file_type}'
    
    st.subheader("📝 Unified NormCode Editor")
    st.caption("Single data model, multiple views. Toggle format per-line to see .ncd/.nc/.ncn representations.")
    
    # Quick actions panel
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        render_quick_actions_panel(file_type, key_prefix, manager)
    
    # Main editor with per-line format toggles
    def on_content_change():
        st.session_state.nc_editor_modified = True
    
    render_structured_editor(
        file_type=file_type,
        on_change=on_content_change
    )
    
    # Bottom actions
    st.divider()
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button("📜 Version History", key='nc_history_unified'):
            st.session_state['nc_show_history_unified'] = True
    
    with col_act2:
        if st.button("📥 Import from File", key='nc_import_unified'):
            st.session_state['nc_show_import'] = True
    
    with col_act3:
        if manager and manager.has_modifications():
            st.markdown("⚠️ **Unsaved changes**")
    
    # Version history modal
    if st.session_state.get('nc_show_history_unified', False):
        _render_version_history(file_type, manifest['files'][file_type], version_ctrl)
    
    # Import modal
    if st.session_state.get('nc_show_import', False):
        _render_import_panel(manifest)


def _render_export_panel(manifest: dict, version_ctrl: VersionControl):
    """Render panel for exporting to specific formats."""
    st.subheader("💾 Export to Files")
    st.caption("Save the same data structure to all three file formats (.ncd, .nc, .ncn)")
    
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 1])
    
    key_prefix = 'struct_editor_draft'
    manager = st.session_state.get(f'{key_prefix}_manager')
    
    with col1:
        if st.button("📄 Save as .ncd", key='export_ncd', use_container_width=True):
            content = get_content('draft', 'draft')
            file_path = manifest['files']['draft']
            _save_to_file(file_path, content, version_ctrl)
            st.success(f"Saved: {file_path}")
    
    with col2:
        if st.button("📋 Save as .nc", key='export_nc', use_container_width=True):
            content = get_content('draft', 'formal')
            file_path = manifest['files']['formal']
            _save_to_file(file_path, content, version_ctrl)
            st.success(f"Saved: {file_path}")
    
    with col3:
        if st.button("📖 Save as .ncn", key='export_ncn', use_container_width=True):
            content = get_content('draft', 'natural')
            file_path = manifest['files']['natural']
            _save_to_file(file_path, content, version_ctrl)
            st.success(f"Saved: {file_path}")
    
    with col4:
        if st.button("💾 Save All 3", key='export_all', use_container_width=True):
            # Save the same data to all three format files (synchronized by flow_index)
            _save_to_file(manifest['files']['draft'], get_content('draft', 'draft'), version_ctrl)
            _save_to_file(manifest['files']['formal'], get_content('draft', 'formal'), version_ctrl)
            _save_to_file(manifest['files']['natural'], get_content('draft', 'natural'), version_ctrl)
            st.success("✓ Saved all 3 formats!")
            st.session_state.nc_editor_modified = False


def _render_import_panel(manifest: dict):
    """Render import options."""
    with st.expander("📥 Import Content", expanded=True):
        import_source = st.selectbox(
            "Import from:",
            options=['Select...', 'Draft (.ncd)', 'Formal (.nc)', 'Natural (.ncn)'],
            key='import_source'
        )
        
        if import_source != 'Select...':
            file_map = {
                'Draft (.ncd)': manifest['files']['draft'],
                'Formal (.nc)': manifest['files']['formal'],
                'Natural (.ncn)': manifest['files']['natural']
            }
            file_path = file_map[import_source]
            
            if os.path.exists(file_path):
                if st.button(f"Load from {file_path}"):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    load_content('draft', content)
                    st.session_state['nc_show_import'] = False
                    st.success(f"Imported from {file_path}")
                    st.rerun()
            else:
                st.warning(f"File not found: {file_path}")
        
        if st.button("Cancel", key='import_cancel'):
            st.session_state['nc_show_import'] = False
            st.rerun()


def _save_to_file(file_path: str, content: str, version_ctrl: VersionControl):
    """Save content to file and create version snapshot."""
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    version_ctrl.save_snapshot(file_path, content, 'Manual save')


def _render_structured_file_editor(
    file_type: str, 
    extension: str, 
    manifest: dict, 
    version_ctrl: VersionControl
):
    """Render the structured editor for a specific file type (legacy, kept for compatibility)."""
    file_path = manifest['files'][file_type]
    key_prefix = f'struct_editor_{file_type}'
    
    # File info header
    col_info1, col_info2, col_info3 = st.columns([3, 1, 1])
    with col_info1:
        st.caption(f"📁 {file_path}")
    with col_info2:
        manager: LineManager = st.session_state.get(f'{key_prefix}_manager')
        if manager and manager.has_modifications():
            st.caption("⚠️ Modified")
    with col_info3:
        # Quick save button
        if st.button("💾", key=f'nc_quick_save_{file_type}', help="Save this file"):
            _save_single_file(file_type, file_path, version_ctrl)
    
    # Quick actions panel
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        render_quick_actions_panel(file_type, key_prefix, manager)
    
    # Main editor
    def on_content_change():
        st.session_state.nc_editor_modified[file_type] = True
    
    render_structured_editor(
        file_type=file_type,
        on_change=on_content_change
    )
    
    # Bottom actions
    st.divider()
    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
    
    with col_act1:
        if st.button("💾 Save", key=f'nc_save_{file_type}'):
            _save_single_file(file_type, file_path, version_ctrl)
            st.success(f"Saved {extension} file")
    
    with col_act2:
        if st.button("📜 History", key=f'nc_history_{file_type}'):
            st.session_state[f'nc_show_history_{file_type}'] = True
    
    with col_act3:
        if st.button("📥 Load File", key=f'nc_load_{file_type}'):
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                load_content(file_type, content)
                st.success(f"Loaded from {file_path}")
                st.rerun()
            else:
                st.warning(f"File not found: {file_path}")
    
    with col_act4:
        if st.button("🎨 Preview", key=f'nc_preview_{file_type}'):
            st.session_state[f'nc_show_preview_{file_type}'] = True
    
    # Version history modal
    if st.session_state.get(f'nc_show_history_{file_type}', False):
        _render_version_history(file_type, file_path, version_ctrl)
    
    # Syntax preview modal
    if st.session_state.get(f'nc_show_preview_{file_type}', False):
        _render_syntax_preview(file_type, extension)


def _render_sync_panel(manifest: dict, version_ctrl: VersionControl):
    """Render the synchronization panel."""
    st.subheader("🔄 Format Synchronization")
    st.markdown("""
    Convert content between formats. Changes are previewed before applying.
    
    ⚠️ Some conversions are **lossy** (e.g., annotations may be lost when converting to `.nc`).
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**From .ncd (Draft):**")
        if st.button("→ Convert to .nc", key='sync_ncd_to_nc'):
            _sync_files('draft', 'formal', manifest, version_ctrl)
        if st.button("→ Convert to .ncn", key='sync_ncd_to_ncn'):
            _sync_files('draft', 'natural', manifest, version_ctrl)
    
    with col2:
        st.markdown("**To .ncd (Draft):**")
        if st.button("← Convert from .nc", key='sync_nc_to_ncd'):
            _sync_files('formal', 'draft', manifest, version_ctrl)
        if st.button("← Convert from .ncn", key='sync_ncn_to_ncd'):
            _sync_files('natural', 'draft', manifest, version_ctrl)
    
    # Show sync preview if active
    if st.session_state.nc_sync_preview:
        _render_sync_preview(version_ctrl)


def _render_version_history(file_type: str, file_path: str, version_ctrl: VersionControl):
    """Render version history panel."""
    with st.expander("📜 Version History", expanded=True):
        versions = version_ctrl.get_history(file_path, limit=20)
        
        if not versions:
            st.info("No version history yet. Save the file to create the first snapshot.")
        else:
            st.caption(f"📊 {len(versions)} version(s) found")
            
            for version in versions:
                with st.container():
                    col_v1, col_v2, col_v3 = st.columns([2, 2, 1])
                    
                    with col_v1:
                        st.caption(f"🕒 {version.timestamp[:19]}")
                    
                    with col_v2:
                        st.caption(f"💬 {version.message}")
                    
                    with col_v3:
                        if st.button("Restore", key=f'nc_restore_{version.id}'):
                            # Restore into structured editor
                            load_content(file_type, version.content)
                            st.success(f"Restored version {version.id[:8]}")
                            st.rerun()
        
        if st.button("Close", key=f'nc_close_history_{file_type}'):
            st.session_state[f'nc_show_history_{file_type}'] = False
            st.rerun()


def _render_syntax_preview(file_type: str, extension: str):
    """Render syntax-highlighted preview."""
    with st.expander("🎨 Syntax Highlight Preview", expanded=True):
        content = get_content(file_type)
        
        if extension == '.ncd':
            highlighted = SyntaxHighlighter.highlight_ncd(content)
        elif extension == '.nc':
            highlighted = SyntaxHighlighter.highlight_nc(content)
        else:
            highlighted = SyntaxHighlighter.highlight_ncn(content)
        
        st.markdown(highlighted, unsafe_allow_html=True)
        
        if st.button("Close Preview", key=f'nc_close_preview_{file_type}'):
            st.session_state[f'nc_show_preview_{file_type}'] = False
            st.rerun()


def _render_sync_preview(version_ctrl: VersionControl):
    """Show sync preview with diff."""
    preview = st.session_state.nc_sync_preview
    
    st.subheader("🔍 Sync Preview")
    
    # Show warnings
    if preview['warnings']:
        for warning in preview['warnings']:
            st.warning(warning)
    
    # Show diff
    col_diff1, col_diff2 = st.columns(2)
    
    with col_diff1:
        st.caption(f"Current {preview['target_type']} content")
        current = preview['current_target']
        st.code(current[:500] + ('...' if len(current) > 500 else ''))
    
    with col_diff2:
        st.caption(f"New content from {preview['source_type']}")
        new = preview['target_content']
        st.code(new[:500] + ('...' if len(new) > 500 else ''))
    
    # Diff view
    with st.expander("📊 Detailed Diff"):
        diff = version_ctrl.diff(
            file_path="temp",
            content1=preview['current_target'],
            content2=preview['target_content']
        )
        st.code(diff, language='diff')
    
    # Actions
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        if st.button("✅ Apply Changes"):
            # Load into structured editor
            load_content(preview['target_type'], preview['target_content'])
            st.session_state.nc_editor_modified[preview['target_type']] = True
            st.session_state.nc_sync_preview = None
            st.success("Changes applied!")
            st.rerun()
    
    with col_act2:
        if st.button("❌ Cancel"):
            st.session_state.nc_sync_preview = None
            st.rerun()


def _save_single_file(file_type: str, file_path: str, version_ctrl: VersionControl):
    """
    Save a single file format from the unified editor.
    
    Note: This uses the single 'draft' manager and serializes to the requested format.
    """
    # Always use the canonical 'draft' manager
    content = get_content('draft', file_type)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Create version snapshot
    version_ctrl.save_snapshot(file_path, content, 'Manual save')
    
    # Clear modification flags
    st.session_state.nc_editor_modified = False
    key_prefix = 'struct_editor_draft'
    manager = st.session_state.get(f'{key_prefix}_manager')
    if manager:
        manager.clear_modifications()


def _save_all_files(manifest: dict, version_ctrl: VersionControl):
    """
    Save all three file formats from the single unified data model.
    
    The same LineManager data is serialized to three different formats:
    - .ncd (draft): with indentation, operators, and metadata
    - .nc (formal): flow.type|content format
    - .ncn (natural): natural language representation
    
    All three files maintain the same flow_index structure.
    """
    # Get the single canonical manager
    key_prefix = 'struct_editor_draft'
    manager = st.session_state.get(f'{key_prefix}_manager')
    
    if not manager:
        st.error("No content to save")
        return
    
    # Serialize to all three formats
    draft_content = manager.serialize('draft')
    formal_content = manager.serialize('formal')
    natural_content = manager.serialize('natural')
    
    # Save each format to its file
    _save_to_file(manifest['files']['draft'], draft_content, version_ctrl)
    _save_to_file(manifest['files']['formal'], formal_content, version_ctrl)
    _save_to_file(manifest['files']['natural'], natural_content, version_ctrl)
    
    # Clear modification flag
    st.session_state.nc_editor_modified = False
    manager.clear_modifications()
    
    st.success("✓ All 3 formats saved! (.ncd, .nc, .ncn)")


def _load_manifest_files_structured(manifest: dict):
    """
    Load manifest files into THE SINGLE structured editor.
    
    Uses .ncd (draft) as the primary source since it contains the most metadata.
    The three file formats (.ncd/.nc/.ncn) are just different serializations
    of the same hierarchical structure, linked by flow_index.
    """
    # Try loading from draft first (most complete format)
    draft_path = manifest['files']['draft']
    loaded = False
    
    if draft_path and os.path.exists(draft_path):
        with open(draft_path, 'r', encoding='utf-8') as f:
            content = f.read()
        load_content('draft', content)
        loaded = True
    
    # Fallback to formal if draft doesn't exist
    elif manifest['files']['formal'] and os.path.exists(manifest['files']['formal']):
        with open(manifest['files']['formal'], 'r', encoding='utf-8') as f:
            content = f.read()
        load_content('draft', content)  # Still load into single 'draft' editor
        loaded = True
    
    # Fallback to natural if neither exists
    elif manifest['files']['natural'] and os.path.exists(manifest['files']['natural']):
        with open(manifest['files']['natural'], 'r', encoding='utf-8') as f:
            content = f.read()
        load_content('draft', content)  # Still load into single 'draft' editor
        loaded = True
    
    # If no files exist, initialize empty
    if not loaded:
        load_content('draft', "")


def _sync_files(source_type: str, target_type: str, manifest: dict, version_ctrl: VersionControl):
    """Sync content from source to target file type."""
    source_content = get_content(source_type)
    
    if not source_content.strip():
        st.warning("Source file is empty")
        return
    
    # Determine conversion function
    ext_map = {'draft': 'ncd', 'formal': 'nc', 'natural': 'ncn'}
    source_ext = ext_map[source_type]
    target_ext = ext_map[target_type]
    
    conversion_key = f"{source_ext}_to_{target_ext}"
    
    try:
        if conversion_key == "ncd_to_nc":
            converted, warnings = FormatConverter.ncd_to_nc(source_content)
        elif conversion_key == "ncd_to_ncn":
            converted, warnings = FormatConverter.ncd_to_ncn(source_content)
        elif conversion_key == "nc_to_ncd":
            converted, warnings = FormatConverter.nc_to_ncd(source_content)
        elif conversion_key == "ncn_to_ncd":
            converted, warnings = FormatConverter.ncn_to_ncd(source_content)
        elif conversion_key == "nc_to_ncn":
            converted, warnings = FormatConverter.nc_to_ncn(source_content)
        elif conversion_key == "ncn_to_nc":
            converted, warnings = FormatConverter.ncn_to_nc(source_content)
        else:
            st.error(f"Unsupported conversion: {conversion_key}")
            return
        
        # Store sync preview
        st.session_state.nc_sync_preview = {
            'source_type': source_type,
            'target_type': target_type,
            'source_content': source_content,
            'target_content': converted,
            'warnings': warnings,
            'current_target': get_content(target_type)
        }
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Conversion error: {str(e)}")
