# Results Tab Package

This package contains the refactored Results tab for the NormCode Orchestrator Streamlit App.

## Structure

- **`results_tab.py`** - Main tab module (entry point)
- **`constants.py`** - Configuration constants and display settings
- **`ui_components.py`** - Reusable UI rendering components
- **`concept_display.py`** - Enhanced concept display with tensor visualization

## Usage

The package is imported in `streamlit_app/tabs/__init__.py`:

```python
from .results import render_results_tab
```

## Features

- ✅ Modular UI components
- ✅ Clean separation of concerns
- ✅ Easy to test and maintain
- ✅ Consistent with execute tab structure
- ✅ Execution logs with export functionality
- ✅ Concept results filtering and display
- ✅ JSON export for results and logs
- ✅ **Enhanced tensor visualization** - Reuses components from execute/preview
- ✅ **Interactive tensor display** - Supports 0D to N-D tensors
- ✅ **Category-based styling** - Semantic functions/values, syntactic functions

## Components

### `results_tab.py`
Main entry point that orchestrates the tab rendering. Handles the overall flow:
- Check for available results
- Display run information
- Coordinate logs and concepts display

### `ui_components.py`
Reusable UI rendering functions:
- `render_execution_logs()` - Display execution logs with expandable sections
- `render_export_button()` - Export results as JSON
- `render_final_concepts()` - Display concepts with filtering options
- `render_no_results_message()` - Empty state message
- `render_database_warning()` - Database not found warning

### `constants.py`
Configuration constants for display:
- Maximum number of recent logs to show
- Filter option labels
- Export file prefixes
- Display icons and formatting

### `concept_display.py`
Enhanced concept display with tensor visualization:
- `display_concept_result_enhanced()` - Enhanced concept display with tensor preview
- Reuses tensor display components from `execute/preview`
- Category-based styling (semantic functions/values, syntactic functions)
- Interactive tensor viewer for multi-dimensional data
- Read-only display (no editing in results view)

