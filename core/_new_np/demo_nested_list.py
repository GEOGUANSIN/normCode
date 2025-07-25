import ast

# Nested List Operations Module
# Core functionality for working with nested lists, dictionaries, and filtering combinations

def simplify_extracted_value(value):
    """
    Simplify extracted values by flattening nested lists to simple strings or flat lists.
    
    Args:
        value: The value to simplify (could be nested lists, strings, etc.)
    
    Returns:
        Simplified value (string or flat list)
    """
    if isinstance(value, str):
        return value
    elif isinstance(value, list):
        # Flatten the list recursively
        flattened = []
        for item in value:
            if isinstance(item, list):
                result = simplify_extracted_value(item)
                if isinstance(result, list):
                    flattened.extend(result)
                else:
                    flattened.append(result)
            else:
                flattened.append(item)
        # If we have multiple items, return the list; if single item, return just the item
        return flattened if len(flattened) > 1 else flattened[0] if flattened else ""
    else:
        return value

def extract_from_combinations(combos_dict, extraction_guide):
    """
    Extract values from combinations based on extraction guide and modify combo dict in-place.
    
    Args:
        combos_dict: dict mapping tuple(indices) -> combination (list of values)
        extraction_guide: dict mapping rank-1 indices to keys to extract
            e.g. {0: "{technical_concepts}", 1: "{relatable_ideas}"}
    
    Returns:
        None (modifies combos_dict in-place)
    """
    for idx_tuple, combo in combos_dict.items():
        for rank1_idx, key in extraction_guide.items():
            if rank1_idx < len(combo):
                element = combo[rank1_idx]
                if isinstance(element, dict) and key in element:
                    extracted_value = element[key]
                    combo[rank1_idx] = simplify_extracted_value(extracted_value)

def get_combinations_dict_and_indices(nested_data, filter_constraints=None, extraction_guide=None):
    """
    Main function: Returns combinations as dictionary and list of index tuples.
    
    Args:
        nested_data: The nested list to process (can contain lists, dicts, or mixed types)
        filter_constraints: list of lists, e.g. [[1,3]] means elements 1 and 3 
                           must have the same sub-indices (ignoring rank 1 index)
        extraction_guide: dict mapping rank-1 indices to keys to extract from dicts at those positions
            e.g. {0: "{technical_concepts}", 1: "{relatable_ideas}"}
    
    Returns:
        tuple: (combos_dict, all_indices, extracted_values_dict) where:
            - combos_dict: dict mapping tuple(indices) -> combination (list of values)
            - all_indices: list of tuple(indices), in the same order as combinations
            - extracted_values_dict: dict mapping tuple(indices) -> dict of extracted values (empty if extraction_guide is None)
    """
    nested_data = evaluate_rank1_elements(nested_data)
    combos_dict = {}
    all_indices = []
    
    for combo, indices in all_combinations(nested_data):
        idx_tuple = tuple(tuple(idx) for idx in indices)
        if satisfies_filter_constraints(idx_tuple, filter_constraints):
            combos_dict[idx_tuple] = combo
            all_indices.append(idx_tuple)
    
    # Apply extraction if guide is provided
    if extraction_guide:
        extract_from_combinations(combos_dict, extraction_guide)
    
    return combos_dict, all_indices

def all_combinations(nested_data):
    """Generate all possible combinations by picking one element from each rank 1 element."""
    nested_data = evaluate_rank1_elements(nested_data)
    def helper(data, path_prefix=None):
        if path_prefix is None:
            path_prefix = []
        
        # Handle different data types
        if isinstance(data, dict):
            # Treat dictionaries as atomic units
            yield ([data], [path_prefix])
            return
        elif not isinstance(data, list):
            # For non-list, non-dict types (strings, numbers, etc.)
            yield ([data], [path_prefix])
            return
        elif data is nested_data:
            # Top-level list - generate combinations across all elements
            iterators = []
            for i, element in enumerate(data):
                picks = list(helper(element, [i]))
                iterators.append(picks)
            from itertools import product
            for combo in product(*iterators):
                values = [c[0][0] for c in combo]
                indices = [c[1][0] for c in combo]
                yield (values, indices)
        else:
            # Regular list - iterate through elements
            for j, sub in enumerate(data):
                for val, idxs in helper(sub, path_prefix + [j]):
                    yield (val, idxs)
    yield from helper(nested_data)

def extract_one_from_each_rank1(nested_data):
    """Extract one element from each rank 1 element, recursively going down the first element."""
    results = []
    for i, element in enumerate(nested_data):
        indices = [i]
        current = element
        while isinstance(current, list) and current:
            # Only traverse lists, not dictionaries
            current = current[0]
            indices.append(0)
        results.append((current, indices))
    return results

# Helper Functions
def satisfies_filter_constraints(idx_tuple, filter_constraints):
    """Check if a combination satisfies the given filter constraints."""
    if not filter_constraints:
        return True
    
    for constraint_group in filter_constraints:
        if len(constraint_group) > 1:
            first_sub_indices = idx_tuple[constraint_group[0]][1:]
            for idx in constraint_group[1:]:
                current_sub_indices = idx_tuple[idx][1:]
                if current_sub_indices != first_sub_indices:
                    return False
    return True

def evaluate_rank1_elements(nested_data):
    """Evaluate stringified lists/dicts at rank 1 of the nested data."""
    evaluated = []
    for el in nested_data:
        if isinstance(el, str):
            el_strip = el.strip()
            if (el_strip.startswith("[") and el_strip.endswith("]")) or \
               (el_strip.startswith("{") and el_strip.endswith("}")):
                try:
                    evaluated.append(ast.literal_eval(el_strip))
                    continue
                except Exception:
                    pass
        evaluated.append(el)
    return evaluated

# Example Data and Demonstration
def create_nested_list_example():
    """Create a nested list with duplicate elements at rank 1."""
    return [
        "fruits",
        ["apple", "banana", "orange"],
        [
            ["orange", "lemon", "lime"],
            ["banana", "mango", "pineapple"],
            ["apple", "pear", "cherry"]
        ],
        ["apple", "banana", "orange"]  # Duplicate of element 1
    ]

def create_technical_concepts_example():
    """Create an example with dictionaries and nested structures."""
    return [
        "technical_concepts",
        [
            {
                "{technical_concepts}": "cloud architecture",
                "{relatable_ideas}": [[["Cloud architecture is like a virtual LEGO set for computers — just like how you can snap together LEGO pieces to build different structures, cloud architecture lets you combine virtual servers, storage, and networks to create IT solutions without needing physical hardware."]]]
            },
            {
                "{technical_concepts}": "latency",
                "{relatable_ideas}": [[["Latency is like a traffic jam on the information highway — the more congested it is, the longer it takes for data to reach its destination."]]]
            }
        ],
        ["server", "database", "network"],
        {
            "concept_type": "infrastructure",
            "examples": ["AWS", "Azure", "GCP"]
        }
    ]

def demonstrate_functionality(nested_data, title="Nested List Operations"):
    """Demonstrate all functionality in a concise way."""
    print(f"=== {title} ===\n")
    
    # Show data structure
    print("Data structure:")
    for i, element in enumerate(nested_data):
        print(f"  [{i}]: {element}")
    print()
    
    # Show rank 1 extraction
    print("Rank 1 extraction (first element from each):")
    results = extract_one_from_each_rank1(nested_data)
    for element, indices in results:
        print(f"  {element} (indices: {indices})")
    print()
    
    # Show combinations with filtering
    print("Combinations with different filters:")
    
    # Unfiltered
    unfiltered_dict, unfiltered_indices = get_combinations_dict_and_indices(nested_data)
    print(f"  Unfiltered: {len(unfiltered_indices)} combinations")
    
    # Filtered (if applicable)
    if len(nested_data) > 1:
        filtered_dict, filtered_indices = get_combinations_dict_and_indices(nested_data, [[0,1]])
        print(f"  Filtered [[0,1]]: {len(filtered_indices)} combinations")
    
    # Show examples
    print("\nExample combinations:")
    for i, (idx_tuple, combo) in enumerate(list(unfiltered_dict.items())[:3]):
        print(f"  {i+1}. {combo} -> {idx_tuple}")

def demonstrate_stringified_json_example():
    """Demonstrate with stringified JSON-style input as rank 1 elements."""
    print("=== Stringified JSON Example ===\n")
    data = [
        "[{'{technical_concepts}': 'cloud architecture', '{relatable_ideas}': [[['Cloud architecture is like a virtual LEGO set for computers — just like how you can snap together LEGO pieces to build different structures, cloud architecture lets you combine virtual servers, storage, and networks to create IT solutions without needing physical hardware.']]]}, {'{technical_concepts}': 'latency', '{relatable_ideas}': [[['Latency is like a traffic jam on the information highway — the more congested it is, the longer it takes for data to reach its destination.']]]}]",
        "[{'{technical_concepts}': 'cloud architecture', '{relatable_ideas}': [[['Cloud architecture is like a virtual LEGO set for computers — just like how you can snap together LEGO pieces to build different structures, cloud architecture lets you combine virtual servers, storage, and networks to create IT solutions without needing physical hardware.']]]}, {'{technical_concepts}': 'latency', '{relatable_ideas}': [[['Latency is like a traffic jam on the information highway — the more congested it is, the longer it takes for data to reach its destination.']]]}]"
    ]
    # Extraction guide for stringified JSON: extract both keys from both dicts in each list
    extraction_guide = {0: "{technical_concepts}", 1: "{relatable_ideas}"}
    # Apply filter to show only combinations where elements 0 and 1 have same sub-indices
    filter_constraints = [[0, 1]]
    demonstrate_functionality_with_extraction(data, "Stringified JSON as Rank 1 Elements", extraction_guide, filter_constraints)

def demonstrate_functionality_with_extraction(nested_data, title, extraction_guide, filter_constraints=None):
    print(f"=== {title} (with extraction) ===\n")
    print("Data structure:")
    for i, element in enumerate(nested_data):
        print(f"  [{i}]: {element}")
    print()
    
    # Show both unfiltered and filtered results
    print("Unfiltered combinations:")
    unfiltered_dict, unfiltered_indices = get_combinations_dict_and_indices(nested_data, extraction_guide=extraction_guide)
    print(f"  Total combinations: {len(unfiltered_indices)}")
    for i, idx_tuple in enumerate(list(unfiltered_dict.keys())[:3]):
        print(f"    {i+1}. Combo: {unfiltered_dict[idx_tuple]} -> {idx_tuple}")
    
    if filter_constraints:
        print(f"\nFiltered combinations (filter: {filter_constraints}):")
        filtered_dict, filtered_indices = get_combinations_dict_and_indices(nested_data, filter_constraints=filter_constraints, extraction_guide=extraction_guide)
        print(f"  Total combinations: {len(filtered_indices)}")
        for i, idx_tuple in enumerate(list(filtered_dict.keys())[:3]):
            print(f"    {i+1}. Combo: {filtered_dict[idx_tuple]} -> {idx_tuple}")

# Module execution
if __name__ == "__main__":
    print("=== Basic Example ===\n")
    data1 = create_nested_list_example()
    demonstrate_functionality(data1, "Basic Nested List Example")
    
    print("\n" + "="*50 + "\n")
    
    print("=== Technical Concepts Example ===\n")
    data2 = create_technical_concepts_example()
    # Extraction guide for technical concepts: extract both keys from each dict in element 1
    extraction_guide = {1: "{technical_concepts}", 1: "{relatable_ideas}"}
    # Apply filter to show only combinations where elements 0 and 1 have same sub-indices
    filter_constraints = [[0, 1]]
    demonstrate_functionality_with_extraction(data2, "Technical Concepts with Dictionaries", extraction_guide, filter_constraints)
    
    print("\n" + "="*50 + "\n")
    
    demonstrate_stringified_json_example()


    
