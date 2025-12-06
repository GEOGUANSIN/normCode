<!-- 2d32bc6a-00eb-4a26-aaf1-d56601112103 66b7a434-0faa-435e-bafc-ed22fa4581d7 -->
# Customize Paradigms Tab

## Architecture

Create a new `paradigms/` package under `streamlit_app/tabs/` following the existing pattern used by `execute/` and `results/` tabs. Custom paradigms will be stored in `streamlit_app/custom_paradigms/`.

## Key Files

- **Built-in paradigms source**: [`infra/_agent/_models/_paradigms/`](infra/_agent/_models/_paradigms/) (read-only)
- **Custom paradigms storage**: `streamlit_app/custom_paradigms/` (new directory)
- **Tab package**: `streamlit_app/tabs/paradigms/` (new package)

## Implementation

### 1. Create Custom Paradigms Directory

Create `streamlit_app/custom_paradigms/` with an empty `__init__.py` to store user-created paradigms.

### 2. Create Paradigms Tab Package

Create `streamlit_app/tabs/paradigms/` with:

- `__init__.py` - exports `render_paradigms_tab`
- `paradigms_tab.py` - main tab entry point with tabbed interface (List / Create / Edit)
- `paradigm_loader.py` - utility to list/load paradigms from both built-in and custom directories
- `ui_components.py` - reusable UI components (paradigm card, JSON editor, step visualizer)

### 3. Core Features

- **List View**: Display all paradigms (built-in tagged as read-only, custom as editable) with cards showing name, inputs/outputs parsed from naming convention
- **View/Edit**: JSON editor with syntax highlighting, structured form for editing `env_spec` and `sequence_spec`
- **Create**: Template-based creation starting from existing paradigm or blank
- **Delete**: Remove custom paradigms only (built-in are protected)

### 4. Integration

- Update [`streamlit_app/tabs/__init__.py`](streamlit_app/tabs/__init__.py) to export `render_paradigms_tab`
- Update [`streamlit_app/app.py`](streamlit_app/app.py) to add the new tab

## UI Structure

```
Paradigms Tab
├── Sidebar: Filter (built-in/custom), search
└── Main Area:
    ├── Paradigm Cards Grid (clickable)
    └── Detail Panel (when selected):
        ├── Info header (name, source, I/O)
        ├── JSON viewer/editor
        └── Action buttons (Edit/Clone/Delete)
```

### To-dos

- [ ] Create streamlit_app/custom_paradigms/ directory with __init__.py
- [ ] Create paradigms/paradigm_loader.py - list/load from both directories
- [ ] Create paradigms/ui_components.py - paradigm cards, JSON editor
- [ ] Create paradigms/paradigms_tab.py - main tab with list/view/edit/create/delete
- [ ] Create paradigms/__init__.py and update tabs/__init__.py
- [ ] Update app.py to add Paradigms tab