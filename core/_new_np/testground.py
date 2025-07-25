from typing import Union, List, Dict, Any


def find_list_depth(obj: Any) -> int:
    """
    Find the maximum depth of nested lists in a structure.
    
    Args:
        obj: The object to analyze (can be list, dict, or other types)
        
    Returns:
        Maximum depth of nested lists (0 for non-lists, 1 for flat lists, etc.)
        
    Examples:
        find_list_depth([1, 2, 3]) -> 1
        find_list_depth([[1, 2], [3, 4]]) -> 2
        find_list_depth([[[1]], [2, [3]]]) -> 3
        find_list_depth({"key": [1, 2]}) -> 0
    """
    if not isinstance(obj, list):
        return 0
    
    if not obj:  # Empty list
        return 1
    
    max_depth = 1
    for item in obj:
        if isinstance(item, list):
            item_depth = find_list_depth(item)
            max_depth = max(max_depth, 1 + item_depth)
    
    return max_depth


def find_list_depth_with_paths(obj: Any, current_path: str = "") -> List[tuple]:
    """
    Find the depth of nested lists and return paths to each list.
    
    Args:
        obj: The object to analyze
        current_path: Current path in the structure
        
    Returns:
        List of tuples (path, depth) for each list found
    """
    results = []
    
    def _traverse(item, path):
        if isinstance(item, list):
            depth = find_list_depth(item)
            results.append((path, depth))
            
            for i, sub_item in enumerate(item):
                new_path = f"{path}[{i}]" if path else f"[{i}]"
                _traverse(sub_item, new_path)
        elif isinstance(item, dict):
            for key, value in item.items():
                new_path = f"{path}.{key}" if path else key
                _traverse(value, new_path)
    
    _traverse(obj, current_path)
    return results


def analyze_structure_depth(obj: Any) -> Dict[str, Any]:
    """
    Comprehensive analysis of structure depth.
    
    Args:
        obj: The object to analyze
        
    Returns:
        Dictionary with depth analysis information
    """
    if isinstance(obj, list):
        max_depth = find_list_depth(obj)
        paths = find_list_depth_with_paths(obj)
        
        return {
            "type": "list",
            "max_depth": max_depth,
            "paths": paths,
            "is_empty": len(obj) == 0,
            "element_count": len(obj)
        }
    elif isinstance(obj, dict):
        paths = find_list_depth_with_paths(obj)
        max_depth = max([depth for _, depth in paths]) if paths else 0
        
        return {
            "type": "dict",
            "max_depth": max_depth,
            "paths": paths,
            "key_count": len(obj)
        }
    else:
        return {
            "type": type(obj).__name__,
            "max_depth": 0,
            "paths": [],
            "value": obj
        }


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("Simple flat list", [1, 2, 3]),
        ("Nested lists", [[1, 2], [3, 4]]),
        ("Deep nested", [[[1]], [2, [3]]]),
        ("Mixed structure", {"key": [1, [2, 3]], "other": [4, 5]}),
        ("Empty list", []),
        ("Single element", [42]),
        ("Complex nested", [[[[1, 2], 3], [4, [5, 6]]], [7, 8]])
    ]
    
    print("Depth Analysis Results:")
    print("=" * 50)
    
    for name, test_obj in test_cases:
        depth = find_list_depth(test_obj)
        analysis = analyze_structure_depth(test_obj)
        
        print(f"\n{name}:")
        print(f"  Object: {test_obj}")
        print(f"  Max depth: {depth}")
        print(f"  Analysis: {analysis}")
        
        if analysis["paths"]:
            print("  Paths with depths:")
            for path, path_depth in analysis["paths"]:
                print(f"    {path}: depth {path_depth}") 