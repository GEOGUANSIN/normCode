# NormCode Editor - Usage Examples

Quick examples for common tasks with the NormCode editor and format tools.

## Table of Contents
- [Interactive Editing](#interactive-editing)
- [Format Conversion](#format-conversion)
- [Validation](#validation)
- [Batch Processing](#batch-processing)
- [Automation](#automation)

## Interactive Editing

### Example 1: Edit a Simple Concept

**Start:**
```bash
cd streamlit_app/editor_subapp
python launch_demo.py
```

**In the Editor:**
1. Click "Load Example" in sidebar
2. Click "Load example.ncd/ncn"
3. Edit any line directly in the text field
4. Click "💾 Export .ncd" to save changes

### Example 2: Toggle Between NCD and NCN Views

**Scenario:** You want to edit technical syntax in NCD but descriptions in NCN.

**Steps:**
1. Load your files
2. Set "Default View" to NCD
3. For specific lines, click the 🔄 button to switch to NCN
4. Edit the natural language description
5. Click 🔄 again to switch back to NCD

### Example 3: Focus on Specific Sections

**Scenario:** Large file with many nested concepts, you want to focus on section 1.3.

**Steps:**
1. Load your file
2. In "Display Options", find "Collapse Section"
3. Type "1.1" and click "➖ Collapse"
4. Type "1.2" and click "➖ Collapse"
5. Type "1.4" and click "➖ Collapse"
6. Now only section 1.3 and its children are visible
7. Edit as needed
8. Click "🔄 Expand All" when done

### Example 4: Pure Text Editing

**Scenario:** You prefer editing in a single text area rather than line-by-line.

**Steps:**
1. Load your files
2. Switch to "📝 Pure Text" mode
3. Edit in the large text area (supports multi-line select/copy)
4. Click "✅ Apply" to save changes
5. Flow indices automatically refresh

**Pure Text Format:**
```
     1 │ :<:({result}) | 1. assigning
       │     |?{natural language}: :<: The result is calculated.
   1.1 │     <= $.({calculate})
       │         |?{natural language}: <= This is done by the calculate method.
```

## Format Conversion

### Example 5: Convert .ncd to .ncdn

**Command:**
```bash
python update_format.py convert example.ncd --to ncdn
```

**Result:**
```
Converted example.ncd -> example.ncdn
```

**What this does:**
- Reads `example.ncd` and `example.ncn` (if exists)
- Combines them into unified `.ncdn` format
- Creates `example.ncdn` with inline annotations

### Example 6: Convert to JSON for Processing

**Command:**
```bash
python update_format.py convert concept.ncd --to nc.json
```

**Result:**
Creates `concept.nc.json`:
```json
{
  "lines": [
    {
      "flow_index": "1",
      "type": "main",
      "depth": 0,
      "nc_main": ":<:({result}) | 1. assigning",
      "ncn_content": ":<: The result is calculated."
    }
  ]
}
```

### Example 7: Generate Inference Format

**Command:**
```bash
python update_format.py convert concept.ncd --to nci.json
```

**Result:**
Creates `concept.nci.json`:
```json
[
  {
    "concept_to_infer": {
      "flow_index": "1",
      "type": "main",
      "nc_main": ":<:({result})"
    },
    "function_concept": {
      "flow_index": "1.1",
      "type": "main",
      "nc_main": "<= $.({calculate})"
    },
    "value_concepts": [
      {
        "flow_index": "1.2",
        "type": "main",
        "nc_main": "<- {number a}"
      }
    ]
  }
]
```

## Validation

### Example 8: Validate Before Committing

**Command:**
```bash
python update_format.py validate my_concept.ncd my_concept.ncn
```

**Success output:**
```
✅ Validation passed for my_concept.ncd
```

**Failure output:**
```
❌ Validation failed for my_concept.ncd

Issues found:
  - Line 5: Depth jump from 0 to 2
  - Line 12: Duplicate flow index 3.1
  - Line 15: Main line missing 'nc_main' field
```

### Example 9: Validate NCDN File

**Command:**
```bash
python update_format.py validate combined.ncdn
```

**What gets checked:**
- All required fields present
- Flow indices are unique and hierarchical
- Depth increases correctly
- Round-trip conversion works

## Batch Processing

### Example 10: Convert All Files in Directory

**Scenario:** You have 50 `.ncd` files and want to create `.ncdn` versions.

**Command:**
```bash
python update_format.py batch-convert ./concepts --from ncd --to ncdn
```

**Output:**
```
Batch converting ncd -> ncdn in ./concepts

Results:
  Total files: 50
  Success: 50
  Failed: 0
```

### Example 11: Recursive Directory Conversion

**Scenario:** Convert all files in project including subdirectories.

**Command:**
```bash
python update_format.py batch-convert ./my_project --from ncd --to ncdn --recursive
```

**Result:**
- Processes all `.ncd` files in `./my_project` and all subdirectories
- Creates `.ncdn` files in the same locations
- Reports success/failure statistics

### Example 12: Generate Missing Companions

**Scenario:** You have `.ncd` files but need all other formats.

**Command:**
```bash
# For a single file
python update_format.py generate concept.ncd --all

# For all files in directory (using shell loop)
for file in *.ncd; do
    python update_format.py generate "$file" --all
done
```

**Result:**
For `concept.ncd`, creates:
- `concept.ncn`
- `concept.ncdn`
- `concept.nc.json`
- `concept.nci.json`

## Automation

### Example 13: Pre-commit Validation Script

**File: `pre-commit.sh`**
```bash
#!/bin/bash
# Validate all NormCode files before committing

echo "🔍 Validating NormCode files..."
failed=0

# Find all .ncd and .ncdn files
for file in $(find . -name "*.ncd" -o -name "*.ncdn"); do
    if ! python update_format.py validate "$file" 2>/dev/null; then
        echo "❌ Failed: $file"
        failed=$((failed + 1))
    else
        echo "✅ Valid: $file"
    fi
done

if [ $failed -eq 0 ]; then
    echo ""
    echo "✅ All files valid! Proceeding with commit."
    exit 0
else
    echo ""
    echo "❌ $failed file(s) failed validation. Fix issues before committing."
    exit 1
fi
```

**Usage:**
```bash
chmod +x pre-commit.sh
./pre-commit.sh
```

### Example 14: Sync Script

Keep all formats in sync whenever .ncd files change.

**File: `sync_formats.py`**
```python
#!/usr/bin/env python
"""Sync all NormCode formats whenever .ncd files change."""

import os
import sys
from pathlib import Path
from update_format import FormatUpdater

def sync_all_formats(directory='.', recursive=False):
    """Generate all companion formats for .ncd files."""
    updater = FormatUpdater()
    
    pattern = '**/*.ncd' if recursive else '*.ncd'
    ncd_files = list(Path(directory).glob(pattern))
    
    print(f"Found {len(ncd_files)} .ncd file(s)")
    
    for ncd_file in ncd_files:
        print(f"\n📄 Processing: {ncd_file}")
        
        companions = updater.generate_companions(
            str(ncd_file),
            generate_ncn=True,
            generate_json=True,
            generate_ncdn=True,
            generate_nci=True
        )
        
        print(f"  ✅ Generated {len(companions)} companion(s)")

if __name__ == '__main__':
    recursive = '--recursive' in sys.argv or '-r' in sys.argv
    sync_all_formats('.', recursive)
```

**Usage:**
```bash
python sync_formats.py
python sync_formats.py --recursive
```

### Example 15: CI/CD Pipeline Integration

**File: `.github/workflows/validate-normcode.yml`**
```yaml
name: Validate NormCode Files

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Validate NormCode files
      working-directory: streamlit_app/editor_subapp
      run: |
        for file in $(find . -name "*.ncd" -o -name "*.ncdn"); do
          python update_format.py validate "$file" || exit 1
        done
    
    - name: Check format consistency
      working-directory: streamlit_app/editor_subapp
      run: python test_update_format.py
```

### Example 16: Watch and Auto-Convert

Monitor directory for changes and auto-convert to .ncdn.

**File: `watch_convert.py`**
```python
#!/usr/bin/env python
"""Watch directory and auto-convert .ncd files to .ncdn."""

import time
import os
from pathlib import Path
from update_format import FormatUpdater

def get_ncd_files(directory):
    """Get all .ncd files with their modification times."""
    files = {}
    for ncd_file in Path(directory).glob('*.ncd'):
        files[str(ncd_file)] = os.path.getmtime(ncd_file)
    return files

def watch_and_convert(directory='.', interval=2):
    """Watch for changes and convert."""
    updater = FormatUpdater()
    known_files = get_ncd_files(directory)
    
    print(f"👀 Watching {directory} for .ncd changes...")
    print(f"   Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(interval)
            current_files = get_ncd_files(directory)
            
            # Check for new or modified files
            for file_path, mod_time in current_files.items():
                if file_path not in known_files or known_files[file_path] < mod_time:
                    print(f"\n🔄 Detected change: {file_path}")
                    success, message = updater.convert_file(file_path, 'ncdn')
                    if success:
                        print(f"   ✅ {message}")
                    else:
                        print(f"   ❌ {message}")
                    
                    known_files[file_path] = mod_time
    
    except KeyboardInterrupt:
        print("\n\n👋 Stopped watching.")

if __name__ == '__main__':
    watch_and_convert()
```

**Usage:**
```bash
python watch_convert.py
# Make changes to any .ncd file
# Script automatically converts to .ncdn
```

## Windows-Specific Examples

### Example 17: Batch File for Windows

**File: `convert_all.bat`**
```batch
@echo off
REM Convert all .ncd files in current directory to .ncdn

echo Converting .ncd files to .ncdn...

for %%f in (*.ncd) do (
    echo Processing %%f
    python update_format.py convert %%f --to ncdn
)

echo Done!
pause
```

**Usage:**
Double-click `convert_all.bat` or run from command prompt.

### Example 18: PowerShell Script

**File: `Sync-NormCode.ps1`**
```powershell
# PowerShell script to sync NormCode formats

param(
    [string]$Directory = ".",
    [switch]$Recursive
)

Write-Host "Syncing NormCode files in $Directory" -ForegroundColor Cyan

$files = if ($Recursive) {
    Get-ChildItem -Path $Directory -Filter "*.ncd" -Recurse
} else {
    Get-ChildItem -Path $Directory -Filter "*.ncd"
}

foreach ($file in $files) {
    Write-Host "`nProcessing: $($file.Name)" -ForegroundColor Yellow
    
    python update_format.py generate $file.FullName --all
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Success" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Failed" -ForegroundColor Red
    }
}

Write-Host "`nDone!" -ForegroundColor Cyan
```

**Usage:**
```powershell
# Current directory
.\Sync-NormCode.ps1

# Recursive
.\Sync-NormCode.ps1 -Recursive

# Specific directory
.\Sync-NormCode.ps1 -Directory "C:\Projects\NormCode" -Recursive
```

## Troubleshooting Examples

### Example 19: Fix Broken Flow Indices

**Problem:** Flow indices are out of order.

**Solution:**
```bash
# Convert to JSON (normalizes flow indices)
python update_format.py convert broken.ncd --to nc.json

# Convert back to .ncd (flow indices recalculated)
python update_format.py convert broken.nc.json --to ncd --output fixed.ncd

# Validate
python update_format.py validate fixed.ncd
```

### Example 20: Recover from Format Corruption

**Problem:** File won't parse correctly.

**Steps:**
```bash
# 1. Try validation to see specific issues
python update_format.py validate corrupted.ncd

# 2. If it's partially valid, try converting to JSON
python update_format.py convert corrupted.ncd --to nc.json

# 3. Manually fix the JSON if needed
# 4. Convert back
python update_format.py convert fixed.nc.json --to ncd

# 5. Regenerate companions
python update_format.py generate fixed.ncd --all
```

## See Also

- **[README_DEMO.md](README_DEMO.md)** - Complete editor documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Get started quickly
- **[FORMAT_UPDATE_GUIDE.md](FORMAT_UPDATE_GUIDE.md)** - Detailed format tool guide
- **`unified_parser.py`** - Parser source code
- **`demo_editor.py`** - Editor source code
- **`update_format.py`** - Format tool source code





