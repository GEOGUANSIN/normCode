# Streamlit App Directory Structure

## Overview

The Streamlit app has been organized into a clean, modular structure for better maintainability and clarity.

## Directory Structure

```
streamlit_app/
├── app.py                    # Main entry point
│
├── core/                     # Core utilities and configuration
│   ├── __init__.py
│   ├── config.py            # Configuration constants and session state
│   ├── file_utils.py        # File handling utilities
│   └── verification.py      # Repository file verification
│
├── ui/                       # UI components
│   ├── __init__.py
│   ├── ui_components.py     # Reusable UI components and styling
│   └── sidebar.py           # Sidebar configuration UI
│
├── orchestration/            # Orchestration execution logic
│   ├── __init__.py
│   └── orchestration_runner.py  # Orchestrator creation and execution
│
├── tabs/                     # Tab modules
│   ├── __init__.py
│   ├── execute_tab.py       # Execute orchestration tab
│   ├── results_tab.py       # Results viewer tab
│   ├── history_tab.py       # Execution history tab
│   └── help_tab.py          # Help/documentation tab
│
├── tools/                    # Custom tools
│   ├── __init__.py
│   └── user_input_tool.py   # Streamlit input tool for human-in-the-loop
│
├── docs/                     # Documentation
│   └── ...
│
├── generated_scripts/        # Generated Python scripts
├── generated_prompts/        # Generated prompt files
├── saved_repositories/       # Saved repository files
│
└── [other files]            # Configuration files, run scripts, etc.
```

## Module Organization

### `core/` - Core Utilities
**Purpose:** Foundation utilities used throughout the app

- **`config.py`**: 
  - Configuration constants (paths, defaults, model lists)
  - Session state initialization
  - State management helpers

- **`file_utils.py`**: 
  - File upload/download operations
  - File path management
  - JSON parsing utilities

- **`verification.py`**: 
  - Repository file validation
  - Dependency checking
  - Error reporting

### `ui/` - UI Components
**Purpose:** User interface components and styling

- **`ui_components.py`**: 
  - Reusable UI display functions
  - Custom CSS styling
  - Component rendering helpers

- **`sidebar.py`**: 
  - Complete sidebar UI
  - Configuration widgets
  - File uploaders
  - Settings management

### `orchestration/` - Execution Logic
**Purpose:** Orchestration creation and execution

- **`orchestration_runner.py`**: 
  - Orchestrator creation (fresh/resume/fork)
  - Input injection
  - File verification coordination
  - Execution state management

### `tabs/` - Tab Modules
**Purpose:** Individual tab implementations

- **`execute_tab.py`**: Main execution interface
- **`results_tab.py`**: Results viewer and export
- **`history_tab.py`**: Execution history and logs
- **`help_tab.py`**: Documentation and guides

## Import Structure

### From `app.py`:
```python
from core import init_session_state
from ui import apply_custom_styling, render_main_header, render_footer, render_sidebar
from tabs import render_execute_tab, render_results_tab, render_history_tab, render_help_tab
```

### Within packages:
- **Relative imports** (e.g., `from ..core.config import ...`)
- **Package imports** via `__init__.py` (e.g., `from core import ...`)

## Benefits

1. **Clear Separation**: Each folder has a distinct purpose
2. **Easy Navigation**: Find files quickly by their function
3. **Scalability**: Easy to add new modules in appropriate folders
4. **Maintainability**: Related code is grouped together
5. **Clean Root**: Main directory only contains entry point and config files

## Adding New Features

### New Core Utility
Add to `core/` directory and export via `core/__init__.py`

### New UI Component
Add to `ui/` directory and export via `ui/__init__.py`

### New Tab
Add to `tabs/` directory and export via `tabs/__init__.py`

### New Tool
Add to `tools/` directory and export via `tools/__init__.py`

## File Count Summary

- **Core modules**: 3 files
- **UI modules**: 2 files
- **Orchestration modules**: 1 file
- **Tab modules**: 4 files
- **Total organized modules**: 10 files
- **Main entry point**: 1 file (`app.py`)

This organization keeps the codebase clean, maintainable, and easy to navigate! 🎉

