# Changelog - NormCode Orchestrator Streamlit App

All notable changes to this project will be documented in this file.

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
- **Issue**: Detailed execution logs stored in database were not accessible through the UI
- **Solution**: Added comprehensive log viewing in Results and History tabs
- **Impact**: Users can now debug and analyze executions effectively
- **Technical Fix**: Used checkboxes instead of nested expanders to avoid Streamlit API limitations

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

