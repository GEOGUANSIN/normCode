"""
Extract Field Script

Extracts a specific field from a dictionary or structured data.
Used by paradigm: h_Data-c_ExtractField-o_Literal
"""

from typing import Any, Optional, List


def extract_field(data: Any, field_path: str) -> Any:
    """
    Extract a field from data using a dot-separated path.
    
    Args:
        data: Dictionary or nested structure
        field_path: Path like "operations" or "nested.field.value"
    
    Returns:
        The value at the specified path
    
    Raises:
        KeyError: If path doesn't exist
        TypeError: If data isn't subscriptable at some point in path
    """
    if not field_path:
        return data
    
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


def extract_field_safe(data: Any, field_path: str, default: Any = None) -> Any:
    """
    Safe version that returns default if path doesn't exist.
    """
    try:
        return extract_field(data, field_path)
    except (KeyError, IndexError, TypeError):
        return default


def infer_field_from_context(context: str) -> Optional[str]:
    """
    Infer field name from natural language context.
    
    Examples:
        "get operations from extraction data" -> "operations"
        "extract concepts from data" -> "concepts"
    """
    # Common extraction patterns
    patterns = [
        ("operations", ["operations", "operation list"]),
        ("concepts", ["concepts", "concept list"]),
        ("dependencies", ["dependencies", "dependency list"]),
        ("control_patterns", ["control patterns", "patterns"]),
    ]
    
    context_lower = context.lower()
    for field_name, keywords in patterns:
        for keyword in keywords:
            if keyword in context_lower:
                return field_name
    
    return None


# Entry point for orchestrator
def main(inputs: dict) -> Any:
    """
    Main entry point called by orchestrator.
    
    Args:
        inputs: Dict with 'data' and optionally 'field_path' or context
    
    Returns:
        The extracted field value
    """
    data = inputs.get('data')
    field_path = inputs.get('field_path')
    
    # If no explicit field path, try to infer from context
    if not field_path and 'context' in inputs:
        field_path = infer_field_from_context(inputs['context'])
    
    if not field_path:
        raise ValueError("No field_path specified and couldn't infer from context")
    
    return extract_field(data, field_path)


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

