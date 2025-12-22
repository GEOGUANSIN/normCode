# NormCode Files Editor Tab

## Overview

The NormCode Files Editor is a new tab in the Streamlit app that provides a sophisticated interface for editing `.ncd`, `.nc`, and `.ncn` files with bidirectional synchronization, manifest-based file linking, and version control.

## Features

### 1. **Project Management**
- Create new projects with manifest files
- Load existing projects from saved manifests
- Link related `.ncd`, `.nc`, and `.ncn` files together
- Save project configurations

### 2. **Multi-Format Editing**
- Edit `.ncd` (NormCode Draft) files with full syntax support
- Edit `.nc` (NormCode Formal) files
- Edit `.ncn` (NormCode Natural) files
- Switch between formats using tabs
- Track modifications for each file

### 3. **Syntax Highlighting**
- Color-coded syntax highlighting for each format
- Preview mode to see highlighted content
- Support for:
  - Operators (`<=`, `<-`, `::`, `&in`, etc.)
  - Concepts (`{}`, `[]`, `<>`)
  - Annotations (`?:`, `/:`, `...:`)
  - Flow indices and sequence types

### 4. **Bidirectional Format Conversion**
- Convert between any two formats:
  - `.ncd` ↔ `.nc`
  - `.ncd` ↔ `.ncn`
  - `.nc` ↔ `.ncn`
- Preview changes before applying
- View detailed diffs
- Warnings for lossy conversions

### 5. **Version Control**
- Automatic version snapshots on save
- View version history for each file
- Restore previous versions
- Diff between versions
- SQLite-based storage

## Architecture

### Core Components

1. **`streamlit_app/core/manifest.py`**
   - `ManifestManager` class for managing project manifests
   - Create, load, save, update, and delete manifests
   - Validates manifest structure

2. **`streamlit_app/core/parsers/`**
   - `ir.py`: Common intermediate representation (`NormCodeNode`)
   - `ncd_parser.py`: Parse/serialize `.ncd` format
   - `nc_parser.py`: Parse/serialize `.nc` format
   - `ncn_parser.py`: Parse/serialize `.ncn` format

3. **`streamlit_app/core/converters/`**
   - `format_converter.py`: Bidirectional format conversion
   - Uses parsers to convert between formats
   - Provides warnings for lossy conversions

4. **`streamlit_app/core/version_control.py`**
   - `VersionControl` class for version management
   - SQLite database storage
   - Snapshot, history, rollback, and diff functionality

5. **`streamlit_app/core/syntax_highlighter.py`**
   - `SyntaxHighlighter` class for syntax highlighting
   - HTML generation with inline styles
   - Format-specific highlighting rules

6. **`streamlit_app/tabs/normcode_editor_tab.py`**
   - Main UI component
   - Project management interface
   - File editors with tabs
   - Sync preview with diff viewer

## Usage

### Creating a New Project

1. Navigate to the "📝 NormCode Files" tab
2. Click "➕ Create New"
3. Enter a project name and optional description
4. Click "Create"
5. The manifest will be created with placeholder file paths

### Loading an Existing Project

1. Select a project from the dropdown
2. Click "Load Project"
3. Files will be loaded if they exist at the specified paths

### Editing Files

1. Use the file tabs to switch between `.ncd`, `.nc`, and `.ncn`
2. Edit content in the text area
3. Preview syntax highlighting in the expander
4. Click "💾 Save" to save changes and create a version snapshot

### Synchronizing Files

1. Make changes to one file (e.g., `.ncd`)
2. Click a sync button (e.g., "🔄 .ncd → .nc")
3. Review the preview with warnings and diff
4. Click "✅ Apply Changes" to update the target file
5. Save the target file when ready

### Version Control

1. Click "📜 View History" for any file
2. Browse previous versions with timestamps
3. Click "Restore" to load a previous version
4. Use the diff viewer to compare versions

## Data Storage

### Manifests
- Stored in: `streamlit_app/data/manifests/`
- Format: `{project_name}.json`
- Contains file paths and metadata

### Version History
- Stored in: `streamlit_app/data/normcode_versions.db` (SQLite)
- Schema:
  - `id`: Unique version ID
  - `file_path`: Path to file
  - `content`: File content snapshot
  - `timestamp`: When snapshot was created
  - `message`: Commit message
  - `hash`: SHA256 hash of content

## File Formats

### .ncd (NormCode Draft)
- Indentation-based hierarchy (4 spaces per level)
- Annotations: `?:`, `/:`, `...:`
- Operators: `<=`, `<-`, `:<:`
- Metadata: `| flow_index sequence_type`

### .nc (NormCode Formal)
- Line-based format
- Format: `flow_index.type|content`
- No annotations
- Machine-readable

### .ncn (NormCode Natural)
- Similar to `.ncd` but with natural language
- Simplified content
- Easier for human reading

## Integration

The NormCode Files editor is integrated into the main Streamlit app:

1. **`streamlit_app/app.py`**: Imports and renders the tab
2. **`streamlit_app/tabs/__init__.py`**: Exports the render function

## Future Enhancements

- Auto-complete for NormCode operators
- Visual graph view of flow structure
- Integration with translation pipeline (normtext → .ncd)
- Export to Python repository format (JSON)
- Collaborative editing with conflict resolution
- Real-time collaboration
- Import from existing files
- Batch operations

## Technical Notes

### Parser Complexity
The `.ncd` parser handles indentation-based parsing with care for whitespace preservation.

### Lossy Conversions
Some conversions lose information:
- `.ncd` → `.nc`: Loses annotations (`?:`, `/:`, `...:`)
- `.ncn` → `.nc`: Loses natural language nuances
- `.nc` → `.ncd`: May lose type details

The system provides warnings for these cases.

### Performance
- Large files (>10MB) may need optimization
- Consider streaming/chunking for very large files
- SQLite provides fast version retrieval

## Troubleshooting

### Files Not Loading
- Check that file paths in manifest are correct
- Ensure files exist at specified locations
- Try using absolute paths

### Sync Not Working
- Ensure source file has content
- Check console for error messages
- Verify file format is valid

### Version History Empty
- Save the file at least once to create first snapshot
- Check that database file exists at `data/normcode_versions.db`

## Support

For issues or questions, consult the main project documentation or review the source code in `streamlit_app/tabs/normcode_editor_tab.py`.

