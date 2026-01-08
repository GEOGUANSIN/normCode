"""
Extract Field Script

Extracts a specific field from a dictionary or structured data.
Used by paradigm: v_ScriptLocation-h_Literal-c_Execute-o_Literal

Simplified version:
- Handles dict, list, or JSON string input
- Supports dot-notation paths like "nested.field.value"
- Returns input as-is if no field specified
- Returns None if field not found (safe by default)
"""

from typing import Any
import json


def _parse(value: Any) -> Any:
    """Parse JSON string to object, or return as-is."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
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


def extract_field(input_1: Any, input_2: str = None, body=None) -> Any:
    """
    Extract a field from data.
    
    Args:
        input_1: The data (dict, list, or JSON string)
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
    """
    # Parse input if it's a string
    data = _parse(input_1)
    
    # No field specified = passthrough
    if not input_2:
        return data
    
    # Navigate dot-path
    current = data
    for part in input_2.split('.'):
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
