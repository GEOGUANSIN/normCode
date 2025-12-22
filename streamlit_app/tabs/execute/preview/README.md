# Preview Module

Refactored preview components for the Execute tab, providing enhanced visualization of concepts, inferences, and input data.

## Module Structure

```
preview/
├── __init__.py          # Main entry point with render_file_previews()
├── utils.py             # Shared utilities
├── tensor_display.py    # Tensor rendering and editing
├── card_view.py         # Card-based preview components
├── graph_view.py        # Graph visualization
└── README.md           # This file
```

## Components

### 1. `__init__.py` - Main Entry Point

Exports the primary function:
- `render_file_previews()` - Orchestrates the entire preview UI

### 2. `utils.py` - Utility Functions

**Concept Categorization:**
- `get_concept_category()` - Categorize concepts by name pattern
- `get_category_style()` - Get styling (emoji, color) for categories

**Tensor Utilities:**
- `get_tensor_shape()` - Calculate shape of nested list data
- `get_tensor_shape_str()` - Human-readable shape string
- `count_dimensions()` - Count tensor dimensions

**Value Formatting:**
- `format_cell_value()` - Format values for display (handles special syntax like `%()`)

**Tensor Slicing:**
- `slice_tensor()` - Extract 2D slices from N-D tensors
- `get_slice_description()` - Generate slice description text

### 3. `tensor_display.py` - Tensor Rendering

**Main Display Functions:**
- `render_tensor_input()` - Entry point for tensor/value display
- `render_simple_input()` - Non-tensor value display
- `render_tensor_display()` - Tensor display orchestrator

**Display-Only Renderers:**
- `render_scalar_value()` - 0D (scalar) values
- `render_1d_tensor()` - 1D arrays (inline or list view)
- `render_2d_tensor()` - 2D matrices (HTML table)
- `render_2d_tensor_html()` - HTML table implementation
- `render_interactive_tensor_viewer()` - 3D+ tensors with axis selectors

**Editable Renderers:**
- `render_editable_scalar()` - Edit scalar values
- `render_editable_1d_tensor()` - Edit 1D arrays
- `render_editable_2d_tensor()` - Edit 2D matrices
- `render_editable_nd_tensor()` - Edit N-D tensors (JSON mode)

### 4. `card_view.py` - Card-Based Preview

**Main Functions:**
- `render_card_view()` - Orchestrate card view layout

**Concepts:**
- `render_concepts_preview()` - Concepts list with metrics
- `render_concept_card()` - Single concept card with badges

**Inferences:**
- `render_inferences_preview()` - Inferences list with metrics
- `render_inference_card()` - Single inference card with flow arrows

**Inputs:**
- `render_inputs_preview()` - Input data preview with edit mode
- `render_metadata_section()` - Metadata fields (_comment, _note, etc.)

**Concept Repo:**
- `render_concept_repo_references()` - Pre-defined reference data

### 5. `graph_view.py` - Graph Visualization

**Main Functions:**
- `render_graph_view()` - Orchestrate graph view
- `render_zoomable_graph_with_vizjs()` - Interactive graph with Viz.js

**DOT Generation:**
- `build_graphviz_source()` - Generate Graphviz DOT syntax
- `escape_dot()` - Escape special characters for DOT
- `get_node_style()` - Calculate node styles based on attributes

**Fallback:**
- `render_text_flow()` - Text-based flow representation

## Features

### Card View
- **Visual Categorization**: Color-coded concept types (semantic functions, values, syntactic)
- **Badges**: Ground (🌱), Final (🎯), Invariant (🔒)
- **Metrics**: Total, ground, final, invariant counts
- **Tensor Display**: Interactive viewers for multi-dimensional data
- **Edit Mode**: Live editing of input values

### Graph View
- **Interactive Visualization**: Pan, zoom, fit-to-view
- **Pure JavaScript**: Uses Viz.js (no system binaries needed)
- **Downloadable**: Export as SVG
- **Node Styling**: Color and shape by concept type
- **Edge Types**: Function (solid) vs value (dashed) relationships

### Tensor Features
- **Multi-dimensional Support**: 0D to N-D tensors
- **Axis Selection**: Interactive slicer for 3D+ tensors
- **Edit Mode**: Inline editing for 0D-2D, JSON for 3D+
- **Special Syntax**: Handles `%(value)` wrapping
- **Responsive Layout**: Adapts to tensor size

## Usage

```python
from streamlit_app.tabs.execute.preview import render_file_previews

# In your Streamlit app:
render_file_previews(
    config={
        'concepts_file': 'path/to/concepts.json',
        'inferences_file': 'path/to/inferences.json',
        'inputs_file': 'path/to/inputs.json'  # Optional
    },
    loaded_concepts=None,  # Or pre-loaded dict
    loaded_inferences=None,
    loaded_inputs=None
)
```

## Backward Compatibility

The original `preview_components.py` now imports from this module, maintaining full backward compatibility with existing code.

## Design Principles

1. **Separation of Concerns**: Each module handles a specific aspect
2. **Reusability**: Utility functions shared across components
3. **Progressive Enhancement**: Fallbacks for missing data/features
4. **User Experience**: Interactive, responsive, visually clear
5. **Performance**: Minimal reruns, efficient state management

## Dependencies

- **Streamlit**: UI framework
- **Viz.js** (CDN): Graph rendering (no local install needed)
- **svg-pan-zoom** (CDN): Interactive graph controls

## Future Enhancements

- [ ] Advanced graph layouts (hierarchical, circular)
- [ ] Tensor statistics and validation
- [ ] Export capabilities (JSON, CSV)
- [ ] Search and filter within previews
- [ ] Diff view for comparing versions

