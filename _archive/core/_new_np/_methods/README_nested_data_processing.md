# Nested Data Processing in Workspace Demo Methods

This document describes the enhanced nested data processing functionality added to the workspace demo methods, allowing for automatic generation of all possible combinations from nested input data.

## Overview

The `_generation_function_n` function in `_workspace_demo.py` has been enhanced to automatically detect and process nested data structures. When nested data is detected, the function:

1. Generates all possible combinations using the utility functions from `_util_nested_list.py`
2. Processes each combination individually through the LLM
3. Aggregates all results into a single output

## Key Features

### 1. Automatic Nested Data Detection
The function automatically detects when input data contains nested structures:
```python
has_nested_data = any(isinstance(item, list) and len(item) > 1 for item in input_list)
```

### 2. Combination Generation
Uses `get_combinations_dict_and_indices()` from `_util_nested_list.py` to generate all possible combinations.

### 3. Relation Extraction Support
Supports relation extraction guides to extract specific fields from dictionary structures within nested data.

### 4. Filter Constraints
Supports filter constraints to limit combinations based on specific rules (e.g., requiring certain elements to have matching sub-indices).

## Configuration

### Working Configuration Structure
Add the following fields to your working configuration's `perception.ap` section:

```json
{
  "perception": {
    "ap": {
      "relation_extraction": true,
      "relation_extraction_guide": {
        "0": "{technical_concepts}",
        "1": "{relatable_ideas}"
      },
      "filter_constraints": [[0, 1]]
    }
  }
}
```

### Parameters

- `relation_extraction` (bool): Enable relation extraction from nested data
- `relation_extraction_guide` (dict): Maps rank-1 indices to keys to extract from dictionaries
- `filter_constraints` (list): List of constraint groups, each containing indices that must have matching sub-indices

## Usage Examples

### Basic Nested Data Processing
```python
# Input with nested lists
nested_data = [
    ["apple", "banana", "orange"],
    ["red", "yellow", "orange"],
    ["fruit", "tropical", "citrus"]
]

# Function automatically generates all combinations:
# - apple + red + fruit
# - apple + red + tropical
# - apple + red + citrus
# - apple + yellow + fruit
# ... and so on
```

### Technical Concepts with Extraction
```python
# Input with dictionaries
technical_data = [
    "technical_concepts",
    [
        {
            "{technical_concepts}": "cloud architecture",
            "{relatable_ideas}": "virtual LEGO set"
        },
        {
            "{technical_concepts}": "latency",
            "{relatable_ideas}": "traffic jam"
        }
    ]
]

# With extraction guide: {1: "{technical_concepts}", 1: "{relatable_ideas}"}
# Extracts: "cloud architecture", "virtual LEGO set", "latency", "traffic jam"
```

### Filtered Combinations
```python
# Complex nested data
complex_data = [
    [["A1", "A2"], ["B1", "B2"]],
    [["X1", "X2"], ["Y1", "Y2"]],
    ["simple1", "simple2"]
]

# Filter constraint: [[0, 1]] means elements 0 and 1 must have same sub-indices
# This ensures A1 pairs with X1, A2 pairs with X2, etc.
```

## Integration with Existing Code

The enhanced functionality is backward compatible. Existing code that doesn't use nested data will continue to work unchanged. The function automatically detects whether nested processing is needed.

### Function Signature Changes
The `_create_actuator_function` now accepts additional parameters:
```python
def _create_actuator_function(
    actuator_translated_template, 
    instruction_template, 
    instruction_validation_template,
    system_message, 
    concept_to_infer_name, 
    input_length, 
    llm, 
    relation_extraction=False, 
    relation_extraction_guide=None, 
    filter_constraints=None
):
```

## Testing

Run the test examples to see the functionality in action:

```bash
# Basic test
python test_nested_processing.py

# Comprehensive examples
python nested_data_example.py
```

## Performance Considerations

- **Memory Usage**: Large nested structures can generate many combinations, potentially consuming significant memory
- **Processing Time**: Each combination is processed individually through the LLM, so processing time scales with the number of combinations
- **Rate Limiting**: Consider LLM API rate limits when processing large numbers of combinations

## Error Handling

The function includes robust error handling:
- Graceful fallback to original behavior for non-nested data
- Proper logging of combination generation and processing steps
- Error handling for malformed nested data structures

## Future Enhancements

Potential future improvements:
- Batch processing of combinations to reduce LLM API calls
- Caching of processed combinations
- Parallel processing of combinations
- More sophisticated filtering and constraint systems 