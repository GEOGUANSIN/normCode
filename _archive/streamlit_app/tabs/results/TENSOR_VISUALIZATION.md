# Tensor Visualization in Results Tab

## Overview

The Results tab now features **enhanced tensor visualization** by reusing components from the Execute tab's preview system. This provides a rich, interactive display of concept results with support for multi-dimensional tensors.

## What Changed

### Before (Basic Display)

```python
# Old display: Simple code block
st.code(str(concept_entry.concept.reference.tensor), language="python")
```

**Limitations:**
- ❌ Raw text output only
- ❌ No structure for multi-dimensional data
- ❌ Hard to read large tensors
- ❌ No interactive exploration
- ❌ No axis labels or shape information

### After (Enhanced Display)

```python
# New display: Rich tensor visualization
from .concept_display import display_concept_result_enhanced

display_concept_result_enhanced(concept_entry, filter_option)
```

**Features:**
- ✅ Interactive tensor viewer
- ✅ Support for 0D to N-D tensors
- ✅ Axis labels and shape information
- ✅ Category-based styling
- ✅ Slicing controls for high-dimensional data
- ✅ Multiple view modes (Table, List, JSON)

## Supported Tensor Types

### Scalar (0D)
- **Display:** Single value in styled box
- **Example:** Temperature, count, flag

### 1D Tensor
- **Display:** Horizontal list or vertical scrolling list
- **Example:** Feature vector, sequence

### 2D Tensor
- **Display:** Styled table with row/column labels
- **Example:** Matrix, grid, spreadsheet

### N-D Tensor (3D+)
- **Display:** Interactive slicer with axis selectors
- **Features:**
  - Choose which 2 axes to display
  - Slider controls for other dimensions
  - View different slices of the data
  - Current slice indicator
  
## Category-Based Styling

Concepts are automatically categorized and styled:

### 🟣 Semantic Functions
- Pattern: `:({})` or `:<{}>` 
- Color: Purple/Violet
- Example: `state:({initial})`

### 🔵 Semantic Values
- Pattern: `{}`, `<>`, `[]`
- Color: Blue
- Example: `{temperature}`, `<user_input>`

### ⚫ Syntactic Functions
- Pattern: Everything else
- Color: Gray
- Example: `compute_average`, `process_data`

## Component Reuse

The tensor visualization reuses components from `execute/preview/`:

### From `tensor_display.py`
- `render_tensor_display()` - Main display function
- `render_scalar_value()` - Scalar display
- `render_1d_tensor()` - 1D list display
- `render_2d_tensor()` - 2D table display
- `render_interactive_tensor_viewer()` - N-D slicer

### From `utils.py`
- `get_tensor_shape()` - Calculate tensor dimensions
- `get_tensor_shape_str()` - Format shape string
- `format_cell_value()` - Format individual cells
- `slice_tensor()` - Extract tensor slices
- `get_concept_category()` - Categorize concepts
- `get_category_style()` - Get styling for category

## Usage Example

### In Results Tab

When viewing orchestration results:

1. Navigate to **Results** tab
2. Expand a concept to view details
3. See enhanced visualization:
   - Metadata bar (Category, Type, Shape)
   - Interactive tensor display
   - Axis labels and dimensions

### For Different Tensor Types

**Scalar Example:**
```
Concept: {total_count}
Shape: scalar
Display: Large centered value
```

**2D Matrix Example:**
```
Concept: {confusion_matrix}
Shape: 3×3
Display: Table with row/column headers
```

**4D Tensor Example:**
```
Concept: {video_frames}
Shape: 30×480×640×3
Display: Interactive slicer
- Select 2 axes to display (e.g., height×width)
- Sliders for other axes (frame, color channel)
- View current slice: frame[5] × height[:] × width[:] × channel[0]
```

## Benefits

### 1. **Consistent Experience**
- Same visualization in Execute (preview) and Results tabs
- Users familiar with one will understand the other
- Reduces learning curve

### 2. **Better Data Understanding**
- Visual structure matches conceptual structure
- Easy to spot patterns and anomalies
- Interactive exploration of large tensors

### 3. **Code Reuse**
- Single source of truth for tensor display logic
- Bugs fixed in one place benefit both tabs
- Easier to add new features

### 4. **Maintainability**
- Centralized visualization logic
- Clear separation of concerns
- Well-tested components

## Technical Details

### Import Structure

```python
# In concept_display.py
from ..execute.preview.tensor_display import render_tensor_display
from ..execute.preview.utils import (
    get_concept_category,
    get_category_style,
    get_tensor_shape_str
)
```

### Read-Only Mode

Results are displayed in **read-only mode** (unlike Execute tab preview):

```python
render_tensor_display(
    concept_name=concept_name,
    data=tensor_data,
    axes=axes,
    source="repo",
    editable=False  # Read-only in results
)
```

### Styling Differences

Execute tab preview uses **green** for input data:
- Border: `#22c55e` (green)
- Background: Green gradient

Results tab uses **indigo** for repo data:
- Border: `#6366f1` (indigo)
- Background: Purple/blue gradient

## Future Enhancements

Possible improvements:

1. **Comparison Mode** - Compare tensors across runs
2. **Export Views** - Export specific slices as CSV
3. **Statistics** - Show min/max/mean for numeric tensors
4. **Heatmaps** - Color-coded display for numeric 2D tensors
5. **Diff View** - Highlight changes between expected/actual
6. **Search/Filter** - Find specific values in large tensors

## See Also

- `execute/preview/README.md` - Preview system documentation
- `execute/preview/tensor_display.py` - Tensor display implementation
- `execute/preview/utils.py` - Utility functions

