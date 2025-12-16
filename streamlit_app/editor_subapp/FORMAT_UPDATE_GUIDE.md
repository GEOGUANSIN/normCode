# NormCode Format Update Tool Guide

Complete guide to using `update_format.py` for format conversion, validation, and batch processing.

## Overview

The Format Update Tool provides command-line utilities for:
- Converting between NormCode formats (.ncd, .ncn, .ncdn, .nc.json, .nci.json)
- Validating format consistency and structure
- Batch processing multiple files
- Generating companion files automatically

## Quick Reference

```bash
# Convert single file
python update_format.py convert <input> --to <format>

# Validate files
python update_format.py validate <ncd_file> [ncn_file]

# Batch convert
python update_format.py batch-convert <directory> --from <format> --to <format>

# Generate companions
python update_format.py generate <input> [--ncn] [--json] [--ncdn] [--nci] [--all]
```

## Commands

### 1. Convert Command

Convert a single file from one format to another.

**Syntax:**
```bash
python update_format.py convert INPUT --to FORMAT [--output OUTPUT]
```

**Arguments:**
- `INPUT` - Input file path
- `--to FORMAT` - Target format: `ncd`, `ncn`, `ncdn`, `nc.json`, or `nci.json`
- `--output OUTPUT` (optional) - Custom output path

**Examples:**

```bash
# Convert .ncd to .ncdn
python update_format.py convert example.ncd --to ncdn

# Convert to JSON with custom output path
python update_format.py convert example.ncd --to nc.json --output custom_name.json

# Convert .ncdn to .nci.json (inference format)
python update_format.py convert example.ncdn --to nci.json

# Convert JSON back to .ncd
python update_format.py convert example.nc.json --to ncd
```

**Auto-generated output paths:**
- Input: `example.ncd` → Output: `example.ncdn` (when converting to ncdn)
- Input: `test.nc.json` → Output: `test.ncd` (when converting to ncd)
- Input: `file.ncdn` → Output: `file.nci.json` (when converting to nci.json)

### 2. Validate Command

Validate NormCode files for structural consistency and correctness.

**Syntax:**
```bash
python update_format.py validate NCD_FILE [NCN_FILE]
```

**Arguments:**
- `NCD_FILE` - Path to .ncd file
- `NCN_FILE` (optional) - Path to companion .ncn file

**Examples:**

```bash
# Validate single .ncd file
python update_format.py validate example.ncd

# Validate .ncd with companion .ncn
python update_format.py validate example.ncd example.ncn

# Validate .ncdn file
python update_format.py validate example.ncdn
```

**What gets validated:**

1. **Required Fields**
   - Every line has `type`, `depth`, and `flow_index`
   - Main lines have `nc_main` content
   - Comment lines have `nc_comment` content

2. **Flow Index Consistency**
   - No duplicate flow indices for main lines
   - Flow indices follow hierarchical structure (1, 1.1, 1.2, 1.2.1, etc.)

3. **Depth Validation**
   - Depth increases by at most 1 level at a time
   - Depth corresponds to indentation structure

4. **Round-Trip Integrity**
   - File can be parsed and re-serialized without data loss
   - Re-parsed structure matches original

**Exit codes:**
- `0` - Validation passed
- `1` - Validation failed (issues found)

### 3. Batch Convert Command

Convert multiple files in a directory from one format to another.

**Syntax:**
```bash
python update_format.py batch-convert DIRECTORY --from FORMAT --to FORMAT [--recursive]
```

**Arguments:**
- `DIRECTORY` - Directory containing files to convert
- `--from FORMAT` - Source format: `ncd`, `ncn`, `ncdn`, `json`, or `nci`
- `--to FORMAT` - Target format: `ncd`, `ncn`, `ncdn`, `nc.json`, or `nci.json`
- `--recursive` or `-r` (optional) - Process subdirectories

**Examples:**

```bash
# Convert all .ncd files in current directory to .ncdn
python update_format.py batch-convert . --from ncd --to ncdn

# Recursively convert all .ncd files in project to .ncdn
python update_format.py batch-convert ./my_project --from ncd --to ncdn --recursive

# Convert all .ncdn files back to JSON
python update_format.py batch-convert ./files --from ncdn --to nc.json

# Convert JSON files to inference format
python update_format.py batch-convert ./data --from json --to nci.json -r
```

**Output:**
```
Batch converting ncd -> ncdn in ./files

Results:
  Total files: 10
  Success: 9
  Failed: 1

Failed files:
  - ./files/broken.ncd: Error parsing file: ...
```

### 4. Generate Command

Generate companion files for an existing NormCode file.

**Syntax:**
```bash
python update_format.py generate INPUT [--ncn] [--json] [--ncdn] [--nci] [--all]
```

**Arguments:**
- `INPUT` - Input file path
- `--ncn` - Generate .ncn file
- `--json` - Generate .nc.json file
- `--ncdn` - Generate .ncdn file
- `--nci` - Generate .nci.json file
- `--all` - Generate all companion formats

**Examples:**

```bash
# Generate all companion files
python update_format.py generate example.ncd --all

# Generate only .ncn and .json companions
python update_format.py generate example.ncd --ncn --json

# Generate inference format from .ncdn
python update_format.py generate example.ncdn --nci

# Generate .ncdn from JSON
python update_format.py generate data.nc.json --ncdn
```

**Output:**
```
✅ Generated 4 companion file(s):
  - example.ncn
  - example.nc.json
  - example.ncdn
  - example.nci.json
```

## Format Types

### .ncd (NormCode Draft)
- Technical format with operators
- Indentation-based structure (4 spaces per level)
- Main concepts: `<=`, `<-`, `:<:`
- Comments: `?:`, `/:`, `...:`
- Metadata: `| flow_index sequence_type`

### .ncn (NormCode Natural)
- Natural language descriptions
- Same structure as .ncd but with readable content
- Matches .ncd line-by-line for main concepts

### .ncdn (NormCode Draft + Natural)
- Hybrid format combining .ncd and .ncn
- NCD content with inline NCN annotations
- Format: `|?{natural language}: <NCN content>`
- Single file contains both representations

### .nc.json
- JSON structure with line array
- Each line has: flow_index, type, depth, content
- Direct translation of .ncd/.ncn structure
- Machine-readable format

### .nci.json
- Inference-focused format
- Groups concepts by inference relationships
- Identifies function concepts (`<=`) and value concepts (`<-`)
- Structure: concept_to_infer, function_concept, value_concepts

## Common Workflows

### Workflow 1: Project-Wide Format Migration

Convert an entire project from .ncd/.ncn pairs to unified .ncdn format:

```bash
# Step 1: Validate all existing files
for file in *.ncd; do
    python update_format.py validate "$file"
done

# Step 2: Batch convert to .ncdn
python update_format.py batch-convert . --from ncd --to ncdn --recursive

# Step 3: Verify conversions
for file in *.ncdn; do
    python update_format.py validate "$file"
done
```

### Workflow 2: Generate Missing Companion Files

You have .ncd files but need to generate all other formats:

```bash
# Generate all companions for each .ncd file
for file in *.ncd; do
    python update_format.py generate "$file" --all
done
```

### Workflow 3: Convert to Inference Format for AI Processing

Prepare files for AI inference processing:

```bash
# Convert all .ncd files to .nci.json
python update_format.py batch-convert ./concepts --from ncd --to nci.json --recursive

# Verify inference format
ls -la ./concepts/**/*.nci.json
```

### Workflow 4: Quality Assurance Check

Validate all files before version control commit:

```bash
#!/bin/bash
# validate_all.sh

echo "Validating all NormCode files..."
failed=0

for file in $(find . -name "*.ncd" -o -name "*.ncdn"); do
    if ! python update_format.py validate "$file"; then
        echo "❌ Failed: $file"
        failed=$((failed + 1))
    fi
done

if [ $failed -eq 0 ]; then
    echo "✅ All files valid!"
    exit 0
else
    echo "❌ $failed file(s) failed validation"
    exit 1
fi
```

### Workflow 5: Round-Trip Verification

Ensure format conversions are lossless:

```bash
# Original -> NCDN -> JSON -> NCD -> compare
python update_format.py convert original.ncd --to ncdn --output temp.ncdn
python update_format.py convert temp.ncdn --to nc.json --output temp.nc.json
python update_format.py convert temp.nc.json --to ncd --output final.ncd
python update_format.py validate final.ncd

# Clean up
rm temp.ncdn temp.nc.json final.ncd
```

## Windows Usage

For Windows users, use the provided batch wrapper:

```cmd
REM Convert file
update_format.bat convert example.ncd --to ncdn

REM Validate
update_format.bat validate example.ncd

REM Batch convert
update_format.bat batch-convert .\files --from ncd --to ncdn
```

Or make the .bat file executable and use it directly:
```cmd
update_format convert example.ncd --to ncdn
```

## Unix/Linux/Mac Usage

Use the shell wrapper:

```bash
# Make executable (first time only)
chmod +x update_format.sh

# Use wrapper
./update_format.sh convert example.ncd --to ncdn
./update_format.sh validate example.ncd
```

Or call Python directly:
```bash
python3 update_format.py convert example.ncd --to ncdn
```

## Troubleshooting

### "Module not found" error

**Problem:** `ModuleNotFoundError: No module named 'unified_parser'`

**Solution:** Make sure you're running the script from the `editor_subapp` directory:
```bash
cd streamlit_app/editor_subapp
python update_format.py convert example.ncd --to ncdn
```

### "File not found" error

**Problem:** Input file cannot be found

**Solutions:**
1. Use absolute paths: `python update_format.py convert /full/path/to/file.ncd --to ncdn`
2. Check current directory: `ls` (Unix) or `dir` (Windows)
3. Verify file extension is correct

### Validation fails with "depth jump" error

**Problem:** `Depth jump from 0 to 2`

**Explanation:** Indentation increased by more than one level

**Solution:** Fix the .ncd file indentation:
```
Bad:
:<:({a}) | 1. assigning
        <= $.({b})  # Jumped from depth 0 to depth 2

Good:
:<:({a}) | 1. assigning
    <= $.({b})      # Depth 0 to depth 1
```

### Round-trip test fails

**Problem:** Content doesn't match after conversion cycle

**Solutions:**
1. Check for invisible characters (tabs vs spaces)
2. Ensure UTF-8 encoding
3. Verify no manual edits to JSON broke structure
4. Run validation to identify specific issues

### Batch conversion partially fails

**Problem:** Some files convert, others don't

**Action steps:**
1. Note which files failed from the error report
2. Validate each failed file individually:
   ```bash
   python update_format.py validate failed_file.ncd
   ```
3. Fix identified issues in failed files
4. Re-run batch conversion

## Testing

Run the comprehensive test suite:

```bash
cd streamlit_app/editor_subapp
python test_update_format.py
```

This tests:
- Single file conversions
- Validation logic
- Round-trip integrity
- All format combinations
- Companion generation
- Batch processing

## Integration with Editor

The format update tool complements the Streamlit editor:

1. **Editor** - Interactive editing with visual interface
2. **Update Tool** - Batch processing and automation

**Combined workflow:**
```bash
# 1. Validate before editing
python update_format.py validate concept.ncd

# 2. Edit in Streamlit
python launch_demo.py

# 3. Generate all formats after editing
python update_format.py generate concept.ncd --all

# 4. Validate changes
python update_format.py validate concept.ncd concept.ncn
```

## Exit Codes

- `0` - Success
- `1` - Failure (validation failed, conversion error, etc.)

Use in scripts:
```bash
if python update_format.py validate file.ncd; then
    echo "Valid!"
else
    echo "Invalid!"
    exit 1
fi
```

## Advanced Usage

### Scripting with Python

Import and use the FormatUpdater class directly:

```python
from update_format import FormatUpdater

updater = FormatUpdater()

# Convert
success, message = updater.convert_file('input.ncd', 'ncdn')

# Validate
is_valid, issues = updater.validate_files('example.ncd')

# Batch
stats = updater.batch_convert('./files', 'ncd', 'ncdn', recursive=True)
```

### Custom Automation

Create custom automation scripts:

```python
# auto_sync.py - Keep formats in sync
import os
from update_format import FormatUpdater

updater = FormatUpdater()

# Find all .ncd files
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.ncd'):
            ncd_path = os.path.join(root, file)
            
            # Generate all companion formats
            companions = updater.generate_companions(
                ncd_path,
                generate_ncn=True,
                generate_json=True,
                generate_ncdn=True
            )
            
            print(f"Synced: {ncd_path} -> {len(companions)} companions")
```

## See Also

- `README_DEMO.md` - Full editor documentation
- `QUICKSTART.md` - Quick start guide
- `unified_parser.py` - Parser implementation
- `demo_editor.py` - Streamlit editor




