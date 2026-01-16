from infra._states._judgement_states import States
from infra._core._reference import Reference
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Truth value markers
TRUE_MARKER = "%{truth value}(true)"
FALSE_MARKER = "%{truth value}(false)"


def _normalize_condition(condition: Any) -> Any:
    """
    Normalize a condition to match truth value markers.
    
    Converts Python booleans to their marker equivalents so comparisons work.
    - True / "true" -> "%{truth value}(true)"
    - False / "false" -> "%{truth value}(false)"
    """
    if condition is True or condition == "true":
        return TRUE_MARKER
    elif condition is False or condition == "false":
        return FALSE_MARKER
    elif condition == TRUE_MARKER or condition == FALSE_MARKER:
        return condition
    else:
        # For non-boolean conditions, return as-is
        return condition


def _value_matches_condition(value: Any, condition: Any) -> bool:
    """
    Check if a value matches a condition.
    
    Handles wrapped values like '%b1a(%{truth value}(false))' or '%xyz(True)' 
    by checking if the condition (or its boolean equivalent) is contained 
    within the value string.
    
    Args:
        value: The value to check (may be wrapped)
        condition: The condition to match
        
    Returns:
        True if the value matches the condition
    """
    if value == condition:
        return True
    
    # Check if condition is contained in a wrapped value
    if isinstance(value, str) and isinstance(condition, str):
        # Direct containment check
        if condition in value:
            return True
        
        # Handle case variations for boolean markers
        # Condition might be "%{truth value}(true)" but value has "True" or "true"
        if condition == TRUE_MARKER:
            # Check for various true representations in wrapped values
            if "(True)" in value or "(true)" in value or "true)" in value:
                return True
        elif condition == FALSE_MARKER:
            # Check for various false representations in wrapped values
            if "(False)" in value or "(false)" in value or "false)" in value:
                return True
    
    return False

# Quantifier behaviors for edge cases
QUANTIFIER_ON_EMPTY = {
    "all": True,         # Vacuous truth
    "some": False,       # No witness
    "none": True,        # Vacuous truth  
    "exists": False,     # Must have elements
}


def _apply_quantifier_to_slice(
    slice_data: Any, 
    quantifier: str, 
    condition: Any,
    skip_value: str = "@#SKIP#@"
) -> bool:
    """
    Apply a collapsing quantifier to a tensor slice.
    
    Args:
        slice_data: The slice of tensor data (can be nested list or leaf)
        quantifier: One of "all", "some", "none", "exists"
        condition: Value to match against
        skip_value: Skip value marker
        
    Returns:
        Boolean result of applying the quantifier
    """
    if slice_data == skip_value:
        return QUANTIFIER_ON_EMPTY.get(quantifier, False)
    
    if not isinstance(slice_data, list):
        # Leaf value - use _value_matches_condition for wrapped value support
        if quantifier == "all":
            return _value_matches_condition(slice_data, condition)
        elif quantifier == "some":
            return _value_matches_condition(slice_data, condition)
        elif quantifier == "none":
            return not _value_matches_condition(slice_data, condition)
        elif quantifier == "exists":
            return slice_data != skip_value
        return False
    
    # Empty list
    if not slice_data:
        return QUANTIFIER_ON_EMPTY.get(quantifier, False)
    
    # Recurse into list
    if quantifier == "all":
        return all(_apply_quantifier_to_slice(item, quantifier, condition, skip_value) 
                   for item in slice_data)
    elif quantifier == "some":
        return any(_apply_quantifier_to_slice(item, quantifier, condition, skip_value) 
                   for item in slice_data)
    elif quantifier == "none":
        return all(_apply_quantifier_to_slice(item, quantifier, condition, skip_value) 
                   for item in slice_data)
    elif quantifier == "exists":
        return any(_apply_quantifier_to_slice(item, quantifier, condition, skip_value) 
                   for item in slice_data)
    
    return False


def _transform_leaf_to_truth(value: Any, condition: Any, skip_value: str = "@#SKIP#@") -> str:
    """Transform a single leaf value to a truth marker."""
    if value == skip_value:
        return skip_value
    return TRUE_MARKER if _value_matches_condition(value, condition) else FALSE_MARKER


def _hierarchical_collapse(
    tensor: Any,
    axes: List[str],
    filter_axis_index: int,
    criterion_quantifiers: Dict[int, str],  # axis_index -> quantifier
    condition: Any,
    skip_value: str = "@#SKIP#@",
    current_depth: int = 0
) -> Any:
    """
    Hierarchically collapse inner axes while preserving the filter axis.
    
    For each element along the filter axis, apply the criterion quantifiers
    to collapse inner axes, producing a boolean per filter-axis element.
    
    Args:
        tensor: The nested list tensor
        axes: List of axis names
        filter_axis_index: Index of the filter (for-each) axis
        criterion_quantifiers: Dict mapping axis indices to their quantifiers
        condition: Value to match against
        skip_value: Skip value marker
        current_depth: Current recursion depth
        
    Returns:
        Transformed tensor with truth markers along filter axis
    """
    if tensor == skip_value:
        return skip_value
    
    if not isinstance(tensor, list):
        # Leaf value - apply criterion if we've passed all axes
        return _transform_leaf_to_truth(tensor, condition, skip_value)
    
    if current_depth == filter_axis_index:
        # We're at the filter axis - evaluate each element
        result = []
        for i, element in enumerate(tensor):
            # For this element, apply criterion quantifiers to inner axes
            if criterion_quantifiers:
                # Get the innermost criterion quantifier
                inner_indices = sorted(criterion_quantifiers.keys())
                inner_quantifier = criterion_quantifiers[inner_indices[0]]
                
                logger.debug(f"Filter axis element [{i}]: {element}, quantifier='{inner_quantifier}', condition={condition}")
                
                # Apply quantifier to this slice
                passes = _apply_quantifier_to_slice(element, inner_quantifier, condition, skip_value)
                logger.debug(f"  -> passes={passes}")
                result.append(TRUE_MARKER if passes else FALSE_MARKER)
            else:
                # No criterion - just transform to truth mask
                result.append(_hierarchical_collapse(
                    element, axes, filter_axis_index, criterion_quantifiers,
                    condition, skip_value, current_depth + 1
                ))
        return result
    
    elif current_depth < filter_axis_index:
        # We're above the filter axis - recurse
        return [_hierarchical_collapse(
            item, axes, filter_axis_index, criterion_quantifiers,
            condition, skip_value, current_depth + 1
        ) for item in tensor]
    
    else:
        # We're below the filter axis - this shouldn't happen in normal flow
        # but handle by transforming to truth mask
        return [_hierarchical_collapse(
            item, axes, filter_axis_index, criterion_quantifiers,
            condition, skip_value, current_depth + 1
        ) if isinstance(item, list) else _transform_leaf_to_truth(item, condition, skip_value)
        for item in tensor]


def _simple_truth_mask(tensor: Any, condition: Any, skip_value: str = "@#SKIP#@") -> Any:
    """Transform entire tensor to truth mask without any collapsing."""
    if tensor == skip_value:
        return skip_value
    
    if isinstance(tensor, list):
        return [_simple_truth_mask(item, condition, skip_value) for item in tensor]
    
    return TRUE_MARKER if tensor == condition else FALSE_MARKER


def _global_collapse(tensor: Any, quantifier: str, condition: Any, skip_value: str = "@#SKIP#@") -> bool:
    """Apply a quantifier globally to the entire tensor."""
    return _apply_quantifier_to_slice(tensor, quantifier, condition, skip_value)


def _extract_true_indices(truth_mask: Any, axis_index: int, current_depth: int = 0) -> List[int]:
    """
    Extract indices along a specific axis where truth mask is true.
    
    Returns indices where the element (or any nested element) is TRUE_MARKER.
    """
    if not isinstance(truth_mask, list):
        return []
    
    if current_depth == axis_index:
        matching = []
        for idx, item in enumerate(truth_mask):
            if _contains_true(item):
                matching.append(idx)
        return matching
    else:
        # Recurse and collect unique indices
        all_indices = set()
        for item in truth_mask:
            if isinstance(item, list):
                sub_indices = _extract_true_indices(item, axis_index, current_depth + 1)
                all_indices.update(sub_indices)
        return sorted(list(all_indices))


def _contains_true(data: Any) -> bool:
    """Check if data contains any TRUE_MARKER."""
    if data == TRUE_MARKER:
        return True
    if isinstance(data, list):
        return any(_contains_true(item) for item in data)
    return False


def truth_inference_assertion(states: States) -> States:
    """
    TIA (Truth Inference Assertion) - Assert truth conditions on TVA output.
    
    OVERVIEW:
    Always produces a TRUTH MASK as the primary output. The truth mask preserves
    the tensor structure with each element transformed to truth value markers.
    
    QUANTIFIER TYPES:
    
    1. Collapsing Quantifiers (used as criterion for filtering):
       - "all": All elements in slice must match condition
       - "some": At least one element in slice must match
       - "none": No elements in slice may match
       - "exists": Slice must have at least one non-skip element
       
    2. Non-Collapsing Quantifiers (defines filter axis):
       - "for-each": Evaluate each element along this axis
    
    COMBINED PATTERN (Recommended for multi-axis):
    
    "For each document where SOME paragraph mentions keyword":
    {
        "quantifiers": {
            "document": "for-each",  # Filter axis: which documents
            "paragraph": "some"      # Criterion: how to evaluate each document
        },
        "condition": True
    }
    
    This produces a truth mask along the document axis:
    - Each document becomes TRUE_MARKER if it has SOME matching paragraph
    - Each document becomes FALSE_MARKER otherwise
    
    OUTPUTS:
    - truth_mask_reference: Reference with truth value markers (primary output)
    - condition_met: Boolean - did ANY element pass?
    
    The truth mask IS the complete result. Downstream steps can use it
    directly for filtering without needing separate index lists.
    """
    logger.debug("Executing Tool Inference Assertion (TIA)")
    
    tva_ref = states.get_reference("inference", "TVA")
    assertion = getattr(states, 'assertion_condition', None)
    
    # Pass-through if no assertion defined or no TVA reference
    if not assertion or not tva_ref:
        if tva_ref:
            states.set_reference("inference", "TIA", tva_ref)
        states.condition_met = True
        states.set_current_step("TIA")
        logger.debug("TIA pass-through: no assertion condition defined")
        return states
    
    quantifiers = assertion.get("quantifiers", {})
    raw_condition = assertion.get("condition", True)
    condition = _normalize_condition(raw_condition)  # Convert bool to marker format
    skip_value = tva_ref.skip_value if hasattr(tva_ref, 'skip_value') else "@#SKIP#@"
    
    logger.debug(f"TIA assertion: quantifiers={quantifiers}, condition={raw_condition} -> {condition}")
    
    # Separate quantifiers into filter (for-each) and criterion (collapsing)
    filter_axes = {}   # axis_name -> axis_index (for-each axes)
    criterion_axes = {}  # axis_name -> quantifier (collapsing axes)
    
    for axis_name, quantifier in quantifiers.items():
        if quantifier == "for-each":
            if axis_name in tva_ref.axes:
                filter_axes[axis_name] = tva_ref.axes.index(axis_name)
            else:
                logger.warning(f"Filter axis '{axis_name}' not found in reference axes {tva_ref.axes}")
        elif quantifier in ("all", "some", "none", "exists"):
            criterion_axes[axis_name] = quantifier
        else:
            logger.warning(f"Unknown quantifier '{quantifier}' for axis '{axis_name}'")
    
    tensor = tva_ref.tensor
    
    # Case 1: Only collapsing quantifiers (no for-each)
    # Apply globally and return scalar truth result
    if not filter_axes:
        if criterion_axes:
            # Apply all criterion quantifiers globally (AND them together)
            results = []
            for axis_name, quantifier in criterion_axes.items():
                result = _global_collapse(tensor, quantifier, condition, skip_value)
                results.append(result)
                logger.debug(f"Global collapse '{quantifier}': {result}")
            
            final_result = all(results) if results else True
            states.condition_met = final_result
            
            # Create scalar truth mask
            result_marker = TRUE_MARKER if final_result else FALSE_MARKER
            result_ref = Reference.from_data([result_marker], axis_names=['assertion_result'])
            states.set_reference("inference", "TIA", result_ref)
        else:
            # No quantifiers at all - just transform to simple truth mask
            truth_mask = _simple_truth_mask(tensor, condition, skip_value)
            states.condition_met = _contains_true(truth_mask)
            result_ref = Reference(
                axes=tva_ref.axes.copy(),
                shape=tva_ref.shape,
                initial_value=None,
                skip_value=skip_value
            )
            result_ref._replace_data(truth_mask)
            states.set_reference("inference", "TIA", result_ref)
        
        states.set_current_step("TIA")
        logger.info(f"TIA completed (collapsing only): condition_met={states.condition_met}")
        return states
    
    # Case 2: Has filter axes (for-each)
    # Apply hierarchical collapse: criterion quantifiers per filter-axis element
    
    # Use the outermost for-each axis as primary filter
    primary_filter_axis = min(filter_axes.items(), key=lambda x: x[1])
    filter_axis_name, filter_axis_index = primary_filter_axis
    
    logger.debug(f"Primary filter axis: '{filter_axis_name}' at index {filter_axis_index}")
    
    # Check if any criterion axes are OUTSIDE (before) the filter axis
    # If so, we need to transpose to put the filter axis first
    outer_criterion_axes = []
    inner_criterion_axes = []
    for axis_name, quantifier in criterion_axes.items():
        if axis_name in tva_ref.axes:
            axis_idx = tva_ref.axes.index(axis_name)
            if axis_idx < filter_axis_index:
                outer_criterion_axes.append((axis_name, quantifier, axis_idx))
            else:
                inner_criterion_axes.append((axis_name, quantifier, axis_idx))
    
    # If we have outer criterion axes, transpose the tensor so filter axis comes first
    working_ref = tva_ref
    working_filter_index = filter_axis_index
    if outer_criterion_axes:
        # Build new axis order: filter axis first, then all others
        new_axis_order = [filter_axis_name] + [ax for ax in tva_ref.axes if ax != filter_axis_name]
        logger.debug(f"Transposing tensor from {tva_ref.axes} to {new_axis_order} (filter axis '{filter_axis_name}' moved to front)")
        working_ref = tva_ref.transpose(new_axis_order)
        working_filter_index = 0  # Filter axis is now at index 0
        
        # Recalculate criterion indices in the transposed tensor
        inner_criterion_axes = []
        for axis_name, quantifier in criterion_axes.items():
            if axis_name in working_ref.axes:
                axis_idx = working_ref.axes.index(axis_name)
                if axis_idx > working_filter_index:  # Now all criterion axes should be inner
                    inner_criterion_axes.append((axis_name, quantifier, axis_idx))
    
    # Build criterion quantifiers dict indexed by axis position (in working_ref)
    criterion_by_index = {}
    for axis_name, quantifier, axis_idx in inner_criterion_axes:
        criterion_by_index[axis_idx] = quantifier
        logger.debug(f"Criterion axis '{axis_name}' (idx {axis_idx}): '{quantifier}'")
    
    # If no inner criterion axes, default to "some" for all inner axes
    if not criterion_by_index and len(working_ref.axes) > working_filter_index + 1:
        # Default: treat as "some element in the slice matches"
        logger.debug("No inner criterion specified, defaulting to 'some' behavior")
    
    # Apply hierarchical collapse
    truth_mask = _hierarchical_collapse(
        working_ref.tensor,
        working_ref.axes,
        working_filter_index,
        criterion_by_index,
        condition,
        skip_value
    )
    
    # Create result reference
    # The shape along filter axis is preserved, inner axes are collapsed
    if criterion_by_index:
        # Inner axes were collapsed - output is just the filter axis
        new_axes = [filter_axis_name]  # Always use original filter axis name
        new_shape = (working_ref.shape[working_filter_index],)
    else:
        # No collapse - preserve full shape (but use working_ref's structure)
        new_axes = working_ref.axes.copy()
        new_shape = working_ref.shape
    
    result_ref = Reference(
        axes=new_axes,
        shape=new_shape,
        initial_value=None,
        skip_value=skip_value
    )
    result_ref._replace_data(truth_mask)
    
    # condition_met: did ANY filter-axis element pass?
    states.condition_met = _contains_true(truth_mask)
    
    # Store the truth mask reference
    states.set_reference("inference", "TIA", result_ref)
    
    # Also store the primary filter axis name for downstream reference
    states.primary_filter_axis = filter_axis_name
    
    states.set_current_step("TIA")
    logger.info(f"TIA completed (hierarchical): condition_met={states.condition_met}, "
               f"filter_axis='{filter_axis_name}', truth_mask_shape={result_ref.shape}")
    
    return states


if __name__ == "__main__":
    print("=" * 80)
    print("TIA (Tool Inference Assertion) Demonstration - Version 2.0")
    print("Using Truth Mask + Hierarchical Collapsing")
    print("=" * 80)
    
    # Example 1: Simple collapsing - "all"
    print("\n" + "=" * 80)
    print("Example 1: Simple Collapsing - 'all'")
    print("=" * 80)
    print("Scenario: Check if ALL elements are True")
    
    tva_data = [
        [True, True, True],
        [True, False, True],
        [True, True, True]
    ]
    tva_ref = Reference.from_data(tva_data, axis_names=['document', 'paragraph'])
    
    print(f"\nInput: {tva_ref.tensor}")
    
    states1 = States()
    states1.set_reference("inference", "TVA", tva_ref)
    states1.assertion_condition = {
        "quantifiers": {"document": "all"},
        "condition": True
    }
    
    states1 = truth_inference_assertion(states1)
    tia_ref1 = states1.get_reference("inference", "TIA")
    
    print(f"Output: condition_met={states1.condition_met}")
    print(f"Truth mask: {tia_ref1.tensor if tia_ref1 else 'None'}")
    print("Expected: False (not all elements are True)")
    
    # Example 2: Simple collapsing - "some"
    print("\n" + "=" * 80)
    print("Example 2: Simple Collapsing - 'some'")
    print("=" * 80)
    print("Scenario: Check if SOME elements are True")
    
    states2 = States()
    states2.set_reference("inference", "TVA", tva_ref)
    states2.assertion_condition = {
        "quantifiers": {"paragraph": "some"},
        "condition": True
    }
    
    states2 = truth_inference_assertion(states2)
    tia_ref2 = states2.get_reference("inference", "TIA")
    
    print(f"Output: condition_met={states2.condition_met}")
    print(f"Truth mask: {tia_ref2.tensor if tia_ref2 else 'None'}")
    print("Expected: True (at least one element is True)")
    
    # Example 3: COMBINED PATTERN - "for each document where SOME paragraph"
    print("\n" + "=" * 80)
    print("Example 3: Combined Pattern - 'for-each' + 'some' (RECOMMENDED)")
    print("=" * 80)
    print("Scenario: For each DOCUMENT where SOME paragraph is True")
    
    states3 = States()
    states3.set_reference("inference", "TVA", tva_ref)
    states3.assertion_condition = {
        "quantifiers": {
            "document": "for-each",  # Filter: which documents
            "paragraph": "some"      # Criterion: has SOME True paragraph
        },
        "condition": True
    }
    
    print(f"\nInput tensor: {tva_ref.tensor}")
    print("  Document 0: [True, True, True] - has SOME True")
    print("  Document 1: [True, False, True] - has SOME True")
    print("  Document 2: [True, True, True] - has SOME True")
    
    states3 = truth_inference_assertion(states3)
    tia_ref3 = states3.get_reference("inference", "TIA")
    
    print(f"\nOutput:")
    print(f"  condition_met: {states3.condition_met}")
    print(f"  Truth mask axes: {tia_ref3.axes if tia_ref3 else 'None'}")
    print(f"  Truth mask shape: {tia_ref3.shape if tia_ref3 else 'None'}")
    print(f"  Truth mask: {tia_ref3.tensor if tia_ref3 else 'None'}")
    print("Expected: All 3 documents have SOME True paragraph -> all are TRUE_MARKER")
    
    # Example 4: COMBINED PATTERN - "for each document where ALL paragraphs"
    print("\n" + "=" * 80)
    print("Example 4: Combined Pattern - 'for-each' + 'all'")
    print("=" * 80)
    print("Scenario: For each DOCUMENT where ALL paragraphs are True")
    
    states4 = States()
    states4.set_reference("inference", "TVA", tva_ref)
    states4.assertion_condition = {
        "quantifiers": {
            "document": "for-each",  # Filter: which documents
            "paragraph": "all"       # Criterion: ALL paragraphs must be True
        },
        "condition": True
    }
    
    print(f"\nInput tensor: {tva_ref.tensor}")
    print("  Document 0: [True, True, True] - ALL True [YES]")
    print("  Document 1: [True, False, True] - NOT all True [NO]")
    print("  Document 2: [True, True, True] - ALL True [YES]")
    
    states4 = truth_inference_assertion(states4)
    tia_ref4 = states4.get_reference("inference", "TIA")
    
    print(f"\nOutput:")
    print(f"  condition_met: {states4.condition_met}")
    print(f"  Truth mask: {tia_ref4.tensor if tia_ref4 else 'None'}")
    print("Expected: Docs 0,2 are TRUE_MARKER, Doc 1 is FALSE_MARKER")
    
    # Example 5: Simple for-each (no criterion)
    print("\n" + "=" * 80)
    print("Example 5: Simple For-Each (Pure Truth Mask)")
    print("=" * 80)
    print("Scenario: Just transform to truth mask, no collapsing")
    
    simple_data = [True, False, True, False]
    simple_ref = Reference.from_data(simple_data, axis_names=['item'])
    
    states5 = States()
    states5.set_reference("inference", "TVA", simple_ref)
    states5.assertion_condition = {
        "quantifiers": {"item": "for-each"},
        "condition": True
    }
    
    print(f"\nInput: {simple_ref.tensor}")
    
    states5 = truth_inference_assertion(states5)
    tia_ref5 = states5.get_reference("inference", "TIA")
    
    print(f"\nOutput:")
    print(f"  condition_met: {states5.condition_met}")
    print(f"  Truth mask: {tia_ref5.tensor if tia_ref5 else 'None'}")
    print("Expected: [TRUE, FALSE, TRUE, FALSE] markers")
    
    # Example 6: 3-axis example
    print("\n" + "=" * 80)
    print("Example 6: 3-Axis - 'for-each section where SOME paragraph'")
    print("=" * 80)
    
    # sections x documents x paragraphs
    three_axis_data = [
        [[True, False], [True, True]],   # section 0: doc0 has True, doc1 has True
        [[False, False], [False, True]], # section 1: doc0 has no True, doc1 has True
    ]
    three_ref = Reference.from_data(three_axis_data, axis_names=['section', 'document', 'paragraph'])
    
    states6 = States()
    states6.set_reference("inference", "TVA", three_ref)
    states6.assertion_condition = {
        "quantifiers": {
            "section": "for-each",    # Filter: which sections
            "paragraph": "some"       # Criterion: has SOME True paragraph (across all docs in section)
        },
        "condition": True
    }
    
    print(f"\nInput tensor: {three_ref.tensor}")
    print("  Section 0: [[True, False], [True, True]] - has SOME True")
    print("  Section 1: [[False, False], [False, True]] - has SOME True")
    
    states6 = truth_inference_assertion(states6)
    tia_ref6 = states6.get_reference("inference", "TIA")
    
    print(f"\nOutput:")
    print(f"  condition_met: {states6.condition_met}")
    print(f"  Truth mask axes: {tia_ref6.axes if tia_ref6 else 'None'}")
    print(f"  Truth mask: {tia_ref6.tensor if tia_ref6 else 'None'}")
    
    # Example 7: Edge case - empty axis
    print("\n" + "=" * 80)
    print("Example 7: Edge Case - Empty Tensor")
    print("=" * 80)
    
    empty_ref = Reference.from_data([], axis_names=['empty'])
    states7 = States()
    states7.set_reference("inference", "TVA", empty_ref)
    states7.assertion_condition = {
        "quantifiers": {"empty": "all"},
        "condition": True
    }
    
    print(f"\nInput: {empty_ref.tensor}")
    
    states7 = truth_inference_assertion(states7)
    
    print(f"Output: condition_met={states7.condition_met}")
    print("Expected: True (vacuous truth - all zero elements satisfy)")
    
    print("\n" + "=" * 80)
    print("Demonstration Complete")
    print("=" * 80)
    print("\nKey Points:")
    print("1. Truth mask is the PRIMARY output - preserves structure")
    print("2. Combined pattern: 'for-each' (filter) + 'some/all/none' (criterion)")
    print("3. Hierarchical collapse: criterion applied per filter-axis element")
    print("4. condition_met: whether ANY element passes (for control flow)")
