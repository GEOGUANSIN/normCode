# ✅ Complete Setup Loading Feature - v1.3.1

## What's New

The configuration loading feature has been **significantly enhanced** to provide a complete "one-click reload" experience. You can now load:

✅ **Configuration** (LLM model, max cycles, etc.)  
✅ **Repository Files** (concepts.json, inferences.json, inputs.json)  
✅ **Database Path** (checkpoint database location)

## Summary

With v1.3.1, you can now reload an **entire previous run setup** with a single action. No more manually uploading files or re-entering settings!

## How It Works

### 1. Automatic File Saving

When you execute a run, the app now automatically:
- Saves all uploaded repository files to disk
- Stores them in `streamlit_app/saved_repositories/{run_id}/`
- Records file paths in the database metadata

### 2. Complete Configuration Storage

The metadata now includes:
```json
{
  "llm_model": "qwen-plus",
  "max_cycles": 50,
  "base_dir": "/path/to/base",
  "db_path": "orchestration.db",
  "concepts_file_path": "saved_repositories/abc123.../concepts.json",
  "inferences_file_path": "saved_repositories/abc123.../inferences.json",
  "inputs_file_path": "saved_repositories/abc123.../inputs.json"
}
```

### 3. One-Click Reload

Load everything from a previous run:
1. Select run from dropdown
2. Check "📁 Also load repository files"
3. Click "🔄 Load Config"
4. ✨ Everything is ready to execute!

## Usage Guide

### Basic Workflow

```
┌─────────────────────────────────────────────┐
│ 1. First Run                                │
├─────────────────────────────────────────────┤
│ - Upload concepts.json                      │
│ - Upload inferences.json                    │
│ - Upload inputs.json                        │
│ - Configure settings                        │
│ - Execute                                   │
│ ✓ Files automatically saved                 │
│ ✓ Config automatically saved                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 2. Later - Complete Reload                  │
├─────────────────────────────────────────────┤
│ - Select previous run from dropdown         │
│ - Check "📁 Also load repository files"     │
│ - Click "🔄 Load Config"                    │
│ ✓ All settings loaded                       │
│ ✓ All files loaded                          │
│ ✓ Database path loaded                      │
│ ✓ Ready to execute!                         │
└─────────────────────────────────────────────┘
```

### UI Features

#### File Loading Indicator

When files are loaded from a previous run:

```
📁 Repository Files
───────────────────────────────────
📄 Using loaded: `concepts.json`
   [🔄 Upload Different Concepts File]

📄 Using loaded: `inferences.json`
   [🔄 Upload Different Inferences File]

📄 Using loaded: `inputs.json`
   [🔄 Upload Different Inputs File]
```

#### Optional File Loading

```
📋 Load Previous Config
───────────────────────────────────
Load settings from:
[Select run... ▼]

☑️ 📁 Also load repository files
   Available: concepts.json, inferences.json, inputs.json

[🔄 Load Config]  [👁️ Preview]
```

#### Status Indicator

```
📌 Config + Files loaded from: `abc12345...`
   Loaded files: concepts, inferences, inputs

[🗑️ Clear Loaded Config]
```

## Use Cases

### 1. Exact Re-run
**Goal**: Run the exact same setup again

**Steps**:
1. Load config + files from previous run
2. Click "Start Execution"

**Result**: Identical run with fresh execution

### 2. Modified Repository
**Goal**: Test changes to repository while keeping same config

**Steps**:
1. Load config from previous run (without files)
2. Upload modified repository files
3. Execute

**Result**: Same settings, updated repository

### 3. Cross-Repository Testing
**Goal**: Test different repository with proven configuration

**Steps**:
1. Load config + files from Run A
2. Click "Upload Different" for repository files
3. Upload Repository B files
4. Execute

**Result**: Repository B with Run A's configuration

### 4. Template-Based Execution
**Goal**: Use standard configurations for different tasks

**Steps**:
1. Create template runs with optimal settings
2. Load template config (without files)
3. Upload task-specific repository
4. Execute

**Result**: Consistent configuration across different tasks

## Technical Details

### File Storage Structure

```
streamlit_app/
├── saved_repositories/
│   ├── run_abc123.../
│   │   ├── concepts.json
│   │   ├── inferences.json
│   │   └── inputs.json
│   ├── run_def456.../
│   │   ├── concepts.json
│   │   ├── inferences.json
│   │   └── inputs.json
│   └── ...
└── ...
```

### Metadata Structure (Enhanced)

```json
{
  "llm_model": "qwen-plus",
  "max_cycles": 50,
  "base_dir": "/path/to/streamlit_app",
  "base_dir_option": "App Directory (default)",
  "db_path": "orchestration.db",
  "agent_frame_model": "demo",
  "resume_mode": "Fresh Run",
  "verify_files": true,
  "app_version": "1.3.1",
  
  // NEW in v1.3.1
  "concepts_file_path": "saved_repositories/abc123.../concepts.json",
  "inferences_file_path": "saved_repositories/abc123.../inferences.json",
  "inputs_file_path": "saved_repositories/abc123.../inputs.json"
}
```

### Session State

```python
st.session_state.loaded_repo_files = {
    'concepts': {
        'name': 'concepts.json',
        'content': '...',  # JSON string
        'path': 'saved_repositories/abc123.../concepts.json'
    },
    'inferences': {...},
    'inputs': {...}
}
```

### File Loading Logic

1. **Check Session State**: Are files loaded?
2. **If Loaded**: Show indicator, skip uploader
3. **If Not Loaded**: Show uploader
4. **Execution**: Use loaded files or uploaded files
5. **Save**: Save uploaded files to disk, store paths

## Benefits

### For Users

⚡ **One-Click Reload**: Complete setup in one action  
📁 **No File Re-uploading**: Files loaded automatically  
🎯 **Guaranteed Accuracy**: Exact same files as before  
🔄 **Easy Experimentation**: Quick to test variations  
💾 **Persistent Storage**: Files saved for future use

### For Development

📝 **Complete Audit Trail**: Full history of what was run  
🔍 **Easy Debugging**: Exact reproduction of any run  
🧪 **Test Consistency**: Same setup across test runs  
📊 **Performance Comparison**: Same files, different configs

## Comparison: v1.3 vs v1.3.1

| Feature | v1.3 | v1.3.1 |
|---------|------|--------|
| **Load Configuration** | ✅ Yes | ✅ Yes |
| **Load Repository Files** | ❌ No | ✅ Yes |
| **Load Database Path** | ❌ No | ✅ Yes |
| **Save Files to Disk** | ❌ No | ✅ Yes |
| **One-Click Complete Reload** | ❌ No | ✅ Yes |
| **File Change Detection** | ❌ No | ✅ Yes |
| **Selective File Loading** | ❌ No | ✅ Yes |

## Examples

### Example 1: Exact Re-run

**Scenario**: You want to re-run a successful execution

```
Previous Run: abc123 (2025-11-30 10:00)
- LLM: gpt-4o
- Max Cycles: 100
- Files: addition_concepts.json, addition_inferences.json, addition_inputs.json
- Database: orchestration.db

New Run:
1. Select abc123 from dropdown
2. Check "Also load repository files"
3. Click "Load Config"
4. Click "Start Execution"

Result:
- Exact same configuration
- Exact same files
- Fresh execution
```

### Example 2: Test Modified Repository

**Scenario**: You modified inferences.json and want to test it

```
Previous Run: def456
- LLM: qwen-plus
- Max Cycles: 50
- Files: concepts.json, inferences.json, inputs.json

New Run:
1. Select def456 from dropdown
2. Uncheck "Also load repository files" (or load and change)
3. Click "Load Config"
4. Click "Upload Different Inferences File"
5. Upload modified inferences.json
6. Execute

Result:
- Same configuration
- Same concepts and inputs
- Modified inferences
```

### Example 3: Cross-Repository with Fork

**Scenario**: Run combination repository using results from addition run

```
Source Run: ghi789 (addition repository, completed)
- LLM: gpt-4o
- Max Cycles: 50
- Database: orchestration.db

New Run:
1. Select ghi789 from dropdown
2. Uncheck "Also load repository files"
3. Click "Load Config"
4. Upload combination_concepts.json
5. Upload combination_inferences.json
6. Select "Fork from Checkpoint"
7. Enter ghi789 as source run
8. Execute

Result:
- Configuration from ghi789
- State from ghi789 (addition results)
- New repository (combination logic)
```

## Troubleshooting

### "Files not found"

**Cause**: Saved files were deleted or moved

**Solution**:
- Upload files manually
- Files will be saved for next time

### "Some files available"

**Cause**: Only some files were saved in previous run

**Solution**:
- Load available files
- Upload missing files manually

### "Cannot load files"

**Cause**: File paths are invalid or inaccessible

**Solution**:
- Check file permissions
- Verify file paths in Preview
- Upload files manually

## Version Info

- **Version**: 1.3.1
- **Release Date**: 2025-11-30
- **Feature**: Complete Setup Loading (Config + Files + Database)
- **Backward Compatible**: Yes (works with v1.3 databases)

## Changes from v1.3

### Added

- ✅ Automatic file saving to disk
- ✅ File path storage in metadata
- ✅ Database path in configuration
- ✅ Checkbox to load repository files
- ✅ File availability indicator
- ✅ Button to change loaded files
- ✅ Status showing loaded files
- ✅ Support for loaded files in execution

### Changed

- 📝 Metadata now includes file paths
- 📝 UI shows loaded files instead of uploaders
- 📝 App version updated to 1.3.1
- 📝 Footer message updated

### Technical

- Created `saved_repositories/` directory
- Added `save_uploaded_file()` helper function
- Added `load_file_from_path()` helper function
- Enhanced session state with `loaded_repo_files`
- Updated execution logic to use loaded files
- Updated all execution modes (Fresh, Resume, Fork)

## Next Steps

1. **Try It Out**:
   ```bash
   cd streamlit_app
   streamlit run app.py
   ```

2. **Execute a Run**:
   - Upload repository files
   - Configure settings
   - Execute
   - Files automatically saved!

3. **Reload Everything**:
   - Select previous run
   - Check "Also load repository files"
   - Click "Load Config"
   - Everything ready to go!

4. **Experiment**:
   - Try loading config without files
   - Try changing individual files
   - Try different combinations

## Summary

**v1.3.1 transforms configuration loading into complete setup loading!**

You can now:
- ✅ Load entire previous setups with one click
- ✅ Selectively load or change files
- ✅ Guarantee exact reproduction
- ✅ Save time on repetitive setups
- ✅ Experiment with variations easily

**Ready to use! Enjoy the complete reload experience!** 🎉

