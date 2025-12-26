# NormCode Inline Editor Demo

A minimal Streamlit app for editing `.ncd` and `.ncn` files with inline editing capabilities.

## Files

1. **`unified_parser.py`** - Parser and serializer for NormCode files
   - Parses .ncd and .ncn formats together
   - Assigns flow indices automatically
   - Serializes to .ncd, .ncn, .ncdn, and .nc.json
   - Round-trip consistency verified
   - `.ncdn` format: Hybrid format showing NCD with NCN annotations inline

2. **`demo_editor.py`** - Streamlit inline editor
   - Load .ncd, .ncn, .ncdn, or .nc.json files
   - Two editing modes: Line-by-Line and Pure Text
   - Save to any format (.ncd, .ncn, .ncdn, .nc.json)
   - Mixed view: Toggle NCD/NCN per line
   - Visibility controls: Hide comments, collapse sections
   - Live preview of all formats

3. **`update_format.py`** - Format conversion and validation tool
   - Convert between all NormCode formats
   - Batch process multiple files
   - Validate format consistency
   - Generate companion files automatically
   - Command-line interface for automation

## Quick Start

### 1. Run the Demo

**Option A: Using the Launcher (Recommended)**

```bash
# Navigate to examples directory
cd streamlit_app/examples

# Run the launcher
python launch_demo.py
```

Or on Windows, double-click `launch_demo.bat`

**Option B: Direct Streamlit Command**

```bash
cd streamlit_app/examples
streamlit run demo_editor.py
```

### 2. Load Example Files

- Click "Load Example" in the sidebar
- Click "Load example.ncd/ncn"
- The example files will be parsed and displayed

### 3. Edit Lines

- Each line appears as an editable text field
- Flow indices are shown on the left
- Line types (Main, Comment, Meta) are indicated
- Changes are tracked (warning appears when modified)

### 4. Save Your Work

**Save as .ncd and .ncn:**
- Enter output paths in sidebar
- Click "💾 Save Files"
- Both formats are generated from the current state

**Save as .nc.json:**
- Enter output path in sidebar
- Click "💾 Save JSON"
- JSON structure is saved

## Features

### Editor Modes

**📋 Line-by-Line Mode:**
- Individual text input for each line
- Per-line controls (toggle NCD/NCN, collapse/expand)
- Precise line-by-line editing
- Flow indices and type indicators visible

**📝 Pure Text Mode:**
- Single text area showing all visible lines
- NCD content with optional inline NCN annotations
- Format: Each main line followed by `|?{natural language}: <NCN content>`
- **Display Options for Pure Text:**
  - 📖 Show Natural Language: Toggle NCN annotations on/off
  - When enabled: Shows NCDN format (NCD + inline NCN)
  - When disabled: Shows NCD only
- Select and copy text across multiple lines
- See both formats together at a glance (when natural language enabled)
- Edit as continuous text
- Hidden lines preserved (comments, collapsed sections)
- Perfect for reading and understanding both technical and natural language

Toggle between modes with the radio buttons at the top.

### Load Options

1. **Load Example** - Quick load of example.ncd/ncn
2. **Load Custom Files** - Specify custom .ncd and .ncn paths
3. **Load from JSON** - Load from .nc.json file

### Inline Editing

- **Mixed View Mode**: Switch between NCD and NCN on a per-line basis
  - **Default View**: Set global default (NCD or NCN)
  - **Per-Line Toggle**: Click 📄 or 📖 button to switch individual lines
  - **Bulk Actions**: "All NCD" or "All NCN" buttons to set all at once
  - **📄 NCD Mode**: Edit draft format (shows operators and syntax)
  - **📖 NCN Mode**: Edit natural language format (readable descriptions)
- **Flow Index**: Shows hierarchical position (e.g., "1.2.3")
- **Type Indicator**: Main (🔹), Comment (💬), or Meta (📝)
- **Content Field**: Inline editable text input
- **Smart Display**: Content adjusts based on each line's view mode
- **Comment Handling**: Comments/metadata hidden in NCN mode for cleaner view

### Preview

- **NCD Preview**: See reconstructed .ncd format
- **NCN Preview**: See reconstructed .ncn format
- **JSON Preview**: See internal JSON structure

### Visibility Controls

- **Show Comments Toggle**: Hide/show all comment and metadata lines
  - Useful for focusing on core concepts
  - Comments remain in the data, just hidden from view
- **Collapse/Expand**: Hierarchical line collapsing
  - **Per-Line Buttons**: ➕/➖ next to lines with children
  - **Manual Input**: Type flow index (e.g., "1.4") and click Collapse
  - **Expand All**: Clear all collapsed sections at once
  - Collapsed lines are hidden but preserved in the data

### Statistics

- **Total Lines**: Count of all lines in the document
- **Main Lines**: Count of concept lines (<=, <-, :<:)
- **Comments**: Count of annotation/comment lines
- **Visible**: Count of currently visible lines (after all filters)

## Example Workflows

### Workflow 1: Mixed View Editing

1. Load files with both NCD and NCN content
2. Set default view to NCD
3. Toggle specific lines to NCN for natural language editing
4. Keep technical lines (with operators) in NCD
5. Keep descriptive lines in NCN for readability
6. Save to update both formats

**Use Case**: Edit complex technical concepts in NCD while keeping explanations in NCN for better readability.

### Workflow 3: Focus Mode with Collapsed Sections

1. Load a large file with many nested levels
2. Click ➖ next to high-level lines to collapse their children
3. Or type "1.4" and click "Collapse" to hide all 1.4.x lines
4. Uncheck "Show Comments" to hide annotations
5. Focus on editing visible top-level concepts
6. Click ➕ or "Expand All" when ready to see details
7. Save (all hidden content is preserved)

**Use Case**: Work on large files by focusing on specific sections while hiding irrelevant details.

### Workflow 4: Pure Text Mode with .ncdn

1. Load `.ncd` and `.ncn` files (or load existing `.ncdn`)
2. Switch to **Pure Text** mode
3. View NCD and NCN together in one text area:
   ```
   :<:({result}) | 1. assigning
       |?{natural language}: :<: The result is calculated.
   ```
4. Edit the text directly - modify either NCD or NCN content
5. Adjust visibility/filters in Display Options
6. Click **🔄 Refresh Text** to update the view
7. Preview output in different formats
8. Use **💾 Export** section to save files

**Use Case**: Work with both technical and natural formats simultaneously. Perfect for reviewing or translating code while seeing both representations together.

## Workflow Summary

The app follows a clear **Edit → Preview → Export** workflow:

1. **Edit**: Make changes in Line-by-Line or Pure Text mode
2. **Preview**: See output in all formats (NCD, NCN, NCDN, JSON)
3. **Export**: Save to files in your preferred format(s)

### Workflow 2: Create a new .ncd file

```normcode
:<:({result}) | 1. assigning
    ?: What is the result?
    <= $.({number})
    <- {number a} | 1.1. imperative
        /: The first number
```

### 2. Create corresponding .ncn file

```normcode
:<: The result is calculated.
    <= This is accomplished by a defined method.
    <- The first number is number a.
```

### 3. Load and edit

- Load both files
- Edit content inline
- Add/modify lines
- Preview changes

### 4. Export

- Save as .ncd/.ncn for text files
- Save as .nc.json for structured data

## File Formats

### .ncd (NormCode Draft)
- Indentation-based (4 spaces)
- Operators: `<=`, `<-`, `:<:`
- Comments: `?:`, `/:`, `...:`
- Metadata: `| flow_index sequence_type`

### .ncn (NormCode Natural)
- Similar structure to .ncd
- Natural language descriptions
- Same operators but readable content

### .ncdn (NormCode Draft + Natural)
- Hybrid format combining NCD and NCN
- NCD lines with inline NCN annotations
- Format: Each main line optionally followed by:
  ```
  <NCD line> | <metadata>
      |?{natural language}: <NCN content>
  ```
- Perfect for editing both formats in one view
- Easily convert to .ncd, .ncn, or .nc.json
- Example:
  ```
  :<:({result}) | 1. assigning
      |?{natural language}: :<: The result is calculated.
  ```

### .nc.json
- JSON array of line objects
- Each object has:
  - `flow_index`: Position in hierarchy
  - `type`: "main", "comment", or "inline_comment"
  - `depth`: Indentation level
  - `nc_main` or `nc_comment`: Content
  - `ncn_content`: Natural language (optional)

## Architecture

```
demo_editor.py
├── Load files (.ncd, .ncn, .ncdn, .nc.json, or .nci.json)
├── Parse with unified_parser.py
├── Display as inline editable fields
├── Track modifications
└── Serialize back to any format

unified_parser.py
├── assign_flow_indices()
│   └── Calculate hierarchical indices
├── parse()
│   └── Combine .ncd and .ncn
├── serialize()
│   └── Generate .ncd and .ncn from JSON
├── serialize_ncdn()
│   └── Generate .ncdn format
├── parse_ncdn()
│   └── Parse .ncdn format
├── to_nci()
│   └── Convert to inference format
└── from_nci()
    └── Convert from inference format

update_format.py (CLI Tool)
├── convert_file()
│   └── Convert between formats
├── validate_files()
│   └── Check format consistency
├── batch_convert()
│   └── Process multiple files
└── generate_companions()
    └── Create companion files
```

## Tips

1. **Start Small**: Begin with the example files to understand the structure
2. **Check Flow Indices**: They auto-update based on line hierarchy
3. **Use Preview**: Check the preview before saving
4. **Save Often**: Use both file and JSON formats for backup
5. **NCN Optional**: You can work with just .ncd if needed

## Limitations

- No visual hierarchy tree (lines are flat list)
- No drag-and-drop reordering
- No syntax highlighting in editor (only in preview)
- No undo/redo (use version control externally)

## Next Steps

- Add line insertion/deletion buttons
- Implement drag-and-drop reordering
- Add syntax highlighting to editor fields
- Create visual tree view
- Add validation and error checking

## Format Conversion Tool

The `update_format.py` script provides powerful command-line tools for batch processing and format management.

### Convert Single File

```bash
# Convert .ncd to .ncdn format
python update_format.py convert example.ncd --to ncdn

# Convert to .nci.json (inference format)
python update_format.py convert example.ncd --to nci.json

# Specify custom output path
python update_format.py convert input.ncd --to ncdn --output custom_output.ncdn
```

### Validate Files

```bash
# Validate a single .ncd file
python update_format.py validate example.ncd

# Validate .ncd with companion .ncn
python update_format.py validate example.ncd example.ncn
```

Validation checks:
- Required field presence
- Flow index consistency
- Depth level validation
- Round-trip conversion integrity

### Batch Convert Directory

```bash
# Convert all .ncd files in directory to .ncdn
python update_format.py batch-convert ./files --from ncd --to ncdn

# Recursive conversion (includes subdirectories)
python update_format.py batch-convert ./project --from ncd --to ncdn --recursive

# Convert .ncdn back to .nc.json
python update_format.py batch-convert ./files --from ncdn --to nc.json
```

### Generate Companion Files

```bash
# Generate all companion formats
python update_format.py generate example.ncd --all

# Generate specific formats
python update_format.py generate example.ncd --ncn --json
python update_format.py generate example.ncd --ncdn --nci
```

Supported formats:
- `--ncn` - Natural language format
- `--json` - JSON structure (.nc.json)
- `--ncdn` - Hybrid format with inline annotations
- `--nci` - Inference format (.nci.json)
- `--all` - All of the above

### Use Cases

**Workflow 1: Project Migration**
```bash
# Convert entire project to .ncdn format for easier editing
python update_format.py batch-convert ./normcode_project --from ncd --to ncdn --recursive
```

**Workflow 2: Format Validation**
```bash
# Validate all .ncd files before committing
for file in *.ncd; do
    python update_format.py validate "$file"
done
```

**Workflow 3: Generate Missing Companions**
```bash
# You have .ncd files but missing .ncn
python update_format.py generate example.ncd --ncn
```

## Troubleshooting

**Files not loading:**
- Check file paths are correct
- Ensure files exist in the specified location
- Try absolute paths if relative paths fail
- Use `update_format.py validate` to check format issues

**Changes not saving:**
- Check you have write permissions
- Verify output directory exists
- Look for error messages in the app

**Flow indices wrong:**
- Flow indices are auto-calculated
- They depend on indentation depth
- Check your depth values are correct
- Use validation tool to identify issues

**Format conversion errors:**
- Run `python update_format.py validate` first
- Check that input file is not corrupted
- Ensure all required fields are present
- Look for encoding issues (use UTF-8)

