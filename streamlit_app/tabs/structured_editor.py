"""
Structured Line-by-Line Editor Component

Renders NormCode content as individually editable lines with
per-line controls for structural operations.
"""

import streamlit as st
from typing import List, Optional, Callable
from pathlib import Path
import sys

# Add parent to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from core.line_editor import EditableLine, LineManager, LineType


# Color scheme for syntax highlighting
COLORS = {
    'functional': '#ff79c6',      # Pink - <=
    'value': '#8be9fd',           # Cyan - <-
    'output': '#bd93f9',          # Purple - :<:
    'question': '#50fa7b',        # Green - ?:
    'description': '#f1fa8c',     # Yellow - /:
    'source': '#ffb86c',          # Orange - ...:
    'generic': '#f8f8f2',         # White
    'flow_index': '#ff5555',      # Red
    'sequence_type': '#6272a4',   # Gray
    'indent_guide': '#44475a',    # Dark gray
}

# Operator options for dropdown
OPERATOR_OPTIONS = [
    ('<=', 'Functional (<=)'),
    ('<-', 'Value (<-)'),
    (':<:', 'Output (:<:)'),
    ('?:', 'Question (?:)'),
    ('/:', 'Description (/:)'),
    ('...:', 'Source (...:)'),
    ('', 'None'),
]

# Sequence type options
SEQUENCE_TYPE_OPTIONS = [
    '', 'imperative', 'grouping', 'assigning', 
    'quantifying', 'timing', 'judgement', 'simple'
]


def init_structured_editor_state(file_type: str):
    """Initialize session state for a structured editor instance."""
    key_prefix = f'struct_editor_{file_type}'
    
    if f'{key_prefix}_lines' not in st.session_state:
        st.session_state[f'{key_prefix}_lines'] = []
    if f'{key_prefix}_manager' not in st.session_state:
        st.session_state[f'{key_prefix}_manager'] = LineManager()
    if f'{key_prefix}_selected' not in st.session_state:
        st.session_state[f'{key_prefix}_selected'] = None
    if f'{key_prefix}_mode' not in st.session_state:
        st.session_state[f'{key_prefix}_mode'] = 'structured'  # or 'text'
    if f'{key_prefix}_format' not in st.session_state:
        st.session_state[f'{key_prefix}_format'] = 'draft'  # 'draft', 'formal', 'natural'


def load_content(file_type: str, content: str):
    """Load content into the structured editor."""
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    lines = manager.parse_text(content)
    st.session_state[f'{key_prefix}_lines'] = lines


def get_content(file_type: str, format: str = None) -> str:
    """
    Get serialized content from the structured editor.
    
    Args:
        file_type: The file type key
        format: Output format ('draft', 'formal', 'natural'). 
                If None, uses the current format setting.
    """
    key_prefix = f'struct_editor_{file_type}'
    manager = st.session_state[f'{key_prefix}_manager']
    
    if format is None:
        format = st.session_state.get(f'{key_prefix}_format', 'draft')
    
    return manager.serialize(format)


def render_structured_editor(
    file_type: str,
    on_change: Optional[Callable] = None
):
    """
    Render the structured line-by-line editor.
    
    Args:
        file_type: Type of file ('draft', 'formal', 'natural')
        on_change: Callback when content changes
    """
    key_prefix = f'struct_editor_{file_type}'
    init_structured_editor_state(file_type)
    
    manager: LineManager = st.session_state[f'{key_prefix}_manager']
    
    # Migrate existing lines to add new attributes (backwards compatibility)
    # Check if method exists (for old cached managers in session state)
    if hasattr(manager, 'migrate_lines'):
        manager.migrate_lines()
    else:
        # Fallback: manually migrate lines for old manager instances
        for line in manager.lines:
            if not hasattr(line, 'display_format'):
                object.__setattr__(line, 'display_format', 'draft')
    
    mode = st.session_state[f'{key_prefix}_mode']
    
    # Mode toggle and toolbar
    _render_toolbar(file_type, key_prefix, manager)
    
    if mode == 'text':
        _render_text_mode(file_type, key_prefix, manager, on_change)
    else:
        _render_structured_mode(file_type, key_prefix, manager, on_change)


def _render_toolbar(file_type: str, key_prefix: str, manager: LineManager):
    """Render the editor toolbar."""
    col1, col2, col3, col4, col5 = st.columns([1.5, 1, 1, 1.5, 1])
    
    # Bulk format actions
    with col1:
        st.caption("📋 Bulk Format:")
        bulk_cols = st.columns(3)
        with bulk_cols[0]:
            if st.button("📄", key=f'{key_prefix}_bulk_draft', help="Set all to Draft"):
                for line in manager.lines:
                    manager.update_line_display_format(line.id, 'draft')
                st.rerun()
        with bulk_cols[1]:
            if st.button("📋", key=f'{key_prefix}_bulk_formal', help="Set all to Formal"):
                for line in manager.lines:
                    manager.update_line_display_format(line.id, 'formal')
                st.rerun()
        with bulk_cols[2]:
            if st.button("📖", key=f'{key_prefix}_bulk_natural', help="Set all to Natural"):
                for line in manager.lines:
                    manager.update_line_display_format(line.id, 'natural')
                st.rerun()
    
    with col2:
        mode = st.session_state[f'{key_prefix}_mode']
        if st.button(
            "📝 Text" if mode == 'structured' else "🔧 Struct",
            key=f'{key_prefix}_mode_toggle',
            help="Toggle between structured and text editing modes"
        ):
            new_mode = 'text' if mode == 'structured' else 'structured'
            st.session_state[f'{key_prefix}_mode'] = new_mode
            st.rerun()
    
    with col3:
        if st.button("➕ Add", key=f'{key_prefix}_add_line'):
            # Add a new line at the end
            manager.insert_line(len(manager.lines))
            st.rerun()
    
    with col4:
        if manager.has_modifications():
            st.markdown("⚠️ **Modified**")
        else:
            st.caption(f"{len(manager.lines)} lines")
    
    with col5:
        # Show format distribution (use getattr for backwards compatibility with existing lines)
        draft_count = sum(1 for line in manager.lines if getattr(line, 'display_format', 'draft') == 'draft')
        formal_count = sum(1 for line in manager.lines if getattr(line, 'display_format', 'draft') == 'formal')
        natural_count = sum(1 for line in manager.lines if getattr(line, 'display_format', 'draft') == 'natural')
        st.caption(f"📄{draft_count} 📋{formal_count} 📖{natural_count}")


def _render_text_mode(
    file_type: str, 
    key_prefix: str, 
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render text area mode for bulk editing."""
    current_format = st.session_state.get(f'{key_prefix}_format', 'draft')
    current_content = manager.serialize(current_format)
    
    # Show format indicator
    format_names = {'draft': '.ncd (Draft)', 'formal': '.nc (Formal)', 'natural': '.ncn (Natural)'}
    st.caption(f"Editing as: **{format_names[current_format]}**")
    
    new_content = st.text_area(
        "Raw Content",
        value=current_content,
        height=500,
        key=f'{key_prefix}_text_area_{current_format}',  # Include format in key to refresh
        label_visibility='collapsed'
    )
    
    # Parse changes back (always parse as draft for now - formal/natural parsing would need more work)
    if new_content != current_content:
        manager.parse_text(new_content)
        if on_change:
            on_change()
    
    # Show all three formats preview
    with st.expander("📊 All Formats Preview", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("Draft (.ncd)")
            st.code(manager.serialize('draft'), language='text')
        
        with col2:
            st.caption("Formal (.nc)")
            st.code(manager.serialize('formal'), language='text')
        
        with col3:
            st.caption("Natural (.ncn)")
            st.code(manager.serialize('natural'), language='text')


def _render_structured_mode(
    file_type: str,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render the structured line-by-line editing mode with per-line format toggles."""
    
    # Custom CSS for editor styling
    st.markdown("""
    <style>
    .line-editor-container {
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
    }
    .line-row {
        display: flex;
        align-items: center;
        border-bottom: 1px solid #2d2d3d;
        padding: 2px 0;
    }
    .line-number {
        color: #6272a4;
        width: 40px;
        text-align: right;
        padding-right: 10px;
        user-select: none;
    }
    .indent-guide {
        color: #44475a;
        user-select: none;
    }
    .line-operator {
        font-weight: bold;
        min-width: 30px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get visible lines (respecting collapse state)
    visible_lines = manager.get_visible_lines()
    
    if not visible_lines:
        st.info("No content yet. Click 'Add' to start editing.")
        return
    
    # Render each line (each line has its own format preference)
    for i, line in enumerate(visible_lines):
        _render_line_row(
            line=line,
            line_number=i + 1,
            key_prefix=key_prefix,
            manager=manager,
            on_change=on_change
        )
    
    # Multi-format preview panel
    with st.expander("📊 All Formats Preview", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("📄 Draft (.ncd)")
            st.code(manager.serialize('draft'), language='text')
        
        with col2:
            st.caption("📋 Formal (.nc)")
            st.code(manager.serialize('formal'), language='text')
        
        with col3:
            st.caption("📖 Natural (.ncn)")
            st.code(manager.serialize('natural'), language='text')


def _render_line_row(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render a single editable line row with per-line format toggle."""
    
    # Check if this line has children (for collapse toggle)
    has_children = len(manager.get_children(line.id)) > 0
    
    # Build indent string for display
    indent_display = "│  " * line.depth if line.depth > 0 else ""
    
    # Use per-line format preference (with backwards compatibility)
    line_format = getattr(line, 'display_format', 'draft')
    
    # Main layout: Flow Index | Format Toggle | Indent | Content | Actions
    cols = st.columns([0.8, 1.0, 0.5, 5.5, 1.5])
    
    # Column 1: Flow Index
    with cols[0]:
        st.markdown(
            f"<span style='color: {COLORS['flow_index']}; font-weight: bold; font-family: monospace;'>{line.flow_index or '—'}</span>",
            unsafe_allow_html=True
        )
    
    # Column 2: Per-Line Format Toggle
    with cols[1]:
        format_options = {
            'draft': '📄 Draft',
            'formal': '📋 Formal',
            'natural': '📖 Natural'
        }
        
        new_format = st.selectbox(
            "Format",
            options=['draft', 'formal', 'natural'],
            index=['draft', 'formal', 'natural'].index(line_format),
            format_func=lambda x: format_options[x],
            key=f'{key_prefix}_fmt_{line.id}',
            label_visibility='collapsed'
        )
        
        if new_format != line_format:
            manager.update_line_display_format(line.id, new_format)
            if on_change:
                on_change()
            st.rerun()
    
    # Column 3: Indent/Collapse Toggle
    with cols[2]:
        if has_children:
            collapse_icon = "▼" if not line.is_collapsed else "▶"
            if st.button(
                f"{collapse_icon}",
                key=f'{key_prefix}_collapse_{line.id}',
                help="Collapse/expand children"
            ):
                manager.toggle_collapse(line.id)
                st.rerun()
        else:
            st.markdown(
                f"<span style='color: {COLORS['indent_guide']}'>{indent_display}├</span>",
                unsafe_allow_html=True
            )
    
    # Column 4: Content (format-specific editing)
    with cols[3]:
        _render_line_content_editable(line, line_number, key_prefix, manager, on_change, line_format)
    
    # Column 5: Action Buttons
    with cols[4]:
        _render_line_actions(line, key_prefix, manager, on_change)


def _render_line_content_editable(
    line: EditableLine,
    line_number: int,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable],
    line_format: str
):
    """Render editable content based on the line's display format."""
    
    if line_format == 'formal':
        # Formal format: display and edit as flow.type|content
        display_content = line.as_formal()
        
        new_content = st.text_input(
            "Content",
            value=display_content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="flow.type|operator content"
        )
        
        if new_content != display_content:
            # Parse the formal format
            operator, content, sequence_type = manager.parse_line_from_format(new_content, 'formal')
            manager.update_line_operator(line.id, operator)
            manager.update_line_content(line.id, content)
            if sequence_type:
                manager.update_line_metadata(line.id, sequence_type=sequence_type)
            if on_change:
                on_change()
    
    elif line_format == 'natural':
        # Natural format: display and edit as natural language
        display_content = line.as_natural().strip()
        
        new_content = st.text_input(
            "Content",
            value=display_content,
            key=f'{key_prefix}_content_{line.id}',
            label_visibility='collapsed',
            placeholder="Natural language description"
        )
        
        if new_content != display_content:
            # Parse the natural format
            operator, content, sequence_type = manager.parse_line_from_format(new_content, 'natural')
            manager.update_line_operator(line.id, operator)
            manager.update_line_content(line.id, content)
            if sequence_type:
                manager.update_line_metadata(line.id, sequence_type=sequence_type)
            if on_change:
                on_change()
    
    else:  # draft format - full structured editing with operator dropdown
        # Create sub-columns for operator and content
        sub_cols = st.columns([0.8, 5.5, 1.0])
        
        with sub_cols[0]:
            # Operator dropdown
            current_op = line.operator
            op_index = next(
                (i for i, (op, _) in enumerate(OPERATOR_OPTIONS) if op == current_op),
                len(OPERATOR_OPTIONS) - 1
            )
            
            new_op = st.selectbox(
                "Op",
                options=[op for op, _ in OPERATOR_OPTIONS],
                format_func=lambda x: x if x else "—",
                index=op_index,
                key=f'{key_prefix}_op_{line.id}',
                label_visibility='collapsed'
            )
            
            if new_op != current_op:
                manager.update_line_operator(line.id, new_op)
                if on_change:
                    on_change()
        
        with sub_cols[1]:
            # Content input
            new_content = st.text_input(
                "Content",
                value=line.content,
                key=f'{key_prefix}_content_{line.id}',
                label_visibility='collapsed',
                placeholder="Enter content..."
            )
            
            if new_content != line.content:
                manager.update_line_content(line.id, new_content)
                if on_change:
                    on_change()
        
        with sub_cols[2]:
            # Sequence type dropdown
            seq_index = SEQUENCE_TYPE_OPTIONS.index(line.sequence_type) if line.sequence_type in SEQUENCE_TYPE_OPTIONS else 0
            
            new_seq = st.selectbox(
                "Seq",
                options=SEQUENCE_TYPE_OPTIONS,
                index=seq_index,
                key=f'{key_prefix}_seq_{line.id}',
                label_visibility='collapsed',
                format_func=lambda x: x[:3] if x else "—"
            )
            
            if new_seq != line.sequence_type:
                manager.update_line_metadata(line.id, sequence_type=new_seq)
                if on_change:
                    on_change()


def _render_line_actions(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render action buttons for a line."""
    
    # Use a popover/expander for actions to save space
    action_cols = st.columns([1, 1, 1, 1, 1])
    
    # Indent/Outdent
    with action_cols[0]:
        if st.button("→", key=f'{key_prefix}_indent_{line.id}', help="Indent"):
            manager.indent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[1]:
        if st.button("←", key=f'{key_prefix}_outdent_{line.id}', help="Outdent"):
            manager.outdent_line(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Move up/down
    with action_cols[2]:
        if st.button("↑", key=f'{key_prefix}_up_{line.id}', help="Move up"):
            manager.move_line_up(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    with action_cols[3]:
        if st.button("↓", key=f'{key_prefix}_down_{line.id}', help="Move down"):
            manager.move_line_down(line.id)
            if on_change:
                on_change()
            st.rerun()
    
    # Delete
    with action_cols[4]:
        if st.button("🗑", key=f'{key_prefix}_del_{line.id}', help="Delete"):
            manager.delete_line(line.id)
            if on_change:
                on_change()
            st.rerun()


def render_line_context_menu(
    line: EditableLine,
    key_prefix: str,
    manager: LineManager,
    on_change: Optional[Callable]
):
    """Render an expanded context menu for a line."""
    
    with st.expander(f"Line {manager.get_line_index(line.id) + 1} Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Duplicate", key=f'{key_prefix}_dup_{line.id}'):
                manager.duplicate_line(line.id)
                if on_change:
                    on_change()
                st.rerun()
            
            if st.button("📋 Duplicate with children", key=f'{key_prefix}_dup_children_{line.id}'):
                manager.duplicate_line(line.id, include_children=True)
                if on_change:
                    on_change()
                st.rerun()
        
        with col2:
            st.markdown("**Add Annotation:**")
            ann_cols = st.columns(3)
            
            with ann_cols[0]:
                if st.button("?:", key=f'{key_prefix}_add_q_{line.id}', help="Add question"):
                    manager.add_annotation(line.id, 'question')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[1]:
                if st.button("/:", key=f'{key_prefix}_add_d_{line.id}', help="Add description"):
                    manager.add_annotation(line.id, 'description')
                    if on_change:
                        on_change()
                    st.rerun()
            
            with ann_cols[2]:
                if st.button("...:", key=f'{key_prefix}_add_s_{line.id}', help="Add source"):
                    manager.add_annotation(line.id, 'source')
                    if on_change:
                        on_change()
                    st.rerun()


def render_quick_actions_panel(
    file_type: str,
    key_prefix: str,
    manager: LineManager
):
    """Render a panel with quick actions for the entire document."""
    
    with st.expander("🔧 Quick Actions", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Structure:**")
            st.caption("💡 Flow indices auto-update based on indent structure")
            
            if st.button("📐 Rebuild hierarchy", key=f'{key_prefix}_fix_indent'):
                _normalize_indentation(manager)
                st.rerun()
        
        with col2:
            st.markdown("**Insert Templates:**")
            if st.button("➕ Functional block", key=f'{key_prefix}_tpl_func'):
                _insert_functional_template(manager)
                st.rerun()
            
            if st.button("➕ Value block", key=f'{key_prefix}_tpl_value'):
                _insert_value_template(manager)
                st.rerun()
        
        with col3:
            st.markdown("**View:**")
            if st.button("▼ Expand all", key=f'{key_prefix}_expand_all'):
                for line in manager.lines:
                    line.is_collapsed = False
                st.rerun()
            
            if st.button("▶ Collapse all", key=f'{key_prefix}_collapse_all'):
                for line in manager.lines:
                    if manager.get_children(line.id):
                        line.is_collapsed = True
                st.rerun()


def _normalize_indentation(manager: LineManager):
    """Ensure consistent indentation based on parent-child relationships."""
    manager._build_hierarchy()
    for line in manager.lines:
        line.is_modified = True


def _insert_functional_template(manager: LineManager):
    """Insert a template for a functional concept block."""
    lines = [
        EditableLine(depth=0, operator='<=', line_type=LineType.FUNCTIONAL_CONCEPT,
                    content='$.({method_name})', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description of what this does', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_1}', is_modified=True),
        EditableLine(depth=1, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{input_2}', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()


def _insert_value_template(manager: LineManager):
    """Insert a template for a value concept block."""
    lines = [
        EditableLine(depth=0, operator='<-', line_type=LineType.VALUE_CONCEPT,
                    content='{concept_name}', is_modified=True),
        EditableLine(depth=1, operator='/:', line_type=LineType.ANNOTATION_DESC,
                    content='Description', is_modified=True),
    ]
    
    for line in lines:
        manager.lines.append(line)
    
    manager._build_hierarchy()

