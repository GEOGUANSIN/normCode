"""
Check Type Script - Compare concept type against expected type.

Used for conditional branching in formalization - checks if a concept's
type matches the expected type for type-specific formalization.
"""

import ast
import json
from typing import Any


def parse_string_input(input_str: str) -> Any:
    """
    Parse a string that might be JSON or Python repr format.
    """
    # Try JSON first (double quotes, null)
    try:
        return json.loads(input_str)
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Try Python literal eval (single quotes, None)
    try:
        return ast.literal_eval(input_str)
    except (ValueError, SyntaxError):
        pass
    
    # Return original string if neither works
    return input_str


def check_type(input_1: Any, input_2: str = None, body=None) -> bool:
    """
    Check if the concept type equals the expected type.
    
    Args:
        input_1: The concept type string (e.g., "object", "imperative")
                 OR a dict with 'concept_type' key
                 OR a string repr of a dict
        input_2: The expected type to match (e.g., "object")
        body: Optional Body instance (not used)
        
    Returns:
        True if types match, False otherwise
    """
    # Handle string input (JSON or Python repr from literal wrapping)
    data = input_1
    if isinstance(input_1, str):
        data = parse_string_input(input_1)
    
    # Handle dict input (from LLM response)
    if isinstance(data, dict):
        actual_type = data.get("concept_type", data.get("type", ""))
    else:
        actual_type = str(data) if data else ""
    
    # Normalize both types for comparison
    actual_normalized = actual_type.lower().strip()
    expected_normalized = (input_2 or "").lower().strip()
    
    return actual_normalized == expected_normalized


# Alias for paradigm compatibility
def main(input_1: Any, input_2: str = None, body=None) -> bool:
    """Alias for paradigm compatibility."""
    return check_type(input_1, input_2, body)

