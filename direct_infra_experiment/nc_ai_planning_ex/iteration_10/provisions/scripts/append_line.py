"""
Append Line Script - Append a formalized line to existing content.

Used for incremental file building - appends each formalized line
to the growing .ncd file content.
"""

import ast
import json
from typing import Any, Union


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


def extract_string(value: Any) -> str:
    """Extract string content from potentially wrapped value."""
    if value is None:
        return ""
    
    # If it's a string, try to parse it first
    if isinstance(value, str):
        parsed = parse_string_input(value)
        if isinstance(parsed, dict):
            # LLM output might have 'formalized_line' or 'content' key
            return str(parsed.get('formalized_line', 
                      parsed.get('content', 
                      parsed.get('data', value))))
        elif isinstance(parsed, str):
            return parsed
        return value
    
    # If it's a dict, extract content
    if isinstance(value, dict):
        return str(value.get('formalized_line', 
                  value.get('content', 
                  value.get('data', str(value)))))
    
    return str(value)


def append_line(input_1: Any, input_2: Any, body=None) -> str:
    """
    Append a new line to existing content.
    
    Args:
        input_1: The current content (may be empty, None, or wrapped)
        input_2: The new line to append (may be wrapped from LLM output)
        body: Optional Body instance (not used)
        
    Returns:
        The combined content with the new line appended
    """
    current = extract_string(input_1)
    new_line = extract_string(input_2)
    
    # Handle None or empty inputs
    if not current and not new_line:
        return ""
    
    if not current:
        return new_line
    
    if not new_line:
        return current
    
    # Ensure proper line separation
    if current.endswith('\n'):
        return current + new_line
    else:
        return current + '\n' + new_line


# Alias for paradigm compatibility
def main(input_1: Any, input_2: Any, body=None) -> str:
    """Alias for paradigm compatibility."""
    return append_line(input_1, input_2, body)

