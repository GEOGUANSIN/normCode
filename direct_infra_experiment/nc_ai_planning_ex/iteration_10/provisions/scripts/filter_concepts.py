"""
Filter Concepts Script - Remove comment lines from parsed NCDS.

Filters the parsed line list to keep only concept lines (type == "main"),
excluding pure comment lines.
"""

from typing import Any, Dict, List


def filter_concepts(input_1: List[Dict[str, Any]], body=None) -> List[Dict[str, Any]]:
    """
    Filter out comment lines, keeping only concept lines.
    
    Args:
        input_1: List of parsed line dictionaries from ncds_parser
        body: Optional Body instance (not used)
        
    Returns:
        Filtered list containing only lines where type == "main"
    """
    if not input_1:
        return []
    
    return [line for line in input_1 if line.get("type") == "main"]


# Alias for paradigm compatibility
def main(input_1: List[Dict[str, Any]], body=None) -> List[Dict[str, Any]]:
    """Alias for paradigm compatibility."""
    return filter_concepts(input_1, body)

