<!-- 976edbab-46cb-46a0-9a17-b8cfa2221205 c4b69cb9-4bff-4fdf-944e-20f08c6c30e0 -->
# NormCode File Editor Tab

## Overview

Add a new "NormCode Files" tab to the existing Streamlit app that provides a sophisticated interface for editing .ncd (draft), .nc (formal), and .ncn (natural) files with bidirectional synchronization, manifest-based linking, and version control.

## Architecture

### 1. Manifest System

Create a JSON manifest format to link related NormCode files:

```json
{
  "project_name": "my_normcode_plan",
  "created": "2025-12-04T10:30:00",
  "files": {
    "draft": "path/to/file.ncd",
    "formal": "path/to/file.nc",
    "natural": "path/to/file.ncn"
  },
  "metadata": {
    "description": "Plan description",
    "version": "1.0"
  }
}
```

**Implementation**: [`streamlit_app/core/manifest.py`](streamlit_app/core/manifest.py)

- `ManifestManager` class with methods: `create()`, `load()`, `save()`, `update_file_path()`
- Validate manifest structure
- Store manifests in `streamlit_app/data/manifests/`

### 2. Format Parsers and Internal Representation

**Common IR Structure**:

```python
class NormCodeNode:
    flow_index: str  # e.g., "1.2.3"
    depth: int
    node_type: str  # inference, concept
    sequence_type: str  # imperative, grouping, etc.
    content: str
    annotations: dict  # {question, description, source_text}
    children: List[NormCodeNode]
```

**Parsers**:

- [`streamlit_app/core/parsers/ncd_parser.py`](streamlit_app/core/parsers/ncd_parser.py): Parse indented .ncd format
- [`streamlit_app/core/parsers/nc_parser.py`](streamlit_app/core/parsers/nc_parser.py): Parse line-based .nc format
- [`streamlit_app/core/parsers/ncn_parser.py`](streamlit_app/core/parsers/ncn_parser.py): Parse natural language .ncn format

Each parser implements:

- `parse(file_content: str) -> List[NormCodeNode]`
- `serialize(nodes: List[NormCodeNode]) -> str`

### 3. Bidirectional Converters

**Implementation**: [`streamlit_app/core/converters/format_converter.py`](streamlit_app/core/converters/format_converter.py)

```python
class FormatConverter:
    def ncd_to_nc(nodes: List[NormCodeNode]) -> str
    def nc_to_ncd(nodes: List[NormCodeNode]) -> str
    def ncd_to_ncn(nodes: List[NormCodeNode]) -> str
    def ncn_to_ncd(nodes: List[NormCodeNode]) -> str
    def nc_to_ncn(nodes: List[NormCodeNode]) -> str
    def ncn_to_nc(nodes: List[NormCodeNode]) -> str
```

**Conversion Strategy**:

- Parse source format to IR
- Apply format-specific transformations
- Serialize to target format
- Handle lossy conversions with warnings

### 4. Version Control System

**Implementation**: [`streamlit_app/core/version_control.py`](streamlit_app/core/version_control.py)

```python
class VersionControl:
    def save_snapshot(file_path: str, content: str, message: str) -> str
    def get_history(file_path: str) -> List[Version]
    def rollback(file_path: str, version_id: str) -> str
    def diff(file_path: str, version1: str, version2: str) -> str
```

**Storage**: SQLite database at `streamlit_app/data/normcode_versions.db`

- Schema: `versions(id, file_path, content, timestamp, message, hash)`
- Keep all versions for complete history
- Compute diffs using difflib

### 5. Syntax Highlighting

**Implementation**: [`streamlit_app/core/syntax_highlighter.py`](streamlit_app/core/syntax_highlighter.py)

Define highlighting rules for each format:

- **.ncd**: Operators (`<=`, `<-`), concepts (`{}`, `[]`, `<>`), annotations (`...:`, `?:`, `/:`), flow indices
- **.nc**: Line format, types, content
- **.ncn**: Natural language structure markers

Use Streamlit's code component with custom CSS for highlighting.

### 6. Main Tab Interface

**Implementation**: [`streamlit_app/tabs/normcode_editor_tab.py`](streamlit_app/tabs/normcode_editor_tab.py)

**Layout**:

```
┌─────────────────────────────────────────────────┐
│ Project Management                              │
│ [Load Manifest] [Create New] [Save Manifest]   │
├─────────────────────────────────────────────────┤
│ File Selector: [.ncd ▼] [.nc] [.ncn]          │
├─────────────────────────────────────────────────┤
│                                                 │
│  Editor Area (syntax-highlighted)              │
│  - Line numbers                                │
│  - Indentation guides (.ncd)                   │
│  - Auto-complete (future)                      │
│                                                 │
├─────────────────────────────────────────────────┤
│ Actions:                                        │
│ [Save] [Sync to .nc] [Sync to .ncn]           │
│ [View History] [Rollback] [Show Diff]         │
├─────────────────────────────────────────────────┤
│ Sync Preview (when syncing):                   │
│ Shows side-by-side diff before applying        │
│ [Apply Changes] [Cancel]                       │
└─────────────────────────────────────────────────┘
```

**Key Features**:

1. **Project Panel**:

   - Load existing manifests from dropdown
   - Create new project (prompts for file paths)
   - Display current project metadata

2. **File Tabs**:

   - Switch between .ncd, .nc, .ncn views
   - Each has its own editor instance
   - Show file modification status

3. **Editor Component**:

   - Use `st.text_area` with syntax highlighting
   - Line numbers in left margin
   - Indentation visualization for .ncd

4. **Sync Panel**:

   - Manual sync buttons (e.g., "Sync .ncd → .nc")
   - Preview changes before applying
   - Show warnings for lossy conversions

5. **Version Control Panel**:

   - View commit history
   - Diff viewer (side-by-side or unified)
   - Rollback to previous versions

### 7. Integration with Streamlit App

**Update**: [`streamlit_app/app.py`](streamlit_app/app.py)

Add new tab:

```python
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🚀 Execute", "📊 Results", "📜 History", 
    "🧪 Sandbox", "🎨 Paradigms", "📝 NormCode Files", "📖 Help"
])

with tab6:
    render_normcode_editor_tab()
```

**Update**: [`streamlit_app/tabs/__init__.py`](streamlit_app/tabs/__init__.py)

Export new tab:

```python
from .normcode_editor_tab import render_normcode_editor_tab
```

### 8. File Structure

```
streamlit_app/
├── app.py (update to add new tab)
├── tabs/
│   ├── __init__.py (export new tab)
│   └── normcode_editor_tab.py (main UI)
├── core/
│   ├── manifest.py (manifest management)
│   ├── version_control.py (version system)
│   ├── syntax_highlighter.py (highlighting)
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── ncd_parser.py
│   │   ├── nc_parser.py
│   │   └── ncn_parser.py
│   └── converters/
│       ├── __init__.py
│       └── format_converter.py
└── data/
    ├── manifests/ (project manifests)
    └── normcode_versions.db (version history)
```

## Implementation Phases

### Phase 1: Core Infrastructure (Files 1-3)

1. Create manifest system
2. Implement parsers for .ncd, .nc, .ncn
3. Build common IR and basic converters

### Phase 2: Editor UI (Files 4-5)

4. Create main tab interface
5. Add syntax highlighting
6. Implement file loading/saving

### Phase 3: Sync & Version Control (Files 6-7)

7. Add version control system
8. Implement sync preview
9. Add diff viewer

### Phase 4: Polish (File 8)

10. Error handling and validation
11. User feedback and warnings
12. Documentation and help text

## Technical Considerations

1. **Parser Complexity**: .ncd indentation-based parsing requires careful handling of whitespace
2. **Sync Conflicts**: Lossy conversions (e.g., .ncn → .nc loses some detail) need clear warnings
3. **Performance**: Large files may need streaming/chunking for editor
4. **State Management**: Use Streamlit session state for current edits, unsaved changes
5. **File Locking**: Prevent concurrent edits if manifest is shared

## Future Enhancements

- Auto-complete for NormCode operators
- Visual graph view of flow structure
- Integration with translation pipeline (normtext → .ncd)
- Export to Python repository format (JSON)
- Collaborative editing with conflict resolution

### To-dos

- [ ] Create manifest.py with ManifestManager class for linking files
- [ ] Implement parsers for .ncd, .nc, .ncn formats with IR
- [ ] Build bidirectional format converters using IR
- [ ] Implement version control system with SQLite backend
- [ ] Create syntax highlighter for each format
- [ ] Build main editor tab with file selector and editor
- [ ] Add sync preview with diff viewer
- [ ] Integrate new tab into existing Streamlit app