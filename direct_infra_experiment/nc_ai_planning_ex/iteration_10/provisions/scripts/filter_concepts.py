"""
Filter Concepts Script - Remove comment lines from parsed NCDS.

Filters the parsed line list to keep only concept lines (type == "main"),
excluding pure comment lines.
"""

import ast
import json
from typing import Any, Dict, List, Union


def parse_string_input(input_str: str) -> Any:
    """
    Parse a string that might be JSON or Python repr format.
    
    The literal wrapping uses Python's str() which gives:
    - Single quotes instead of double quotes
    - None instead of null
    
    This function handles both formats.
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
    
    # Return None if neither works
    return None


def filter_concepts(input_1: Union[List[Dict[str, Any]], str], body=None) -> List[Dict[str, Any]]:
    """
    Filter out comment lines, keeping only concept lines.
    
    Args:
        input_1: List of parsed line dictionaries from ncds_parser
                 (may be a string repr if passed through literal wrapping)
        body: Optional Body instance (not used)
        
    Returns:
        Filtered list containing only lines where type == "main"
    """
    if not input_1:
        return []
    
    # Handle case where input is a string (from literal wrapping)
    data = input_1
    if isinstance(input_1, str):
        data = parse_string_input(input_1)
        if data is None:
            return []
    
    # Ensure we have a list
    if not isinstance(data, list):
        return []
    
    return [line for line in data if isinstance(line, dict) and line.get("type") == "main"]


# Alias for paradigm compatibility
def main(input_1: Union[List[Dict[str, Any]], str], body=None) -> List[Dict[str, Any]]:
    """Alias for paradigm compatibility."""
    return filter_concepts(input_1, body)

