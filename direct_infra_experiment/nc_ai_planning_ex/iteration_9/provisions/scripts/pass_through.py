"""
Pass Through Script

Identity function that returns data unchanged.
Used by paradigm: v_ScriptLocation-h_Literal-c_Execute-o_Literal

Function Signature Requirements (New Vision):
- Parameters named input_1, input_2, etc. matching value concept order
- Optional 'body' parameter for tool access
- Direct return value (no 'result' variable)
"""

from typing import Any


def pass_through(
    input_1: Any,    # data to pass through
    body=None        # Optional Body instance
) -> Any:
    """
    Return data unchanged (identity function).
    
    Args:
        input_1: Any data
        body: Optional Body instance (not used, but available)
    
    Returns:
        The same data unchanged
    """
    return input_1


# Main entry point for paradigm (calls pass_through)
def main(input_1: Any = None, body=None, **kwargs) -> Any:
    """Main entry point for paradigm execution."""
    return pass_through(input_1, body)


if __name__ == "__main__":
    # Test
    test_data = {"key": "value", "nested": [1, 2, 3]}
    result = pass_through(test_data)
    print(f"Input:  {test_data}")
    print(f"Output: {result}")
    print(f"Same object: {test_data is result}")  # True
