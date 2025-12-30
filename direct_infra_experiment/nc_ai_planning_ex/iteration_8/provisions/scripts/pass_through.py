"""
Pass Through Script

Identity function that returns data unchanged.
Used by paradigm: h_Data-c_PassThrough-o_Literal
"""

from typing import Any


def pass_through(data: Any) -> Any:
    """
    Return data unchanged (identity function).
    
    Args:
        data: Any data
    
    Returns:
        The same data unchanged
    """
    return data


# Entry point for orchestrator
def main(inputs: dict) -> Any:
    """
    Main entry point called by orchestrator.
    
    Args:
        inputs: Dict with 'data'
    
    Returns:
        The input data unchanged
    """
    return inputs.get('data')


if __name__ == "__main__":
    # Test
    test_data = {"key": "value", "nested": [1, 2, 3]}
    result = pass_through(test_data)
    print(f"Input:  {test_data}")
    print(f"Output: {result}")
    print(f"Same object: {test_data is result}")  # True

