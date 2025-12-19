# Editor and Format Tools

**Interactive editor and command-line utilities for working with NormCode files.**

---

## Overview

This document covers the tools available for creating, editing, converting, and validating NormCode files across all formats.

**Available Tools**:
1. **Interactive Inline Editor** - Streamlit web app for visual editing
2. **Format Conversion Tool** - CLI for batch format conversion
3. **Validation Tools** - Check format consistency

---

## The Format Ecosystem

### All NormCode Formats

| Format | Extension | Purpose | Audience |
|--------|-----------|---------|----------|
| **Draft** | `.ncds` | Easy authoring | Plan writers |
| **Formal** | `.ncd` | Rigorous syntax | Compiler intermediate |
| **Natural** | `.ncn` | Readable companion | Stakeholder review |
| **Hybrid** | `.ncdn` | NCD + NCN together | Editor, visual review |
| **Structured JSON** | `.nc.json` | Parsed structure | Tooling, analysis |
| **Inference JSON** | `.nci.json` | Inference format | Compiler intermediate |
| **Concept Repo** | `.concept.json` | Executable concepts | Orchestrator |
| **Inference Repo** | `.inference.json` | Executable inferences | Orchestrator |

### Format Relationships

```
.ncds (draft) ─────formalize────→ .ncd (formal)
                                     ↓
                                 .ncn (companion)
                                     ↓
                              .ncdn (hybrid)
                                     ↓
                              .nc.json (structure)
                                     ↓
                              .nci.json (inferences)
                                     ↓
                    .concept.json + .inference.json (executable)
```

---

## Tool 1: Interactive Inline Editor

### Overview

**Streamlit web application** for editing NormCode files with inline editing capabilities.

**Location**: `streamlit_app/examples/`

**Files**:
- `demo_editor.py` - Main editor app
- `unified_parser.py` - Parser and serializer
- `launch_demo.py` - Launcher script

### Quick Start

**Option A: Using Launcher (Recommended)**
```bash
cd streamlit_app/examples
python launch_demo.py
```

**Option B: Direct Command**
```bash
cd streamlit_app/examples
streamlit run demo_editor.py
```

**On Windows**: Double-click `launch_demo.bat`

### Features

#### Two Editing Modes

**📋 Line-by-Line Mode**:
- Individual text input for each line
- Per-line controls (toggle NCD/NCN, collapse/expand)
- Precise line-by-line editing
- Flow indices and type indicators visible

**📝 Pure Text Mode**:
- Single text area showing all visible lines
- NCD content with optional inline NCN annotations
- Select and copy across multiple lines
- Perfect for reading both formats together

**Toggle** between modes with radio buttons at the top.

#### Load Options

1. **Load Example** - Quick load of example.ncd/ncn
2. **Load Custom Files** - Specify custom .ncd and .ncn paths
3. **Load from JSON** - Load from .nc.json file
4. **Load from NCDN** - Load from hybrid .ncdn file

#### Mixed View Mode (Line-by-Line)

**Switch between NCD and NCN on a per-line basis**:

- **Default View**: Set global default (NCD or NCN)
- **Per-Line Toggle**: Click 📄 or 📖 button to switch individual lines
  - **📄 NCD Mode**: Edit draft format (shows operators and syntax)
  - **📖 NCN Mode**: Edit natural language format (readable descriptions)
- **Bulk Actions**: "All NCD" or "All NCN" buttons to set all at once

**Use Case**: Edit technical syntax in NCD while keeping explanations in NCN for better readability.

#### Visibility Controls

**Show Comments Toggle**:
- Hide/show all comment and metadata lines
- Useful for focusing on core concepts
- Comments remain in data, just hidden from view

**Collapse/Expand**:
- **Per-Line Buttons**: ➕/➖ next to lines with children
- **Manual Input**: Type flow index (e.g., "1.4") and click Collapse
- **Expand All**: Clear all collapsed sections at once
- Collapsed lines hidden but preserved

**Use Case**: Focus on specific sections of large files while hiding irrelevant details.

#### Statistics Display

- **Total Lines**: Count of all lines in document
- **Main Lines**: Count of concept lines (<=, <-, :<:)
- **Comments**: Count of annotation/comment lines
- **Visible**: Count after all filters applied

#### Preview Sections

View output in different formats:
- **NCD Preview**: Reconstructed .ncd format
- **NCN Preview**: Reconstructed .ncn format
- **JSON Preview**: Internal JSON structure

#### Export Options

**Save as .ncd and .ncn**:
1. Enter output paths in sidebar
2. Click "💾 Save Files"
3. Both formats generated from current state

**Save as .nc.json**:
1. Enter output path
2. Click "💾 Save JSON"
3. JSON structure saved

### Example Workflows

#### Workflow 1: Mixed View Editing

```
1. Load files with both NCD and NCN content
2. Set default view to NCD
3. Toggle specific lines to NCN for natural language editing
4. Keep technical lines (with operators) in NCD
5. Keep descriptive lines in NCN for readability
6. Save to update both formats
```

**Use Case**: Edit complex technical concepts in NCD while keeping explanations in NCN.

#### Workflow 2: Focus Mode with Collapsed Sections

```
1. Load a large file with many nested levels
2. Click ➖ next to high-level lines to collapse children
3. Or type "1.4" and click "Collapse" to hide all 1.4.x lines
4. Uncheck "Show Comments" to hide annotations
5. Focus on editing visible top-level concepts
6. Click ➕ or "Expand All" when ready to see details
7. Save (all hidden content preserved)
```

**Use Case**: Work on large files by focusing on specific sections.

#### Workflow 3: Pure Text Mode with NCDN

```
1. Load .ncd and .ncn files (or existing .ncdn)
2. Switch to Pure Text mode
3. View NCD and NCN together in one text area
4. Edit directly - modify either NCD or NCN content
5. Click "🔄 Refresh Text" to update view
6. Preview output in different formats
7. Export to any format
```

**Use Case**: Work with both technical and natural formats simultaneously.

### File Format Support

**Load**:
- `.ncd` (formal syntax)
- `.ncn` (natural language companion)
- `.ncdn` (hybrid format)
- `.nc.json` (structured JSON)

**Export**:
- `.ncd` + `.ncn` (separate files)
- `.ncdn` (hybrid with inline annotations)
- `.nc.json` (structured JSON)
- `.nci.json` (inference format)

---

## Tool 2: Format Conversion CLI

### Overview

**Command-line utility** for batch format conversion and validation.

**Location**: `streamlit_app/examples/update_format.py`

### Installation

No installation needed if Python 3.7+ is available:
```bash
cd streamlit_app/examples
python update_format.py --help
```

### Commands

#### Convert Single File

**Basic conversion**:
```bash
# Convert .ncd to .ncdn format
python update_format.py convert example.ncd --to ncdn

# Convert to .nci.json (inference format)
python update_format.py convert example.ncd --to nci.json
```

**With custom output**:
```bash
python update_format.py convert input.ncd --to ncdn --output custom_output.ncdn
```

**Supported target formats**: `ncd`, `ncn`, `ncdn`, `nc.json`, `nci.json`

#### Validate Files

**Single file**:
```bash
python update_format.py validate example.ncd
```

**With companion**:
```bash
python update_format.py validate example.ncd example.ncn
```

**Validation checks**:
- Required field presence
- Flow index consistency
- Depth level validation
- Round-trip conversion integrity

#### Batch Convert Directory

**Convert all files in directory**:
```bash
# Convert all .ncd files to .ncdn
python update_format.py batch-convert ./files --from ncd --to ncdn

# Recursive (includes subdirectories)
python update_format.py batch-convert ./project --from ncd --to ncdn --recursive
```

**Supported conversions**:
- `.ncd` → `.ncdn`, `.nc.json`, `.nci.json`
- `.ncdn` → `.ncd`, `.ncn`, `.nc.json`
- `.nc.json` → `.ncd`, `.ncdn`

#### Generate Companion Files

**Generate all formats**:
```bash
python update_format.py generate example.ncd --all
```

**Generate specific formats**:
```bash
# Just NCN and JSON
python update_format.py generate example.ncd --ncn --json

# Just NCDN and NCI
python update_format.py generate example.ncd --ncdn --nci
```

**Available options**:
- `--ncn` - Natural language format
- `--json` - JSON structure (.nc.json)
- `--ncdn` - Hybrid format with inline annotations
- `--nci` - Inference format (.nci.json)
- `--all` - All of the above

### Example Use Cases

#### Use Case 1: Project Migration

**Scenario**: Convert entire project to .ncdn format for easier editing.

**Command**:
```bash
python update_format.py batch-convert ./normcode_project --from ncd --to ncdn --recursive
```

**Result**: All `.ncd` files converted to `.ncdn` throughout the project tree.

#### Use Case 2: Format Validation

**Scenario**: Validate all .ncd files before committing.

**Bash script**:
```bash
for file in *.ncd; do
    python update_format.py validate "$file"
done
```

**PowerShell script**:
```powershell
Get-ChildItem *.ncd | ForEach-Object {
    python update_format.py validate $_.FullName
}
```

#### Use Case 3: Generate Missing Companions

**Scenario**: You have .ncd files but missing .ncn.

**Command**:
```bash
python update_format.py generate example.ncd --ncn
```

**Result**: `example.ncn` created alongside `example.ncd`.

---

## Tool 3: Validation

### What Gets Validated

**Structural Validation**:
- All required fields present
- Flow indices unique and hierarchical
- Indentation consistent with depth
- Markers correctly used (`<-`, `<=`, `<*`)

**Semantic Validation**:
- Concept types match usage
- Operators have required modifiers
- Value bindings are sequential
- References are resolvable

**Round-Trip Validation**:
- Convert to JSON and back
- Ensure no data loss
- Verify formatting preserved

### Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| **Duplicate flow index** | Two lines same index | Re-run formalization |
| **Invalid depth** | Indentation doesn't match tree | Fix indentation |
| **Missing field** | Required JSON field absent | Add missing annotation |
| **Type mismatch** | Concept type inconsistent | Fix semantic type |
| **Orphaned concept** | No connection to tree | Add parent inference |

### Validation in Editor

The editor provides **live validation**:
- Red highlights on syntax errors
- Warnings on missing fields
- Flow index consistency checks
- Preview validates on-the-fly

---

## Format Conversion Examples

### Example 1: .ncd → .ncdn

**Purpose**: Create hybrid format for easier review.

**Command**:
```bash
python update_format.py convert plan.ncd --to ncdn
```

**Input (.ncd)**:
```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(calculate) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {input} | ?{flow_index}: 1.2
```

**Output (.ncdn)**:
```ncdn
:<:{result} | ?{flow_index}: 1
    |?{natural language}: :<: The result is calculated.
    <= ::(calculate) | ?{flow_index}: 1.1 | ?{sequence}: imperative
        |?{natural language}: <= This is done by the calculate method.
    <- {input} | ?{flow_index}: 1.2
        |?{natural language}: <- The input is provided.
```

### Example 2: .ncdn → .ncd + .ncn

**Purpose**: Extract separate files from hybrid format.

**Command**:
```bash
python update_format.py convert plan.ncdn --to ncd
```

**Result**: Creates both `plan.ncd` and `plan.ncn`.

### Example 3: .ncd → .nci.json

**Purpose**: Generate inference structure for analysis.

**Command**:
```bash
python update_format.py convert plan.ncd --to nci.json
```

**Output**: Structured inference JSON with concept_to_infer, function_concept, value_concepts.

---

## Automation Scripts

### Pre-Commit Validation

**File**: `pre-commit.sh`
```bash
#!/bin/bash
echo "🔍 Validating NormCode files..."
failed=0

for file in $(find . -name "*.ncd" -o -name "*.ncdn"); do
    if ! python update_format.py validate "$file" 2>/dev/null; then
        echo "❌ Failed: $file"
        failed=$((failed + 1))
    else
        echo "✅ Valid: $file"
    fi
done

if [ $failed -eq 0 ]; then
    echo "✅ All files valid!"
    exit 0
else
    echo "❌ $failed file(s) failed validation."
    exit 1
fi
```

### Watch and Auto-Convert

**File**: `watch_convert.py`
```python
#!/usr/bin/env python
"""Watch directory and auto-convert .ncd files to .ncdn."""
import time, os
from pathlib import Path
from update_format import FormatUpdater

def watch_and_convert(directory='.', interval=2):
    updater = FormatUpdater()
    known_files = {}
    
    print(f"👀 Watching {directory} for .ncd changes...")
    
    while True:
        time.sleep(interval)
        for ncd_file in Path(directory).glob('*.ncd'):
            mod_time = os.path.getmtime(ncd_file)
            if str(ncd_file) not in known_files or known_files[str(ncd_file)] < mod_time:
                print(f"🔄 Converting: {ncd_file}")
                updater.convert_file(str(ncd_file), 'ncdn')
                known_files[str(ncd_file)] = mod_time

if __name__ == '__main__':
    watch_and_convert()
```

### Batch Sync Script

**File**: `sync_formats.py`
```python
#!/usr/bin/env python
"""Generate all companion formats for .ncd files."""
from pathlib import Path
from update_format import FormatUpdater

def sync_all_formats(directory='.', recursive=False):
    updater = FormatUpdater()
    pattern = '**/*.ncd' if recursive else '*.ncd'
    
    for ncd_file in Path(directory).glob(pattern):
        print(f"\n📄 Processing: {ncd_file}")
        updater.generate_companions(
            str(ncd_file),
            generate_ncn=True,
            generate_json=True,
            generate_ncdn=True,
            generate_nci=True
        )
        print(f"  ✅ Done")

if __name__ == '__main__':
    import sys
    recursive = '--recursive' in sys.argv
    sync_all_formats('.', recursive)
```

---

## Troubleshooting

### Files Not Loading

**Problem**: Editor can't load files.

**Solutions**:
- Check file paths are correct
- Ensure files exist
- Try absolute paths
- Use `validate` command to check format

### Changes Not Saving

**Problem**: Edits not persisting.

**Solutions**:
- Check write permissions
- Verify output directory exists
- Look for error messages in app
- Try different output path

### Flow Indices Wrong

**Problem**: Indices don't match hierarchy.

**Solutions**:
- Flow indices auto-calculated from depth
- Check indentation is correct
- Use validation tool to identify issues
- Re-run formalization phase

### Format Conversion Errors

**Problem**: Conversion fails.

**Solutions**:
- Run `validate` first to check format
- Ensure input file not corrupted
- Check all required fields present
- Verify encoding (use UTF-8)

---

## Best Practices

### Workflow Recommendations

1. **Draft in .ncds** - Start with easiest format
2. **Formalize to .ncd** - Add rigor automatically
3. **Review in .ncdn** - Use hybrid for stakeholder review
4. **Validate frequently** - Catch issues early
5. **Generate companions** - Keep all formats in sync
6. **Version control .ncd** - Store as text, not JSON

### File Organization

```
project/
├── plans/
│   ├── plan1.ncd          # Formal syntax
│   ├── plan1.ncn          # Natural companion
│   ├── plan1.ncdn         # Hybrid for review
│   └── plan1.nc.json      # Structured JSON
├── compiled/
│   ├── plan1.concept.json      # Executable concepts
│   └── plan1.inference.json    # Executable inferences
└── provision/
    ├── data/              # Ground data files
    ├── prompts/           # Prompt templates
    └── scripts/           # Python scripts
```

### Editor Tips

1. **Use Pure Text mode** for reading/understanding
2. **Use Line-by-Line mode** for precise editing
3. **Toggle NCD/NCN** to see both representations
4. **Collapse sections** when working on large files
5. **Preview often** to check output
6. **Validate before saving** to catch errors

---

## Advanced Features

### Custom Parsers

Extend `unified_parser.py` to handle custom formats:

```python
from unified_parser import NCDParser

class CustomParser(NCDParser):
    def parse_custom_marker(self, line):
        # Your custom parsing logic
        pass
```

### Batch Processing

Process hundreds of files programmatically:

```python
from update_format import FormatUpdater
from pathlib import Path

updater = FormatUpdater()
for file in Path('plans/').rglob('*.ncd'):
    updater.convert_file(str(file), 'ncdn')
    updater.validate_file(str(file))
```

### Integration with CI/CD

See [Automation Scripts](#automation-scripts) for GitHub Actions examples.

---

## API Reference

### FormatUpdater Class

```python
class FormatUpdater:
    def convert_file(self, input_path, target_format):
        """Convert file to target format."""
        pass
    
    def validate_file(self, file_path):
        """Validate file structure."""
        pass
    
    def batch_convert(self, directory, from_format, to_format, recursive=False):
        """Batch convert all files in directory."""
        pass
    
    def generate_companions(self, ncd_path, generate_ncn=True, 
                          generate_json=True, generate_ncdn=True,
                          generate_nci=True):
        """Generate all companion formats."""
        pass
```

### NCDParser Class

```python
class NCDParser:
    def parse(self, ncd_content, ncn_content=None):
        """Parse .ncd and optional .ncn into JSON structure."""
        pass
    
    def serialize(self, json_structure):
        """Serialize JSON back to .ncd and .ncn."""
        pass
    
    def parse_ncdn(self, ncdn_content):
        """Parse hybrid .ncdn format."""
        pass
    
    def serialize_ncdn(self, json_structure):
        """Serialize to hybrid .ncdn format."""
        pass
```

---

## Summary

### Key Takeaways

| Tool | Purpose | Use When |
|------|---------|----------|
| **Interactive Editor** | Visual editing | Creating/modifying plans |
| **Format Converter** | Batch conversion | Project-wide updates |
| **Validator** | Check consistency | Before committing/deploying |
| **Automation Scripts** | CI/CD integration | Continuous validation |

### The Tools Promise

**NormCode's tooling makes compilation manageable**:

1. Edit visually with inline editor
2. Convert between formats easily
3. Validate automatically
4. Integrate with workflows
5. Round-trip without data loss

**Result**: Productive editing and reliable format management across the entire compilation pipeline.

---

## Next Steps

- **[Overview](overview.md)** - Return to compilation overview
- **[Activation](activation.md)** - See how repositories are generated
- **[Execution Section](../3_execution/README.md)** - How compiled plans run

---

**Ready to start editing?** Launch the editor with `python launch_demo.py` and load example files to explore!
