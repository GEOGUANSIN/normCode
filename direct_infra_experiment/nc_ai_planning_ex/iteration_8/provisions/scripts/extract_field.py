"""
Extract Field Script

Extracts a specific field from a dictionary or structured data.
Used by paradigm: v_ScriptLocation-h_Literal-c_Execute-o_Literal

Enhanced version:
- Handles dict, list, or JSON/Python string input
- Supports Python dict repr format (single quotes, None instead of null)
- Supports dot-notation paths like "nested.field.value"
- For lists of stringified dicts, searches for the element containing the field
- Returns input as-is if no field specified
- Returns None if field not found (safe by default)
"""

from typing import Any
import json
import ast


def _parse(value: Any) -> Any:
    """
    Parse string to object. Handles:
    - JSON strings (double quotes, null)
    - Python dict repr strings (single quotes, None)
    - Returns as-is if not a string or parsing fails
    """
    if not isinstance(value, str):
        return value
    
    # First try JSON parsing
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Then try Python literal eval (handles single quotes, None, True, False)
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        pass
    
    return value


def _get(data: Any, key: str) -> Any:
    """Get a single key from dict or index from list."""
    data = _parse(data)
    if isinstance(data, dict):
        return data.get(key)
    if isinstance(data, (list, tuple)):
        try:
            return data[int(key)]
        except (ValueError, IndexError):
            return None
    return None


def _find_field_in_list(data_list: list, field: str) -> Any:
    """
    Search through a list of (possibly stringified) dicts to find one containing the field.
    
    This handles the case where extraction data is stored as:
    [
      "instruction text...",
      "{'concepts': [...], ...}",
      "{'operations': [...], ...}",
      ...
    ]
    
    Returns the field value from the first dict that contains it.
    """
    for item in data_list:
        parsed = _parse(item)
        if isinstance(parsed, dict) and field in parsed:
            return parsed.get(field)
    return None


def extract_field(input_1: Any, input_2: str = None, body=None) -> Any:
    """
    Extract a field from data.
    
    Args:
        input_1: The data (dict, list, or JSON/Python string)
        input_2: Field name or dot-path like "concepts" or "tree.nodes"
                 If None, returns input_1 as-is
        body: Optional Body instance (unused)
    
    Returns:
        The extracted value, or None if not found
    
    Examples:
        extract_field({"a": 1}, "a")           -> 1
        extract_field({"x": {"y": 2}}, "x.y")  -> 2
        extract_field([1, 2, 3], "1")          -> 2
        extract_field(data, None)              -> data (passthrough)
        
        # List of stringified dicts (Phase 2 extraction format):
        extract_field(["{'operations': [...]}", "{'concepts': [...]}"], "operations")
        -> [...]  (searches list for dict containing 'operations')
    """
    # Parse input if it's a string
    data = _parse(input_1)
    
    # No field specified = passthrough
    if not input_2:
        return data
    
    # Get the first part of the path
    parts = input_2.split('.')
    first_key = parts[0]
    
    # Try direct access first
    current = None
    if isinstance(data, dict):
        current = data.get(first_key)
    elif isinstance(data, (list, tuple)):
        # First try numeric index
        try:
            current = data[int(first_key)]
        except (ValueError, IndexError):
            # Not a numeric index - search for field in list elements
            current = _find_field_in_list(data, first_key)
    
    if current is None:
        return None
    
    # Navigate remaining path parts
    for part in parts[1:]:
        current = _get(current, part)
        if current is None:
            return None
    
    return current


# Main entry point for paradigm
def main(input_1: Any = None, input_2: str = None, body=None, **kwargs) -> Any:
    """Main entry point for paradigm execution."""
    return extract_field(input_1, input_2, body)


if __name__ == "__main__":
    # Test cases
    print("=== Dict tests ===")
    test = {"concepts": ["a", "b"], "tree": {"root": "goal", "nodes": {"x": 1}}}
    print(f"concepts: {extract_field(test, 'concepts')}")
    print(f"tree.root: {extract_field(test, 'tree.root')}")
    print(f"tree.nodes.x: {extract_field(test, 'tree.nodes.x')}")
    print(f"missing: {extract_field(test, 'missing')}")
    print(f"passthrough: {extract_field(test, None)}")
    
    print("\n=== List tests ===")
    test_list = [{"a": 1}, {"b": 2}]
    print(f"index 0: {extract_field(test_list, '0')}")
    print(f"index 1.b: {extract_field(test_list, '1.b')}")
    
    print("\n=== JSON string tests ===")
    json_str = '{"result": {"answer": 42}}'
    print(f"result.answer: {extract_field(json_str, 'result.answer')}")
    
    print("\n=== No thinking field (just result) ===")
    no_thinking = {"result": "just the answer"}
    print(f"result: {extract_field(no_thinking, 'result')}")
    
    print("\n=== Already extracted (no wrapper) ===")
    already_extracted = {"concepts": ["x", "y"], "summary": {"count": 2}}
    print(f"concepts: {extract_field(already_extracted, 'concepts')}")
    print(f"passthrough: {extract_field(already_extracted, None)}")
    
    print("\n=== Phase 2 extraction format (list of stringified Python dicts) ===")
    # This is the actual format from the derivation execution
    phase2_data = [
        "Build a simple calculator...",
        "{'concepts': [{'name': 'two numbers'}], 'summary': {'count': 1}}",
        "{'operations': [{'name': 'add numbers'}], 'summary': {'count': 1}}",
        "{'dependencies': [{'from': 'a', 'to': 'b'}]}",
        "{'patterns': [{'type': 'linear'}]}"
    ]
    print(f"operations: {extract_field(phase2_data, 'operations')}")
    print(f"concepts: {extract_field(phase2_data, 'concepts')}")
    print(f"dependencies: {extract_field(phase2_data, 'dependencies')}")
    print(f"patterns: {extract_field(phase2_data, 'patterns')}")
    
    print("\n=== Python dict with None ===")
    python_dict_str = "{'value': None, 'items': [1, 2, None]}"
    print(f"value: {extract_field(python_dict_str, 'value')}")
    print(f"items: {extract_field(python_dict_str, 'items')}")
