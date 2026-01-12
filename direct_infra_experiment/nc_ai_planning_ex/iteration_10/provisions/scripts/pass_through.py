"""
Pass Through Script - Identity function for NormCode.

Simply returns the input unchanged. Used when an operation
needs to "return" a value without transformation.
"""


def pass_through(input_1, body=None):
    """
    Pass through the input unchanged.
    
    Args:
        input_1: Any value to pass through
        body: Optional Body instance (not used)
        
    Returns:
        The input value unchanged
    """
    return input_1


# Alias for paradigm compatibility
def main(input_1, body=None):
    """Alias for paradigm compatibility."""
    return pass_through(input_1, body)

