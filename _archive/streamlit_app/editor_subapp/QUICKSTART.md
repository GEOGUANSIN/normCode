# Quick Start Guide

## Launch the Demo (3 Easy Steps)

### Step 1: Navigate to the Examples Directory

```bash
cd streamlit_app/examples
```

### Step 2: Run the Launcher

**Windows:**
```bash
python launch_demo.py
```
Or just double-click `launch_demo.bat`

**Mac/Linux:**
```bash
python launch_demo.py
```
Or:
```bash
chmod +x launch_demo.sh
./launch_demo.sh
```

### Step 3: Use the Editor

1. **Load Example Files**
   - In the sidebar, select "Load Example"
   - Click "Load example.ncd/ncn"

2. **Edit Lines**
   - Each line appears as an editable text field
   - Make your changes inline
   - Flow indices update automatically

3. **Save Your Work**
   - Enter output filenames in the sidebar
   - Click "💾 Save Files" for .ncd/.ncn
   - Click "💾 Save JSON" for .nc.json

## What You Get

- **🎭 Two Editor Modes**:
  - **📋 Line-by-Line**: Individual controls per line
  - **📝 Pure Text**: Single text area with NCN annotations inline
- **📝 Inline Editing**: Edit each line directly
- **🔄 Mixed View**: Toggle between NCD and NCN per line
- **👁️ Visibility Controls**: 
  - Hide/show comments with one click
  - Collapse/expand hierarchical sections
  - Focus on what matters
- **🔍 Live Preview**: See changes in real-time
- **💾 Multi-Format Save**: Export to .ncd, .ncn, or .nc.json
- **📊 Statistics**: Track line counts and visibility
- **🎯 Flow Indices**: Auto-calculated hierarchical positions

## Files Included

- `demo_editor.py` - Main Streamlit app
- `unified_parser.py` - Parser/serializer
- `update_format.py` - Format conversion and validation tool
- `launch_demo.py` - Python launcher
- `launch_demo.bat` - Windows launcher
- `launch_demo.sh` - Unix/Linux/Mac launcher
- `example.ncd` - Example draft file
- `example.ncn` - Example natural language file
- `example.ncdn` - Example hybrid format (NCD + NCN annotations)
- `example.nc.json` - Example JSON structure

## Troubleshooting

**Port already in use?**
The launcher uses port 8502. If that's busy, edit `launch_demo.py` and change the port number.

**Module not found?**
Make sure you're in the `streamlit_app/examples` directory when running.

**Can't find files?**
The example files should be in the same directory as the launcher.

## Quick Format Conversion

Need to convert or validate files? Use the command-line tool:

```bash
# Convert a file
python update_format.py convert example.ncd --to ncdn

# Validate files
python update_format.py validate example.ncd example.ncn

# Generate all companion formats
python update_format.py generate example.ncd --all
```

See help for more options:
```bash
python update_format.py --help
```

## Next Steps

See `README_DEMO.md` for detailed documentation and advanced features.

