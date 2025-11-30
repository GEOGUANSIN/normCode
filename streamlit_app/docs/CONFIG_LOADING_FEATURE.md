# Configuration Loading Feature - v1.3

## Overview

The NormCode Orchestrator Streamlit app now supports loading and reusing configurations from previous runs. This feature allows you to quickly replicate run settings without manual re-entry, making it easier to run experiments, compare results, and maintain consistency across runs.

## What's New

### 1. Load Previous Run Configurations

**Location:** Sidebar → "📋 Load Previous Config"

You can now:
- Browse all previous runs with saved configurations
- Preview configuration details before loading
- Load settings with one click to auto-populate the configuration form
- Clear loaded configurations to start fresh

### 2. Automatic Configuration Saving

The app now automatically saves comprehensive configuration metadata for every run:

- **LLM Settings**: Model name
- **Execution Settings**: Max cycles, checkpoint frequency
- **Environment**: Base directory, base directory option
- **Mode Information**: Fresh Run, Resume, or Fork
- **Advanced Settings**: Reconciliation mode, verify files option
- **Tracking**: App version, timestamps

### 3. Enhanced History View

**Location:** History Tab → Database Runs

Each run now displays:
- Run configuration summary (LLM model, max cycles, mode)
- Full configuration in expandable section
- Fork/resume relationships
- Last modified timestamp

## Usage Guide

### Loading a Configuration

1. **Navigate to Sidebar**
   - Look for "📋 Load Previous Config" section at the top

2. **Select a Previous Run**
   - Choose from dropdown showing: `run_id... (timestamp)`
   - Example: `abc12345678... (2025-11-30 10:30)`

3. **Preview (Optional)**
   - Click "👁️ Preview" to see full configuration JSON
   - Review settings before loading

4. **Load Configuration**
   - Click "🔄 Load Config"
   - All settings auto-populate in the form below
   - A success message confirms the load

5. **Modify if Needed**
   - All loaded settings are editable
   - Change any setting as needed for your new run

6. **Execute**
   - Upload repository files (concepts, inferences, inputs)
   - Click "▶️ Start Execution"
   - New run will use the loaded configuration

### What Gets Loaded

When you load a configuration, the following settings are auto-populated:

| Setting | Description |
|---------|-------------|
| **LLM Model** | Language model used (e.g., qwen-plus, gpt-4o) |
| **Max Cycles** | Maximum execution cycles |
| **Base Directory** | Directory for generated scripts/prompts |
| **Base Dir Option** | App Directory, Project Root, or Custom Path |

*Note: Repository files (concepts, inferences, inputs) are NOT loaded - you still need to upload them manually.*

### Clearing Loaded Configuration

If you've loaded a configuration and want to start fresh:

1. Look for the success indicator: `📌 Config loaded from: run_id...`
2. Click "🗑️ Clear Loaded Config"
3. Settings remain at their current values but are no longer linked to the previous run

## Use Cases

### 1. Re-running Experiments

**Scenario:** You want to re-run the same repository with identical settings

```
1. Load config from previous run
2. Upload same repository files
3. Execute
```

**Result:** Identical configuration, fresh execution

### 2. Comparing Repositories

**Scenario:** You want to test different repositories with the same configuration

```
1. Load config from Run A
2. Upload Repository B's files
3. Execute
```

**Result:** Different repository, same settings → easier comparison

### 3. Iterative Development

**Scenario:** You're tweaking a repository and want consistent settings

```
1. Run initial version → save as Run 1
2. Modify repository
3. Load config from Run 1
4. Upload modified repository
5. Execute
```

**Result:** Consistent configuration across iterations

### 4. Configuration Templates

**Scenario:** You have standard configurations for different task types

```
1. Create "template" runs with optimal settings
   - Fast run: qwen-turbo-latest, 30 cycles
   - Deep run: gpt-4o, 100 cycles
   - Debug run: qwen-plus, 10 cycles
2. Load appropriate template for new work
3. Execute with your repository
```

**Result:** Reusable configuration templates

## Technical Details

### Database Schema

Configurations are stored in the `run_metadata` table:

```sql
CREATE TABLE run_metadata (
    run_id TEXT PRIMARY KEY,
    metadata_json TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Metadata Structure

```json
{
  "llm_model": "qwen-plus",
  "max_cycles": 50,
  "base_dir": "/path/to/streamlit_app",
  "base_dir_option": "App Directory (default)",
  "agent_frame_model": "demo",
  "resume_mode": "Fresh Run",
  "verify_files": true,
  "app_version": "1.3",
  "reconciliation_mode": "PATCH",        // For Resume/Fork modes
  "forked_from_run_id": "abc123...",     // For Fork mode
  "last_resumed": "2025-11-30T10:30:00"  // For Resume mode
}
```

### When Metadata is Saved

- **Fresh Run**: When orchestrator is created
- **Resume from Checkpoint**: When checkpoint is loaded (updates existing metadata)
- **Fork from Checkpoint**: When fork is created (new metadata with fork info)

### Backward Compatibility

- Older runs without metadata will show "No configuration metadata available"
- The feature gracefully handles missing metadata
- All new runs automatically save metadata

## API Reference

### Session State

```python
st.session_state.loaded_config        # Dict or None - currently loaded configuration
st.session_state.config_loaded_from_run  # str or None - run_id config was loaded from
```

### Database Methods

```python
# Save metadata
db.save_run_metadata(run_id: str, metadata: Dict[str, Any])

# Retrieve metadata
db.get_run_metadata(run_id: str) -> Optional[Dict[str, Any]]

# List runs with metadata
db.list_runs(include_metadata: bool = False) -> List[Dict[str, Any]]
```

## Examples

### Example 1: Quick Re-run

```
Previous Run: abc123 (2025-11-29 14:30)
- LLM: gpt-4o
- Max Cycles: 100
- Mode: Fresh Run

New Run:
1. Load config from abc123
2. Upload same repository files
3. Execute
→ New run with identical settings
```

### Example 2: Cross-Repository Comparison

```
Run A: Addition Repository (def456)
- LLM: qwen-plus
- Max Cycles: 50

Run B: Combination Repository (new)
1. Load config from def456
2. Upload Combination repository files
3. Execute
→ Both runs use qwen-plus with 50 cycles
```

### Example 3: Forking with Config Reuse

```
Source Run: ghi789 (completed addition)
New Run:
1. Load config from ghi789
2. Upload Combination repository
3. Select "Fork from Checkpoint"
4. Enter ghi789 as source run
5. Execute
→ State from ghi789 + Config from ghi789 + Combination logic
```

## Troubleshooting

### "No previous runs with configurations found"

**Cause:** Database is empty or runs were created before v1.3

**Solution:** Execute at least one run with v1.3 to create metadata

### "Could not load run configurations"

**Cause:** Database file is locked or corrupted

**Solution:**
1. Close any other apps accessing the database
2. Check database file permissions
3. Try with a fresh database path

### Configuration Loads but Settings Don't Match

**Cause:** Configuration was from a different app version or manually modified

**Solution:**
1. Click "👁️ Preview" to verify configuration JSON
2. Manually adjust settings as needed
3. Loaded config is just a starting point - all settings are editable

### LLM Model Not in Dropdown

**Cause:** Previous run used a model that's no longer in the dropdown

**Solution:**
1. Configuration loads the closest match (defaults to first option)
2. Manually select the correct model from current dropdown
3. The app will use your manual selection

## Migration Guide

### From v1.2 to v1.3

**Existing Databases:**
- v1.2 runs will not have configuration metadata
- v1.3 runs will automatically save metadata
- Both types coexist in the same database
- History tab shows "No configuration metadata available" for old runs

**No Action Required:**
- The feature is fully backward compatible
- Old runs continue to work normally
- Start using the feature on new runs

## Future Enhancements

Potential future additions:

- [ ] Export/import configurations as JSON files
- [ ] Configuration comparison tool (diff two runs)
- [ ] Configuration validation before execution
- [ ] Configuration presets/favorites
- [ ] Bulk operations (apply config to multiple runs)
- [ ] Configuration inheritance (base config + overrides)

## Changelog

### v1.3.0 (2025-11-30)

**Added:**
- Configuration loading from previous runs
- Automatic configuration saving for all runs
- Configuration preview in sidebar
- Configuration display in History tab
- Session state tracking for loaded configs

**Changed:**
- Updated footer to v1.3
- Enhanced Help tab with config loading documentation

**Fixed:**
- Database path initialization order in sidebar

## Support

For issues or questions:
1. Check the Help tab in the app
2. Review this documentation
3. Check the main README and other docs in `streamlit_app/docs/`

---

**Version:** 1.3.0  
**Date:** 2025-11-30  
**Feature:** Configuration Loading

