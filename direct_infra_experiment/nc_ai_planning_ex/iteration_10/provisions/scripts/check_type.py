"""
Check Type Script - Compare concept type against expected type.

Used for conditional branching in formalization - checks if a concept's
type matches the expected type for type-specific formalization.
"""

from typing import Any


def check_type(input_1: Any, input_2: str = None, body=None) -> bool:
    """
    Check if the concept type equals the expected type.
    
    Args:
        input_1: The concept type string (e.g., "object", "imperative")
                 OR a dict with 'concept_type' key
        input_2: The expected type to match (e.g., "object")
        body: Optional Body instance (not used)
        
    Returns:
        True if types match, False otherwise
    """
    # Handle dict input (from LLM response)
    if isinstance(input_1, dict):
        actual_type = input_1.get("concept_type", input_1.get("type", ""))
    else:
        actual_type = str(input_1) if input_1 else ""
    
    # Normalize both types for comparison
    actual_normalized = actual_type.lower().strip()
    expected_normalized = (input_2 or "").lower().strip()
    
    return actual_normalized == expected_normalized


# Alias for paradigm compatibility
def main(input_1: Any, input_2: str = None, body=None) -> bool:
    """Alias for paradigm compatibility."""
    return check_type(input_1, input_2, body)

