"""
Extract Field Script

Extracts a specific field from a dictionary or structured data.
Used by paradigm: v_ScriptLocation-h_Literal-c_Execute-o_Literal

Function Signature Requirements (New Vision):
- Parameters named input_1, input_2, etc. matching value concept order
- Optional 'body' parameter for tool access
- Direct return value (no 'result' variable)
"""

from typing import Any, Optional


def extract_field(
    input_1: Any,          # data (from {extraction data})
    input_2: str = None,   # field_name (from {field_name: "operations"})
    body=None              # Optional Body instance
) -> Any:
    """
    Extract a field from data using a field name or dot-separated path.
    
    Args:
        input_1: Dictionary or nested structure
        input_2: Field name like "operations" or path like "nested.field.value"
        body: Optional Body instance (not used, but available)
    
    Returns:
        The value at the specified field/path
    
    Raises:
        KeyError: If field doesn't exist
        TypeError: If data isn't a dict
    """
    data = input_1
    field_path = input_2
    
    if not field_path:
        raise ValueError("No field_name specified (input_2)")
    
    if not data:
        raise ValueError("No data provided (input_1)")
    
    # Handle dot-separated paths
    parts = field_path.split('.')
    current = data
    
    for part in parts:
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, (list, tuple)):
            # Allow numeric indices
            current = current[int(part)]
        else:
            raise TypeError(f"Cannot access '{part}' on {type(current)}")
    
    return current


def extract_field_safe(
    input_1: Any,
    input_2: str = None,
    default: Any = None,
    body=None
) -> Any:
    """
    Safe version that returns default if field doesn't exist.
    """
    try:
        return extract_field(input_1, input_2, body)
    except (KeyError, IndexError, TypeError, ValueError):
        return default


if __name__ == "__main__":
    # Test
    test_data = {
        "concepts": ["review", "sentiment", "summary"],
        "operations": ["extract", "analyze", "generate"],
        "nested": {
            "field": {
                "value": 42
            }
        }
    }
    
    print(f"operations: {extract_field(test_data, 'operations')}")
    print(f"nested.field.value: {extract_field(test_data, 'nested.field.value')}")
