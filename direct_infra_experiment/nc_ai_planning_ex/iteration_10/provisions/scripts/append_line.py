"""
Append Line Script - Append a formalized line to existing content.

Used for incremental file building - appends each formalized line
to the growing .ncd file content.
"""

from typing import Any


def append_line(input_1: str, input_2: str, body=None) -> str:
    """
    Append a new line to existing content.
    
    Args:
        input_1: The current content (may be empty or None)
        input_2: The new line to append
        body: Optional Body instance (not used)
        
    Returns:
        The combined content with the new line appended
    """
    current = input_1 or ""
    new_line = input_2 or ""
    
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
def main(input_1: str, input_2: str, body=None) -> str:
    """Alias for paradigm compatibility."""
    return append_line(input_1, input_2, body)

