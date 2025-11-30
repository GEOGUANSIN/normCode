# Changelog - NormCode Orchestrator Streamlit App

All notable changes to this project will be documented in this file.

## [1.3.1] - 2025-11-30

### 🎉 Enhanced - Complete Setup Loading (Config + Files + Database)

#### Automatic Repository File Saving
- ✅ **Save Uploaded Files to Disk**
  - All uploaded repository files automatically saved
  - Stored in `saved_repositories/{run_id}/` directory
  - Files persist for future loading
  - Supports concepts.json, inferences.json, inputs.json

#### Complete Configuration Storage
- ✅ **Enhanced Metadata**
  - Now includes file paths for all repository files
  - Stores database path in configuration
  - Tracks which files are available for loading
  - Maintains backward compatibility

#### Repository File Loading
- ✅ **One-Click File Reload**
  - Checkbox to load repository files with configuration
  - Shows which files are available
  - Displays loaded files in UI
  - Button to change individual loaded files
  - No need to manually re-upload files!

#### UI Enhancements
- ✅ **Smart File Display**
  - Shows "Using loaded: filename" for loaded files
  - "Upload Different" button to change loaded files
  - Status indicator shows loaded files
  - Preview shows available files before loading

#### Database Path Loading
- ✅ **Database Configuration**
  - Database path now included in saved configuration
  - Auto-populated when loading previous config
  - Ensures checkpoint compatibility

### Use Cases Enabled
- ✅ **Exact Re-runs**: Load everything from previous run with one click
- ✅ **Selective Modification**: Load config + some files, change others
- ✅ **Template Workflows**: Load config without files for different repositories
- ✅ **Guaranteed Reproduction**: Exact same files as before

### Technical Implementation
- Added `saved_repositories/` directory structure
- Added `save_uploaded_file()` helper function
- Added `load_file_from_path()` helper function
- Enhanced session state with `loaded_repo_files`
- Updated execution logic to handle both uploaded and loaded files
- Updated all execution modes (Fresh, Resume, Fork) to save files

### 📝 Documentation
- Added `COMPLETE_SETUP_LOADING.md` - Complete guide for v1.3.1 features
- Updated all existing documentation to reflect new capabilities

### 🔧 Changed
- Metadata structure now includes file paths (v1.3.1 format)
- Footer updated to v1.3.1
- App version metadata set to "1.3.1"

### 🐛 Fixed
- File loading now works seamlessly with execution
- Loaded files properly used instead of requiring re-upload

---

## [1.3.0] - 2025-11-30

### 🎉 Added - Configuration Loading Feature

#### Load Previous Run Configurations
- ✅ **New Sidebar Section**: "📋 Load Previous Config"
  - Browse all previous runs with saved configurations
  - Select from dropdown showing run_id and timestamp
  - Load configuration with one click
  - Preview configuration JSON before loading
  - Clear loaded configuration to start fresh
  
#### Automatic Configuration Saving
- ✅ **Comprehensive Metadata Storage**
  - Saves configuration for all execution modes (Fresh/Resume/Fork)
  - Stores: LLM model, max cycles, base directory, execution mode
  - Tracks: Reconciliation mode, fork relationships, timestamps
  - Uses existing `run_metadata` database table
  - Fully backward compatible (old runs show "No metadata available")

#### Auto-population of Settings
- ✅ **Smart Form Population**
  - LLM Model: Auto-selected from loaded config
  - Max Cycles: Auto-filled from loaded config
  - Base Directory: Auto-detected and selected from loaded config
  - All settings remain editable after loading
  - Help text indicates when settings are loaded

#### Enhanced History Tab
- ✅ **Configuration Display for Each Run**
  - Shows configuration summary (LLM, cycles, mode)
  - Displays base directory and reconciliation mode
  - Shows fork relationships if applicable
  - Full configuration viewable in expandable JSON section

#### Use Cases Enabled
- ✅ **Quick Re-runs**: Load exact settings from successful runs
- ✅ **Repository Comparison**: Test different repos with same config
- ✅ **Configuration Templates**: Create and reuse optimized settings
- ✅ **Reproducibility**: Guarantee exact same settings as previous runs

#### Technical Implementation
- Uses existing `OrchestratorDB.save_run_metadata()` and `get_run_metadata()`
- Session state tracking: `loaded_config` and `config_loaded_from_run`
- Database path initialization fix for early access
- Configuration saved at orchestrator creation for all modes
- Resume mode updates existing metadata with latest settings

### 📝 Documentation
- Added `CONFIG_LOADING_FEATURE.md` - Comprehensive guide (400+ lines)
  - Usage instructions and examples
  - Technical details and API reference
  - Troubleshooting and migration guide
- Added `CONFIG_LOADING_SUMMARY.md` - Quick reference
  - One-page summary with use cases
  - Quick start guide
- Added `CONFIG_LOADING_UI_GUIDE.md` - Visual walkthrough
  - UI screenshots and layouts
  - User interaction flows
  - Error states and best practices
- Added `CONFIGURATION_LOADING_IMPLEMENTATION.md` - Developer guide
  - Implementation summary
  - Code examples and test cases
- Updated `README.md` - Feature announcement
- Updated Help tab - Usage instructions

### 🔧 Changed
- Footer updated to v1.3
- Sidebar reorganized with config loading at top
- Runtime settings enhanced with auto-population logic

### 🐛 Fixed
- Database path initialization order in sidebar

---

## [1.2.0] - 2025-11-30

### 🎉 Added - Repository Forking Feature

#### Fork from Checkpoint Mode
- ✅ **New Execution Mode**: "Fork from Checkpoint"
  - Load state from one run
  - Execute with a different repository
  - Start fresh execution history
  - Enables repository chaining workflows
  
#### Reconciliation Mode Selection
- ✅ **Separated Execution Mode from Reconciliation Mode**
  - Execution Mode: Fresh Run / Resume / Fork (main choice)
  - Reconciliation Mode: PATCH / OVERWRITE / FILL_GAPS (Advanced Options)
  - **Smart defaults:** 
    - **PATCH for Resume** - Safe for same repo with bug fixes
    - **OVERWRITE for Fork** - Essential for repository chaining (keeps data despite signature differences)
  - Users can override defaults as needed in Advanced Options

#### UI Enhancements
- ✅ **New Run ID Field**: Specify custom run ID for forked runs
  - Auto-generates if left empty (`fork-abc123...`)
  - Supports semantic naming for better organization
- ✅ **Forking Status Messages**: Clear feedback when forking
  - Shows source run ID
  - Shows new run ID
  - Confirms state transfer

#### Use Cases Enabled
- ✅ **Repository Chaining**: Connect repositories in pipelines (e.g., addition → combination)
- ✅ **Multi-stage Processing**: Load data → Process → Analyze → Visualize
- ✅ **Testing Variations**: Run same input through different repositories
- ✅ **Reuse Expensive Computations**: Don't re-run costly operations

#### Technical Implementation
- ✅ Uses `Orchestrator.load_checkpoint()` with `new_run_id` parameter
- ✅ Automatically applies PATCH mode for safe state transfer
- ✅ Resets execution counters and cycle count
- ✅ Preserves completed concept data from source run
- ✅ Compatible with existing checkpoint database

### 📝 Documentation
- Added `FORKING_GUIDE.md` - Comprehensive forking tutorial
  - Step-by-step instructions
  - Example workflows (addition→combination)
  - Best practices
  - Troubleshooting guide
- Updated Help tab with forking section
  - Example: Addition → Combination pipeline
  - Use cases and benefits
- Updated README with forking feature mention

### 🔧 Technical Changes
- Modified execution mode selection UI
- Added fork handling in orchestrator initialization
- Added `import uuid` for auto-generating fork IDs
- Enhanced status messaging for forking

---

## [1.1.0] - 2025-11-30

### 🎉 Added - Comprehensive Logging Features

#### UI/UX Improvements
- ✅ **Compact Log Display**
  - Reduced font size (0.7rem) for log content
  - Tighter line spacing (1.25) for better density
  - Smaller log headers using `<small>` tags
  - Reduced padding and margins for more content on screen
  - Thinner dividers between log entries

#### Results Tab Enhancements
- ✅ **Quick Log Access Section**
  - View recent logs (last 10 entries) immediately after execution
  - Expandable full logs viewer for runs with more entries
  - Export logs to JSON directly from Results tab
  - No need to switch tabs for debugging

#### History Tab Enhancements
- ✅ **Execution History Viewer**
  - See all execution records with status, cycle, and concept info
  - Visual status indicators (✅ success, ❌ failed, ⏳ pending)
  - Collapsible summary view

- ✅ **Detailed Logs Viewer with Filtering**
  - Filter by "All Logs" - view everything
  - Filter by "Cycle" - focus on specific execution phase
  - Filter by "Status" - find failures or successes
  - Code-formatted log display for readability
  - Export filtered logs to JSON

- ✅ **Log Statistics**
  - Total log entries count
  - Quick summaries and metadata

#### Help Tab Enhancements
- ✅ **New Documentation Section**: "Execution Logs & History"
  - Where to find logs (Results vs History)
  - How to filter and export
  - Log content explanation
  - Session Log vs Database Logs comparison

#### Other Improvements
- ✅ Better error handling for missing logs
- ✅ Informative messages when logs aren't available
- ✅ Updated footer to v1.1 with logging badge
- ✅ Updated README with logging features

### 📝 Documentation
- Added `LOGGING_FEATURES_UPDATE.md` - Comprehensive documentation of new features
- Updated `README.md` - Added logging features to features list
- Updated Help tab - New logging section with usage instructions

### 🔧 Technical Changes
- Leveraged existing `OrchestratorDB` methods:
  - `get_all_logs(run_id)`
  - `get_execution_history(run_id)`
  - `get_logs_for_execution(execution_id)`
- No breaking changes
- Fully backward compatible with existing databases
- No new dependencies

### 🐛 Fixed
- **Issue**: Fork mode was using PATCH reconciliation, causing data loss
  - When forking (e.g., Addition → Combination), concepts like `{new number pair}` have different signatures in each repo
  - PATCH mode discarded them due to signature mismatch
  - Caused "missing ground concept data" errors
- **Solution**: 
  - Default to OVERWRITE mode for forking (keeps all checkpoint data)
  - Default to PATCH mode for resuming (safe for same repo)
  - Allow users to override in Advanced Options
- **Impact**: Repository chaining workflows now work correctly

---

## [1.0.0] - 2025-11-30

### 🎉 Initial Release

#### Core Features
- 📁 Upload repository files (concepts, inferences, inputs)
- 🚀 Execute orchestrations with configurable parameters
- 💾 Checkpoint & resume functionality (PATCH/OVERWRITE/FILL_GAPS)
- 📊 View final concepts and results
- 📜 Browse history of runs and checkpoints
- 💾 Export results as JSON

#### Tabs
- **Execute Tab**: File upload, configuration, and execution
- **Results Tab**: View final concepts and export
- **History Tab**: Browse runs and checkpoints (basic)
- **Help Tab**: Built-in documentation

#### Configuration Options
- LLM model selection (qwen-plus, gpt-4o, claude-3-sonnet, qwen-turbo-latest)
- Max cycles configuration
- Base directory selection
- Database path configuration
- Resume modes (Fresh, PATCH, OVERWRITE, FILL_GAPS)

#### Documentation
- `QUICK_START_APP.md` - Quick start guide
- `STREAMLIT_APP_GUIDE.md` - Comprehensive user guide
- `APP_ARCHITECTURE.md` - Technical architecture
- `APP_SUMMARY.md` - Implementation summary
- `README.md` - Project overview

#### Launchers
- `run_app.py` - Python launcher with dependency checks
- `run_app.bat` - Windows batch launcher
- `run_app.ps1` - PowerShell launcher

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- **Major.Minor.Patch** (e.g., 1.1.0)
  - **Major**: Breaking changes
  - **Minor**: New features (backward compatible)
  - **Patch**: Bug fixes

---

## Upgrade Guide

### From v1.0 to v1.1

**No action required!** v1.1 is fully backward compatible.

**What's new:**
1. Open any run in the **History** tab to view logs
2. Check the **Results** tab after execution for quick log access
3. Use filters to find specific log entries
4. Export logs for offline analysis

**Existing features:**
- All v1.0 features continue to work exactly as before
- No configuration changes needed
- Existing databases work without migration

---

## Future Roadmap

### Potential v1.2 Features
- [ ] Real-time log streaming during execution (WebSocket)
- [ ] Text search within logs
- [ ] Pagination for large log sets
- [ ] Advanced filtering (date range, regex)

### Potential v1.3 Features
- [ ] Execution timeline visualization
- [ ] Dependency graph with log annotations
- [ ] HTML/PDF report generation
- [ ] Success/failure rate analytics

### Potential v2.0 Features
- [ ] Multi-user support
- [ ] Cloud storage integration
- [ ] Collaborative editing
- [ ] Version control integration

---

**Last Updated**: November 30, 2025

