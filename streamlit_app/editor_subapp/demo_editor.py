"""
Minimal NormCode Inline Editor Demo

A simple Streamlit app for editing .ncd and .ncn files with inline editing.
Uses unified_parser.py for parsing and serialization.
"""

import streamlit as st
import json
import os
from pathlib import Path
from unified_parser import UnifiedParser, load_file

# Page config
st.set_page_config(
    page_title="NormCode Inline Editor",
    page_icon="📝",
    layout="wide"
)

# Custom CSS and JavaScript for Tab handling
st.markdown("""
<style>
/* Center all button text */
button[kind="secondary"] {
    text-align: center !important;
}

button[kind="secondary"] p {
    width: 100%;
    text-align: center !important;
    margin: 0 auto !important;
    justify-content: center !important;
}

/* Center button container */
button[kind="secondary"] div {
    justify-content: center !important;
    text-align: center !important;
}

/* For small icon buttons */
button[kind="secondary"][data-testid="baseButton-secondary"] {
    padding: 0 !important;
    min-width: 2.5rem !important;
}

/* Disable line wrapping in text areas - enable horizontal scrolling */
textarea {
    white-space: pre !important;
    overflow-x: auto !important;
    word-wrap: normal !important;
    font-family: monospace !important;
    font-size: 11px !important;
    line-height: 1.4 !important;
}
</style>
""", unsafe_allow_html=True)

# JavaScript for Tab/Shift+Tab - using components to access parent frame
import streamlit.components.v1 as components

tab_handler_html = """
<script>
(function() {
    // Access the parent window (Streamlit's main page)
    var parentDoc = window.parent.document;
    var parentWin = window.parent;
    
    // Check if already installed
    if (parentWin._ncTabHandler) return;
    
    // Separator used in the flow index format
    var SEP = ' │ ';
    
    function handleTab(e) {
        // Only intercept Tab key
        if (e.key !== 'Tab') return;
        
        // Only for textareas
        var target = e.target;
        if (!target || target.tagName !== 'TEXTAREA') return;
        
        // Stop the event completely
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        
        var start = target.selectionStart;
        var end = target.selectionEnd;
        var value = target.value;
        
        // Find line boundaries
        var beforeSel = value.substring(0, start);
        var lineStart = beforeSel.lastIndexOf('\\n') + 1;
        var lineEnd = value.indexOf('\\n', end);
        if (lineEnd === -1) lineEnd = value.length;
        
        var selectedText = value.substring(lineStart, lineEnd);
        var lines = selectedText.split('\\n');
        var totalChange = 0;
        var firstLineChange = 0;
        
        if (e.shiftKey) {
            // Shift+Tab: Unindent content after separator
            var newLines = lines.map(function(line, idx) {
                var change = 0;
                var sepIdx = line.indexOf(SEP);
                
                if (sepIdx >= 0) {
                    // Has separator - unindent content after it
                    var prefix = line.substring(0, sepIdx + SEP.length);
                    var content = line.substring(sepIdx + SEP.length);
                    
                    // Remove leading spaces from content
                    if (content.substring(0,4) === '    ') { content = content.substring(4); change = 4; }
                    else if (content.substring(0,1) === '\\t') { content = content.substring(1); change = 1; }
                    else if (content.substring(0,3) === '   ') { content = content.substring(3); change = 3; }
                    else if (content.substring(0,2) === '  ') { content = content.substring(2); change = 2; }
                    else if (content.substring(0,1) === ' ') { content = content.substring(1); change = 1; }
                    
                    line = prefix + content;
                } else {
                    // No separator - unindent from beginning
                    if (line.substring(0,4) === '    ') { line = line.substring(4); change = 4; }
                    else if (line.substring(0,1) === '\\t') { line = line.substring(1); change = 1; }
                    else if (line.substring(0,3) === '   ') { line = line.substring(3); change = 3; }
                    else if (line.substring(0,2) === '  ') { line = line.substring(2); change = 2; }
                    else if (line.substring(0,1) === ' ') { line = line.substring(1); change = 1; }
                }
                
                if (idx === 0) firstLineChange = change;
                totalChange += change;
                return line;
            });
            
            target.value = value.substring(0, lineStart) + newLines.join('\\n') + value.substring(lineEnd);
            target.selectionStart = Math.max(lineStart, start - firstLineChange);
            target.selectionEnd = Math.max(target.selectionStart, end - totalChange);
            
        } else {
            // Tab: Indent content after separator
            if (start === end) {
                // No selection - just insert 4 spaces at cursor
                target.value = value.substring(0, start) + '    ' + value.substring(end);
                target.selectionStart = target.selectionEnd = start + 4;
            } else {
                // Selection - indent content after separator on each line
                var newLines = lines.map(function(line) {
                    var sepIdx = line.indexOf(SEP);
                    
                    if (sepIdx >= 0) {
                        // Has separator - add spaces after it
                        var prefix = line.substring(0, sepIdx + SEP.length);
                        var content = line.substring(sepIdx + SEP.length);
                        return prefix + '    ' + content;
                    } else {
                        // No separator - add spaces at beginning
                        return '    ' + line;
                    }
                });
                
                target.value = value.substring(0, lineStart) + newLines.join('\\n') + value.substring(lineEnd);
                target.selectionStart = start + 4;
                target.selectionEnd = end + (lines.length * 4);
            }
        }
        
        // Notify Streamlit of change
        target.dispatchEvent(new Event('input', { bubbles: true }));
        return false;
    }
    
    // Install on parent document with capture phase
    parentDoc.addEventListener('keydown', handleTab, true);
    
    // Also install directly on any existing textareas in parent
    var textareas = parentDoc.querySelectorAll('textarea');
    textareas.forEach(function(ta) {
        ta.addEventListener('keydown', handleTab, true);
    });
    
    // Watch for new textareas in parent and attach handler
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(m) {
            m.addedNodes.forEach(function(node) {
                if (node.nodeType !== 1) return;
                if (node.tagName === 'TEXTAREA') {
                    node.addEventListener('keydown', handleTab, true);
                }
                if (node.querySelectorAll) {
                    node.querySelectorAll('textarea').forEach(function(ta) {
                        ta.addEventListener('keydown', handleTab, true);
                    });
                }
            });
        });
    });
    observer.observe(parentDoc.body, { childList: true, subtree: true });
    
    parentWin._ncTabHandler = true;
    console.log('NormCode Tab handler installed on parent');
})();
</script>
"""

# Inject the JavaScript (height=0 makes the iframe invisible)
components.html(tab_handler_html, height=0)

# Initialize session state
if 'lines' not in st.session_state:
    st.session_state.lines = []
if 'current_file' not in st.session_state:
    st.session_state.current_file = None
if 'modified' not in st.session_state:
    st.session_state.modified = False
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'ncd'  # Global default: 'ncd' or 'ncn'
if 'line_view_modes' not in st.session_state:
    st.session_state.line_view_modes = {}  # Per-line view mode overrides
if 'show_natural_language' not in st.session_state:
    st.session_state.show_natural_language = True  # For pure text mode: show NCN annotations
if 'show_comments' not in st.session_state:
    st.session_state.show_comments = True  # Toggle to show/hide comments
if 'collapsed_indices' not in st.session_state:
    st.session_state.collapsed_indices = set()  # Set of collapsed flow indices
if 'editor_mode' not in st.session_state:
    st.session_state.editor_mode = 'line_by_line'  # 'line_by_line' or 'pure_text'
if 'text_editor_key' not in st.session_state:
    st.session_state.text_editor_key = 0  # Counter to force text area refresh
if 'pending_text' not in st.session_state:
    st.session_state.pending_text = None  # Store pending text changes
if 'delete_confirmations' not in st.session_state:
    st.session_state.delete_confirmations = set()  # Track which lines need delete confirmation
if 'max_flow_len' not in st.session_state:
    st.session_state.max_flow_len = 6  # Default flow index column width

# Initialize parser
parser = UnifiedParser()

# Helper functions
def load_files(ncd_path, ncn_path):
    """Load .ncd and .ncn files and parse them."""
    try:
        ncd_content = load_file(ncd_path) if os.path.exists(ncd_path) else ""
        ncn_content = load_file(ncn_path) if os.path.exists(ncn_path) else ""
        
        if ncd_content:
            parsed = parser.parse(ncd_content, ncn_content)
            st.session_state.lines = parsed['lines']
            st.session_state.current_file = ncd_path
            st.session_state.modified = False
            st.session_state.line_view_modes = {}  # Reset per-line view modes
            st.session_state.collapsed_indices = set()  # Reset collapsed indices
            st.session_state.pending_text = None  # Reset pending text changes
            st.session_state.text_editor_key += 1  # Force text editor refresh
            return True
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return False

def get_visible_lines_as_text(lines, show_comments, collapsed_indices, show_natural_language=True):
    """
    Generate .ncdn or .ncd format text from visible lines.
    Uses the parser's serialize_ncdn (if show_natural_language) or serialize_ncd method with filtering.
    """
    # Filter lines based on visibility settings
    visible_lines = []
    
    for idx, line in enumerate(lines):
        flow_idx = line.get('flow_index', '')
        line_type = line.get('type', '')
        
        # Apply filters
        if not show_comments and line_type in ['comment', 'inline_comment']:
            continue
        
        is_collapsed = False
        if flow_idx:
            for collapsed_idx in collapsed_indices:
                if flow_idx.startswith(collapsed_idx + "."):
                    is_collapsed = True
                    break
        if is_collapsed:
            continue
        
        visible_lines.append(line)
    
    # Use parser to generate appropriate format
    parsed_data = {"lines": visible_lines}
    if show_natural_language:
        return parser.serialize_ncdn(parsed_data)
    else:
        # Just show NCD without NCN annotations
        serialized = parser.serialize(parsed_data)
        return serialized['ncd']

def get_visible_lines_with_flow_prefix(lines, show_comments, collapsed_indices, show_natural_language=True):
    """
    Generate text with flow indices prefixed to each line.
    Format: "flow_idx | content"
    Returns tuple of (text_with_prefixes, list_of_flow_indices, max_flow_len)
    
    When show_natural_language=True, NCN annotations get extra lines.
    We track flow indices per output line (including NCN annotation lines).
    """
    # Filter lines based on visibility settings
    visible_lines = []
    
    for line in lines:
        flow_idx = line.get('flow_index', '')
        line_type = line.get('type', '')
        
        # Apply filters
        if not show_comments and line_type in ['comment', 'inline_comment']:
            continue
        
        is_collapsed = False
        if flow_idx:
            for collapsed_idx in collapsed_indices:
                if flow_idx.startswith(collapsed_idx + "."):
                    is_collapsed = True
                    break
        if is_collapsed:
            continue
        
        visible_lines.append(line)
    
    # Build flow indices that match the output lines from serialize_ncdn
    # Only main lines show their flow index; comments and NCN annotations get empty
    output_flow_indices = []
    
    i = 0
    while i < len(visible_lines):
        line = visible_lines[i]
        flow_idx = line.get('flow_index', '')
        line_type = line.get('type', '')
        
        if line_type == 'main':
            # Main line gets its flow index
            output_flow_indices.append(flow_idx)
            
            # Check if next line is inline_comment (combined on same output line in NCDN)
            # No extra flow index needed since they're on the same line
            next_is_inline = (i + 1 < len(visible_lines) and 
                             visible_lines[i + 1].get('type') == 'inline_comment')
            if next_is_inline:
                i += 1  # Skip the inline_comment, it's merged with main
            
            # If showing natural language and line has NCN content, add placeholder for NCN line
            if show_natural_language and line.get('ncn_content'):
                output_flow_indices.append('')  # NCN annotation line - no flow index
                
        elif line_type == 'comment':
            # Comments get empty flow index (so each flow_idx appears only once)
            output_flow_indices.append('')
        
        # Note: inline_comment is handled above with main line
        
        i += 1
    
    # Use parser to generate appropriate format
    parsed_data = {"lines": visible_lines}
    if show_natural_language:
        content_text = parser.serialize_ncdn(parsed_data)
    else:
        serialized = parser.serialize(parsed_data)
        content_text = serialized['ncd']
    
    # Split content into lines and add flow index prefix
    content_lines = content_text.split('\n')
    # Remove trailing empty line if present
    if content_lines and content_lines[-1] == '':
        content_lines = content_lines[:-1]
    
    # Find max flow index length for alignment
    all_flow_indices = [f for f in output_flow_indices if f]
    max_flow_len = max((len(f) for f in all_flow_indices), default=4)
    max_flow_len = max(max_flow_len, 6)  # Minimum width of 6
    
    # Combine flow indices with content lines
    prefixed_lines = []
    for i, content_line in enumerate(content_lines):
        if i < len(output_flow_indices):
            flow_idx = output_flow_indices[i]
            # Right-align flow index for neat appearance (empty for NCN lines)
            prefixed_lines.append(f"{flow_idx:>{max_flow_len}} │ {content_line}")
        else:
            # Extra lines (shouldn't happen normally)
            prefixed_lines.append(f"{'':>{max_flow_len}} │ {content_line}")
    
    return '\n'.join(prefixed_lines), output_flow_indices, max_flow_len

def strip_flow_prefix_from_text(prefixed_text, max_flow_len):
    """
    Remove flow index prefixes from text if present.
    Returns just the content portion.
    If no prefix found, returns the line as-is.
    """
    lines = prefixed_text.split('\n')
    content_lines = []
    
    for line in lines:
        # Look for the separator " │ " and extract content after it
        sep_idx = line.find(' │ ')
        if sep_idx >= 0:
            # Found separator - extract content after it
            content_lines.append(line[sep_idx + 3:])
        else:
            # No separator found - line might have been edited without flow prefix
            # Just use the line as-is
            content_lines.append(line)
    
    return '\n'.join(content_lines)

def update_lines_from_ncdn_text(ncdn_text, lines, show_comments, collapsed_indices, show_natural_language=True):
    """
    Update lines based on edited .ncdn text.
    Uses parser's parse_ncdn method.
    
    This function synchronizes edits from the pure text editor back to the
    central JSON structure (st.session_state.lines), which is the single
    source of truth for all formats (NCD, NCN, NCDN).
    
    Flow:
    1. Parse edited NCDN text -> new JSON structure
    2. Replace visible lines with new parsed lines
    3. Keep hidden lines (collapsed/filtered) in their original positions
    4. Merge everything back together
    
    Args:
        ncdn_text: The edited text from the pure text editor
        lines: The current lines (JSON structure) to update
        show_comments: Whether comments were visible in editor
        collapsed_indices: Set of collapsed flow indices
        show_natural_language: Whether NCN annotations were visible in editor
    """
    # Parse the edited text (handles both NCDN and NCD-only formats)
    reparsed = parser.parse_ncdn(ncdn_text)
    new_visible_lines = reparsed['lines']
    
    # Collect hidden lines (ones that were not visible in the editor)
    hidden_lines = []
    for line in lines:
        flow_idx = line.get('flow_index', '')
        line_type = line.get('type', '')
        
        # Check if this line was hidden from the editor
        is_hidden = False
        
        # Hidden by comment filter
        if not show_comments and line_type in ['comment', 'inline_comment']:
            is_hidden = True
        
        # Hidden by collapse filter
        if not is_hidden and flow_idx:
            for collapsed_idx in collapsed_indices:
                if flow_idx.startswith(collapsed_idx + "."):
                    is_hidden = True
                    break
        
        if is_hidden:
            hidden_lines.append(line.copy())
    
    # Strategy: Replace all visible sections with new lines, keep hidden lines
    # For simplicity, we'll put all new visible lines first, then append hidden lines
    # This maintains functionality while allowing additions/deletions
    result_lines = new_visible_lines + hidden_lines
    
    return result_lines

def add_line_after(lines, after_idx, line_type='main'):
    """Add a new line after the specified index."""
    # Get context from the line we're inserting after
    ref_line = lines[after_idx]
    ref_depth = ref_line.get('depth', 0)
    ref_flow = ref_line.get('flow_index', '1')
    
    # Create new line with incremented flow index
    if ref_flow:
        parts = ref_flow.split('.')
        # Increment last part
        parts[-1] = str(int(parts[-1]) + 1)
        new_flow = '.'.join(parts)
    else:
        new_flow = '1'
    
    new_line = {
        'flow_index': new_flow,
        'type': line_type,
        'depth': ref_depth
    }
    
    # Initialize content fields based on type
    if line_type == 'main':
        new_line['nc_main'] = ''
        new_line['ncn_content'] = ''
    else:
        new_line['nc_comment'] = ''
    
    # Insert after the specified index
    lines.insert(after_idx + 1, new_line)
    return lines

def delete_line(lines, idx):
    """Delete a line at the specified index."""
    if 0 <= idx < len(lines):
        del lines[idx]
    return lines

def update_flow_index(lines, idx, new_flow_index):
    """Update the flow index of a line."""
    if 0 <= idx < len(lines):
        lines[idx]['flow_index'] = new_flow_index
        st.session_state.modified = True
    return lines

def load_json(json_path):
    """Load from .nc.json."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        st.session_state.lines = data.get('lines', [])
        st.session_state.current_file = json_path
        st.session_state.modified = False
        st.session_state.line_view_modes = {}  # Reset per-line view modes
        st.session_state.collapsed_indices = set()  # Reset collapsed indices
        st.session_state.pending_text = None  # Reset pending text changes
        st.session_state.text_editor_key += 1  # Force text editor refresh
        return True
    except Exception as e:
        st.error(f"Error loading JSON: {e}")
        return False

def load_ncdn(ncdn_path):
    """Load from .ncdn file."""
    try:
        ncdn_content = load_file(ncdn_path)
        parsed = parser.parse_ncdn(ncdn_content)
        st.session_state.lines = parsed['lines']
        st.session_state.current_file = ncdn_path
        st.session_state.modified = False
        st.session_state.line_view_modes = {}  # Reset per-line view modes
        st.session_state.collapsed_indices = set()  # Reset collapsed indices
        st.session_state.pending_text = None  # Reset pending text changes
        st.session_state.text_editor_key += 1  # Force text editor refresh
        return True
    except Exception as e:
        st.error(f"Error loading NCDN: {e}")
        return False

def load_nci(nci_path):
    """Load from .nci.json file."""
    try:
        with open(nci_path, 'r', encoding='utf-8') as f:
            nci_data = json.load(f)
        # Convert NCI back to NC format
        parsed = parser.from_nci(nci_data)
        st.session_state.lines = parsed.get('lines', [])
        st.session_state.current_file = nci_path
        st.session_state.modified = False
        st.session_state.line_view_modes = {}  # Reset per-line view modes
        st.session_state.collapsed_indices = set()  # Reset collapsed indices
        st.session_state.pending_text = None  # Reset pending text changes
        st.session_state.text_editor_key += 1  # Force text editor refresh
        return True
    except Exception as e:
        st.error(f"Error loading NCI: {e}")
        return False

# Main UI
st.title("📝 NormCode Inline Editor")
st.markdown("Minimal demo for editing .ncd and .ncn files with inline editing")

# File management section
st.sidebar.header("File Management")

# Get base path
base_path = Path(__file__).parent

# File input
file_option = st.sidebar.radio(
    "Choose action:",
    ["Load Example", "Load Custom Files", "Load from JSON", "Load from NCDN", "Load from NCI"]
)

if file_option == "Load Example":
    if st.sidebar.button("Load example.ncd/ncn"):
        ncd_path = str(base_path / "example.ncd")
        ncn_path = str(base_path / "example.ncn")
        if load_files(ncd_path, ncn_path):
            st.success("Loaded example files!")
            st.rerun()

elif file_option == "Load Custom Files":
    ncd_input = st.sidebar.text_input("NCD file path:", value="example.ncd")
    ncn_input = st.sidebar.text_input("NCN file path:", value="example.ncn")
    
    if st.sidebar.button("Load Files"):
        if load_files(ncd_input, ncn_input):
            st.success(f"Loaded {ncd_input} and {ncn_input}")
            st.rerun()

elif file_option == "Load from JSON":
    json_input = st.sidebar.text_input("JSON file path:", value="example.nc.json")
    
    if st.sidebar.button("Load JSON"):
        if os.path.exists(json_input):
            if load_json(json_input):
                st.success(f"Loaded {json_input}")
                st.rerun()
        else:
            st.error("File not found")

elif file_option == "Load from NCDN":
    ncdn_input = st.sidebar.text_input("NCDN file path:", value="example.ncdn")
    
    if st.sidebar.button("Load NCDN"):
        if os.path.exists(ncdn_input):
            if load_ncdn(ncdn_input):
                st.success(f"Loaded {ncdn_input}")
                st.rerun()
        else:
            st.error("File not found")

else:  # Load from NCI
    nci_input = st.sidebar.text_input("NCI file path:", value="example.nci.json")
    
    if st.sidebar.button("Load NCI"):
        if os.path.exists(nci_input):
            if load_nci(nci_input):
                st.success(f"Loaded {nci_input}")
                st.rerun()
        else:
            st.error("File not found")

# Export Paths Configuration
st.sidebar.divider()
st.sidebar.subheader("📁 Export Paths")
st.sidebar.caption("Configure default export paths (used in Export section)")

save_ncd_path = st.sidebar.text_input("NCD path:", value="output.ncd", key='sidebar_ncd_path')
st.session_state.save_ncd_path = save_ncd_path
save_ncn_path = st.sidebar.text_input("NCN path:", value="output.ncn", key='sidebar_ncn_path')
st.session_state.save_ncn_path = save_ncn_path
save_ncdn_path = st.sidebar.text_input("NCDN path:", value="output.ncdn", key='sidebar_ncdn_path')
st.session_state.save_ncdn_path = save_ncdn_path
save_json_path = st.sidebar.text_input("JSON path:", value="output.nc.json", key='sidebar_json_path')
st.session_state.save_json_path = save_json_path
save_nci_path = st.sidebar.text_input("NCI path:", value="output.nci.json", key='sidebar_nci_path')
st.session_state.save_nci_path = save_nci_path

st.sidebar.info("💡 Use the 💾 Export section below the editor to save files")

# Editor section
st.divider()

if not st.session_state.lines:
    st.info("👈 Load a file from the sidebar to start editing")
else:
    # Display modification status
    if st.session_state.modified:
        st.warning("⚠️ Unsaved changes")
    
    # Stats
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Total Lines", len(st.session_state.lines))
    with col_stat2:
        main_count = sum(1 for l in st.session_state.lines if l['type'] == 'main')
        st.metric("Main Lines", main_count)
    with col_stat3:
        comment_count = sum(1 for l in st.session_state.lines if l['type'] in ['comment', 'inline_comment'])
        st.metric("Comments", comment_count)
    with col_stat4:
        # Count visible lines based on all filters
        visible = 0
        for idx, l in enumerate(st.session_state.lines):
            line_mode = st.session_state.line_view_modes.get(idx, st.session_state.view_mode)
            line_flow = l.get('flow_index', '')
            line_type = l.get('type', '')
            
            # Check comment filter
            if not st.session_state.show_comments and line_type in ['comment', 'inline_comment']:
                continue
            
            # Check NCN mode filter
            if line_mode == 'ncn' and line_type in ['comment', 'inline_comment']:
                continue
            
            # Check collapse filter
            is_collapsed = False
            if line_flow:
                for collapsed_idx in st.session_state.collapsed_indices:
                    if line_flow.startswith(collapsed_idx + "."):
                        is_collapsed = True
                        break
            if is_collapsed:
                continue
            
            visible += 1
        
        st.metric("Visible", visible)
    
    st.divider()
    
    # Editor mode and view selector
    st.subheader("Inline Editor")
    
    # Editor mode toggle
    col_mode1, col_mode2 = st.columns([3, 9])
    with col_mode1:
        editor_mode = st.radio(
            "Editor Mode:",
            options=['line_by_line', 'pure_text'],
            format_func=lambda x: '📋 Line-by-Line' if x == 'line_by_line' else '📝 Pure Text',
            horizontal=True,
            key='editor_mode_selector'
        )
        if editor_mode != st.session_state.editor_mode:
            st.session_state.editor_mode = editor_mode
            st.session_state.pending_text = None  # Reset pending text when switching modes
            st.session_state.text_editor_key += 1  # Force text editor refresh
            st.rerun()
    
    with col_mode2:
        if st.session_state.editor_mode == 'pure_text':
            st.caption("💡 Pure text mode: Edit as continuous text with NCN annotations inline")
        else:
            st.caption("💡 Line-by-line mode: Individual editing controls per line")
    
    st.divider()
    
    # Display options in a cleaner layout
    with st.expander("⚙️ Display Options", expanded=True):
        # Different options based on editor mode
        if st.session_state.editor_mode == 'pure_text':
            # Pure Text Mode: Show/Hide Natural Language toggle
            st.markdown("**Pure Text Editor Options**")
            col_opt1, col_opt2 = st.columns([3, 9])
            
            with col_opt1:
                show_nl = st.checkbox(
                    "📖 Show Natural Language",
                    value=st.session_state.show_natural_language,
                    key='show_nl_checkbox',
                    help="Show/hide NCN annotations (|?{natural language}: ...)"
                )
                if show_nl != st.session_state.show_natural_language:
                    st.session_state.show_natural_language = show_nl
                    st.rerun()
            
            with col_opt2:
                st.caption("💡 Toggle to show/hide natural language annotations in the text editor")
            
            st.divider()
        
        else:
            # Line-by-Line Mode: Default view and bulk actions
            col_opt1, col_opt2, col_opt3 = st.columns([3, 3, 6])
            
            with col_opt1:
                st.markdown("**Default View**")
                view_mode = st.radio(
                    "Default View Mode:",
                    options=['ncd', 'ncn'],
                    format_func=lambda x: '📄 NCD' if x == 'ncd' else '📖 NCN',
                    horizontal=True,
                    key='view_mode_selector',
                    label_visibility="collapsed"
                )
                if view_mode != st.session_state.view_mode:
                    st.session_state.view_mode = view_mode
            
            with col_opt2:
                st.markdown("**Bulk Actions**")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("All NCD", help="Show all lines in NCD format", use_container_width=True):
                        st.session_state.line_view_modes = {idx: 'ncd' for idx in range(len(st.session_state.lines))}
                        st.rerun()
                with col_btn2:
                    if st.button("All NCN", help="Show all main lines in NCN format", use_container_width=True):
                        st.session_state.line_view_modes = {idx: 'ncn' for idx in range(len(st.session_state.lines))}
                        st.rerun()
            
            with col_opt3:
                st.caption("💡 Use 📄/📖 buttons on each line to toggle individually")
            
            st.divider()
        
        # Common options for both modes: Visibility and collapse controls
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            st.markdown("**Visibility**")
            # Toggle to show/hide comments
            show_comments = st.checkbox(
                "☑️ Show Comments",
                value=st.session_state.show_comments,
                key='show_comments_checkbox',
                help="Show/hide comment and metadata lines (?: /: ...:)"
            )
            if show_comments != st.session_state.show_comments:
                st.session_state.show_comments = show_comments
                st.rerun()
            
            # Show currently collapsed count
            if st.session_state.collapsed_indices:
                st.caption(f"🔒 {len(st.session_state.collapsed_indices)} section(s) collapsed")
                if st.button("🔄 Expand All"):
                    st.session_state.collapsed_indices = set()
                    st.rerun()
        
        with col_opt2:
            st.markdown("**Collapse Section**")
            # Input to collapse specific flow index
            collapse_input = st.text_input(
                "Flow index to collapse:",
                placeholder="e.g., 1.4",
                help="Enter flow index to collapse/expand",
                key='collapse_input',
                label_visibility="collapsed"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("➖ Collapse", use_container_width=True):
                    if collapse_input:
                        st.session_state.collapsed_indices.add(collapse_input)
                        st.rerun()
            with col_btn2:
                if st.button("➕ Expand", use_container_width=True):
                    if collapse_input and collapse_input in st.session_state.collapsed_indices:
                        st.session_state.collapsed_indices.remove(collapse_input)
                        st.rerun()
    
    st.divider()
    
    # Choose display mode
    if st.session_state.editor_mode == 'pure_text':
        # Pure text mode: single text area with NCN annotations and flow indices
        st.markdown("### Pure Text Editor")
        
        # Generate text with flow index prefixes (e.g., "1.2.3 │ content")
        source_text, visible_flow_indices, max_flow_len = get_visible_lines_with_flow_prefix(
            st.session_state.lines,
            st.session_state.show_comments,
            st.session_state.collapsed_indices,
            st.session_state.show_natural_language
        )
        
        # Store max_flow_len in session state for parsing
        st.session_state.max_flow_len = max_flow_len
        
        # Single text area with flow indices embedded at the start of each line
        new_text = st.text_area(
            "Edit content",
            value=source_text,
            height=500,
            key=f'pure_text_editor_{st.session_state.text_editor_key}',
            label_visibility="collapsed",
            help="Flow indices are shown for reference (flow_idx │ content). Edit freely - you can keep or remove them. Click Apply to refresh."
        )
        
        # Check for pending changes by comparing current widget value with source
        has_pending = new_text != source_text
        
        # Update pending_text state for tracking
        if has_pending:
            st.session_state.pending_text = new_text
        else:
            st.session_state.pending_text = None
        
        # Action buttons AFTER text area (so we can use has_pending correctly)
        col_action1, col_action2, col_action3 = st.columns([2, 2, 8])
        with col_action1:
            if st.button("🔄 Refresh", help="Discard edits and reload from current state", use_container_width=True):
                # Increment key to force text area to reset
                st.session_state.text_editor_key += 1
                st.session_state.pending_text = None
                st.rerun()
        with col_action2:
            apply_btn = st.button(
                "✅ Apply",
                help="Apply text changes to global state",
                use_container_width=True,
                disabled=not has_pending,
                type="primary" if has_pending else "secondary"
            )
            if apply_btn and has_pending:
                # Strip flow index prefixes before parsing
                content_only = strip_flow_prefix_from_text(new_text, st.session_state.max_flow_len)
                st.session_state.lines = update_lines_from_ncdn_text(
                    content_only,
                    st.session_state.lines,
                    st.session_state.show_comments,
                    st.session_state.collapsed_indices,
                    st.session_state.show_natural_language
                )
                st.session_state.modified = True
                st.session_state.pending_text = None
                st.session_state.text_editor_key += 1  # Reset editor with new content
                st.success("✅ Changes applied to global state!")
                st.rerun()
        with col_action3:
            if has_pending:
                st.warning("⚠️ You have unsaved edits. Click **Apply** to update and refresh flow indices.")
            else:
                st.caption("💡 Edit the text above, then click **Apply** to save changes and refresh flow indices")
        
        # Display format information
        st.caption("ℹ️ Flow indices shown as `flow_index │ content` for reference. You can edit freely - flow indices will refresh when you Apply changes.")
        
    else:
        # Line-by-line mode: individual controls
        st.markdown("### Line-by-Line Editor")
        
        # Add new line at top button
        col_top1, col_top2 = st.columns([2, 10])
        with col_top1:
            if st.button("➕ Add Line at Top", use_container_width=True):
                new_line = {
                    'flow_index': '1',
                    'type': 'main',
                    'depth': 0,
                    'nc_main': '',
                    'ncn_content': ''
                }
                st.session_state.lines.insert(0, new_line)
                st.session_state.modified = True
                st.rerun()
        with col_top2:
            st.caption("💡 Add a new line at the beginning of the document")
        
        st.divider()
        
        # Display each line with inline editing
        lines_to_delete = []  # Collect lines to delete after iteration
        
        for idx, line in enumerate(st.session_state.lines):
            flow_idx = line.get('flow_index', '')
            line_type = line.get('type', '')
            depth = line.get('depth', 0)
            
            # Get view mode for this line (per-line override or global default)
            line_view_mode = st.session_state.line_view_modes.get(idx, st.session_state.view_mode)
            
            # Filter 1: Hide comments if show_comments is False
            if not st.session_state.show_comments and line_type in ['comment', 'inline_comment']:
                continue
            
            # Filter 2: In NCN mode, skip comment and inline_comment lines
            if line_view_mode == 'ncn' and line_type in ['comment', 'inline_comment']:
                continue
            
            # Filter 3: Check if this line is under a collapsed flow index
            is_collapsed = False
            if flow_idx:
                for collapsed_idx in st.session_state.collapsed_indices:
                    if flow_idx.startswith(collapsed_idx + "."):
                        is_collapsed = True
                        break
            
            if is_collapsed:
                continue
            
            # Check if this line has children (for collapse button)
            has_children = False
            if flow_idx and line_type == 'main':
                for other_line in st.session_state.lines:
                    other_idx = other_line.get('flow_index', '')
                    if other_idx.startswith(flow_idx + "."):
                        has_children = True
                        break
            
            # Type indicator
            type_icons = {
                'main': '🔹',
                'comment': '💬',
                'inline_comment': '📝'
            }
            type_icon = type_icons.get(line_type, '')
            
            # View mode indicator for main lines
            view_icon = ""
            if line_type == 'main':
                view_icon = "📄" if line_view_mode == 'ncd' else "📖"
            
            # Create columns: flow_idx + type + buttons + content + actions
            col_flow, col_type, col_buttons, col_content, col_actions = st.columns([1.5, 0.5, 1.5, 5.5, 2])
            
            with col_flow:
                # Editable flow index
                new_flow_idx = st.text_input(
                    f"Flow {idx}",
                    value=flow_idx,
                    key=f"flow_{idx}",
                    label_visibility="collapsed",
                    placeholder="1.1"
                )
                if new_flow_idx != flow_idx:
                    st.session_state.lines = update_flow_index(st.session_state.lines, idx, new_flow_idx)
            
            with col_type:
                st.caption(f"{type_icon}{view_icon}")
            
            with col_buttons:
                # View toggle and collapse buttons
                buttons_needed = []
                if line_type == 'main':
                    buttons_needed.append('toggle')
                if has_children:
                    buttons_needed.append('collapse')
                
                if buttons_needed:
                    btn_cols = st.columns(len(buttons_needed))
                    btn_idx = 0
                    
                    if 'toggle' in buttons_needed:
                        with btn_cols[btn_idx]:
                            if st.button("🔄", key=f"toggle_{idx}", help=f"Switch to {'NCN' if line_view_mode == 'ncd' else 'NCD'}", use_container_width=True):
                                new_mode = 'ncn' if line_view_mode == 'ncd' else 'ncd'
                                st.session_state.line_view_modes[idx] = new_mode
                                st.rerun()
                        btn_idx += 1
                    
                    if 'collapse' in buttons_needed:
                        with btn_cols[btn_idx]:
                            is_currently_collapsed = flow_idx in st.session_state.collapsed_indices
                            collapse_label = "➕" if is_currently_collapsed else "➖"
                            if st.button(collapse_label, key=f"collapse_{idx}", help=f"{'Expand' if is_currently_collapsed else 'Collapse'}", use_container_width=True):
                                if is_currently_collapsed:
                                    st.session_state.collapsed_indices.remove(flow_idx)
                                else:
                                    st.session_state.collapsed_indices.add(flow_idx)
                                st.rerun()
            
            with col_content:
                # Determine what to edit based on line's view mode
                if line_view_mode == 'ncd':
                    # NCD mode: show nc_main or nc_comment
                    if 'nc_main' in line:
                        current_value = line['nc_main']
                        field_key = 'nc_main'
                    elif 'nc_comment' in line:
                        current_value = line['nc_comment']
                        field_key = 'nc_comment'
                    else:
                        current_value = ""
                        field_key = 'content'
                else:
                    # NCN mode: show ncn_content for main lines
                    if line_type == 'main':
                        current_value = line.get('ncn_content', '')
                        field_key = 'ncn_content'
                    else:
                        current_value = ""
                        field_key = 'ncn_content'
                
                # Editable text input with indentation
                indent = "    " * depth
                new_value = st.text_input(
                    f"Line {idx}",
                    value=current_value,
                    key=f"line_{idx}_{field_key}_{line_view_mode}",
                    label_visibility="collapsed",
                    placeholder=f"{indent}(empty)"
                )
                
                # Track changes
                if new_value != current_value:
                    line[field_key] = new_value
                    st.session_state.modified = True
                    
                    # Ensure the field exists in the line dict
                    if field_key == 'ncn_content' and field_key not in line:
                        line[field_key] = new_value
            
            with col_actions:
                # Add and delete buttons
                action_cols = st.columns(2)
                
                with action_cols[0]:
                    if st.button("➕", key=f"add_{idx}", help="Add line after this", use_container_width=True):
                        st.session_state.lines = add_line_after(st.session_state.lines, idx, line_type='main')
                        st.session_state.modified = True
                        st.rerun()
                
                with action_cols[1]:
                    # Delete with confirmation
                    if idx in st.session_state.delete_confirmations:
                        if st.button("⚠️ Confirm", key=f"confirm_delete_{idx}", help="Click again to confirm deletion", use_container_width=True, type="primary"):
                            lines_to_delete.append(idx)
                            st.session_state.delete_confirmations.discard(idx)
                            st.session_state.modified = True
                    else:
                        if st.button("🗑️", key=f"delete_{idx}", help="Delete this line", use_container_width=True):
                            st.session_state.delete_confirmations.add(idx)
                            st.rerun()
        
        # Delete lines after iteration (to avoid modifying list during iteration)
        if lines_to_delete:
            # Delete in reverse order to maintain indices
            for idx in sorted(lines_to_delete, reverse=True):
                st.session_state.lines = delete_line(st.session_state.lines, idx)
            st.rerun()

# Preview section
if st.session_state.lines:
    st.divider()
    
    with st.expander("🔍 Preview Output", expanded=False):
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📄 NCD Preview", 
            "📖 NCN Preview", 
            "📝 NCDN Preview",
            "📊 JSON Preview",
            "🔗 NCI Preview"
        ])
        
        parsed_data = {"lines": st.session_state.lines}
        serialized = parser.serialize(parsed_data)
        
        with tab1:
            st.code(serialized['ncd'], language="text")
            st.caption("Draft format (.ncd)")
        
        with tab2:
            st.code(serialized['ncn'], language="text")
            st.caption("Natural language format (.ncn)")
        
        with tab3:
            ncdn_output = parser.serialize_ncdn(parsed_data)
            st.code(ncdn_output, language="text")
            st.caption("Combined format (.ncdn) - NCD with inline NCN annotations")
        
        with tab4:
            st.json(st.session_state.lines[:5])  # Show first 5 lines
            st.caption(f"Showing first 5 of {len(st.session_state.lines)} lines")
        
        with tab5:
            nci_output = parser.to_nci(parsed_data)
            st.json(nci_output)
            st.caption(f"Inference format (.nci.json) - {len(nci_output)} inference group(s)")
    
    # Export section (after preview)
    st.divider()
    with st.expander("💾 Export to Files", expanded=False):
        st.markdown("**Save current state to files**")
        
        col_export1, col_export2, col_export3, col_export4 = st.columns(4)
        
        with col_export1:
            st.text_input("NCD path:", value=st.session_state.get('save_ncd_path', 'output.ncd'), key='export_ncd_path')
            if st.button("💾 Export .ncd", use_container_width=True):
                try:
                    parsed_data = {"lines": st.session_state.lines}
                    serialized = parser.serialize(parsed_data)
                    export_path = st.session_state.export_ncd_path
                    
                    os.makedirs(os.path.dirname(export_path) if os.path.dirname(export_path) else '.', exist_ok=True)
                    with open(export_path, 'w', encoding='utf-8') as f:
                        f.write(serialized['ncd'])
                    
                    st.success(f"✅ Exported {export_path}")
                    st.session_state.modified = False
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col_export2:
            st.text_input("NCN path:", value=st.session_state.get('save_ncn_path', 'output.ncn'), key='export_ncn_path')
            if st.button("💾 Export .ncn", use_container_width=True):
                try:
                    parsed_data = {"lines": st.session_state.lines}
                    serialized = parser.serialize(parsed_data)
                    export_path = st.session_state.export_ncn_path
                    
                    os.makedirs(os.path.dirname(export_path) if os.path.dirname(export_path) else '.', exist_ok=True)
                    with open(export_path, 'w', encoding='utf-8') as f:
                        f.write(serialized['ncn'])
                    
                    st.success(f"✅ Exported {export_path}")
                    st.session_state.modified = False
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col_export3:
            st.text_input("NCDN path:", value=st.session_state.get('save_ncdn_path', 'output.ncdn'), key='export_ncdn_path')
            if st.button("💾 Export .ncdn", use_container_width=True):
                try:
                    parsed_data = {"lines": st.session_state.lines}
                    ncdn_content = parser.serialize_ncdn(parsed_data)
                    export_path = st.session_state.export_ncdn_path
                    
                    os.makedirs(os.path.dirname(export_path) if os.path.dirname(export_path) else '.', exist_ok=True)
                    with open(export_path, 'w', encoding='utf-8') as f:
                        f.write(ncdn_content)
                    
                    st.success(f"✅ Exported {export_path}")
                    st.session_state.modified = False
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col_export4:
            st.text_input("JSON path:", value=st.session_state.get('save_json_path', 'output.nc.json'), key='export_json_path')
            if st.button("💾 Export .nc.json", use_container_width=True):
                try:
                    export_path = st.session_state.export_json_path
                    
                    os.makedirs(os.path.dirname(export_path) if os.path.dirname(export_path) else '.', exist_ok=True)
                    with open(export_path, 'w', encoding='utf-8') as f:
                        json.dump({"lines": st.session_state.lines}, f, indent=2, ensure_ascii=False)
                    
                    st.success(f"✅ Exported {export_path}")
                    st.session_state.modified = False
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Add NCI export in a new row
        st.divider()
        st.markdown("**Export Inference Format**")
        
        col_export_nci = st.columns([3, 9])[0]
        with col_export_nci:
            st.text_input("NCI path:", value=st.session_state.get('save_nci_path', 'output.nci.json'), key='export_nci_path')
            if st.button("💾 Export .nci.json", use_container_width=True):
                try:
                    parsed_data = {"lines": st.session_state.lines}
                    nci_output = parser.to_nci(parsed_data)
                    export_path = st.session_state.export_nci_path
                    
                    os.makedirs(os.path.dirname(export_path) if os.path.dirname(export_path) else '.', exist_ok=True)
                    with open(export_path, 'w', encoding='utf-8') as f:
                        json.dump(nci_output, f, indent=2, ensure_ascii=False)
                    
                    st.success(f"✅ Exported {export_path} ({len(nci_output)} inference group(s))")
                    st.session_state.modified = False
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        st.caption("ℹ️ NCI format identifies inference groups with function concepts (<=) and value concepts (<-)")

