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
import json
import ast


def _parse_value(value: Any) -> Any:
    """
    Attempt to parse a value that might be a JSON/Python string representation.
    Returns the parsed value, or the original if parsing fails.
    """
    if not isinstance(value, str):
        return value
    
    # Try JSON first
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Try Python literal (handles {'key': 'value'} syntax with single quotes)
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        pass
    
    return value


def _find_field_in_list(data_list: list, field_name: str) -> Any:
    """
    Search through a list of items to find one containing the specified field.
    Each item may be a string that needs parsing.
    """
    top_level_field = field_name.split('.')[0]
    
    for item in data_list:
        parsed_item = _parse_value(item)
        if isinstance(parsed_item, dict) and top_level_field in parsed_item:
            return parsed_item
    
    raise KeyError(f"Field '{field_name}' not found in any list item")


def extract_field(
    input_1: Any,          # data (from {extraction data})
    input_2: str = None,   # field_name (from {field_name: "operations"})
    body=None              # Optional Body instance
) -> Any:
    """
    Extract a field from data using a field name or dot-separated path.
    
    Args:
        input_1: Dictionary, list, or JSON/Python string representation
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
    
    # Parse data if it's a string
    data = _parse_value(data)
    
    # If data is a list, search for an item containing the field
    if isinstance(data, list):
        top_level_field = field_path.split('.')[0]
        # Check if first part is a numeric index
        try:
            idx = int(top_level_field)
            # It's a numeric index, get that element and continue
            data = _parse_value(data[idx])
            field_path = '.'.join(field_path.split('.')[1:]) if '.' in field_path else None
            if not field_path:
                return data
        except ValueError:
            # Not a numeric index, search for field in list items
            data = _find_field_in_list(data, field_path)
    
    # Handle dot-separated paths
    parts = field_path.split('.')
    current = data
    
    for part in parts:
        # Parse current if it's still a string
        current = _parse_value(current)
        
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


# Main entry point for paradigm (calls extract_field)
def main(input_1: Any = None, input_2: str = None, body=None, **kwargs) -> Any:
    """Main entry point for paradigm execution."""
    return extract_field(input_1, input_2, body)


if __name__ == "__main__":
    # Test with dict
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
    
    # Test with list of strings (like extraction data)
    test_list = [
        "Build a simple calculator",
        "{'thinking': 'test', 'concepts': ['a', 'b']}",
        "{'thinking': 'test2', 'operations': ['op1', 'op2', 'op3']}",
        "{'thinking': 'test3', 'dependencies': ['dep1']}"
    ]
    
    print(f"\nFrom list - operations: {extract_field(test_list, 'operations')}")
    print(f"From list - concepts: {extract_field(test_list, 'concepts')}")
    
    # Test with JSON string
    json_str = '["item1", "item2", {"key": "value", "nested": {"deep": 123}}]'
    print(f"\nFrom JSON - 2.nested.deep: {extract_field(json_str, '2.nested.deep')}")
